import time
import os
import json
import tempfile
import base64
import requests
import re
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageEnhance


load_dotenv()

class AvicenaLogin:
    def __init__(self, download_dir=None):
        """Inicializa el navegador para login en Avicena y cliente OpenAI"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL"}
        )
        if download_dir:
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
            }
            chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd("Network.enable", {})
        self.wait = WebDriverWait(self.driver, 10)

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No se encontró la API key de OpenAI en las variables de entorno")
        self.openai_client = OpenAI(api_key=api_key)

    def presionar_consultar_historia_clinica(self):
        try:

            form_menu = self.wait.until(
                EC.visibility_of_element_located((By.ID, "formMenu"))
            )
            print('Presionar consulta se esta ejecutando')

            actions = ActionChains(self.driver)
            actions.move_to_element(form_menu).perform()  

            print("✅ Menú desplegado tras hover")

            consultar_historia_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formMenu:ctlItemConsultarHistoria:anchor"))
            )
            consultar_historia_btn.click()  # Hacer clic en el enlace
            print("✅ Historia Clínica Avicena abierta")

            time.sleep(5)

        except Exception as e:
            print(f"❌ Error al abrir Historia Clínica Avicena: {str(e)}")
    
    def seleccionar_tipo_identificacion(self):
        try:
            select_element = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlTipoIdentificacion"))
            )
        
            select = Select(select_element)
            
            select.select_by_value("433")
            
            print("✅ 'Cédula de ciudadanía' seleccionada correctamente.")
        
        except Exception as e:
            print(f"❌ Error al seleccionar el tipo de identificación: {str(e)}")
            traceback.print_exc()

    def ingresar_numero_documento(self, numero_documento="41389309"):
        try:
            campo_documento = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlNumeroDocumento"))
            )
            
            campo_documento.send_keys(numero_documento)
            
            print(f"✅ Número de documento '{numero_documento}' ingresado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al ingresar el número de documento: {str(e)}")
            traceback.print_exc()

    def clic_buscar(self):
        """Hace clic en el botón 'Buscar'."""
        try:
    
            boton_buscar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:buscar1"))
            )
            
            boton_buscar.click()
            
            print("✅ Botón 'Buscar' clickeado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al hacer clic en el botón 'Buscar': {str(e)}")
            traceback.print_exc()
       
    def clic_consultar_historia_sophia(self):
        """Hace clic en el botón de consultar historia clínica."""
        try:
            boton_consultar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlFolios:0:sophiaBtn"))
            )
            
            boton_consultar.click()
            
            print("✅ Botón 'Consultar Historia Clínica' clickeado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al hacer clic en el botón 'Consultar Historia Clínica': {str(e)}")
            traceback.print_exc()

    def cambiar_a_nueva_ventana(self):
        try:
            time.sleep(2)

            ventanas = self.driver.window_handles
            print(len(ventanas))
            self.driver.switch_to.window(ventanas[1])
            print("✅ Cambiado al contexto de la nueva ventana.")
        
        except Exception as e:
            print(f"❌ Error al cambiar a la nueva ventana: {str(e)}")
            traceback.print_exc()
        
    def presionar_boton_regresar(self):
        """Método mejorado para hacer clic en el botón 'Regresar' con verificación de éxito"""
        max_intentos = 3
        for intento in range(max_intentos):
            try:
                # Usar un tiempo de espera más largo
                wait_boton = WebDriverWait(self.driver, 15)
                boton_regresar = wait_boton.until(
                    EC.element_to_be_clickable((By.ID, "form:botonVolver"))
                )
                
                # Hacer scroll para asegurar que el botón es visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", boton_regresar)
                time.sleep(1)
                
                # Intentar primero con click normal
                boton_regresar.click()
                print(f"✅ Botón 'Regresar' clickeado correctamente (intento {intento+1}).")
                
                # Esperar a que la tabla de resultados sea visible nuevamente
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "form:ctlFolios"))
                    )
                    print("✅ Retorno a la tabla de resultados confirmado.")
                    return True
                except TimeoutException:
                    print("⚠️ No se detectó retorno a la tabla de resultados.")
                    if intento < max_intentos - 1:
                        # Si no funcionó el clic normal, intentar con JavaScript
                        self.driver.execute_script("arguments[0].click();", boton_regresar)
                        time.sleep(5)
            except Exception as e:
                print(f"⚠️ Error en intento {intento+1}/{max_intentos} al hacer clic en 'Regresar': {str(e)}")
                if intento < max_intentos - 1:
                    time.sleep(3)
                else:
                    return False
        
        # Verificación final
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "form:ctlFolios"))
            ) is not None
        except:
            return False

    def descargar_historia(self, indice=0):
        try:
            print(f"Esperando a que la tabla esté completamente cargada para registro #{indice}...")
            tabla = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:ctlFolios"))
            )

            boton_id = f"form:ctlFolios:{indice}:verhcSophia"
            boton = self.wait.until(
                EC.presence_of_element_located((By.ID, boton_id))
            )
            print(f"✅ Botón con ID {boton_id} encontrado.")

            self.driver.execute_script("arguments[0].scrollIntoView();", boton)
            time.sleep(1) 
            print(f"✅ Botón con ID {boton_id} ahora visible.")

            boton.click()
            print("✅ Modal del visor PDF cargado correctamente.")
            
        except Exception as e:
            print(f"❌ Error al cargar el PDF #{indice}: {str(e)}")
            traceback.print_exc()

    def descargar_pdf_con_url(self, pdf_url, save_path):
        """Descarga un PDF directamente usando la URL proporcionada"""
        try:
            print(f"📥 Descargando PDF desde URL: {pdf_url}")
            
            # Construir sesión requests con cookies de Selenium
            session = requests.Session()
            for ck in self.driver.get_cookies():
                session.cookies.set(ck["name"], ck["value"])
            
            # Hacer la petición y guardar el contenido
            resp = session.get(pdf_url, stream=True, timeout=30)
            resp.raise_for_status()
            
            # Guardar el PDF
            with open(save_path, "wb") as f:
                total_size = 0
                for chunk in resp.iter_content(1024 * 50):
                    f.write(chunk)
                    total_size += len(chunk)
            
            print(f"✅ PDF descargado correctamente en: {save_path} (Tamaño: {total_size/1024:.2f} KB)")
            return save_path
        except Exception as e:
            print(f"❌ Error al descargar PDF: {str(e)}")
            traceback.print_exc()
            raise

    def obtener_url_pdf(self, timeout=20):
        """Método mejorado para obtener la URL del PDF con registro de intentos y limpieza de logs"""
        print("🔍 Buscando URL del PDF en los logs de red...")
        
        # Limpiar logs anteriores para evitar confusiones
        self.driver.get_log("performance")
        
        deadline = time.time() + timeout
        intentos = 0
        while time.time() < deadline:
            intentos += 1
            if intentos % 5 == 0:
                print(f"⏳ Búsqueda de URL PDF en progreso... ({intentos} intentos)")
            
            logs = self.driver.get_log("performance")
            for entry in logs:
                try:
                    msg = json.loads(entry["message"])["message"]
                    if (
                        msg.get("method") == "Network.responseReceived"
                        and msg.get("params", {}).get("response", {}).get("mimeType") == "application/pdf"
                    ):
                        url = msg["params"]["response"]["url"]
                        print(f"✅ URL de PDF encontrada después de {intentos} intentos: {url}")
                        return url
                except (KeyError, json.JSONDecodeError):
                    continue
            time.sleep(0.5)
        
        raise TimeoutError(f"No se encontró ninguna respuesta PDF después de {timeout}s y {intentos} intentos")

    def descargar_pdf_directo(self, save_path):
        # 1) Extraer la URL desde el log
        pdf_url = self.obtener_url_pdf()

        # 2) Construir sesión requests con cookies de Selenium
        session = requests.Session()
        for ck in self.driver.get_cookies():
            session.cookies.set(ck["name"], ck["value"])

        # 3) Hacer la petición y guardar el contenido
        resp = session.get(pdf_url, stream=True)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(1024 * 50):
                f.write(chunk)

        print(f"✅ PDF descargado correctamente en: {save_path}")
        return save_path

    def login(self, usuario, password):
        print(f"🔑 Iniciando sesión en Avicena con usuario: {usuario}")
        self.driver.get("https://avicena.colsanitas.com/His/login.seam")

        try:
            usuario_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "ctlFormLogin:idUserNameLogin"))
            )
            password_input = self.driver.find_element(By.ID, "ctlFormLogin:idPwdLogin")

            usuario_input.send_keys(usuario)
            password_input.send_keys(password)

            print("🤖 Resolviendo captcha con OpenAI...")
            captcha_value = self._resolver_captcha_con_openai()

            if not captcha_value:
                print("❌ No se pudo resolver el captcha automáticamente")

                captcha_value = self._resolver_captcha_manual()

            if not captcha_value:
                print("❌ No se ingresó el captcha")
                return False

            print(f"✅ Captcha resuelto: {captcha_value}")

            captcha_input = self.driver.find_element(By.ID, "ctlFormLogin:idCodSegCaptcha")
            captcha_input.send_keys(captcha_value)

            login_btn = self.driver.find_element(By.ID, "ctlFormLogin:botonValidar")
            login_btn.click()

            try:
                self.wait.until_not(
                    EC.presence_of_element_located((By.ID, "ctlFormLogin:botonValidar"))
                )
                print("✅ Inicio de sesión exitoso")
                return True
            except TimeoutException:
                try:
                    error_msg = self.driver.find_element(By.CLASS_NAME, "mensajeErrorLogin").text
                    print(f"❌ Error en el inicio de sesión: {error_msg}")

                    if "captcha" in error_msg.lower():
                        print("🔄 Reintentando con un nuevo captcha...")
                        return self.login(usuario, password)
                except:
                    print("❌ Error en el inicio de sesión: Tiempo de espera excedido")
                return False

        except Exception as e:
            print(f"❌ Error en el formulario de login: {str(e)}")
            return False

    def _resolver_captcha_con_openai(self):

        try:
            captcha_img = self.driver.find_element(By.XPATH, "//img[contains(@id, 'ctlFormLogin:j_id')]")

            captcha_path = os.path.join(tempfile.gettempdir(), "captcha.png")
            captcha_img.screenshot(captcha_path)

            print(f"🔍 Captcha guardado en: {captcha_path}")

            self._mejorar_imagen_captcha(captcha_path)

            with open(captcha_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un sistema especializado en OCR de captchas. Tu tarea es identificar los caracteres numéricos en la imagen de captcha proporcionada. Sólo responde con los números que veas, sin ningún texto adicional."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Reconoce el código numérico en esta imagen de captcha. La imagen solo contiene números. Responde SOLO con los números, sin ningún texto adicional ni explicaciones."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10
            )

            captcha_text = response.choices[0].message.content.strip()
            captcha_text = re.sub(r'[^0-9]', '', captcha_text)

            return captcha_text

        except Exception as e:
            print(f"❌ Error al resolver el captcha con OpenAI: {str(e)}")
            return None

    def _mejorar_imagen_captcha(self, image_path):
        try:
            img = Image.open(image_path)

            img = img.convert('L')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)

            # Guardar la imagen mejorada
            img.save(image_path)

        except Exception as e:
            print(f"⚠️ Error al mejorar imagen: {str(e)}")

    def _resolver_captcha_manual(self):
        
        captcha_img = self.driver.find_element(By.XPATH, "//img[contains(@id, 'ctlFormLogin:j_id')]")

        captcha_path = os.path.join(tempfile.gettempdir(), "captcha.png")
        captcha_img.screenshot(captcha_path)

        print(f"🔍 Captcha guardado en: {captcha_path}")
        print("⚠️ Resolución automática falló. Por favor, abre esta imagen y revisa el código del captcha")

        captcha_value = input("📝 Ingresa el código del captcha que ves en la imagen: ")

        return captcha_value

    
    def seleccionar_sucursal(self, valor_sucursal="29374"):
        print(f"🔄 Seleccionando sucursal con valor: {valor_sucursal}")
        try:

            select_el = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formIngreso:ctlSucursales"))
            )
            select = Select(select_el)

            print(f"   Encontrado elemento select, intentando seleccionar valor '{valor_sucursal}'...")
            select.select_by_value(valor_sucursal)
            print(f"✅ Valor '{valor_sucursal}' seleccionado en el dropdown.")

        except TimeoutException:
             print(f"❌ TimeoutException: No se pudo encontrar o hacer clic en el elemento select 'formIngreso:ctlSucursales' después de esperar.")
             raise 
        except Exception as e:
            print(f"❌ Error inesperado al seleccionar la sucursal: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


    def presionar_ingresar(self, retries=3, delay=0.5):

        print("🔄 Ejecutando la función presionar_ingresar...")

        for attempt in range(retries):
            try:
                
                print(f"   (Intento {attempt + 1}/{retries}) Esperando que el botón 'Ingresar' sea clickeable...")
                ingresar_btn = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "formIngreso:btnIngresar"))
                )
                print(f"✅ (Intento {attempt + 1}/{retries}) El botón 'Ingresar' está clickeable.")

               
                print(f"   (Intento {attempt + 1}/{retries}) Haciendo clic...")
                ingresar_btn.click()

                print("✅ Clic en 'Ingresar' ejecutado exitosamente.")
                
                return True

            except StaleElementReferenceException:
                print(f"⚠️ (Intento {attempt + 1}/{retries}) StaleElementReferenceException encontrada.")
                if attempt < retries - 1:
                    print(f"   Reintentando en {delay} segundos...")
                    time.sleep(delay)
                else:
                    print(f"❌ StaleElementReferenceException después de {retries} intentos. Fallando.")

                    return False 

            except TimeoutException:
                 print(f"❌ (Intento {attempt + 1}/{retries}) TimeoutException: El botón no se volvió clickeable.")
                 return False 

            except ElementClickInterceptedException:
                 print(f"⚠️ (Intento {attempt + 1}/{retries}) ElementClickInterceptedException: Otro elemento está bloqueando el clic.")
                 if attempt < retries - 1:
                      print(f"   Reintentando en {delay} segundos...")
                      time.sleep(delay)
                 else:
                      print(f"❌ ElementClickInterceptedException después de {retries} intentos. Fallando.")
                      return False 

            except Exception as e:
                print(f"❌ Error inesperado al hacer clic en el botón 'Ingresar' (Intento {attempt + 1}): {str(e)}")
                import traceback
                traceback.print_exc()
                return False 

        print(f"❌ No se pudo hacer clic en el botón 'Ingresar' después de {retries} intentos.")
        return False

    def cerrar(self):
        """Cierra el navegador"""
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")
            
    def descargar_multiples_historias(self, cantidad=3):
        """Descarga múltiples historias clínicas en secuencia"""
        download_dir = os.path.join(os.getcwd(), "descargas")
        os.makedirs(download_dir, exist_ok=True)
        
        pdfs_descargados = []
        
        for i in range(cantidad):
            try:
                # Generar nombre único para el PDF
                pdf_path = os.path.join(download_dir, f"historia_clinica_{i+1}.pdf")
                
                print(f"\n🔄 Descargando historia clínica #{i+1} (índice {i})...")
                
                # Verificar que estamos en la vista de lista
                tabla = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "form:ctlFolios"))
                )
                print("✅ Tabla de resultados presente y lista para interacción.")
                
                # Construir ID del botón específico para este índice
                boton_id = f"form:ctlFolios:{i}:verhcSophia"
                
                # Esperar a que el botón específico esté presente
                boton = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, boton_id))
                )
                print(f"✅ Botón con ID {boton_id} encontrado.")
                
                # Hacer scroll hasta el botón para asegurarse que es visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
                time.sleep(2)  # Esperar después del scroll
                
                # Hacer clic en el botón
                boton.click()
                print(f"✅ Clic en botón {boton_id} realizado.")
                
                # Esperar a que el visor PDF se cargue completamente
                print("⏳ Esperando a que el visor PDF se cargue completamente...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "form:botonVolver"))
                )
                time.sleep(7)  # Tiempo ampliado para asegurar carga completa del PDF
                
                # IMPORTANTE: Obtener la URL del PDF SOLO UNA VEZ y usarla directamente
                try:
                    pdf_url = self.obtener_url_pdf(timeout=20)
                    print(f"✅ URL de PDF encontrada: {pdf_url}")
                    
                    # Descargar el PDF DIRECTAMENTE usando la URL que ya tenemos
                    self.descargar_pdf_con_url(pdf_url, pdf_path)
                    
                    # Verificar que el archivo existe y no tiene tamaño cero
                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                        print(f"✅ PDF #{i+1} descargado correctamente: {pdf_path}")
                        pdfs_descargados.append(pdf_path)
                    else:
                        print(f"⚠️ El archivo PDF #{i+1} no se descargó correctamente o está vacío")
                except Exception as e:
                    print(f"❌ Error al descargar PDF #{i+1}: {str(e)}")
                    traceback.print_exc()
                
                # Presionar el botón "Regresar" para volver a la lista
                print("⏳ Presionando botón Regresar...")
                self.presionar_boton_regresar()
                
                # Esperar tiempo suficiente para que se cierre el modal y se actualice la interfaz
                print("⏳ Esperando a que la interfaz se actualice completamente...")
                time.sleep(5)  # Tiempo entre descargas
                
            except Exception as e:
                print(f"❌ Error al procesar historia clínica #{i+1}: {str(e)}")
                traceback.print_exc()
                
        return pdfs_descargados



if __name__ == "__main__":
    print("🚀 Iniciando proceso de login en Avicena Colsanitas...")

    USUARIO = os.environ.get("AVICENA_USUARIO")
    PASSWORD = os.environ.get("AVICENA_PASSWORD")
    API_KEY  = os.environ.get("OPENAI_API_KEY")

    if not (USUARIO and PASSWORD and API_KEY):
        print("❌ Faltan variables de entorno. Asegúrate de tener en .env:")
        print("   AVICENA_USUARIO, AVICENA_PASSWORD, OPENAI_API_KEY")
        exit(1)

    download_dir = os.path.join(os.getcwd(), "descargas")
    os.makedirs(download_dir, exist_ok=True)

    avicena = None
    try:
        avicena = AvicenaLogin(download_dir=download_dir)

        if not avicena.login(USUARIO, PASSWORD):
            print("❌ Falló el inicio de sesión. Saliendo.")
            exit(1)

        avicena.seleccionar_sucursal("29374")
        avicena.presionar_ingresar()
        avicena.presionar_consultar_historia_clinica()
        avicena.seleccionar_tipo_identificacion()
        avicena.ingresar_numero_documento("41389309")
        avicena.clic_buscar()
        avicena.clic_consultar_historia_sophia()
        avicena.cambiar_a_nueva_ventana()
        
        # Usar el método modificado para descargar múltiples historias
        pdfs_descargados = avicena.descargar_multiples_historias(cantidad=3)
        
        print(f"✅ Proceso completado. PDFs descargados:")
        for pdf in pdfs_descargados:
            print(f"  - {pdf}")

    except Exception as e:
        print(f"❌ Error inesperado en el flujo principal: {e}")
        traceback.print_exc()

    finally:
        if avicena:
            print("🚪 Cerrando el navegador...")
            avicena.cerrar()
