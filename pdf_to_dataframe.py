
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
HISTORIAS_DIR = Path(r"D:\\Downloads\\historias_medifolios")

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
    Te paso a continuación el texto de una historia clínica. Quiero que me devuelvas **solo** un objeto JSON (sin ningún texto adicional) con estas 6 claves de nivel superior:
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
    return json.loads(texto_json), peso, talla


# Procesar todos los PDFs en la carpeta
for pdf_file in HISTORIAS_DIR.glob("*.pdf"):
    data, peso, talla = procesar_historia(pdf_file)
    
    # Paciente (incluye demográficos y antropometría)
    p = data.get("Paciente", {})
    pacientes.append({
        "ID":               p.get("Identificacion")       or p.get("DocumentoIdentidad"),
        "Nombre":           p.get("Nombre", "") + " " + p.get("Apellido", ""),
        "Sexo":             p.get("Sexo"),
        "FechaNacimiento":  p.get("FechaNacimiento"),
        "Edad":             p.get("Edad"),
        "Peso":             peso,
        "Talla":            talla
    })
    
    # Diagnósticos
    for d in data.get("Diagnosticos", []):
        if isinstance(d, dict):
            ID =       d.get("Identificacion")
            codigo    = d.get("code")
            diagnostico = d.get("display")
            fecha     = d.get("onsetDateTime")
        else:
            # d es una cadena: la tomamos como diagnóstico libre
            ID =         d.get("Identificacion")
            codigo      = None
            diagnostico = d
            fecha       = None

        diagnosticos.append({
            "ID": ID,
            "Código":    codigo,
            "Diagnóstico": diagnostico,
            "FechaAtencion":     fecha
        })
    
    # Procedimientos
    for proc in data.get("Procedimientos", []):
        if isinstance(proc, dict):
            ID            = proc.get("Identificacion")
            codigo        = proc.get("code")
            display       = proc.get("display")
            fechaHora     = proc.get("performedDateTime")
        else:
            ID            = None
            codigo        = None
            display       = proc
            fechaHora     = None

        procedimientos.append({
            "ID":            ID,
            "Código":        codigo,
            "Procedimiento": display,
            "FechaHora":     fechaHora
        })


    # Signos Vitales
    for sv in data.get("SignosVitales", []):
        if isinstance(sv, dict):
            ID          = sv.get("Identificacion")
            row = {
                "ID":            ID,
                "FechaHora":     sv.get("effectiveDateTime")
            }
            for comp in sv.get("component", []):
                medida = comp.get("code", {}).get("display",
                        comp.get("code", {}).get("text", ""))
                valor  = comp.get("valueQuantity", {}).get("value")
                row[medida] = valor
        else:
            row = {
                "ID":            None,
                "FechaHora":     None,
                "Observación":   sv
            }
        signos_vitales.append(row)


    
    # Paraclínicos
    for lab in data.get("Paraclinicos", []):
        if isinstance(lab, dict):
            ID        = lab.get("Identificacion")
            fecha     = lab.get("effectiveDateTime")
            prueba    = lab.get("code", {}).get("display")
            resultado = lab.get("valueQuantity", {}).get("value")
            unidad    = lab.get("valueQuantity", {}).get("unit")
        else:
            ID        = None
            fecha     = None
            prueba    = lab
            resultado = None
            unidad    = None

        paraclinicos.append({
            "ID":       ID,
            "Fecha":    fecha,
            "Prueba":   prueba,
            "Resultado":resultado,
            "Unidad":   unidad
        })


        
    # Medicamentos
    for med in data.get("Medicamentos", []):
        if isinstance(med, dict):
            ID      = med.get("Identificacion")
            med_cc  = med.get("medicationCodeableConcept", {})
            nombre  = med_cc.get("text") or med_cc.get("coding", [{}])[0].get("display")
            inicio  = med.get("effectivePeriod", {}).get("start")
        else:
            ID      = None
            nombre  = med
            inicio  = None

        medicamentos.append({
            "ID":             ID,
            "Medicamento":    nombre,
            "Inicio":         inicio
        })
    print(pacientes)



# Crear DataFrames
df_pacientes = pd.DataFrame(pacientes)
df_diagnosticos = pd.DataFrame(diagnosticos)
df_procedimientos = pd.DataFrame(procedimientos)
df_signos = pd.DataFrame(signos_vitales)
df_paraclinicos = pd.DataFrame(paraclinicos)
df_medicamentos = pd.DataFrame(medicamentos)


# Generar HTML con todas las tablas
html = f"""
<html>
<head>
  <meta charset="utf-8">
  <title>Resumen Historias Clínicas</title>
  <style>
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; }}
    th {{ background-color: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>Pacientes</h1> {df_pacientes.to_html(index=False, border=0)}
  <h1>Diagnósticos</h1> {df_diagnosticos.to_html(index=False, border=0)}
  <h1>Procedimientos</h1> {df_procedimientos.to_html(index=False, border=0)}
  <h1>Signos Vitales</h1> {df_signos.to_html(index=False, border=0)}
  <h1>Paraclínicos</h1> {df_paraclinicos.to_html(index=False, border=0)}
  <h1>Medicamentos</h1> {df_medicamentos.to_html(index=False, border=0)}
</body>
</html>
"""

output_path = Path(r"D:\\Downloads\\historias_medifolios\\output\\html_historias")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Archivo HTML generado en: {output_path.resolve()}")