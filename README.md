# Extractor de Historias Clínicas Web

Este proyecto automatiza la extracción de datos desde el sistema web "Historias Clínicas Online" y estructura la información en dos tablas CSV siguiendo un modelo de base de datos predefinido.

## Características

- Inicio de sesión automático en el sistema web
- Navegación por la interfaz de pacientes
- Extracción de historias clínicas desde el visor de PDF integrado
- Procesamiento inteligente del texto con OpenAI GPT-4o
- Generación de tablas estructuradas en formato CSV

## Información extraída

La información se estructura en dos tablas:

### Tabla Pacientes
- Paciente: Nombre completo
- Fecha: Fecha de nacimiento
- ID_Paciente: Identificador único 
- Edad: Edad del paciente

### Tabla Consultas
- ID_Paciente: Identificador que vincula con la tabla pacientes
- No_Consulta: Número o fecha de consulta
- Tabaquismo: SI/NO
- Diabetes: SI/NO
- PSA: Valor numérico (si existe)
- Presion_Arterial: Valor de la presión arterial
- Diagnostico: Texto del diagnóstico
- Tratamiento: Tratamiento indicado

## Requisitos

- Python 3.8+
- OpenAI API con acceso a GPT-4o
- Chrome o Chromium
- Conexión a internet estable
- Credenciales válidas para el sistema web

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/salosolutions-pharma/historia-clinica.git
cd historia-clinica