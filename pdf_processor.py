import os
import csv
import pandas as pd
from openai import OpenAI
from pathlib import Path
import json
import time
import re

class PDFProcessor:
    def __init__(self, api_key=None):
        # Inicializar cliente de OpenAI
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        
        # Crear directorios de salida si no existen
        os.makedirs("output", exist_ok=True)
        
        # Inicializar DataFrames para los CSV
        self.pacientes_df = pd.DataFrame(columns=["Paciente", "Fecha", "ID_Paciente", "Edad"])
        self.consultas_df = pd.DataFrame(columns=["ID_Paciente", "No_Consulta", "Tabaquismo", 
                                                 "Diabetes", "PSA", "Presion_Arterial", 
                                                 "Diagnostico", "Tratamiento"])
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrae el texto de un archivo PDF utilizando una librería de extracción"""
        try:
            # Importamos PyPDF2 aquí para no tener dependencia si no se usa
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n"
            
            return text
        except Exception as e:
            print(f"Error extrayendo texto del PDF {pdf_path}: {str(e)}")
            return ""
    
    def process_pdf_with_openai(self, pdf_path):
        """Procesa un PDF con la API de OpenAI o4-mini para extraer información estructurada"""
        # Extraer el texto del PDF
        pdf_text = self.extract_text_from_pdf(pdf_path)
        
        if not pdf_text.strip():
            print(f"⚠️ No se pudo extraer texto del PDF: {pdf_path}")
            return None
        
        print(f"🔍 Procesando PDF con OpenAI: {pdf_path}")
        
        # Definir el prompt para OpenAI
        prompt = f"""
        Extrae la siguiente información del texto de una historia clínica. La información debe estar en formato JSON con dos objetos: "paciente" y "consultas".
        
        Para "paciente" extrae:
        - Nombre completo del paciente
        - Fecha (de la consulta o documento)
        - ID del paciente (número de identificación)
        - Edad del paciente
        
        Para "consultas" extrae una lista donde cada consulta tiene:
        - ID del paciente (el mismo de arriba)
        - Número de consulta (si está disponible, otherwise "1")
        - Tabaquismo (responde solo "Si", "No" o "No reporta")
        - Diabetes (responde solo "Si", "No" o "No reporta")
        - PSA (valor numérico o "No reporta")
        - Presión Arterial (valor numérico o "No reporta")
        - Diagnóstico (texto del diagnóstico principal)
        - Tratamiento (texto del tratamiento indicado)
        
        El formato debe ser exactamente así:
        {{
            "paciente": {{
                "nombre": "valor",
                "fecha": "valor",
                "id": "valor",
                "edad": "valor"
            }},
            "consultas": [
                {{
                    "id_paciente": "valor",
                    "no_consulta": "valor",
                    "tabaquismo": "valor",
                    "diabetes": "valor",
                    "psa": "valor",
                    "presion_arterial": "valor",
                    "diagnostico": "valor",
                    "tratamiento": "valor"
                }}
            ]
        }}
        
        Aquí está el texto de la historia clínica:
        
        {pdf_text[:15000]}  # Limitamos a 15000 caracteres para no exceder límites de tokens
        """
        
        try:
            # Llamar a la API de OpenAI
            response = self.client.chat.completions.create(
                model="o4-mini",  # Usar o4-mini como especificaste
                messages=[
                    {"role": "system", "content": "Eres un asistente especializado en extraer información médica estructurada de historias clínicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Usar temperatura baja para respuestas consistentes
                response_format={"type": "json_object"}  # Forzar respuesta en JSON
            )
            
            # Extraer el contenido de la respuesta
            result = response.choices[0].message.content
            
            try:
                # Parsear el JSON
                data = json.loads(result)
                print("✅ Información extraída correctamente")
                return data
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON: {str(e)}")
                print(f"Respuesta recibida: {result[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error al llamar a la API de OpenAI: {str(e)}")
            return None
    
    def add_to_dataframes(self, data):
        """Añade la información extraída a los DataFrames de pacientes y consultas"""
        if not data:
            return
        
        try:
            # Añadir información del paciente
            paciente_info = data.get("paciente", {})
            if paciente_info:
                self.pacientes_df = pd.concat([
                    self.pacientes_df, 
                    pd.DataFrame([{
                        "Paciente": paciente_info.get("nombre", ""),
                        "Fecha": paciente_info.get("fecha", ""),
                        "ID_Paciente": paciente_info.get("id", ""),
                        "Edad": paciente_info.get("edad", "")
                    }])
                ], ignore_index=True)
            
            # Añadir información de consultas
            consultas_info = data.get("consultas", [])
            for consulta in consultas_info:
                self.consultas_df = pd.concat([
                    self.consultas_df,
                    pd.DataFrame([{
                        "ID_Paciente": consulta.get("id_paciente", ""),
                        "No_Consulta": consulta.get("no_consulta", ""),
                        "Tabaquismo": consulta.get("tabaquismo", "No reporta"),
                        "Diabetes": consulta.get("diabetes", "No reporta"),
                        "PSA": consulta.get("psa", "No reporta"),
                        "Presion_Arterial": consulta.get("presion_arterial", "No reporta"),
                        "Diagnostico": consulta.get("diagnostico", ""),
                        "Tratamiento": consulta.get("tratamiento", "")
                    }])
                ], ignore_index=True)
                
            print(f"✅ Datos añadidos a los DataFrames. Pacientes: {len(self.pacientes_df)}, Consultas: {len(self.consultas_df)}")
        
        except Exception as e:
            print(f"❌ Error al añadir datos a los DataFrames: {str(e)}")
    
    def process_directory(self, pdf_directory):
        """Procesa todos los PDFs en un directorio"""
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            print(f"❌ No se encontraron archivos PDF en {pdf_directory}")
            return
        
        print(f"🔍 Encontrados {len(pdf_files)} archivos PDF para procesar")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_directory, pdf_file)
            print(f"\n📄 Procesando: {pdf_file}")
            
            # Procesar el PDF con OpenAI
            data = self.process_pdf_with_openai(pdf_path)
            
            # Añadir datos a los DataFrames
            self.add_to_dataframes(data)
            
            # Pequeña pausa para evitar límites de rate en la API
            time.sleep(1)
    
    def save_to_csv(self, output_dir="output"):
        """Guarda los DataFrames a archivos CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Eliminar duplicados basándose en el ID del paciente
        self.pacientes_df.drop_duplicates(subset=["ID_Paciente"], keep="first", inplace=True)
        
        # Guardar CSVs
        pacientes_path = os.path.join(output_dir, "pacientes.csv")
        consultas_path = os.path.join(output_dir, "consultas.csv")
        
        self.pacientes_df.to_csv(pacientes_path, index=False)
        self.consultas_df.to_csv(consultas_path, index=False)
        
        print(f"\n✅ CSVs guardados:")
        print(f"📄 Pacientes: {pacientes_path} ({len(self.pacientes_df)} registros)")
        print(f"📄 Consultas: {consultas_path} ({len(self.consultas_df)} registros)")


# Ejemplo de uso del procesador de PDF
if __name__ == "__main__":
    # Ruta donde están los PDFs generados
    PDF_DIRECTORY = "D:\\Downloads\\historias_medifolios"
    
    # Clave API de OpenAI (reemplazar con tu clave o configurar como variable de entorno)
    OPENAI_API_KEY = "YOUR_API_KEY_HERE"
    
    # Inicializar y ejecutar el procesador
    processor = PDFProcessor(api_key=OPENAI_API_KEY)
    processor.process_directory(PDF_DIRECTORY)
    processor.save_to_csv()