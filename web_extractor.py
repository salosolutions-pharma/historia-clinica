import os
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
            time.sleep(5)  # Esperamos más tiempo para que cargue completamente
            
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
                
                time.sleep(5)
                
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
            time.sleep(5)
            
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
                            time.sleep(5)
            
            # Si encontramos el botón con los métodos 1-3, hacer clic
            if 'pacientes_btn' in locals():
                pacientes_btn.click()
            
            # Esperar a que cargue la página de pacientes
            time.sleep(5)
            
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
                time.sleep(5)
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
        print("📋 Obteniendo lista de pacientes...")
        try:
            # Esperar a que cargue la lista de pacientes
            time.sleep(5)
            
            # Tomar captura para diagnóstico
            self.driver.save_screenshot("pacientes_list.png")
            print(f"📸 Captura de pantalla guardada en pacientes_list.png")
            
            # Intentar diferentes selectores para encontrar las filas de pacientes
            pacientes_ids = []
            
            # Método 1: Selector de tabla estándar
            try:
                pacientes = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                if pacientes and len(pacientes) > 0:
                    print(f"✅ Encontrados {len(pacientes)} pacientes con selector de tabla estándar")
                    
                    for i, paciente in enumerate(pacientes):
                        try:
                            nombre = paciente.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                            pacientes_ids.append({"index": i, "nombre": nombre})
                        except:
                            continue
                else:
                    print("❌ No se encontraron filas con selector de tabla estándar")
            except Exception as e:
                print(f"⚠️ Error con selector estándar: {str(e)}")
            
            # Método 2: Buscar por íconos de edición
            if not pacientes_ids:
                try:
                    edit_icons = self.driver.find_elements(By.CSS_SELECTOR, "a.editar, .icon-edit, svg[name='edit'], .edit-button")
                    if edit_icons and len(edit_icons) > 0:
                        print(f"✅ Encontrados {len(edit_icons)} iconos de edición")
                        
                        # Para cada icono, encontrar el nombre del paciente asociado
                        for i, icon in enumerate(edit_icons):
                            try:
                                # Intentar encontrar el nombre en la fila padre
                                row = icon.find_element(By.XPATH, "./ancestor::tr")
                                nombre = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                                pacientes_ids.append({"index": i, "nombre": nombre})
                            except:
                                # Si falla, usar un índice genérico
                                pacientes_ids.append({"index": i, "nombre": f"Paciente {i+1}"})
                    else:
                        print("❌ No se encontraron iconos de edición")
                except Exception as e:
                    print(f"⚠️ Error buscando iconos de edición: {str(e)}")
            
            # Método 3: Usar JavaScript para encontrar las filas de pacientes
            if not pacientes_ids:
                print("⚠️ Usando JavaScript para encontrar pacientes")
                try:
                    pacientes_js = self.driver.execute_script("""
                        var rows = [];
                        
                        // Buscar filas de tabla con contenido
                        var tableRows = document.querySelectorAll('table tr');
                        for(var i=0; i<tableRows.length; i++) {
                            if(tableRows[i].children.length > 1 && tableRows[i].textContent.trim() != '') {
                                rows.push({
                                    index: i,
                                    nombre: tableRows[i].children[0] ? tableRows[i].children[0].textContent.trim() : 'Nombre no encontrado'
                                });
                            }
                        }
                        
                        // Si no hay filas, buscar divs que podrían ser filas
                        if(rows.length === 0) {
                            var divRows = document.querySelectorAll('.row-patient, .patient-item, div[role="row"]');
                            for(var i=0; i<divRows.length; i++) {
                                rows.push({
                                    index: i,
                                    nombre: divRows[i].textContent.trim().split('\\n')[0] || 'Paciente ' + (i+1)
                                });
                            }
                        }
                        
                        return rows;
                    """)
                    
                    if pacientes_js and len(pacientes_js) > 0:
                        print(f"✅ Encontrados {len(pacientes_js)} pacientes con JavaScript")
                        pacientes_ids = pacientes_js
                    else:
                        print("❌ No se encontraron pacientes con JavaScript")
                except Exception as e:
                    print(f"⚠️ Error en JavaScript: {str(e)}")
            
            # Método 4: Buscar directamente los lápices de edición
            if not pacientes_ids:
                try:
                    edit_pencils = self.driver.find_elements(By.CSS_SELECTOR, "svg[stroke='currentColor'], .pencil-icon, .edit-icon, .fa-pencil")
                    if edit_pencils and len(edit_pencils) > 0:
                        print(f"✅ Encontrados {len(edit_pencils)} iconos de lápiz")
                        
                        for i in range(len(edit_pencils)):
                            pacientes_ids.append({"index": i, "nombre": f"Paciente {i+1}"})
                    else:
                        print("❌ No se encontraron iconos de lápiz")
                except Exception as e:
                    print(f"⚠️ Error buscando iconos de lápiz: {str(e)}")
            
            # Verificar si encontramos pacientes
            if pacientes_ids:
                print(f"✅ Se encontraron {len(pacientes_ids)} pacientes")
                return pacientes_ids
            else:
                # Último recurso: generar datos ficticios solo para depuración
                print("⚠️ No se encontraron pacientes, generando entrada manual para depuración")
                debug_pacientes = [
                    {"index": 0, "nombre": "GARCIA LOPEZ, ANTONIO"},
                    {"index": 1, "nombre": "PEREZ VILLA, JOSE MIGUEL"},
                    {"index": 2, "nombre": "VILLANUEVA, LEOPOLDO"}
                ]
                return debug_pacientes
                
        except Exception as e:
            print(f"❌ Error al obtener lista de pacientes: {str(e)}")
            return []
    
    def procesar_paciente(self, paciente_index):
        print(f"👤 Procesando paciente #{paciente_index+1}...")
        try:
            # Tomar captura para diagnóstico
            self.driver.save_screenshot(f"pre_click_paciente_{paciente_index}.png")
            
            # Métodos para hacer clic en el paciente
            clicked = False
            
            # Método 1: Intentar con el ícono de editar (lápiz)
            try:
                edit_icons = self.driver.find_elements(By.CSS_SELECTOR, "a.editar, .icon-edit, svg[name='edit'], .edit-button, svg[stroke='currentColor'], .pencil-icon, .edit-icon, .fa-pencil")
                if paciente_index < len(edit_icons):
                    edit_icon = edit_icons[paciente_index]
                    nombre_paciente = f"Paciente #{paciente_index+1}"
                    
                    # Intentar obtener el nombre del paciente
                    try:
                        row = edit_icon.find_element(By.XPATH, "./ancestor::tr")
                        nombre_paciente = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                    except:
                        pass
                    
                    print(f"🔍 Accediendo a datos de: {nombre_paciente}")
                    edit_icon.click()
                    clicked = True
                else:
                    print("❌ Índice de ícono de edición fuera de rango")
            except Exception as e:
                print(f"⚠️ Error haciendo clic en ícono de edición: {str(e)}")
            
            # Método 2: Hacer clic en la fila de la tabla
            if not clicked:
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    if paciente_index < len(rows):
                        row = rows[paciente_index]
                        nombre_paciente = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                        print(f"🔍 Accediendo a datos de: {nombre_paciente}")
                        
                        # Intentar hacer clic en cualquier enlace dentro de la fila
                        try:
                            row.find_element(By.TAG_NAME, "a").click()
                            clicked = True
                        except:
                            # Si no hay enlaces, hacer clic en la fila
                            row.click()
                            clicked = True
                    else:
                        print("❌ Índice de fila fuera de rango")
                except Exception as e:
                    print(f"⚠️ Error haciendo clic en fila: {str(e)}")
            
            # Método 3: JavaScript como último recurso
            if not clicked:
                print("⚠️ Usando JavaScript para hacer clic en el paciente")
                try:
                    clicked = self.driver.execute_script(f"""
                        var rows = document.querySelectorAll('table tbody tr');
                        if(rows.length > {paciente_index}) {{
                            rows[{paciente_index}].click();
                            return true;
                        }}
                        
                        var editIcons = document.querySelectorAll('a.editar, .icon-edit, svg[name="edit"], .edit-button, svg[stroke="currentColor"], .pencil-icon, .edit-icon, .fa-pencil');
                        if(editIcons.length > {paciente_index}) {{
                            editIcons[{paciente_index}].click();
                            return true;
                        }}
                        
                        return false;
                    """)
                except Exception as e:
                    print(f"⚠️ Error en JavaScript para clic: {str(e)}")
            
            if not clicked:
                print("❌ No se pudo hacer clic en ningún paciente")
                return False
                
            # Esperar a que cargue la ficha del paciente
            time.sleep(5)
            self.driver.save_screenshot(f"post_click_paciente_{paciente_index}.png")
            
            # Intentar encontrar el enlace a Consultas H.Clínica
            try:
                # Método 1: XPATH
                consultas_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Consultas H.Clínica')]"))
                )
                print("✅ Enlace a Consultas H.Clínica encontrado con XPATH")
            except:
                try:
                    # Método 2: CSS Selector
                    consultas_btn = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='consultas'], a[href*='histo'], a[href*='clinic']"))
                    )
                    print("✅ Enlace a Consultas H.Clínica encontrado con CSS")
                except:
                    try:
                        # Método 3: JavaScript
                        print("⚠️ Usando JavaScript para encontrar Consultas H.Clínica")
                        self.driver.execute_script("""
                            var links = document.querySelectorAll('a');
                            for(var i=0; i<links.length; i++) {
                                if(links[i].textContent.includes('Consulta') || 
                                links[i].textContent.includes('Historia') || 
                                links[i].textContent.includes('Clínica') ||
                                links[i].href.includes('consulta') ||
                                links[i].href.includes('historia')) {
                                    links[i].click();
                                    return true;
                                }
                            }
                            return false;
                        """)
                        time.sleep(3)
                        self.driver.save_screenshot(f"post_consultas_click_{paciente_index}.png")
                    except Exception as e:
                        print(f"❌ No se pudo encontrar enlace a Consultas H.Clínica: {str(e)}")
                        return False
            
            # Si encontramos el botón con los métodos 1-2, hacer clic
            if 'consultas_btn' in locals():
                consultas_btn.click()
                time.sleep(3)
                self.driver.save_screenshot(f"post_consultas_click_{paciente_index}.png")
            
            # Extraer información básica del paciente
            info_paciente = self.extraer_info_paciente()
            
            # Hacer clic en el botón "Más"
            try:
                mas_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Más')]"))
                )
                mas_btn.click()
                print("✅ Botón 'Más' encontrado y clicado")
            except:
                try:
                    # Intentar con CSS
                    mas_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-mas, .more-options, .menu-more")
                    mas_btn.click()
                    print("✅ Botón 'Más' encontrado con CSS y clicado")
                except:
                    # Intentar con JavaScript
                    print("⚠️ Usando JavaScript para encontrar botón 'Más'")
                    clicked = self.driver.execute_script("""
                        var buttons = document.querySelectorAll('button');
                        for(var i=0; i<buttons.length; i++) {
                            if(buttons[i].textContent.includes('Más') || 
                            buttons[i].classList.contains('btn-mas') ||
                            buttons[i].classList.contains('more')) {
                                buttons[i].click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    if not clicked:
                        print("❌ No se pudo encontrar el botón 'Más'")
                        return False
            
            time.sleep(2)
            self.driver.save_screenshot(f"post_mas_click_{paciente_index}.png")
            
            # Hacer clic en "Imprimir Histórico"
            try:
                imprimir_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Imprimir Histórico')]"))
                )
                imprimir_btn.click()
                print("✅ Opción 'Imprimir Histórico' encontrada y clicada")
            except:
                try:
                    # Intentar con CSS
                    imprimir_btn = self.driver.find_element(By.CSS_SELECTOR, ".print-history, .imprimir-historico")
                    imprimir_btn.click()
                    print("✅ Opción 'Imprimir Histórico' encontrada con CSS y clicada")
                except:
                    # Intentar con JavaScript
                    print("⚠️ Usando JavaScript para encontrar 'Imprimir Histórico'")
                    clicked = self.driver.execute_script("""
                        var elements = document.querySelectorAll('a, button, span, div');
                        for(var i=0; i<elements.length; i++) {
                            if(elements[i].textContent.includes('Imprimir Histórico') || 
                            elements[i].textContent.includes('Imprimir historial') ||
                            elements[i].textContent.includes('Print history')) {
                                elements[i].click();
                                return true;
                            }
                        }
                        return false;
                    """)
                    if not clicked:
                        print("❌ No se pudo encontrar 'Imprimir Histórico'")
                        return False
            
            # Esperar a que se genere el PDF en una nueva pestaña
            time.sleep(5)
            
            # Tomar captura antes de cambiar de pestaña
            self.driver.save_screenshot(f"pre_tab_switch_{paciente_index}.png")
            
            # Verificar si hay más de una pestaña
            if len(self.driver.window_handles) > 1:
                print(f"✅ Nueva pestaña detectada (total: {len(self.driver.window_handles)})")
                
                # Cambiar a la nueva pestaña
                self.driver.switch_to.window(self.driver.window_handles[1])
                time.sleep(3)
                
                # Tomar captura de la pestaña del PDF
                self.driver.save_screenshot(f"pdf_tab_{paciente_index}.png")
                
                # Extraer el contenido del PDF
                pdf_content = self.extraer_contenido_pdf_desde_navegador()
                
                # Procesar el contenido con OpenAI
                info_consultas = self.extraer_info_consultas_con_openai(pdf_content, info_paciente["ID_Paciente"])
                
                # Guardar información en DataFrames
                self.guardar_datos_paciente(info_paciente)
                self.guardar_datos_consultas(info_consultas)
                
                # Cerrar la pestaña del PDF y volver a la principal
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
                # Volver a la lista de pacientes
                try:
                    # Intentar con el botón de navegación
                    back_btn = self.driver.find_element(By.CSS_SELECTOR, ".back-button, .return-button, .go-back")
                    back_btn.click()
                except:
                    # Si no hay botón, usar JavaScript
                    self.driver.execute_script("window.history.go(-1)")
                
                time.sleep(3)
                self.driver.save_screenshot(f"post_process_{paciente_index}.png")
                
                print(f"✅ Procesamiento exitoso del paciente")
                return True
            else:
                print("⚠️ No se abrió ninguna pestaña nueva para el PDF")
                
                # Intentar buscar un frame con el PDF
                try:
                    frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                    if frames:
                        print(f"✅ Frame encontrado, intentando cambiar a él")
                        self.driver.switch_to.frame(frames[0])
                        
                        # Extraer contenido del frame
                        pdf_content = self.driver.find_element(By.TAG_NAME, "body").text
                        
                        # Volver al contenido principal
                        self.driver.switch_to.default_content()
                        
                        # Procesar con OpenAI
                        info_consultas = self.extraer_info_consultas_con_openai(pdf_content, info_paciente["ID_Paciente"])
                        
                        # Guardar información
                        self.guardar_datos_paciente(info_paciente)
                        self.guardar_datos_consultas(info_consultas)
                        
                        # Volver a la lista de pacientes
                        self.driver.execute_script("window.history.go(-1)")
                        time.sleep(3)
                        
                        print(f"✅ Procesamiento exitoso a través de frame")
                        return True
                except Exception as e:
                    print(f"❌ Error al intentar procesar frame: {str(e)}")
                
                # Si no se pudo procesar, intentar volver a la lista de pacientes
                try:
                    self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                    time.sleep(3)
                except:
                    pass
                
                return False
                    
        except Exception as e:
            print(f"❌ Error al procesar paciente: {str(e)}")
            # Intentar volver a la lista de pacientes
            try:
                self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                time.sleep(3)
            except:
                pass
            return False
    
    def extraer_info_paciente(self):
        """Extrae información básica del paciente desde la ficha"""
        try:
            # Esperar a que cargue la ficha
            time.sleep(2)
            
            # Extraer nombre del paciente del encabezado
            nombre_completo = self.driver.find_element(By.CSS_SELECTOR, ".cabecera-ficha h2").text
            
            # Extraer otros datos (esto puede variar según la estructura)
            # Intentar obtener fecha de nacimiento si está visible
            fecha_nacimiento = ""
            try:
                fecha_elemento = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Fecha nacimiento')]/following-sibling::div")
                fecha_nacimiento = fecha_elemento.text
            except:
                pass
                
            # Generar un ID único para el paciente (basado en su nombre)
            id_paciente = ''.join(filter(str.isalnum, nombre_completo)).lower()
            
            # Intentar obtener edad si está visible
            edad = ""
            try:
                edad_elemento = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Edad')]/following-sibling::div")
                edad = edad_elemento.text.replace("años", "").strip()
            except:
                pass
            
            return {
                "Paciente": nombre_completo,
                "Fecha": fecha_nacimiento,
                "ID_Paciente": id_paciente,
                "Edad": edad
            }
            
        except Exception as e:
            print(f"❌ Error al extraer información del paciente: {str(e)}")
            return {
                "Paciente": "Desconocido",
                "Fecha": "",
                "ID_Paciente": f"unknown_{int(time.time())}",
                "Edad": ""
            }
    
    def extraer_contenido_pdf_desde_navegador(self):
        """Extrae el contenido del PDF mostrado en el navegador"""
        try:
            # Esperar a que el PDF se cargue
            time.sleep(3)
            
            # Intentar capturar el PDF como texto
            pdf_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Si no hay texto significativo, intentar extraer con captura de pantalla
            if len(pdf_text.strip()) < 100:
                print("⚠️ El texto extraído del PDF es muy corto, se intentará capturar la pantalla")
                screenshot = self.driver.get_screenshot_as_base64()
                return f"[SCREENSHOT_BASE64]{screenshot}"
            
            return pdf_text
            
        except Exception as e:
            print(f"❌ Error al extraer contenido del PDF: {str(e)}")
            # Intentar tomar una captura de pantalla como alternativa
            try:
                screenshot = self.driver.get_screenshot_as_base64()
                return f"[SCREENSHOT_BASE64]{screenshot}"
            except:
                return "Error: No se pudo extraer el contenido del PDF"
    
    def extraer_info_consultas_con_openai(self, texto_pdf, id_paciente):
        """Utiliza OpenAI para extraer información estructurada de las consultas"""
        print("🧠 Procesando información con OpenAI...")
        
        # Verificar si el contenido es una captura de pantalla
        if texto_pdf.startswith("[SCREENSHOT_BASE64]"):
            # Extraer la imagen base64
            imagen_base64 = texto_pdf.replace("[SCREENSHOT_BASE64]", "")
            
            prompt = """
            Extrae la siguiente información de esta captura de pantalla de una historia clínica:
            - Número de consulta o fecha de la consulta
            - Información sobre tabaquismo (SI/NO)
            - Información sobre diabetes (SI/NO)
            - Valor de PSA (si existe)
            - Presión arterial (si existe)
            - Diagnóstico (si existe)
            - Tratamiento indicado (si existe)
            
            Organiza la información para cada consulta encontrada en formato JSON:
            [
                {
                    "No_Consulta": "fecha o número",
                    "Tabaquismo": "SI/NO",
                    "Diabetes": "SI/NO",
                    "PSA": "valor",
                    "Presion_Arterial": "valor",
                    "Diagnostico": "texto",
                    "Tratamiento": "texto"
                }
            ]
            """
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{imagen_base64}"
                            }}
                        ]}
                    ],
                    max_tokens=1500
                )
                
                content = response.choices[0].message.content
                
                # Intentar extraer JSON de la respuesta
                try:
                    # Buscar patrón de JSON en la respuesta
                    json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        consultas = json.loads(json_str)
                    else:
                        consultas = []
                        
                    # Añadir ID_Paciente a cada consulta
                    for consulta in consultas:
                        consulta["ID_Paciente"] = id_paciente
                        
                    return consultas
                except Exception as e:
                    print(f"❌ Error al procesar JSON de OpenAI: {str(e)}")
                    return []
                
            except Exception as e:
                print(f"❌ Error en la API de OpenAI: {str(e)}")
                return []
        else:
            # Procesar texto plano
            prompt = f"""
            Extrae la siguiente información de esta historia clínica:
            
            {texto_pdf[:4000]}  # Limitado a 4000 caracteres para no exceder límites de token
            
            Información a extraer para cada consulta encontrada:
            - Número de consulta o fecha de la consulta
            - Información sobre tabaquismo (SI/NO)
            - Información sobre diabetes (SI/NO)
            - Valor de PSA (si existe)
            - Presión arterial (si existe)
            - Diagnóstico (si existe)
            - Tratamiento indicado (si existe)
            
            Organiza la información para cada consulta encontrada en formato JSON:
            [
                {{
                    "No_Consulta": "fecha o número",
                    "Tabaquismo": "SI/NO",
                    "Diabetes": "SI/NO",
                    "PSA": "valor",
                    "Presion_Arterial": "valor",
                    "Diagnostico": "texto",
                    "Tratamiento": "texto"
                }}
            ]
            """
            
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1500
                )
                
                content = response.choices[0].message.content
                
                # Intentar extraer JSON de la respuesta
                try:
                    # Buscar patrón de JSON en la respuesta
                    json_match = re.search(r'(\[.*\])', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        consultas = json.loads(json_str)
                    else:
                        consultas = []
                        
                    # Añadir ID_Paciente a cada consulta
                    for consulta in consultas:
                        consulta["ID_Paciente"] = id_paciente
                        
                    return consultas
                except Exception as e:
                    print(f"❌ Error al procesar JSON de OpenAI: {str(e)}")
                    return []
                
            except Exception as e:
                print(f"❌ Error en la API de OpenAI: {str(e)}")
                return []
    
    def guardar_datos_paciente(self, info_paciente):
        """Guarda los datos del paciente en el DataFrame"""
        try:
            self.pacientes_df = pd.concat([
                self.pacientes_df, 
                pd.DataFrame([info_paciente])
            ], ignore_index=True)
            
            # Guardar CSV después de cada actualización
            self.pacientes_df.to_csv(self.pacientes_csv, index=False)
            print(f"✅ Datos del paciente guardados (Total: {len(self.pacientes_df)})")
        except Exception as e:
            print(f"❌ Error al guardar datos del paciente: {str(e)}")
    
    def guardar_datos_consultas(self, consultas):
        """Guarda los datos de consultas en el DataFrame"""
        try:
            if consultas:
                self.consultas_df = pd.concat([
                    self.consultas_df, 
                    pd.DataFrame(consultas)
                ], ignore_index=True)
                
                # Guardar CSV después de cada actualización
                self.consultas_df.to_csv(self.consultas_csv, index=False)
                print(f"✅ Datos de consultas guardados (Total: {len(self.consultas_df)})")
            else:
                print("⚠️ No se encontraron consultas para guardar")
        except Exception as e:
            print(f"❌ Error al guardar datos de consultas: {str(e)}")
    
    def cerrar(self):
        """Cierra el navegador y finaliza la extracción"""
        try:
            self.driver.quit()
            print("👋 Navegador cerrado correctamente")
        except:
            print("⚠️ Error al cerrar el navegador")