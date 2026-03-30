import os
import pickle
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from dotenv import load_dotenv

# Cargar variables de entorno (para GEMINI_API_KEY)
load_dotenv()

# Variables globales para almacenar los componentes inicializados
faiss_db = None
bm25_retriever = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica de Inicialización al arranque del servidor
    global faiss_db, bm25_retriever
    print("Iniciando servidor y cargando modelos para RAG Híbrido...")

    # Configurar API de Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        print("Gemini API Key configurada.")
    else:
        print("ADVERTENCIA: No se encontró la variable de entorno GEMINI_API_KEY.")

    try:
        # 1. Cargar el modelo de embeddings
        print("Inicializando modelo de embeddings (all-MiniLM-L6-v2)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # 2. Cargar FAISS vector store
        directorio_indice = "./indice_faiss"
        print(f"Cargando índice FAISS desde {directorio_indice}...")
        faiss_db = FAISS.load_local(
            folder_path=directorio_indice,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )

        # 3. Cargar chunks para BM25 usando pickle
        ruta_chunks = os.path.join(directorio_indice, "chunks_memoria.pkl")
        print(f"Cargando chunks_memoria.pkl desde {ruta_chunks}...")
        with open(ruta_chunks, "rb") as f:
            chunks_memoria = pickle.load(f)

        # 4. Inicializar BM25Retriever
        print("Inicializando BM25 con k=3...")
        bm25_retriever = BM25Retriever.from_documents(chunks_memoria)
        bm25_retriever.k = 3 # top 3 documentos

        print(" RAG inicializado exitosamente.")
    except Exception as e:
        print(f" Error durante la inicialización de RAG: {e}")
        
    yield # Aquí FastAPI arranca y atiende peticiones
    
    # Limpieza al detener el servidor
    print("Servidor deteniéndose...")

# Inicializar aplicación FastAPI
app = FastAPI(title="Chatbot Legal RAG", lifespan=lifespan)

# Modelo Pydantic para el payload JSON entrante
class ChatRequest(BaseModel):
    pregunta: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.pregunta:
        return JSONResponse(status_code=400, content={"error": "La pregunta es requerida."})
        
    pregunta = request.pregunta
    
    if faiss_db is None or bm25_retriever is None:
        return JSONResponse(status_code=500, content={"error": "Los modelos de recuperación no están inicializados."})

    try:
        # 1. RECUPERACIÓN HÍBRIDA
        # Obtener top 3 de FAISS (Similitud Semántica)
        faiss_docs = faiss_db.similarity_search(pregunta, k=3)
        # Obtener top 3 de BM25 (Búsqueda por Palabras Clave)
        bm25_docs = bm25_retriever.invoke(pregunta)
        
        # 2. UNIÓN Y ELIMINACIÓN DE DUPLICADOS
        todos_los_docs = faiss_docs + bm25_docs
        documentos_unicos = []
        contenidos_vistos = set()
        
        for doc in todos_los_docs:
            # Elimina duplicados en base al contenido exacto del fragmento
            if doc.page_content not in contenidos_vistos:
                contenidos_vistos.add(doc.page_content)
                documentos_unicos.append(doc)
                
        # 3. CONSTRUIR CONTEXTO LEGAL Y EXTRAER FUENTES
        contextos_texto = []
        fuentes_lista = []
        fuentes_vistas = set()
        
        for doc in documentos_unicos:
            # Extraer metadatos origen
            source_raw = doc.metadata.get("source", "Documento Desconocido")
            nombre_archivo = os.path.basename(source_raw) # Solo el nombre del archivo
            pagina = doc.metadata.get("page", "?")
            
            # Formatear la fuente para listar al usuario
            fuente_label = f"{nombre_archivo} - Pág: {pagina}"
            if fuente_label not in fuentes_vistas:
                fuentes_vistas.add(fuente_label)
                fuentes_lista.append(fuente_label)
                
            # Formatear el contexto para el LLM
            contexto_fragmento = f"--- Documento: {nombre_archivo}, Página: {pagina} ---\n{doc.page_content}\n"
            contextos_texto.append(contexto_fragmento)
            
        contexto_legal_final = "\n".join(contextos_texto)
        
        # 4. CONSTRUIR PROMPT RESTRINGIDO ESTRICTO
        prompt = f'''Actúa como un Auditor Legal Banco experto en interpretaciones de normativas. Se te proporciona un marco "CONTEXTO LEGAL RECUPERADO" compuesto por fragmentos reales de normativas de la entidad.

INSTRUCCIONES ESTRICTAS:
1. Responde a la pregunta del usuario basándote EXCLUSIVAMENTE en el contexto proporcionado.
2. BAJO NINGUNA CIRCUNSTANCIA inventes información, normativas, métricas o datos que no figuren explícitamente en el contexto.
3. Debes citar obligatoriamente el documento, y si se indica en el texto, el número de artículo, sección o capítulo en tu respuesta para justificarla.
4. Si el contexto no contiene la información para responder total o parcialmente a la pregunta, debes decir textualmente: "No he encontrado información suficiente en la base normativa documental para responder a esta pregunta." No intentes suponer ni predecir.
5. Redacta de forma profesional, unificada, clara y corporativa.

CONTEXTO LEGAL RECUPERADO:
{contexto_legal_final}

PREGUNTA DEL USUARIO:
{pregunta}

RESPUESTA DEL AUDITOR LEGAL:
'''
        
        # 5. INVOCAR AL MODELO GEMINI CON TEMPERATURA 0.0 (Máximo determinismo)
        modelo_gemini = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            generation_config=genai.GenerationConfig(temperature=0.0)
        )
        
        respuesta_ia = modelo_gemini.generate_content(prompt)
        
        # 6. ENVIAR RESPUESTA AL FRONTEND
        return {
            "respuesta": respuesta_ia.text,
            "fuentes": fuentes_lista
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Error interno en la generación RAG: {str(e)}"})

# Montar los estáticos para el Frontend nativo después de definir las rutas API
# Se encargará de servir index.html, style.css, script.js en la raíz "/"
app.mount("/", StaticFiles(directory="static", html=True), name="static")
