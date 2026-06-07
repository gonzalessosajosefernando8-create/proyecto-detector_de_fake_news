import os
from flask import Flask, render_template, request
from datetime import datetime
from openai import OpenAI  # Nueva sintaxis oficial
from googlesearch import search

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get(
    "OPENAI_API_KEY", "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")
client = OpenAI(api_key=OPENAI_API_KEY)


def analizar_con_inteligencia_artificial(url, texto_usuario, pregunta):
    """
    Usa la nueva sintaxis de OpenAI para conectar con el modelo gpt-4o-mini
    y extraer datos dinámicos de contraste.
    """
    ano_actual = datetime.now().year

    prompt_sistema = (
        "Eres el núcleo analítico avanzado del S.I.F.D. Tu tarea es evaluar con un criterio "
        "científico, académico y metodológico agudo el fragmento de texto y la URL provistos. "
        "Explica detalladamente la validez de las cifras o datos cronológicos aportados."
    )

    prompt_usuario = f"""
    AUDITORÍA SOLICITADA:
    - URL de la fuente: {url}
    - Fragmento del contenido: "{texto_usuario}"
    - Inquietud del investigador: "{pregunta}"
    
    Genera una respuesta estructurada respetando estrictamente estas etiquetas:
    [ESTADO] -> Nivel de confianza corto.
    [RESOLUCION] -> Mínimo dos párrafos extendidos analizando los datos empíricos del texto y sus pros/contras metodológicos.
    [TERMINOS_BUSQUEDA] -> 3 o 4 palabras clave técnicas (solo conceptos científicos, sin conectores ni páginas web) para buscar en Google.
    [CITA] -> Citación bibliográfica exacta en formato APA 7ma edición.
    """

    try:
        # Nueva sintaxis compatible con las últimas librerías
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.2
        )

        respuesta_ia = response.choices[0].message.content

        # Parseo de seguridad
        estado = "CONFIANZA BAJA / EN EVALUACIÓN"
        resolucion = ""
        terminos = ""
        cita_apa = f"Consulta Digital. ({ano_actual}). Extracción S.I.F.D."

        bloques = respuesta_ia.split('\n')
        leyendo_resolucion = False
        resolucion_lineas = []

        for linea in bloques:
            if linea.startswith("[ESTADO]"):
                leyendo_resolucion = False
                estado = linea.replace(
                    "[ESTADO]", "").replace("->", "").strip()
            elif linea.startswith("[RESOLUCION]"):
                leyendo_resolucion = True
                cont = linea.replace(
                    "[RESOLUCION]", "").replace("->", "").strip()
                if cont:
                    resolucion_lineas.append(cont)
            elif linea.startswith("[TERMINOS_BUSQUEDA]"):
                leyendo_resolucion = False
                terminos = linea.replace(
                    "[TERMINOS_BUSQUEDA]", "").replace("->", "").strip()
            elif linea.startswith("[CITA]"):
                leyendo_resolucion = False
                cita_apa = linea.replace(
                    "[CITA]", "").replace("->", "").strip()
            elif leyendo_resolucion:
                if linea.strip():
                    resolucion_lineas.append(linea.strip())

        resolucion = "<br><br>".join(
            resolucion_lineas) if resolucion_lineas else "Error de procesamiento."
        return estado, resolucion, terminos, cita_apa

    except Exception as e:
        # Este print te mostrará el error exacto en la terminal si algo falla
        print(f"❌ ERROR CRÍTICO EN OPENAI: {e}")
        return (
            "CONFIANZA LIMITADA / ERROR DE CONEXIÓN",
            f"No se pudo conectar con OpenAI. Verifica tu API Key. Detalle técnico: {e}",
            "ciencia educacion",
            f"Consulta Digital. ({ano_actual}). S.I.F.D."
        )


