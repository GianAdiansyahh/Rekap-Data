# import streamlit as st
# import tempfile
# import os
# from logic import proses_rekap

# st.title("📊 Rekap Data Penyakit")

# uploaded_files = st.file_uploader(
#     "Upload file Excel",
#     type=["xlsx"],
#     accept_multiple_files=True
# )

# if uploaded_files:
#     if st.button("Proses Data"):
#         with tempfile.TemporaryDirectory() as tmpdir:
#             input_dir = os.path.join(tmpdir, "data")
#             output_dir = os.path.join(tmpdir, "output")
#             os.makedirs(input_dir)
#             os.makedirs(output_dir)

#             for file in uploaded_files:
#                 with open(os.path.join(input_dir, file.name), "wb") as f:
#                     f.write(file.getbuffer())

#             hasil = proses_rekap(input_dir, output_dir)

#             with open(hasil, "rb") as f:
#                 st.download_button(
#                     "Download Hasil Excel",
#                     f,
#                     file_name="HASIL_REKAP.xlsx"
#                 )

import streamlit as st
import pandas as pd
from io import BytesIO
from logic import (
    baca_dan_bersihkan_file,
    hitung_ranking,
    cari_penyakit_umum
)

st.set_page_config(page_title="Rekap Penyakit", layout="wide")

st.title("📊 Rekap Data Penyakit")

uploaded_files = st.file_uploader(
    "Upload file Excels",
    type="xlsx",
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file berhasil diupload")

    all_data = []
    for file in uploaded_files:
        df = baca_dan_bersihkan_file(file)
        all_data.append(df)

    master_df = pd.concat(all_data, ignore_index=True)

    top_10_pusk = hitung_ranking(master_df, ['Puskesmas'])
    top_10_kec = hitung_ranking(master_df, ['Kecamatan'])
    top_5_common_pusk = cari_penyakit_umum(top_10_pusk, 'Puskesmas')
    top_5_common_kec = cari_penyakit_umum(top_10_kec, 'Kecamatan')

    st.subheader("📌 Preview Top 10 Kecamatan")
    st.dataframe(top_10_kec)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_10_kec.to_excel(writer, sheet_name="TOP_10_KECAMATAN", index=False)
        top_10_pusk.to_excel(writer, sheet_name="TOP_10_PUSKESMAS", index=False)
        top_5_common_kec.to_excel(writer, sheet_name="5_UMUM__KECAMATAN", index=False)
        top_5_common_pusk.to_excel(writer, sheet_name="5_UMUM_PUSKESMAS", index=False)
        master_df.to_excel(writer, sheet_name="DATA_MENTAH_FULL", index=False)

    st.download_button(
        label="⬇️ Download Laporan Excel",
        data=output.getvalue(),
        file_name="LAPORAN_FINAL_TERSTRUKTUR.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
