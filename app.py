import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import pandas as pd
import urllib.parse
import os

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

st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; padding-top: 2rem; }

    .app-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #43a047, #81c784);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: .2rem;
    }
    .app-subtitle {
        text-align: center;
        color: var(--text-color);
        opacity: .7;
        margin-bottom: 1.6rem;
    }

    .card {
        background: var(--secondary-background-color, rgba(128,128,128,.08));
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 16px;
        padding: 1.2rem 1.4rem;
    }

    .badge {
        border-radius: 14px;
        padding: .9rem 1.1rem;
        font-size: 1.2rem;
        font-weight: 700;
        text-align: center;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: .6rem;
    }
    .badge-healthy { background: linear-gradient(135deg, #2e7d32, #66bb6a); }
    .badge-disease { background: linear-gradient(135deg, #c62828, #fb8c00); }
    .dot {
        width: 12px; height: 12px; border-radius: 50%;
        background: #fff; box-shadow: 0 0 0 4px rgba(255,255,255,.25);
    }

    .conf {
        text-align: center;
        color: var(--text-color);
        margin-top: .7rem;
        font-size: 1.05rem;
    }
    .bar-track {
        height: 12px; border-radius: 8px;
        background: rgba(128,128,128,.2);
        overflow: hidden; margin: .5rem 0 1rem;
    }
    .bar-fill-healthy { height: 100%; background: linear-gradient(90deg, #2e7d32, #66bb6a); }
    .bar-fill-disease { height: 100%; background: linear-gradient(90deg, #c62828, #fb8c00); }

    .advice {
        border-radius: 12px;
        padding: 1rem 1.2rem;
        line-height: 1.55;
        color: var(--text-color);
        background: rgba(251,192,45,.14);
        border-left: 4px solid #fbc02d;
    }
    .advice-ok {
        background: rgba(67,160,71,.14);
        border-left: 4px solid #43a047;
    }
    .advice b { display: block; margin-bottom: .35rem; }

    .notice {
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        background: rgba(96,125,139,.16);
        border-left: 4px solid #607d8b;
        color: var(--text-color);
        line-height: 1.55;
    }
    .notice b { display: block; margin-bottom: .4rem; font-size: 1.15rem; }

    .top-item {
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(128,128,128,.12);
        border: 1px solid rgba(128,128,128,.15);
        border-radius: 10px;
        padding: .6rem 1rem;
        margin-bottom: .5rem;
        color: var(--text-color);
        font-size: 1rem;
    }

    .src-item {
        background: rgba(128,128,128,.10);
        border: 1px solid rgba(128,128,128,.15);
        border-radius: 12px;
        padding: .8rem 1.1rem;
        margin-bottom: .6rem;
    }
    .src-item a { font-weight: 600; font-size: 1.02rem; text-decoration: none; }
    .src-item p { margin: .3rem 0 0; opacity: .75; font-size: .9rem; }

    .foot {
        text-align: center;
        color: var(--text-color);
        opacity: .6;
        margin-top: 1.5rem;
        font-size: .9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    "Apple___Apple_scab": ("Яблоня — Парша",
        "Удаляйте и сжигайте опавшие листья осенью. Обрабатывайте фунгицидами на основе меди или серы ранней весной и после цветения. Прореживайте крону для вентиляции."),
    "Apple___Black_rot": ("Яблоня — Чёрная гниль",
        "Вырезайте поражённые ветви и мумифицированные плоды, уничтожайте остатки. Применяйте фунгициды (каптан, манкоцеб) в период вегетации."),
    "Apple___Cedar_apple_rust": ("Яблоня — Ржавчина",
        "По возможности убирайте растущие рядом можжевельники. Опрыскивайте фунгицидами весной, высаживайте устойчивые сорта."),
    "Apple___healthy": ("Яблоня — Здоровое растение",
        "Растение здорово. Продолжайте регулярный полив, подкормку и профилактические осмотры, следите за вентиляцией кроны."),
    "Blueberry___healthy": ("Голубика — Здоровое растение",
        "Растение здорово. Поддерживайте кислую почву (pH 4.5–5.5), мульчируйте и обеспечивайте умеренный полив."),
    "Cherry___Powdery_mildew": ("Вишня — Мучнистая роса",
        "Удаляйте поражённые побеги, обрабатывайте серными препаратами или фунгицидами. Избегайте избытка азота и загущения."),
    "Cherry___healthy": ("Вишня — Здоровое растение",
        "Растение здорово. Своевременная обрезка и сбалансированные подкормки сохранят здоровье дерева."),
    "Corn___Cercospora_leaf_spot": ("Кукуруза — Серая пятнистость",
        "Соблюдайте севооборот, заделывайте остатки, высаживайте устойчивые гибриды. При сильном поражении применяйте фунгициды."),
    "Corn___Common_rust": ("Кукуруза — Обыкновенная ржавчина",
        "Используйте устойчивые гибриды. При раннем сильном поражении применяйте фунгициды, контролируйте сорняки и влажность."),
    "Corn___Northern_Leaf_Blight": ("Кукуруза — Северный гельминтоспориоз",
        "Севооборот и глубокая заделка остатков, устойчивые гибриды. Фунгициды при появлении вытянутых серо-зелёных пятен."),
    "Corn___healthy": ("Кукуруза — Здоровое растение",
        "Растение здорово. Поддерживайте оптимальную густоту посева и сбалансированное питание."),
    "Grape___Black_rot": ("Виноград — Чёрная гниль",
        "Удаляйте мумифицированные ягоды и поражённые листья, обеспечьте вентиляцию. Профилактические обработки фунгицидами в течение сезона."),
    "Grape___Esca_(Black_Measles)": ("Виноград — Эска",
        "Удаляйте и сжигайте поражённую древесину, дезинфицируйте инструмент при обрезке. Радикального лечения нет — важна профилактика."),
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": ("Виноград — Пятнистость листьев",
        "Удаляйте поражённые листья, улучшайте проветривание. Применяйте медьсодержащие фунгициды, избегайте полива по листьям."),
    "Grape___healthy": ("Виноград — Здоровое растение",
        "Растение здорово. Регулярная обрезка, подвязка и проветривание сохранят его здоровым."),
    "Orange___Haunglongbing_(Citrus_greening)": ("Апельсин — Позеленение цитрусовых",
        "Опасное неизлечимое заболевание. Удаляйте заражённые деревья, боритесь с переносчиком, используйте здоровый посадочный материал."),
    "Peach___Bacterial_spot": ("Персик — Бактериальная пятнистость",
        "Высаживайте устойчивые сорта, обрабатывайте препаратами меди в период покоя. Избегайте избыточного азота."),
    "Peach___healthy": ("Персик — Здоровое растение",
        "Растение здорово. Поддерживайте дренаж, обрезку и профилактику грибковых заболеваний весной."),
    "Pepper,_bell___Bacterial_spot": ("Перец сладкий — Бактериальная пятнистость",
        "Используйте здоровые семена и рассаду, соблюдайте севооборот. Обработки медьсодержащими препаратами, удаление поражённых растений."),
    "Pepper,_bell___healthy": ("Перец сладкий — Здоровое растение",
        "Растение здорово. Обеспечьте равномерный полив и подкормки калием и кальцием."),
    "Potato___Early_blight": ("Картофель — Альтернариоз",
        "Севооборот и уничтожение ботвы, крепкое питание. Фунгициды (манкоцеб, хлороталонил) при появлении концентрических пятен."),
    "Potato___Late_blight": ("Картофель — Фитофтороз",
        "Очень заразен. Удаляйте поражённые растения, проводите профилактические обработки, избегайте полива по листьям, окучивайте клубни."),
    "Potato___healthy": ("Картофель — Здоровое растение",
        "Растение здорово. Соблюдайте севооборот и окучивание для защиты клубней."),
    "Raspberry___healthy": ("Малина — Здоровое растение",
        "Растение здорово. Прореживайте побеги, мульчируйте и удаляйте старые ветви после плодоношения."),
    "Soybean___healthy": ("Соя — Здоровое растение",
        "Растение здорово. Соблюдайте севооборот и контролируйте влажность почвы."),
    "Squash___Powdery_mildew": ("Кабачок — Мучнистая роса",
        "Удаляйте поражённые листья, обрабатывайте раствором соды, серой или фунгицидами. Обеспечьте циркуляцию воздуха и полив под корень."),
    "Strawberry___Leaf_scorch": ("Клубника — Ожог листьев",
        "Удаляйте старые поражённые листья, прореживайте грядки, применяйте фунгициды. Избегайте полива дождеванием."),
    "Strawberry___healthy": ("Клубника — Здоровое растение",
        "Растение здорово. Мульчируйте, удаляйте лишние усы и обеспечьте проветривание."),
    "Tomato___Bacterial_spot": ("Томат — Бактериальная пятнистость",
        "Используйте здоровые семена, соблюдайте севооборот. Медьсодержащие препараты, удаление поражённых листьев, не работайте во влажную погоду."),
    "Tomato___Early_blight": ("Томат — Альтернариоз",
        "Удаляйте нижние поражённые листья, мульчируйте. Фунгициды (манкоцеб, хлороталонил), севооборот и проветривание."),
    "Tomato___Late_blight": ("Томат — Фитофтороз",
        "Очень опасен. Удаляйте поражённые растения, проводите профилактические обработки, поливайте под корень, не загущайте посадки."),
    "Tomato___Leaf_Mold": ("Томат — Бурая плесень",
        "Снижайте влажность в теплице, проветривайте, удаляйте поражённые листья. Применяйте фунгициды, используйте устойчивые сорта."),
    "Tomato___Septoria_leaf_spot": ("Томат — Септориоз",
        "Удаляйте нижние листья с пятнами, мульчируйте почву. Фунгициды и севооборот, избегайте полива по листьям."),
    "Tomato___Spider_mites": ("Томат — Паутинный клещ",
        "Повышайте влажность воздуха, опрыскивайте акарицидами или настоями, удаляйте сильно поражённые листья."),
    "Tomato___Target_Spot": ("Томат — Целевая пятнистость",
        "Удаляйте поражённые листья и остатки, обеспечьте проветривание и севооборот. Фунгициды при первых симптомах."),
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": ("Томат — Жёлтая курчавость листьев",
        "Вирус неизлечим. Боритесь с белокрылкой-переносчиком, удаляйте заражённые растения, используйте устойчивые гибриды и сетки."),
    "Tomato___Tomato_mosaic_virus": ("Томат — Вирус мозаики",
        "Вирус неизлечим. Удаляйте больные растения, дезинфицируйте инструмент и руки, используйте здоровые семена."),
    "Tomato___healthy": ("Томат — Здоровое растение",
        "Растение здорово. Поддерживайте полив под корень, подкормки и пасынкование."),
}


def ru_name(key):
    if key in DISEASE_INFO:
        return DISEASE_INFO[key][0]
    return key.replace("___", " — ").replace("_", " ")


def advice_for(key):
    if key in DISEASE_INFO:
        return DISEASE_INFO[key][1]
    return "Рекомендации для этого класса пока не добавлены."


def vegetation_fraction(pil_img):
    a = np.asarray(pil_img.resize((128, 128))).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    exg = 2 * g - r - b
    return float((exg > 25).mean())


def fallback_links(query):
    q = urllib.parse.quote(query)
    return [
        ("Поиск в Google", f"https://www.google.com/search?q={q}"),
        ("Поиск в Яндексе", f"https://yandex.ru/search/?text={q}"),
        ("Википедия", f"https://ru.wikipedia.org/w/index.php?search={q}"),
    ]


@st.cache_data(ttl=3600, show_spinner=False)
def web_advice(query, n=5):
    if DDGS is None:
        return None
    try:
        with DDGS() as ddgs:
            res = list(ddgs.text(query, region="ru-ru", max_results=n))
        out = [(r.get("title"), r.get("href"), r.get("body")) for r in res if r.get("href")]
        return out or None
    except Exception:
        return None


@st.cache_resource
def load_model():
    path = "trained_model.keras"
    if not os.path.exists(path):
        st.error("Файл модели 'trained_model.keras' не найден. Положите его в папку с приложением.")
        st.stop()
    return tf.keras.models.load_model(path)


model = load_model()

with st.sidebar:
    st.header("Настройки")
    conf_min = st.slider("Минимальная уверенность, %", 0, 100, 60)
    veg_min = st.slider("Минимум растительности, %", 0, 50, 12) / 100.0
    st.caption("Если на фото мало растительности или модель не уверена, диагноз не показывается автоматически.")

st.markdown('<div class="app-title">Диагностика болезней растений</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Загрузите фото листа или сделайте снимок — нейросеть определит состояние растения и подскажет, что делать.</div>',
    unsafe_allow_html=True,
)

source = st.radio("Источник изображения", ["Загрузить файл", "Сделать фото"], horizontal=True)

img_input = None
if source == "Загрузить файл":
    img_input = st.file_uploader(
        "Выберите изображение листа",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif"],
    )
else:
    img_input = st.camera_input("Наведите камеру на лист и сделайте снимок")

if img_input is None:
    st.info("Загрузите изображение или сделайте фото, чтобы начать диагностику.")
else:
    image = Image.open(img_input).convert("RGB")
    veg = vegetation_fraction(image)

    arr = np.expand_dims(np.array(image.resize((128, 128))), axis=0)
    with st.spinner("Анализирую изображение..."):
        preds = model.predict(arr, verbose=0)[0]

    idx = int(np.argmax(preds))
    confidence = float(np.max(preds) * 100)
    key = CLASS_NAMES[idx]
    name = ru_name(key)
    healthy = "healthy" in key.lower()

    is_plant = veg >= veg_min
    confident = confidence >= conf_min

    if is_plant and confident:
        proceed = True
    else:
        reasons = []
        if not is_plant:
            reasons.append(f"на фото почти нет растительности ({veg * 100:.0f}% зелёных пикселей)")
        if not confident:
            reasons.append(f"модель не уверена в результате ({confidence:.1f}%)")
        st.markdown(
            f'<div class="notice"><b>Похоже, на фото нет листа растения</b>'
            f'Причина: {", ".join(reasons)}. Сфотографируйте лист крупнее, при хорошем освещении и на однородном фоне.</div>',
            unsafe_allow_html=True,
        )
        col_img, _ = st.columns([1, 1.15])
        with col_img:
            st.image(image, use_container_width=True, caption="Загруженное изображение")
        proceed = st.checkbox("Всё равно показать результат диагностики")

    if proceed:
        left, right = st.columns([1, 1.15], gap="large")

        with left:
            with st.container(height=460, border=False):
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.image(image, use_container_width=True, caption="Исходное изображение")
                st.markdown('</div>', unsafe_allow_html=True)

        with right:
            with st.container(height=460, border=False):
                badge_cls = "badge-healthy" if healthy else "badge-disease"
                label = "Растение здорово" if healthy else "Обнаружено заболевание"
                fill_cls = "bar-fill-healthy" if healthy else "bar-fill-disease"
                advice_cls = "advice advice-ok" if healthy else "advice"
                advice_title = "Рекомендации по уходу" if healthy else "Рекомендации по лечению"

                st.markdown(
                    f'<div class="badge {badge_cls}"><span class="dot"></span>{name}</div>'
                    f'<div class="conf">{label} · уверенность {confidence:.2f}%</div>'
                    f'<div class="bar-track"><div class="{fill_cls}" style="width:{min(confidence,100):.1f}%"></div></div>'
                    f'<div class="{advice_cls}"><b>{advice_title}</b>{advice_for(key)}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("### Топ-3 наиболее вероятных варианта")
        top3 = np.argsort(preds)[-3:][::-1]
        medals = ["🥇", "🥈", "🥉"]
        for medal, i in zip(medals, top3):
            st.markdown(
                f'<div class="top-item"><span>{medal} {ru_name(CLASS_NAMES[i])}</span>'
                f'<b>{float(preds[i] * 100):.2f}%</b></div>',
                unsafe_allow_html=True,
            )

        st.markdown("### Распределение вероятностей")
        top5 = np.argsort(preds)[-5:][::-1]
        chart_df = pd.DataFrame(
            {"Вероятность, %": [float(preds[i] * 100) for i in top5]},
            index=[ru_name(CLASS_NAMES[i]) for i in top5],
        )
        st.bar_chart(chart_df, horizontal=True, color="#43a047")

        st.markdown("### Советы и материалы из интернета")
        query = name.split("—")[0].strip() + (" уход выращивание" if healthy else " болезнь лечение")
        results = web_advice(query)
        if results:
            for title, url, body in results:
                snippet = (body or "")[:180]
                st.markdown(
                    f'<div class="src-item"><a href="{url}" target="_blank">{title}</a>'
                    f'<p>{snippet}</p></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Живой поиск недоступен — вот готовые ссылки для самостоятельного поиска:")
            for title, url in fallback_links(query):
                st.markdown(f'<div class="src-item"><a href="{url}" target="_blank">{title}</a></div>',
                            unsafe_allow_html=True)

        st.caption(
            "Результат и материалы носят рекомендательный характер. При серьёзных поражениях обращайтесь к специалисту по защите растений."
        )

st.markdown('<div class="foot">Создано с помощью Streamlit и TensorFlow</div>', unsafe_allow_html=True)