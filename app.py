import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importante para permitir conexiones desde Lovable
from googlesearch import search
from openai import OpenAI
from supabase import Client, create_client

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app)

# Cliente oficial de OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extraer_texto_de_url(url):
    """Visita la URL enviada y extrae el texto limpio de la página web."""
    if not url or not url.startswith("http"):
        return ""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.extract()
            parrafos = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
            return " ".join(parrafos[:12])[:3500] 
    except Exception as e:
        print(f"Error al inspeccionar la URL: {e}")
    return ""

def analizar_con_inteligencia_artificial(url, texto_usuario, pregunta):
    contenido_web_scraping = extraer_texto_de_url(url)
    
    contexto_analisis = f"""
    URL: {url}
    Fragmento de usuario: {texto_usuario}
    Contenido web (Scraping): {contenido_web_scraping}
    Objetivo: {pregunta}
    """

    prompt_sistema = """
    Eres el motor forense del S.I.F.D. Evalúa la veracidad y calidad de la información.
    Responde usando estrictamente estas etiquetas:

    [ESTADO]
    ALERTA / RIESGO (o VERIFICADO / CONFIANZA ALTA)

    [CONFIANZA]
    Un número entero de 0 a 100 (ejm: 25%).

    [RESOLUCION]
    Redacta un informe forense analítico profundo (mínimo 2 a 3 párrafos amplios y detallados). Evalúa la fuente, contrasta con ciencia/hechos y da un dictamen forense detallado. Explayate lo necesario, no seas breve.

    [CITA]
    Cita bibliográfica en formato APA 7ma edición para el sitio evaluado.

    [EVIDENCIAS]
    Genera 3 hallazgos clave separados por '|'. (Ejm: Discrepancia: Sin rigor | Análisis: Lenguaje alarmista | Coincidencia: Indexado)

    [REPOSITORIOS]
    Sugiere exactamente 4 repositorios, bases de datos científicas, gubernamentales o académicas altamente relevantes al TEMA ESPECÍFICO de esta consulta. 
    Usa estrictamente este formato por línea: Nombre | Breve descripción | URL
    """

    response = client.chat.completions.create(
        model="gpt-6-luna",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": contexto_analisis}
        ]
    )
    return response.choices[0].message.content

def extraer_bloque(etiqueta, texto, por_defecto=""):
    patron = rf"\[{etiqueta}\]\s*(.*?)(?=\s*\[(?:ESTADO|CONFIANZA|RESOLUCION|CITA|EVIDENCIAS|REPOSITORIOS)\]|$)"
    match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else por_defecto

@app.route('/', methods=['POST', 'GET'])
def analizar():
    if request.method == 'GET':
        return jsonify({"status": "Servidor S.I.F.D. activo."}), 200

    datos = request.get_json() or {}
    url = datos.get('url', '')
    texto = datos.get('texto', '')
    pregunta = datos.get('pregunta', '')

    try:
        respuesta_bruta = analizar_con_inteligencia_artificial(url, texto, pregunta)
        
        estado = extraer_bloque("ESTADO", respuesta_bruta, "FUENTE NO CONFIRMADA")
        confianza = extraer_bloque("CONFIANZA", respuesta_bruta, "50%")
        resolucion = extraer_bloque("RESOLUCION", respuesta_bruta, "No se pudo generar una resolución detallada.")
        cita = extraer_bloque("CITA", respuesta_bruta, "Sin cita disponible.")
        evidencias_raw = extraer_bloque("EVIDENCIAS", respuesta_bruta, "")
        repositorios_raw = extraer_bloque("REPOSITORIOS", respuesta_bruta, "")

        evidencias_list = [item.strip() for item in evidencias_raw.split('|') if item.strip()]
        
        # Procesar repositorios dinámicos a formato JSON
        repositorios_list = []
        for linea in repositorios_raw.split('\n'):
            if '|' in linea:
                partes = linea.split('|')
                if len(partes) >= 3:
                    repositorios_list.append({
                        "nombre": partes[0].strip(),
                        "descripcion": partes[1].strip(),
                        "url": partes[2].strip()
                    })

        return jsonify({
            "estado": estado,
            "confianza": confianza,
            "resolucion": resolucion,
            "cita_apa": cita,
            "evidencias": evidencias_list,
            "repositorios": repositorios_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
