import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
from docx import Document
import io
from supabase import create_client, Client

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
    </style>
    """, unsafe_allow_html=True)

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
    API_KEY = "BURAYA_GECICI_OLARAK_ANAHTARINI_YAZABILIRSIN"
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

# --- GİRİŞ VE KAYIT EKRANI (LOGIN SYSTEM) ---
if not st.session_state.logged_in:
    st.title("🧪 ChemMind AI Laboratuvarına Hoş Geldiniz")
    st.markdown("Lütfen laboratuvara girmek için öğrenci kimliğinizi doğrulayın.")
    
    tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Yeni Kayıt Ol"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Mevcut Hesaba Giriş")
            l_no = st.text_input("Öğrenci Numaranız:")
            l_pass = st.text_input("Şifreniz:", type="password")
            submitted = st.form_submit_button("Laboratuvara Gir", use_container_width=True)
            
            if submitted:
                # Supabase'den kullanıcıyı kontrol et
                res = supabase.table("kullanicilar").select("*").eq("ogrenci_no", l_no).eq("sifre", l_pass).execute()
                if len(res.data) > 0:
                    st.session_state.logged_in = True
                    st.session_state.user_info = res.data[0]
                    st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Öğrenci numarası veya şifre hatalı!")

    with tab2:
        with st.form("register_form"):
            st.subheader("Yeni Öğrenci Kaydı")
            r_no = st.text_input("Öğrenci Numaranız:")
            r_name = st.text_input("Adınız ve Soyadınız:")
            r_pass = st.text_input("Bir Şifre Belirleyin:", type="password")
            r_submitted = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            if r_submitted:
                if len(r_no) < 3 or len(r_name) < 3 or len(r_pass) < 3:
                    st.warning("Lütfen tüm alanları eksiksiz doldurun.")
                else:
                    # Numara daha önce kayıtlı mı kontrol et
                    check = supabase.table("kullanicilar").select("*").eq("ogrenci_no", r_no).execute()
                    if len(check.data) > 0:
                        st.error("Bu öğrenci numarası zaten sisteme kayıtlı!")
                    else:
                        # Yeni öğrenciyi kaydet
                        supabase.table("kullanicilar").insert({"ogrenci_no": r_no, "ad_soyad": r_name, "sifre": r_pass}).execute()
                        st.success("Kayıt başarılı! Şimdi 'Giriş Yap' sekmesinden sisteme girebilirsiniz.")
    
    st.stop() # Giriş yapılmadıysa uygulamanın geri kalanını çalıştırma

# --- ANA UYGULAMA (GİRİŞ YAPILDIYSA ÇALIŞIR) ---
ogrenci = st.session_state.user_info

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046269.png", width=150)
    st.title(f"🎓 Merhaba, {ogrenci['ad_soyad'].split()[0]}")
    st.caption(f"Öğrenci No: {ogrenci['ogrenci_no']}")
    st.divider()
    
    exp_title = st.selectbox("Konu Başlığı Seçin:", [
        "Atom ve Periyodik Sistem",
        "Kimyasal Bağlar ve Molekül Geometrisi",
        "Kimyasal Hesaplamalar",
        "Maddenin Halleri",
        "Sıvı Çözeltiler ve Çözünürlük",
        "Kimyasal Tepkimelerde Enerji",
        "Kimyasal Tepkimelerde Hız",
        "Kimyasal Tepkimelerde Denge",
        "Asitler-Bazlar-Tuzlar",
        "Elektrokimya"
    ])
    
    if st.button("✅ Seçimi Onayla ve Başla", use_container_width=True):
        st.session_state.current_subject = exp_title
        st.session_state.messages = [
            {"role": "assistant", "content": f"👋 Merhaba {ogrenci['ad_soyad']}! **{exp_title}** konusunu seçtiğini görüyorum. Harika bir seçim. Bu konuyla ilgili bir deney mi tasarlamak istersin, yoksa kafana takılan teorik bir kavramı mı tartışalım?"}
        ]
        st.rerun()
        
    st.divider()

    # GEÇMİŞ SOHBETLERİ VERİTABANINDAN ÇEKME
    with st.expander("📂 Geçmiş Sohbetlerim", expanded=False):
        past_chats_res = supabase.table("sohbetler").select("*").eq("ogrenci_no", ogrenci['ogrenci_no']).order('kayit_tarihi', desc=True).execute()
        past_chats = past_chats_res.data
        
        if len(past_chats) == 0:
            st.info("Henüz kaydedilmiş sohbetiniz yok.")
        else:
            for chat in past_chats:
                # Tarihi düzeltelim
                tarih_str = chat['kayit_tarihi'].split("T")[0]
                if st.button(f"🕒 {tarih_str} - {chat['konu']}", key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.messages = chat['mesajlar']
                    st.session_state.current_subject = chat['konu']
                    st.toast("Arşivdeki sohbet yüklendi!", icon="📂")
                    st.rerun()

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    with col2:
        if st.button("💾 Buluta Kaydet", use_container_width=True):
            if len(st.session_state.messages) > 0:
                # Sohbeti veritabanına kaydet!
                yeni_kayit = {
                    "ogrenci_no": ogrenci['ogrenci_no'],
                    "konu": st.session_state.current_subject,
                    "mesajlar": st.session_state.messages
                }
                supabase.table("sohbetler").insert(yeni_kayit).execute()
                st.toast("Sohbet başarıyla veritabanına kaydedildi!", icon="✅")
            else:
                st.warning("Kaydedilecek mesaj yok!")

    # --- WORD İNDİRME BUTONU ---
    if st.session_state.messages:
        doc = Document()
        doc.add_heading('ChemMind AI - Öğrenci Sohbet Raporu', 0)
        doc.add_paragraph(f"Öğrenci Adı: {ogrenci['ad_soyad']}")
        doc.add_paragraph(f"Öğrenci No: {ogrenci['ogrenci_no']}")
        doc.add_paragraph(f"Çalışılan Konu: {st.session_state.current_subject}")
        doc.add_paragraph(f"Rapor Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        doc.add_heading('Sohbet Geçmişi', level=1)
        for msg in st.session_state.messages:
            role_name = "Öğrenci" if msg["role"] == "user" else "ChemMind AI"
            p = doc.add_paragraph()
            p.add_run(f"{role_name}: ").bold = True
            p.add_run(msg["content"])
            
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        st.download_button(
            label="📄 Word Olarak İndir",
            data=buffer,
            file_name=f"{ogrenci['ad_soyad']}_{st.session_state.current_subject}_Raporu.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        
    st.divider()
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_info = None
        st.session_state.messages = []
        st.rerun()

# --- SİSTEM TALİMATI ---
sistem_promptu = f"""
Sen destekleyici, zeki ve deneyimli bir Kimya Öğretmenisin. Karşındaki öğrencinin adı {ogrenci['ad_soyad']}.
Şu an tartıştığınız konu: '{st.session_state.current_subject}'.
Öğrencinin öğrenmesine rehberlik et, cevapları doğrudan vermek yerine sorgulat.
"""

# --- SOHBET EKRANI ---
st.title("🔬 ChemMind AI: İnteraktif Laboratuvar")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Laboratuvar asistanına bir şey sor..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Asistanınız düşünüyor..."):
            time.sleep(1) 
            response = model.generate_content(f"{sistem_promptu}\n\nÖğrenci Mesajı: {prompt}")
            full_response = response.text
            st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
