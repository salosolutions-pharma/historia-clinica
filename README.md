# Extractor de Historias Clínicas con OpenAI GPT-4o

Este proyecto permite procesar archivos PDF escaneados de historias clínicas para extraer información estructurada utilizando la API de OpenAI GPT-4o.

## Información extraída

- Nombre, edad, cédula
- Diagnóstico
- PSA total
- Tratamientos
- Antecedentes relevantes (hipertensión, diabetes, tabaquismo)
- Datos de imagenología

## Requisitos

- Python 3.8+
- OpenAI API con acceso a GPT-4o
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/salosolutions-pharma/historia-clinica.git
cd historia-clinica
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Crea un archivo `.env` con tu clave de OpenAI:
```
OPENAI_API_KEY=sk-xxxxx...
```

## Uso

1. Coloca tus PDFs escaneados en la carpeta `pdfs/`

2. Ejecuta el script principal:
```bash
python main.py
```

3. Los resultados se guardarán en `resultados_vision.csv`

## Estructura del proyecto

```
historia-clinica/
│
├── pdfs/                  # Carpeta para almacenar los PDFs 
├── utils/
│   └── extractor.py       # Código para extraer información
├── main.py                # Script principal
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Documentación
```

## Notas sobre la versión

Este proyecto utiliza el modelo `gpt-4o` de OpenAI

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE).