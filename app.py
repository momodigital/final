# app.py
import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from predictor import TogelPredictor, get_pasaran_data

st.set_page_config(page_title="🏆 Final Predictor v3.3", page_icon="🎯", layout="wide")

st.title("🏆 FINAL PREDICTOR v3.3")
st.markdown("**Top 2D (CT5D + KE) + Top 3D/4D dengan Mistik & Index**")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    MARKET_NAMES = ["Bullseye", "California", "Carolina Day", "Carolina Evening", "Chinapools",
                    "Florida Evening", "Florida Mid", "Hongkong Lotto", "Hongkong Pools",
                    "Japan", "Kentucky Evening", "Kentucky Mid", "Magnum Cambodia",
                    "New York Evening", "Oregon 10", "Oregon 13", "Sydney Lotto",
                    "Sydney Pools", "Taiwan", "Toto Macau 00", "Toto Macau 13",
                    "Toto Macau 16", "Toto Macau 19", "Toto Macau 22", "pcso", "singapore"]
    
    market_name = st.selectbox("Pilih Pasaran", MARKET_NAMES, index=8)
    data_limit = st.slider("Jumlah Data Historis", 50, 200, 120, step=10)

if st.button("🚀 MULAI PREDIKSI SEKARANG", type="primary", use_container_width=True):
    with st.spinner("Menganalisa..."):
        try:
            data = asyncio.run(get_pasaran_data(market_name, data_limit))
            
            if len(data) < 20:
                st.error("Data tidak cukup")
            else:
                predictor = TogelPredictor(data)
                
                # Fix seed lagi di app.py (extra safety)
                if predictor.results:
                    seed_value = sum(ord(c) for c in ''.join(predictor.results[:100])) % (10**9)
                    random.seed(seed_value)
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("CT 5D", predictor.get_ct_5d())
                with col2: st.metric("CT 3D", predictor.get_ct_3d())
                with col3: st.metric("Confidence", f"{predictor.get_confidence_score()}%")
                with col4: 
                    acc = predictor.calculate_accuracy(predictor.analyze_history(10))
                    st.metric("Accuracy", f"{acc['overall']}%")
                
                # BBFS
                bbfs_list = predictor.generate_bbfs_8d()
                plus_one = predictor.generate_bbfs_plus_one(bbfs_list)['plus']
                st.subheader("BBFS 8D + Plus")
                st.success(f"**{''.join(bbfs_list)} + {plus_one}**")
                
                # Tabs
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["TOP 2D", "TOP 3D", "TOP 4D", "Posisi", "History"])
                
                with tab1:
                    top2d = predictor.generate_top_2d_filtered(60)
                    formatted_2d = "*".join(top2d[:55])
                    st.code(formatted_2d, language=None)
                    if st.button("Copy TOP 2D"):
                        st.success("✅ Copied!")
                        st.code(formatted_2d, language=None)
                
                with tab2:
                    top3d = " ".join(predictor.generate_top_3d_filtered(15))
                    st.code(top3d, language=None)
                    if st.button("Copy TOP 3D"):
                        st.success("✅ Copied!")
                        st.code(top3d, language=None)
                
                with tab3:
                    top4d = " ".join(predictor.generate_top_4d_filtered(12))
                    st.code(top4d, language=None)
                    if st.button("Copy TOP 4D"):
                        st.success("✅ Copied!")
                        st.code(top4d, language=None)
                
                with tab4:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a: st.code(predictor.get_unique_8d(predictor.get_top_by_position('KOP',8), predictor.get_top_by_position('KOP',8,True)))
                    with col_b: st.code(predictor.get_unique_8d(predictor.get_top_by_position('KEPALA',8), predictor.get_top_by_position('KEPALA',8,True)))
                    with col_c: st.code(predictor.get_unique_8d(predictor.get_top_by_position('EKOR',8), predictor.get_top_by_position('EKOR',8,True)))
                
                with tab5:
                    history = predictor.analyze_history(10)
                    if history:
                        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
                
                # Download
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                content = f"""🏆 FINAL PREDICTOR - {market_name}\n..."""  # (sama seperti sebelumnya)
                st.download_button("Download TXT", content, f"PREDIKSI_{market_name}_{timestamp}.txt")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
