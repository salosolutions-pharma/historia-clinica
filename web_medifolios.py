from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class HistoriasClinicasExtractor:
    def login(self, usuario, password):
        print(f"🔑 Iniciando sesión con usuario: {usuario}")
        self.driver.get("https://www.medifolios.net")

        # Click en botón INGRESO
        try:
            ingreso_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'server0medifolios.net') and contains(text(), 'INGRESO')]"))
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
        except Exception as e:
            print(f"❌ Error en formulario de login: {str(e)}")
            return False

        time.sleep(5)
        return True

    def navegar_a_pacientes(self):
        try:
            # Click en menú Bienvenido (abre el menú)
            menu_bienvenido = self.wait.until(
                EC.element_to_be_clickable((By.ID, "OpenMenuMedifolios"))
            )
            menu_bienvenido.click()
            time.sleep(1)

            # Click en Pacientes
            pacientes_btn = self.driver.find_element(By.XPATH, "//a[contains(@href,'SALUD_HOME/paciente')]")
            pacientes_btn.click()
            print("✅ Sección pacientes abierta")
        except Exception as e:
            print(f"❌ Error navegando a pacientes: {str(e)}")

    def abrir_listado_pacientes(self):
        try:
            listado_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnListadoPacientes"))
            )
            listado_btn.click()
            print("✅ Listado de pacientes abierto")
        except Exception as e:
            print(f"❌ No se pudo abrir el listado de pacientes: {str(e)}")

    def visualizar_historia(self):
        try:
            # Click botón editar paciente (simulación)
            editar_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnCodPacienteListado"))
            )
            editar_btn.click()
            time.sleep(2)

            # Cerrar modal
            cerrar_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ui-dialog-titlebar-close"))
            )
            cerrar_btn.click()
            time.sleep(1)

            # Historial del paciente
            historial_btn = self.driver.find_element(By.ID, "btnPanelHistorico")
            historial_btn.click()
            time.sleep(2)

            # Seleccionar todas las historias
            checkbox = self.driver.find_element(By.ID, "btnSeleccionarHistorias")
            checkbox.click()
            time.sleep(1)

            # Visualizar seleccionado
            visualizar_btn = self.driver.find_element(By.ID, "btnVisualizarSeleccionado")
            visualizar_btn.click()
            time.sleep(2)

            # Imprimir historia
            imprimir_btn = self.driver.find_element(By.ID, "btn_imprimir_visualizar_historia")
            imprimir_btn.click()
            print("✅ Historia clínica visualizada e impresa")
        except Exception as e:
            print(f"❌ Error al visualizar historia clínica: {str(e)}")
