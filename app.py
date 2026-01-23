import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
from logic import (
    baca_dan_bersihkan_file,
    hitung_ranking,
    cari_penyakit_umum
)

# --- 0. State Management untuk Reset Flow ---
if 'upload_key' not in st.session_state:
    st.session_state.upload_key = 0

def reset_app():
    """Fungsi untuk mereset aplikasi dan uploader"""
    st.session_state.upload_key += 1

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
    h1 {
        font-weight: 700;
        color: #2C3E50;
        font-size: 2.5rem;
        margin-bottom: 0rem;
    }
    h3 {
        font-weight: 600;
        color: #34495E;
        margin-top: 1rem;
    }
    div[data-testid="stMetric"] {
        background-color: #F0F2F6;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        color: #31333F;
    }
    div[data-testid="stMetric"] label { color: #555 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #000 !important; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #2C3E50;
    }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] p {
        color: #ECF0F1 !important;
    }
    /* Dropdown Multiselect di Sidebar */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #34495E;
        color: white;
        border-color: #5D6D7E;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {
        background-color: #1ABC9C;
    }
    /* Input Number Styling */
    section[data-testid="stSidebar"] div[data-baseweb="input"] {
        background-color: #34495E !important;
        color: white !important;
        border-color: #5D6D7E !important;
    }
    section[data-testid="stSidebar"] input {
        color: white !important;
    }
    
    div.stAlert > div[data-testid="stMarkdownContainer"] {
        color: #2C3E50 !important; 
    }
    div.stButton > button[kind="primary"] {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    div.stButton > button[kind="secondary"] {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #E74C3C;
        color: #E74C3C;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #C0392B;
        color: #C0392B;
        background-color: #FDEDEC;
    }
    .block-container { padding-top: 2rem; }
    
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
    """
    Memberikan warna selang-seling (zigzag) berdasarkan group.
    """
    try:
        if group_col not in df.columns:
            return df
            
        unique_groups = df[group_col].unique()
        # Warna 1: Sangat gelap (mendekati hitam)
        # Warna 2: Abu gelap
        styles = [
            'background-color: #1A1A1A; color: white;', 
            'background-color: #333333; color: white;' 
        ]
        
        group_map = {
            group: styles[i % 2] for i, group in enumerate(unique_groups)
        }
        
        def apply_style(row):
            group_val = row.get(group_col)
            css = group_map.get(group_val, '')
            return [css] * len(row)

        return df.style.apply(apply_style, axis=1)
    except:
        return df

# --- 3. Sidebar (Area Upload & Filter) ---
with st.sidebar:
    st.header("📂 Input Data")
    st.markdown("Upload file Excel laporan puskesmas di sini.")
    
    uploaded_files = st.file_uploader(
        "Pilih file Excel",
        type="xlsx",
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_{st.session_state.upload_key}"
    )
    
    st.info(
        """
        **Panduan:**
        1. Pastikan format file sesuai standar dinas.
        2. Upload file, lalu gunakan fitur Filter di bawah.
        3. Klik tombol 'Terapkan' untuk memproses filter.
        """
    )

# --- 4. Main Content ---
st.title("🏥 Rekap Data Penyakit")
st.markdown("Dashboard rekapitulasi data penyakit per kecamatan dan puskesmas secara otomatis.")
st.divider()

if not uploaded_files:
    st.container().markdown(
        """
        <div style="text-align: center; padding: 50px; color: #7f8c8d;">
            <h3>👋 Selamat Datang!</h3>
            <p>Belum ada data yang diproses. Silakan upload file Excel melalui panel di sebelah kiri.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    # Proses Data Awal (Load File)
    with st.spinner('Sedang memuat data...'):
        all_data = []
        progress_text = "Memproses file..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, file in enumerate(uploaded_files):
            df = baca_dan_bersihkan_file(file)
            all_data.append(df)
            my_bar.progress((i + 1) / len(uploaded_files), text=f"Memproses {file.name}")
        
        my_bar.empty()
        
        master_df = pd.concat(all_data, ignore_index=True)

    # --- FITUR FILTER & SETTING (DALAM FORM) ---
    master_df['Label_Filter'] = master_df['ICD X'].astype(str) + " - " + master_df['Jenis Penyakit'].astype(str)
    master_df['Alpha_Filter'] = master_df['ICD X'].astype(str).str[0].str.upper()
    
    unique_diseases = sorted(master_df['Label_Filter'].unique())
    unique_alpha = sorted(master_df['Alpha_Filter'].unique())

    with st.sidebar:
        # Menggunakan st.form agar tidak auto-process
        with st.form(key='settings_form'):
            st.markdown("---")
            st.header("⚙️ Pengaturan Ranking")
            
            st.caption("Tentukan jumlah ranking (1-25) untuk setiap kategori:")
            
            top_n_kec_val = st.number_input(
                "Top N - Kecamatan:",
                min_value=1, max_value=25, value=10, step=1,
                help="Jumlah penyakit tertinggi yang ditampilkan per Kecamatan."
            )
            
            top_n_pusk_val = st.number_input(
                "Top N - Puskesmas:",
                min_value=1, max_value=25, value=10, step=1,
                help="Jumlah penyakit tertinggi yang ditampilkan per Puskesmas."
            )

            top_n_common_val = st.number_input(
                "Top N - Penyakit Umum:",
                min_value=1, max_value=25, value=5, step=1,
                help="Jumlah penyakit yang ditampilkan di tabel analisis 'Paling Umum'."
            )

            st.markdown("---")
            st.header("🔍 Filter Data")
            
            tab_include, tab_exclude = st.tabs(["✅ Include", "❌ Exclude"])
            
            with tab_include:
                st.caption("Tampilkan HANYA data ini:")
                include_alpha = st.multiselect(
                    "Pilih Huruf Awal:",
                    options=unique_alpha,
                    key='inc_alpha'
                )
                include_list = st.multiselect(
                    "Pilih Spesifik Penyakit:",
                    options=unique_diseases,
                    placeholder="Cari kode/nama penyakit...",
                    key='inc_list'
                )
                
            with tab_exclude:
                st.caption("BUANG/SEMBUNYIKAN data ini:")
                exclude_alpha = st.multiselect(
                    "Pilih Huruf Awal:",
                    options=unique_alpha,
                    key='exc_alpha'
                )
                exclude_list = st.multiselect(
                    "Pilih Spesifik Penyakit:",
                    options=unique_diseases,
                    placeholder="Cari kode/nama penyakit...",
                    key='exc_list'
                )
            
            st.markdown("---")
            # Tombol Submit Form
            submitted = st.form_submit_button("Terapkan", type="primary")

    # 4. Terapkan Filter ke DataFrame Utama (Hanya berjalan setelah form disubmit atau load awal)
    
    filtered_df = master_df.copy()

    # Logic Include
    mask_include_alpha = pd.Series([False] * len(filtered_df), index=filtered_df.index)
    mask_include_list = pd.Series([False] * len(filtered_df), index=filtered_df.index)
    
    has_include_filter = False

    if include_alpha:
        mask_include_alpha = filtered_df['Alpha_Filter'].isin(include_alpha)
        has_include_filter = True
    
    if include_list:
        mask_include_list = filtered_df['Label_Filter'].isin(include_list)
        has_include_filter = True
        
    if has_include_filter:
        final_include_mask = mask_include_alpha | mask_include_list
        filtered_df = filtered_df[final_include_mask]

    # Logic Exclude
    if exclude_alpha:
        filtered_df = filtered_df[~filtered_df['Alpha_Filter'].isin(exclude_alpha)]
    
    if exclude_list:
        filtered_df = filtered_df[~filtered_df['Label_Filter'].isin(exclude_list)]

    if filtered_df.empty:
        st.error("⚠️ Data tidak ditemukan! Kombinasi filter Anda menghasilkan data kosong.")
    else:
        # --- PERHITUNGAN DINAMIS MENGGUNAKAN INPUT MANUAL TERPISAH ---
        
        # 1. Ranking Kecamatan pakai top_n_kec_val
        top_n_kec = hitung_ranking(filtered_df, ['Kecamatan'], top_n=top_n_kec_val)
        
        # 2. Ranking Puskesmas pakai top_n_pusk_val
        top_n_pusk = hitung_ranking(filtered_df, ['Puskesmas'], top_n=top_n_pusk_val)
        
        # 3. Penyakit Umum pakai top_n_common_val
        top_common_pusk = cari_penyakit_umum(top_n_pusk, 'Puskesmas', top_n=top_n_common_val)
        top_common_kec = cari_penyakit_umum(top_n_kec, 'Kecamatan', top_n=top_n_common_val)

        # Dashboard Metrics
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total File", f"{len(uploaded_files)} File")
        with col2: st.metric("Total Puskesmas", f"{filtered_df['Puskesmas'].nunique()} Unit")
        with col3: st.metric("Total Kasus", f"{filtered_df['Total_Kasus'].sum():,} penderita")

        st.markdown("---")
        
        # Info Status
        filter_status = "Aktif" if (has_include_filter or exclude_alpha or exclude_list) else "Non-Aktif"
        st.info(f"ℹ️ **Status Filter:** {filter_status} | **Ranking:** Kec(Top {top_n_kec_val}), Pusk(Top {top_n_pusk_val}), Umum(Top {top_n_common_val})")

        # Tabs View
        tab1, tab2, tab3, tab4 = st.tabs([
            f"🏢 Top {top_n_kec_val} Kecamatan", 
            f"🏥 Top {top_n_pusk_val} Puskesmas", 
            f"🦠 Top {top_n_common_val} Penyakit Umum",
            "📂 Data Mentah"
        ])

        with tab1:
            st.subheader(f"Top {top_n_kec_val} Penyakit per Kecamatan")
            st.dataframe(
                style_zigzag_groups(top_n_kec, 'Kecamatan'), 
                use_container_width=True, 
                height=500
            )

        with tab2:
            st.subheader(f"Top {top_n_pusk_val} Penyakit per Puskesmas")
            st.dataframe(
                style_zigzag_groups(top_n_pusk, 'Puskesmas'), 
                use_container_width=True, 
                height=500
            )

        with tab3:
            st.subheader(f"Analisis Top {top_n_common_val} Penyakit Paling Umum")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Dominasi di Kecamatan**")
                st.dataframe(top_common_kec, use_container_width=True)
            with col_b:
                st.markdown("**Dominasi di Puskesmas**")
                st.dataframe(top_common_pusk, use_container_width=True)

        with tab4:
            st.subheader("Database Lengkap (Terfilter)")
            display_df = filtered_df.drop(columns=['Label_Filter', 'Alpha_Filter'])
            st.dataframe(display_df, use_container_width=True)

        # --- 5. Export & Download Section ---
        st.markdown("---")
        st.subheader("📥 Export & Download Data")
        
        # Nama dataset dinamis sesuai N masing-masing
        raw_data_options = {
            "Data Mentah (Full)": filtered_df.drop(columns=['Label_Filter', 'Alpha_Filter']),
            f"Top {top_n_kec_val} Kecamatan": top_n_kec,
            f"Top {top_n_pusk_val} Puskesmas": top_n_pusk,
            f"Top {top_n_common_val} Umum (Kecamatan)": top_common_kec,
            f"Top {top_n_common_val} Umum (Puskesmas)": top_common_pusk
        }

        with st.container():
            col_opt1, col_opt2 = st.columns(2)
            
            with col_opt1:
                st.markdown("**1. Pilih Data yang ingin di-download:**")
                special_option = "✅ Laporan Lengkap (Semua Data)"
                display_options = [special_option] + list(raw_data_options.keys())
                
                selected_datasets = st.multiselect(
                    "Pilih dataset:",
                    options=display_options,
                    default=[special_option]
                )

            with col_opt2:
                st.markdown("**2. Pilih Format File:**")
                format_file = st.radio("Format:", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
                st.caption("*Catatan: Data yang didownload akan mengikuti filter dan setting N ranking yang aktif.*")

            st.markdown("")

            final_export_dict = {}
            if selected_datasets:
                if special_option in selected_datasets:
                    final_export_dict = raw_data_options
                else:
                    for key in selected_datasets:
                        if key in raw_data_options:
                            final_export_dict[key] = raw_data_options[key]

            if final_export_dict:
                if format_file == "Excel (.xlsx)":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        for name, data in final_export_dict.items():
                            # Bersihkan nama sheet (max 31 chars & valid chars)
                            clean_name = name[:30].replace(" ", "_").upper()
                            clean_name = "".join(c for c in clean_name if c.isalnum() or c == "_")
                            data.to_excel(writer, sheet_name=clean_name, index=False)
                    
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=output.getvalue(),
                        file_name="REKAP_DATA_CUSTOM_RANKING.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
                
                elif format_file == "CSV (.csv)":
                    if len(final_export_dict) == 1:
                        name = list(final_export_dict.keys())[0]
                        csv_data = final_export_dict[name].to_csv(index=False).encode('utf-8')
                        file_name = f"{name.replace(' ', '_').upper()}.csv"
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_data,
                            file_name=file_name,
                            mime="text/csv",
                            type="primary"
                        )
                    else:
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for name, data in final_export_dict.items():
                                csv_data = data.to_csv(index=False)
                                file_name = f"{name.replace(' ', '_').upper()}.csv"
                                zf.writestr(file_name, csv_data)
                        
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_buffer.getvalue(),
                            file_name="REKAP_DATA_CSV.zip",
                            mime="application/zip",
                            type="primary"
                        )
            else:
                st.warning("⚠️ Silakan pilih setidaknya satu data.")

    # --- 6. Reset Flow ---
    st.markdown("---")
    st.markdown("#### Selesai? Proses file lain:")
    
    col_reset1, col_reset2 = st.columns([1, 4])
    with col_reset1:
        if st.button("🔄 Proses File Lain", type="secondary", on_click=reset_app):
            pass

# --- 7. Footer Credits ---
st.markdown(
    """
    <div style='text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 3rem; margin-bottom: 2rem; padding-top: 1rem; border-top: 1px solid #eee;'>
        Developed by <b>Muhammad Dzaky</b> & <b>Gian Adiansyah</b>
    </div>
    """,
    unsafe_allow_html=True
)