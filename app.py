import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
from logic import (
    baca_dan_bersihkan_file,
    hitung_ranking,
    cari_penyakit_umum
)

# --- 0. State Management ---
if 'upload_key' not in st.session_state:
    st.session_state.upload_key = 0
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False

def reset_app():
    """Fungsi untuk mereset aplikasi dan uploader"""
    st.session_state.upload_key += 1
    st.session_state.data_processed = False
    st.cache_data.clear()

# --- 1. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Rekap Data Kesehatan",
    page_icon="🏥",
    layout="wide"
)

# --- 2. Custom CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    h1 { font-weight: 700; color: #2C3E50; font-size: 2.5rem; margin-bottom: 0rem; }
    h3 { font-weight: 600; color: #34495E; margin-top: 1rem; }
    
    /* Metrics */
    div[data-testid="stMetric"] {
        background-color: #F0F2F6;
        border: 1px solid #E0E0E0;
        padding: 15px; border-radius: 10px; color: #31333F;
    }
    div[data-testid="stMetric"] label { color: #555 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #000 !important; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #2C3E50; }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] p { color: #ECF0F1 !important; }
    
    /* Inputs in Sidebar */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="input"] {
        background-color: #34495E !important;
        color: white !important;
        border-color: #5D6D7E !important;
    }
    section[data-testid="stSidebar"] input { color: white !important; }
    section[data-testid="stSidebar"] div[data-baseweb="tag"] { background-color: #1ABC9C; }
    
    div.stButton > button[kind="primary"] { width: 100%; border-radius: 8px; font-weight: 600; }
    div.stButton > button[kind="secondary"] { width: 100%; border-radius: 8px; border: 1px solid #E74C3C; color: #E74C3C; }
    
    .block-container { padding-top: 2rem; }
    
    .ready-box {
        padding: 20px;
        background-color: #e8f8f5;
        border: 1px solid #1abc9c;
        border-radius: 10px;
        color: #16a085;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Style untuk instruksi di sidebar */
    .sidebar-info {
        background-color: #34495E;
        padding: 15px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-bottom: 15px;
        border-left: 4px solid #1ABC9C;
    }
    
    /* Footer Style */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #F8F9FA;
        color: #7F8C8D;
        text-align: center;
        padding: 10px 0;
        font-size: 0.85rem;
        border-top: 1px solid #E9ECEF;
        z-index: 100;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI STYLING ZIGZAG ---
def style_zigzag_groups(df, group_col):
    try:
        if group_col not in df.columns: return df
        unique_groups = df[group_col].unique()
        styles = ['background-color: #1A1A1A; color: white;', 'background-color: #333333; color: white;']
        group_map = {group: styles[i % 2] for i, group in enumerate(unique_groups)}
        def apply_style(row):
            return [group_map.get(row.get(group_col), '')] * len(row)
        return df.style.apply(apply_style, axis=1)
    except: return df

# --- FUNGSI PROSES DATA PER FILE (CACHED) ---
@st.cache_data(show_spinner=False)
def process_single_file(file):
    file.seek(0)
    return baca_dan_bersihkan_file(file)

# --- 3. Sidebar (Upload & Form) ---
with st.sidebar:
    st.header("📂 1. Input Data")
    
    # Keterangan Ketentuan File (Dikembalikan)
    st.markdown("""
    <div class="sidebar-info">
        <b>Ketentuan File Excel:</b><br>
        1. Format wajib <b>.xlsx</b><br>
        2. Header data harus di <b>Baris ke-2</b> (Index 1)<br>
        3. Data Penyakit ada di kolom <b>D s/d AY</b><br>
        4. Nama file mengandung nama <b>Puskesmas</b>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload Excel:", type="xlsx", accept_multiple_files=True,
        label_visibility="collapsed", key=f"uploader_{st.session_state.upload_key}"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} File Terbaca")
    else:
        st.caption("Silakan upload file untuk melanjutkan.")

# --- 4. Main Content ---
st.title("🏥 Rekap Data Penyakit")
st.markdown("Dashboard rekapitulasi data penyakit per kecamatan dan puskesmas.")
st.divider()

if not uploaded_files:
    # Tampilan Awal Kosong
    st.container().markdown(
        """
        <div style="text-align: center; padding: 50px; color: #7f8c8d;">
            <h3>👋 Selamat Datang!</h3>
            <p>Silakan upload file Excel laporan puskesmas melalui panel di sebelah kiri.</p>
        </div>
        """, unsafe_allow_html=True
    )
    # Reset status jika file dihapus manual
    st.session_state.data_processed = False

else:
    # --- LOAD DATA AWAL (Hanya untuk keperluan Filter, belum dihitung ranking) ---
    with st.spinner('Membaca struktur data...'):
        all_data = []
        for file in uploaded_files:
            df = process_single_file(file)
            all_data.append(df)
        
        if all_data:
            master_df = pd.concat(all_data, ignore_index=True)
        else:
            master_df = pd.DataFrame()

    if not master_df.empty:
        # Siapkan opsi filter dari data yang sudah di-load
        master_df['Label_Filter'] = master_df['ICD X'].astype(str) + " - " + master_df['Jenis Penyakit'].astype(str)
        master_df['Alpha_Filter'] = master_df['ICD X'].astype(str).str[0].str.upper()
        
        unique_diseases = sorted(master_df['Label_Filter'].unique())
        unique_alpha = sorted(master_df['Alpha_Filter'].unique())

        # --- SIDEBAR: FORM PENGATURAN (Muncul setelah upload) ---
        with st.sidebar:
            st.markdown("---")
            # Gunakan Form agar tidak auto-run saat ubah setting
            with st.form(key='settings_form'):
                st.header("⚙️ 2. Pengaturan & Filter")
                
                # A. Pengaturan Ranking
                st.subheader("Ranking (Top N)")
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    top_n_kec_val = st.number_input("Kecamatan", 1, 25, 10)
                    top_n_common_val = st.number_input("Analisis Umum", 1, 25, 5)
                with col_n2:
                    top_n_pusk_val = st.number_input("Puskesmas", 1, 25, 10)
                
                st.markdown("---")
                
                # B. Filter Data
                st.subheader("Filter Data")
                tab_include, tab_exclude = st.tabs(["✅ Include", "❌ Exclude"])
                
                with tab_include:
                    st.caption("HANYA tampilkan:")
                    include_alpha = st.multiselect("Huruf Awal:", unique_alpha, key='inc_a')
                    include_list = st.multiselect("Penyakit:", unique_diseases, key='inc_l')
                    
                with tab_exclude:
                    st.caption("SEMBUNYIKAN data:")
                    exclude_alpha = st.multiselect("Huruf Awal:", unique_alpha, key='exc_a')
                    exclude_list = st.multiselect("Penyakit:", unique_diseases, key='exc_l')
                
                st.markdown("---")
                
                # TOMBOL EKSEKUSI
                submitted = st.form_submit_button("MULAI REKAPITULASI", type="primary")
                
                if submitted:
                    st.session_state.data_processed = True

    # --- TAMPILAN UTAMA (LOGIC SPLIT) ---
    
    # KONDISI 1: File sudah upload, tapi tombol belum ditekan
    if not st.session_state.data_processed:
        st.markdown(
            f"""
            <div class="ready-box">
                <h3>✅ {len(uploaded_files)} File Berhasil Dimuat</h3>
                <p>Data siap diproses. Silakan atur <b>Ranking</b> dan <b>Filter</b> di sidebar kiri,</p>
                <p>lalu klik tombol <b>"MULAI REKAPITULASI"</b> untuk melihat hasil.</p>
            </div>
            """, unsafe_allow_html=True
        )
        
        with st.expander("Intip Data Mentah (Preview 5 Baris Awal)"):
            st.dataframe(master_df.head(), use_container_width=True)

    # KONDISI 2: Tombol sudah ditekan -> PROSES & TAMPILKAN HASIL
    else:
        # 1. Terapkan Filter
        filtered_df = master_df.copy()
        
        # Include Logic
        mask_inc = pd.Series([False]*len(filtered_df), index=filtered_df.index)
        has_inc = False
        if include_alpha:
            mask_inc |= filtered_df['Alpha_Filter'].isin(include_alpha)
            has_inc = True
        if include_list:
            mask_inc |= filtered_df['Label_Filter'].isin(include_list)
            has_inc = True
        if has_inc:
            filtered_df = filtered_df[mask_inc]

        # Exclude Logic
        if exclude_alpha:
            filtered_df = filtered_df[~filtered_df['Alpha_Filter'].isin(exclude_alpha)]
        if exclude_list:
            filtered_df = filtered_df[~filtered_df['Label_Filter'].isin(exclude_list)]

        if filtered_df.empty:
            st.error("⚠️ Hasil filter kosong! Silakan atur ulang filter di sidebar dan klik 'Mulai Rekapitulasi' lagi.")
        else:
            # 2. Hitung Ranking (Baru dihitung di sini)
            top_n_kec = hitung_ranking(filtered_df, ['Kecamatan'], top_n=top_n_kec_val)
            top_n_pusk = hitung_ranking(filtered_df, ['Puskesmas'], top_n=top_n_pusk_val)
            top_common_pusk = cari_penyakit_umum(top_n_pusk, 'Puskesmas', top_n=top_n_common_val)
            top_common_kec = cari_penyakit_umum(top_n_kec, 'Kecamatan', top_n=top_n_common_val)

            # 3. Tampilkan Dashboard
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Total File", f"{len(uploaded_files)}")
            with col2: st.metric("Unit Puskesmas", f"{filtered_df['Puskesmas'].nunique()}")
            with col3: st.metric("Total Kasus", f"{filtered_df['Total_Kasus'].sum():,}")

            st.markdown("---")
            
            # Status Filter Info
            f_status = "Aktif" if (has_inc or exclude_alpha or exclude_list) else "Non-Aktif"
            st.info(f"ℹ️ **Filter:** {f_status} | **Ranking:** Kec({top_n_kec_val}), Pusk({top_n_pusk_val}), Umum({top_n_common_val})")

            # Tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                f"🏢 Top {top_n_kec_val} Kecamatan", 
                f"🏥 Top {top_n_pusk_val} Puskesmas", 
                f"🦠 Top {top_n_common_val} Umum",
                "📂 Data Mentah"
            ])

            with tab1:
                st.subheader(f"Top {top_n_kec_val} Penyakit per Kecamatan")
                st.dataframe(style_zigzag_groups(top_n_kec, 'Kecamatan'), use_container_width=True, height=500)

            with tab2:
                st.subheader(f"Top {top_n_pusk_val} Penyakit per Puskesmas")
                st.dataframe(style_zigzag_groups(top_n_pusk, 'Puskesmas'), use_container_width=True, height=500)

            with tab3:
                st.subheader("Analisis Dominasi Penyakit")
                c1, c2 = st.columns(2)
                with c1: st.markdown("**Persebaran di Kecamatan**"); st.dataframe(top_common_kec, use_container_width=True)
                with c2: st.markdown("**Persebaran di Puskesmas**"); st.dataframe(top_common_pusk, use_container_width=True)

            with tab4:
                st.subheader("Data Terfilter")
                st.dataframe(filtered_df.drop(columns=['Label_Filter', 'Alpha_Filter']), use_container_width=True)

            # 4. Download Section
            st.markdown("---")
            st.subheader("📥 Download Hasil")
            
            raw_opts = {
                "Data Mentah": filtered_df.drop(columns=['Label_Filter', 'Alpha_Filter']),
                f"Top {top_n_kec_val} Kecamatan": top_n_kec,
                f"Top {top_n_pusk_val} Puskesmas": top_n_pusk,
                "Analisis Umum": top_common_kec
            }
            
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                sel_data = st.multiselect("Pilih Data:", ["Semua Data"] + list(raw_opts.keys()), default=["Semua Data"])
            with c_d2:
                fmt = st.radio("Format:", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
            
            if sel_data:
                final_data = raw_opts if "Semua Data" in sel_data else {k:v for k,v in raw_opts.items() if k in sel_data}
                
                if fmt == "Excel":
                    buf = BytesIO()
                    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                        for k, v in final_data.items():
                            sheet = k[:30].replace(" ", "_").upper()
                            clean_sheet = "".join(c for c in sheet if c.isalnum() or c=="_")
                            v.to_excel(writer, sheet_name=clean_sheet, index=False)
                    st.download_button("Download Excel", buf.getvalue(), "REKAP_HASIL.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
                else:
                    if len(final_data) == 1:
                        k = list(final_data.keys())[0]
                        st.download_button("Download CSV", final_data[k].to_csv(index=False).encode(), f"{k}.csv", "text/csv", type="primary")
                    else:
                        zbuf = BytesIO()
                        with zipfile.ZipFile(zbuf, "w") as zf:
                            for k, v in final_data.items():
                                zf.writestr(f"{k}.csv", v.to_csv(index=False))
                        st.download_button("Download ZIP", zbuf.getvalue(), "REKAP_CSV.zip", "application/zip", type="primary")

    # --- Reset Button ---
    st.markdown("---")
    if st.button("Reset / Proses File Baru", type="secondary"):
        reset_app()
        st.rerun()

# --- 7. Footer Credits ---
st.markdown(
    """
    <div style='text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 3rem; margin-bottom: 2rem; padding-top: 1rem; border-top: 1px solid #eee;'>
        Developed by <b>Muhammad Dzaky</b> & <b>Gian Adiansyah</b>
    </div>
    """,
    unsafe_allow_html=True
)