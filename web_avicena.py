from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
import tempfile
import base64
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import re

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
    
    try:
        avicena = AvicenaLogin()
        
        # Iniciar sesión (con resolución automática del captcha)
        if avicena.login(USUARIO, PASSWORD):
            # Mantener la sesión abierta para navegación manual
            avicena.mantener_sesion_abierta()
        else:
            print("❌ Falló el inicio de sesión. Finalizando.")
            avicena.cerrar()

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        try:
            avicena.cerrar()
        except:
            pass