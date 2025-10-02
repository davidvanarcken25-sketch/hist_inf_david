import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# ================= FUNCIONES =================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return None

def analizar_dibujo(base64_image, api_key):
    prompt_text = "Describe en español y de forma breve lo que aparece en este dibujo relacionado con fútbol."
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content if response.choices[0].message.content else ""

# ================= INTERFAZ =================
st.set_page_config(page_title='Historia de Fútbol')
st.title('⚽ Generador de Historias de Fútbol a partir de Dibujos')

with st.sidebar:
    st.subheader("Instrucciones:")
    st.write("👉 Dibuja primero un elemento de fútbol (ej: balón).")
    st.write("👉 Luego dibuja el segundo (ej: jugador).")
    st.write("👉 Finalmente, dibuja el tercero (ej: portería).")
    st.write("✨ Con base en los 3 se creará una historia de fútbol.")

# Inicializar estados
if "step" not in st.session_state:
    st.session_state.step = 1
if "descriptions" not in st.session_state:
    st.session_state.descriptions = []

# Configuración del canvas
drawing_mode = "freedraw"
stroke_width = st.sidebar.slider('Ancho de línea', 1, 30, 5)
stroke_color = "#000000"
bg_color = "#FFFFFF"

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=300,
    width=400,
    drawing_mode=drawing_mode,
    key=f"canvas_{st.session_state.step}",
)

# Clave API
ke = st.text_input('Ingresa tu Clave de OpenAI', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ['OPENAI_API_KEY'] if ke else None
client = OpenAI(api_key=api_key) if ke else None

# Botón de análisis paso por paso
if canvas_result.image_data is not None and api_key:
    if st.button(f"Analizar dibujo {st.session_state.step}"):
        with st.spinner(f"Analizando dibujo {st.session_state.step} ..."):
            input_numpy_array = np.array(canvas_result.image_data)
            input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
            file_name = f"dibujo_{st.session_state.step}.png"
            input_image.save(file_name)

            base64_image = encode_image_to_base64(file_name)
            desc = analizar_dibujo(base64_image, api_key)

            st.session_state.descriptions.append(desc)
            st.success(f"Dibujo {st.session_state.step} analizado: {desc}")

            # Avanzar de paso
            st.session_state.step += 1

# Una vez estén los 3 dibujos, generar la historia
if len(st.session_state.descriptions) == 3:
    st.divider()
    st.subheader("📚 Crear historia de fútbol")
    if st.button("✨ Generar historia"):
        with st.spinner("Creando historia de fútbol..."):
            joined_desc = " | ".join(st.session_state.descriptions)
            story_prompt = f"Tienes estas tres descripciones de dibujos: {joined_desc}. Con base en ellas, crea una historia breve, emocionante y creativa sobre un partido de fútbol."
            
            story_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": story_prompt}],
                max_tokens=600,
            )
            
            st.markdown("**📖 Tu historia de fútbol:**")
            st.write(story_response.choices[0].message.content)


# Warnings for user action required
if not api_key:
    st.warning("Por favor ingresa tu API key.")
