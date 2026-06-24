import streamlit as st
import os

# ПРИНУДИТЕЛЬНОЕ ИСПОЛЬЗОВАНИЕ KERAS 2 (Legacy)
# Это должно быть ПЕРЕД импортом tensorflow
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import tensorflow as tf
import numpy as np
from PIL import Image
import pandas as pd
import urllib.parse

# Если установлена библиотека tf_keras (пакет для совместимости с Keras 2 в TF 2.16+)
try:
    import tf_keras as keras
except ImportError:
    from tensorflow import keras

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

st.set_page_config(
    page_title="Диагностика болезней растений",
    page_icon="🌿",
    layout="wide",
)

# ... (весь CSS и CLASS_NAMES остаются прежними, пропускаю для краткости, но в финальном файле они должны быть)
# (Вставляю их сюда для полной работоспособности)

st.markdown("""<style>
.block-container { max-width: 1100px; padding-top: 2rem; }
.app-title { font-size: 2.4rem; font-weight: 800; text-align: center; background: linear-gradient(90deg, #43a047, #81c784); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: .2rem; }
.app-subtitle { text-align: center; color: var(--text-color); opacity: .7; margin-bottom: 1.6rem; }
.card { background: var(--secondary-background-color, rgba(128,128,128,.08)); border: 1px solid rgba(128,128,128,.18); border-radius: 16px; padding: 1.2rem 1.4rem; }
.badge { border-radius: 14px; padding: .9rem 1.1rem; font-size: 1.2rem; font-weight: 700; text-align: center; color: #fff; display: flex; align-items: center; justify-content: center; gap: .6rem; }
.badge-healthy { background: linear-gradient(135deg, #2e7d32, #66bb6a); }
.badge-disease { background: linear-gradient(135deg, #c62828, #fb8c00); }
.dot { width: 12px; height: 12px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 4px rgba(255,255,255,.25); }
.conf { text-align: center; color: var(--text-color); margin-top: .7rem; font-size: 1.05rem; }
.bar-track { height: 12px; border-radius: 8px; background: rgba(128,128,128,.2); overflow: hidden; margin: .5rem 0 1rem; }
.bar-fill-healthy { height: 100%; background: linear-gradient(90deg, #2e7d32, #66bb6a); }
.bar-fill-disease { height: 100%; background: linear-gradient(90deg, #c62828, #fb8c00); }
.advice { border-radius: 12px; padding: 1rem 1.2rem; line-height: 1.55; color: var(--text-color); background: rgba(251,192,45,.14); border-left: 4px solid #fbc02d; }
.advice-ok { background: rgba(67,160,71,.14); border-left: 4px solid #43a047; }
.advice b { display: block; margin-bottom: .35rem; }
.notice { border-radius: 14px; padding: 1.1rem 1.3rem; background: rgba(96,125,139,.16); border-left: 4px solid #607d8b; color: var(--text-color); line-height: 1.55; }
.notice b { display: block; margin-bottom: .4rem; font-size: 1.15rem; }
.top-item { display: flex; justify-content: space-between; align-items: center; background: rgba(128,128,128,.12); border: 1px solid rgba(128,128,128,.15); border-radius: 10px; padding: .6rem 1rem; margin-bottom: .5rem; color: var(--text-color); font-size: 1rem; }
.src-item { background: rgba(128,128,128,.10); border: 1px solid rgba(128,128,128,.15); border-radius: 12px; padding: .8rem 1.1rem; margin-bottom: .6rem; }
.src-item a { font-weight: 600; font-size: 1.02rem; text-decoration: none; }
.src-item p { margin: .3rem 0 0; opacity: .75; font-size: .9rem; }
.foot { text-align: center; color: var(--text-color); opacity: .6; margin-top: 1.5rem; font-size: .9rem; }
</style>""", unsafe_allow_html=True)

CLASS_NAMES = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
    "Blueberry___healthy", "Cherry___Powdery_mildew", "Cherry___healthy",
    "Corn___Cercospora_leaf_spot", "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy",
    "Grape___Black_rot", "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot", "Peach___healthy",
    "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy",
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch", "Strawberry___healthy",
    "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight",
    "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites",
    "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus", "Tomato___healthy"
]

