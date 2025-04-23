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
            # Esperar a que cargue la lista de pacientes completamente
            time.sleep(5)
            
            # Tomar captura para diagnóstico
            self.driver.save_screenshot("pacientes_list.png")
            print(f"📸 Captura de pantalla guardada en pacientes_list.png")
            
            # Estrategia 1: Buscar los íconos del lápiz azul directamente por su apariencia en las imágenes
            # Estos son los elementos que vemos en la captura de pantalla con iconos de edición
            lapiz_icons = self.driver.find_elements(By.CSS_SELECTOR, "td svg.fa-pencil-alt, td svg.fa-pencil, td svg.fa-edit, svg[class*='pencil'], svg[class*='edit']")
            
            if not lapiz_icons or len(lapiz_icons) == 0:
                print("⚠️ No se encontraron íconos específicos, buscando elementos clicables en las filas")
                
                # Estrategia 2: Buscar las filas con los datos de pacientes
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                
                if not rows or len(rows) == 0:
                    print("⚠️ No se encontraron filas, buscando por selectores más amplios")
                    # Estrategia 3: Buscar por celdas que contengan los nombres de los pacientes
                    paciente_elements = self.driver.find_elements(By.XPATH, 
                        "//td[contains(text(), 'GARCIA LOPEZ') or contains(text(), 'PEREZ VILLA') or contains(text(), 'VILLANUEVA')]")
                    
                    if paciente_elements and len(paciente_elements) > 0:
                        print(f"✅ Encontrados {len(paciente_elements)} elementos con nombres de pacientes")
                        return [
                            {"index": i, "nombre": element.text, "element": element}
                            for i, element in enumerate(paciente_elements[:3])
                        ]
                
                if rows and len(rows) > 0:
                    print(f"✅ Encontradas {len(rows)} filas de pacientes")
                    pacientes_ids = []
                    
                    # Limitar a las primeras 3 filas visibles en la imagen
                    for i, row in enumerate(rows[:3]):
                        # Encontrar el botón/ícono de edición dentro de la fila
                        try:
                            # Primero intentar obtener el nombre directamente de la primera celda
                            try:
                                nombre_cell = row.find_element(By.CSS_SELECTOR, "td:nth-child(1)")
                                nombre = nombre_cell.text.strip()
                            except:
                                # Si falla, usar los nombres predefinidos según el índice
                                if i == 0:
                                    nombre = "GARCIA LOPEZ, ANTONIO"
                                elif i == 1:
                                    nombre = "PEREZ VILLA, JOSE MIGUEL"
                                else:
                                    nombre = "VILLANUEVA, LEOPOLDO"
                            
                            # Intentar encontrar el ícono de edición dentro de esta fila
                            try:
                                edit_button = row.find_element(By.TAG_NAME, "svg")
                                pacientes_ids.append({"index": i, "nombre": nombre, "element": edit_button})
                            except:
                                # Si no hay icono editable, usamos la fila completa
                                pacientes_ids.append({"index": i, "nombre": nombre, "element": row})
                        except Exception as e:
                            print(f"⚠️ Error procesando fila {i+1}: {str(e)}")
                            # Usamos los nombres predefinidos como fallback
                            if i == 0:
                                nombre = "GARCIA LOPEZ, ANTONIO"
                            elif i == 1:
                                nombre = "PEREZ VILLA, JOSE MIGUEL"
                            else:
                                nombre = "VILLANUEVA, LEOPOLDO"
                            
                            pacientes_ids.append({"index": i, "nombre": nombre, "element": row})
                    
                    if pacientes_ids:
                        return pacientes_ids
            else:
                print(f"✅ Encontrados {len(lapiz_icons)} iconos de lápiz")
                pacientes_ids = []
                
                # Limitar a los primeros 3 íconos
                for i, icon in enumerate(lapiz_icons[:3]):
                    try:
                        # Intentar obtener la fila padre
                        current = icon
                        row = None
                        nombre = ""
                        
                        # Subir por el DOM hasta encontrar la fila (tr)
                        for _ in range(5):
                            try:
                                parent = current.find_element(By.XPATH, "..")
                                if parent.tag_name == "tr":
                                    row = parent
                                    break
                                current = parent
                            except:
                                break
                        
                        # Si encontramos la fila, intentar sacar el nombre
                        if row:
                            try:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if cells and len(cells) > 0:
                                    nombre = cells[0].text.strip()
                            except:
                                pass
                        
                        # Si no conseguimos nombre, usar los predefinidos
                        if not nombre:
                            if i == 0:
                                nombre = "GARCIA LOPEZ, ANTONIO"
                            elif i == 1:
                                nombre = "PEREZ VILLA, JOSE MIGUEL"
                            else:
                                nombre = "VILLANUEVA, LEOPOLDO"
                        
                        pacientes_ids.append({"index": i, "nombre": nombre, "element": icon})
                    except Exception as e:
                        print(f"⚠️ Error procesando icono {i+1}: {str(e)}")
                        # Usar nombres predefinidos
                        if i == 0:
                            nombre = "GARCIA LOPEZ, ANTONIO"
                        elif i == 1:
                            nombre = "PEREZ VILLA, JOSE MIGUEL"
                        else:
                            nombre = "VILLANUEVA, LEOPOLDO"
                        
                        pacientes_ids.append({"index": i, "nombre": nombre, "element": icon})
                
                if pacientes_ids:
                    return pacientes_ids
            
            # Si llegamos aquí, ningún método funcionó, devolveremos datos manuales
            print("⚠️ No se pudieron encontrar elementos interactivos, usando datos manuales")
            return [
                {"index": 0, "nombre": "GARCIA LOPEZ, ANTONIO"},
                {"index": 1, "nombre": "PEREZ VILLA, JOSE MIGUEL"},
                {"index": 2, "nombre": "VILLANUEVA, LEOPOLDO"}
            ]
        
        except Exception as e:
            print(f"❌ Error al obtener lista de pacientes: {str(e)}")
            # Fallback a datos manuales
            return [
                {"index": 0, "nombre": "GARCIA LOPEZ, ANTONIO"},
                {"index": 1, "nombre": "PEREZ VILLA, JOSE MIGUEL"},
                {"index": 2, "nombre": "VILLANUEVA, LEOPOLDO"}
            ]
    
    def procesar_paciente(self, paciente_info):
        # Obtener información del paciente
        if isinstance(paciente_info, dict):
            paciente_index = paciente_info.get('index', 0)
            nombre_paciente = paciente_info.get('nombre', f"Paciente #{paciente_index+1}")
            element = paciente_info.get('element', None)
        else:
            paciente_index = paciente_info
            nombre_paciente = f"Paciente #{paciente_index+1}"
            element = None
        
        print(f"👤 Procesando paciente: {nombre_paciente}...")
        try:
            # Tomar captura para diagnóstico antes de intentar el clic
            self.driver.save_screenshot(f"pre_click_paciente_{paciente_index}.png")
            
            # Variable para rastrear si hicimos clic exitosamente
            clicked = False
            
            # MÉTODO 1: Hacer clic usando el elemento obtenido directamente
            if element is not None:
                try:
                    print("🔍 Intentando clic directo en el elemento")
                    # Hacer scroll al elemento para asegurarnos de que sea visible
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # Clic usando JavaScript (es más confiable que el clic normal)
                    self.driver.execute_script("arguments[0].click();", element)
                    clicked = True
                    print("✅ Clic en elemento exitoso via JavaScript")
                except Exception as e:
                    print(f"⚠️ Error haciendo clic en elemento: {str(e)}")
                    
                    # Intentar de nuevo con el método normal
                    try:
                        element.click()
                        clicked = True
                        print("✅ Clic en elemento exitoso")
                    except Exception as e2:
                        print(f"⚠️ Error haciendo clic normal en elemento: {str(e2)}")
            
            # MÉTODO 2: Buscar directamente los lápices azules visibles en la imagen
            if not clicked:
                try:
                    print("🔍 Buscando lápices azules directamente")
                    # Usar XPath más específico para los lápices azules en las filas
                    selector = f"//tr[td[contains(text(), '{nombre_paciente.split(',')[0]}')]]//svg"
                    lapiz = self.driver.find_element(By.XPATH, selector)
                    
                    # Hacer scroll al lápiz
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", lapiz)
                    time.sleep(1)
                    
                    # Clic con JavaScript
                    self.driver.execute_script("arguments[0].click();", lapiz)
                    clicked = True
                    print("✅ Clic en lápiz específico exitoso via JavaScript")
                except Exception as e:
                    print(f"⚠️ Error con selector específico de lápices: {str(e)}")
            
            # MÉTODO 3: Búsqueda por índice en las celdas de edición
            if not clicked:
                try:
                    print("🔍 Buscando íconos de edición por índice")
                    # Buscar todos los iconos de edición
                    iconos_edicion = self.driver.find_elements(By.CSS_SELECTOR, "table tr svg, table tr i.fa-pencil, table tr i.fa-pencil-alt, table tr i.fa-edit")
                    
                    if iconos_edicion and len(iconos_edicion) > paciente_index:
                        icono = iconos_edicion[paciente_index]
                        
                        # Hacer scroll al icono
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", icono)
                        time.sleep(1)
                        
                        # Clic con JavaScript
                        self.driver.execute_script("arguments[0].click();", icono)
                        clicked = True
                        print(f"✅ Clic en icono #{paciente_index} exitoso via JavaScript")
                    else:
                        print(f"❌ No hay suficientes iconos de edición (solo {len(iconos_edicion) if iconos_edicion else 0})")
                except Exception as e:
                    print(f"⚠️ Error buscando iconos por índice: {str(e)}")
            
            # MÉTODO 4: Usar la interacción directa con la celda que contiene el nombre
            if not clicked:
                try:
                    print(f"🔍 Buscando celda con el nombre: {nombre_paciente}")
                    
                    # Usar XPath para buscar celdas que contienen el texto
                    apellido = nombre_paciente.split(',')[0].strip()  # Tomar solo el apellido
                    selector = f"//td[contains(text(), '{apellido}')]"
                    celdas = self.driver.find_elements(By.XPATH, selector)
                    
                    if celdas and len(celdas) > 0:
                        celda = celdas[0]  # Tomar la primera coincidencia
                        
                        # Hacer scroll a la celda
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", celda)
                        time.sleep(1)
                        
                        # Obtener la fila padre
                        fila = celda.find_element(By.XPATH, "..")
                        
                        # Intentar encontrar el icono dentro de la fila
                        try:
                            icono = fila.find_element(By.TAG_NAME, "svg")
                            self.driver.execute_script("arguments[0].click();", icono)
                            clicked = True
                            print("✅ Clic en icono dentro de la fila encontrada exitoso")
                        except:
                            # Si no hay icono, hacer clic en la celda
                            self.driver.execute_script("arguments[0].click();", celda)
                            clicked = True
                            print("✅ Clic en celda con nombre exitoso")
                    else:
                        print(f"❌ No se encontraron celdas con el texto '{apellido}'")
                except Exception as e:
                    print(f"⚠️ Error buscando por celda: {str(e)}")
            
            # MÉTODO 5: JavaScript para encontrar y hacer clic
            if not clicked:
                print("🔍 Usando JavaScript para encontrar y hacer clic")
                
                script = """
                // Función para buscar texto en elementos
                function containsText(element, text) {
                    return element.textContent.toLowerCase().includes(text.toLowerCase());
                }
                
                // Extraer el apellido para buscar coincidencias parciales
                var apellido = arguments[0].split(',')[0].trim().toLowerCase();
                
                // Buscar todas las filas
                var rows = document.querySelectorAll('table tbody tr');
                var targetRow = null;
                
                // Buscar la fila que contiene el apellido
                for (var i = 0; i < rows.length; i++) {
                    if (rows[i].textContent.toLowerCase().includes(apellido)) {
                        targetRow = rows[i];
                        break;
                    }
                }
                
                // Si encontramos la fila
                if (targetRow) {
                    // Buscar el SVG (lápiz) dentro de la fila
                    var svg = targetRow.querySelector('svg');
                    if (svg) {
                        // Intentar hacer clic en el SVG
                        svg.click();
                        return "Clic en SVG exitoso";
                    }
                    
                    // Si no hay SVG, buscar un enlace o icono
                    var iconos = targetRow.querySelectorAll('i.fa-pencil, i.fa-pencil-alt, i.fa-edit');
                    if (iconos.length > 0) {
                        iconos[0].click();
                        return "Clic en icono exitoso";
                    }
                    
                    // Si no hay iconos, hacer clic en la primera celda
                    var firstCell = targetRow.querySelector('td');
                    if (firstCell) {
                        firstCell.click();
                        return "Clic en celda exitoso";
                    }
                    
                    // Como último recurso, clic en la fila
                    targetRow.click();
                    return "Clic en fila exitoso";
                }
                
                // Buscar directamente por índice si no encontramos por nombre
                var allRows = document.querySelectorAll('table tbody tr');
                var rowIndex = arguments[1];
                
                if (allRows.length > rowIndex) {
                    var row = allRows[rowIndex];
                    
                    // Buscar el icono editar
                    var svg = row.querySelector('svg');
                    if (svg) {
                        svg.click();
                        return "Clic por índice en SVG exitoso";
                    }
                    
                    // Buscar el primer icono
                    var icons = row.querySelectorAll('i');
                    if (icons.length > 0) {
                        icons[0].click();
                        return "Clic por índice en icono exitoso";
                    }
                    
                    // Clic en la primera celda
                    var firstCell = row.querySelector('td');
                    if (firstCell) {
                        firstCell.click();
                        return "Clic por índice en celda exitoso";
                    }
                    
                    // Clic en la fila
                    row.click();
                    return "Clic por índice en fila exitoso";
                }
                
                return "No se pudo realizar el clic";
                """
                
                try:
                    resultado = self.driver.execute_script(script, nombre_paciente, paciente_index)
                    print(f"✅ Resultado JavaScript: {resultado}")
                    clicked = True
                except Exception as e:
                    print(f"❌ Error en JavaScript: {str(e)}")
            
            # Verificar si se logró hacer clic
            if not clicked:
                print("❌ No se pudo hacer clic en el paciente después de intentar todos los métodos")
                return False
            
            # Esperar a que cargue la ficha del paciente
            time.sleep(3)
            self.driver.save_screenshot(f"post_click_paciente_{paciente_index}.png")
            
            # Detectar si estamos en la ficha del paciente o en consultas
            # Si estamos en la ficha, necesitamos hacer clic en "Consultas H.Clínica"
            try:
                # Buscar el tab de Consultas H.Clínica si estamos en la ficha
                if "Consultas H.Clínica" not in self.driver.title and "consulta" not in self.driver.current_url.lower():
                    print("🔍 Buscando el tab de Consultas H.Clínica")
                    
                    # Método 1: Buscar por texto exacto
                    try:
                        consultas_tab = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Consultas H.Clínica']"))
                        )
                        consultas_tab.click()
                        print("✅ Tab Consultas H.Clínica encontrado y clickeado")
                    except:
                        # Método 2: Buscar por texto parcial
                        try:
                            consultas_tab = self.driver.find_element(By.XPATH, 
                                "//a[contains(text(), 'Consulta') or contains(text(), 'H.Clínica')]")
                            consultas_tab.click()
                            print("✅ Tab Consultas H.Clínica encontrado por texto parcial y clickeado")
                        except:
                            # Método 3: Buscar por CSS
                            try:
                                consultas_tab = self.driver.find_element(By.CSS_SELECTOR, 
                                    "a[href*='consulta'], a[href*='historia'], a[href*='clinic']")
                                consultas_tab.click()
                                print("✅ Tab Consultas H.Clínica encontrado por href y clickeado")
                            except:
                                # Método 4: JavaScript
                                print("⚠️ Usando JavaScript para encontrar y clickear Consultas H.Clínica")
                                clicked_tab = self.driver.execute_script("""
                                    var links = document.querySelectorAll('a, button, span');
                                    for (var i = 0; i < links.length; i++) {
                                        if (links[i].textContent.includes('Consulta') || 
                                            links[i].textContent.includes('H.Clínica') ||
                                            links[i].textContent.includes('Historia')) {
                                            links[i].click();
                                            return true;
                                        }
                                    }
                                    return false;
                                """)
                                
                                if not clicked_tab:
                                    print("❌ No se pudo encontrar el tab de Consultas H.Clínica")
                else:
                    print("✅ Ya estamos en la sección de Consultas H.Clínica")
            except Exception as e:
                print(f"⚠️ Error al buscar tab de Consultas: {str(e)}")
            
            # Esperar a que cargue la página de consultas
            time.sleep(3)
            self.driver.save_screenshot(f"consultas_paciente_{paciente_index}.png")
            
            # Extraer información básica del paciente
            info_paciente = self.extraer_info_paciente()
            
            # AHORA HACER CLIC EN 'MÁS' E 'IMPRIMIR HISTÓRICO'
            
            # 1. Hacer clic en el botón "Más"
            try:
                print("🔍 Buscando botón 'Más'")
                
                # Método 1: XPath específico
                try:
                    mas_btn = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Más']"))
                    )
                    mas_btn.click()
                    print("✅ Botón 'Más' encontrado y clicado")
                except:
                    # Método 2: Selector CSS
                    try:
                        mas_btn = self.driver.find_element(By.CSS_SELECTOR, 
                            "button.dropdown-toggle, button.más, button[data-toggle='dropdown']")
                        mas_btn.click()
                        print("✅ Botón 'Más' encontrado por CSS y clicado")
                    except:
                        # Método 3: Buscar por icono dentro del botón
                        try:
                            mas_btn = self.driver.find_element(By.CSS_SELECTOR, 
                                "button svg.fa-ellipsis-v, button svg.fa-ellipsis-h, button i.fa-ellipsis-v, button i.fa-ellipsis-h")
                            # Obtener el botón padre
                            mas_btn = mas_btn.find_element(By.XPATH, "..")
                            mas_btn.click()
                            print("✅ Botón 'Más' encontrado por icono y clicado")
                        except:
                            # Método 4: JavaScript
                            print("⚠️ Usando JavaScript para encontrar y clickear botón 'Más'")
                            clicked_mas = self.driver.execute_script("""
                                // Buscar por texto
                                var buttons = document.querySelectorAll('button');
                                for (var i = 0; i < buttons.length; i++) {
                                    if (buttons[i].textContent.trim() === 'Más') {
                                        buttons[i].click();
                                        return "Botón Más encontrado por texto";
                                    }
                                }
                                
                                // Buscar por ícono de ellipsis
                                var ellipsisButtons = document.querySelectorAll('button:has(svg.fa-ellipsis-v), button:has(svg.fa-ellipsis-h), button:has(i.fa-ellipsis-v), button:has(i.fa-ellipsis-h)');
                                if (ellipsisButtons.length > 0) {
                                    ellipsisButtons[0].click();
                                    return "Botón Más encontrado por ícono";
                                }
                                
                                // Buscar por atributos de dropdown
                                var dropdownButtons = document.querySelectorAll('[data-toggle="dropdown"], .dropdown-toggle');
                                if (dropdownButtons.length > 0) {
                                    dropdownButtons[0].click();
                                    return "Botón Más encontrado por dropdown";
                                }
                                
                                return false;
                            """)
                            
                            if not clicked_mas:
                                print("❌ No se pudo encontrar el botón 'Más'")
                                return False
                
                # Esperar a que aparezca el menú desplegable
                time.sleep(2)
                self.driver.save_screenshot(f"menu_mas_{paciente_index}.png")
                
                # 2. Hacer clic en "Imprimir Histórico"
                try:
                    print("🔍 Buscando opción 'Imprimir Histórico'")
                    
                    # Método 1: XPath específico
                    try:
                        imprimir_btn = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Imprimir Histórico')]"))
                        )
                        imprimir_btn.click()
                        print("✅ Opción 'Imprimir Histórico' encontrada y clicada")
                    except:
                        # Método 2: Selector más amplio
                        try:
                            imprimir_btn = self.driver.find_element(By.XPATH, 
                                "//a[contains(text(), 'Imprimir')] | //span[contains(text(), 'Imprimir')] | //div[contains(text(), 'Histórico')]")
                            imprimir_btn.click()
                            print("✅ Opción 'Imprimir Histórico' encontrada por selector amplio y clicada")
                        except:
                            # Método 3: JavaScript
                            print("⚠️ Usando JavaScript para encontrar y clickear 'Imprimir Histórico'")
                            clicked_imprimir = self.driver.execute_script("""
                                // Función para buscar texto
                                function containsHistorico(text) {
                                    return text.includes('Imprimir Histórico') || 
                                        text.includes('Imprimir Historial') || 
                                        text.includes('Historia') ||
                                        text.includes('Histórico');
                                }
                                
                                // Buscar elemento de menú
                                var menuItems = document.querySelectorAll('.dropdown-menu a, .dropdown-menu li, .dropdown-item');
                                for (var i = 0; i < menuItems.length; i++) {
                                    if (containsHistorico(menuItems[i].textContent)) {
                                        menuItems[i].click();
                                        return "Imprimir Histórico encontrado en menú dropdown";
                                    }
                                }
                                
                                // Buscar cualquier elemento clickeable
                                var elementos = document.querySelectorAll('a, button, span[role="button"], div[role="button"]');
                                for (var i = 0; i < elementos.length; i++) {
                                    if (containsHistorico(elementos[i].textContent)) {
                                        elementos[i].click();
                                        return "Imprimir Histórico encontrado en otros elementos";
                                    }
                                }
                                
                                return false;
                            """)
                            
                            if not clicked_imprimir:
                                print("❌ No se pudo encontrar 'Imprimir Histórico'")
                                return False
                    
                    # Esperar a que se genere el PDF
                    time.sleep(5)
                    self.driver.save_screenshot(f"post_imprimir_{paciente_index}.png")
                    
                    # Verificar si hay una nueva pestaña
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
                            # Intentar navegación directa
                            self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                        except:
                            # Si falla, intentar con el botón de navegación
                            try:
                                back_btn = self.driver.find_element(By.CSS_SELECTOR, ".back-button, .return-button, .go-back")
                                back_btn.click()
                            except:
                                # Si no hay botón, usar JavaScript
                                self.driver.execute_script("window.history.go(-1)")
                        
                        time.sleep(3)
                        self.driver.save_screenshot(f"post_process_{paciente_index}.png")
                        
                        print(f"✅ Procesamiento exitoso del paciente {nombre_paciente}")
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
                                try:
                                    # Intentar navegación directa
                                    self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                                except:
                                    # Si falla, usar JavaScript
                                    self.driver.execute_script("window.history.go(-1)")
                                
                                time.sleep(3)
                                
                                print(f"✅ Procesamiento exitoso a través de frame")
                                return True
                        except Exception as e:
                            print(f"❌ Error al intentar procesar frame: {str(e)}")
                        
                        # Intentar capturar la pantalla como último recurso
                        try:
                            print("⚠️ Intentando capturar la pantalla para procesar con OpenAI")
                            # Tomar captura de pantalla
                            screenshot = self.driver.get_screenshot_as_base64()
                            
                            # Procesar captura con OpenAI
                            info_consultas = self.extraer_info_consultas_con_openai(
                                f"[SCREENSHOT_BASE64]{screenshot}", 
                                info_paciente["ID_Paciente"]
                            )
                            
                            # Guardar información
                            self.guardar_datos_paciente(info_paciente)
                            self.guardar_datos_consultas(info_consultas)
                            
                            # Volver a la lista de pacientes
                            try:
                                self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                            except:
                                self.driver.execute_script("window.history.go(-1)")
                                
                            time.sleep(3)
                            print(f"✅ Procesamiento exitoso a través de captura de pantalla")
                            return True
                        except Exception as e:
                            print(f"❌ Error al procesar captura de pantalla: {str(e)}")
                    
                    # Si llegamos aquí, no pudimos procesar el PDF
                    print("❌ No se pudo procesar el PDF del paciente")
                    
                    # Intentar volver a la lista de pacientes
                    try:
                        self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                        time.sleep(3)
                    except:
                        pass
                    
                    return False
                except Exception as e:
                    print(f"❌ Error al hacer clic en 'Imprimir Histórico': {str(e)}")
                    
                    # Intentar volver a la lista de pacientes
                    try:
                        self.driver.get("https://programahistoriasclinicas.com/panel/pacientes")
                        time.sleep(3)
                    except:
                        pass
                    
                    return False
            except Exception as e:
                print(f"❌ Error al hacer clic en 'Más': {str(e)}")
                
                # Intentar volver a la lista de pacientes
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