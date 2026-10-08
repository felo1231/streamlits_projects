import streamlit as st
import os
import asyncio
import edge_tts
import tempfile
import re
from pypdf import PdfReader

# إعدادات واجهة التطبيق وتعديل الألوان إلى الأسود (CSS)
st.markdown("""
    <style>
    /* تغيير لون الخلفية المتدرجة */
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

    /* تعديل الصندوق الأبيض الرئيسي وتغيير لون النصوص بداخله للأسود */
    .main .block-container {
        background: rgba(255, 255, 255, 0.92);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* جعل جميع النصوص، العناوين، والفقرات باللون الأسود */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #000000 !important;
    }

    /* تعديل تصميم الأزرار لتظل واضحة */
    div.stButton > button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #ffffff !important; /* كتابة بيضاء داخل الزرار ليكون مقروءاً */
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        color: #38bdf8 !important;
    }
    </style>
""", unsafe_allow_html=True)

# دالة ذكية لتنظيف النص المقلوب وإصلاح التداخل بين العربي والإنجليزي
def clean_and_fix_text(text):
    if not text:
        return ""
    
    # إزالة المسافات الزائدة والسطور الفارغة العشوائية
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    
    # معالجة الكلمات الشائعة المكتوبة بنطق خاطئ في ملازم الكلاود
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
            
    # تنظيف وتصليح النص بعد الاستخراج مباشرة
    return clean_and_fix_text(text)

# دالة تحويل النص إلى صوت باستخدام نظام ملائم للغتين
async def generate_audio(text, output_file):
    # صوت "سلمى" الأفضل في دمج المصطلحات الإنجليزية وسط العربي
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
                    
                    # تحويل النص إلى صوت
                    with st.spinner("جاري توليد الصوت النقي (عربي + إنجليزي لغات)..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                            asyncio.run(generate_audio(full_text, tmp_audio.name))
                            st.audio(tmp_audio.name)
                            st.success("جاهز للاستماع الآن!")
                        
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
