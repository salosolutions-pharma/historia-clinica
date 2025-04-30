
import os
import json
import openai
import pandas as pd
from pathlib import Path
import base64
import re
from PyPDF2 import PdfReader

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")  
MODEL_NAME = "o4-mini"

# Ruta a la carpeta con historias clínicas
HISTORIAS_DIR = Path(r"C:\Users\salos\Downloads\historia_clinica\descargas")

# Listas para acumular datos
pacientes = []
diagnosticos = []
procedimientos = []
signos_vitales = []
paraclinicos = []
medicamentos = []

def clean_json(texto: str) -> str:
    # 1) Quitar bloque de Markdown ```json ... ```
    texto = re.sub(r"^```(?:json)?\s*", "", texto)
    texto = re.sub(r"\s*```$", "", texto)
    # 2) Encontrar la primera '{' y la última '}', y extraer ese fragmento
    start = texto.find("{")
    end = texto.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No se encontró un JSON válido en la respuesta.")
    return texto[start:end+1].strip()

# Función para extraer y parsear información usando el modelo
def procesar_historia(file_path: Path) -> dict:
    # 1) Leer texto del PDF
    reader = PdfReader(str(file_path))
    full_text = []
    for page in reader.pages:
        full_text.append(page.extract_text() or "")
    documento = "\n\n".join(full_text).strip()

    # 1) Capturar todos los valores de PESO (kgs) y quedarnos con el último
    pesos = re.findall(
        r'PESO\s*([0-9]+(?:\.[0-9]+)?)\s*kgs',
        documento,
        flags=re.IGNORECASE
    )
    peso = float(pesos[-1]) if pesos else None
    print(peso)
    # 2) Capturar todos los valores de TALLA (cms) y quedarnos con el último
    tallas = re.findall(
        r'TALLA\s*([0-9]+(?:\.[0-9]+)?)(?=\s*cms)',
        documento,
        flags=re.IGNORECASE
    )
    talla = float(tallas[-1]) if tallas else None
    
    # 2) Construir prompt con el texto (posiblemente recortándolo si es muy largo)
    system_prompt = """
    Te paso a continuación el texto de una historia clínica. Quiero que me devuelvas **solo** un objeto JSON con el estandar  HL7 FHIR (sin ningún texto adicional) con estas 6 claves de nivel superior:
    1. "Paciente": un objeto con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "Nombre": cadena (solo nombres en mayuscula)
    - "Apellido": cadena (solo apellidos en mayuscula)
    - "FechaNacimiento": fecha ISO (YYYY-MM-DD)
    - "Edad": edad como número (por ejemplo, "64")
    - "Sexo": "Masculino" o "Femenino"
    - "Peso": {peso} <!-- aquí irá el valor numérico -->
    - "Talla": {talla} <!-- aquí irá el valor numérico -->

    2. "Diagnosticos": una lista de objetos, cada uno con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "code": código ICD-10 (por ejemplo "M79.7") o null
    - "display": texto descriptivo en minuscula (por ejemplo "Fibromialgia")
    - "onsetDateTime": FECHA ATENCIÓN: ISO (YYYY-MM-DD)

    3. "Procedimientos": una lista de objetos, cada uno con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "code": código SNOMED (por ejemplo "999100") o null
    - "display": descripción (por ejemplo "Sesión de acupuntura")
    - "performedDateTime": fecha y hora ISO (o null)

    4. "SignosVitales": una lista de objetos, cada uno con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "effectiveDateTime": fecha y hora ISO (o null)
    - "component": lista de objetos con:
        - "code": { "display": nombre de la medida (p.ej. "Presión sistólica") }
        - "valueQuantity": { "value": número, "unit": unidad }

    5. "Paraclinicos": una lista de objetos, cada uno con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "effectiveDateTime": fecha ISO (o null)
    - "code": { "display": nombre de la prueba (p.ej. "Colesterol total") }
    - "valueQuantity": { "value": número, "unit": unidad }

    6. "Medicamentos": una lista de objetos, cada uno con:
    - "Identificacion": cadena (ejemplo RC 11004310)
    - "medicationCodeableConcept": { "text": nombre del medicamento }
    - "effectivePeriod": { "start": fecha ISO de inicio }' 
    devuélvelo **solo** como JSON con claves "
        "Paciente, Diagnosticos, Procedimientos, SignosVitales, Paraclinicos, Medicamentos"""

    # 3) Llamada al modelo
    user_prompt = f"""
    --- INICIO HISTORIA ---
    {documento[:3000]}
    --- FIN HISTORIA ---
    """

    respuesta = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    texto = respuesta.choices[0].message.content
    texto_json = clean_json(texto)
    return json.loads(texto_json)


'''# Procesar todos los PDFs en la carpeta
for pdf_file in HISTORIAS_DIR.glob("*.pdf"):
    data = procesar_historia(pdf_file)
    print(data)'''


html_jsones = ""
for pdf_file in HISTORIAS_DIR.glob("*.pdf"):
    data = procesar_historia(pdf_file)
    json_formatted = json.dumps(data, indent=2, ensure_ascii=False)
    html_jsones += f"<pre>{json_formatted}</pre>\n"
    print(data)

# Generar HTML con todas las tablas
html = f"""
<html>
<head>
  <meta charset="utf-8">
  <title>Resumen Historias Clínicas</title>
  <style>
    body {{ font-family: Arial, sans-serif; }}
    h2 {{ color: #333; }}
    pre {{
      background-color: #f9f9f9;
      border: 1px solid #ccc;
      padding: 10px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
    }}
  </style>
</head>
<body>
  <h1>Historias Clínicas en estándar HL7-FHIR</h1>
  {html_jsones}
</body>
</html>
"""

output_path = Path(r"C:\Users\salos\Downloads\historia_clinica\descargas\output\html_historias_FHIR")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Archivo HTML generado en: {output_path.resolve()}")