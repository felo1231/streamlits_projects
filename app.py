import streamlit as st
import os
import asyncio
import edge_tts
import tempfile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #42f719, #e73c7e, #23a6d5, #23d5ab);
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


# 1. إعداد الصلاحيات
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents.readonly'
]

# 2. الدوال المساعدة
def get_services():
    # نستخدم st.secrets لقراءة البيانات الحساسة
    creds_info = st.secrets["GOOGLE_CREDENTIALS"]
    
    # تحويل البيانات إلى كائن Credentials
    creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)
    return drive_service, docs_service

    
def upload_and_convert(drive_service, file_path):
    file_metadata = {
        'name': 'Converted_PDF_to_Doc',
        'mimeType': 'application/vnd.google-apps.document'
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def extract_text_from_doc(docs_service, document_id):
    document = docs_service.documents().get(documentId=document_id).execute()
    text = ""
    content = document.get('body').get('content')
    for item in content:
        if 'paragraph' in item:
            for element in item['paragraph']['elements']:
                if 'textRun' in element:
                    text += element['textRun']['content']
    return text

async def generate_audio(text, output_file):
    communicate = edge_tts.Communicate(text, "ar-EG-ShakirNeural")
    await communicate.save(output_file)

# 3. واجهة التطبيق
st.title("📚 قارئ الملزمة الذكي")
uploaded_file = st.file_uploader("ارفع ملف الـ PDF هنا:", type="pdf")

if uploaded_file is not None:
    if st.button("تحويل وقراءة"):
        try:
            with st.spinner('جاري الاتصال بجوجل والتحويل...'):
                # حفظ الملف مؤقتاً
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # الحصول على الخدمات
                drive_serv, docs_serv = get_services()
                
                # الرفع والتحويل
                doc_id = upload_and_convert(drive_serv, "temp.pdf")
                st.success("تم التحويل إلى Google Doc بنجاح!")
                
                # استخراج النص
                full_text = extract_text_from_doc(docs_serv, doc_id)
                st.write("تم استخراج النص بنجاح.")
                
                # تحويل لصوت
                with st.spinner("جاري تحويل النص إلى صوت..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                        asyncio.run(generate_audio(full_text, tmp_audio.name))
                        st.audio(tmp_audio.name)
                        st.success("جاهز للاستماع!")
                        
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
            st.write("تأكد من إعدادات Google Cloud Console ووجود ملف credentials.json.")