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
            # Cerrar el diálogo que aparece - usar selector más específico
            try:
                cerrar_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@class='ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only ui-dialog-titlebar-close']"))
                )
                cerrar_btn.click()
                print("✅ Diálogo cerrado usando selector XPATH")
            except Exception as e:
                print(f"⚠️ Error con selector XPATH, intentando alternativa: {str(e)}")
                try:
                    # Intentar con un selector más genérico
                    cerrar_btn = self.driver.find_element(By.CSS_SELECTOR, "button.ui-dialog-titlebar-close")
                    cerrar_btn.click()
                    print("✅ Diálogo cerrado usando selector CSS alternativo")
                except Exception as e2:
                    print(f"⚠️ Error con selector alternativo: {str(e2)}")
                    try:
                        # Último intento con JavaScript
                        self.driver.execute_script("document.querySelector('.ui-dialog-titlebar-close').click();")
                        print("✅ Diálogo cerrado usando JavaScript")
                    except Exception as e3:
                        print(f"❌ No se pudo cerrar el diálogo: {str(e3)}")
            
            time.sleep(3)  # Esperar después de cerrar el diálogo
            
            # Verificar si hay un overlay y removerlo si existe
            try:
                overlay = self.driver.find_element(By.CSS_SELECTOR, "div.ui-widget-overlay")
                if overlay:
                    print("⚠️ Detectado overlay, intentando removerlo...")
                    self.driver.execute_script("arguments[0].remove();", overlay)
                    print("✅ Overlay removido")
            except Exception as e:
                print("✅ No se encontró overlay o no fue necesario removerlo")
                
            time.sleep(2)  # Esperar un poco más para asegurar que todo esté listo
        except Exception as e:
            print(f"❌ Error general al cerrar ventana: {str(e)}")

    def visualizar_historia(self):
        try:
            # Verificar si hay un overlay y removerlo si existe
            try:
                overlays = self.driver.find_elements(By.CSS_SELECTOR, "div.ui-widget-overlay, div.ui-front")
                if overlays:
                    print(f"⚠️ Detectados {len(overlays)} overlays antes de historial, intentando removerlos...")
                    for overlay in overlays:
                        self.driver.execute_script("arguments[0].remove();", overlay)
                    print("✅ Overlays removidos")
            except Exception as e:
                print(f"ℹ️ No se removieron overlays: {str(e)}")
                
            time.sleep(2)  # Esperar para asegurar que todo esté listo
            
            # Click en Historial del Paciente con JavaScript para evitar bloqueos
            try:
                historial_btn = self.wait.until(
                    EC.presence_of_element_located((By.ID, "btnPanelHistorico"))
                )
                self.driver.execute_script("arguments[0].click();", historial_btn)
                print("✅ Historial de paciente abierto (usando JavaScript)")
            except Exception as e:
                print(f"❌ Error al abrir historial con JavaScript: {str(e)}")
                # Intentar con método tradicional como respaldo
                historial_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "btnPanelHistorico"))
                )
                historial_btn.click()
                print("✅ Historial de paciente abierto (método tradicional)")
                
            time.sleep(4)  # Esperar más tiempo para asegurar que el panel de historial se haya cargado completamente

            # Seleccionar todas las historias
            checkbox = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnSeleccionarHistorias"))
            )
            checkbox.click()
            print("✅ Historias seleccionadas")
            time.sleep(2)

            # Visualizar seleccionado
            visualizar_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnVisualizarSeleccionado"))
            )
            visualizar_btn.click()
            print("✅ Visualizando historias seleccionadas")
            time.sleep(3)

            # Imprimir
            imprimir_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btn_imprimir_visualizar_historia"))
            )
            imprimir_btn.click()
            print("✅ Historia clínica visualizada e impresa")
            time.sleep(3)
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