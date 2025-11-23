import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import json
import hashlib
import time
import pandas as pd
from PIL import Image
import io

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# 👇👇👇 ZONA CRÍTICA: PEGA TU CLAVE DE GOOGLE AQUÍ ABAJO 👇👇👇
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

API_KEY = "AIzaSyBcqFlPe5l9AGNvM1uojyZMhT4IzqVcMkE"

# 👆 En la línea 17 (arriba), borra "PEGAR_TU_CLAVE_AQUI" y pon tu clave real.
# Mantén las comillas. Ejemplo: API_KEY = "AIzaSyD_tus_numeros..."

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# 👆👆👆 ¡LISTO! NO TOQUES NADA MÁS ABAJO DE ESTA LÍNEA 👆👆👆
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# --- 1. CONFIGURACIÓN DE LA APP ---
st.set_page_config(
    page_title="AUREX",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Intento de cargar desde Secrets (por si usas configuración avanzada)
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]

# --- 2. MEMORIA DE LA APP ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_hash' not in st.session_state:
    st.session_state.last_hash = None

MAX_HISTORY = 15 

# --- 3. DISEÑO "AUREX DARK PRO" ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

        .stApp {
            background-color: #000000;
            background-image: radial-gradient(circle at 50% 0%, #1a1a1a 0%, #000000 80%);
            color: #e0e0e0;
        }

        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 6rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* HEADER */
        .aurex-header {
            text-align: center;
            padding: 15px 0;
            background: rgba(0,0,0,0.9);
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 999;
            border-bottom: 1px solid #333;
            margin-bottom: 10px;
        }
        .aurex-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 26px;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 4px;
            text-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
        }
        .aurex-subtitle {
            font-family: 'Roboto', sans-serif;
            font-size: 9px;
            color: #ff6600;
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        /* TABS PERSONALIZADOS */
        div[data-testid="stTabs"] button {
            flex: 1;
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            color: #888;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #ff6600 !important;
            border-bottom-color: #ff6600 !important;
        }

        /* TARJETAS */
        .result-card {
            background: rgba(20, 20, 20, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        }
        
        .history-bg {
            position: absolute;
            top: -10px;
            right: 0px;
            font-size: 70px;
            font-family: 'Orbitron', sans-serif;
            color: rgba(255, 255, 255, 0.02);
            pointer-events: none;
        }

        .model-name {
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            color: white;
            border-bottom: 2px solid #ff6600;
            padding-bottom: 3px;
            margin-bottom: 5px;
            display: inline-block;
        }
        
        .sku-badge {
            background: #222;
            color: #aaa;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-family: monospace;
            display: inline-block;
            margin-left: 5px;
        }

        .tech-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 2px;
            background: rgba(255,255,255,0.02);
            padding: 8px;
            border-radius: 6px;
            font-size: 11px;
            color: #ccc;
            margin-bottom: 8px;
        }
        .tech-label { color: #ff6600; font-weight: bold; }

        .price-tag {
            font-size: 20px;
            font-weight: bold;
            color: #00ff00;
        }
        
        .dexter-btn {
            background: linear-gradient(135deg, #ff6600 0%, #d9534f 100%);
            color: white !important;
            padding: 6px 14px;
            border-radius: 20px;
            text-decoration: none;
            font-weight: bold;
            font-size: 11px;
            float: right;
            box-shadow: 0 2px 8px rgba(255, 68, 0, 0.4);
        }

        /* Ocultar elementos */
        #MainMenu, footer, header {visibility: hidden;}
    </style>
    
    <div class="aurex-header">
        <div class="aurex-title">AUREX</div>
        <div class="aurex-subtitle">ULTIMATE SYSTEM</div>
    </div>
""", unsafe_allow_html=True)

# --- 4. LÓGICA OPTIMIZADA (Backend) ---

def optimizar_imagen(image_bytes):
    """Reduce el tamaño de la imagen para que la IA responda más rápido"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # Redimensionar si es muy grande (Max 1024px)
        max_size = (1024, 1024)
        image.thumbnail(max_size)
        
        # Guardar en buffer comprimido
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue()
    except:
        return image_bytes # Si falla, devolver original

def consultar_gemini(entrada, tipo="imagen"):
    """Consulta flexible: sirve para Imagen o Texto"""
    # Verificación extra de seguridad
    if not API_KEY or API_KEY == "PEGAR_TU_CLAVE_AQUI": 
        return {"error": "⚠️ ERROR: No has pegado tu API KEY en la línea 17 del código."}
    
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        base_prompt = """
        Eres AUREX, experto en calzado técnico.
        Responde SIEMPRE en este JSON exacto:
        {"sku": "...", "modelo": "...", "uso": "...", "tech": "..."}
        
        Instrucciones:
        1. SKU: Prioridad máxima. Si no hay, pon "".
        2. Modelo: Nombre comercial exacto.
        3. Uso: (ej: Running, Basket, Moda). Máx 3 palabras.
        4. Tech: (ej: Boost, Air, React). Máx 3 palabras.
        """

        if tipo == "imagen":
            prompt = base_prompt + " Analiza la imagen para extraer datos."
            blob = {"mime_type": "image/jpeg", "data": entrada}
            response = model.generate_content([prompt, blob], generation_config={"response_mime_type": "application/json"})
        else:
            prompt = base_prompt + f" El usuario busca: '{entrada}'. Completa los datos técnicos de ese modelo."
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

def buscar_dexter(termino):
    """Buscador optimizado"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10)'}
        clean = termino.strip().replace(" ", "%20")
        url = f"https://www.dexter.com.ar/buscar?q={clean}"
        res = requests.get(url, headers=headers, timeout=4) # Timeout rápido
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, 'html.parser')
            precio = soup.find("span", class_="sales") or soup.find("span", class_="value")
            no_hits = soup.find("div", class_="no-hits")
            
            if no_hits: return "Agotado", url, False
            if precio: return precio.get_text().strip(), url, True
            return "Ver Web", url, True
        return "Error Red", url, False
    except:
        return "Error", "", False

def guardar_historial(data, precio, link, ok):
    nuevo = {
        "id_scan": len(st.session_state.history) + 1,
        "modelo": data.get("modelo", "Desconocido"),
        "sku": data.get("sku", ""),
        "uso": data.get("uso", "N/A"),
        "tech": data.get("tech", "N/A"),
        "precio": precio,
        "link": link,
        "ok": ok,
        "hora": time.strftime("%H:%M")
    }
    st.session_state.history.insert(0, nuevo)
    if len(st.session_state.history) > MAX_HISTORY:
        st.session_state.history.pop()

# --- 5. INTERFAZ PRINCIPAL (TABS) ---

tab1, tab2, tab3 = st.tabs(["📷 ESCÁNER", "⌨️ MANUAL", "💾 DATOS"])

# --- TAB 1: CÁMARA ---
with tab1:
    img_file = st.camera_input("SCAN", label_visibility="collapsed")

    if img_file:
        bytes_data = img_file.getvalue()
        curr_hash = hashlib.md5(bytes_data).hexdigest()
        
        if curr_hash != st.session_state.last_hash:
            st.session_state.last_hash = curr_hash
            
            with st.spinner('⚡ OPTIMIZANDO Y ANALIZANDO...'):
                img_optimizada = optimizar_imagen(bytes_data)
                data = consultar_gemini(img_optimizada, tipo="imagen")
                
                if data and "error" not in data:
                    sku = data.get("sku", "")
                    modelo = data.get("modelo", "")
                    busqueda = sku if (sku and len(sku) > 3) else modelo
                    
                    precio, link, ok = buscar_dexter(busqueda)
                    guardar_historial(data, precio, link, ok)
                elif data and "error" in data:
                     st.error(data['error'])

# --- TAB 2: MANUAL ---
with tab2:
    with st.form("manual_form"):
        texto_busqueda = st.text_input("Escribe el modelo o SKU:", placeholder="Ej: Nike Pegasus 40")
        enviar = st.form_submit_button("ANALIZAR", use_container_width=True)
        
    if enviar and texto_busqueda:
        with st.spinner('⚡ BUSCANDO...'):
            precio, link, ok = buscar_dexter(texto_busqueda)
            data = consultar_gemini(texto_busqueda, tipo="texto")
            if "error" not in data:
                guardar_historial(data, precio, link, ok)
            else:
                st.error(data["error"])

# --- TAB 3: DATOS Y EXPORTAR ---
with tab3:
    if st.session_state.history:
        st.caption("Gestiona tu sesión actual")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("BORRAR TODO", type="primary", use_container_width=True):
                st.session_state.history = []
                st.rerun()
        with col2:
            df = pd.DataFrame(st.session_state.history)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "DESCARGAR CSV",
                data=csv,
                file_name="aurex_scan.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        st.dataframe(df, hide_index=True)
    else:
        st.info("El historial está vacío.")

# --- 6. RENDERIZADO DE RESULTADOS (COMÚN) ---
if st.session_state.history:
    st.markdown("---")
    st.caption(f"ÚLTIMOS ESCANEOS ({len(st.session_state.history)})")
    
    for i, item in enumerate(st.session_state.history):
        color_p = "#00ff00" if item['ok'] else "#ff4444"
        opacidad = "1" if i == 0 else "0.7"
        
        st.markdown(f"""
        <div class="result-card" style="opacity: {opacidad};">
            <div class="history-bg">{item['id_scan']}</div>
            <div style="position: relative; z-index: 2;">
                <div style="display:flex; justify-content:space-between;">
                    <div class="model-name">{item['modelo']}</div>
                    <div style="color:#666; font-size:10px;">{item['hora']}</div>
                </div>
                <div><span class="sku-badge">SKU: {item['sku']}</span></div>
                
                <div class="tech-grid" style="margin-top:8px;">
                    <div><span class="tech-label">USO:</span> {item['uso']}</div>
                    <div><span class="tech-label">TECH:</span> {item['tech']}</div>
                </div>
                
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
                    <div class="price-tag" style="color: {color_p}">{item['precio']}</div>
                    <a href="{item['link']}" target="_blank" class="dexter-btn">VER DEXTER ➔</a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
