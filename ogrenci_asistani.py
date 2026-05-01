import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time
from docx import Document
import io
from supabase import create_client, Client
import extra_streamlit_components as stx
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ChemMind AI - Pro", page_icon="🧪", layout="wide")

# --- ÖZEL STİL (CSS) ---
st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .report-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border: 1px solid #dee2e6; 
        border-radius: 15px;
        border-left: 8px solid #28a745;
    }
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] a {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

# --- ÇEREZ (COOKIE) YÖNETİCİSİ ---
cookie_manager = stx.CookieManager()

# --- VERİTABANI (SUPABASE) BAĞLANTISI ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- API AYARLARI ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = ""
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- OTURUM (SESSION) HAFIZALARI ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_subject" not in st.session_state:
    st.session_state.current_subject = "Genel"

# --- MAİL GÖNDERME FONKSİYONU ---
def mail_gonder(doc_buffer, ogrenci_ad, konu):
    try:
        sender = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        receiver = st.secrets["HOCA_EMAIL"]
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"ChemMind AI: {ogrenci_ad} - {konu} Raporu"
        
        govde = f"Merhaba Hocam,\n\n{ogrenci_ad} adlı öğrencinin {konu} konusu üzerine gerçekleştirdiği ChemMind AI etkileşim raporu ektedir.\n\nİyi çalışmalar dileriz."
        msg.attach(MIMEText(govde, 'plain'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(doc_buffer.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{ogrenci_ad}_Raporu.docx"')
        msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True, "Rapor hocanıza başarıyla e-postalandı!"
    except Exception as e:
        return False, f"Hata: {str(e)}"

# --- OTOMATİK GİRİŞ ---
cerez_ogrenci_no = cookie_manager.get(cookie="chem_user")
if cerez_ogrenci_no and not st.session_state.logged_in:
    res = supabase.table("kullanicilar").select("*").eq("ogrenci_no", cerez_ogrenci_no).execute()
    if len(res.data) > 0:
        st.session_state.logged_in = True
        st.session_state.user_info = res.data[0]
        st.rerun()

# --- GİRİŞ VE KAYIT EKRANI ---
if not st.session_state.logged_in:
    st.title("🧪 ChemMind AI Laboratuvarına Hoş Geldiniz")
    tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Yeni Kayıt Ol"])
    with tab1:
        with st.form("login_form"):
            l_no = st.text_input("Öğrenci Numaranız:")
            l_pass = st.text_input("Şifreniz:", type="password")
            if st.form_submit_button("Laboratuvara Gir", use_container_width=True):
                res = supabase.table("kullanicilar").select("*").eq("ogrenci_no", l_no).eq("sifre", l_pass).execute()
                if len(res.data) > 0:
                    st.session_state.logged_in = True
                    st.session_state.user_info = res.data[0]
                    cookie_manager.set("chem_user", l_no, expires_at=datetime.now() + timedelta(days=30))
                    st.success("Giriş başarılı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Hatalı numara veya şifre!")
    with tab2:
        with st.form("register_form"):
            r_no = st.text_input("Öğrenci No:")
            r_name = st.text_input("Ad Soyad:")
            r_pass = st.text_input("Şifre:", type="password")
            if st.form_submit_button("Kayıt Ol", use_container_width=True):
                supabase.table("kullanicilar").insert({"ogrenci_no": r_no, "ad_soyad": r_name, "sifre": r_pass}).execute()
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
    st.stop()

# --- ANA UYGULAMA ---
ogrenci = st.session_state.user_info
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046269.png", width=120)
    st.title(f"🎓 Merhaba, {ogrenci['ad_soyad'].split()[0]}")
    st.divider()
    exp_title = st.selectbox("Konu Başlığı Seçin:", ["Atom ve Periyodik Sistem", "Kimyasal Bağlar", "Kimyasal Hesaplamalar", "Maddenin Halleri", "Sıvı Çözeltiler", "Tepkimelerde Enerji"])
    if st.button("✅ Seçimi Onayla", use_container_width=True):
        st.session_state.current_subject = exp_title
        st.session_state.messages = [{"role": "assistant", "content": f"👋 **{exp_title}** konusuna hoş geldin! Seni dinliyorum."}]
        st.rerun()
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Yeni Sohbet", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": f"👋 Yeni sayfa açıldı. Konu: {st.session_state.current_subject}"}]
            st.rerun()
    with c2:
        if st.button("💾 Sohbeti Kaydet", use_container_width=True):
            if len(st.session_state.messages) > 1:
                supabase.table("sohbetler").insert({"ogrenci_no": ogrenci['ogrenci_no'], "konu": st.session_state.current_subject, "mesajlar": st.session_state.messages}).execute()
                st.toast("Veritabanına kaydedildi!", icon="✅")
    
    st.divider()
    # WORD VE MAİL BUTONLARI
    if len(st.session_state.messages) > 1:
        doc = Document()
        doc.add_heading('ChemMind AI Raporu', 0)
        doc.add_paragraph(f"Öğrenci: {ogrenci['ad_soyad']}\nKonu: {st.session_state.current_subject}")
        for msg in st.session_state.messages:
            p = doc.add_paragraph()
            p.add_run(f"{'Öğrenci' if msg['role']=='user' else 'Asistan'}: ").bold = True
            p.add_run(msg['content'])
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        st.download_button("📄 Word İndir", data=buffer, file_name="Rapor.docx", use_container_width=True)
        if st.button("📧 Hocama Gönder", use_container_width=True):
            buffer.seek(0)
            ok, msg = mail_gonder(buffer, ogrenci['ad_soyad'], st.session_state.current_subject)
            if ok: st.toast(msg, icon="🚀")
            else: st.error(msg)

    st.divider()
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        cookie_manager.delete("chem_user")
        st.rerun()

# --- SOHBET ---
st.title("🔬 ChemMind AI: Laboratuvar")
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if prompt := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyorum..."):
            response = model.generate_content(f"Sen Kimya Öğretmenisin. Konu: {st.session_state.current_subject}. Öğrenci: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
