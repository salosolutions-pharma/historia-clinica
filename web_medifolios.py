from selenium.webdriver.common.by import By 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

class HistoriasClinicasExtractor:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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

    def visualizar_historia(self):
        try:
            # Dar tiempo para que la página se estabilice después de cerrar diálogos
            time.sleep(3)
            
            # Limpiar posibles overlays antes de interactuar con el historial
            self._limpiar_overlays()
            
            print("🔍 Buscando botón de historial clínico...")
            
            # Intentar hacer clic con JavaScript primero (más confiable cuando hay problemas de superposición)
            try:
                historial_btn = self.wait.until(
                    EC.presence_of_element_located((By.ID, "btnPanelHistorico"))
                )
                # Hacer scroll al elemento para asegurarnos que está visible
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", historial_btn)
                time.sleep(1)  # Breve pausa después del scroll
                
                # Hacer clic con JavaScript
                self.driver.execute_script("arguments[0].click();", historial_btn)
                print("✅ Historial de paciente abierto (usando JavaScript)")
            except Exception as e:
                print(f"⚠️ Error al hacer clic en historial con JavaScript: {str(e)[:100]}...")
                # Último intento con clic normal
                try:
                    historial_btn = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "btnPanelHistorico"))
                    )
                    historial_btn.click()
                    print("✅ Historial de paciente abierto (clic normal)")
                except Exception as e2:
                    print(f"❌ No se pudo acceder al historial: {str(e2)[:100]}...")
                    raise Exception("No se pudo acceder al historial clínico")
            
            # Esperar a que cargue el panel de historial
            time.sleep(5)
            
            # Seleccionar todas las historias usando JavaScript
            try:
                print("🔍 Buscando checkbox para seleccionar historias...")
                checkbox = self.wait.until(
                    EC.presence_of_element_located((By.ID, "btnSeleccionarHistorias"))
                )
                # Hacer scroll y asegurar visibilidad
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(1)
                # Clic con JavaScript
                self.driver.execute_script("arguments[0].click();", checkbox)
                print("✅ Historias seleccionadas (usando JavaScript)")
            except Exception as e:
                print(f"❌ Error al seleccionar historias: {str(e)[:100]}...")
                raise Exception("No se pudieron seleccionar las historias")

            time.sleep(2)

            # Visualizar seleccionado con JavaScript
            try:
                print("🔍 Buscando botón para visualizar seleccionado...")
                visualizar_btn = self.wait.until(
                    EC.presence_of_element_located((By.ID, "btnVisualizarSeleccionado"))
                )
                # Hacer scroll y asegurar visibilidad
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", visualizar_btn)
                time.sleep(1)
                # Clic con JavaScript
                self.driver.execute_script("arguments[0].click();", visualizar_btn)
                print("✅ Visualizando historias seleccionadas (usando JavaScript)")
            except Exception as e:
                print(f"❌ Error al visualizar historias: {str(e)[:100]}...")
                raise Exception("No se pudieron visualizar las historias seleccionadas")

            time.sleep(4)

            # Imprimir con JavaScript
            try:
                print("🔍 Buscando botón para imprimir...")
                imprimir_btn = self.wait.until(
                    EC.presence_of_element_located((By.ID, "btn_imprimir_visualizar_historia"))
                )
                # Hacer scroll y asegurar visibilidad
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", imprimir_btn)
                time.sleep(1)
                # Clic con JavaScript
                self.driver.execute_script("arguments[0].click();", imprimir_btn)
                print("✅ Historia clínica visualizada e impresa (usando JavaScript)")
            except Exception as e:
                print(f"❌ Error al imprimir historia: {str(e)[:100]}...")
                raise Exception("No se pudo imprimir la historia clínica")

            time.sleep(3)
            print("🎉 Proceso de visualización de historia clínica completado exitosamente")
        except Exception as e:
            print(f"❌ Error al visualizar historia clínica: {str(e)}")
    
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

        print("✅ Proceso completado con éxito")

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

    finally:
        extractor.cerrar()