import openai
from PIL import Image
import base64
import json
import re

def extract_info_from_image(image_path):
    """
    Extrae información específica de una imagen de historia clínica usando OpenAI GPT-4o.
    
    Args:
        image_path (str): Ruta a la imagen de la historia clínica
        
    Returns:
        dict: Información estructurada extraída de la imagen, o None si hay un error
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    prompt = """
Lee esta historia clínica escaneada y extrae SOLO los siguientes campos en formato JSON:
{
  "Nombre": "",
  "Cédula": "",
  "Edad": "",
  "Hipertenso": "SI/NO",
  "Diabético": "SI/NO",
  "Tabaquismo": "SI/NO",
  "PSA_total": "",
  "Tratamiento": "",
  "Examenes_laboratorio": "",
  "Antecedentes": ""
}

Instrucciones específicas:
1. Para PSA_total: Extrae solo el valor numérico o la descripción exacta (ej: "alterado", "< 0.1", "82.5 ng/mL")
2. Para Hipertenso, Diabético y Tabaquismo: Responde SOLO con "SI" o "NO"
3. Si no encuentras información para algún campo, déjalo vacío, no inventes información
4. Para Antecedentes: Solo incluye información relevante como enfermedades previas
5. Asegúrate de buscar en todo el documento estos datos, pueden estar en diferentes secciones
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
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