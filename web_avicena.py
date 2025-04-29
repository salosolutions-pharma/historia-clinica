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
import time
import os
import tempfile
import base64
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import re
import traceback


# Cargar variables de entorno desde el archivo .env
load_dotenv()

class AvicenaLogin:
    def __init__(self):
        """Inicializa el navegador para login en Avicena y cliente OpenAI"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        # Inicializar cliente de OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No se encontró la API key de OpenAI en las variables de entorno")
        self.openai_client = OpenAI(api_key=api_key)

    def presionar_consultar_historia_clinica(self):
        try:
            # Esperar a que el formulario esté visible para hacer hover
            form_menu = self.wait.until(
                EC.visibility_of_element_located((By.ID, "formMenu"))
            )
            print('Presionar consulta se esta ejecutando')
            # Crear una acción de hover para colocar el mouse sobre el formulario
            actions = ActionChains(self.driver)
            actions.move_to_element(form_menu).perform()  # Hover sobre el formulario

            print("✅ Menú desplegado tras hover")

            # Esperar a que el enlace "Consultar Historia Clínica Avicena" sea clickeable
            consultar_historia_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formMenu:ctlItemConsultarHistoria:anchor"))
            )
            consultar_historia_btn.click()  # Hacer clic en el enlace
            print("✅ Historia Clínica Avicena abierta")

            # Opcionalmente, puedes esperar un poco más para asegurar que se haya cargado la página o contenido
            time.sleep(5)

        except Exception as e:
            print(f"❌ Error al abrir Historia Clínica Avicena: {str(e)}")
    
    def seleccionar_tipo_identificacion(self):
        """Selecciona la opción 'Cédula de ciudadanía' en el dropdown de tipo de identificación."""
        try:
            # Esperar a que el dropdown sea clickeable
            select_element = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlTipoIdentificacion"))
            )
            
            # Crear un objeto Select para interactuar con el dropdown
            select = Select(select_element)
            
            # Seleccionar la opción por valor
            select.select_by_value("433")  # 'Cédula de ciudadanía'
            
            print("✅ 'Cédula de ciudadanía' seleccionada correctamente.")
        
        except Exception as e:
            print(f"❌ Error al seleccionar el tipo de identificación: {str(e)}")
            traceback.print_exc()

    def ingresar_numero_documento(self, numero_documento="41389309"):
        """Ingresa el número de documento en el campo correspondiente."""
        try:
            # Esperar a que el campo de texto esté visible y sea interactuable
            campo_documento = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlNumeroDocumento"))
            )
            
            # Escribir el número de documento en el campo
            campo_documento.send_keys(numero_documento)
            
            print(f"✅ Número de documento '{numero_documento}' ingresado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al ingresar el número de documento: {str(e)}")
            traceback.print_exc()

    def clic_buscar(self):
        """Hace clic en el botón 'Buscar'."""
        try:
            # Esperar a que el botón sea clickeable
            boton_buscar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:buscar1"))
            )
            
            # Hacer clic en el botón
            boton_buscar.click()
            
            print("✅ Botón 'Buscar' clickeado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al hacer clic en el botón 'Buscar': {str(e)}")
            traceback.print_exc()
       
    def clic_consultar_historia_sophia(self):
        """Hace clic en el botón de consultar historia clínica."""
        try:
            # Esperar a que el botón sea clickeable
            boton_consultar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formPrerrequisitos:ctlFolios:0:sophiaBtn"))
            )
            
            # Hacer clic en el botón
            boton_consultar.click()
            
            print("✅ Botón 'Consultar Historia Clínica' clickeado correctamente.")
        
        except Exception as e:
            print(f"❌ Error al hacer clic en el botón 'Consultar Historia Clínica': {str(e)}")
            traceback.print_exc()

    def cambiar_a_nueva_ventana(self):
        """Cambia al contexto de la nueva ventana que se abre."""
        try:
            # Esperar un tiempo para asegurarse de que la nueva ventana se haya abierto
            time.sleep(2)

            # Obtener los identificadores de todas las ventanas abiertas
            ventanas = self.driver.window_handles
            print(len(ventanas))
            # Cambiar al contexto de la nueva ventana (suponiendo que es la última ventana abierta)
            self.driver.switch_to.window(ventanas[1])
            print("✅ Cambiado al contexto de la nueva ventana.")
        
        except Exception as e:
            print(f"❌ Error al cambiar a la nueva ventana: {str(e)}")
            traceback.print_exc()
        
 

    def descargar_historia(self):
        """Descargar el PDF desde el visor dentro del modal."""
        try:
            print("Esperando a que la tabla esté completamente cargada...")
            tabla = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:ctlFolios"))
            )

            # Buscar el botón dentro de la tabla, específicamente con el ID "form:ctlFolios:0:verhcSophia"
            boton_id = "form:ctlFolios:0:verhcSophia"
            boton = self.wait.until(
                EC.presence_of_element_located((By.ID, boton_id))
            )
            print(f"✅ Botón con ID {boton_id} encontrado.")

            # Asegurarse de que el botón es visible en la pantalla (scroll)
            self.driver.execute_script("arguments[0].scrollIntoView();", boton)
            time.sleep(1)  # Pausa para asegurar que el scroll se haya completado
            print(f"✅ Botón con ID {boton_id} ahora visible.")

            # Hacer clic en el botón para abrir el PDF
            boton.click()
            print("✅ Modal del visor PDF cargado correctamente.")
            
        except Exception as e:
            print(f"❌ Error durante la descarga del archivo o al regresar: {str(e)}")
            traceback.print_exc()




    def login(self, usuario, password):
        """Inicia sesión en el sistema Avicena con resolución automática del captcha"""
        print(f"🔑 Iniciando sesión en Avicena con usuario: {usuario}")
        self.driver.get("https://avicena.colsanitas.com/His/login.seam")

        try:
            # Esperar a que cargue el formulario de login
            usuario_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "ctlFormLogin:idUserNameLogin"))
            )
            password_input = self.driver.find_element(By.ID, "ctlFormLogin:idPwdLogin")

            # Ingresar credenciales
            usuario_input.send_keys(usuario)
            password_input.send_keys(password)

            # Resolver el captcha con OpenAI
            print("🤖 Resolviendo captcha con OpenAI...")
            captcha_value = self._resolver_captcha_con_openai()

            if not captcha_value:
                print("❌ No se pudo resolver el captcha automáticamente")
                # Caer al método manual como respaldo
                captcha_value = self._resolver_captcha_manual()

            if not captcha_value:
                print("❌ No se ingresó el captcha")
                return False

            print(f"✅ Captcha resuelto: {captcha_value}")

            # Ingresar el captcha
            captcha_input = self.driver.find_element(By.ID, "ctlFormLogin:idCodSegCaptcha")
            captcha_input.send_keys(captcha_value)

            # Hacer clic en el botón de inicio de sesión
            login_btn = self.driver.find_element(By.ID, "ctlFormLogin:botonValidar")
            login_btn.click()

            # Verificar si el login fue exitoso
            try:
                # Esperamos a que desaparezca el formulario de login
                self.wait.until_not(
                    EC.presence_of_element_located((By.ID, "ctlFormLogin:botonValidar"))
                )
                print("✅ Inicio de sesión exitoso")
                return True
            except TimeoutException:
                # Verificar si hay algún mensaje de error
                try:
                    error_msg = self.driver.find_element(By.CLASS_NAME, "mensajeErrorLogin").text
                    print(f"❌ Error en el inicio de sesión: {error_msg}")

                    # Si el error es sobre el captcha, reintentar
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
        """Utiliza OpenAI para resolver el captcha"""
        try:
            # Mostrar la imagen del captcha
            captcha_img = self.driver.find_element(By.XPATH, "//img[contains(@id, 'ctlFormLogin:j_id')]")

            # Guardar temporalmente la imagen del captcha
            captcha_path = os.path.join(tempfile.gettempdir(), "captcha.png")
            captcha_img.screenshot(captcha_path)

            print(f"🔍 Captcha guardado en: {captcha_path}")

            # Mejorar la imagen para el OCR
            self._mejorar_imagen_captcha(captcha_path)

            # Convertir la imagen a base64
            with open(captcha_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Enviar la imagen a OpenAI para reconocimiento
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # o cualquier otro modelo con capacidades de visión
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

            # Extraer el texto reconocido
            captcha_text = response.choices[0].message.content.strip()

            # Limpiar el resultado (mantener solo dígitos)
            captcha_text = re.sub(r'[^0-9]', '', captcha_text)

            return captcha_text

        except Exception as e:
            print(f"❌ Error al resolver el captcha con OpenAI: {str(e)}")
            return None

    def _mejorar_imagen_captcha(self, image_path):
        """Mejora la imagen del captcha para facilitar el OCR"""
        try:
            # Abrir la imagen
            img = Image.open(image_path)

            # Convertir a escala de grises
            img = img.convert('L')

            # Aumentar el contraste
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)

            # Guardar la imagen mejorada
            img.save(image_path)

        except Exception as e:
            print(f"⚠️ Error al mejorar imagen: {str(e)}")

    def _resolver_captcha_manual(self):
        """Solicita al usuario que ingrese manualmente el captcha (método de respaldo)"""
        # Mostrar la imagen del captcha
        captcha_img = self.driver.find_element(By.XPATH, "//img[contains(@id, 'ctlFormLogin:j_id')]")

        # Guardar temporalmente la imagen del captcha
        captcha_path = os.path.join(tempfile.gettempdir(), "captcha.png")
        captcha_img.screenshot(captcha_path)

        print(f"🔍 Captcha guardado en: {captcha_path}")
        print("⚠️ Resolución automática falló. Por favor, abre esta imagen y revisa el código del captcha")

        # Solicitar al usuario que ingrese el captcha
        captcha_value = input("📝 Ingresa el código del captcha que ves en la imagen: ")

        return captcha_value

    
    def seleccionar_sucursal(self, valor_sucursal="29374"):
        """Selecciona la sucursal en el formulario tras el login."""
        print(f"🔄 Seleccionando sucursal con valor: {valor_sucursal}")
        try:
            # Espera a que aparezca el <select> y esté listo para usar
            select_el = self.wait.until(
                EC.element_to_be_clickable((By.ID, "formIngreso:ctlSucursales"))
            )
            select = Select(select_el)

            # Selecciona por value. Si prefieres por texto, usa select.select_by_visible_text("...")
            print(f"   Encontrado elemento select, intentando seleccionar valor '{valor_sucursal}'...")
            select.select_by_value(valor_sucursal)
            print(f"✅ Valor '{valor_sucursal}' seleccionado en el dropdown.")

        except TimeoutException:
             print(f"❌ TimeoutException: No se pudo encontrar o hacer clic en el elemento select 'formIngreso:ctlSucursales' después de esperar.")
             raise # Re-lanzar la excepción para que el flujo principal la maneje
        except Exception as e:
            print(f"❌ Error inesperado al seleccionar la sucursal: {str(e)}")
            import traceback
            traceback.print_exc()
            raise # Re-lanzar la excepción


    def presionar_ingresar(self, retries=3, delay=0.5):
        """Hace click en el botón Ingresar tras seleccionar sucursal, con reintentos para stale elements."""
        print("🔄 Ejecutando la función presionar_ingresar...")

        for attempt in range(retries):
            try:
                # 1. Esperar a que el botón sea clickeable en CADA intento
                #    Esto asegura que si la página se recarga o cambia, esperamos la nueva versión.
                print(f"   (Intento {attempt + 1}/{retries}) Esperando que el botón 'Ingresar' sea clickeable...")
                ingresar_btn = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "formIngreso:btnIngresar"))
                )
                print(f"✅ (Intento {attempt + 1}/{retries}) El botón 'Ingresar' está clickeable.")

                # 2. Hacer clic
                print(f"   (Intento {attempt + 1}/{retries}) Haciendo clic...")
                ingresar_btn.click()

                print("✅ Clic en 'Ingresar' ejecutado exitosamente.")
                # Si el clic fue exitoso, salimos de la función (y del bucle)
                return True

            except StaleElementReferenceException:
                print(f"⚠️ (Intento {attempt + 1}/{retries}) StaleElementReferenceException encontrada.")
                if attempt < retries - 1:
                    print(f"   Reintentando en {delay} segundos...")
                    time.sleep(delay)
                else:
                    print(f"❌ StaleElementReferenceException después de {retries} intentos. Fallando.")
                    # Opcionalmente, podrías intentar un clic con JavaScript como último recurso aquí
                    # self.intentar_clic_javascript("formIngreso:btnIngresar")
                    return False # Indicar fallo

            except TimeoutException:
                 print(f"❌ (Intento {attempt + 1}/{retries}) TimeoutException: El botón no se volvió clickeable.")
                 # Generalmente, si no se vuelve clickeable, no tiene sentido reintentar lo mismo.
                 return False # Indicar fallo

            except ElementClickInterceptedException:
                 print(f"⚠️ (Intento {attempt + 1}/{retries}) ElementClickInterceptedException: Otro elemento está bloqueando el clic.")
                 # Esto puede ser un overlay temporal. Reintentar podría ayudar.
                 if attempt < retries - 1:
                      print(f"   Reintentando en {delay} segundos...")
                      time.sleep(delay)
                 else:
                      print(f"❌ ElementClickInterceptedException después de {retries} intentos. Fallando.")
                      # Opcionalmente, podrías intentar un clic con JavaScript
                      # self.intentar_clic_javascript("formIngreso:btnIngresar")
                      return False # Indicar fallo

            except Exception as e:
                print(f"❌ Error inesperado al hacer clic en el botón 'Ingresar' (Intento {attempt + 1}): {str(e)}")
                import traceback
                traceback.print_exc()
                return False # Indicar fallo ante errores no manejados específicamente

        # Si el bucle termina sin éxito
        print(f"❌ No se pudo hacer clic en el botón 'Ingresar' después de {retries} intentos.")
        return False

    
    def mantener_sesion_abierta(self):
        """Mantiene la sesión abierta para que puedas interactuar manualmente"""
        print("\n✅ Sesión iniciada correctamente.")
        print("⌛ La ventana del navegador permanecerá abierta para que puedas navegar manualmente.")
        print("⚠️ El script seguirá ejecutándose hasta que cierres manualmente la ventana o presiones Ctrl+C en la consola.")

        try:
            # Esperar indefinidamente hasta que el usuario cierre la ventana o interrumpa el script
            while self.driver.window_handles:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⚠️ Proceso interrumpido por el usuario")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        finally:
            self.cerrar()

    def cerrar(self):
        """Cierra el navegador"""
        try:
            self.driver.quit()
            print("✅ Navegador cerrado correctamente")
        except Exception as e:
            print(f"⚠️ Error al cerrar el navegador: {str(e)}")


# -----------------------------------------------------
# MAIN PARA EJECUCIÓN
# -----------------------------------------------------
if __name__ == "__main__":
    print("🚀 Iniciando proceso de login en Avicena Colsanitas...")

    # Obtener credenciales desde variables de entorno
    USUARIO = os.environ.get("AVICENA_USUARIO")
    PASSWORD = os.environ.get("AVICENA_PASSWORD")

    # Verificar que existan las credenciales
    if not USUARIO or not PASSWORD:
        print("❌ Error: No se encontraron las credenciales en el archivo .env")
        print("Por favor, crea un archivo .env con las siguientes variables:")
        print("AVICENA_USUARIO=tu_usuario")
        print("AVICENA_PASSWORD=tu_contraseña")
        print("OPENAI_API_KEY=tu_api_key_de_openai")
        exit(1)

    # Verificar que exista la API key de OpenAI
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: No se encontró la API key de OpenAI en el archivo .env")
        print("Añade OPENAI_API_KEY=tu_api_key_de_openai al archivo .env")
        exit(1)

    avicena = None # Inicializar fuera del try para poder usarlo en finally
    try:
        avicena = AvicenaLogin()

        # Iniciar sesión (con resolución automática del captcha)
        if avicena.login(USUARIO, PASSWORD):
            avicena.seleccionar_sucursal("29374") # O el valor que necesites

            avicena.presionar_ingresar() 

            avicena.presionar_consultar_historia_clinica()

            avicena.seleccionar_tipo_identificacion()

            avicena.ingresar_numero_documento()

            avicena.clic_buscar()

            avicena.clic_consultar_historia_sophia()
            avicena.cambiar_a_nueva_ventana()

            avicena.descargar_historia()

            # Ahora sí, si quieres mantener la ventana abierta después de ingresar:
            avicena.mantener_sesion_abierta()

        else:
            print("❌ Falló el inicio de sesión. Finalizando.")
            # No necesitas llamar a cerrar aquí si lo haces en finally

    except Exception as e:
        print(f"❌ Error inesperado en el flujo principal: {str(e)}")
        import traceback
        traceback.print_exc() # Imprime la traza completa del error

    finally:
        # Asegurarse de cerrar el navegador incluso si hay errores
        # (excepto si se interrumpe manualmente desde mantener_sesion_abierta)
        if avicena is not None and 'mantener_sesion_abierta' not in traceback.format_exc():
             print("🚪 Cerrando el navegador desde el bloque finally...")
             avicena.cerrar()
        elif avicena is None:
             print("⚠️ No se pudo inicializar el objeto AvicenaLogin.")