# app.py
import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from predictor import TogelPredictor, get_pasaran_data

# ================== CONFIG ==================
st.set_page_config(
    page_title="🏆 Final Predictor v3.3",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #FF4B4B; text-align: center;}
    .metric-card {background-color: #0E1117; padding: 15px; border-radius: 10px; border: 1px solid #FF4B4B;}
    .stButton>button {width: 100%; height: 3em; font-size: 1.1rem;}
</style>
""", unsafe_allow_html=True)

st.title("🏆 FINAL PREDICTOR v3.3")
st.markdown("**Top 2D (CT5D + KE) + Top 3D/4D dengan Mistik & Index** — Lebih Ketat & Akurat")

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("⚙️ Pengaturan")
    
    MARKET_NAMES = [
        "Bullseye", "California", "Carolina Day", "Carolina Evening", "Chinapools",
        "Florida Evening", "Florida Mid", "Hongkong Lotto", "Hongkong Pools",
        "Japan", "Kentucky Evening", "Kentucky Mid", "Magnum Cambodia",
        "New York Evening", "Oregon 10", "Oregon 13", "Sydney Lotto",
        "Sydney Pools", "Taiwan", "Toto Macau 00", "Toto Macau 13",
        "Toto Macau 16", "Toto Macau 19", "Toto Macau 22", "pcso", "singapore"
    ]
    
    market_name = st.selectbox("Pilih Pasaran", MARKET_NAMES, index=8)
    data_limit = st.slider("Jumlah Data Historis", 50, 200, 120, step=10)
    
    st.markdown("---")
    st.caption("💡 Semakin banyak data = semakin stabil prediksi")

# ================== MAIN BUTTON ==================
if st.button("🚀 MULAI PREDIKSI SEKARANG", type="primary", use_container_width=True):
    with st.spinner("Mengambil data Turso DB & menganalisa... Mohon tunggu"):
        try:
            data = asyncio.run(get_pasaran_data(market_name, data_limit))
            
            if len(data) < 20:
                st.error("❌ Data tidak cukup untuk analisa. Pilih data limit lebih tinggi.")
            else:
                predictor = TogelPredictor(data)
                
                # ================== METRICS ==================
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔧 CT 5D", predictor.get_ct_5d())
                with col2:
                    st.metric("🔧 CT 3D", predictor.get_ct_3d())
                with col3:
                    st.metric("📊 Confidence", f"{predictor.get_confidence_score()}%")
                with col4:
                    acc = predictor.calculate_accuracy(predictor.analyze_history(10))
                    st.metric("📈 Accuracy", f"{acc['overall']}%")
                
                # ================== BBFS ==================
                bbfs_list = predictor.generate_bbfs_8d()
                plus_one = predictor.generate_bbfs_plus_one(bbfs_list)['plus']
                
                st.subheader("📌 BBFS 8D + Plus One")
                st.success(f"**{''.join(bbfs_list)} + {plus_one}**")
                
                # ================== TABS ==================
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🔥 TOP 2D", "🔥 TOP 3D", "🔥 TOP 4D", 
                    "📍 Posisi Lengkap", "📜 History Analisis"
                ])
                
                with tab1:
                    top2d = predictor.generate_top_2d_filtered(60)
                    st.write("*".join(top2d[:55]))   # ← Diubah jadi * tanpa spasi
                
                with tab2:
                    top3d = predictor.generate_top_3d_filtered(15)
                    st.write("  ".join(top3d))
                
                with tab3:
                    top4d = predictor.generate_top_4d_filtered(12)
                    st.write("  ".join(top4d))
                
                with tab4:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.subheader("KOP")
                        st.code(predictor.get_unique_8d(
                            predictor.get_top_by_position('KOP',8),
                            predictor.get_top_by_position('KOP',8,True)
                        ), language=None)
                    with col_b:
                        st.subheader("KEPALA")
                        st.code(predictor.get_unique_8d(
                            predictor.get_top_by_position('KEPALA',8),
                            predictor.get_top_by_position('KEPALA',8,True)
                        ), language=None)
                    with col_c:
                        st.subheader("EKOR")
                        st.code(predictor.get_unique_8d(
                            predictor.get_top_by_position('EKOR',8),
                            predictor.get_top_by_position('EKOR',8,True)
                        ), language=None)
                
                with tab5:
                    st.subheader("📜 History Akurasi 10 Putaran Terakhir")
                    history = predictor.analyze_history(10)
                    if history:
                        df = pd.DataFrame(history)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("History belum tersedia")
                
                # ================== DOWNLOAD TXT ==================
                st.markdown("---")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                
                content = f"""🏆 FINAL PREDICTOR - {market_name}
🕒 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🔧 CT 5D     : {predictor.get_ct_5d()}
🔧 CT 3D     : {predictor.get_ct_3d()}
📌 BBFS      : {''.join(bbfs_list)} + {plus_one}
📊 Confidence: {predictor.get_confidence_score()}% | Accuracy: {acc['overall']}%

📍 POSISI
   KOP     : {predictor.get_unique_8d(predictor.get_top_by_position('KOP',8), predictor.get_top_by_position('KOP',8,True))}
   KEPALA  : {predictor.get_unique_8d(predictor.get_top_by_position('KEPALA',8), predictor.get_top_by_position('KEPALA',8,True))}
   EKOR    : {predictor.get_unique_8d(predictor.get_top_by_position('EKOR',8), predictor.get_top_by_position('EKOR',8,True))}

🔥 TOP 2D
{"*".join(top2d[:60])}

🔥 TOP 3D
{" ".join(top3d)}

🔥 TOP 4D
{" ".join(top4d)}

Semoga Beruntung! 🍀
"""

                st.download_button(
                    label="💾 Download Prediksi sebagai TXT",
                    data=content,
                    file_name=f"PREDIKSI_{market_name}_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")

st.caption("Made with ❤️ | Share link ini ke temanmu!")
