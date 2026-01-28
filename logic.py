import pandas as pd
import os
import streamlit as st

# Mapping nama Puskesmas ke Kecamatan
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
    """
    Membaca file Excel.
    Returns: (dataframe, log_dict)
    log_dict = {'file': str, 'status': 'SUCCESS'|'WARNING'|'ERROR', 'message': str}
    """
    log = {'file': uploaded_file.name, 'status': 'SUCCESS', 'message': 'Berhasil diproses.'}
    
    try:
        # Ambil nama puskesmas dari nama file
        nama_pusk = os.path.splitext(uploaded_file.name)[0].upper().strip()
        kecamatan = MAPPING_KECAMATAN.get(nama_pusk, 'TIDAK TERDAFTAR')

        # OPTIMASI 1: Coba pakai engine 'calamine' (Rust) yang super cepat
        try:
            df = pd.read_excel(uploaded_file, header=1, engine='calamine')
        except Exception:
            # Fallback ke engine default (openpyxl) jika calamine gagal/belum install
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, header=1)

        # 1. Filter Baris Sampah (Total/Jumlah)
        mask_sampah = df['Jenis Penyakit'].astype(str).str.contains(
            'TOTAL|JUMLAH|SUB TOTAL', case=False, na=False
        )
        df = df[~mask_sampah]

        # 2. Sum Kolom D (Index 3) sampai AY (Index 50)
        data_angka = df.iloc[:, 3:51].apply(pd.to_numeric, errors='coerce').fillna(0)
        df['Total_Kasus'] = data_angka.sum(axis=1)

        # 3. Standardisasi Teks
        df['Jenis Penyakit'] = df['Jenis Penyakit'].astype(str).str.strip().str.upper()
        df['ICD X'] = df['ICD X'].astype(str).str.strip().str.upper()

        # 4. Ambil Kolom Penting Saja
        try:
            clean_df = df[['Jenis Penyakit', 'ICD X', 'Total_Kasus']].copy()
        except KeyError as e:
            log['status'] = 'ERROR'
            log['message'] = f"Kolom wajib tidak ditemukan: {str(e)}"
            return pd.DataFrame(), log

        # OPTIMASI 2: Gunakan Category untuk hemat memori
        clean_df['Puskesmas'] = pd.Series([nama_pusk] * len(clean_df)).astype('category')
        clean_df['Kecamatan'] = pd.Series([kecamatan] * len(clean_df)).astype('category')

        # Hanya ambil yang ada kasusnya
        clean_df = clean_df[clean_df['Total_Kasus'] > 0]
        
        if clean_df.empty:
            log['status'] = 'WARNING'
            log['message'] = 'File valid tapi tidak ada data kasus (>0).'

        return clean_df, log

    except Exception as e:
        # Error handling agar aplikasi tidak crash jika ada 1 file bermasalah
        log['status'] = 'ERROR'
        log['message'] = f"Gagal memproses: {str(e)}"
        return pd.DataFrame(), log

def hitung_ranking(df, group_cols, top_n=10):
    """Menghitung Top N penyakit berdasarkan grup (Kecamatan/Puskesmas)."""
    # Grouping unik (menggabungkan penyakit yang sama dalam grup tersebut)
    agg_cols = group_cols + ['Jenis Penyakit', 'ICD X']
    grouped = df.groupby(agg_cols)['Total_Kasus'].sum().reset_index()

    result = (
        grouped.sort_values(group_cols + ['Total_Kasus'])
        .groupby(group_cols, group_keys=False)
        .apply(lambda x: x.sort_values('Total_Kasus', ascending=False).head(top_n))
        .reset_index(drop=True)
    )
    
    # UPDATE: Index dimulai dari 1
    result.index += 1
    return result

def cari_penyakit_umum(df_ranking, group_col, top_n=5):
    """Mencari penyakit yang paling sering muncul di Top 10 berbagai wilayah."""
    total_groups = df_ranking[group_col].nunique()

    freq = df_ranking.groupby(['Jenis Penyakit', 'ICD X']).size().reset_index(name='Frekuensi')
    total = df_ranking.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index()

    summary = pd.merge(freq, total, on=['Jenis Penyakit', 'ICD X'])

    # Logic status sama persis, hanya disederhanakan pakai lambda untuk performa
    summary['Status'] = summary['Frekuensi'].apply(
        lambda x: "LOLOS (Ada di SEMUA)" if x == total_groups else f"HAMPIR (Absen di {total_groups - x} unit)"
    )

    result = summary.sort_values(['Frekuensi', 'Total_Kasus'], ascending=False).head(top_n).reset_index(drop=True)
    
    # UPDATE: Index dimulai dari 1
    result.index += 1
    return result