# import pandas as pd
# import glob
# import os

# def proses_rekap_valid():
#     input_folder = 'data'
#     output_folder = 'output'
    
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     mapping_kec = {
#         'PONCOL': 'SEMARANG TENGAH', 'MIROTO': 'SEMARANG TENGAH',
#         'BANDARHARJO': 'SEMARANG UTARA', 'BULU LOR': 'SEMARANG UTARA',
#         'HALMAHERA': 'SEMARANG TIMUR', 'KARANGDORO': 'SEMARANG TIMUR', 'BUGANGAN': 'SEMARANG TIMUR',
#         'LAMPER TENGAH': 'SEMARANG SELATAN', 'PANDANARAN': 'SEMARANG SELATAN',
#         'LEBDOSARI': 'SEMARANG BARAT', 'KROBOKAN': 'SEMARANG BARAT', 'MANYARAN': 'SEMARANG BARAT', 
#         'NGEMPLAK SIMONGAN': 'SEMARANG BARAT', 'KARANGAYU': 'SEMARANG BARAT',
#         'GAYAMSARI': 'GAYAMSARI', 'CANDILAMA': 'CANDISARI', 'KAGOK': 'CANDISARI',
#         'PEGANDAN': 'GAJAHMUNGKUR', 'BANGETAYU': 'GENUK', 'GENUK': 'GENUK',
#         'TLOGOSARI KULON': 'PEDURUNGAN', 'TLOGOSARI WETAN': 'PEDURUNGAN', 'PLAMONGANSARI': 'PEDURUNGAN',
#         'ROWOSARI': 'TEMBALANG', 'KEDUNGMUNDU': 'TEMBALANG', 'BULUSAN': 'TEMBALANG',
#         'NGEREP': 'BANYUMANIK', 'PADANGSARI': 'BANYUMANIK', 'PUPAY': 'BANYUMANIK', 'SRONDOL': 'BANYUMANIK',
#         'SEKARAN': 'GUNUNGPATI', 'GUNUNGPATI': 'GUNUNGPATI', 'MIJEN': 'MIJEN', 'KARANGMALANG': 'MIJEN',
#         'PURWOYOSO': 'NGALIYAN', 'TAMBAKAJI': 'NGALIYAN', 'NGALIYAN': 'NGALIYAN',
#         'KARANGANYAR': 'TUGU', 'MANGKANG': 'TUGU'
#     }

#     files = glob.glob(os.path.join(input_folder, "*.xlsx"))
#     list_top_10_pusk = []

#     print(f"[*] Memproses {len(files)} file puskesmas...")

#     for f in files:
#         nama_pusk = os.path.basename(f).replace('.xlsx', '').upper().strip()
#         kecamatan = mapping_kec.get(nama_pusk, 'TIDAK TERDAFTAR')
        
#         try:

#             df = pd.read_excel(f, header=1)
            
#             # --- Filter SUM ---
#             df = df[~df['Jenis Penyakit'].astype(str).str.contains('TOTAL|JUMLAH|SUB TOTAL', case=False, na=False)]
            
#             # --- SUM INDEX (Index 3 s/d 50) ---
#             data_angka = df.iloc[:, 3:51].apply(pd.to_numeric, errors='coerce').fillna(0)
#             df['Total_Baris'] = data_angka.sum(axis=1)
            
#             # Standardisasi Teks
#             df['Jenis Penyakit'] = df['Jenis Penyakit'].astype(str).str.strip().str.upper()
#             df['ICD X'] = df['ICD X'].astype(str).str.strip().str.upper()
            
#             # Top 10 Puskesmas
#             top_pusk = df[['Jenis Penyakit', 'ICD X', 'Total_Baris']].copy()
#             top_pusk = top_pusk[top_pusk['Total_Baris'] > 0]
#             top_pusk = top_pusk.sort_values(by='Total_Baris', ascending=False).head(10)
            
#             # Tambahkan Identitas
#             top_pusk['Puskesmas'] = nama_pusk
#             top_pusk['Kecamatan'] = kecamatan
            
#             list_top_10_pusk.append(top_pusk)
#             print(f"    [V] {nama_pusk} OK.")
            
#         except Exception as e:
#             print(f"    [X] Error di {nama_pusk}: {e}")

#     # Gabung 10 Top Puskesmas
#     pool_df = pd.concat(list_top_10_pusk, ignore_index=True)

#     # --- Recap Kecamatan ---
#     agg_kec = pool_df.groupby(['Kecamatan', 'Jenis Penyakit', 'ICD X'])['Total_Baris'].sum().reset_index()
    
#     # Rank 10 Top Kecamatan
#     top_10_kec = agg_kec.sort_values(['Kecamatan', 'Total_Baris'], ascending=[True, False]).groupby('Kecamatan').head(10)

#     # Export ke Excel
#     output_path = os.path.join(output_folder, 'REKAP_FIX_AKURAT.xlsx')
#     with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
#         top_10_kec.to_excel(writer, sheet_name='TOP_10_KECAMATAN', index=False)
#         pool_df.to_excel(writer, sheet_name='TOP_10_PUSKESMAS', index=False)

#     print("\n" + "="*50)
#     print(f"REKAP SELESAI! Hasilnya sudah dicek anti-double sum.")
#     print(f"File: {output_path}")
#     print("="*50)

# if __name__ == "__main__":
#     proses_rekap_valid()

import pandas as pd
import glob
import os

def proses_rekap(input_folder, output_folder):

    mapping_kec = {
        'PONCOL': 'SEMARANG TENGAH', 'MIROTO': 'SEMARANG TENGAH',
        'BANDARHARJO': 'SEMARANG UTARA', 'BULU LOR': 'SEMARANG UTARA',
        'HALMAHERA': 'SEMARANG TIMUR', 'KARANGDORO': 'SEMARANG TIMUR',
        'BUGANGAN': 'SEMARANG TIMUR',
        'LAMPER TENGAH': 'SEMARANG SELATAN', 'PANDANARAN': 'SEMARANG SELATAN',
        'LEBDOSARI': 'SEMARANG BARAT', 'KROBOKAN': 'SEMARANG BARAT',
        'MANYARAN': 'SEMARANG BARAT', 'NGEMPLAK SIMONGAN': 'SEMARANG BARAT',
        'KARANGAYU': 'SEMARANG BARAT',
        'GAYAMSARI': 'GAYAMSARI', 'CANDILAMA': 'CANDISARI', 'KAGOK': 'CANDISARI',
        'PEGANDAN': 'GAJAHMUNGKUR', 'BANGETAYU': 'GENUK', 'GENUK': 'GENUK',
        'TLOGOSARI KULON': 'PEDURUNGAN', 'TLOGOSARI WETAN': 'PEDURUNGAN',
        'PLAMONGANSARI': 'PEDURUNGAN',
        'ROWOSARI': 'TEMBALANG', 'KEDUNGMUNDU': 'TEMBALANG',
        'BULUSAN': 'TEMBALANG',
        'NGEREP': 'BANYUMANIK', 'PADANGSARI': 'BANYUMANIK',
        'PUPAY': 'BANYUMANIK', 'SRONDOL': 'BANYUMANIK',
        'SEKARAN': 'GUNUNGPATI', 'GUNUNGPATI': 'GUNUNGPATI',
        'MIJEN': 'MIJEN', 'KARANGMALANG': 'MIJEN',
        'PURWOYOSO': 'NGALIYAN', 'TAMBAKAJI': 'NGALIYAN',
        'NGALIYAN': 'NGALIYAN',
        'KARANGANYAR': 'TUGU', 'MANGKANG': 'TUGU'
    }

    files = glob.glob(os.path.join(input_folder, "*.xlsx"))
    if not files:
        raise ValueError("Tidak ada file Excel yang diproses")

    list_top_10_pusk = []

    for f in files:
        nama_pusk = os.path.basename(f)\
            .replace(".xlsx", "")\
            .split("(")[0]\
            .strip()\
            .upper()

        kecamatan = mapping_kec.get(nama_pusk, "TIDAK TERDAFTAR")

        df = pd.read_excel(f, header=1)

        df = df[~df["Jenis Penyakit"].astype(str).str.contains(
            "TOTAL|JUMLAH|SUB TOTAL", case=False, na=False
        )]

        data_angka = df.iloc[:, 3:51].apply(pd.to_numeric, errors="coerce").fillna(0)
        df["Total_Baris"] = data_angka.sum(axis=1)

        df["Jenis Penyakit"] = df["Jenis Penyakit"].str.upper().str.strip()
        df["ICD X"] = df["ICD X"].str.upper().str.strip()

        top_pusk = df[["Jenis Penyakit", "ICD X", "Total_Baris"]]
        top_pusk = top_pusk[top_pusk["Total_Baris"] > 0]
        top_pusk = top_pusk.sort_values("Total_Baris", ascending=False).head(10)

        top_pusk["Puskesmas"] = nama_pusk
        top_pusk["Kecamatan"] = kecamatan

        list_top_10_pusk.append(top_pusk)

    pool_df = pd.concat(list_top_10_pusk, ignore_index=True)

    agg_kec = pool_df.groupby(
        ["Kecamatan", "Jenis Penyakit", "ICD X"]
    )["Total_Baris"].sum().reset_index()

    top_10_kec = agg_kec.sort_values(
        ["Kecamatan", "Total_Baris"],
        ascending=[True, False]
    ).groupby("Kecamatan").head(10)

    output_path = os.path.join(output_folder, "REKAP_FIX_AKURAT.xlsx")

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pool_df.to_excel(writer, sheet_name="TOP_10_PUSKESMAS", index=False)
        top_10_kec.to_excel(writer, sheet_name="TOP_10_KECAMATAN", index=False)

    return output_path
