
# import pandas as pd
# import glob
# import os

# def proses_rekap(input_folder, output_folder):

#     mapping_kec = {
#         'PONCOL': 'SEMARANG TENGAH', 'MIROTO': 'SEMARANG TENGAH',
#         'BANDARHARJO': 'SEMARANG UTARA', 'BULU LOR': 'SEMARANG UTARA',
#         'HALMAHERA': 'SEMARANG TIMUR', 'KARANGDORO': 'SEMARANG TIMUR',
#         'BUGANGAN': 'SEMARANG TIMUR',
#         'LAMPER TENGAH': 'SEMARANG SELATAN', 'PANDANARAN': 'SEMARANG SELATAN',
#         'LEBDOSARI': 'SEMARANG BARAT', 'KROBOKAN': 'SEMARANG BARAT',
#         'MANYARAN': 'SEMARANG BARAT', 'NGEMPLAK SIMONGAN': 'SEMARANG BARAT',
#         'KARANGAYU': 'SEMARANG BARAT',
#         'GAYAMSARI': 'GAYAMSARI', 'CANDILAMA': 'CANDISARI', 'KAGOK': 'CANDISARI',
#         'PEGANDAN': 'GAJAHMUNGKUR', 'BANGETAYU': 'GENUK', 'GENUK': 'GENUK',
#         'TLOGOSARI KULON': 'PEDURUNGAN', 'TLOGOSARI WETAN': 'PEDURUNGAN',
#         'PLAMONGANSARI': 'PEDURUNGAN',
#         'ROWOSARI': 'TEMBALANG', 'KEDUNGMUNDU': 'TEMBALANG',
#         'BULUSAN': 'TEMBALANG',
#         'NGEREP': 'BANYUMANIK', 'PADANGSARI': 'BANYUMANIK',
#         'PUPAY': 'BANYUMANIK', 'SRONDOL': 'BANYUMANIK',
#         'SEKARAN': 'GUNUNGPATI', 'GUNUNGPATI': 'GUNUNGPATI',
#         'MIJEN': 'MIJEN', 'KARANGMALANG': 'MIJEN',
#         'PURWOYOSO': 'NGALIYAN', 'TAMBAKAJI': 'NGALIYAN',
#         'NGALIYAN': 'NGALIYAN',
#         'KARANGANYAR': 'TUGU', 'MANGKANG': 'TUGU'
#     }

#     files = glob.glob(os.path.join(input_folder, "*.xlsx"))
#     if not files:
#         raise ValueError("Tidak ada file Excel yang diproses")

#     list_top_10_pusk = []

#     for f in files:
#         nama_pusk = os.path.basename(f)\
#             .replace(".xlsx", "")\
#             .split("(")[0]\
#             .strip()\
#             .upper()

#         kecamatan = mapping_kec.get(nama_pusk, "TIDAK TERDAFTAR")

#         df = pd.read_excel(f, header=1)

#         df = df[~df["Jenis Penyakit"].astype(str).str.contains(
#             "TOTAL|JUMLAH|SUB TOTAL", case=False, na=False
#         )]

#         data_angka = df.iloc[:, 3:51].apply(pd.to_numeric, errors="coerce").fillna(0)
#         df["Total_Baris"] = data_angka.sum(axis=1)

#         df["Jenis Penyakit"] = df["Jenis Penyakit"].str.upper().str.strip()
#         df["ICD X"] = df["ICD X"].str.upper().str.strip()

#         top_pusk = df[["Jenis Penyakit", "ICD X", "Total_Baris"]]
#         top_pusk = top_pusk[top_pusk["Total_Baris"] > 0]
#         top_pusk = top_pusk.sort_values("Total_Baris", ascending=False).head(10)

#         top_pusk["Puskesmas"] = nama_pusk
#         top_pusk["Kecamatan"] = kecamatan

#         list_top_10_pusk.append(top_pusk)

#     pool_df = pd.concat(list_top_10_pusk, ignore_index=True)

#     agg_kec = pool_df.groupby(
#         ["Kecamatan", "Jenis Penyakit", "ICD X"]
#     )["Total_Baris"].sum().reset_index()

#     top_10_kec = agg_kec.sort_values(
#         ["Kecamatan", "Total_Baris"],
#         ascending=[True, False]
#     ).groupby("Kecamatan").head(10)

#     output_path = os.path.join(output_folder, "REKAP_FIX_AKURAT.xlsx")

#     with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
#         pool_df.to_excel(writer, sheet_name="TOP_10_PUSKESMAS", index=False)
#         top_10_kec.to_excel(writer, sheet_name="TOP_10_KECAMATAN", index=False)

