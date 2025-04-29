from selenium.webdriver.common.by import By  
from selenium import webdriver  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.chrome.options import Options  
from dotenv import load_dotenv  
import time, os, re, json, openai, base64
import xml.etree.ElementTree as ET  
from dicttoxml import dicttoxml
import PyPDF2
import requests
from bs4 import BeautifulSoup

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  

class HistoriasClinicasExtractor:
    def __init__(self, output_dir="C:\\Users\\salos\\Downloads\\historia_clinica\\datos_medifolios"):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--kiosk-printing')  # Impresión sin ventana

        # Preferencias para descargar PDFs
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": False  # No forzar descarga PDF
            }
        )
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Lista para almacenar información sobre los PDFs descargados
        self.pdfs_info = []

    def login(self, usuario, password):
        print(f"🔑 Iniciando sesión con usuario: {usuario}")
        self.driver.get("https://www.medifolios.net")

        # Click en botón INGRESO
        try:
            # Usando el selector más específico según el HTML proporcionado
            ingreso_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'server0medifolios.net') and contains(@class, 'block-menu')]"))
            )
            ingreso_btn.click()
            print("✅ Botón INGRESO clicado")
        except Exception as e:
            print(f"❌ Error clicando en INGRESO: {str(e)}")
            return False

        # Completar formulario de login
        try:
            usuario_input = self.wait.until(EC.presence_of_element_located((By.ID, "txt_usuario_login")))
            password_input = self.driver.find_element(By.ID, "txt_password_login")
            usuario_input.send_keys(usuario)
            password_input.send_keys(password)

            login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Ingresar')]")
            login_btn.click()
            print("✅ Formulario de login enviado")
            
            # Esperar a que cargue la página principal después del login
            time.sleep(5)
            return True
        except Exception as e:
            print(f"❌ Error en formulario de login: {str(e)}")
            return False

    def navegar_a_pacientes(self):
        try:
            # Click en menú Bienvenido (abre el menú)
            menu_bienvenido = self.wait.until(
                EC.element_to_be_clickable((By.ID, "OpenMenuMedifolios"))
            )
            menu_bienvenido.click()
            print("✅ Menú Bienvenido clicado")
            time.sleep(3)

            # Click en Pacientes (según el selector HTML proporcionado)
            try:
                # Primer intento con selector más específico
                pacientes_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'item_menu_board')]//a[contains(@href,'SALUD_HOME/paciente')]"))
                )
                pacientes_btn.click()
                print("✅ Sección pacientes abierta (selector específico)")
            except Exception as e:
                print(f"⚠️ Primer selector falló, intentando alternativa: {str(e)}")
                # Segundo intento con selector más genérico
                pacientes_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'SALUD_HOME/paciente')]"))
                )
                pacientes_btn.click()
                print("✅ Sección pacientes abierta (selector genérico)")
            time.sleep(5)  # Esperar más tiempo para que cargue la sección de pacientes
        except Exception as e:
            print(f"❌ Error navegando a pacientes: {str(e)}")

    def abrir_listado_pacientes(self):
        try:
            # Click en botón Listado Pacientes
            listado_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnListadoPacientes"))
            )
            listado_btn.click()
            print("✅ Listado de pacientes abierto")
            time.sleep(5)  # Esperar a que cargue el listado completo
        except Exception as e:
            print(f"❌ Error al abrir listado de pacientes: {str(e)}")
    
    def obtener_datos_paciente_actual(self):
        """Obtiene los datos del paciente que está actualmente abierto"""
        try:
            # Intentar obtener el nombre del paciente
            nombre_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(@class,'titulo_historia_paciente')]/span"))
            )
            nombre_paciente = nombre_element.text.strip()
            
            # Intentar obtener el ID/documento del paciente
            try:
                documento_element = self.driver.find_element(By.XPATH, "//span[contains(@class,'documento_paciente')]")
                documento = documento_element.text.strip()
                # Extraer solo números del documento
                documento = re.sub(r'[^0-9]', '', documento)
            except:
                documento = "ID_no_encontrado"
            
            print(f"📋 Paciente actual: {nombre_paciente} (ID: {documento})")
            return {
                "nombre": nombre_paciente,
                "id": documento
            }
        except Exception as e:
            print(f"⚠️ No se pudieron obtener datos del paciente: {str(e)}")
            return {"nombre": "Desconocido", "id": "Desconocido"}
    
    def seleccionar_paciente_por_indice(self, indice=0):
        """Selecciona un paciente del listado por su índice (0 es el primero)"""
        try:
            # Buscar todos los botones de editar pacientes
            botones_editar = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "btnCodPacienteListado"))
            )
            
            if not botones_editar or len(botones_editar) <= indice:
                print(f"⚠️ No hay suficientes pacientes en la lista (se encontraron {len(botones_editar)})")
                return False
            
            # Obtener el botón del paciente en el índice deseado
            boton_paciente = botones_editar[indice]
            
            # Obtener datos del paciente antes de hacer clic
            fila_paciente = boton_paciente.find_element(By.XPATH, "./ancestor::tr")
            celdas = fila_paciente.find_elements(By.TAG_NAME, "td")
            
            id_paciente = "Desconocido"
            nombre_paciente = "Desconocido"
            
            if len(celdas) > 1:
                id_paciente = celdas[1].get_attribute("title") if celdas[1].get_attribute("title") else "Desconocido"
            
            if len(celdas) > 3:
                nombre_paciente = celdas[3].get_attribute("title") if celdas[3].get_attribute("title") else "Desconocido"
            
            # Hacer clic en el botón del paciente
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_paciente)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", boton_paciente)
            print(f"✅ Paciente #{indice+1} seleccionado: {nombre_paciente} (ID: {id_paciente})")
            time.sleep(3)
            
            return {"id": id_paciente, "nombre": nombre_paciente}
            
        except Exception as e:
            print(f"❌ Error al seleccionar paciente por índice {indice}: {str(e)}")
            return False

    def cerrar_ventana(self):
        try:
            print("🔍 Buscando botón de cierre (X) en la ventana...")
            
            # Intentar múltiples selectores para encontrar el botón X
            selectors = [
                "//button[contains(@class, 'ui-dialog-titlebar-close')]",                   # Xpath general
                "//span[@class='ui-button-icon-primary ui-icon ui-icon-closethick']/parent::button",  # Por el ícono
                "//button[@title='Close']",                                                # Por el título
                "//div[contains(@class,'ui-dialog')]/div/button",                          # Por la estructura del diálogo
                "//button[contains(@class,'close')]"                                       # Selector genérico para botones de cierre
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    close_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    close_btn.click()
                    print(f"✅ Ventana cerrada usando selector #{i+1}")
                    time.sleep(3)  # Esperar a que se cierre la ventana
                    return True
                except Exception as e:
                    print(f"⚠️ Selector #{i+1} falló: {str(e)[:100]}...")
            
            # Si llegamos aquí, intentemos con JavaScript
            try:
                print("🔧 Intentando cerrar ventana con JavaScript...")
                # Intentar múltiples opciones de JavaScript
                js_commands = [
                    "document.querySelector('.ui-dialog-titlebar-close').click();",
                    "document.querySelector('button[title=\"Close\"]').click();",
                    "document.querySelectorAll('.ui-button.ui-dialog-titlebar-close')[0].click();",
                    "var buttons = document.getElementsByTagName('button'); for(var i=0; i<buttons.length; i++) { if(buttons[i].title === 'Close') buttons[i].click(); }",
                    "document.querySelector('.ui-icon-closethick').parentNode.click();"
                ]
                
                for cmd in js_commands:
                    try:
                        self.driver.execute_script(cmd)
                        print("✅ Ventana cerrada usando JavaScript")
                        time.sleep(3)
                        return True
                    except Exception as js_e:
                        print(f"⚠️ Comando JS falló: {str(js_e)[:50]}...")
            except Exception as e:
                print(f"⚠️ Error general con JavaScript: {str(e)[:100]}...")
            
            # Última opción: Presionar tecla ESC
            print("🔑 Intentando cerrar con tecla ESC...")
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(2)
            
            # Verificar si hay un overlay y removerlo si existe
            self._limpiar_overlays()
            
            return False
        except Exception as e:
            print(f"❌ Error general al cerrar ventana: {str(e)}")
            return False
            
    def _limpiar_overlays(self):
        """Método auxiliar para limpiar overlays que puedan estar bloqueando la interfaz"""
        try:
            # Buscar todos los posibles overlays
            overlays = self.driver.find_elements(By.CSS_SELECTOR, 
                "div.ui-widget-overlay, div.ui-front, div.modal-backdrop, div.modal")
            
            if overlays:
                print(f"⚠️ Detectados {len(overlays)} overlays, intentando removerlos...")
                for overlay in overlays:
                    try:
                        self.driver.execute_script("arguments[0].remove();", overlay)
                    except:
                        pass  # Ignorar errores individuales
                print("✅ Overlays removidos")
            
            # También intentar con script genérico
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('.ui-widget-overlay, .ui-front, .modal-backdrop, .modal');
                for(var i=0; i<overlays.length; i++) {
                    overlays[i].remove();
                }
            """)
            
            time.sleep(1)  # Breve pausa
        except Exception as e:
            print(f"ℹ️ Limpieza de overlays: {str(e)[:100]}...")
 
    def imprimir_con_cdp(self, path):
        import base64
        from pathlib import Path

        result = self.driver.execute_cdp_cmd("Page.printToPDF", {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True
        })

        data = base64.b64decode(result['data'])
        Path(path).write_bytes(data)
        print(f"📥 PDF guardado en: {path}")
        return path

    def visualizar_historia(self, paciente_info, intento=1):
        max_intentos = 3
        
        try:
            time.sleep(3)
            self._limpiar_overlays()

            print("🔍 Buscando botón de historial clínico...")
            historial_btn = self.wait.until(EC.presence_of_element_located((By.ID, "btnPanelHistorico")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", historial_btn)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", historial_btn)
            print("✅ Historial de paciente abierto (JS)")

            time.sleep(5)

            print("🔍 Seleccionando todas las historias...")
            checkbox = self.wait.until(EC.presence_of_element_located((By.ID, "btnSeleccionarHistorias")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", checkbox)
            print("✅ Historias seleccionadas")

            time.sleep(2)

            print("🔍 Visualizando historias seleccionadas...")
            visualizar_btn = self.wait.until(EC.presence_of_element_located((By.ID, "btnVisualizarSeleccionado")))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", visualizar_btn)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", visualizar_btn)
            print("✅ Visualización iniciada")

            time.sleep(5)

            print("🔍 Localizando el iframe del visor...")
            iframe = self.wait.until(EC.presence_of_element_located((By.ID, "iframe_visualizar_reporte_formato")))
            src = iframe.get_attribute("src")
            print(f"📄 URL del visor: {src}")

            # Abre la pestaña, imprime PDF y luego la cierra
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(src)

            time.sleep(5)

            # Crear nombre de archivo con ID y nombre del paciente
            nombre_archivo = f"{paciente_info['id']}_{paciente_info['nombre'].replace(' ', '_')}.pdf"
            # Limpia el nombre de archivo de caracteres especiales
            nombre_archivo = re.sub(r'[\\/*?:"<>|]', '', nombre_archivo)
            ruta_pdf = os.path.join(self.output_dir, nombre_archivo)
            
            print(f"🖨️ Generando PDF desde visor para {paciente_info['nombre']}...")
            self.imprimir_con_cdp(ruta_pdf)

            # Registrar la información del PDF
            self.pdfs_info.append({
                "ruta": ruta_pdf,
                "id_paciente": paciente_info['id'],
                "nombre_paciente": paciente_info['nombre']
            })

            # Verificar el número de ventanas abiertas después de cerrar la pestaña
            print(f"Ventanas abiertas después de cerrar la pestaña del PDF: {len(self.driver.window_handles)}")
            self.driver.close()  # Cerrar pestaña del reporte
            self.driver.switch_to.window(self.driver.window_handles[0])
            print(f"✅ Regresado a la ventana principal. Ventanas abiertas: {len(self.driver.window_handles)}")
            time.sleep(5)
            
            return ruta_pdf
        
        except Exception as e:
            print(f"❌ Error al visualizar historia clínica: {str(e)}")
            if intento < max_intentos:
                print(f"🔄 Reintentando visualización (intento {intento+1}/{max_intentos})...")
                return self.visualizar_historia(paciente_info, intento + 1)
            return None

    def cerrar_visor_historia(self):
        try:
            # Esperar a que el botón de cerrar esté disponible y sea clickeable
            print("🔍 Buscando el botón de cierre del visor...")
            
            # Intentar diferentes selectores para el botón de cierre
            selectores = [
                "//button[contains(@class, 'ui-button-icon-only') and @title='Close']",
                "//span[@class='ui-icon ui-icon-closethick']/parent::button",
                "//button[contains(@class, 'ui-dialog-titlebar-close')]"
            ]
            
            for selector in selectores:
                try:
                    close_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    close_button.click()
                    print("✅ Botón de cierre del visor clicado con éxito.")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            # Si no funcionó con los selectores, intentar con JavaScript
            js_commands = [
                "document.querySelector('.ui-dialog-titlebar-close').click();",
                "document.querySelector('button[title=\"Close\"]').click();",
                "document.querySelectorAll('.ui-button.ui-dialog-titlebar-close')[0].click();"
            ]
            
            for cmd in js_commands:
                try:
                    self.driver.execute_script(cmd)
                    print("✅ Visor cerrado usando JavaScript.")
                    time.sleep(3)
                    return True
                except:
                    continue
                    
            # Como último recurso, limpiar overlays
            self._limpiar_overlays()
            return False
        
        except Exception as e:
            print(f"❌ Error al intentar cerrar el visor de la historia clínica: {str(e)}")
            return False

    def volver_a_listado_pacientes(self):
        """Navega de regreso al listado de pacientes"""
        try:
            print("🔄 Volviendo al listado de pacientes...")
            
            # Primera opción: buscar un botón específico para volver al listado
            try:
                volver_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "btnVolverListadoPacientes"))
                )
                volver_btn.click()
                print("✅ Vuelto al listado mediante botón específico")
                time.sleep(3)
                return True
            except:
                print("⚠️ No se encontró botón específico para volver, intentando alternativas...")
            
            # Segunda opción: ir directamente a la URL del listado
            try:
                self.driver.get("https://www.server0medifolios.net/index.php/SALUD_HOME/paciente")
                time.sleep(3)
                self.abrir_listado_pacientes()
                print("✅ Vuelto al listado mediante URL directa")
                return True
            except Exception as e:
                print(f"❌ Error volviendo al listado: {str(e)}")
                return False
                
        except Exception as e:
            print(f"❌ Error general volviendo al listado: {str(e)}")
            return False

    def cerrar(self):
        print("👋 Cerrando navegador...")
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")

    def descargar_historias_clinicas(self, num_pacientes=3):
        """Descarga las historias clínicas de varios pacientes secuencialmente"""
        
        self.pdfs_info = []  # Reiniciar la lista de PDFs
        
        for i in range(num_pacientes):
            print(f"\n{'='*50}")
            print(f"🏥 PROCESANDO PACIENTE {i+1}/{num_pacientes}")
            print(f"{'='*50}")
            
            try:
                # Si es el primer paciente, necesitamos abrir el listado y seleccionarlo
                if i == 0:
                    self.abrir_listado_pacientes()
                    paciente_info = self.seleccionar_paciente_por_indice(i)
                    if not paciente_info:
                        print("❌ No se pudo seleccionar el primer paciente. Abortando.")
                        break
                # Para los siguientes pacientes, cerrar ficha actual y volver al listado
                else:
                    if not self.volver_a_listado_pacientes():
                        print("❌ No se pudo volver al listado de pacientes. Abortando.")
                        break
                    
                    paciente_info = self.seleccionar_paciente_por_indice(i)
                    if not paciente_info:
                        print(f"❌ No se pudo seleccionar el paciente #{i+1}. Abortando.")
                        break
                
                # Visualizar y extraer la historia clínica
                pdf_path = self.visualizar_historia(paciente_info)
                
                # Cerrar el visor de la historia
                self.cerrar_visor_historia()
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error procesando paciente #{i+1}: {str(e)}")
                # Intentar continuar con el siguiente paciente
                try:
                    self.volver_a_listado_pacientes()
                except:
                    print("❌ No se pudo recuperar del error. Abortando.")
                    break
        
        print(f"\n📊 RESUMEN: Se generaron {len(self.pdfs_info)} archivos PDF")
        for i, pdf_info in enumerate(self.pdfs_info):
            print(f"  {i+1}. {pdf_info['nombre_paciente']} (ID: {pdf_info['id_paciente']}) -> {os.path.basename(pdf_info['ruta'])}")
        
        return self.pdfs_info
    
    def extraer_texto_pdf(self, pdf_path):
        """
        Extrae el texto de un archivo PDF con pre-procesamiento mejorado
        """
        try:
            texto_completo = ""
            with open(pdf_path, 'rb') as archivo:
                lector_pdf = PyPDF2.PdfReader(archivo)
                num_paginas = len(lector_pdf.pages)
                
                print(f"📄 Extrayendo texto de {pdf_path} ({num_paginas} páginas)")
                
                for num_pagina in range(num_paginas):
                    pagina = lector_pdf.pages[num_pagina]
                    texto_pagina = pagina.extract_text()
                    
                    # Mejoras en el procesamiento de texto
                    # 1. Normalizar espacios para facilitar búsqueda de patrones
                    texto_pagina = re.sub(r'\s+', ' ', texto_pagina)
                    
                    # 2. Asegurar que "EDAD:" y "SEXO:" sean reconocibles (espacio después de los dos puntos)
                    texto_pagina = re.sub(r'EDAD:(\d)', r'EDAD: \1', texto_pagina, flags=re.IGNORECASE)
                    texto_pagina = re.sub(r'SEXO:([A-Za-z])', r'SEXO: \1', texto_pagina, flags=re.IGNORECASE)
                    
                    texto_completo += texto_pagina + "\n\n"
                        
                return texto_completo
        except Exception as e:
            print(f"❌ Error extrayendo texto del PDF {pdf_path}: {str(e)}")
            return ""
    
    def diagnosticar_extraccion_pdf(self, pdf_path):
        """
        Extrae el texto del PDF y busca patrones específicos para diagnóstico
        """
        texto = self.extraer_texto_pdf(pdf_path)
        
        # Buscar patrones relevantes
        patrones = {
            "EDAD": re.findall(r'EDAD:\s*(\d+)\s*[Aa][ñÑ][oO][sS]?', texto),
            "SEXO": re.findall(r'SEXO:\s*([A-Za-z]+)', texto),
            "IDENTIFICACIÓN": re.findall(r'IDENTIFICACI[ÓO]N:\s*([A-Za-z0-9\s]+)', texto),
            "NOMBRE": re.findall(r'NOMBRE:\s*([A-Za-z\s]+)', texto),
            "FECHA DE NACIMIENTO": re.findall(r'FECHA DE NACIMIENTO:\s*(\d{4}-\d{2}-\d{2})', texto)
        }
        
        print(f"\n{'='*50}")
        print(f"DIAGNÓSTICO DE EXTRACCIÓN PARA: {os.path.basename(pdf_path)}")
        print(f"{'='*50}")
        
        for clave, valores in patrones.items():
            print(f"{clave}: {valores if valores else 'NO ENCONTRADO'}")
        
        print(f"{'='*50}")
        print(f"Primeros 500 caracteres del texto extraído:")
        print(f"{'='*50}")
        print(texto[:500])
        print(f"{'='*50}\n")
        
        return patrones
    
    def convertir_pdf_a_fhir(self, pdf_path):
        """
        Extrae el texto del PDF y lo envía a OpenAI para convertirlo a un JSON HL7-FHIR.
        Compatible con la API de OpenAI v1.0+
        """
        try:
            # Extraer texto del PDF
            texto_pdf = self.extraer_texto_pdf(pdf_path)
            
            if not texto_pdf or len(texto_pdf.strip()) < 50:
                print(f"⚠️ El PDF {pdf_path} no contiene suficiente texto extraíble")
                return None
                
            print(f"🔄 Enviando contenido del PDF a OpenAI para análisis FHIR...")
            
            system_prompt = """
            Eres un experto en el estándar HL7-FHIR y en extracción de datos de historias clínicas.

            Tienes que recibir como entrada el texto entero de la historia clínica (tal cual lo extrae PyPDF2, con saltos de línea). A partir de ahí, debes generar un único JSON válido con un Bundle FHIR, siguiendo estas reglas:

            1. **Patient**  
            - Busca una línea que contenga "IDENTIFICACIÓN:" y extrae el tipo y número de documento:
                - Ejemplo: "IDENTIFICACIÓN: RC 11004310" → identifier.system="RC", identifier.value="11004310"  
            - Busca "NOMBRE:" y extrae family/given:
                - "NOMBRE: AARON GABRIEL SANTAMARIA RODRIGUEZ" → family="SANTAMARIA RODRIGUEZ", given=["AARON","GABRIEL"]  
            - Busca "FECHA DE NACIMIENTO:" con formato YYYY-MM-DD → birthDate  
            - Busca **"EDAD:"** (seguido de cualquier número y la palabra "Años", "Año", "años" o "año") y extrae el número como:
                ```json
                "extension": [{"url":"age","valueInteger": X }]
                ```  
            - Busca **"SEXO:"** seguido de cualquier valor y mapea:
                - Si contiene "MASCULINO", "masculino", "Masculino" o "M" → gender: "male"
                - Si contiene "FEMENINO", "femenino", "Femenino" o "F" → gender: "female"
                - Para otros valores → gender: "unknown"

            2. **Encounter**  
            - Busca “FECHA ATENCIÓN: YYYY-MM-DD HH:MM:SS” y usa esa fecha con Z → Encounter.start  
            - Si hay motivo (“MOTIVO DE CONSULTA”), ponlo en reasonCode.text

            3. **Observation**  
            Para cada signo vital o paraclínico, crea un Observation:
            - Blood pressure → code.text="Blood pressure", valueQuantity.value+unit  
            - Heart rate → code.text="Heart rate", …  
            - Temperature → code.text="Body temperature", …  
            - Laboratorio (p.ej. “Colesterol total: 207 (Alto)”) → code.text="Cholesterol total", valueQuantity.value=207, unit="mg/dL"  
            - Siempre incluye effectiveDateTime si aparece fecha explícita, sino omítelo.

            4. **Condition**  
            - Para cada línea de diagnóstico (“E441 - DESNUTRICION PROTEICOCALÓRICA LEVE”) → code.text y coding[0].code

            5. **MedicationStatement**  
            - Para cada plan o medicamento (“Albendazol, recomendaciones nutricionales”) → medicationCodeableConcept.text y dosage[0].text

            6. **Procedure**  
            - Para cada procedimiento (“Acupuntura”) → code.text y performedDateTime si hay fecha

            **MUY IMPORTANTE:**  
            - Devuelve **solo** el JSON (sin markdown ni explicaciones).  
            - El JSON debe empezar por:
            ```json
            {
                "resourceType":"Bundle",
                "type":"collection",
                "entry":[
                    {
                    "resource":{
                        "resourceType":"Patient",
                        "identifier":[{"system":"RC","value":"11004310"}],
                        "name":[{"family":"SANTAMARIA RODRIGUEZ","given":["AARON","GABRIEL"]}],
                        "gender":"male",
                        "birthDate":"2020-12-07",
                        "extension":[{"url":"age","valueInteger":4}]
                    }
                    },
                    {
                    "resource":{
                        "resourceType":"Observation",
                        "code":{"text":"Heart rate"},
                        "valueQuantity":{"value":130,"unit":"beats/min"},
                        "effectiveDateTime":"2023-06-06T10:46:34Z"
                    }
                    },
                    {
                    "resource":{
                        "resourceType":"Condition",
                        "code":{"text":"Desnutrición proteicocalórica leve","coding":[{"code":"E441"}]},
                        "clinicalStatus":{"text":"active"}
                    }
                    }
                    // …otros recursos…
                ]
                }

            Devuelve un JSON válido y bien estructurado sin texto adicional.
            """
            
            # Limitar el texto a enviar a OpenAI (para evitar límites de tokens)
            max_tokens = 12000  # Ajustar según el modelo
            texto_recortado = texto_pdf[:max_tokens] if len(texto_pdf) > max_tokens else texto_pdf
            
            # Usar la nueva API de OpenAI (versión >= 1.0.0)
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Ajustar modelo según disponibilidad y necesidad
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Historia clínica extraída del PDF:\n\n{texto_recortado}"}
                ],
                temperature=0.3,  # Baja temperatura para respuestas más deterministas
                max_tokens=4000,  # Ajustar según el modelo
            )
            
            content = response.choices[0].message.content

            # Primero registrar el contenido para diagnóstico
            print(f"Respuesta de OpenAI (primeros 200 caracteres): {content[:200]}")

            # Intentar parsear JSON
            try:
                # Primero verificar si la respuesta ya es JSON directamente
                fhir_json = json.loads(content)
                print("✅ JSON parseado directamente de la respuesta")
            except json.JSONDecodeError:
                # Si no, intentar extraer JSON de bloques de código
                match = re.search(r"```(?:json)?([\s\S]*?)```", content)
                if match:
                    try:
                        fhir_json = json.loads(match.group(1).strip())
                        print("✅ JSON extraído de bloque de código markdown")
                    except json.JSONDecodeError:
                        print(f"❌ No se pudo parsear el JSON extraído del bloque de código")
                        return None
                else:
                    # Tercer intento: buscar llaves de inicio y fin del JSON
                    match = re.search(r"({[\s\S]*})", content)
                    if match:
                        try:
                            fhir_json = json.loads(match.group(1).strip())
                            print("✅ JSON extraído usando expresión regular de llaves")
                        except json.JSONDecodeError:
                            print(f"❌ No se pudo parsear el JSON usando expresión regular")
                            return None
                    else:
                        print(f"❌ No se encontró estructura JSON en la respuesta")
                        return None
                    
            print(f"✅ Documento FHIR generado exitosamente")
            return fhir_json
            
        except Exception as e:
            print(f"❌ Error en proceso de conversión a FHIR: {str(e)}")
            return None

    def generar_xml_de_fhir(self, fhir_json):
        """
        Convierte el JSON FHIR a una cadena XML.
        """
        try:
            # Configurar parámetros para la conversión
            xml_bytes = dicttoxml(
                fhir_json, 
                custom_root='Bundle', 
                attr_type=False,
                item_func=lambda x: 'item'  # Usar 'item' para elementos de lista
            )
            return xml_bytes.decode('utf-8')
        except Exception as e:
            print(f"❌ Error generando XML: {str(e)}")
            return None

    def generar_html_tabular(self, fhir_json, html_path, pdf_info):
        """
        Genera un archivo HTML con visualización tabular de los datos FHIR extraídos.
        """
        try:
            if not fhir_json:
                print(f"⚠️ No hay datos FHIR para generar HTML")
                return False
                
            # Función auxiliar para aplanar la estructura JSON a pares clave-valor
            def aplanar_json(json_obj, prefijo=''):
                items = []
                if isinstance(json_obj, dict):
                    for k, v in json_obj.items():
                        nueva_clave = f"{prefijo}.{k}" if prefijo else k
                        if isinstance(v, (dict, list)):
                            items.extend(aplanar_json(v, nueva_clave))
                        else:
                            if v is not None and v != "":  # Solo incluir valores no vacíos
                                items.append((nueva_clave, v))
                elif isinstance(json_obj, list):
                    for i, item in enumerate(json_obj):
                        nueva_clave = f"{prefijo}[{i}]"
                        items.extend(aplanar_json(item, nueva_clave))
                return items
                
            # Aplanar el JSON FHIR
            datos_aplanados = aplanar_json(fhir_json)
            
            # Crear HTML con Bootstrap para mejor presentación
            html = [
                '<!DOCTYPE html>',
                '<html lang="es">',
                '<head>',
                '    <meta charset="UTF-8">',
                '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                '    <title>Datos FHIR - Historia Clínica</title>',
                '    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">',
                '    <style>',
                '        body { padding: 20px; }',
                '        .header { margin-bottom: 30px; }',
                '        .table-container { margin-top: 20px; }',
                '        .resource-title { margin-top: 30px; background-color: #f8f9fa; padding: 10px; border-radius: 5px; }',
                '    </style>',
                '</head>',
                '<body>',
                '    <div class="container">',
                '        <div class="header">',
                f'            <h1>Historia Clínica FHIR</h1>',
                f'            <h3>Paciente: {pdf_info["nombre_paciente"]}</h3>',
                f'            <p>ID: {pdf_info["id_paciente"]}</p>',
                f'            <p>Archivo Original: {os.path.basename(pdf_info["ruta"])}</p>',
                '        </div>',
                '',
                '        <div class="table-container">',
                '            <h2>Datos Extraídos (HL7-FHIR)</h2>',
                '            <table class="table table-striped table-bordered">',
                '                <thead class="table-primary">',
                '                    <tr>',
                '                        <th width="40%">Campo</th>',
                '                        <th width="60%">Valor</th>',
                '                    </tr>',
                '                </thead>',
                '                <tbody>'
            ]
            
            # Organizar datos por recursos FHIR
            recursos = {}
            for clave, valor in datos_aplanados:
                # Extraer el tipo de recurso (primer segmento de la clave)
                partes = clave.split('.')
                if len(partes) > 0:
                    recurso = partes[0]
                    if recurso not in recursos:
                        recursos[recurso] = []
                    recursos[recurso].append((clave, valor))
            
            # Agregar secciones por cada tipo de recurso
            for recurso, datos in recursos.items():
                html.append(f'                    <tr><td colspan="2" class="resource-title"><strong>{recurso}</strong></td></tr>')
                for clave, valor in datos:
                    # Convertir valores booleanos y numéricos a texto
                    if isinstance(valor, bool):
                        valor_str = "Sí" if valor else "No"
                    else:
                        valor_str = str(valor)
                    
                    html.append(f'                    <tr><td>{clave}</td><td>{valor_str}</td></tr>')
            
            # Cerrar HTML
            html.extend([
                '                </tbody>',
                '            </table>',
                '        </div>',
                '    </div>',
                '    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>',
                '</body>',
                '</html>'
            ])
            
            # Escribir archivo HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
                
            print(f"✅ HTML generado exitosamente: {html_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generando HTML: {str(e)}")
            return False
    
    def generar_html_global(self, output_dir):
        # Definir la ruta del archivo HTML global
        html_path = os.path.join(output_dir, "historias_clinicas_fhir.html")
        
        # Recopilar todos los datos FHIR de los archivos JSON generados
        datos_consolidados = {
            "pacientes": [],
            "diagnosticos": [],
            "observaciones": [],
            "medicamentos": [],
            "procedimientos": []
        }
        
        # Recorrer todos los PDFs procesados
        for info in self.pdfs_info:
            pdf_path = info['ruta']
            json_path = os.path.splitext(pdf_path)[0] + '.json'
            
            # Verificar si existe el archivo JSON correspondiente
            if os.path.exists(json_path):
                try:
                    # Cargar datos FHIR desde JSON
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        fhir_data = json.load(jf)
                    
                    # Extraer información del paciente
                    paciente_info = {
                        "id": info['id_paciente'],
                        "nombre": info['nombre_paciente'],
                        "genero": self._extraer_valor(fhir_data, ["Patient", "gender"], "Desconocido"),
                        "edad": self._extraer_valor(fhir_data, ["Patient", "age"], "Desconocido"),
                        "diagnosticos": [],
                        "observaciones": [],
                        "medicamentos": [],
                        "procedimientos": []
                    }
                    
                    # Extraer diagnósticos
                    diagnosticos = self._extraer_recursos(fhir_data, "Condition")
                    for diag in diagnosticos:
                        diag_info = {
                            "descripcion": self._extraer_valor(diag, ["code", "text"], "Desconocido"),
                            "estado": self._extraer_valor(diag, ["clinicalStatus", "text"], "Desconocido"),
                            "paciente": info['nombre_paciente'],
                            "id_paciente": info['id_paciente']
                        }
                        paciente_info["diagnosticos"].append(diag_info)
                        datos_consolidados["diagnosticos"].append(diag_info)
                    
                    # Extraer observaciones
                    observaciones = self._extraer_recursos(fhir_data, "Observation")
                    for obs in observaciones:
                        valor = self._extraer_valor_observacion(obs)
                        obs_info = {
                            "descripcion": self._extraer_valor(obs, ["code", "text"], "Desconocido"),
                            "valor": valor,
                            "fecha": self._extraer_valor(obs, ["effectiveDateTime"], "Desconocido"),
                            "paciente": info['nombre_paciente'],
                            "id_paciente": info['id_paciente']
                        }
                        paciente_info["observaciones"].append(obs_info)
                        datos_consolidados["observaciones"].append(obs_info)
                    
                    # Extraer medicamentos
                    medicamentos = self._extraer_recursos(fhir_data, "MedicationStatement") + self._extraer_recursos(fhir_data, "MedicationRequest")
                    for med in medicamentos:
                        med_info = {
                            "medicamento": self._extraer_valor(med, ["medicationCodeableConcept", "text"], 
                                                self._extraer_valor(med, ["medication", "text"], "Desconocido")),
                            "dosificacion": self._extraer_dosificacion(med),
                            "estado": self._extraer_valor(med, ["status"], "Desconocido"),
                            "paciente": info['nombre_paciente'],
                            "id_paciente": info['id_paciente']
                        }
                        paciente_info["medicamentos"].append(med_info)
                        datos_consolidados["medicamentos"].append(med_info)
                    
                    # Extraer procedimientos
                    procedimientos = self._extraer_recursos(fhir_data, "Procedure")
                    for proc in procedimientos:
                        proc_info = {
                            "procedimiento": self._extraer_valor(proc, ["code", "text"], "Desconocido"),
                            "estado": self._extraer_valor(proc, ["status"], "Desconocido"),
                            "fecha": self._extraer_valor(proc, ["performedDateTime"], "Desconocido"),
                            "paciente": info['nombre_paciente'],
                            "id_paciente": info['id_paciente']
                        }
                        paciente_info["procedimientos"].append(proc_info)
                        datos_consolidados["procedimientos"].append(proc_info)
                    
                    # Agregar paciente al listado consolidado
                    datos_consolidados["pacientes"].append(paciente_info)
                    
                except Exception as e:
                    print(f"⚠️ Error al procesar datos FHIR para consolidación: {str(e)}")
        
        # Generar HTML con sistema de pestañas
        html = self._generar_estructura_html(datos_consolidados)
        
        # Escribir archivo HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML global generado: {html_path}")
        return html_path

    def _extraer_recursos(self, fhir_data, tipo_recurso):
        """Extrae recursos de un tipo específico del conjunto de datos FHIR"""
        recursos = []
        
        # Buscar en la estructura de "entry" si existe
        if "entry" in fhir_data:
            for entry in fhir_data["entry"]:
                if "resource" in entry and "resourceType" in entry["resource"]:
                    if entry["resource"]["resourceType"] == tipo_recurso:
                        recursos.append(entry["resource"])
        
        # Buscar directamente en el nivel superior
        if tipo_recurso in fhir_data:
            if isinstance(fhir_data[tipo_recurso], list):
                recursos.extend(fhir_data[tipo_recurso])
            else:
                recursos.append(fhir_data[tipo_recurso])
        
        return recursos

    def _extraer_valor(self, data, path, default=""):
        """Extrae un valor de un objeto siguiendo una ruta de acceso - versión mejorada"""
        if not data:
            return default
        
        current = data
        # Primero intentamos el camino directo
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and len(current) > 0:
                # Si es una lista, intentar con el primer elemento
                if isinstance(current[0], dict) and key in current[0]:
                    current = current[0][key]
                else:
                    # Buscar en todos los elementos de la lista si el primero no funciona
                    for item in current:
                        if isinstance(item, dict) and key in item:
                            current = item[key]
                            break
                    else:  # No se encontró en ningún elemento
                        return default
            else:
                # Buscar en estructura "entry" si existe
                if "entry" in current and isinstance(current["entry"], list):
                    for entry in current["entry"]:
                        if "resource" in entry and path[0] in entry["resource"]:
                            # Reiniciar la búsqueda desde este punto con el resto del path
                            return self._extraer_valor(entry["resource"], path, default)
                return default
        
        return current if current is not None else default
    
    # Modificación para la función _extraer_valor
    def _extraer_valor(self, data, path, default=""):
        """Extrae un valor de un objeto siguiendo una ruta de acceso - versión mejorada"""
        if not data:
            return default
        
        current = data
        # Primero intentamos el camino directo
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and len(current) > 0:
                # Si es una lista, intentar con el primer elemento
                if isinstance(current[0], dict) and key in current[0]:
                    current = current[0][key]
                else:
                    # Buscar en todos los elementos de la lista si el primero no funciona
                    for item in current:
                        if isinstance(item, dict) and key in item:
                            current = item[key]
                            break
                    else:  # No se encontró en ningún elemento
                        return default
            else:
                # Buscar en estructura "entry" si existe
                if "entry" in current and isinstance(current["entry"], list):
                    for entry in current["entry"]:
                        if "resource" in entry and path[0] in entry["resource"]:
                            # Reiniciar la búsqueda desde este punto con el resto del path
                            return self._extraer_valor(entry["resource"], path, default)
                return default
        
        return current if current is not None else default

    # Modificación para extraer correctamente género y edad
    def _extraer_paciente_datos(self, fhir_data):
        """Extrae datos completos del paciente desde JSON FHIR - versión mejorada"""
        paciente_info = {}
        
        # Buscar el recurso Patient
        patient_resource = None
        if "entry" in fhir_data:
            for entry in fhir_data["entry"]:
                if entry.get("resource", {}).get("resourceType") == "Patient":
                    patient_resource = entry["resource"]
                    break
        
        if not patient_resource and "Patient" in fhir_data:
            patient_resource = fhir_data["Patient"]
        
        if patient_resource:
            # ID del paciente
            identifier = patient_resource.get("identifier", [{}])[0]
            paciente_info["id"] = identifier.get("value", "Desconocido")
            
            # Nombre completo
            if "name" in patient_resource and len(patient_resource["name"]) > 0:
                name = patient_resource["name"][0]
                family = name.get("family", "")
                given = name.get("given", [])
                given_str = " ".join(given) if given else ""
                paciente_info["nombre"] = f"{given_str} {family}".strip()
            else:
                paciente_info["nombre"] = "Desconocido"
            
            # Género - con manejo mejorado
            gender = patient_resource.get("gender", "unknown")
            if gender == "male":
                paciente_info["genero"] = "Masculino"
            elif gender == "female":
                paciente_info["genero"] = "Femenino"
            else:
                paciente_info["genero"] = "Desconocido"
            
            # Edad - búsqueda más exhaustiva
            edad = "Desconocido"
            
            # Primero buscar en extensiones
            if "extension" in patient_resource:
                for ext in patient_resource["extension"]:
                    if ext.get("url") == "age" and "valueInteger" in ext:
                        edad = f"{ext['valueInteger']} años"
                        break
            
            # Si no se encontró en extensiones, calcular desde birthDate
            if edad == "Desconocido" and "birthDate" in patient_resource:
                edad = self._calcular_edad_desde_birthdate(patient_resource["birthDate"])
            
            paciente_info["edad"] = edad
        
        return paciente_info

    def _calcular_edad_desde_birthdate(self, birthdate):
        """Calcula la edad a partir de la fecha de nacimiento"""
        from datetime import datetime
        try:
            # Formato ISO: YYYY-MM-DD
            birth = datetime.strptime(birthdate, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return f"{age} años"
        except Exception:
            return "Desconocido"
    
    def _extraer_valor_observacion(self, observacion):
        """Extrae el valor de una observación que puede estar en diferentes formatos"""
        if "valueQuantity" in observacion:
            valor = self._extraer_valor(observacion, ["valueQuantity", "value"], "")
            unidad = self._extraer_valor(observacion, ["valueQuantity", "unit"], "")
            if valor and unidad:
                return f"{valor} {unidad}"
            elif valor:
                return str(valor)
        elif "valueString" in observacion:
            return observacion["valueString"]
        elif "valueCodeableConcept" in observacion:
            return self._extraer_valor(observacion, ["valueCodeableConcept", "text"], "No disponible")
        elif "valueBoolean" in observacion:
            return "Sí" if observacion["valueBoolean"] else "No"
        elif "component" in observacion and isinstance(observacion["component"], list):
            # Para observaciones con múltiples componentes
            componentes = []
            for comp in observacion["component"]:
                codigo = self._extraer_valor(comp, ["code", "text"], "")
                valor = self._extraer_valor_observacion(comp)  # Recursivo para componentes
                if codigo and valor:
                    componentes.append(f"{codigo}: {valor}")
            return ", ".join(componentes) if componentes else "No disponible"
        
        return "No disponible"

    def _extraer_dosificacion(self, medicamento):
        """Extrae información de dosificación de un medicamento"""
        if "dosage" in medicamento and isinstance(medicamento["dosage"], list) and len(medicamento["dosage"]) > 0:
            dosage = medicamento["dosage"][0]
            texto = self._extraer_valor(dosage, ["text"], "")
            if texto:
                return texto
            
            # Intentar construir la dosificación a partir de componentes
            dosis = self._extraer_valor(dosage, ["doseQuantity", "value"], "")
            unidad = self._extraer_valor(dosage, ["doseQuantity", "unit"], "")
            frecuencia = ""
            if "timing" in dosage:
                frecuencia = self._extraer_valor(dosage, ["timing", "code", "text"], "")
            
            if dosis and unidad:
                if frecuencia:
                    return f"{dosis} {unidad}, {frecuencia}"
                return f"{dosis} {unidad}"
        
        return "No especificada"

    def _generar_estructura_html(self, datos):
        """Genera la estructura HTML completa con sistema de pestañas y diseño mejorado"""
        html = [
            '<!DOCTYPE html>',
            '<html lang="es">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Historias Clínicas - HL7 FHIR</title>',
            '    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">',
            '    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
            '    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css">',
            '    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.min.css">',
            '    <style>',
            '        :root {',
            '            --primary-color: #0d6efd;',
            '            --secondary-color: #6c757d;',
            '            --success-color: #198754;',
            '            --info-color: #0dcaf0;',
            '            --warning-color: #ffc107;',
            '            --danger-color: #dc3545;',
            '            --light-color: #f8f9fa;',
            '            --dark-color: #212529;',
            '        }',
            '        body {',
            '            font-family: "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;',
            '            background-color: #f5f8fa;',
            '            color: #333;',
            '            line-height: 1.6;',
            '        }',
            '        .main-container {',
            '            background-color: #fff;',
            '            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);',
            '            border-radius: 0.5rem;',
            '            padding: 2rem;',
            '            margin-top: 2rem;',
            '            margin-bottom: 2rem;',
            '        }',
            '        .header {',
            '            padding-bottom: 1.5rem;',
            '            border-bottom: 1px solid #e9ecef;',
            '            margin-bottom: 2rem;',
            '        }',
            '        .header h1 {',
            '            font-weight: 600;',
            '            color: var(--primary-color);',
            '        }',
            '        .header p {',
            '            color: var(--secondary-color);',
            '            max-width: 600px;',
            '        }',
            '        .nav-tabs {',
            '            border-bottom: 1px solid rgba(0,0,0,.125);',
            '            margin-bottom: 2rem;',
            '        }',
            '        .nav-tabs .nav-link {',
            '            border: none;',
            '            color: var(--secondary-color);',
            '            font-weight: 500;',
            '            padding: 0.75rem 1.25rem;',
            '            transition: all 0.2s ease;',
            '        }',
            '        .nav-tabs .nav-link:hover {',
            '            color: var(--primary-color);',
            '            background-color: rgba(13, 110, 253, 0.05);',
            '        }',
            '        .nav-tabs .nav-link.active {',
            '            color: var(--primary-color);',
            '            background-color: #fff;',
            '            border-bottom: 3px solid var(--primary-color);',
            '        }',
            '        .nav-tabs .nav-link i {',
            '            margin-right: 0.5rem;',
            '        }',
            '        .filter-container {',
            '            background-color: #f8f9fa;',
            '            border-radius: 0.5rem;',
            '            padding: 1.5rem;',
            '            margin-bottom: 2rem;',
            '        }',
            '        .filter-container h3 {',
            '            font-size: 1.25rem;',
            '            margin-bottom: 1rem;',
            '            color: var(--dark-color);',
            '        }',
            '        .form-control {',
            '            border-radius: 0.375rem;',
            '            padding: 0.75rem 1rem;',
            '            border: 1px solid #ced4da;',
            '            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;',
            '        }',
            '        .form-control:focus {',
            '            border-color: #86b7fe;',
            '            box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);',
            '        }',
            '        .search-icon {',
            '            position: absolute;',
            '            right: 1.5rem;',
            '            top: 0.75rem;',
            '            color: var(--secondary-color);',
            '        }',
            '        .card {',
            '            border-radius: 0.5rem;',
            '            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);',
            '            margin-bottom: 1.5rem;',
            '            border: none;',
            '            transition: transform 0.3s ease;',
            '        }',
            '        .card:hover {',
            '            transform: translateY(-5px);',
            '        }',
            '        .card-header {',
            '            background-color: rgba(0, 0, 0, 0.03);',
            '            border-bottom: 1px solid rgba(0, 0, 0, 0.125);',
            '            padding: 1rem 1.5rem;',
            '            border-radius: 0.5rem 0.5rem 0 0 !important;',
            '        }',
            '        .card-header h4 {',
            '            margin-bottom: 0;',
            '            font-weight: 600;',
            '            color: var(--primary-color);',
            '        }',
            '        .card-body {',
            '            padding: 1.5rem;',
            '        }',
            '        .stat-card {',
            '            text-align: center;',
            '            color: #fff;',
            '            border-radius: 0.5rem;',
            '            padding: 1.5rem;',
            '            margin-bottom: 1.5rem;',
            '            box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.15);',
            '        }',
            '        .stat-card h2 {',
            '            font-size: 2.5rem;',
            '            margin-bottom: 0.5rem;',
            '            font-weight: 700;',
            '        }',
            '        .stat-card p {',
            '            font-size: 1rem;',
            '            margin-bottom: 0;',
            '            opacity: 0.8;',
            '        }',
            '        .stat-card i {',
            '            font-size: 2rem;',
            '            margin-bottom: 1rem;',
            '        }',
            '        .bg-primary-gradient {',
            '            background: linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%);',
            '        }',
            '        .bg-success-gradient {',
            '            background: linear-gradient(135deg, #198754 0%, #146c43 100%);',
            '        }',
            '        .bg-info-gradient {',
            '            background: linear-gradient(135deg, #0dcaf0 0%, #0aa2c0 100%);',
            '        }',
            '        .bg-warning-gradient {',
            '            background: linear-gradient(135deg, #ffc107 0%, #cc9a06 100%);',
            '        }',
            '        .bg-danger-gradient {',
            '            background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%);',
            '        }',
            '        .table-container {',
            '            background-color: #fff;',
            '            border-radius: 0.5rem;',
            '            padding: 1.5rem;',
            '            margin-bottom: 1.5rem;',
            '            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);',
            '        }',
            '        .table-container h3 {',
            '            font-size: 1.5rem;',
            '            margin-bottom: 1.5rem;',
            '            color: var(--dark-color);',
            '            font-weight: 600;',
            '        }',
            '        .table {',
            '            width: 100%;',
            '            margin-bottom: 1rem;',
            '            color: #212529;',
            '            border-color: #dee2e6;',
            '        }',
            '        .table thead th {',
            '            vertical-align: bottom;',
            '            border-bottom: 2px solid #dee2e6;',
            '            background-color: var(--light-color);',
            '            color: var(--dark-color);',
            '            font-weight: 600;',
            '            padding: 0.75rem;',
            '        }',
            '        .table tbody tr {',
            '            transition: background-color 0.2s ease;',
            '        }',
            '        .table tbody tr:hover {',
            '            background-color: rgba(0, 0, 0, 0.02);',
            '        }',
            '        .table td {',
            '            padding: 0.75rem;',
            '            vertical-align: middle;',
            '            border-top: 1px solid #dee2e6;',
            '        }',
            '        .dataTables_wrapper .dataTables_info,',
            '        .dataTables_wrapper .dataTables_paginate {',
            '            margin-top: 1rem;',
            '        }',
            '        .dataTables_wrapper .dataTables_paginate .paginate_button {',
            '            padding: 0.5rem 0.75rem;',
            '            margin-left: 0.25rem;',
            '            border-radius: 0.25rem;',
            '        }',
            '        .dataTables_wrapper .dataTables_paginate .paginate_button.current {',
            '            background-color: var(--primary-color);',
            '            color: #fff !important;',
            '            border: 1px solid var(--primary-color);',
            '        }',
            '        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {',
            '            background-color: #f8f9fa;',
            '            color: var(--primary-color) !important;',
            '        }',
            '        .chart-container {',
            '            position: relative;',
            '            height: 300px;',
            '            margin-top: 1.5rem;',
            '        }',
            '        .empty-state {',
            '            text-align: center;',
            '            padding: 3rem 1.5rem;',
            '            color: var(--secondary-color);',
            '        }',
            '        .empty-state i {',
            '            font-size: 4rem;',
            '            margin-bottom: 1.5rem;',
            '            opacity: 0.5;',
            '        }',
            '        .empty-state h4 {',
            '            font-size: 1.5rem;',
            '            margin-bottom: 1rem;',
            '            color: var(--dark-color);',
            '        }',
            '        .empty-state p {',
            '            max-width: 500px;',
            '            margin: 0 auto;',
            '        }',
            '        .badge {',
            '            padding: 0.5em 0.75em;',
            '            font-weight: 500;',
            '            border-radius: 0.375rem;',
            '        }',
            '        .badge-pill {',
            '            border-radius: 50rem;',
            '        }',
            '        .badge-success {',
            '            background-color: var(--success-color);',
            '            color: #fff;',
            '        }',
            '        .badge-warning {',
            '            background-color: var(--warning-color);',
            '            color: #212529;',
            '        }',
            '        .badge-danger {',
            '            background-color: var(--danger-color);',
            '            color: #fff;',
            '        }',
            '        .badge-info {',
            '            background-color: var(--info-color);',
            '            color: #212529;',
            '        }',
            '        .badge-primary {',
            '            background-color: var(--primary-color);',
            '            color: #fff;',
            '        }',
            '        .badge-secondary {',
            '            background-color: var(--secondary-color);',
            '            color: #fff;',
            '        }',
            '        .footer {',
            '            padding: 1.5rem 0;',
            '            text-align: center;',
            '            color: var(--secondary-color);',
            '            border-top: 1px solid #dee2e6;',
            '            margin-top: 2rem;',
            '        }',
            '        /* Estilos responsivos */    ',
            '        @media (max-width: 767.98px) {',
            '            .main-container {',
            '                padding: 1rem;',
            '            }',
            '            .card-body {',
            '                padding: 1rem;',
            '            }',
            '            .nav-tabs .nav-link {',
            '                padding: 0.5rem 0.75rem;',
            '            }',
            '            .stat-card {',
            '                margin-bottom: 1rem;',
            '            }',
            '            .filter-container {',
            '                padding: 1rem;',
            '            }',
            '            .table-container {',
            '                padding: 1rem;',
            '            }',
            '        }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="container main-container">',
            '        <div class="header">',
            '            <h1><i class="fas fa-hospital-user me-2"></i>Sistema de Historias Clínicas HL7-FHIR</h1>',
            '            <p class="lead">Visualización integrada de datos clínicos en formato estándar HL7-FHIR, permitiendo un acceso unificado a la información médica de los pacientes.</p>',
            '        </div>',
            '',
            '        <!-- Pestañas de navegación -->',
            '        <ul class="nav nav-tabs" id="myTab" role="tablist">',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link active" id="resumen-tab" data-bs-toggle="tab" data-bs-target="#resumen" type="button" role="tab" aria-controls="resumen" aria-selected="true">',
            '                    <i class="fas fa-chart-pie"></i> Resumen General',
            '                </button>',
            '            </li>',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link" id="pacientes-tab" data-bs-toggle="tab" data-bs-target="#pacientes" type="button" role="tab" aria-controls="pacientes" aria-selected="false">',
            '                    <i class="fas fa-user-injured"></i> Pacientes',
            '                </button>',
            '            </li>',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link" id="diagnosticos-tab" data-bs-toggle="tab" data-bs-target="#diagnosticos" type="button" role="tab" aria-controls="diagnosticos" aria-selected="false">',
            '                    <i class="fas fa-stethoscope"></i> Diagnósticos',
            '                </button>',
            '            </li>',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link" id="observaciones-tab" data-bs-toggle="tab" data-bs-target="#observaciones" type="button" role="tab" aria-controls="observaciones" aria-selected="false">',
            '                    <i class="fas fa-clipboard-list"></i> Observaciones',
            '                </button>',
            '            </li>',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link" id="medicamentos-tab" data-bs-toggle="tab" data-bs-target="#medicamentos" type="button" role="tab" aria-controls="medicamentos" aria-selected="false">',
            '                    <i class="fas fa-pills"></i> Medicamentos',
            '                </button>',
            '            </li>',
            '            <li class="nav-item" role="presentation">',
            '                <button class="nav-link" id="procedimientos-tab" data-bs-toggle="tab" data-bs-target="#procedimientos" type="button" role="tab" aria-controls="procedimientos" aria-selected="false">',
            '                    <i class="fas fa-procedures"></i> Procedimientos',
            '                </button>',
            '            </li>',
            '        </ul>',
            '',
            '        <!-- Contenido de las pestañas -->',
            '        <div class="tab-content" id="myTabContent">',
        ]
        
        # Pestaña: Resumen General
        num_pacientes = len(datos["pacientes"])
        num_diagnosticos = len(datos["diagnosticos"])
        num_observaciones = len(datos["observaciones"])
        num_medicamentos = len(datos["medicamentos"])
        num_procedimientos = len(datos["procedimientos"])

        html.extend([
            '            <!-- Resumen General -->',
            '            <div class="tab-pane fade show active" id="resumen" role="tabpanel" aria-labelledby="resumen-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <h2 class="mb-4">Resumen de Datos Clínicos</h2>',
            '                    </div>',
            '                </div>',
            '                <div class="row">',
            '                    <div class="col-md-4 col-sm-6 mb-4">',
            '                        <div class="stat-card bg-primary-gradient">',
            '                            <i class="fas fa-user-injured"></i>',
            f'                            <h2>{num_pacientes}</h2>',
            '                            <p>Pacientes</p>',
            '                        </div>',
            '                    </div>',
            '                    <div class="col-md-4 col-sm-6 mb-4">',
            '                        <div class="stat-card bg-danger-gradient">',
            '                            <i class="fas fa-stethoscope"></i>',
            f'                            <h2>{num_diagnosticos}</h2>',
            '                            <p>Diagnósticos</p>',
            '                        </div>',
            '                    </div>',
            '                    <div class="col-md-4 col-sm-6 mb-4">',
            '                        <div class="stat-card bg-info-gradient">',
            '                            <i class="fas fa-clipboard-list"></i>',
            f'                            <h2>{num_observaciones}</h2>',
            '                            <p>Observaciones</p>',
            '                        </div>',
            '                    </div>',
            '                    <div class="col-md-6 col-sm-6 mb-4">',
            '                        <div class="stat-card bg-success-gradient">',
            '                            <i class="fas fa-pills"></i>',
            f'                            <h2>{num_medicamentos}</h2>',
            '                            <p>Medicamentos</p>',
            '                        </div>',
            '                    </div>',
            '                    <div class="col-md-6 col-sm-6 mb-4">',
            '                        <div class="stat-card bg-warning-gradient">',
            '                            <i class="fas fa-procedures"></i>',
            f'                            <h2>{num_procedimientos}</h2>',
            '                            <p>Procedimientos</p>',
            '                        </div>',
            '                    </div>',
            '                </div>',

            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="card">',
            '                            <div class="card-header">',
            '                                <h4><i class="fas fa-table me-2"></i>Resumen de Pacientes</h4>',
            '                            </div>',
            '                            <div class="card-body">',
            '                                <div class="table-responsive">',
            '                                    <table class="table table-bordered table-hover" id="resumenTable">',
            '                                        <thead class="table-light">',
            '                                            <tr>',
            '                                                <th>ID</th>',
            '                                                <th>Paciente</th>',
            '                                                <th>Género</th>',
            '                                                <th>Edad</th>',
            '                                                <th>Diagnósticos</th>',
            '                                                <th>Obs.</th>',
            '                                                <th>Med.</th>',
            '                                                <th>Proc.</th>',
            '                                            </tr>',
            '                                        </thead>',
            '                                        <tbody>',
        ])

        # Generar filas de pacientes para el resumen
        for paciente in datos["pacientes"]:
            diags = ", ".join([d["descripcion"] for d in paciente["diagnosticos"][:2]]) if paciente["diagnosticos"] else "Ninguno"
            if len(paciente["diagnosticos"]) > 2:
                diags += f" y {len(paciente['diagnosticos'])-2} más"
            
            obs_count = len(paciente["observaciones"])
            meds_count = len(paciente["medicamentos"])
            procs_count = len(paciente["procedimientos"])
            
            html.append(f'                                            <tr>')
            html.append(f'                                                <td>{paciente["id"]}</td>')
            html.append(f'                                                <td>{paciente["nombre"]}</td>')
            html.append(f'                                                <td>{paciente["genero"]}</td>')
            html.append(f'                                                <td>{paciente["edad"]}</td>')
            html.append(f'                                                <td>{diags}</td>')
            html.append(f'                                                <td><span class="badge bg-info rounded-pill">{obs_count}</span></td>')
            html.append(f'                                                <td><span class="badge bg-success rounded-pill">{meds_count}</span></td>')
            html.append(f'                                                <td><span class="badge bg-warning rounded-pill">{procs_count}</span></td>')
            html.append(f'                                            </tr>')

        html.extend([
            '                                        </tbody>',
            '                                    </table>',
            '                                </div>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row mt-4">',
            '                    <div class="col-12">',
            '                        <div class="card">',
            '                            <div class="card-body">',
            '                                <h5 class="card-title">Acerca del Sistema</h5>',
            '                                <p>Este sistema presenta datos clínicos extraídos automáticamente y estructurados según el estándar HL7-FHIR (Fast Healthcare Interoperability Resources).</p>',
            '                                <p>FHIR es un estándar de interoperabilidad que facilita el intercambio de información entre sistemas de salud, permitiendo un acceso unificado y seguro a los datos del paciente.</p>',
            '                                <p><small class="text-muted">Generado automáticamente mediante procesamiento de historias clínicas.</small></p>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])

        # Pestaña: Pacientes
        html.extend([
            '            <!-- Pacientes -->',
            '            <div class="tab-pane fade" id="pacientes" role="tabpanel" aria-labelledby="pacientes-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="filter-container">',
            '                            <h3><i class="fas fa-search me-2"></i>Buscar Pacientes</h3>',
            '                            <div class="position-relative">',
            '                                <input type="text" class="form-control" id="filtrarPacientes" placeholder="Buscar por nombre, ID o diagnóstico...">',
            '                                <i class="fas fa-search search-icon"></i>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="table-container">',
            '                            <h3><i class="fas fa-user-injured me-2"></i>Listado de Pacientes</h3>',
            '                            <div class="table-responsive">',
            '                                <table class="table table-striped table-bordered" id="pacientesTable">',
            '                                    <thead>',
            '                                        <tr>',
            '                                            <th>ID</th>',
            '                                            <th>Paciente</th>',
            '                                            <th>Género</th>',
            '                                            <th>Edad</th>',
            '                                            <th>Diagnósticos</th>',
            '                                            <th>Observaciones</th>',
            '                                            <th>Medicamentos</th>',
            '                                            <th>Procedimientos</th>',
            '                                        </tr>',
            '                                    </thead>',
            '                                    <tbody>',
        ])

        # Generar filas de pacientes
        for paciente in datos["pacientes"]:
            diags = ", ".join([d["descripcion"] for d in paciente["diagnosticos"]]) if paciente["diagnosticos"] else "Ninguno"
            obs_list = ", ".join([o["descripcion"] for o in paciente["observaciones"][:3]]) 
            if len(paciente["observaciones"]) > 3:
                obs_list += f" y {len(paciente['observaciones'])-3} más"
            elif not paciente["observaciones"]:
                obs_list = "Ninguna"
                
            meds_list = ", ".join([m["medicamento"] for m in paciente["medicamentos"][:3]])
            if len(paciente["medicamentos"]) > 3:
                meds_list += f" y {len(paciente['medicamentos'])-3} más"
            elif not paciente["medicamentos"]:
                meds_list = "Ninguno"
                
            procs_list = ", ".join([p["procedimiento"] for p in paciente["procedimientos"][:3]])
            if len(paciente["procedimientos"]) > 3:
                procs_list += f" y {len(paciente['procedimientos'])-3} más"
            elif not paciente["procedimientos"]:
                procs_list = "Ninguno"
            
            html.append(f'                                        <tr>')
            html.append(f'                                            <td>{paciente["id"]}</td>')
            html.append(f'                                            <td>{paciente["nombre"]}</td>')
            html.append(f'                                            <td>{paciente["genero"]}</td>')
            html.append(f'                                            <td>{paciente["edad"]}</td>')
            html.append(f'                                            <td>{diags}</td>')
            html.append(f'                                            <td>{obs_list}</td>')
            html.append(f'                                            <td>{meds_list}</td>')
            html.append(f'                                            <td>{procs_list}</td>')
            html.append(f'                                        </tr>')

        html.extend([
            '                                    </tbody>',
            '                                </table>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])

        # Pestaña: Medicamentos
        html.extend([
            '            <!-- Medicamentos -->',
            '            <div class="tab-pane fade" id="medicamentos" role="tabpanel" aria-labelledby="medicamentos-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="filter-container">',
            '                            <h3><i class="fas fa-search me-2"></i>Buscar Medicamentos</h3>',
            '                            <div class="position-relative">',
            '                                <input type="text" class="form-control" id="filtrarMedicamentos" placeholder="Buscar por medicamento, dosificación o paciente...">',
            '                                <i class="fas fa-search search-icon"></i>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="table-container">',
            '                            <h3><i class="fas fa-pills me-2"></i>Listado de Medicamentos</h3>',
        ])

        # Verificar si hay medicamentos
        if datos["medicamentos"]:
            html.extend([
                '                            <div class="table-responsive">',
                '                                <table class="table table-striped table-bordered" id="medicamentosTable">',
                '                                    <thead>',
                '                                        <tr>',
                '                                            <th>Medicamento</th>',
                '                                            <th>Dosificación</th>',
                '                                            <th>Estado</th>',
                '                                            <th>Paciente</th>',
                '                                            <th>ID Paciente</th>',
                '                                        </tr>',
                '                                    </thead>',
                '                                    <tbody>',
            ])
            
            # Generar filas de medicamentos
            for med in datos["medicamentos"]:
                estado_text = med["estado"]
                estado_class = "badge bg-secondary"
                
                if med["estado"].lower() == "active":
                    estado_class = "badge bg-success"
                    estado_text = "Activo"
                elif med["estado"].lower() == "completed":
                    estado_class = "badge bg-info"
                    estado_text = "Completado"
                elif med["estado"].lower() == "stopped":
                    estado_class = "badge bg-danger"
                    estado_text = "Suspendido"
                    
                html.append(f'                                        <tr>')
                html.append(f'                                            <td>{med["medicamento"]}</td>')
                html.append(f'                                            <td>{med["dosificacion"]}</td>')
                html.append(f'                                            <td><span class="{estado_class}">{estado_text}</span></td>')
                html.append(f'                                            <td>{med["paciente"]}</td>')
                html.append(f'                                            <td>{med["id_paciente"]}</td>')
                html.append(f'                                        </tr>')
            
            html.extend([
                '                                    </tbody>',
                '                                </table>',
                '                            </div>',
            ])
        else:
            # Mostrar estado vacío si no hay medicamentos
            html.extend([
                '                            <div class="empty-state">',
                '                                <i class="fas fa-prescription-bottle"></i>',
                '                                <h4>No hay medicamentos registrados</h4>',
                '                                <p>No se encontraron registros de medicamentos para los pacientes seleccionados.</p>',
                '                            </div>',
            ])

        html.extend([
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])
        
        # Pestaña: Procedimientos
        html.extend([
            '            <!-- Procedimientos -->',
            '            <div class="tab-pane fade" id="procedimientos" role="tabpanel" aria-labelledby="procedimientos-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="filter-container">',
            '                            <h3><i class="fas fa-search me-2"></i>Buscar Procedimientos</h3>',
            '                            <div class="position-relative">',
            '                                <input type="text" class="form-control" id="filtrarProcedimientos" placeholder="Buscar por procedimiento o paciente...">',
            '                                <i class="fas fa-search search-icon"></i>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="table-container">',
            '                            <h3><i class="fas fa-procedures me-2"></i>Listado de Procedimientos</h3>',
        ])

        # Verificar si hay procedimientos
        if datos["procedimientos"]:
            html.extend([
                '                            <div class="table-responsive">',
                '                                <table class="table table-striped table-bordered" id="procedimientosTable">',
                '                                    <thead>',
                '                                        <tr>',
                '                                            <th>Procedimiento</th>',
                '                                            <th>Estado</th>',
                '                                            <th>Fecha</th>',
                '                                            <th>Paciente</th>',
                '                                            <th>ID Paciente</th>',
                '                                        </tr>',
                '                                    </thead>',
                '                                    <tbody>',
            ])
            
            # Generar filas de procedimientos
            for proc in datos["procedimientos"]:
                # Formatear la fecha si es posible
                fecha_formateada = proc["fecha"]
                try:
                    if proc["fecha"] and proc["fecha"] != "Desconocido" and len(proc["fecha"]) > 10:
                        # Intentar formatear la fecha ISO 8601 a un formato más amigable
                        fecha_formateada = proc["fecha"].replace("T", " ").replace("Z", "")
                        if len(fecha_formateada) > 19:
                            fecha_formateada = fecha_formateada[:19]
                except:
                    pass
                    
                # Determinar clase para el estado
                estado_class = "badge bg-secondary"
                estado_text = proc["estado"]
                
                if proc["estado"].lower() == "completed":
                    estado_class = "badge bg-success"
                    estado_text = "Completado"
                elif proc["estado"].lower() == "in-progress":
                    estado_class = "badge bg-info"
                    estado_text = "En progreso"
                elif proc["estado"].lower() == "not-done":
                    estado_class = "badge bg-danger"
                    estado_text = "No realizado"
                elif proc["estado"].lower() == "scheduled":
                    estado_class = "badge bg-warning"
                    estado_text = "Programado"
                    
                html.append(f'                                        <tr>')
                html.append(f'                                            <td>{proc["procedimiento"]}</td>')
                html.append(f'                                            <td><span class="{estado_class}">{estado_text}</span></td>')
                html.append(f'                                            <td>{fecha_formateada}</td>')
                html.append(f'                                            <td>{proc["paciente"]}</td>')
                html.append(f'                                            <td>{proc["id_paciente"]}</td>')
                html.append(f'                                        </tr>')
            
            html.extend([
                '                                    </tbody>',
                '                                </table>',
                '                            </div>',
            ])
        else:
            # Mostrar estado vacío si no hay procedimientos
            html.extend([
                '                            <div class="empty-state">',
                '                                <i class="fas fa-procedures"></i>',
                '                                <h4>No hay procedimientos registrados</h4>',
                '                                <p>No se encontraron registros de procedimientos para los pacientes seleccionados.</p>',
                '                            </div>',
            ])

        html.extend([
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])
        # Pestaña: Diagnósticos
        html.extend([
            '            <!-- Diagnósticos -->',
            '            <div class="tab-pane fade" id="diagnosticos" role="tabpanel" aria-labelledby="diagnosticos-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="filter-container">',
            '                            <h3><i class="fas fa-search me-2"></i>Buscar Diagnósticos</h3>',
            '                            <div class="position-relative">',
            '                                <input type="text" class="form-control" id="filtrarDiagnosticos" placeholder="Buscar por diagnóstico o paciente...">',
            '                                <i class="fas fa-search search-icon"></i>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="table-container">',
            '                            <h3><i class="fas fa-stethoscope me-2"></i>Listado de Diagnósticos</h3>',
            '                            <div class="table-responsive">',
            '                                <table class="table table-striped table-bordered" id="diagnosticosTable">',
            '                                    <thead>',
            '                                        <tr>',
            '                                            <th>Diagnóstico</th>',
            '                                            <th>Estado</th>',
            '                                            <th>Paciente</th>',
            '                                            <th>ID Paciente</th>',
            '                                            <th>Acciones</th>',
            '                                        </tr>',
            '                                    </thead>',
            '                                    <tbody>',
        ])

        # Generar filas de diagnósticos
        for diag in datos["diagnosticos"]:
            estado_class = ""
            if diag["estado"].lower() == "active":
                estado_class = "badge bg-success"
                estado_text = "Activo"
            elif diag["estado"].lower() == "inactive":
                estado_class = "badge bg-secondary"
                estado_text = "Inactivo"
            elif diag["estado"].lower() == "resolved":
                estado_class = "badge bg-info"
                estado_text = "Resuelto"
            else:
                estado_class = "badge bg-warning"
                estado_text = diag["estado"]
                
            html.append(f'                                        <tr>')
            html.append(f'                                            <td>{diag["descripcion"]}</td>')
            html.append(f'                                            <td><span class="{estado_class}">{estado_text}</span></td>')
            html.append(f'                                            <td>{diag["paciente"]}</td>')
            html.append(f'                                            <td>{diag["id_paciente"]}</td>')
            html.append(f'                                            <td><button class="btn btn-sm btn-outline-primary">Ver detalle</button></td>')
            html.append(f'                                        </tr>')

        html.extend([
            '                                    </tbody>',
            '                                </table>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])

        # Pestaña: Observaciones
        html.extend([
            '            <!-- Observaciones -->',
            '            <div class="tab-pane fade" id="observaciones" role="tabpanel" aria-labelledby="observaciones-tab">',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="filter-container">',
            '                            <h3><i class="fas fa-search me-2"></i>Buscar Observaciones</h3>',
            '                            <div class="position-relative">',
            '                                <input type="text" class="form-control" id="filtrarObservaciones" placeholder="Buscar por observación, valor o paciente...">',
            '                                <i class="fas fa-search search-icon"></i>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '',
            '                <div class="row">',
            '                    <div class="col-12">',
            '                        <div class="table-container">',
            '                            <h3><i class="fas fa-clipboard-list me-2"></i>Listado de Observaciones</h3>',
            '                            <div class="table-responsive">',
            '                                <table class="table table-striped table-bordered" id="observacionesTable">',
            '                                    <thead>',
            '                                        <tr>',
            '                                            <th>Observación</th>',
            '                                            <th>Valor</th>',
            '                                            <th>Fecha</th>',
            '                                            <th>Paciente</th>',
            '                                            <th>ID Paciente</th>',
            '                                        </tr>',
            '                                    </thead>',
            '                                    <tbody>',
        ])

        # Generar filas de observaciones
        for obs in datos["observaciones"]:
            # Formatear la fecha si es posible
            fecha_formateada = obs["fecha"]
            try:
                if obs["fecha"] and obs["fecha"] != "Desconocido" and len(obs["fecha"]) > 10:
                    # Intentar formatear la fecha ISO 8601 a un formato más amigable
                    fecha_formateada = obs["fecha"].replace("T", " ").replace("Z", "")
                    if len(fecha_formateada) > 19:
                        fecha_formateada = fecha_formateada[:19]
            except:
                pass
                
            html.append(f'                                        <tr>')
            html.append(f'                                            <td>{obs["descripcion"]}</td>')
            html.append(f'                                            <td><strong>{obs["valor"]}</strong></td>')
            html.append(f'                                            <td>{fecha_formateada}</td>')
            html.append(f'                                            <td>{obs["paciente"]}</td>')
            html.append(f'                                            <td>{obs["id_paciente"]}</td>')
            html.append(f'                                        </tr>')

        html.extend([
            '                                    </tbody>',
            '                                </table>',
            '                            </div>',
            '                        </div>',
            '                    </div>',
            '                </div>',
            '            </div>',
        ])
        # Cierre de la estructura HTML y scripts
        html.extend([
            '        </div>',
            '',
            '        <!-- Footer -->',
            '        <div class="footer">',
            '            <p>Sistema de Historias Clínicas FHIR - Generado automáticamente</p>',
            '            <p><small>HL7-FHIR (Fast Healthcare Interoperability Resources) es un estándar para el intercambio electrónico de información de salud.</small></p>',
            '        </div>',
            '    </div>',
            '',
            '    <!-- Scripts -->',
            '    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>',
            '    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>',
            '    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>',
            '    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>',
            '    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>',
            '    <script>',
            '        document.addEventListener("DOMContentLoaded", function() {',
            '            // Inicializar DataTables para todas las tablas',
            '            $("#resumenTable").DataTable({',
            '                "language": {',
            '                    "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                },',
            '                "pageLength": 5,',
            '                "responsive": true',
            '            });',
            '            ',
            '            $("#pacientesTable").DataTable({',
            '                "language": {',
            '                    "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                },',
            '                "responsive": true',
            '            });',
            '            ',
            '            $("#diagnosticosTable").DataTable({',
            '                "language": {',
            '                    "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                },',
            '                "responsive": true',
            '            });',
            '            ',
            '            $("#observacionesTable").DataTable({',
            '                "language": {',
            '                    "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                },',
            '                "responsive": true',
            '            });',
            '            ',
            '            // Solo inicializar si existen las tablas',
            '            if (document.getElementById("medicamentosTable")) {',
            '                $("#medicamentosTable").DataTable({',
            '                    "language": {',
            '                        "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                    },',
            '                    "responsive": true',
            '                });',
            '            }',
            '            ',
            '            if (document.getElementById("procedimientosTable")) {',
            '                $("#procedimientosTable").DataTable({',
            '                    "language": {',
            '                        "url": "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json"',
            '                    },',
            '                    "responsive": true',
            '                });',
            '            }',
            '',
            '            // Crear gráficos para el dashboard',
            '            // Gráfico de diagnósticos',
            '            const diagnosticoCtx = document.getElementById("diagnosticosChart");',
            '            if (diagnosticoCtx) {',
            '                // Agrupar diagnósticos por tipos',
            '                const diagnosticos = [];',
            '                const conteo = {};',
            '',
            '                // Aquí se asume que datos["diagnosticos"] contiene los datos',
            '                // que quieres representar en el gráfico',
            '                datos["diagnosticos"].forEach(d => {',
            '                    const diag = d.descripcion.split(" - ")[0]; // Usar la primera parte (código)',
            '                    if (conteo[diag]) {',
            '                        conteo[diag]++;',
            '                    } else {',
            '                        conteo[diag] = 1;',
            '                    }',
            '                });',
            '',
            '                // Convertir a arrays para Chart.js',
            '                const diagLabels = Object.keys(conteo);',
            '                const diagData = Object.values(conteo);',
            '',
            '                // Colores para el gráfico',
            '                const colorPalette = [',
            '                    "#0d6efd", "#198754", "#dc3545", "#0dcaf0", "#ffc107",',
            '                    "#6610f2", "#fd7e14", "#20c997", "#d63384", "#6c757d"',
            '                ];',
            '',
            '                // Crear el gráfico de diagnósticos',
            '                new Chart(diagnosticoCtx, {',
            '                    type: "pie",',
            '                    data: {',
            '                        labels: diagLabels,',
            '                        datasets: [{',
            '                            data: diagData,',
            '                            backgroundColor: colorPalette,',
            '                            hoverOffset: 4',
            '                        }]',
            '                    },',
            '                    options: {',
            '                        responsive: true,',
            '                        maintainAspectRatio: false,',
            '                        plugins: {',
            '                            legend: {',
            '                                position: "right",',
            '                            },',
            '                            title: {',
            '                                display: true,',
            '                                text: "Distribución de Diagnósticos"',
            '                            }',
            '                        }',
            '                    }',
            '                });',
            '            }',
            '',
            '            // Gráfico de observaciones por paciente',
            '            const obsCtx = document.getElementById("observacionesChart");',
            '            if (obsCtx) {',
            '                // Preparar datos para el gráfico de observaciones',
            '                const pacientes = [];',
            '                const observaciones = [];',
            '',
            '                // Obtener datos de los 5 pacientes con más observaciones',
            '                datos["pacientes"].forEach(p => {',
            '                    pacientes.push(p.nombre.split(" ")[0]); // Solo primer nombre para simplificar',
            '                    observaciones.push(p.observaciones.length);',
            '                });',
            '',
            '                // Crear el gráfico de observaciones',
            '                new Chart(obsCtx, {',
            '                    type: "bar",',
            '                    data: {',
            '                        labels: pacientes,',
            '                        datasets: [{',
            '                            label: "Número de Observaciones",',
            '                            data: observaciones,',
            '                            backgroundColor: "rgba(13, 110, 253, 0.6)",',
            '                            borderColor: "rgba(13, 110, 253, 1)",',
            '                            borderWidth: 1',
            '                        }]',
            '                    },',
            '                    options: {',
            '                        responsive: true,',
            '                        maintainAspectRatio: false,',
            '                        scales: {',
            '                            y: {',
            '                                beginAtZero: true,',
            '                                title: {',
            '                                    display: true,',
            '                                    text: "Cantidad"',
            '                                }',
            '                            },',
            '                            x: {',
            '                                title: {',
            '                                    display: true,',
            '                                    text: "Paciente"',
            '                                }',
            '                            }',
            '                        },',
            '                        plugins: {',
            '                            title: {',
            '                                display: true,',
            '                                text: "Observaciones por Paciente"',
            '                            }',
            '                        }',
            '                    }',
            '                });',
            '            }',
            '        });',
            '    </script>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html)
        
    def procesar_pdfs_fhir_html(self):
        """
        Recorre todos los PDFs descargados y para cada uno genera:
        1. Extrae texto del PDF
        2. Convierte a formato HL7-FHIR (JSON)
        3. Guarda JSON y lo convierte a XML
        4. Genera una visualización HTML tabular
        
        Al finalizar, genera un HTML global con todas las historias clínicas.
        
        Retorna la cantidad de PDFs procesados exitosamente y la ruta del HTML global.
        """
        procesados_exitosamente = 0
        
        print(f"\n{'='*50}")
        print(f"🔄 PROCESANDO PDFs PARA CONVERTIRLOS A FORMATO FHIR")
        print(f"{'='*50}")
        
        for i, info in enumerate(self.pdfs_info):
            pdf_path = info['ruta']
            base = os.path.splitext(pdf_path)[0]
            json_path = base + '.json'
            xml_path = base + '.xml'
            html_path = base + '.html'
            
            print(f"\n📄 [{i+1}/{len(self.pdfs_info)}] Procesando: {os.path.basename(pdf_path)}")
            
            try:
                # Paso 1: Convertir PDF a formato FHIR (JSON)
                fhir_json = self.convertir_pdf_a_fhir(pdf_path)
                
                if not fhir_json:
                    print(f"⚠️ No se pudo extraer datos FHIR de {pdf_path}. Saltando...")
                    continue
                
                # Paso 2: Guardar JSON
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(fhir_json, jf, ensure_ascii=False, indent=2)
                print(f"✅ JSON guardado: {os.path.basename(json_path)}")
                
                # Paso 3: Generar XML desde JSON
                xml_str = self.generar_xml_de_fhir(fhir_json)
                if xml_str:
                    with open(xml_path, 'w', encoding='utf-8') as xf:
                        xf.write(xml_str)
                    print(f"✅ XML guardado: {os.path.basename(xml_path)}")
                
                # Paso 4: Generar visualización HTML tabular
                if self.generar_html_tabular(fhir_json, html_path, info):
                    print(f"✅ HTML tabular generado: {os.path.basename(html_path)}")
                    procesados_exitosamente += 1
                
            except Exception as e:
                print(f"❌ Error procesando {pdf_path}: {str(e)}")
        
        print(f"\n{'='*50}")
        print(f"📊 RESUMEN: Procesados {procesados_exitosamente}/{len(self.pdfs_info)} archivos PDF")
        print(f"{'='*50}")
        
        # Generar HTML global con todos los datos
        html_global_path = None
        if procesados_exitosamente > 0:
            print(f"\n🔄 Generando vista HTML global de historias clínicas...")
            try:
                html_global_path = self.generar_html_global(self.output_dir)
                print(f"✅ Vista HTML global generada exitosamente")
            except Exception as e:
                print(f"❌ Error generando vista HTML global: {str(e)}")
        
        return procesados_exitosamente, html_global_path

# Modificación del bloque principal
if __name__ == "__main__":
    import argparse
    from datetime import datetime
    import webbrowser  # Para abrir automáticamente el HTML global
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Extractor de Historias Clínicas Medifolios a formato FHIR')
    parser.add_argument('--usuario', '-u', help='Usuario para Medifolios', default="80235068")
    parser.add_argument('--password', '-p', help='Contraseña para Medifolios', default="8U135gf1M")
    parser.add_argument('--pacientes', '-n', type=int, help='Número de pacientes a procesar', default=3)
    parser.add_argument('--dir', '-d', help='Directorio de salida para archivos', 
                       default=os.path.join(os.path.expanduser('~'), 'Downloads', 'historia_clinica', 'output'))
    parser.add_argument('--solo-procesar', '-s', action='store_true', 
                       help='Solo procesar PDFs existentes sin descargar nuevos')
    parser.add_argument('--no-abrir', '-na', action='store_true',
                       help='No abrir automáticamente el HTML generado al finalizar')
    
    args = parser.parse_args()
    
    # Timestamp para carpeta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.dir, f"extraccion_{timestamp}")
    
    print(f"\n{'='*70}")
    print(f"🚀 EXTRACTOR DE HISTORIAS CLÍNICAS MEDIFOLIOS A FORMATO HL7-FHIR")
    print(f"{'='*70}")
    print(f"📅 Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📂 Directorio de salida: {output_dir}")
    print(f"👤 Usuario: {args.usuario}")
    print(f"📊 Pacientes a procesar: {args.pacientes}")
    print(f"{'='*70}\n")
    
    # Crear el directorio de salida
    os.makedirs(output_dir, exist_ok=True)
    
    # Registrar log en archivo
    log_path = os.path.join(output_dir, "extraccion_log.txt")
    
    # Inicializar extractor
    extractor = HistoriasClinicasExtractor(output_dir=output_dir)
    
    html_global_path = None
    
    try:
        if not args.solo_procesar:
            # Proceso de descarga de historias clínicas
            if not extractor.login(args.usuario, args.password):
                print("❌ Falló el inicio de sesión. Finalizando.")
                extractor.cerrar()
                exit(1)
                
            print("✅ Sesión iniciada correctamente")
            
            extractor.navegar_a_pacientes()
            
            print(f"\n🔄 Iniciando descarga de historias clínicas para {args.pacientes} pacientes...")
            # Descargar historias clínicas
            pdfs_info = extractor.descargar_historias_clinicas(args.pacientes)
            
            print("✅ Proceso de descarga completado con éxito")
            
        else:
            print("🔄 Modo solo-procesar: Buscando PDFs existentes en el directorio...")
            # En modo solo-procesar, buscar PDFs existentes en el directorio
            pdfs_encontrados = []
            for archivo in os.listdir(args.dir):
                if archivo.lower().endswith('.pdf'):
                    ruta_completa = os.path.join(args.dir, archivo)
                    # Extraer ID y nombre del paciente del nombre del archivo
                    partes = os.path.splitext(archivo)[0].split('_', 1)
                    id_paciente = partes[0] if len(partes) > 0 else "ID_desconocido"
                    nombre_paciente = partes[1].replace('_', ' ') if len(partes) > 1 else "Nombre desconocido"
                    
                    pdfs_encontrados.append({
                        "ruta": ruta_completa,
                        "id_paciente": id_paciente,
                        "nombre_paciente": nombre_paciente
                    })
            
            if not pdfs_encontrados:
                print("❌ No se encontraron archivos PDF en el directorio. Finalizando.")
                exit(1)
                
            # Copiar los PDFs al directorio de salida y actualizar rutas
            extractor.pdfs_info = []
            for pdf_info in pdfs_encontrados:
                # Crear nombre de archivo
                nombre_archivo = f"{pdf_info['id_paciente']}_{pdf_info['nombre_paciente'].replace(' ', '_')}.pdf"
                nombre_archivo = re.sub(r'[\\/*?:"<>|]', '', nombre_archivo)
                nueva_ruta = os.path.join(output_dir, nombre_archivo)
                
                # Copiar archivo
                import shutil
                shutil.copy2(pdf_info['ruta'], nueva_ruta)
                
                # Actualizar ruta en la información
                pdf_info['ruta'] = nueva_ruta
                extractor.pdfs_info.append(pdf_info)
                
            print(f"✅ Se encontraron {len(extractor.pdfs_info)} PDFs para procesar")
        
        # Procesar PDFs para convertirlos a FHIR
        if extractor.pdfs_info:
            print("\n🔄 Iniciando procesamiento de PDFs a formato FHIR...")
            procesados, html_global_path = extractor.procesar_pdfs_fhir_html()
            
            if procesados > 0:
                print(f"\n✅ Proceso completado exitosamente. Se procesaron {procesados} archivos.")
                
                if html_global_path:
                    print(f"📊 Vista global HTML: {html_global_path}")
                    
                    # Abrir automáticamente el HTML en el navegador si no está desactivado
                    if not args.no_abrir and html_global_path:
                        print(f"🌐 Abriendo visualización HTML en el navegador...")
                        webbrowser.open(f"file://{os.path.abspath(html_global_path)}")
                
                print(f"📂 Resultados guardados en: {output_dir}")
            else:
                print("⚠️ No se pudo procesar ningún archivo PDF correctamente.")
        else:
            print("⚠️ No hay archivos PDF para procesar.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Cerrar navegador solo si estábamos descargando, no en modo solo-procesar
        if not args.solo_procesar:
            extractor.cerrar()
        
        print(f"\n👋 Proceso finalizado. {'Resultados guardados en: ' + output_dir if extractor.pdfs_info else ''}")
        
        # Recordar al usuario el camino del HTML global
        if html_global_path:
            print(f"\n🔍 Para visualizar las historias clínicas, abra: {html_global_path}")