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
    def __init__(self, output_dir="D:\\Downloads\\historias_medifolios"):
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

    def descargar_historias_clinicas(self, num_pacientes=10):
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
    
# Modificación del bloque principal
if __name__ == "__main__":
    import argparse
    from datetime import datetime
    import webbrowser  # Para abrir automáticamente el HTML global
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Extractor de Historias Clínicas Medifolios a formato FHIR')
    parser.add_argument('--usuario', '-u', help='Usuario para Medifolios', default="80235068")
    parser.add_argument('--password', '-p', help='Contraseña para Medifolios', default="8U135gf1M")
    parser.add_argument('--pacientes', '-n', type=int, help='Número de pacientes a procesar', default=10)
    parser.add_argument('--dir', '-d', help='Directorio de salida para archivos', 
                       default=os.path.join(os.path.expanduser('~'), 'Downloads', 'historia_clinica', 'output'))
    parser.add_argument('--solo-procesar', '-s', action='store_true', 
                       help='Solo procesar PDFs existentes sin descargar nuevos')
    parser.add_argument('--no-abrir', '-na', action='store_true',
                       help='No abrir automáticamente el HTML generado al finalizar')
    
    args = parser.parse_args()
    
    # Timestamp para carpeta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "D:\\Downloads\\historias_medifolios"
    
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
    except Exception as e:
        print(f"Error inesperado: {e}")        
        