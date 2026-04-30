import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import time  # Kota hatasını önlemek için zaman modülü

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ChemMind AI - Pro", page_icon="🧪", layout="wide")

# --- ÖZEL STİL (CSS) ---
st.markdown("""
    <style>
    /* Temiz ve okunaklı varsayılan görünüm */
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

# --- API AYARLARI (GÜVENLİ YÖNTEM) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "BURAYA_GECICI_OLARAK_ANAHTARINI_YAZABILIRSIN"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SOHBET HAFIZASI (Session State) ---
# Temizle butonu düzgün çalışsın diye bunu sayfanın başına alıyoruz
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Merhaba! Ben ChemMind AI, senin kişisel laboratuvar asistanınım. Sol menüden bilgilerini doldurup deney konunu seçtiysen başlayabiliriz. Bugün aklında nasıl bir deney tasarımı var veya hangi konuda yardıma ihtiyacın var?"}
    ]

# --- SIDEBAR: ÖĞRENCİ BİLGİLERİ VE BUTONLAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022607.png", width=80)
    st.title("🎓 Öğrenci Paneli")
    
    std_name = st.text_input("Adınız Soyadınız:")
    std_id = st.text_input("Öğrenci Numaranız:")
    exp_title = st.selectbox("Konu Başlığı:", [
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
    
    st.divider()
    
    # YENİ: Seçimi Onaylama Butonu
    if st.button("✅ Seçimi Onayla ve Başla", use_container_width=True):
        # Sağ alttan çıkan şık bildirim
        st.toast(f"{exp_title} konusu aktif edildi!", icon="🎯")
        
        # Yapay zekanın ilk mesajını öğrenciye ve seçtiği konuya özel olarak ayarla
        isim_hitap = f" {std_name}" if std_name else ""
        st.session_state.messages = [
            {"role": "assistant", "content": f"👋 Merhaba{isim_hitap}! **{exp_title}** konusunu seçtiğini görüyorum. Harika bir seçim. Bu konuyla ilgili bir deney mi tasarlamak istersin, yoksa kafana takılan teorik bir kavramı mı tartışalım?"}
        ]
        st.rerun() # Ekranı yenile
        
    st.divider()
    
    # Temizle ve Kaydet Butonları (Yan yana)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Temizle"):
            st.session_state.messages = []
            st.rerun()

    with col2:
        if st.session_state.messages:
            data = {
                "Zaman": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Ogrenci": [std_name],
                "No": [std_id],
                "Konu": [exp_title],
                "Sohbet_Gecmisi": [str(st.session_state.messages)]
            }
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="💾 Kaydet",
                data=csv,
                file_name=f"{std_id}_sohbet_kaydi.csv",
                mime="text/csv"
            )

# --- SİSTEM TALİMATI (GENİŞLETİLMİŞ VE ÇOK YÖNLÜ ÖĞRETMEN) ---
sistem_promptu = f"""
Sen destekleyici, zeki ve deneyimli bir Kimya Öğretmenisin. Öğrencinin adı {std_name}.
İlgilendiğiniz genel konu: '{exp_title}'.

GÖREVİN VE TARZIN:
- ÖNCE ÖĞRENCİYİ ANLA: Öğrenci sana her zaman sıfırdan deney tasarlamak için gelmeyebilir. Bazen yazdığı bir deney raporunu (lab report) kontrol ettirmek, sonuç kısmını nasıl toparlayacağını sormak veya sadece teorik bir kimya sorusu sormak isteyebilir.
- ZORLAMA YAPMA: Öğrenci rapor yazımı, veri analizi veya teorik bilgi hakkında soru soruyorsa, konuyu zorla "Peki bunu deney tasarımında nasıl kullanacaksın?" noktasına GETİRME. Ne soruyorsa o bağlamda yardımcı ol.
- DOĞAL SOHBET: Tıpkı laboratuvarda veya masanda yan yanaymışsınız gibi doğal, samimi ve akıcı bir dil kullan. Robotik listeler veya sürekli soru soran bir tarz kullanma.
- YÖNLENDİRİCİ REHBERLİK: Eğer deney raporu yazıyorsa bilimsel raporlama dili hakkında ipuçları ver; eğer tasarım yapıyorsa yöntemini geliştir. Gerektiğinde net bilgiler vermekten çekinme ama yine de öğrencinin kendi kendine düşünmesini teşvik et.
"""

# --- ANA EKRAN ---
st.title("🔬 ChemMind AI: İnteraktif Kimya Laboratuvarı")

# Geçmiş mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sohbet girişi
if prompt := st.chat_input("Deney tasarımın hakkında bir şeyler yaz..."):
    # 1. Kullanıcı mesajını kaydet ve göster
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI yanıtını oluştur
    with st.chat_message("assistant"):
        with st.spinner("ChemMind Düşünüyor..."):
            # Kota hatasını önlemek için 5 saniye bekletiyoruz
            time.sleep(5) 
            response = model.generate_content(f"{sistem_promptu}\n\nÖğrenci Mesajı: {prompt}")
            full_response = response.text
            st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
