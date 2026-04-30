import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ChemMind AI - Pro", page_icon="🧪", layout="wide")

# --- ÖZEL STİL (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
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
# Streamlit Cloud'da "Advanced Settings > Secrets" kısmına GEMINI_API_KEY eklemeyi unutma!
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "BURAYA_GECICI_OLARAK_ANAHTARINI_YAZABILIRSIN" # Ama GitHub'da gizle!

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SIDEBAR: ÖĞRENCİ BİLGİLERİ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022607.png", width=80)
    st.title("🎓 Öğrenci Paneli")
    
    std_name = st.text_input("Adınız Soyadınız:")
    std_id = st.text_input("Öğrenci Numaranız:")
    exp_title = st.selectbox("Deney Konusu:", [
        "Reaksiyon Hızı", 
        "Asit-Baz Titrasyonu", 
        "Çözünürlük Dengesi", 
        "Elektroliz",
        "Diğer"
    ])
    
    st.divider()
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- SİSTEM TALİMATI (PROMPT MÜHENDİSLİĞİ) ---
sistem_promptu = f"""
Sen uzman bir Kimya Eğitimi profesörüsün. Öğrencinin adı {std_name}.
Görevin, öğrencinin '{exp_title}' konusu üzerine tasarladığı deneyi analiz etmek.
ANALİZ KRİTERLERİN:
1. Değişkenler: Bağımlı, bağımsız ve kontrol değişkenleri doğru mu?
2. Güvenlik: Kimyasal tehlikeler belirtilmiş mi?
3. Bilimsel Yöntem: Deney adımları mantıklı mı?

KURAL: Cevabı doğrudan verme! Hataları bulup öğrenciye "Neden böyle düşündün?" gibi yönlendirici sorular sor.
"""

# --- ANA EKRAN ---
st.title("🔬 ChemMind AI: İnteraktif Kimya Laboratuvarı")

# Sohbet geçmişini tutmak için session state
if "messages" not in st.session_state:
    st.session_state.messages = []

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
        with st.spinner("Hocanız analiz ediyor..."):
            time.sleep(5)
            response = model.generate_content(f"{sistem_promptu}\n\nÖğrenci Mesajı: {prompt}")
            full_response = response.text
            st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- VERİ DIŞA AKTARMA (TEZ İÇİN) ---
st.divider()
if st.session_state.messages:
    st.subheader("📊 Tez Verisi Hazırla")
    if st.button("Tüm Sohbeti Kaydet ve Rapor Oluştur"):
        # Verileri DataFrame'e çevir
        data = {
            "Zaman": [datetime.now().strftime("%Y-%m-%d %H:%M")],
            "Ogrenci": [std_name],
            "No": [std_id],
            "Konu": [exp_title],
            "Sohbet_Gecmisi": [str(st.session_state.messages)]
        }
        df = pd.DataFrame(data)
        
        # Excel/CSV indir
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Excel Verisini İndir (.csv)",
            data=csv,
            file_name=f"{std_id}_deney_analizi.csv",
            mime="text/csv"
        )
        st.success("Veriler tezin için hazırlandı! Bilgisayarına indirebilirsin.")
        st.markdown(f'<div class="teacher-box">{response.text}</div>', unsafe_allow_html=True)
    else:
        st.error("Lütfen bir deney tasarımı metni giriniz.")
