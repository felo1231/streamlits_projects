import streamlit as st
import os
import asyncio
import edge_tts
import tempfile
from pypdf import PdfReader

# إعدادات واجهة التطبيق والألوان (CSS)
st.markdown("""
    <style>
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

    .main .block-container {
        background: rgba(255, 255, 255, 0.92);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    .main-title {
        color: #0f172a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        font-size: 2.3rem;
        margin-bottom: 10px;
        text-align: center;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border-radius: 10px;
        padding: 12px 28px;
        font-weight: 700;
        font-size: 1rem;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
    }

    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.35);
        color: #38bdf8;
    }
    </style>
""", unsafe_allow_html=True)


# دالة استخراج النص من ملف الـ PDF مباشرة
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# دالة تحويل النص إلى صوت باستخدام صوت يدعم العربي والإنجليزي معاً بشكل ممتاز
async def generate_audio(text, output_file):
    # تم تغيير الصوت هنا إلى ar-EG-SalmaNeural لأنها تدعم الـ Multilingual (عربي وإنجليزي بطلاقة)
    communicate = edge_tts.Communicate(text, "ar-EG-SalmaNeural")
    await communicate.save(output_file)

# واجهة التطبيق الرئيسية
st.title("📚 قارئ الملزمة الذكي")
uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا:", type="pdf")

if uploaded_file is not None:
    if st.button("قراءة الملف صوتياً"):
        try:
            with st.spinner('جاري قراءة ملف الـ PDF واستخراج النص...'):
                full_text = extract_text_from_pdf(uploaded_file)
                
                if not full_text.strip():
                    st.warning("لم يتم العثور على نص مقروء في الملف. قد يكون الملف عبارة عن صور مصورة (Scanned).")
                else:
                    st.success("تم استخراج النص من الـ PDF بنجاح!")
                    
                    with st.expander("عرض النص المستخرج"):
                        st.write(full_text)
                    
                    # تحويل النص إلى صوت
                    with st.spinner("جاري تحويل النص إلى صوت مجسم (عربي/إنجليزي)..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                            asyncio.run(generate_audio(full_text, tmp_audio.name))
                            st.audio(tmp_audio.name)
                            st.success("جاهز للاستماع!")
                        
        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الملف: {e}")