#     return output_path

import pandas as pd
import os

MAPPING_KECAMATAN = {
    'PONCOL': 'SEMARANG TENGAH', 'MIROTO': 'SEMARANG TENGAH',
    'BANDARHARJO': 'SEMARANG UTARA', 'BULU LOR': 'SEMARANG UTARA',
    'HALMAHERA': 'SEMARANG TIMUR', 'KARANGDORO': 'SEMARANG TIMUR', 'BUGANGAN': 'SEMARANG TIMUR',
    'LAMPER TENGAH': 'SEMARANG SELATAN', 'PANDANARAN': 'SEMARANG SELATAN',
    'LEBDOSARI': 'SEMARANG BARAT', 'KROBOKAN': 'SEMARANG BARAT', 'MANYARAN': 'SEMARANG BARAT',
    'NGEMPLAK SIMONGAN': 'SEMARANG BARAT', 'KARANGAYU': 'SEMARANG BARAT',
    'GAYAMSARI': 'GAYAMSARI', 'CANDILAMA': 'CANDISARI', 'KAGOK': 'CANDISARI',
    'PEGANDAN': 'GAJAHMUNGKUR', 'BANGETAYU': 'GENUK', 'GENUK': 'GENUK',
    'TLOGOSARI KULON': 'PEDURUNGAN', 'TLOGOSARI WETAN': 'PEDURUNGAN', 'PLAMONGANSARI': 'PEDURUNGAN',
    'ROWOSARI': 'TEMBALANG', 'KEDUNGMUNDU': 'TEMBALANG', 'BULUSAN': 'TEMBALANG',
    'NGEREP': 'BANYUMANIK', 'PADANGSARI': 'BANYUMANIK', 'PUPAY': 'BANYUMANIK', 'SRONDOL': 'BANYUMANIK',
    'SEKARAN': 'GUNUNGPATI', 'GUNUNGPATI': 'GUNUNGPATI', 'MIJEN': 'MIJEN', 'KARANGMALANG': 'MIJEN',
    'PURWOYOSO': 'NGALIYAN', 'TAMBAKAJI': 'NGALIYAN', 'NGALIYAN': 'NGALIYAN',
    'KARANGANYAR': 'TUGU', 'MANGKANG': 'TUGU'
}

def baca_dan_bersihkan_file(uploaded_file):
    nama_pusk = os.path.splitext(uploaded_file.name)[0].upper().strip()
    kecamatan = MAPPING_KECAMATAN.get(nama_pusk, 'TIDAK TERDAFTAR')

    df = pd.read_excel(uploaded_file, header=1)

    mask_sampah = df['Jenis Penyakit'].astype(str).str.contains(
        'TOTAL|JUMLAH|SUB TOTAL', case=False, na=False
    )
    df = df[~mask_sampah]

    data_angka = df.iloc[:, 3:51].apply(pd.to_numeric, errors='coerce').fillna(0)
    df['Total_Kasus'] = data_angka.sum(axis=1)

    df['Jenis Penyakit'] = df['Jenis Penyakit'].astype(str).str.strip().str.upper()
    df['ICD X'] = df['ICD X'].astype(str).str.strip().str.upper()

    clean_df = df[['Jenis Penyakit', 'ICD X', 'Total_Kasus']].copy()
    clean_df['Puskesmas'] = nama_pusk
    clean_df['Kecamatan'] = kecamatan

    return clean_df[clean_df['Total_Kasus'] > 0]

def hitung_ranking(df, group_cols, top_n=10):
    agg_cols = group_cols + ['Jenis Penyakit', 'ICD X']
    grouped = df.groupby(agg_cols)['Total_Kasus'].sum().reset_index()

    return (
        grouped.sort_values(group_cols + ['Total_Kasus'])
        .groupby(group_cols, group_keys=False)
        .apply(lambda x: x.sort_values('Total_Kasus', ascending=False).head(top_n))
    )

def cari_penyakit_umum(df_ranking, group_col, top_n=5):
    total_groups = df_ranking[group_col].nunique()

    freq = df_ranking.groupby(['Jenis Penyakit', 'ICD X']).size().reset_index(name='Frekuensi')
    total = df_ranking.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index()

    summary = pd.merge(freq, total, on=['Jenis Penyakit', 'ICD X'])

    summary['Status'] = summary['Frekuensi'].apply(
        lambda x: "LOLOS (Ada di SEMUA)" if x == total_groups else f"HAMPIR (Absen di {total_groups - x} unit)"
    )

    return summary.sort_values(['Frekuensi', 'Total_Kasus'], ascending=False).head(top_n)
