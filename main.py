import os
from dotenv import load_dotenv
import openai
from web_extractor import HistoriasClinicasExtractor

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def main():
    print("🚀 Iniciando extracción de datos de historias clínicas desde la web...")
    
    # Verificar que exista la API key de OpenAI
    if not openai.api_key:
        print("❌ No se encontró la clave API de OpenAI. Crea un archivo .env con OPENAI_API_KEY=sk-xxx")
        return
    
    # Configurar credenciales
    EMAIL = "maria.londono@solutions2pharma.com"
    PASSWORD = "Clinicasolutions"
    
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
            extractor.procesar_paciente(paciente['index'])
            import time
            time.sleep(2)  # Pequeña pausa entre pacientes
        
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