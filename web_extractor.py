import os
import csv
import time
import json
import pandas as pd
import base64
from openai import OpenAI
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class HistoriasClinicasExtractor:
    def __init__(self, output_folder="datos_extraidos"):
        print("🔄 Inicializando el extractor de historias clínicas...")
        
        # Configurar opciones de Chrome
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Inicializar Selenium con undetected-chromedriver
        try:
            self.driver = uc.Chrome(options=options)
            print("✅ Navegador inicializado correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar el navegador: {str(e)}")
            raise e
            
        self.wait = WebDriverWait(self.driver, 10)
        
        # Configurar rutas de salida
        self.output_folder = output_folder
        self.pacientes_csv = os.path.join(output_folder, "pacientes.csv")
        self.consultas_csv = os.path.join(output_folder, "consultas.csv")
        
        # Asegurarse de que existe la carpeta de salida
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Inicializar DataFrames
        self.pacientes_df = pd.DataFrame(columns=[
            "Paciente", "Fecha", "ID_Paciente", "Edad"
        ])
        
        self.consultas_df = pd.DataFrame(columns=[
            "ID_Paciente", "No_Consulta", "Tabaquismo", "Diabetes", 
            "PSA", "Presion_Arterial", "Diagnostico", "Tratamiento"
        ])
    
    def login(self, email, password):
        print(f"🔑 Iniciando sesión con usuario: {email}")
        try:
            # Abrir la página
            self.driver.get("https://programahistoriasclinicas.com/")
            time.sleep(3)  # Esperamos más tiempo para que cargue completamente
            
            # Tomar captura de pantalla de diagnóstico
            self.driver.save_screenshot("login_page.png")
            print(f"📸 Captura de pantalla guardada en login_page.png")
            
            # Intentar encontrar el botón de iniciar sesión de diferentes maneras
            try:
                # Método 1: XPATH
                iniciar_sesion_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Iniciar Sesión')]"))
                )
                print("✅ Botón encontrado con XPATH")
            except:
                try:
                    # Método 2: CSS Selector
                    iniciar_sesion_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-iniciar-sesion, a.login-button"))
                    )
                    print("✅ Botón encontrado con CSS Selector")
                except:
                    try:
                        # Método 3: Botón verde
                        iniciar_sesion_btn = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-success, .btn-primary"))
                        )
                        print("✅ Botón encontrado por clase btn-success/primary")
                    except:
                        # Método 4: JavaScript (último recurso)
                        print("⚠️ Usando JavaScript para hacer clic en el botón")
                        self.driver.execute_script("""
                            var buttons = document.querySelectorAll('a.btn, button.btn');
                            for(var i=0; i<buttons.length; i++) {
                                if(buttons[i].textContent.includes('Iniciar Sesión') || 
                                buttons[i].textContent.includes('Login') ||
                                buttons[i].classList.contains('btn-success')) {
                                    buttons[i].click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        time.sleep(3)
            
            # Si encontramos el botón con los métodos 1-3, hacer clic
            if 'iniciar_sesion_btn' in locals():
                iniciar_sesion_btn.click()
            
            time.sleep(3)
            
            # Tomar otra captura para ver la página de login
            self.driver.save_screenshot("login_form.png")
            print(f"📸 Captura de pantalla guardada en login_form.png")
            
            # Completar formulario de login (con más robustez)
            try:
                # Intentar encontrar el campo de email de diferentes maneras
                try:
                    email_input = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "email"))
                    )
                except:
                    try:
                        email_input = self.driver.find_element(By.ID, "email")
                    except:
                        try:
                            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                        except:
                            # Último recurso: cualquier input que parezca de email
                            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='email' i], input[placeholder*='correo' i]")
                
                email_input.clear()
                email_input.send_keys(email)
                print("✅ Campo de email completado")
                
                # Intentar encontrar el campo de contraseña
                try:
                    password_input = self.driver.find_element(By.NAME, "password")
                except:
                    try:
                        password_input = self.driver.find_element(By.ID, "password")
                    except:
                        try:
                            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                        except:
                            # Último recurso
                            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='contraseña' i], input[placeholder*='password' i]")
                
                password_input.clear()
                password_input.send_keys(password)
                print("✅ Campo de contraseña completado")
                
                # Buscar el botón de login de varias maneras
                try:
                    login_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Iniciar Sesión')]"))
                    )
                except:
                    try:
                        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn-primary, button.login-button, input[type='submit']")
                    except:
                        # JavaScript como último recurso
                        print("⚠️ Usando JavaScript para hacer clic en el botón de login")
                        self.driver.execute_script("""
                            var buttons = document.querySelectorAll('button, input[type="submit"]');
                            for(var i=0; i<buttons.length; i++) {
                                if(buttons[i].textContent.includes('Iniciar') || 
                                buttons[i].textContent.includes('Login') ||
                                buttons[i].classList.contains('btn-primary')) {
                                    buttons[i].click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        time.sleep(3)
                
                # Si encontramos el botón con los métodos anteriores, hacer clic
                if 'login_btn' in locals():
                    login_btn.click()
                
                time.sleep(3)
                
                # Verificar si el login fue exitoso
                self.driver.save_screenshot("post_login.png")
                print(f"📸 Captura de pantalla guardada en post_login.png")
                
                # Verificar si estamos en la página principal
                if "panel" in self.driver.current_url:
                    print("✅ Sesión iniciada correctamente")
                    return True
                else:
                    print("⚠️ URL después del login no contiene 'panel'. URL actual:", self.driver.current_url)
                    return False
                
            except Exception as e:
                print(f"❌ Error al completar el formulario de login: {str(e)}")
                return False
                
        except Exception as e:
            print(f"❌ Error al iniciar sesión: {str(e)}")
            return False
    
    def ir_a_pacientes(self):
        print("👥 Navegando a la sección de pacientes...")
        try:
            # Tomar captura para diagnóstico
            self.driver.save_screenshot("dashboard.png")
            print(f"📸 Captura de pantalla guardada en dashboard.png")
            
            # Esperar a que cargue completamente la página
            time.sleep(3)
            
            # Intentar diferentes métodos para encontrar el enlace a Pacientes
            try:
                # Método 1: XPATH
                pacientes_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Pacientes')]"))
                )
                print("✅ Enlace a Pacientes encontrado con XPATH")
            except:
                try:
                    # Método 2: CSS Selector
                    pacientes_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='pacientes']"))
                    )
                    print("✅ Enlace a Pacientes encontrado con CSS Selector")
                except:
                    try:
                        # Método 3: Buscar por ícono o clase
                        pacientes_btn = self.wait.until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".menu-pacientes, .icon-pacientes"))
                        )
                        print("✅ Enlace a Pacientes encontrado por clase")
                    except:
                        # Método 4: JavaScript (último recurso)
                        print("⚠️ Usando JavaScript para encontrar y hacer clic en Pacientes")
                        found = self.driver.execute_script("""
                            var links = document.querySelectorAll('a');
                            for(var i=0; i<links.length; i++) {
                                if(links[i].textContent.includes('Paciente') || 
                                links[i].href.includes('paciente') ||
                                links[i].classList.contains('pacientes')) {
                                    links[i].click();
                                    return true;
                                }
                            }
                            // Intentar con botones o divs clicables
                            var elements = document.querySelectorAll('button, div[role="button"], div.clickable');
                            for(var i=0; i<elements.length; i++) {
                                if(elements[i].textContent.includes('Paciente')) {
                                    elements[i].click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        if not found:
                            print("❌ No se encontró ningún enlace a Pacientes con JavaScript")
                            # Intentar ir directamente a la URL
                            self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                            time.sleep(3)
            
            # Si encontramos el botón con los métodos 1-3, hacer clic
            if 'pacientes_btn' in locals():
                pacientes_btn.click()
            
            # Esperar a que cargue la página de pacientes
            time.sleep(3)
            
            # Tomar captura para ver si cargó correctamente
            self.driver.save_screenshot("pacientes_page.png")
            print(f"📸 Captura de pantalla guardada en pacientes_page.png")
            
            # Verificar si la página de pacientes cargó correctamente
            # Buscar elementos típicos de la página de pacientes
            try:
                # Intentar encontrar algún indicador de que estamos en la página de pacientes
                if "pacientes" in self.driver.current_url.lower():
                    print("✅ URL contiene 'pacientes'")
                    return True
                    
                # Intentar encontrar el botón "Nuevo Paciente" o la tabla de pacientes
                self.driver.find_element(By.XPATH, "//button[contains(text(), 'Nuevo Paciente')] | //table[contains(@class, 'pacientes')]")
                print("✅ Navegación exitosa - Se encontró la tabla o botón de pacientes")
                return True
            except:
                # Si no podemos verificar, pero no hay errores, asumimos que funcionó
                print("⚠️ No se pudo verificar si estamos en la página de pacientes, pero continuamos")
                return True
                
        except Exception as e:
            print(f"❌ Error al navegar a pacientes: {str(e)}")
            
            # Último intento - navegar directamente a la URL
            try:
                print("🔄 Intentando navegar directamente a la URL de pacientes...")
                self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                time.sleep(3)
                self.driver.save_screenshot("direct_pacientes.png")
                
                # Verificar si funcionó
                if "pacientes" in self.driver.current_url.lower():
                    print("✅ Navegación directa exitosa")
                    return True
                else:
                    return False
            except:
                return False
    
    def obtener_lista_pacientes(self):
        print("📋 Obteniendo lista de pacientes desde el HTML...")
        lista_pacientes = []
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "datatable-row-wrapper")))
            filas = self.driver.find_elements(By.CSS_SELECTOR, "datatable-row-wrapper")

            for index, fila in enumerate(filas):
                try:
                    celda = fila.find_element(By.CSS_SELECTOR, "datatable-body-cell")
                    nombre = celda.text.strip()
                    if nombre:
                        lista_pacientes.append({"index": index, "nombre": nombre})
                        print(f"✅ Paciente encontrado: {nombre}")
                except Exception as e:
                    print(f"⚠️ Error leyendo fila {index}: {str(e)}")

            print(f"✅ Total pacientes encontrados: {len(lista_pacientes)}")
            return lista_pacientes

        except Exception as e:
            print(f"❌ Error al obtener lista de pacientes: {str(e)}")
            return []

    def procesar_paciente(self, paciente_info, credenciales=None):
        """
        Procesa la información de un paciente.
        
        Args:
            paciente_info: Información del paciente (dict o índice)
            credenciales: Tupla opcional (email, password) para reinicios de sesión
        """
        if isinstance(paciente_info, dict):
            paciente_index = paciente_info.get('index', 0)
            nombre_paciente = paciente_info.get('nombre', f"Paciente #{paciente_index+1}")
        else:
            paciente_index = paciente_info
            nombre_paciente = f"Paciente #{paciente_index+1}"

        print(f"\U0001F464 Procesando paciente: {nombre_paciente}...")

        try:
            self.driver.save_screenshot(f"pre_click_paciente_{paciente_index}.png")
            clicked = False

            # MÉTODO: Clic por contenido HTML
            try:
                print("🔍 Buscando fila del paciente por HTML...")
                nombre_limpio = nombre_paciente.lower().replace(",", "").strip()
                filas = self.driver.find_elements(By.CSS_SELECTOR, "datatable-row-wrapper")
                for fila in filas:
                    try:
                        celda = fila.find_element(By.CSS_SELECTOR, "datatable-body-cell")
                        texto = celda.text.lower().replace(",", "").strip()
                        if nombre_limpio in texto:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", celda)
                            time.sleep(1)
                            celda.click()
                            print(f"✅ Clic exitoso sobre {texto}")
                            clicked = True
                            break
                    except Exception as e:
                        print(f"⚠️ Error leyendo celda: {str(e)}")
                
                if not clicked:
                    print("❌ No se pudo hacer clic en el paciente por HTML")
                    return False

                time.sleep(3)
                self.driver.save_screenshot(f"post_click_paciente_{paciente_index}.png")

                # Ir a pestaña de Consultas H.Clínica
                print("🔍 Buscando el tab de Consultas H.Clínica por texto y rol...")
                consultas_tab = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='tab' and contains(., 'Consultas H.Clínica')]"))
                )
                consultas_tab.click()
                print("✅ Tab Consultas H.Clínica clickeado")

                time.sleep(3)
                self.driver.save_screenshot(f"consultas_tab_{paciente_index}.png")

                # Procesar sección 'Más' y 'Imprimir Histórico'
                print("🔍 Buscando botón 'Más'")
                mas_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Más')]"))
                )
                mas_btn.click()
                print("✅ Botón 'Más' clicado")
                time.sleep(1)

                print("🔍 Buscando opción 'Imprimir Histórico'")
                imprimir_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Imprimir Histórico')]"))
                )
                imprimir_btn.click()
                print("✅ Opción 'Imprimir Histórico' clicada")

                time.sleep(3)
                self.driver.save_screenshot(f"post_imprimir_{paciente_index}.png")

                # MANEJO DE VENTANAS Y PROCESO DE EXTRACCIÓN
                window_handles_count = len(self.driver.window_handles)
                if window_handles_count > 1:
                    print(f"✅ Detectadas {window_handles_count} pestañas")
                    
                    # Guardar la ventana original
                    original_window = self.driver.current_window_handle
                    
                    # Cambiar a la nueva pestaña (última abierta)
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    print("✅ Cambio a la pestaña del PDF")
                    
                    # Dar tiempo para que cargue completamente el PDF
                    time.sleep(5)
                    
                    # Tomar capturas de cada página del PDF (si hay múltiples páginas)
                    screenshot_paths = []
                    
                    # Capturar primera página
                    pdf_screenshot_path = f"pdf_tab_{paciente_index}_p1.png"
                    self.driver.save_screenshot(pdf_screenshot_path)
                    screenshot_paths.append(pdf_screenshot_path)
                    print(f"📸 Captura del PDF guardada: {pdf_screenshot_path}")
                    
                    # Probar si hay un botón para la siguiente página
                    try:
                        next_page_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".next-button, .nextButton, [title='Next Page'], [aria-label='Next page']")
                        if next_page_buttons:
                            for i in range(1, 4):  # Limitamos a 3 páginas adicionales para evitar bucles infinitos
                                next_page_buttons[0].click()
                                time.sleep(2)
                                pdf_screenshot_path = f"pdf_tab_{paciente_index}_p{i+1}.png"
                                self.driver.save_screenshot(pdf_screenshot_path)
                                screenshot_paths.append(pdf_screenshot_path)
                                print(f"📸 Captura de página adicional guardada: {pdf_screenshot_path}")
                    except Exception as page_error:
                        print(f"ℹ️ No se encontraron más páginas para capturar: {str(page_error)}")
                    
                    # Intentar primero la extracción de texto
                    resultado = None
                    texto_extraido = ""
                    
                    try:
                        print("📄 Intentando extraer texto del PDF...")
                        texto_extraido = self.driver.find_element(By.TAG_NAME, 'body').text
                        
                        # Si el texto es suficientemente largo, procesarlo
                        if texto_extraido and len(texto_extraido.strip()) > 100:
                            print(f"✅ Texto extraído exitosamente (longitud: {len(texto_extraido)} caracteres)")
                            print(f"📝 Primeros 100 caracteres: {texto_extraido[:100]}...")
                            resultado = self.extraer_info_clinica_openai(pdf_text=texto_extraido)
                        else:
                            print(f"⚠️ Texto extraído insuficiente (longitud: {len(texto_extraido.strip())} caracteres)")
                            # Intentar método de extracción de texto alternativo
                            texto_extraido = self.extraer_contenido_pdf_desde_navegador()
                            if texto_extraido and len(texto_extraido.strip()) > 100:
                                print(f"✅ Texto extraído con método alternativo (longitud: {len(texto_extraido)} caracteres)")
                                resultado = self.extraer_info_clinica_openai(pdf_text=texto_extraido)
                            else:
                                print(f"⚠️ Texto alternativo insuficiente, pasando a extracción por imagen")
                    except Exception as text_error:
                        print(f"⚠️ Error extrayendo texto: {str(text_error)}")
                    
                    # Si no tenemos resultado con texto, usar la imagen
                    if not resultado and screenshot_paths:
                        print("🖼️ Intentando extraer información a partir de las imágenes...")
                        resultado = self.extraer_info_por_imagen(screenshot_paths[0])  # Usamos la primera página
                    
                    # Si tenemos resultado, guardarlo
                    if resultado:
                        paciente = resultado.get("paciente", {})
                        consultas = resultado.get("consultas", [])
                        self.guardar_datos_paciente(paciente)
                        self.guardar_datos_consultas(consultas)
                        print("✅ Datos guardados en CSV")
                    else:
                        print("⚠️ No se pudo extraer información del PDF")
                    
                    # Cerrar la pestaña del PDF y volver a la principal
                    try:
                        print("🔄 Cerrando pestaña del PDF...")
                        self.driver.close()
                        time.sleep(1)
                        self.driver.switch_to.window(original_window)
                        print("✅ Regreso a la ventana principal")
                    except Exception as close_error:
                        print(f"⚠️ Error al cerrar pestaña: {str(close_error)}")
                        # Intentar recuperación de emergencia
                        try:
                            self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                            time.sleep(3)
                        except:
                            # En caso extremo, reiniciar navegador si tenemos credenciales
                            if credenciales and len(credenciales) == 2:
                                print("🔄 Reiniciando el navegador...")
                                self.driver.quit()
                                options = uc.ChromeOptions()
                                options.add_argument("--window-size=1920,1080")
                                self.driver = uc.Chrome(options=options)
                                self.wait = WebDriverWait(self.driver, 10)
                                
                                email, password = credenciales
                                self.login(email, password)
                                self.ir_a_pacientes()
                                print("✅ Navegador reiniciado")
                            else:
                                print("⚠️ No hay credenciales disponibles para reiniciar")
                                return False
                    
                    # Volver a la página de pacientes
                    try:
                        self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                        time.sleep(3)
                    except Exception as nav_error:
                        print(f"⚠️ Error al volver a la página de pacientes: {str(nav_error)}")
                    
                    self.driver.save_screenshot(f"post_process_{paciente_index}.png")
                    print(f"✅ Procesamiento exitoso del paciente {nombre_paciente}")
                    return True
                else:
                    print("⚠️ No se abrió nueva pestaña para el PDF")
                    return False
                    
            except Exception as e:
                print(f"❌ Error en el flujo principal: {str(e)}")
                # Intentar recuperar la sesión
                try:
                    self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                    time.sleep(3)
                except:
                    pass
                return False

        except Exception as e:
            print(f"❌ Error general al procesar paciente: {str(e)}")
            try:
                self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                time.sleep(3)
            except:
                pass
            return False

    def extraer_contenido_pdf_desde_navegador(self):
        """
        Intenta extraer el contenido de texto de un PDF abierto en el navegador 
        usando diferentes métodos.
        """
        try:
            print("📄 Intentando extraer texto del PDF con método directo...")
            
            # Método 1: Intenta obtener el texto directamente del body
            try:
                texto_directo = self.driver.find_element(By.TAG_NAME, 'body').text
                if texto_directo and len(texto_directo.strip()) > 100:
                    print("✅ Texto extraído directamente del body")
                    return texto_directo
                else:
                    print("⚠️ Texto del body demasiado corto, probando otros métodos")
            except Exception as e:
                print(f"⚠️ Error extrayendo texto directo: {str(e)}")
            
            # Método 2: Intenta usar un script JavaScript más simple
            try:
                print("📄 Intentando extracción con JavaScript simple...")
                script_simple = """
                var text = '';
                var elements = document.querySelectorAll('p, span, div');
                for (var i = 0; i < elements.length; i++) {
                    if (elements[i].innerText && elements[i].innerText.trim()) {
                        text += elements[i].innerText + '\\n';
                    }
                }
                return text;
                """
                texto_js_simple = self.driver.execute_script(script_simple)
                if texto_js_simple and len(texto_js_simple.strip()) > 100:
                    print("✅ Texto extraído con JavaScript simple")
                    return texto_js_simple
                else:
                    print("⚠️ JavaScript simple no extrajo suficiente texto")
            except Exception as e:
                print(f"⚠️ Error con JavaScript simple: {str(e)}")
            
            # Método 3: Para PDF.js, usar un enfoque más específico
            try:
                print("📄 Intentando extracción específica para PDF.js...")
                script_pdfjs = """
                var text = '';
                
                // Intentar encontrar elementos de PDF.js
                var textLayers = document.querySelectorAll('.textLayer');
                if (textLayers && textLayers.length > 0) {
                    for (var i = 0; i < textLayers.length; i++) {
                        text += textLayers[i].innerText + '\\n\\n';
                    }
                }
                
                // Si no encontramos nada, buscar otros elementos con texto
                if (!text.trim()) {
                    var canvasContainers = document.querySelectorAll('.canvasWrapper');
                    if (canvasContainers && canvasContainers.length > 0) {
                        text = 'PDF detectado pero no se puede extraer el texto completo';
                    }
                }
                
                return text;
                """
                texto_pdfjs = self.driver.execute_script(script_pdfjs)
                if texto_pdfjs and len(texto_pdfjs.strip()) > 20:
                    print("✅ Texto extraído con método PDF.js específico")
                    return texto_pdfjs
                else:
                    print("⚠️ Método PDF.js no extrajo suficiente texto")
            except Exception as e:
                print(f"⚠️ Error con método PDF.js: {str(e)}")
            
            # Si llegamos aquí, todos los métodos fallaron
            # En este punto, vamos a tomar una captura de pantalla y usarla como último recurso
            print("⚠️ Todos los métodos de extracción de texto fallaron")
            
            # Devolver un mensaje para que API pueda procesar la captura
            return "El contenido no pudo ser extraído como texto. Por favor, analiza la imagen adjunta."
            
        except Exception as e:
            print(f"❌ Error general extrayendo texto del PDF: {str(e)}")
            return ""

    def guardar_datos_paciente(self, paciente_dict):
        archivo = os.path.join("datos_extraidos", "pacientes.csv")
        campos = ["ID Paciente", "Nombre", "Edad", "Fecha"]
        os.makedirs("datos_extraidos", exist_ok=True)

        try:
            escribir_encabezado = not os.path.exists(archivo)
            with open(archivo, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                if escribir_encabezado:
                    writer.writeheader()
                writer.writerow({k: paciente_dict.get(k, "") for k in campos})
            print("✅ Datos del paciente guardados")
        except Exception as e:
            print(f"❌ Error guardando datos del paciente: {str(e)}")

    def guardar_datos_consultas(self, lista_consultas):
        archivo = os.path.join("datos_extraidos", "consultas.csv")
        campos = [
            "ID Paciente", "No Consulta", "Tabaquismo", "Diabetes", 
            "PSA", "Presion Arterial", "Diagnostico", "Tratamiento"
        ]
        os.makedirs("datos_extraidos", exist_ok=True)

        try:
            escribir_encabezado = not os.path.exists(archivo)
            with open(archivo, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                if escribir_encabezado:
                    writer.writeheader()
                for consulta in lista_consultas:
                    writer.writerow({k: consulta.get(k, "") for k in campos})
            print("✅ Consultas guardadas correctamente")
        except Exception as e:
            print(f"❌ Error guardando consultas: {str(e)}")

    def extraer_info_clinica_openai(self, pdf_text="", fallback_image_path=None):
        """
        Extrae información clínica usando OpenAI, procesando texto o imagen si es necesario.
        
        Args:
            pdf_text: Texto extraído del PDF
            fallback_image_path: Ruta a la imagen de respaldo si el texto está vacío
        
        Returns:
            Dict con la información extraída o None si hay error
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ No se encontró la API key de OpenAI")
                return None
                
            client = OpenAI(api_key=api_key)
            
            # Si el texto está vacío o es muy corto, intentar con la imagen
            if not pdf_text or len(pdf_text.strip()) < 50:
                if fallback_image_path and os.path.exists(fallback_image_path):
                    print(f"🖼️ El texto es insuficiente. Usando la imagen {fallback_image_path} como alternativa...")
                    
                    try:
                        with open(fallback_image_path, "rb") as image_file:
                            # Usar el modelo de visión de OpenAI para analizar la imagen
                            print("🧠 Enviando imagen a OpenAI para análisis...")
                            
                            completion = client.chat.completions.create(
                                model="gpt-4o",  # Este modelo puede procesar imágenes
                                messages=[
                                    {"role": "system", "content": "Eres un asistente experto en análisis clínico, capaz de extraer información de imágenes de historias clínicas."},
                                    {
                                        "role": "user", 
                                        "content": [
                                            {"type": "text", "text": "Extrae la siguiente información en formato JSON a partir de esta imagen de una historia clínica. Debe incluir un diccionario 'paciente' con los campos: ID Paciente, Nombre, Edad, Fecha. Y una lista llamada 'consultas', donde cada elemento contiene: ID Paciente, No Consulta, Tabaquismo, Diabetes, PSA, Presion Arterial, Diagnostico, Tratamiento. Si no se encuentra un campo, debe decir 'No reporta'."},
                                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"}}
                                        ]
                                    }
                                ],
                                temperature=0.2
                            )
                            
                            respuesta = completion.choices[0].message.content
                            print("📄 Respuesta de análisis de imagen recibida")
                        
                    except Exception as img_error:
                        print(f"❌ Error al procesar la imagen: {str(img_error)}")
                        respuesta = "{}"
                else:
                    print("⚠️ No hay texto ni imagen válida para procesar")
                    return None
            else:
                # Procesar el texto normalmente
                print(f"📝 Procesando texto (longitud: {len(pdf_text)} caracteres)...")
                
                prompt = (
                    "Extrae la siguiente información en formato JSON a partir del texto clínico de una historia clínica. "
                    "Debe incluir un diccionario 'paciente' con los campos: ID Paciente, Nombre, Edad, Fecha. "
                    "Y una lista llamada 'consultas', donde cada elemento contiene: ID Paciente, No Consulta, Tabaquismo, "
                    "Diabetes, PSA, Presion Arterial, Diagnostico, Tratamiento. "
                    "Si no se encuentra un campo, debe decir 'No reporta'.\n\nTexto:\n" + pdf_text
                )

                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto en análisis clínico."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )

                respuesta = completion.choices[0].message.content
                print("📄 Respuesta de OpenAI recibida")

            # Procesar la respuesta para extraer el JSON
            try:
                json_data = json.loads(respuesta)
                print("✅ JSON procesado correctamente")
                return json_data
            except json.JSONDecodeError:
                print("⚠️ La respuesta no es un JSON válido, intentando extraer...")
                # Buscar bloques de código JSON en la respuesta
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|\{[\s\S]*\}', respuesta)
                if json_match:
                    json_text = json_match.group(1) or json_match.group(2) or json_match.group(0)
                    try:
                        # Limpiar posibles caracteres adicionales
                        json_text = json_text.strip()
                        if not json_text.startswith('{'):
                            json_text = '{' + json_text.split('{', 1)[1]
                        if not json_text.endswith('}'):
                            json_text = json_text.rsplit('}', 1)[0] + '}'
                        
                        json_data = json.loads(json_text)
                        print("✅ JSON extraído y procesado correctamente")
                        return json_data
                    except Exception as je:
                        print(f"❌ Error procesando JSON extraído: {str(je)}")
                
                # Si todo falla, crear una estructura básica
                print("⚠️ Creando estructura JSON por defecto")
                return {
                    "paciente": {
                        "ID Paciente": "No reporta",
                        "Nombre": "No reporta",
                        "Edad": "No reporta",
                        "Fecha": "No reporta"
                    },
                    "consultas": []
                }
        
        except Exception as e:
            print(f"❌ Error general procesando con OpenAI: {str(e)}")
            # En caso de error, intentar devolver una estructura básica
            return {
                "paciente": {
                    "ID Paciente": "Error de procesamiento",
                    "Nombre": "Error de procesamiento",
                    "Edad": "Error de procesamiento",
                    "Fecha": "Error de procesamiento"
                },
                "consultas": []
            }
    def extraer_info_por_imagen(self, screenshot_path):
        """
        Extraer información de la historia clínica usando la captura de pantalla del PDF
        cuando la extracción de texto falló.
        
        Args:
            screenshot_path: Ruta a la imagen capturada del PDF
        
        Returns:
            Dict con la información extraída o estructura básica si hay error
        """
        try:
            print(f"🖼️ Intentando extraer información de la imagen {screenshot_path}...")
            
            if not os.path.exists(screenshot_path):
                print(f"❌ No se encontró la imagen en la ruta: {screenshot_path}")
                return self._crear_estructura_basica()
                
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ No se encontró la API key de OpenAI")
                return self._crear_estructura_basica()
                
            # Crear cliente de OpenAI
            client = OpenAI(api_key=api_key)
            
            # Leer la imagen y convertirla a base64
            try:
                with open(screenshot_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # Preparar prompt específico para extraer información de historia clínica
                    prompt = """
                    Analiza esta imagen de una historia clínica y extrae la siguiente información en formato JSON:
                    
                    1. Un objeto "paciente" con:
                    - ID Paciente (del campo NIF/DNI)
                    - Nombre (nombre completo del paciente)
                    - Edad (valor numérico)
                    - Fecha (fecha de la consulta)
                    
                    2. Una lista "consultas", donde cada consulta tiene:
                    - ID Paciente (mismo que arriba)
                    - No Consulta (número o fecha de la consulta)
                    - Tabaquismo (Si/No/No reporta)
                    - Diabetes (Si/No/No reporta)
                    - PSA (valor si existe)
                    - Presion Arterial (valores si existen)
                    - Diagnostico (diagnóstico principal)
                    - Tratamiento (medicación o tratamiento indicado)
                    
                    Responde SOLO con el JSON, sin explicaciones adicionales.
                    Si algún campo no aparece en la imagen, usa "No reporta".
                    """
                    
                    print("🧠 Enviando imagen a OpenAI para análisis...")
                    
                    # Llamar a la API de OpenAI con la imagen
                    completion = client.chat.completions.create(
                        model="gpt-4o",  # Modelo con capacidad de visión
                        messages=[
                            {"role": "system", "content": "Eres un asistente especializado en extraer información médica de historias clínicas."},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                                ]
                            }
                        ],
                        temperature=0.2,  # Temperatura baja para respuestas más deterministas
                        max_tokens=2000   # Suficiente para el JSON
                    )
                    
                    # Obtener la respuesta
                    respuesta = completion.choices[0].message.content
                    print("📄 Respuesta de análisis de imagen recibida")
                    
                    # Depuración - guardar la respuesta en un archivo
                    with open(f"{screenshot_path}_respuesta.txt", "w", encoding="utf-8") as f:
                        f.write(respuesta)
                    
                    # Procesar la respuesta para extraer JSON
                    return self._procesar_respuesta_json(respuesta)
                    
            except Exception as img_error:
                print(f"❌ Error procesando la imagen: {str(img_error)}")
                return self._crear_estructura_basica()
                
        except Exception as e:
            print(f"❌ Error general en extracción por imagen: {str(e)}")
            return self._crear_estructura_basica()

    def _procesar_respuesta_json(self, respuesta):
        """
        Procesa la respuesta de la API para extraer el JSON.
        
        Args:
            respuesta: Texto de respuesta de la API
            
        Returns:
            Dict con los datos extraídos
        """
        try:
            # Intentar parsear directamente
            try:
                json_data = json.loads(respuesta)
                print("✅ JSON procesado correctamente")
                return json_data
            except json.JSONDecodeError:
                print("⚠️ La respuesta no es JSON válido, intentando extraer...")
                
                # Buscar bloques de código JSON en la respuesta
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|\{[\s\S]*\}', respuesta)
                if json_match:
                    json_text = json_match.group(1) or json_match.group(2) or json_match.group(0)
                    try:
                        # Limpiar posibles caracteres adicionales
                        json_text = json_text.strip()
                        if not json_text.startswith('{'):
                            json_text = '{' + json_text.split('{', 1)[1]
                        if not json_text.endswith('}'):
                            json_text = json_text.rsplit('}', 1)[0] + '}'
                        
                        json_data = json.loads(json_text)
                        print("✅ JSON extraído y procesado correctamente")
                        return json_data
                    except Exception as je:
                        print(f"❌ Error procesando JSON extraído: {str(je)}")
                
                # Si todo falla, crear una estructura básica
                return self._crear_estructura_basica()
        except Exception as e:
            print(f"❌ Error procesando respuesta JSON: {str(e)}")
            return self._crear_estructura_basica()

    def _crear_estructura_basica(self):
        """
        Crea una estructura JSON básica cuando hay errores.
        
        Returns:
            Dict con estructura básica de datos
        """
        print("⚠️ Usando estructura de datos por defecto")
        return {
            "paciente": {
                "ID Paciente": "No reporta",
                "Nombre": "No reporta",
                "Edad": "No reporta",
                "Fecha": "No reporta"
            },
            "consultas": []
        }    
    def cerrar(self):
        print("👋 Cerrando navegador...")
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")
