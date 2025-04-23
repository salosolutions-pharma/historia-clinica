import os
import csv
import time
import json
import pandas as pd
import openai
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

    def procesar_paciente(self, paciente_info):
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
            except Exception as e:
                print(f"❌ No se pudo buscar por HTML: {str(e)}")

            if not clicked:
                print("❌ No se pudo hacer clic en el paciente por HTML")
                return False

            time.sleep(3)
            self.driver.save_screenshot(f"post_click_paciente_{paciente_index}.png")

            # Ir a pestaña de Consultas H.Clínica
            try:
                print("🔍 Buscando el tab de Consultas H.Clínica por texto y rol...")
                consultas_tab = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='tab' and contains(., 'Consultas H.Clínica')]"))
                )
                consultas_tab.click()
                print("✅ Tab Consultas H.Clínica clickeado")
            except Exception as e:
                print(f"❌ No se pudo encontrar el tab de Consultas H.Clínica: {str(e)}")
                return False

            time.sleep(3)
            self.driver.save_screenshot(f"consultas_tab_{paciente_index}.png")

            # Procesar sección 'Más' y 'Imprimir Histórico'
            try:
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

                if len(self.driver.window_handles) > 1:
                    print("✅ Nueva pestaña detectada")
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    time.sleep(3)

                    # Intentar extraer texto del PDF (si es posible)
                    try:
                        texto_pdf = self.driver.find_element(By.TAG_NAME, 'body').text
                    except:
                        texto_pdf = ""

                    screenshot_path = f"pdf_tab_{paciente_index}.png"
                    self.driver.save_screenshot(screenshot_path)

                    print("🧠 Procesando contenido con OpenAI (texto o imagen)...")
                    resultado = self.extraer_info_clinica_openai(pdf_text=texto_pdf, fallback_image_path=screenshot_path)

                    if resultado:
                        paciente = resultado.get("paciente", {})
                        consultas = resultado.get("consultas", [])
                        self.guardar_datos_paciente(paciente)
                        self.guardar_datos_consultas(consultas)

                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                    time.sleep(3)
                    self.driver.save_screenshot(f"post_process_{paciente_index}.png")
                    print(f"✅ Procesamiento exitoso del paciente {nombre_paciente}")
                    return True

            except Exception as e:
                print(f"❌ Error en procesamiento posterior a clic: {str(e)}")
                try:
                    self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                    time.sleep(3)
                except:
                    pass
                return False

        except Exception as e:
            print(f"❌ Error al procesar paciente: {str(e)}")
            try:
                self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                time.sleep(3)
            except:
                pass
            return False

    def extraer_contenido_pdf_desde_navegador(self):
        try:
            print("📄 Extrayendo texto del PDF con JavaScript desde PDF.js...")
            texto_completo = self.driver.execute_async_script("""
                var callback = arguments[arguments.length - 1];
                let texto = "";

                (async () => {
                    try {
                        const pdf = window.PDFViewerApplication?.pdfDocument;
                        const totalPages = pdf.numPages;
                        for (let i = 1; i <= totalPages; i++) {
                            const page = await pdf.getPage(i);
                            const content = await page.getTextContent();
                            texto += content.items.map(item => item.str).join(" ") + "\n\n";
                        }
                        callback(texto);
                    } catch (err) {
                        callback("");
                    }
                })();
            """)

            if texto_completo and len(texto_completo.strip()) > 100:
                print("✅ Texto extraído del PDF correctamente")
                return texto_completo
            else:
                print("⚠️ El texto del PDF es muy corto o vacío")
                return ""
        except Exception as e:
            print(f"❌ Error extrayendo texto del PDF: {str(e)}")
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
        try:
            if not pdf_text.strip():
                print("⚠️ Texto vacío. No se puede procesar con OpenAI.")
                return None

            print("🧠 Enviando contenido textual a OpenAI para análisis...")
            from openai import OpenAI

            client = OpenAI()
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

            json_data = json.loads(respuesta)
            return json_data

        except Exception as e:
            print(f"❌ Error procesando con OpenAI: {str(e)}")
            return None
        
    def cerrar(self):
        print("👋 Cerrando navegador...")
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")