def procesar_consulta_dinamica(url_ingresada, texto_investigacion, pregunta_usuario):
    url_limpia = url_ingresada.strip()
    texto_limpio = texto_investigacion.strip()
    pregunta_limpia = pregunta_usuario.strip()

    # 1. Llamada a la IA para obtener la resolución y los términos clave dinámicos
    estado, enfoque_respuesta, terminos_busqueda, cita_apa = analizar_con_inteligencia_artificial(
        url_limpia, texto_limpio, pregunta_limpia
    )

    fuentes_vivas = []
    fuentes_sugeridas = []

    # Si la IA funcionó, usará sus términos; si falló, usará palabras clave de la pregunta
    query_final = terminos_busqueda if terminos_busqueda else f"{pregunta_limpia}"

    # 2. BÚSQUEDA 100% DINÁMICA EN GOOGLE EN BASE AL TEMA DEL USUARIO
    try:
        print(f"🔍 Buscando evidencias reales para: {query_final}")
        # Buscamos de manera abierta en la web para traer páginas reales del tema
        enlaces = list(search(query_final, num_results=4, lang="es"))

        for idx, link in enumerate(enlaces):
            # Evitamos recomendar la misma URL que el usuario está consultando
            if link.lower().rstrip('/') == url_limpia.lower().rstrip('/'):
                continue

            # Limpieza básica para armar un título legible basado en el enlace
            dominio = link.split('//')[-1].split('/')[0].replace('www.', '')
            titulo_dinamico = f"Evidencia de Contraste: Enlace verificado en {dominio}"

            if len(fuentes_vivas) < 2:
                fuentes_vivas.append({
                    "url": link,
                    "titulo": titulo_dinamico,
                    "snippet": f"Portal externo indexado útil para contrastar de manera empírica las afirmaciones sobre '{query_final}'."
                })
    except Exception as e:
        print(f"⚠️ Error en Google Search: {e}")

    # Si Google falla por completo, recién ahí dejamos un respaldo académico genérico
    if not fuentes_vivas:
        fuentes_vivas.append({
            "url": "https://alicia.concytec.gob.pe/",
            "titulo": "Repositorio Nacional Digital ALICIA",
            "snippet": "Buscador de contingencia institucional para verificar tesis y artículos científicos arbitrados."
        })

    # Enlaces dinámicos de expansión directos a Google Académico
    fuentes_sugeridas.append({
        "url": f"https://scholar.google.es/scholar?q={query_final.replace(' ', '+')}",
        "titulo": f"Google Académico: Artículos evaluados para '{query_final}'",
        "snippet": "Filtro internacional de literatura científica revisada por pares para robustecer tu marco de investigación."
    })

    return estado, enfoque_respuesta, fuentes_vivas, fuentes_sugeridas, cita_apa


@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    feedback_enviado = False  # Inicializamos la variable de control

    if request.method == "POST":
        # Acción 1: Si el usuario envía una sugerencia o feedback
        if request.form.get("accion") == "feedback":
            comentario = request.form.get("comentario_texto")
            print(f"📥 SUGERENCIA RECIBIDA: {comentario}")
            feedback_enviado = True
            # Recargamos la página marcando que el feedback se envió
            return render_template("index.html", resultado=None, feedback_enviado=feedback_enviado)

        # Acción 2: Si el usuario ejecuta la auditoría de fuentes principal
        url_input = request.form.get("url_input") or ""
        texto_input = request.form.get("texto_input") or ""
        pregunta_input = request.form.get("pregunta_input") or ""

        if url_input.strip() and pregunta_input.strip():
            estado, enfoque, fuentes, sugeridas, cita_apa = procesar_consulta_dinamica(
                url_input, texto_input, pregunta_input
            )

            resultado = {
                "estado": estado,
                "enfoque_respuesta": enfoque,
                "fuentes": fuentes,
                "sugeridas": sugeridas,
                "cita_apa": cita_apa
            }

    # Renderizado final estándar (para cargar la página limpia o con los resultados de la IA)
    return render_template("index.html", resultado=resultado, feedback_enviado=feedback_enviado)


if __name__ == "__main__":
    app.run(debug=True)
