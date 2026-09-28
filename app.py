import os
import re
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS  # 🌐 Importante para permitir conexiones desde Lovable
from googlesearch import search
from openai import OpenAI
from supabase import Client, create_client

# Cargar las variables de entorno desde el archivo .env en local
load_dotenv()

app = Flask(__name__)
CORS(app)  # ⚡ Habilita CORS para todas las rutas y orígenes

# 🤖 Inicialización de OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚡ Inicialización de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🟢 ENDPOINT DE VERIFICACIÓN (Ruta principal para evitar el "Not Found" en Render)
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "sistema": "S.I.F.D. Backend API",
        "estado": "Operativo 🚀",
        "version": "1.0",
        "mensaje": "El motor de inteligencia forense está en línea y esperando peticiones desde Lovable."
    }), 200


def analizar_con_inteligencia_artificial(url, texto_usuario, pregunta):
    ano_actual = datetime.now().year

    prompt_sistema = """Eres el núcleo analítico avanzado del S.I.F.D. (Sistema de Inteligencia Forense Digital). Tu objetivo NO es explicar teoría general, sino evaluar con un criterio científico, agudo y pragmático la inquietud exacta del investigador.

REGLAS CRÍTICAS DE ESTILO:
1. Cero floro: Prohibido dar introducciones históricas o definiciones de diccionario.
2. Respuestas directas: Ataca de inmediato el núcleo de la pregunta del usuario.
3. Evaluación de Fuentes: Si la URL es de plataformas colaborativas como Wikipedia, debes iniciar el bloque de resolución advirtiendo de forma humana que, aunque el dato sea un punto de partida válido, carece de arbitraje científico estricto y requiere contrastación con literatura indexada (Scopus, PubMed, etc.).
4. Enfoque dinámico: Conéctalo directamente con el impacto del fragmento provisto."""

    prompt_usuario = f"""
    CONTEXTO DE AUDITORÍA:
    - URL evaluada: {url}
    - Fragmento de evidencia: "{texto_usuario}"

    INQUIETUD ESPECÍFICA DEL INVESTIGADOR (Responde strictly a esto):
    -> "{pregunta}"

    Genera tu respuesta respetando de forma milimétrica las siguientes 4 etiquetas. No uses negritas en los títulos de las etiquetas:

    [ESTADO]
    Determina el nivel de confianza de forma corta (Ej: VERIFICADO / CONFIANZA ALTA o FUENTE COLABORATIVA EDITABLE).

    [RESOLUCION]
    Párrafo 1: Evaluación crítica de la fuente (Si es Wikipedia, menciona por qué no es 100% confiable y qué mejores alternativas indexadas existen).
    Párrafo 2: Respuesta directa, objetiva y sin rodeos a la inquietud del investigador, analizando la dinámica e impacto real del problema planteado (por ejemplo, el efecto evolutivo o ecológico de la resistencia).

    [TERMINOS_BUSQUEDA]
    3 a 4 palabras clave técnicas avanzadas para que el investigador verifique esto en buscadores científicos reales. Solo los términos separados por comas.

    [CITA]
    Genera la citación exacta en formato APA 7ma edición para la fuente web provista.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.3
        )

        respuesta_ia = response.choices[0].message.content
        print(f"\n--- RESPUESTA BRUTA DE LA IA ---\n{respuesta_ia}\n--------------------------------\n")

        def extraer_bloque(etiqueta, texto, por_defecto=""):
            patron = rf"\[{etiqueta}\]\s*(.*?)(?=\s*\[(?:ESTADO|RESOLUCION|TERMINOS_BUSQUEDA|CITA)\]|$)"
            match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
            if match:
                res = match.group(1).strip()
                res = re.sub(r"^->\s*", "", res)
                return res.replace("**", "").replace("__", "").strip()
            return por_defecto

        estado = extraer_bloque("ESTADO", respuesta_ia, "EVALUACIÓN COMPLETADA")
        terminos = extraer_bloque("TERMINOS_BUSQUEDA", respuesta_ia, "ciencia")
        cita_apa = extraer_bloque("CITA", respuesta_ia, f"Fuente Digitalizada. ({ano_actual}). Extracción S.I.F.D.")

        resolucion_cruda = extraer_bloque("RESOLUCION", respuesta_ia, "")
        if resolucion_cruda:
            lineas_res = [linea.strip() for linea in resolucion_cruda.split('\n') if linea.strip()]
            resolucion = "\n\n".join(lineas_res)  # Formato limpio para React
        else:
            resolucion = "Análisis procesado correctamente."

        return estado, resolucion, terminos, cita_apa

    except Exception as e:
        print(f"❌ Error en OpenAI: {e}")
        return "CONFIANZA LIMITADA", f"Error de conexión. Detalle: {e}", "ciencia", f"Consulta Digital. ({ano_actual})."


def obtener_repositorios_tematicos(query_limpia):
    """Clasifica los repositorios según el tema de las palabras clave de la IA"""
    q = query_limpia.lower()
    
    # 🧬 Medicina, Microbiología y Salud
    if any(k in q for k in ["coli", "bacteria", "virus", "salud", "medicina", "fago", "ampicilina", "fármaco", "enfermedad"]):
        return [
            {"titulo": "PubMed / NCBI", "url": f"https://pubmed.ncbi.nlm.nih.gov/?term={query_limpia.replace(' ', '+')}", "snippet": "Base de datos biomédica internacional revisada por pares."},
            {"titulo": "SciELO Salud Pública", "url": f"https://search.scielo.org/?q={query_limpia.replace(' ', '+')}", "snippet": "Revistas científicas de acceso abierto en ciencias de la salud."}
        ]
    
    # 🌿 Medio Ambiente, Ecología y Clima
    elif any(k in q for k in ["clima", "agua", "ambiente", "ecología", "bosque", "contaminación", "especie"]):
        return [
            {"titulo": "BioOne Complete", "url": f"https://bioone.org/search?term={query_limpia.replace(' ', '+')}", "snippet": "Investigación biológica, ecológica y de ciencias ambientales."},
            {"titulo": "Redalyc Ciencias Naturales", "url": f"https://www.redalyc.org/busqueda.oa?q={query_limpia.replace(' ', '+')}", "snippet": "Red de revistas científicas de América Latina y el Caribe."}
        ]
        
    # ⚖️ Derecho, Política y Ciencias Sociales
    elif any(k in q for k in ["ley", "gobierno", "corrupción", "decreto", "política", "derecho", "social"]):
        return [
            {"titulo": "Dialnet Social", "url": f"https://dialnet.unirioja.es/buscar/documentos?querys.texto={query_limpia.replace(' ', '+')}", "snippet": "Portal de difusión científica en ciencias jurídicas y sociales."},
            {"titulo": "CLACSO", "url": f"https://www.clacso.org.ar/biblioteca_virtual/", "snippet": "Red de ciencias sociales de América Latina."}
        ]
        
    # 🔬 Multidisciplinario General (Por defecto)
    else:
        return [
            {"titulo": "Google Académico", "url": f"https://scholar.google.es/scholar?q={query_limpia.replace(' ', '+')}", "snippet": "Buscador internacional de literatura académica y tesis."},
            {"titulo": "CORE Research", "url": f"https://core.ac.uk/search?q={query_limpia.replace(' ', '+')}", "snippet": "Agregador mundial de artículos de investigación en acceso abierto."}
        ]


def procesar_consulta_dinamica(url_ingresada, texto_investigacion, pregunta_usuario):
    url_limpia = url_ingresada.strip()
    texto_limpio = texto_investigacion.strip()
    pregunta_limpia = pregunta_usuario.strip()

    estado, enfoque_respuesta, terminos_busqueda, cita_apa = analizar_con_inteligencia_artificial(
        url_limpia, texto_limpio, pregunta_limpia
    )

    fuentes_vivas = []
    verbos_vacios = ["esta", "pagina", "mismo", "gobierno", "peru", "analizar", "quiero", "necesito", "sobre", "como", "sirve", "para", "buscar"]
    palabras_clave = [w for w in re.findall(r"\b\w{4,15}\b", terminos_busqueda.lower()) if w not in verbos_vacios]

    query_final = " ".join(palabras_clave) if palabras_clave else terminos_busqueda

    # Búsqueda en Google (Fuentes de contraste)
    try:
        print(f"🔍 Ejecutando Google Search real para: {query_final}")
        enlaces = list(search(query_final, num_results=5, lang="es"))

        for link in enlaces:
            if link.lower().rstrip("/") == url_limpia.lower().rstrip("/"):
                continue

            dominio = link.split("//")[-1].split("/")[0].replace("www.", "")
            titulo_dinamico = f"Evidencia de Contraste: {dominio}"

            if len(fuentes_vivas) < 2:
                fuentes_vivas.append({
                    "url": link,
                    "titulo": titulo_dinamico,
                    "snippet": f"Portal externo indexado útil para contrastar datos sobre '{query_final}'.",
                })
    except Exception as e:
        print(f"⚠️ Error o bloqueo temporal en Google Search: {e}")

    # Fallback si Google Search falla
    if not fuentes_vivas:
        termino_url = query_final.replace(" ", "+")
        fuentes_vivas.append({
            "url": f"https://alicia.concytec.gob.pe/vufind/Search/Results?lookfor={termino_url}",
            "titulo": f"Contraste Institucional: Repositorio ALICIA",
            "snippet": f"Mapeo de contingencia científica activo para '{query_final.title()}'.",
        })

    # 🚀 Llamada a la función dinámica de repositorios
    fuentes_sugeridas = obtener_repositorios_tematicos(query_final)

    return estado, enfoque_respuesta, fuentes_vivas, fuentes_sugeridas, cita_apa


# 🎯 ENDPOINT QUE CONSUME LOVABLE (REACT)
@app.route("/api/analizar", methods=["POST"])
def analizar_api():
    try:
        data = request.get_json() or {}

        url_input = data.get("url") or data.get("url_fuente") or ""
        texto_input = data.get("fragmento") or data.get("texto_investigacion") or ""
        pregunta_input = data.get("pregunta") or data.get("pregunta_usuario") or ""

        if not url_input and not texto_input:
            return jsonify({"error": "Faltan parámetros obligatorios"}), 400

        estado, resolucion, fuentes_vivas, fuentes_sugeridas, cita_apa = procesar_consulta_dinamica(
            url_input, texto_input, pregunta_input
        )

        return jsonify({
            "estado": estado,
            "veredicto": estado,
            "resolucion": resolucion,
            "cita_apa": cita_apa,
            "evidencias": fuentes_vivas,
            "repositorios": fuentes_sugeridas
        }), 200

    except Exception as e:
        print(f"❌ Error en /api/analizar: {e}")
        return jsonify({"error": str(e)}), 500


# 📥 ENDPOINT PARA COMPARTIR FEEDBACK O COMENTARIOS
@app.route("/api/feedback", methods=["POST"])
def feedback_api():
    try:
        data = request.get_json() or {}
        comentario = data.get("comentario") or ""

        if comentario.strip():
            supabase.table("sugerencias").insert({
                "comentario": comentario.strip(),
                "creado_en": datetime.now().isoformat(),
            }).execute()
            return jsonify({"status": "exito", "mensaje": "Comentario guardado"}), 200

        return jsonify({"error": "El comentario está vacío"}), 400
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
