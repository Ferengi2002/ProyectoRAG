# Chatbot Legal RAG Corporativo

Este es un asistente virtual con arquitectura **RAG Híbrida** (Retrieval-Augmented Generation) especializado en normativa corporativa/bancaria.
El backend está construido con **FastAPI** y el Frontend en **Vanilla HTML/JS/CSS** (Responsive). Utiliza **Gemini 2.5 Flash** como modelo de lenguaje y realiza recuperación de información a través de la integración de **FAISS** (Búsqueda Vectorial Semántica con HuggingFace) y **BM25** (Búsqueda por Palabras Clave).

---

## Requisitos Previos

- Python 3.9 o superior.
- Una clave de API de Gemini válida (desde [Google AI Studio](https://aistudio.google.com/app/apikey)).

---

## Instructivo de Instalación y Ejecución

Sigue cuidadosamente estos pasos para levantar el proyecto localmente, mitigando los errores comunes de Windows asociados a la creación de entornos virtuales.

### 1. Clonar o descargar el repositorio
Inicia la terminal dentro de esta carpeta (`ProyectoRAG`).

### 2. Configurar la API de Gemini
Crea un archivo oculto llamado `.env` en la raíz de este directorio y agrega tu API Key sin espacios ni comillas adicionales:
```env
GEMINI_API_KEY=AIzaSyTuClavePersonalGeneradaAqui
```

### 3. Crear el Entorno Virtual Funcional (Importante en Windows)
Debido a conflictos con el sistema de seguridad en Windows (Antivirus o permisos que bloquean la copia de `venvlauncher.exe`), **asegúrate de crear el entorno manualmente SIN pip, y luego instalarlo manualmente**:

Abre `PowerShell` o tu consola preferida y ejecuta lo siguiente, uno tras otro:

```powershell
# Crear una capeta virtual excluyendo a pip momentáneamente para prevenir errores "Unable to copy"
py -m venv app_env --without-pip

# Descargar el instalador de pip manualmente
Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py

# Ejecutar el instalador usando tu nuevo entorno virtual
.\app_env\Scripts\python.exe get-pip.py

# Eliminar el instalador porque ya no se necesita
Remove-Item get-pip.py
```

### 4. Activar el Entorno
Siempre debes activar el entorno de trabajo antes de levantar el servidor. 
En **PowerShell (Windows)**:
```powershell
.\app_env\Scripts\activate
```
*(Deberás ver un prefijo `(app_env)` al inicio de la línea de tu consola si fue exitoso).*
> **Nota de Seguridad Windows**: Si este comando falla e indica "ejecución de scripts deshabilitada", corre esto antes de activarlo:
> `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`

### 5. Instalar Dependencias
Una vez activado el entorno, instala todas las librerías necesarias con:
```bash
pip install -r requirements.txt
```

### 6. Ejecutar el Servidor
Finalmente, levanta el proyecto ejecutando el servidor de FastAPI con *Uvicorn*:
```bash
uvicorn main:app --reload
```

Abre tu navegador web e ingresa a [http://localhost:8000](http://localhost:8000) o [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Organización del Proyecto

```text
ProyectoRAG/
│
├── indice_faiss/             # Base de datos vectorial persistente (Requerida en GitHub)
│   ├── index.faiss
│   ├── index.pkl
│   └── chunks_memoria.pkl
│
├── static/                   # Frontend Nativo Corporativo (Estilo Banco)
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── main.py                   # Servidor FastAPI y Lógica Híbrida GAI/RAG
├── requirements.txt          # Requisitos y dependencias de Python
├── README.md                 # Archivo de instrucciones
└── .env                      # [IGNORADO EN GIT] Variables locales: GEMINI API KEY
```
