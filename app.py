import os
import re
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request
from googlesearch import search
from openai import OpenAI
from supabase import Client, create_client

# Cargar las variables de entorno desde el archivo .env en local
load_dotenv()

app = Flask(__name__)

# 🤖 Inicialización de OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚡ Inicialización de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def analizar_con_inteligencia_artificial(url, texto_usuario, pregunta):
    """Usa OpenAI y procesa de forma flexible la respuesta para asegurar

    que la cita APA y los términos de búsqueda se extraigan mediante expresiones
    regulares robustas.
    """
    ano_actual = datetime.now().year

    prompt_sistema = (
        "Eres el núcleo analítico avanzado del S.I.F.D. Tu tarea es evaluar con un criterio "
        "científico, académico y metodológico agudo el fragmento de texto y la URL provistos. "
        "Sé explícito y detallado en tu análisis."
    )

    prompt_usuario = f"""
    AUDITORÍA SOLICITADA:
    - URL de la fuente: {url}
    - Fragmento del contenido: "{texto_usuario}"
    - Inquietud del investigador: "{pregunta}"
    
    Genera tu respuesta respetando estrictamente la estructura de estas 4 etiquetas. No uses negritas en los títulos de las etiquetas y pon cada bloque separado:
    
    [ESTADO]
    Determina el nivel de confianza de forma corta (Ej: NIVEL DE CONFIANZA MEDIO / DIVULGACIÓN INDEPENDIENTE o COMPLETADA o CERTIFICADA).
    
    [RESOLUCION]
    Escribe mínimo dos párrafos detallados analizando de forma científica los datos del texto.
    
    [TERMINOS_BUSQUEDA]
    Pon de 3 a 4 palabras clave técnicas para buscar en Google (Ej: cronoestratigrafia permico paleozoico). No agregues nada más en esta línea.
    
    [CITA]
    Genera la citación exacta en formato APA 7ma edición para páginas web.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.3,
        )

        respuesta_ia = response.choices[0].message.content
        print(
            f"\n--- RESPUESTA BRUTA DE LA IA ---\n{respuesta_ia}\n--------------------------------\n"
        )

        # 🔍 EXTRACCIÓN ROBUSTA CON EXPRESIONES REGULARES (Evita rupturas por saltos de línea)
        def extraer_bloque(etiqueta, texto, por_defecto=""):
            # Este patrón busca el tag sin importar mayúsculas/minúsculas y captura todo hasta el siguiente tag o fin de texto
            patron = rf"\[{etiqueta}\]\s*(.*?)(?=\s*\[(?:ESTADO|RESOLUCION|TERMINOS_BUSQUEDA|CITA)\]|$)"
            match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
            if match:
                res = match.group(1).strip()
                # Limpiar posibles flechas decorativas "->" o formatos markdown residuales
                res = re.sub(r"^->\s*", "", res)
                return res.replace("**", "").replace("__", "")
            return por_defecto

        estado = extraer_bloque("ESTADO", respuesta_ia,
                                "EVALUACIÓN COMPLETADA")
        terminos = extraer_bloque("TERMINOS_BUSQUEDA", respuesta_ia, "ciencia")
        cita_apa = extraer_bloque(
            "CITA",
            respuesta_ia,
            f"Fuente Digitalizada. ({ano_actual}). Extracción S.I.F.D.",
        )

        # Procesar la resolución separando los párrafos por saltos de línea para inyectar los <br><br>
        resolucion_cruda = extraer_bloque("RESOLUCION", respuesta_ia, "")
        if resolucion_cruda:
            # Filtramos líneas vacías y las unimos de forma limpia
            lineas_res = [
                linea.strip()
                for linea in resolucion_cruda.split("\n")
                if linea.strip()
            ]
            resolucion = "<br><br>".join(lineas_res)
        else:
            resolucion = "Análisis procesado correctamente."

        return estado, resolucion, terminos, cita_apa

    except Exception as e:
        print(f"❌ Error en OpenAI: {e}")
        return (
            "CONFIANZA LIMITADA",
            f"Error de conexión local. Detalle: {e}",
            "ciencia",
            f"Consulta Digital. ({ano_actual}).",
        )


def procesar_consulta_dinamica(
    url_ingresada, texto_investigacion, pregunta_usuario
):
    url_limpia = url_ingresada.strip()
    texto_limpio = texto_investigacion.strip()
    pregunta_limpia = pregunta_usuario.strip()

    # 1. Llamada a la IA para obtener la resolución y los términos clave dinámicos
    (
        estado,
        enfoque_respuesta,
        terminos_busqueda,
        cita_apa,
    ) = analizar_con_inteligencia_artificial(
        url_limpia, texto_limpio, pregunta_limpia
    )

    fuentes_vivas = []
    fuentes_sugeridas = []

    # Filtrado semántico para limpiar conectores y quedarse únicamente con palabras clave potentes
    verbos_vacios = [
        "esta",
        "pagina",
        "mismo",
        "gobierno",
        "peru",
        "analizar",
        "quiero",
        "necesito",
        "sobre",
        "como",
        "sirve",
        "para",
        "buscar",
    ]
    palabras_clave = [
        w
        for w in re.findall(r"\b\w{4,15}\b", terminos_busqueda.lower())
        if w not in verbos_vacios
    ]

    query_final = (
        " ".join(palabras_clave) if palabras_clave else terminos_busqueda
    )

    # 2. BÚSQUEDA DINÁMICA EN GOOGLE EN BASE AL TEMA REAL
    try:
        print(f"🔍 Ejecutando Google Search real para: {query_final}")

        # Ejecutamos la búsqueda real con los términos clave refinados
        enlaces = list(search(query_final, num_results=5, lang="es"))

        for link in enlaces:
            # Evitamos recomendar la misma URL que el usuario está auditando
            if link.lower().rstrip("/") == url_limpia.lower().rstrip("/"):
                continue

            # Extraemos un nombre de dominio amigable para mostrarlo en la interfaz
            dominio = link.split("//")[-1].split("/")[0].replace("www.", "")
            titulo_dinamico = (
                f"Evidencia de Contraste: Registro verificado en {dominio}"
            )

            if len(fuentes_vivas) < 2:
                fuentes_vivas.append(
                    {
                        "url": link,
                        "titulo": titulo_dinamico,
                        "snippet": f"Portal externo indexado útil para contrastar de manera empírica las afirmaciones sobre '{query_final}'.",
                    }
                )
    except Exception as e:
        print(f"⚠️ Error o bloqueo temporal en Google Search: {e}")

    # Sistema de contingencia inteligente con URL de ALICIA dinámica si Google falla o no encuentra ítems
    if not fuentes_vivas:
        termino_url = query_final.replace(" ", "+")
        fuentes_vivas.append(
            {
                "url": f"https://alicia.concytec.gob.pe/vufind/Search/Results?lookfor={termino_url}",
                "titulo": f"Contraste Institucional: Repositorio ALICIA (CONCYTEC) para '{query_final.title()}'",
                "snippet": "Mapeo de contingencia científica activo. Haz clic para consultar las tesis y artículos indexados en el Perú sobre este campo.",
            }
        )

    # Enlace dinámico de expansión directo a Google Académico
    fuentes_sugeridas.append(
        {
            "url": f"https://scholar.google.es/scholar?q={query_final.replace(' ', '+')}",
            "titulo": f"Google Académico: Literatura Científica para '{query_final.title()}'",
            "snippet": "Filtro internacional de literatura científica revisada por pares para robustecer tu marco de investigación.",
        }
    )

    return estado, enfoque_respuesta, fuentes_vivas, fuentes_sugeridas, cita_apa


@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    feedback_enviado = False

    if request.method == "POST":
        accion = request.form.get("accion")

        # 📥 ACCIÓN 1: Guardar comentarios de forma directa en Supabase
        if accion == "feedback":
            comentario = request.form.get("comentario_texto") or ""

            if comentario.strip():
                try:
                    supabase.table("sugerencias").insert(
                        {
                            "comentario": comentario.strip(),
                            "creado_en": datetime.now().isoformat(),
                        }
                    ).execute()
                    print(
                        f"🚀 ¡Comentario guardado en Supabase con éxito!: {comentario}"
                    )
                except Exception as e:
                    print(f"❌ Error al conectar con Supabase: {e}")

            feedback_enviado = True
            return render_template(
                "index.html", resultado=None, feedback_enviado=feedback_enviado
            )

        # 🔍 ACCIÓN 2: Procesar la auditoría del formulario principal
        else:
            url_input = request.form.get("url_fuente") or ""
            texto_input = request.form.get("texto_investigacion") or ""
            pregunta_input = request.form.get("pregunta_usuario") or ""

            # Ejecutamos el motor analítico dinámico
            (
                estado,
                resolucion,
                fuentes_vivas,
                fuentes_sugeridas,
                cita_apa,
            ) = procesar_consulta_dinamica(
                url_input, texto_input, pregunta_input
            )

            # Estructuramos el diccionario que leerá index.html
            resultado = {
                "estado": estado,
                "resolucion": resolucion,
                "fuentes_vivas": fuentes_vivas,
                "fuentes_sugeridas": fuentes_sugeridas,
                "cita_apa": cita_apa,
            }

    return render_template(
        "index.html", resultado=resultado, feedback_enviado=feedback_enviado
    )


if __name__ == "__main__":
    app.run(debug=True)
