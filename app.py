# app.py
import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from predictor import TogelPredictor, get_pasaran_data

# ================== CONFIG ==================
st.set_page_config(
    page_title="🏆 Prediksi Malas v3.3",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #FF4B4B; text-align: center;}
    .stButton>button {width: 100%; height: 2.8em; font-size: 1rem;}
    .copy-btn {background-color: #FF4B4B; color: white;}
</style>
""", unsafe_allow_html=True)

st.title("🏆 PREDIKSI MALAS v3.3")
st.markdown("**Top 2D (CT5D + KE) + Top 3D/4D dengan Mistik & Index** — Banyak angka - Banyak peluang")

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
                st.error("❌ Data tidak cukup untuk analisa.")
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
                
                # ================== TOP 2D ==================
                with tab1:
                    top2d = predictor.generate_top_2d_filtered(60)
                    formatted_2d = "*".join(top2d[:55])
                    
                    st.write("**TOP 2D** (pemisah *)")
                    st.code(formatted_2d, language=None)
                    
                    col_copy1, _ = st.columns([1, 3])
                    with col_copy1:
                        if st.button("📋 Copy TOP 2D", key="copy2d"):
                            st.success("✅ TOP 2D sudah dicopy!")
                            st.code(formatted_2d, language=None)
                
                # ================== TOP 3D ==================
                with tab2:
                    top3d = predictor.generate_top_3d_filtered(15)
                    formatted_3d = " ".join(top3d)
                    
                    st.write("**TOP 3D**")
                    st.code(formatted_3d, language=None)
                    
                    if st.button("📋 Copy TOP 3D (bb lebih baik)", key="copy3d"):
                        st.success("✅ TOP 3D sudah dicopy!")
                        st.code(formatted_3d, language=None)
                
                # ================== TOP 4D ==================
                with tab3:
                    top4d = predictor.generate_top_4d_filtered(12)
                    formatted_4d = " ".join(top4d)
                    
                    st.write("**TOP 4D**")
                    st.code(formatted_4d, language=None)
                    
                    if st.button("📋 Copy TOP 4D (bb lebih baik)", key="copy4d"):
                        st.success("✅ TOP 4D sudah dicopy!")
                        st.code(formatted_4d, language=None)
                
                # ================== POSISI ==================
                with tab4:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.subheader("KOP")
                        kop_text = predictor.get_unique_8d(
                            predictor.get_top_by_position('KOP',8),
                            predictor.get_top_by_position('KOP',8,True)
                        )
                        st.code(kop_text, language=None)
                    with col_b:
                        st.subheader("KEPALA")
                        kep_text = predictor.get_unique_8d(
                            predictor.get_top_by_position('KEPALA',8),
                            predictor.get_top_by_position('KEPALA',8,True)
                        )
                        st.code(kep_text, language=None)
                    with col_c:
                        st.subheader("EKOR")
                        eko_text = predictor.get_unique_8d(
                            predictor.get_top_by_position('EKOR',8),
                            predictor.get_top_by_position('EKOR',8,True)
                        )
                        st.code(eko_text, language=None)
                
                # ================== HISTORY ==================
                with tab5:
                    st.subheader("📜 Akurasi 10 Putaran Terakhir")
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
   KOP     : {kop_text}
   KEPALA  : {kep_text}
   EKOR    : {eko_text}

🔥 TOP 2D
{formatted_2d}

🔥 TOP 3D
{formatted_3d}

🔥 TOP 4D
{formatted_4d}

Semoga Beruntung! 🍀
"""

                st.download_button(
                    label="💾 Download Semua Prediksi sebagai TXT",
                    data=content,
                    file_name=f"PREDIKSI_{market_name}_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")

st.caption("Khusus buat Pejuang 234D ❤️ | UPS & MJP!")
