import os
import fitz
import openai
import pandas as pd
from utils.extractor import extract_info_from_image
from dotenv import load_dotenv
import shutil
import sys

# Cargar variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    print("❌ Error: No se ha encontrado la clave API de OpenAI.")
    print("   Por favor, crea un archivo .env con tu clave API:")
    print("   OPENAI_API_KEY=sk-xxxxx...")
    sys.exit(1)

# Configuración
PDF_FOLDER = "pdfs"
OUTPUT_CSV = "resultados_vision.csv"
TEMP_FOLDER = "temp_images"

def pdf_to_images(pdf_path, temp_folder):
    """
    Convierte un PDF a imágenes PNG
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        temp_folder (str): Carpeta donde guardar las imágenes temporales
        
    Returns:
        list: Lista de rutas a las imágenes generadas
    """
    # Crear carpeta temporal si no existe
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)
        
    doc = fitz.open(pdf_path)
    images = []
    
    for page_number in range(len(doc)):
        pix = doc[page_number].get_pixmap(dpi=200)
        img_path = os.path.join(temp_folder, f"{os.path.basename(pdf_path)}_page{page_number+1}.png")
        pix.save(img_path)
        images.append(img_path)
        
    return images

def test_api_connection():
    """
    Prueba la conexión a la API de OpenAI y verifica que el modelo esté disponible
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        # Hacemos una llamada simple para verificar la conexión
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hola"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        print(f"❌ Error al conectar con la API de OpenAI: {e}")
        return False

def merge_patient_data(page_data_list):
    """
    Combina la información de múltiples páginas del mismo paciente
    
    Args:
        page_data_list (list): Lista de diccionarios con la información de cada página
        
    Returns:
        dict: Diccionario con la información combinada
    """
    if not page_data_list:
        return None
    
    # Empezamos con la primera página
    merged_data = page_data_list[0].copy()
    
    # Combinamos con el resto de páginas
    for page_data in page_data_list[1:]:
        for key, value in page_data.items():
            # Si el campo está vacío en merged_data pero tiene valor en page_data, lo actualizamos
            if (not merged_data.get(key) or merged_data[key] == "") and value:
                merged_data[key] = value
            # Si ambos tienen valor y son diferentes, concatenamos (excepto campos específicos)
            elif value and merged_data.get(key) and value != merged_data[key]:
                if key in ["Nombre", "Cédula", "Edad", "Hipertenso", "Diabético", "Tabaquismo"]:
                    # Para estos campos usamos el valor no vacío o el de la primera página
                    continue
                else:
                    # Para el resto de campos, concatenamos si hay información nueva
                    if value not in merged_data[key]:
                        merged_data[key] = f"{merged_data[key]}; {value}"
    
    return merged_data

def main():
    """Función principal del programa"""
    
    print("🔍 Iniciando extractor de historias clínicas con OpenAI GPT-4o")
    
    # Verificar conexión con API
    print("⚙️ Verificando conexión con OpenAI API...")
    if not test_api_connection():
        print("❌ No se pudo conectar con la API de OpenAI. Verifica tu clave API y conexión a internet.")
        return
    print("✅ Conexión con OpenAI API verificada correctamente")
    
    # Verificar que exista la carpeta de PDFs
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"✅ Carpeta '{PDF_FOLDER}' creada. Por favor, coloca tus PDFs ahí y ejecuta el script nuevamente.")
        return
    
    # Verificar si hay PDFs en la carpeta
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"❌ No se encontraron archivos PDF en la carpeta '{PDF_FOLDER}'.")
        return
    
    print(f"📄 Se encontraron {len(pdf_files)} archivos PDF para procesar")
    
    # Crear carpeta temporal para imágenes
    temp_folder = TEMP_FOLDER
    
    patients_data = []
    processed_count = 0
    error_count = 0
    
    try:
        for file in pdf_files:
            pdf_path = os.path.join(PDF_FOLDER, file)
            print(f"📝 Procesando {file}...")
            
            # Convertir PDF a imágenes
            images = pdf_to_images(pdf_path, temp_folder)
            
            # Procesar cada imagen
            page_data_list = []
            
            for img_path in images:
                print(f"  - Analizando imagen: {os.path.basename(img_path)}")
                
                info = extract_info_from_image(img_path)
                
                if info:
                    # Añadir información de origen
                    info["Origen_PDF"] = file
                    info["Página"] = os.path.basename(img_path).split("_page")[1].replace(".png", "")
                    page_data_list.append(info)
                    print(f"    ✅ Información extraída correctamente")
                else:
                    print(f"    ❌ No se pudo extraer información de esta imagen")
            
            # Si se extrajo información de al menos una página
            if page_data_list:
                # Combinar información de todas las páginas del mismo PDF
                merged_data = merge_patient_data(page_data_list)
                patients_data.append(merged_data)
                processed_count += 1
                print(f"  ✅ Historia clínica procesada correctamente")
            else:
                error_count += 1
                print(f"  ❌ No se pudo extraer información de este PDF")
        
        # Si se extrajo información, crear DataFrame y guardar CSV
        if patients_data:
            df = pd.DataFrame(patients_data)
            # Ordenar las columnas para que las más importantes aparezcan primero
            column_order = [
                "Nombre", "Cédula", "Edad", "Hipertenso", "Diabético", "Tabaquismo", 
                "PSA_total", "Tratamiento", "Examenes_laboratorio", "Antecedentes",
                "Origen_PDF", "Página"
            ]
            # Filtrar para incluir solo las columnas que existen
            existing_columns = [col for col in column_order if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in column_order]
            df = df[existing_columns + remaining_columns]
            
            df.to_csv(OUTPUT_CSV, index=False)
            print(f"\n✅ Datos extraídos guardados en: {OUTPUT_CSV}")
            print(f"📊 Resumen: {processed_count} PDFs procesados exitosamente, {error_count} con errores")
        else:
            print("\n❌ No se pudo extraer información de ninguna imagen")
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        
    finally:
        # Limpiar imágenes temporales
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            print(f"🧹 Imágenes temporales eliminadas")

if __name__ == "__main__":
    main()