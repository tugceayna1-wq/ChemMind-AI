import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import time
from docx import Document
import io
from supabase import create_client, Client
import extra_streamlit_components as stx

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ChemMind AI - Pro", page_icon="🧪", layout="wide")

# --- ÖZEL STİL (CSS) ---
st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ÇEREZ (COOKIE) YÖNETİCİSİ ---
@st.cache_resource
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

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

# --- OTOMATİK GİRİŞ (ÇEREZ KONTROLÜ) ---
# Eğer kullanıcı sayfayı yenilediyse ama çerezi duruyorsa onu otomatik içeri alıyoruz
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
            submitted = st.form_submit_button("Laboratuvara Gir", use_container_width=True)
            
            if submitted:
                res = supabase.table("kullanicilar").select("*").eq("ogrenci_no", l_no).eq("sifre", l_pass).execute()
                if len(res.data) > 0:
                    st.session_state.logged_in = True
                    st.session_state.user_info = res.data[0]
                    # Giriş başarılıysa öğrencinin bilgisini tarayıcıya 30 günlük kaydediyoruz
                    cookie_manager.set("chem_user", l_no, expires_at=datetime.now() + timedelta(days=30))
                    st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Hatalı numara veya şifre!")

    with tab2:
        with st.form("register_form"):
            r_no = st.text_input("Öğrenci Numaranız:")
            r_name = st.text_input("Adınız ve Soyadınız:")
            r_pass = st.text_input("Şifre Belirleyin:", type="password")
            r_submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            if r_submitted:
                check = supabase.table("kullanicilar").select("*").eq("ogrenci_no", r_no).execute()
                if len(check.data) > 0:
                    st.error("Bu numara zaten kayıtlı!")
                else:
                    supabase.table("kullanicilar").insert({"ogrenci_no": r_no, "ad_soyad": r_name, "sifre": r_pass}).execute()
                    st.success("Kayıt başarılı! 'Giriş Yap' sekmesinden girebilirsiniz.")
    
    st.stop()

# --- ANA UYGULAMA ---
ogrenci = st.session_state.user_info

with st.sidebar:
    st.title(f"🎓 Merhaba, {ogrenci['ad_soyad'].split()[0]}")
    st.divider()
    
    # KONU SEÇİMİ
    exp_title = st.selectbox("Konu Başlığı Seçin:", ["Atom ve Periyodik Sistem", "Kimyasal Bağlar", "Kimyasal Hesaplamalar", "Maddenin Halleri", "Sıvı Çözeltiler", "Tepkimelerde Enerji"])
    if st.button("✅ Konuyu Onayla", use_container_width=True):
        st.session_state.current_subject = exp_title
        st.session_state.messages = [{"role": "assistant", "content": f"👋 {ogrenci['ad_soyad']}, **{exp_title}** konusuna hoş geldin! Nasıl yardımcı olabilirim?"}]
        st.rerun()
        
    st.divider()

    # YENİ SOHBET VE KAYDET BUTONLARI
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Yeni Sohbet", use_container_width=True):
            st.session_state.messages = [{"role": "assistant", "content": f"👋 Yeni bir sohbete başladık. Konumuz: {st.session_state.current_subject}. Seni dinliyorum!"}]
            st.rerun()

    with col2:
        if st.button("💾 Sohbeti Kaydet", use_container_width=True):
            if len(st.session_state.messages) > 1:
                yeni_kayit = {"ogrenci_no": ogrenci['ogrenci_no'], "konu": st.session_state.current_subject, "mesajlar": st.session_state.messages}
                supabase.table("sohbetler").insert(yeni_kayit).execute()
                st.toast("Sohbet veritabanına kaydedildi!", icon="✅")
            else:
                st.warning("Kaydedilecek mesaj yok!")

    st.divider()

    # GEÇMİŞ SOHBETLER
    with st.expander("📂 Geçmiş Sohbetlerim", expanded=False):
        past_chats_res = supabase.table("sohbetler").select("*").eq("ogrenci_no", ogrenci['ogrenci_no']).order('kayit_tarihi', desc=True).execute()
        past_chats = past_chats_res.data
        if len(past_chats) == 0:
            st.info("Kayıtlı sohbet yok.")
        else:
            for chat in past_chats:
                tarih = chat['kayit_tarihi'].split("T")[0]
                if st.button(f"🕒 {tarih} - {chat['konu']}", key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.messages = chat['mesajlar']
                    st.session_state.current_subject = chat['konu']
                    st.rerun()

    st.divider()

    # WORD OLUŞTURMA
    if len(st.session_state.messages) > 1:
        doc = Document()
        doc.add_heading('ChemMind AI - Öğrenci Raporu', 0)
        doc.add_paragraph(f"Öğrenci: {ogrenci['ad_soyad']} ({ogrenci['ogrenci_no']})\nKonu: {st.session_state.current_subject}\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        for msg in st.session_state.messages:
            role_name = "Öğrenci" if msg["role"] == "user" else "ChemMind AI"
            p = doc.add_paragraph()
            p.add_run(f"{role_name}: ").bold = True
            p.add_run(msg["content"])
            
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        st.download_button("📄 Word Olarak İndir", data=buffer, file_name=f"{ogrenci['ad_soyad']}_Rapor.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

    st.divider()
    
    # ÇIKIŞ YAP (ÇEREZLERİ SİL)
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.messages = []
        cookie_manager.delete("chem_user")
        st.rerun()

# --- SOHBET EKRANI ---
sistem_promptu = f"Sen bir Kimya Öğretmenisin. Öğrenci: {ogrenci['ad_soyad']}. Konu: {st.session_state.current_subject}. Cevapları direkt verme, sorgulat."

st.title("🔬 ChemMind AI: Laboratuvar")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Mesajınızı yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Asistan düşünüyor..."):
            response = model.generate_content(f"{sistem_promptu}\n\nÖğrenci: {prompt}")
            st.markdown(response.text)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})