DISEASE_INFO = {
    "Apple___Apple_scab": ("Яблоня — Парша", "Удаляйте и сжигайте опавшие листья осенью. Обрабатывайте фунгицидами на основе меди или серы ранней весной и после цветения."),
    "Apple___Black_rot": ("Яблоня — Чёрная гниль", "Вырезайте поражённые ветви и мумифицированные плоды. Применяйте фунгициды."),
    "Apple___Cedar_apple_rust": ("Яблоня — Ржавчина", "Убирайте можжевельники рядом. Опрыскивайте фунгицидами весной."),
    "Apple___healthy": ("Яблоня — Здоровое растение", "Растение здорово. Продолжайте регулярный уход."),
    "Blueberry___healthy": ("Голубика — Здоровое растение", "Поддерживайте кислую почву, мульчируйте."),
    "Cherry___Powdery_mildew": ("Вишня — Мучнистая роса", "Удаляйте поражённые побеги, обрабатывайте серой."),
    "Cherry___healthy": ("Вишня — Здоровое растение", "Растение здорово."),
    "Corn___Cercospora_leaf_spot": ("Кукуруза — Серая пятнистость", "Соблюдайте севооборот, используйте устойчивые гибриды."),
    "Corn___Common_rust": ("Кукуруза — Обыкновенная ржавчина", "Используйте устойчивые гибриды."),
    "Corn___Northern_Leaf_Blight": ("Кукуруза — Северный гельминтоспориоз", "Севооборот и заделка остатков."),
    "Corn___healthy": ("Кукуруза — Здоровое растение", "Растение здорово."),
    "Grape___Black_rot": ("Виноград — Чёрная гниль", "Удаляйте мумифицированные ягоды, применяйте фунгициды."),
    "Grape___Esca_(Black_Measles)": ("Виноград — Эска", "Удаляйте поражённую древесину. Радикального лечения нет."),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": ("Виноград — Пятнистость листьев", "Удаляйте листья, улучшайте проветривание."),
    "Grape___healthy": ("Виноград — Здоровое растение", "Растение здорово."),
    "Orange___Haunglongbing_(Citrus_greening)": ("Апельсин — Позеленение", "Удаляйте заражённые деревья."),
    "Peach___Bacterial_spot": ("Персик — Бактериальная пятнистость", "Обрабатывайте медью в период покоя."),
    "Peach___healthy": ("Персик — Здоровое растение", "Растение здорово."),
    "Pepper,_bell___Bacterial_spot": ("Перец — Бактериальная пятнистость", "Соблюдайте севооборот, обработки медью."),
    "Pepper,_bell___healthy": ("Перец — Здоровое растение", "Растение здорово."),
    "Potato___Early_blight": ("Картофель — Альтернариоз", "Севооборот, фунгициды при первых признаках."),
    "Potato___Late_blight": ("Картофель — Фитофтороз", "Удаляйте больные растения, профилактика фунгицидами."),
    "Potato___healthy": ("Картофель — Здоровое растение", "Растение здорово."),
    "Raspberry___healthy": ("Малина — Здоровое растение", "Растение здорово."),
    "Soybean___healthy": ("Соя — Здоровое растение", "Растение здорово."),
    "Squash___Powdery_mildew": ("Кабачок — Мучнистая роса", "Удаляйте листья, обрабатывайте фунгицидами."),
    "Strawberry___Leaf_scorch": ("Клубника — Ожог листьев", "Удаляйте старые листья, прореживайте грядки."),
    "Strawberry___healthy": ("Клубника — Здоровое растение", "Растение здорово."),
    "Tomato___Bacterial_spot": ("Томат — Бактериальная пятнистость", "Соблюдайте севооборот, обработки медью."),
    "Tomato___Early_blight": ("Томат — Альтернариоз", "Удаляйте нижние листья, мульчируйте."),
    "Tomato___Late_blight": ("Томат — Фитофтороз", "Удаляйте больные растения, полив под корень."),
    "Tomato___Leaf_Mold": ("Томат — Бурая плесень", "Проветривайте теплицу, снижайте влажность."),
    "Tomato___Septoria_leaf_spot": ("Томат — Септориоз", "Удаляйте нижние листья, мульчируйте."),
    "Tomato___Spider_mites": ("Томат — Паутинный клещ", "Повышайте влажность, акарициды."),
    "Tomato___Target_Spot": ("Томат — Мишеневидная пятнистость", "Проветривание и севооборот."),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": ("Томат — Жёлтая курчавость", "Борьба с белокрылкой."),
    "Tomato___Tomato_mosaic_virus": ("Томат — Вирус мозаики", "Удаляйте больные растения."),
    "Tomato___healthy": ("Томат — Здоровое растение", "Растение здорово."),
}

def ru_name(key):
    return DISEASE_INFO[key][0] if key in DISEASE_INFO else key.replace("___", " — ")

def advice_for(key):
    return DISEASE_INFO[key][1] if key in DISEASE_INFO else "Рекомендации не найдены."

def vegetation_fraction(pil_img):
    a = np.asarray(pil_img.resize((128, 128))).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    exg = 2 * g - r - b
    return float((exg > 25).mean())

@st.cache_resource
def load_model():
    path = "trained_model1.keras"
    if not os.path.exists(path):
        st.error(f"Файл {path} не найден.")
        st.stop()
    try:
        # Используем keras (который теперь либо tf_keras, либо tf.keras)
        model = keras.models.load_model(path, compile=False)
        return model
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        st.stop()

model = load_model()

# ... (остальной код интерфейса из app_fixed.py остается таким же)
# Для краткости здесь только логика предсказания

st.markdown('<div class="app-title">Диагностика болезней растений</div>', unsafe_allow_html=True)
img_input = st.file_uploader("Выберите изображение", type=["jpg", "png", "jpeg"])

if img_input:
    image = Image.open(img_input).convert("RGB")
    arr = np.expand_dims(np.array(image.resize((128, 128))), axis=0)
    preds = model.predict(arr, verbose=0)[0]
    idx = np.argmax(preds)
    confidence = preds[idx] * 100
    name = ru_name(CLASS_NAMES[idx])
    
    st.image(image, width=300)
    st.success(f"Результат: {name} (Уверенность: {confidence:.2f}%)")
    st.info(f"Совет: {advice_for(CLASS_NAMES[idx])}")
