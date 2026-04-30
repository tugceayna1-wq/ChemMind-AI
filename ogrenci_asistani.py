import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time
from docx import Document  # Word dosyası oluşturmak için eklendi
import io                  # Dosyayı indirmeye hazırlamak için eklendi

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

# --- API AYARLARI ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "BURAYA_GECICI_OLARAK_ANAHTARINI_YAZABILIRSIN"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- SOHBET HAFIZASI VE GEÇMİŞ SOHBETLER ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "past_chats" not in st.session_state:
    st.session_state.past_chats = []

# --- SIDEBAR: ÖĞRENCİ BİLGİLERİ VE BUTONLAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046269.png", width=150)
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
    
    if st.button("✅ Seçimi Onayla ve Başla", use_container_width=True):
        st.toast(f"{exp_title} konusu aktif edildi!", icon="🎯")
        isim_hitap = f" {std_name}" if std_name else ""
        st.session_state.messages = [
            {"role": "assistant", "content": f"👋 Merhaba{isim_hitap}! **{exp_title}** konusunu seçtiğini görüyorum. Harika bir seçim. Bu konuyla ilgili bir deney mi tasarlamak istersin, yoksa kafana takılan teorik bir kavramı mı tartışalım?"}
        ]
        st.rerun()
        
    st.divider()

    with st.expander("📂 Geçmiş Sohbetlerim", expanded=False):
        if len(st.session_state.past_chats) == 0:
            st.info("Henüz arşivlenmiş sohbetin yok.")
        else:
            for idx, chat in enumerate(st.session_state.past_chats):
                if st.button(f"🕒 {chat['tarih']} - {chat['konu']}", key=f"past_{idx}", use_container_width=True):
                    st.session_state.messages = chat['mesajlar']
                    st.toast("Arşivdeki sohbet yüklendi!", icon="📂")
                    st.rerun()

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Temizle", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    with col2:
        if st.button("📁 Arşivle", use_container_width=True):
            if st.session_state.messages:
                st.session_state.past_chats.append({
                    "tarih": datetime.now().strftime("%H:%M"),
                    "konu": exp_title,
                    "mesajlar": st.session_state.messages.copy()
                })
                st.session_state.messages = []
                st.toast("Sohbet başarıyla arşive kaldırıldı!", icon="✅")
                st.rerun()

    # --- YENİ: WORD İNDİRME BUTONU ---
    if st.session_state.messages:
        # Word belgesini arka planda kodla oluşturuyoruz
        doc = Document()
        doc.add_heading('ChemMind AI - Öğrenci Sohbet Raporu', 0)
        doc.add_paragraph(f"Öğrenci Adı: {std_name}")
        doc.add_paragraph(f"Öğrenci No: {std_id}")
        doc.add_paragraph(f"Çalışılan Konu: {exp_title}")
        doc.add_paragraph(f"Tarih ve Saat: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        doc.add_heading('Sohbet Geçmişi', level=1)
        
        # Ekrandaki mesajları Word formatına dönüştür
        for msg in st.session_state.messages:
            role_name = "Öğrenci" if msg["role"] == "user" else "ChemMind AI"
            p = doc.add_paragraph()
            p.add_run(f"{role_name}: ").bold = True
            p.add_run(msg["content"])
            
        # Dosyayı indirmeye hazırla
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        st.download_button(
            label="📄 Word Olarak İndir",
            data=buffer,
            file_name=f"{std_name}_{exp_title}_Raporu.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

# --- SİSTEM TALİMATI ---
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
st.caption("")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Yaz gitsin, çözeriz (büyük ihtimalle)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("ChemMind Düşünüyor..."):
            time.sleep(3) 
            response = model.generate_content(f"{sistem_promptu}\n\nÖğrenci Mesajı: {prompt}")
            full_response = response.text
            st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
