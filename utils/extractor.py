import openai
from PIL import Image
import base64
import json
import re

def extract_info_from_image(image_path):
    """
    Extrae información de una imagen de historia clínica usando OpenAI GPT-4o (versión actualizada).
    
    Args:
        image_path (str): Ruta a la imagen de la historia clínica
        
    Returns:
        dict: Información estructurada extraída de la imagen, o None si hay un error
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    prompt = """
Lee esta historia clínica escaneada. Extrae los siguientes campos en JSON:
{
  "Nombre": "",
  "Cédula": "",
  "Edad": "",
  "Hipertenso": "SI/NO",
  "Diabético": "SI/NO",
  "Tabaquismo": "SI/NO",
  "PSA_total": "",
  "Tratamiento": "",
  "Diagnóstico": "",
  "Imagenología": ""
}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # Usando el modelo actualizado que soporta visión
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}"
                    }}
                ]}
            ],
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        # Intentamos convertir el JSON a un diccionario de Python
        try:
            # Primero intentamos con json.loads (más seguro que eval)
            return json.loads(content)
        except json.JSONDecodeError:
            # Si no es JSON limpio, intentamos extraer solo la parte JSON
            json_match = re.search(r'({.*})', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    print("❌ No se pudo parsear el JSON devuelto por la API")
                    print(f"Contenido recibido: {content[:100]}...")
                    return None
            
            # Último recurso: intentar con eval (menos seguro)
            try:
                return eval(content)
            except:
                print("❌ No se pudo procesar la respuesta de la API")
                return None
            
    except Exception as e:
        print("❌ Error procesando la imagen:", e)
        return None