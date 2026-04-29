import streamlit as st
import google.generativeai as genai

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="ChemMind AI - Deney Asistanı", page_icon="🧪", layout="wide")

# --- ÖZEL TASARIM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #007bff;
        color: white;
        font-weight: bold;
    }
    .stTextArea>div>div>textarea { border-radius: 15px; }
    .teacher-box {
        background-color: #ffffff;
        padding: 20px;
        border-left: 5px solid #007bff;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- API AYARLARI ---
genai.configure(api_key="AIzaSyDwEqF1yzVghjR7tZynrmCUKwYjO2khSNo")
model = genai.GenerativeModel('gemini-2.5-flash')

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022607.png", width=100)
    st.title("Laboratuvar Rehberi")
    st.info("""
    **Nasıl Kullanılır?**
    1. Deney fikrini yaz.
    2. Değişkenlerini belirt.
    3. 'Analiz Et' butonuna bas.
    """)
    st.divider()
    st.warning("⚠️ Güvenlik İlkemiz: Önlük ve gözlük takmayı unutmayın!")

# --- ANA EKRAN ---
col1, col2 = st.columns([2, 1])

with col1:
    st.title("🧪 ChemMind AI")
    st.caption("Genel Kimya Deney Tasarımı ve Analiz Platformu")
    
    ogrenci_input = st.text_area(
        "Deney Tasarımını Buraya Detaylıca Yaz:",
        placeholder="Örn: Sıcaklığın reaksiyon hızına etkisini ölçmek için 3 farklı sıcaklıkta...",
        height=250
    )
    
    submit = st.button("Deneyimi Analiz Et 🚀")

with col2:
    st.write("### 📚 Kaynaklar & İpuçları")
    st.markdown("- **Bağımlı Değişken:** Ölçtüğün şey.")
    st.markdown("- **Bağımsız Değişken:** Değiştirdiğin şey.")
    st.markdown("- **Kontrol:** Sabit tuttukların.")

# --- ANALİZ SONUCU ---
if submit:
    if ogrenci_input:
        with st.status("Hocanız metni inceliyor...", expanded=True) as status:
            st.write("Kimyasal denklemler kontrol ediliyor...")
            
            sistem_mesaji = "Sen bir kimya öğretmenisin. Öğrenciye rehberlik et, hataları bul ve güvenliği hatılat."
            response = model.generate_content(f"{sistem_mesaji}\n\nÖğrenci: {ogrenci_input}")
            
            status.update(label="Analiz Tamamlandı!", state="complete", expanded=False)
        
        st.markdown('### 👨‍🏫 Hocanın Notu:')
        st.markdown(f'<div class="teacher-box">{response.text}</div>', unsafe_allow_html=True)
    else:
        st.error("Lütfen bir deney tasarımı metni giriniz.")