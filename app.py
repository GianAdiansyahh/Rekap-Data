import streamlit as st
import tempfile
import os
from logic import proses_rekap

st.title("📊 Rekap Data Penyakit")

uploaded_files = st.file_uploader(
    "Upload file Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Proses Data"):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = os.path.join(tmpdir, "data")
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(input_dir)
            os.makedirs(output_dir)

            for file in uploaded_files:
                with open(os.path.join(input_dir, file.name), "wb") as f:
                    f.write(file.getbuffer())

            hasil = proses_rekap(input_dir, output_dir)

            with open(hasil, "rb") as f:
                st.download_button(
                    "Download Hasil Excel",
                    f,
                    file_name="HASIL_REKAP.xlsx"
                )
