import streamlit as st
import os
import asyncio
import edge_tts
import tempfile
import re
from pypdf import PdfReader

# إعدادات واجهة التطبيق وتعديل الألوان بدقة (CSS)
st.markdown("""
    <style>
    /* 1. خلفية التطبيق المتدرجة */
    .stApp {
        background: linear-gradient(-45deg, #19f775, #19f7b1, #19f7da, #19ecf7, #19cbf7, #19b1f7, #1993f7, #196ef7);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* 2. الصندوق الأبيض الرئيسي */
    .main .block-container {
        background: rgba(255, 255, 255, 0.92);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* 3. جعل عناوين التطبيق والنصوص المستخرجة فقط باللون الأسود دون التأثير على أزرار Streamlit */
    .main h1, .main h2, .main h3, .main p, .main .stWrite {
        color: #000000 !important;
    }
    
    /* 4. تعديل نصوص الـ Labels (مثل عنوان خانة الرفع) لتكون سوداء واضحة فوق الخلفية البيضاء */
    .main label p {
        color: #000000 !important;
        font-weight: 600;
    }

    /* 5. تصميم مخصص لزرار "قراءة الملف" ليصبح واضحاً جداً وبكتابة بيضاء سميكة */
    div.stButton > button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important; /* نص أبيض واضح جداً */
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        color: #38bdf8 !important; /* يتحول للأزرق الفاتح عند الوقوف عليه */
        box-shadow: 0 6px 16px rgba(0,0,0,0.25);
    }
    
    /* 6. إصلاح ألوان نصوص صندوق رفع الملفات ليعود واضحاً وقابلاً للقراءة */
    div[data-testid="stFileUploader"] section {
        color: #31333F !important;
    }
    div[data-testid="stFileUploader"] button {
        color: #31333F !important;
    }
    </style>
""", unsafe_allow_html=True)

# دالة ذكية لتنظيف النص المقلوب وإصلاح التداخل بين العربي والإنجليزي
def clean_and_fix_text(text):
    if not text:
        return ""
    
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    
    replacements = {
        "كمبيوتنغ": "Computing",
        "كلاود": "Cloud",
        "أوف": "of",
        "إيه": "A",
        "أم واحد": "M1",
        "بؤوجيكت": "Project"
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
        
    return text.strip()

# دالة استخراج النص من ملف الـ PDF مباشرة
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
            
    return clean_and_fix_text(text)

# دالة تحويل النص إلى صوت باستخدام نظام ملائم للغتين
async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text, "ar-EG-SalmaNeural")
    await communicate.save(output_file)

# واجهة التطبيق الرئيسية
st.title("📚 قارئ الملزمة الذكي المطور")
uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا:", type="pdf")

if uploaded_file is not None:
    if st.button("قراءة الملف بصوت نقي ومعالج"):
        try:
            with st.spinner('جاري قراءة الـ PDF واستخراج النص الذكي...'):
                full_text = extract_text_from_pdf(uploaded_file)
                
                if not full_text.strip():
                    st.warning("لم يتم العثور على نص مقروء في الملف.")
                else:
                    st.success("تم استخراج النص وتصحيحه بنجاح!")
                    
                    with st.expander("عرض النص بعد المعالجة والتصحيح"):
                        st.write(full_text)
                    
                    with st.spinner("جاري توليد الصوت النقي (عربي + إنجليزي لغات)..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                            asyncio.run(generate_audio(full_text, tmp_audio.name))
                            st.audio(tmp_audio.name)
                            st.success("جاهز للاستماع الآن!")
                        
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
