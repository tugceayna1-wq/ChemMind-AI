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
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "BURAYA_GECICI_OLARAK_ANAHTARINI_YAZABILIRSIN"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SOHBET HAFIZASI (Session State) ---
# Temizle butonu düzgün çalışsın diye bunu sayfanın başına alıyoruz
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: ÖĞRENCİ BİLGİLERİ VE BUTONLAR ---
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
    
    # Butonları yan yana koymak için 2 sütun oluşturuyoruz
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Temizle"):
            st.session_state.messages = []
            st.rerun()

    with col2:
        # Sadece mesaj varsa Kaydet butonunu göster
        if st.session_state.messages:
            # Veriyi arka planda hazırla
            data = {
                "Zaman": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "Ogrenci": [std_name],
                "No": [std_id],
                "Konu": [exp_title],
                "Sohbet_Gecmisi": [str(st.session_state.messages)]
            }
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            
            # Doğrudan İndirme Butonu
            st.download_button(
                label="💾 Kaydet",
                data=csv,
                file_name=f"{std_id}_sohbet_kaydi.csv",
                mime="text/csv"
            )

# --- SİSTEM TALİMATI ---
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
st.title("🔬 ChemMind AI: İnteraktif Deney Tasarım Laboratuvarı")

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
