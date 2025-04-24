import os
from dotenv import load_dotenv
from web_extractor import HistoriasClinicasExtractor

# Cargar variables de entorno
load_dotenv()

def main():
    print("🚀 Iniciando extracción de datos de historias clínicas desde la web...")
    
    # Verificar que exista la API key de OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No se encontró la clave API de OpenAI. Crea un archivo .env con OPENAI_API_KEY=sk-xxx")
        return
    else:
        print(f"✅ API key de OpenAI encontrada (longitud: {len(api_key)})")
    
    # Configurar credenciales
    EMAIL = "maria.londono@solutions2pharma.com"
    PASSWORD = "Clinicasolutions"
    
    # Guardar las credenciales para posibles reinicios
    credenciales = (EMAIL, PASSWORD)
    
    # Inicializar extractor
    extractor = HistoriasClinicasExtractor()
    
    try:
        # Iniciar sesión
        if not extractor.login(EMAIL, PASSWORD):
            print("❌ No se pudo iniciar sesión. Finalizando.")
            extractor.cerrar()
            return
        
        # Navegar a la sección de pacientes
        if not extractor.ir_a_pacientes():
            print("❌ No se pudo navegar a la sección de pacientes. Finalizando.")
            extractor.cerrar()
            return
        
        # Obtener lista de pacientes
        pacientes = extractor.obtener_lista_pacientes()
        if not pacientes:
            print("❌ No se encontraron pacientes. Finalizando.")
            extractor.cerrar()
            return
        
        # Procesar cada paciente
        for i, paciente in enumerate(pacientes):
            print(f"\n--- Procesando paciente {i+1}/{len(pacientes)}: {paciente['nombre']} ---")
            # Pasar las credenciales como parámetro
            resultado = extractor.procesar_paciente(paciente, credenciales)
            
            # Si hay un error en el procesamiento del paciente, intentar recuperar la sesión
            if not resultado:
                print("⚠️ Hubo un problema con este paciente, asegurando la sesión antes de continuar...")
                try:
                    # Verificar si la sesión sigue activa
                    extractor.driver.current_url
                    print("✅ La sesión parece estar activa")
                except:
                    print("🔄 Reiniciando sesión...")
                    # Reiniciar el navegador si es necesario
                    extractor.cerrar()
                    extractor = HistoriasClinicasExtractor()
                    if not extractor.login(EMAIL, PASSWORD):
                        print("❌ No se pudo reiniciar la sesión. Finalizando.")
                        extractor.cerrar()
                        return
                    if not extractor.ir_a_pacientes():
                        print("❌ No se pudo navegar a pacientes después de reiniciar. Finalizando.")
                        extractor.cerrar()
                        return
            
            # Pausa entre pacientes
            import time
            time.sleep(3)  # Incrementar pausa entre pacientes
        
        print("\n✅ Extracción completada con éxito")
        print(f"📁 Archivos generados en la carpeta: datos_extraidos/")
        print(f"- Pacientes: datos_extraidos/pacientes.csv")
        print(f"- Consultas: datos_extraidos/consultas.csv")
        
    except Exception as e:
        print(f"❌ Error en el proceso de extracción: {str(e)}")
    
    finally:
        # Cerrar el navegador
        extractor.cerrar()

if __name__ == "__main__":
    main()