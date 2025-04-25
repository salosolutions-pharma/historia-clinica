from selenium.webdriver.common.by import By 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

class HistoriasClinicasExtractor:
    def __init__(self):
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
                #"download.default_directory": 'D:\Downloads\historias_medifolios',  # Dirección donde se descarga
                "plugins.always_open_pdf_externally": False  # Forzar descarga PDF
            }
        )
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

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
            time.sleep(3)
            
            # Click en botón editar (el primero que encuentre)
            editar_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnCodPacienteListado"))
            )
            editar_btn.click()
            print("✅ Botón editar clicado")
            time.sleep(3)  # Esperar a que aparezca el diálogo
        except Exception as e:
            print(f"❌ Error en listado de pacientes: {str(e)}")
            
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

    
    def visualizar_historia(self):
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

            print("🖨️ Generando PDF desde visor...")
            ruta_pdf = "D:\\Downloads\\historias_medifolios\\historia2.pdf"
            self.imprimir_con_cdp(ruta_pdf)

            # Verificar el número de ventanas abiertas después de cerrar la pestaña
            print(f"Ventanas abiertas después de cerrar la pestaña del PDF: {len(self.driver.window_handles)}")
            self.driver.close()  # Cerrar pestaña del reporte
            self.driver.switch_to.window(self.driver.window_handles[0])
            print(f"✅ Regresado a la ventana principal. Ventanas abiertas: {len(self.driver.window_handles)}")
            time.sleep(9)

        
        except Exception as e:
            print(f"❌ Error al visualizar historia clínica: {str(e)}")

    def cerrar_visor_historia(self):
        try:
            # Esperar a que el botón de cerrar esté disponible y sea clickeable
            print("🔍 Buscando el botón de cierre del visor...")
        
            close_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ui-button-icon-only') and @title='Close']"))
            )
            
            # Hacer clic en el botón para cerrar el visor de la historia
            close_button.click()
            print("✅ Botón de cierre del visor clicado con éxito.")
            
            # Esperar unos segundos para asegurarse de que la ventana se cierra correctamente
            time.sleep(2)
        
        except Exception as e:
            print(f"❌ Error al intentar cerrar el visor de la historia clínica: {str(e)}")
        

    def cerrar(self):
        print("👋 Cerrando navegador...")
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")



# -----------------------------------------------------
# MAIN PARA EJECUCIÓN DESDE ESTE MISMO ARCHIVO
# -----------------------------------------------------

if __name__ == "__main__":
    print("🚀 Iniciando proceso en Medifolios...")

    # Credenciales directamente aquí
    USUARIO = "80235068"
    PASSWORD = "8U135gf1M"

    extractor = HistoriasClinicasExtractor()

    try:
        if not extractor.login(USUARIO, PASSWORD):
            print("❌ Falló el inicio de sesión. Finalizando.")
            extractor.cerrar()
            exit()

        extractor.navegar_a_pacientes()
        extractor.abrir_listado_pacientes()
        
        print("🧹 Limpiando ventanas antes de continuar...")
        extractor.cerrar_ventana()  # Cerrar la ventana después de abrir el listado
        
        print("📋 Accediendo al historial clínico...")
        extractor.visualizar_historia()
        extractor.cerrar_visor_historia()

        print("✅ Proceso completado con éxito")

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

    finally:
        extractor.cerrar()