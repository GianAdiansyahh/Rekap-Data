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
    section[data-testid="stSidebar"] {
        background-color: #2C3E50;
    }
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] div {
        color: #ECF0F1 !important;
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
</style>
""", unsafe_allow_html=True)

# --- FUNGSI STYLING ZIGZAG ---
def style_zigzag_groups(df, group_col):
    """
    Memberikan warna selang-seling (zigzag) berdasarkan group.
    Group 1: Hitam/Gelap
    Group 2: Abu Gelap
    Group 3: Hitam/Gelap
    dst.
    """
    try:
        if group_col not in df.columns:
            return df
            
        unique_groups = df[group_col].unique()
        # Warna 1: Sangat gelap (mendekati hitam)
        # Warna 2: Abu gelap
        # Text: Putih agar kontras
        styles = [
            'background-color: #1A1A1A; color: white;', 
            'background-color: #333333; color: white;' 
        ]
        
        # Mapping setiap nama group ke style-nya
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

# --- 3. Sidebar (Area Upload) ---
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
        2. Nama file sebaiknya mengandung nama puskesmas.
        3. Klik 'Browse files' atau drag & drop.
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
    # Proses Data
    with st.spinner('Sedang memproses data...'):
        all_data = []
        progress_text = "Memproses file..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, file in enumerate(uploaded_files):
            df = baca_dan_bersihkan_file(file)
            all_data.append(df)
            my_bar.progress((i + 1) / len(uploaded_files), text=f"Memproses {file.name}")
        
        my_bar.empty()
        
        master_df = pd.concat(all_data, ignore_index=True)
        
        top_10_pusk = hitung_ranking(master_df, ['Puskesmas'])
        top_10_kec = hitung_ranking(master_df, ['Kecamatan'])
        top_5_common_pusk = cari_penyakit_umum(top_10_pusk, 'Puskesmas')
        top_5_common_kec = cari_penyakit_umum(top_10_kec, 'Kecamatan')

    # Dashboard Metrics
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total File", f"{len(uploaded_files)} File")
    with col2: st.metric("Total Puskesmas", f"{master_df['Puskesmas'].nunique()} Unit")
    with col3: st.metric("Total Kasus", f"{master_df['Total_Kasus'].sum():,} penderita")

    st.markdown("---")

    # Tabs View
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Top 10 Kecamatan", 
        "🏥 Top 10 Puskesmas", 
        "🦠 Penyakit Umum",
        "📂 Data Mentah"
    ])

    with tab1:
        st.subheader("Penyakit Tertinggi per Kecamatan")
        # Apply Style Zigzag berdasarkan Kecamatan
        st.dataframe(
            style_zigzag_groups(top_10_kec, 'Kecamatan'), 
            use_container_width=True, 
            height=500
        )

    with tab2:
        st.subheader("Penyakit Tertinggi per Puskesmas")
        # Apply Style Zigzag berdasarkan Puskesmas
        st.dataframe(
            style_zigzag_groups(top_10_pusk, 'Puskesmas'), 
            use_container_width=True, 
            height=500
        )

    with tab3:
        st.subheader("Analisis Penyakit Paling Umum")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Dominasi di Kecamatan**")
            st.dataframe(top_5_common_kec, use_container_width=True)
        with col_b:
            st.markdown("**Dominasi di Puskesmas**")
            st.dataframe(top_5_common_pusk, use_container_width=True)

    with tab4:
        st.subheader("Database Lengkap")
        st.dataframe(master_df, use_container_width=True)

    # --- 5. Export & Download Section ---
    st.markdown("---")
    st.subheader("📥 Export & Download Data")
    
    # Definisi Data Options
    raw_data_options = {
        "Data Mentah (Full)": master_df,
        "Top 10 Kecamatan": top_10_kec,
        "Top 10 Puskesmas": top_10_pusk,
        "Top 5 Penyakit Umum (Kecamatan)": top_5_common_kec,
        "Top 5 Penyakit Umum (Puskesmas)": top_5_common_pusk
    }

    with st.container():
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            st.markdown("**1. Pilih Data yang ingin di-download:**")
            
            # Menambahkan opsi spesial 'All-in-One' di paling atas
            special_option = "✅ Laporan Lengkap (Semua Data)"
            display_options = [special_option] + list(raw_data_options.keys())
            
            selected_datasets = st.multiselect(
                "Pilih dataset:",
                options=display_options,
                default=[special_option] # Default pilih yang lengkap
            )

        with col_opt2:
            st.markdown("**2. Pilih Format File:**")
            format_file = st.radio("Format:", ["Excel (.xlsx)", "CSV (.csv)"], horizontal=True)
            st.caption("*Catatan: Format Excel lebih rapi untuk laporan lengkap.*")

        st.markdown("")

        # Logic Penentuan Data Akhir
        final_export_dict = {}
        if selected_datasets:
            # Jika opsi spesial dipilih, otomatis ambil semua data
            if special_option in selected_datasets:
                final_export_dict = raw_data_options
            else:
                # Jika tidak, ambil sesuai yang dipilih user
                for key in selected_datasets:
                    if key in raw_data_options:
                        final_export_dict[key] = raw_data_options[key]

        # Tombol Download
        if final_export_dict:
            if format_file == "Excel (.xlsx)":
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    for name, data in final_export_dict.items():
                        sheet_name = name[:30].replace(" ", "_").upper()
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                st.download_button(
                    label="⬇️ Download Excel",
                    data=output.getvalue(),
                    file_name="REKAP_DATA_LENGKAP.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            
            elif format_file == "CSV (.csv)":
                if len(final_export_dict) == 1:
                    # Single File
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
                    # Zip File
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zf:
                        for name, data in final_export_dict.items():
                            csv_data = data.to_csv(index=False)
                            file_name = f"{name.replace(' ', '_').upper()}.csv"
                            zf.writestr(file_name, csv_data)
                    
                    st.download_button(
                        label="⬇️ Download ZIP (Kumpulan CSV)",
                        data=zip_buffer.getvalue(),
                        file_name="REKAP_DATA_CSV.zip",
                        mime="application/zip",
                        type="primary"
                    )
        else:
            st.warning("⚠️ Silakan pilih setidaknya satu data.")

    # --- 6. Reset Flow (Paling Bawah) ---
    st.markdown("---")
    st.markdown("#### Selesai? Proses file lain:")
    
    col_reset1, col_reset2 = st.columns([1, 4])
    with col_reset1:
        if st.button("🔄 Proses File Lain", type="secondary", on_click=reset_app):
            # Callback reset_app akan dijalankan sebelum script di-rerun
            pass
st.markdown(
    """
    <div style='text-align: center; color: #95a5a6; font-size: 0.85rem; margin-top: 3rem; margin-bottom: 2rem; padding-top: 1rem; border-top: 1px solid #eee;'>
        Developed by <b>Muhammad Dzaky</b> & <b>Gian Adiansyah</b>
    </div>
    """,
    unsafe_allow_html=True
)