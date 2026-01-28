import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import zipfile
import concurrent.futures

# --- Local Modules ---
from logic import (
    baca_dan_bersihkan_file,
    hitung_ranking,
    cari_penyakit_umum
)
from pdf_generator import (
    create_pdf_report,
    create_custom_pdf
)

# ==============================================================================
# 0. KONFIGURASI & STATE
# ==============================================================================
st.set_page_config(
    page_title="Rekap Data Kesehatan",
    page_icon="🏥",
    layout="wide"
)

if 'upload_key' not in st.session_state:
    st.session_state.upload_key = 0
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False

def reset_app():
    """Mereset aplikasi dan cache."""
    st.session_state.upload_key += 1
    st.session_state.data_processed = False
    st.cache_data.clear()

# ==============================================================================
# 1. HELPER FUNCTIONS (STYLING, VISUALIZATION, PREVIEW)
# ==============================================================================

def load_css(file_name):
    """Memuat file CSS eksternal."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def style_zigzag_groups(df, group_col):
    """
    Memberikan warna selang-seling (Zebra Striping) berdasarkan grup value.
    Adaptif untuk Light/Dark mode.
    """
    try:
        if group_col not in df.columns: return df
        unique_groups = df[group_col].unique()
        
        # Style transparan & abu halus
        styles = [
            'background-color: rgba(128, 128, 128, 0.1);', 
            'background-color: transparent;'
        ]
        
        group_map = {group: styles[i % 2] for i, group in enumerate(unique_groups)}
        
        def apply_style(row):
            return [group_map.get(row.get(group_col), '')] * len(row)
            
        return df.style.apply(apply_style, axis=1)
    except: return df

def make_bar_chart(df, label_context="Kategori", value_col='Total_Kasus', title=""):
    """Helper untuk membuat Horizontal Bar Chart dengan Altair."""
    df = df.copy()
    
    # Ensure columns exist
    if 'ICD X' not in df.columns: df['ICD X'] = '-'
    if label_context not in df.columns:
        df['Context'] = label_context
        tooltip_ctx = 'Context'
    else:
        tooltip_ctx = label_context

    # Truncate label
    df['Label_Pendek'] = df['Jenis Penyakit'].str.slice(0, 30) + '...'
    
    chart = alt.Chart(df).mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
        x=alt.X(value_col, title=value_col.replace('_', ' ')),
        y=alt.Y('Label_Pendek', sort='-x', title=None),
        color=alt.value("#4facfe"), # Modern Blue
        tooltip=['Jenis Penyakit', 'ICD X', value_col, alt.Tooltip(tooltip_ctx, title='Kategori')]
    ).properties(title=title, height=400)
    
    text = chart.mark_text(align='left', dx=5, color='white').encode(
        text=alt.Text(value_col)
    )
    
    return (chart + text).configure_axis(
        labelFontSize=12, titleFontSize=14
    ).configure_view(strokeWidth=0)

def render_theme_preview(theme_name, title_text="Laporan Rekapitulasi Data Kesehatan"):
    """Menampilkan preview visual CSS sederhana untuk tema PDF."""
    
    # Config Colors (Match pdf_generator.py)
    if theme_name == 'Formal Monochrome':
        header_bg = "#FFFFFF"
        header_txt = "#000000"
        border = "1px solid #000000"
        font = "Times New Roman, serif"
        stripe = "#FFFFFF"
    elif theme_name == 'Medical Fresh':
        header_bg = "#16A085" # Teal
        header_txt = "#FFFFFF" 
        border = "none"
        font = "Helvetica, Arial, sans-serif"
        stripe = "#FFFFFF" # Clean
        border_bottom = "1px solid #ddd" # Only horizontal
    else: # Modern Minimalist
        header_bg = "#2C3E50" # Navy
        header_txt = "#FFFFFF"
        border = "none"
        font = "Helvetica, Arial, sans-serif"
        stripe = "#F2F2F2"

    # HTML Preview
    st.markdown(f"""
    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-family: {font}; color: #333;">
        <div style="font-size: 10px; color: #888; margin-bottom: 5px;">PREVIEW DESAIN: {theme_name.upper()}</div>
        <!-- HEADER -->
        <div style="background-color: {header_bg}; color: {header_txt}; padding: 10px; font-weight: bold; font-size: 14px; border: {border};">
            {title_text}
        </div>
        <div style="margin-top: 10px; font-size: 12px;">
            <b>1. Pendahuluan</b><br>
            Berikut adalah data penyakit...
        </div>
        <!-- TABLE -->
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px;">
            <tr style="background-color: {header_bg}; color: {header_txt};">
                <th style="padding: 5px; border: {border}; text-align: left;">Kecamatan</th>
                <th style="padding: 5px; border: {border}; text-align: left;">Penyakit</th>
                <th style="padding: 5px; border: {border}; text-align: left;">Kasus</th>
            </tr>
            <tr style="background-color: #fff; border-bottom: { '1px solid #eee' if theme_name != 'Formal Monochrome' else '1px solid black' };">
                <td style="padding: 5px; border: {border};">Semarang Tengah</td>
                <td style="padding: 5px; border: {border};">Hipertensi</td>
                <td style="padding: 5px; border: {border};">150</td>
            </tr>
            <tr style="background-color: {stripe}; border-bottom: { '1px solid #eee' if theme_name != 'Formal Monochrome' else '1px solid black' };">
                <td style="padding: 5px; border: {border};">Banyumanik</td>
                <td style="padding: 5px; border: {border};">ISPA</td>
                <td style="padding: 5px; border: {border};">120</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
# ==============================================================================
# 2. LOGIC WRAPPER
# ==============================================================================

@st.cache_data(show_spinner=False)
def process_single_file_v2(file):
    """Wrapper cached untuk file processing."""
    file.seek(0)
    return baca_dan_bersihkan_file(file)

# ==============================================================================
# 3. PAGE MODULES (VIEW LOGIC)
# ==============================================================================

def show_quality_report(log_data):
    """Menampilkan expander laporan kualitas data data."""
    with st.expander("📝 Laporan Kualitas Data (Quality Check)", expanded=False):
        if log_data:
            df_log = pd.DataFrame(log_data)
            
            # Summary Counts
            err_count = df_log[df_log['status'] == 'ERROR'].shape[0]
            warn_count = df_log[df_log['status'] == 'WARNING'].shape[0]
            
            if err_count > 0:
                st.error(f"Ditemukan {err_count} File Gagal Diproses!")
            elif warn_count > 0:
                st.warning(f"Ditemukan {warn_count} File dengan Peringatan.")
            else:
                st.success("Semua File Berhasil Diproses Sempurna.")
                
            def highlight_status(val):
                color = 'green' if val == 'SUCCESS' else 'red' if val == 'ERROR' else 'orange'
                return f'color: {color}; font-weight: bold'
            
            # Note: Styler.applymap is deprecated, usage depends on pandas version. 
            # Using map() which is standard in newer pandas.
            try:
                styled_df = df_log.style.map(highlight_status, subset=['status'])
            except AttributeError:
                styled_df = df_log.style.applymap(highlight_status, subset=['status'])

            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("Belum ada data log.")

def show_dashboard_recap(master_df, uploaded_files, log_data):
    """Tampilan Mode: Dashboard Utama"""
    st.title("🏥 Rekap Data Penyakit")
    st.markdown("Dashboard rekapitulasi data penyakit per kecamatan dan puskesmas.")
    
    # QA Report
    show_quality_report(log_data)
    
    st.divider()

    # --- HELPER COLUMNS FOR FILTER ---
    master_df['Label_Filter'] = master_df['ICD X'].astype(str) + " - " + master_df['Jenis Penyakit'].astype(str)
    master_df['Alpha_Filter'] = master_df['ICD X'].astype(str).str[0].str.upper()
    unique_diseases = sorted(master_df['Label_Filter'].unique())
    unique_alpha = sorted(master_df['Alpha_Filter'].unique())

    # --- SIDEBAR: SETTINGS & FILTER ---
    with st.sidebar:
        st.markdown("---")
        with st.form(key='settings_form'):
            st.header("⚙️ 2. Pengaturan & Filter")
            
            # Ranking Settings
            st.subheader("Ranking (Top N)")
            c1, c2 = st.columns(2)
            with c1:
                top_n_kec_val = st.number_input("Kecamatan", 1, 25, 10)
                top_n_common_val = st.number_input("Analisis Umum", 1, 25, 5)
            with c2:
                top_n_pusk_val = st.number_input("Puskesmas", 1, 25, 10)
            
            st.markdown("---")
            
            # Filter Tabs
            st.subheader("Filter Data")
            tab_inc, tab_exc = st.tabs(["✅ Include", "❌ Exclude"])
            with tab_inc:
                st.caption("HANYA tampilkan:")
                inc_a = st.multiselect("Huruf Awal:", unique_alpha, key='inc_a')
                inc_l = st.multiselect("Penyakit:", unique_diseases, key='inc_l')
            with tab_exc:
                st.caption("SEMBUNYIKAN data:")
                exc_a = st.multiselect("Huruf Awal:", unique_alpha, key='exc_a')
                exc_l = st.multiselect("Penyakit:", unique_diseases, key='exc_l')
            
            st.markdown("---")
            submitted = st.form_submit_button("MULAI REKAPITULASI", type="primary")
            
            if submitted:
                st.session_state.data_processed = True

    # --- MAIN DISPLAY (IF PROCESSED) ---
    if not st.session_state.data_processed:
        st.markdown("""
        <div class="ready-box">
            <h3>✅ Data Siap Diproses</h3>
            <p>Silakan atur filter di sidebar, lalu klik tombol <b>"MULAI REKAPITULASI"</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Preview Data Mentah"):
            st.dataframe(master_df.head(), use_container_width=True)
    else:
        # 1. APPLY FILTERS
        df_view = master_df.copy()
        
        # Include Logic
        mask_inc = pd.Series([False]*len(df_view), index=df_view.index)
        has_inc = False
        if inc_a: mask_inc |= df_view['Alpha_Filter'].isin(inc_a); has_inc=True
        if inc_l: mask_inc |= df_view['Label_Filter'].isin(inc_l); has_inc=True
        if has_inc: df_view = df_view[mask_inc]
        
        # Exclude Logic
        if exc_a: df_view = df_view[~df_view['Alpha_Filter'].isin(exc_a)]
        if exc_l: df_view = df_view[~df_view['Label_Filter'].isin(exc_l)]

        if df_view.empty:
            st.error("⚠️ Hasil filter kosong! Silakan atur ulang filter.")
            return

        # 2. CALCULATE RANKING
        top_kec = hitung_ranking(df_view, ['Kecamatan'], top_n=top_n_kec_val)
        top_pusk = hitung_ranking(df_view, ['Puskesmas'], top_n=top_n_pusk_val)
        common_pusk = cari_penyakit_umum(top_pusk, 'Puskesmas', top_n=top_n_common_val)
        common_kec = cari_penyakit_umum(top_kec, 'Kecamatan', top_n=top_n_common_val)

        # 3. METRICS
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Total File", f"{len(uploaded_files)}")
        with m2: st.metric("Unit Puskesmas", f"{df_view['Puskesmas'].nunique()}")
        with m3: st.metric("Total Kasus", f"{df_view['Total_Kasus'].sum():,}")
        
        st.markdown("---")
        status_txt = "Aktif" if (has_inc or exc_a or exc_l) else "Non-Aktif"
        st.info(f"ℹ️ **Filter:** {status_txt} | **Ranking:** Kec({top_n_kec_val}), Pusk({top_n_pusk_val}), Umum({top_n_common_val})")

        # 4. TABS & VISUALIZATION
        t1, t2, t3, t4 = st.tabs([
            f"🏢 Top {top_n_kec_val} Kecamatan", 
            f"🏥 Top {top_n_pusk_val} Puskesmas", 
            f"🦠 Top {top_n_common_val} Umum",
            "📂 Data Mentah"
        ])

        with t1:
            st.subheader(f"Top {top_n_kec_val} Penyakit per Kecamatan")
            with st.expander("📊 Lihat Grafik Visualisasi", expanded=True):
                c_data = top_kec.groupby('Jenis Penyakit')['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(10)
                st.altair_chart(make_bar_chart(c_data, "Global Kecamatan", title="Top 10 Global"), use_container_width=True)
            st.dataframe(style_zigzag_groups(top_kec, 'Kecamatan'), use_container_width=True, height=500)

        with t2:
            st.subheader(f"Top {top_n_pusk_val} Penyakit per Puskesmas")
            with st.expander("📊 Lihat Grafik Visualisasi", expanded=True):
                c_data = top_pusk.groupby('Jenis Penyakit')['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(10)
                st.altair_chart(make_bar_chart(c_data, "Global Puskesmas", title="Top 10 Global"), use_container_width=True)
            st.dataframe(style_zigzag_groups(top_pusk, 'Puskesmas'), use_container_width=True, height=500)

        with t3:
            st.subheader("Analisis Dominasi Penyakit")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Persebaran di Kecamatan**")
                st.altair_chart(make_bar_chart(common_kec.head(10), "Kecamatan", value_col='Frekuensi'), use_container_width=True)
                st.dataframe(common_kec, use_container_width=True)
            with c2:
                st.markdown("**Persebaran di Puskesmas**")
                st.altair_chart(make_bar_chart(common_pusk.head(10), "Puskesmas", value_col='Frekuensi'), use_container_width=True)
                st.dataframe(common_pusk, use_container_width=True)

        with t4:
            st.subheader("Data Terfilter")
            st.dataframe(df_view.drop(columns=['Label_Filter', 'Alpha_Filter']), use_container_width=True)

        # 5. EXPORT / DOWNLOAD
        _render_download_section(df_view, top_kec, top_pusk, common_kec, uploaded_files, {
            "kec":top_n_kec_val, "pusk":top_n_pusk_val, "umum":top_n_common_val
        })

def _render_download_section(df_view, top_kec, top_pusk, common_kec, uploaded_files, n_stats):
    """Helper internal bagian download."""
    st.markdown("---")
    st.subheader("📥 Download Hasil")
    
    raw_opts = {
        "Data Mentah": df_view.drop(columns=['Label_Filter', 'Alpha_Filter'] if 'Label_Filter' in df_view else [], errors='ignore'),
        f"Top {n_stats['kec']} Kecamatan": top_kec,
        f"Top {n_stats['pusk']} Puskesmas": top_pusk,
        "Analisis Umum": common_kec
    }
    
    c1, c2 = st.columns(2)
    with c1: sel_data = st.multiselect("Pilih Data:", ["Semua Data"] + list(raw_opts.keys()), default=["Semua Data"])
    with c2: fmt = st.radio("Format:", ["Excel", "CSV"], horizontal=True)
    
    if sel_data:
        final_data = raw_opts if "Semua Data" in sel_data else {k:v for k,v in raw_opts.items() if k in sel_data}
        
        if fmt == "Excel":
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                for k, v in final_data.items():
                    sheet = k[:30].replace(" ", "_").upper()
                    clean_sheet = "".join(c for c in sheet if c.isalnum() or c=="_")
                    v.to_excel(writer, sheet_name=clean_sheet, index=False)
            st.download_button("⬇️ Download Excel", buf.getvalue(), "REKAP_HASIL.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
        else:
            if len(final_data) == 1:
                k = list(final_data.keys())[0]
                st.download_button("⬇️ Download CSV", final_data[k].to_csv(index=False).encode(), f"{k}.csv", "text/csv", type="primary")
            else:
                zbuf = BytesIO()
                with zipfile.ZipFile(zbuf, "w") as zf:
                    for k, v in final_data.items():
                        zf.writestr(f"{k}.csv", v.to_csv(index=False))
                st.download_button("⬇️ Download ZIP", zbuf.getvalue(), "REKAP_CSV.zip", "application/zip", type="primary")

    # PDF Report Section
    st.markdown("#### 📄 Laporan PDF")
    if st.button("Generate PDF Report"):
        with st.spinner("Membuat PDF..."):
            metrics = {
                "total_file": len(uploaded_files),
                "total_pusk": df_view['Puskesmas'].nunique(),
                "total_kasus": df_view['Total_Kasus'].sum()
            }
            try:
                pdf_bytes = create_pdf_report(metrics, top_kec, top_pusk, common_kec, n_stats)
                st.download_button(
                    label="⬇️ Download PDF Result",
                    data=bytes(pdf_bytes),
                    file_name="Laporan_Rekap_Penyakit.pdf",
                    mime="application/pdf",
                    type="secondary"
                )
            except Exception as e:
                st.error(f"Gagal memproses PDF: {e}")

def show_regional_filter(master_df):
    """Tampilan Mode: Filter Wilayah (Drill-Down)"""
    st.title("🌍 Filter Wilayah")
    st.markdown("Analisis spesifik untuk satu Kecamatan atau Puskesmas tertentu.")
    st.divider()

    c1, c2 = st.columns(2)
    with c1: scope = st.selectbox("Pilih Tingkat Wilayah:", ["Kecamatan", "Puskesmas"])
    with c2:
        # FIX: Ensure sorting on strings only to prevent float-str comparison error
        opts = sorted(master_df[scope].dropna().astype(str).unique())
        entity = st.selectbox(f"Pilih Nama {scope}:", opts)

    if entity:
        df_sub = master_df[master_df[scope] == entity].copy()
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Total Kasus", f"{df_sub['Total_Kasus'].sum():,}")
        with m2: st.metric("Jenis Penyakit Unik", f"{df_sub['Jenis Penyakit'].nunique()}")
        with m3: 
            if scope == "Kecamatan": st.metric("Jumlah Pusk.", f"{df_sub['Puskesmas'].nunique()}")
            else: st.metric("Kecamatan", df_sub['Kecamatan'].iloc[0] if not df_sub.empty else "-")
        
        st.markdown("### Top 10 Penyakit")
        top_10 = hitung_ranking(df_sub, [scope], top_n=10)
        
        c_chart, c_table = st.columns([1, 1])
        with c_chart:
            c_data = top_10.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(10)
            st.altair_chart(make_bar_chart(c_data, entity, title=f"Top 10 di {entity}"), use_container_width=True)
        with c_table:
            st.dataframe(style_zigzag_groups(top_10, scope), use_container_width=True)

def show_comparison(master_df):
    """Tampilan Mode: Komparasi"""
    st.title("⚖️ Komparasi Puskesmas")
    st.markdown("Bandingkan data kesehatan antara dua Puskesmas secara head-to-head.")
    st.divider()

    # FIX: Casting to str before sorting to avoid TypeError with NaNs or mixed types
    pusk_list = sorted(master_df['Puskesmas'].dropna().astype(str).unique())
    c1, c2 = st.columns(2)
    with c1: p1 = st.selectbox("Pilih Puskesmas A", pusk_list, index=0)
    with c2: p2 = st.selectbox("Pilih Puskesmas B", pusk_list, index=1 if len(pusk_list)>1 else 0)

    if p1 and p2:
        if p1 == p2:
            st.warning("Silakan pilih dua Puskesmas yang berbeda.")
        else:
            df1 = master_df[master_df['Puskesmas'] == p1]
            df2 = master_df[master_df['Puskesmas'] == p2]

            # Compare Metrics
            st.subheader("1. Perbandingan Total Kasus")
            cm1, cm2 = st.columns(2)
            val1 = df1['Total_Kasus'].sum()
            val2 = df2['Total_Kasus'].sum()
            with cm1: st.metric(f"Total {p1}", f"{val1:,}")
            with cm2: st.metric(f"Total {p2}", f"{val2:,}", delta=f"{val2-val1:,}")
            st.markdown("---")

            # Compare Top 5
            st.subheader("2. Top 5 Penyakit Masing-Masing")
            top5_1 = df1.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(5)
            top5_2 = df2.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(5)

            cc1, cc2 = st.columns(2)
            with cc1:
                st.caption(f"Di {p1}")
                st.altair_chart(make_bar_chart(top5_1, p1, title=p1), use_container_width=True)
            with cc2:
                st.caption(f"Di {p2}")
                st.altair_chart(make_bar_chart(top5_2, p2, title=p2), use_container_width=True)
            
            # Intersection
            st.subheader("3. Irisan Penyakit")
            merged = pd.merge(top5_1[['Jenis Penyakit', 'Total_Kasus']], top5_2[['Jenis Penyakit', 'Total_Kasus']], on='Jenis Penyakit', how='inner', suffixes=(f'_{p1}', f'_{p2}'))
            if not merged.empty: st.dataframe(merged, use_container_width=True)
            else: st.info("Tidak ada irisan penyakit di Top 5.")



def show_custom_report(master_df):
    """Tampilan Mode: Laporan Custom"""
    st.title("📄 Laporan PDF Custom")
    st.markdown("Rancang isi laporan PDF sesuai kebutuhan Anda.")
    st.markdown("*Fitur ini masih dalam tahap pengembangan, jika ada kesalahan dalam generate mohon lapor ke admin")
    st.divider()

    # --- CONFIG FORM ---
    with st.form("custom_report_form"):
        st.subheader("1. Desain & Judul")
        
        c_des1, c_des2 = st.columns([1, 2])
        with c_des1:
            # Theme Selector
            pdf_theme = st.selectbox(
                "Pilih Tema Desain:", 
                ['Modern Minimalist', 'Formal Monochrome', 'Medical Fresh']
            )
            # Show live preview (Dynamic Title)
            curr_title = st.session_state.get('rep_title', "Laporan Custom Rekap Data Kesehatan")
            render_theme_preview(pdf_theme, curr_title)
            
        with c_des2:
            st.text_input("Judul Laporan:", "Laporan Custom Rekap Data Kesehatan", key="rep_title")
            st.info("💡 Tema mempengaruhi jenis font, warna header, dan gaya tabel di PDF.")
        
        st.markdown("---")
        st.subheader("2. Pilih Konten")
        
        # Section 1: Rankings
        c1, c2, c3 = st.columns(3)
        with c1:
            inc_kec = st.checkbox("Top N Kecamatan", value=True)
            n_kec = st.number_input("N Kecamatan", 1, 50, 10, disabled=not inc_kec)
        with c2:
            inc_pusk = st.checkbox("Top N Puskesmas", value=True)
            n_pusk = st.number_input("N Puskesmas", 1, 50, 10, disabled=not inc_pusk)
        with c3:
            inc_umum = st.checkbox("Top N Umum", value=True)
            n_umum = st.number_input("N Umum", 1, 50, 5, disabled=not inc_umum)
            
        st.markdown("---")
        
        # Section 2: Drill Down Filter
        inc_filter = st.checkbox("Sertakan Detail Wilayah (Filter)", value=False)
        f_scope, f_entity = None, None
        
        if inc_filter:
            fc1, fc2 = st.columns(2)
            with fc1: f_scope = st.selectbox("Tingkat Wilayah:", ["Kecamatan", "Puskesmas"], key="cust_f_scope")
            with fc2: 
                opts = sorted(master_df[f_scope].dropna().astype(str).unique())
                f_entity = st.selectbox(f"Pilih Nama {f_scope}:", opts, key="cust_f_entity")
        
        st.markdown("---")
        
        # Section 3: Comparison
        inc_compare = st.checkbox("Sertakan Komparasi Puskesmas", value=False)
        comp_p1, comp_p2 = None, None
        
        if inc_compare:
            p_list = sorted(master_df['Puskesmas'].dropna().astype(str).unique())
            cc1, cc2 = st.columns(2)
            with cc1: comp_p1 = st.selectbox("Puskesmas A:", p_list, index=0, key="cust_c_p1")
            with cc2: comp_p2 = st.selectbox("Puskesmas B:", p_list, index=1 if len(p_list)> 1 else 0, key="cust_c_p2")
            
        st.markdown("---")
        submit = st.form_submit_button("🔨 Generate Laporan PDF", type="primary")

    if submit:
        # VALIDATION
        if inc_compare and comp_p1 == comp_p2:
            st.error("Komparasi gagal: Pilih dua Puskesmas yang berbeda.")
            return

        with st.spinner("Mengumpulkan data dan menyusun PDF..."):
            # 1. GATHER DATA (Recalculate based on input)
            report_title_val = st.session_state.rep_title if 'rep_title' in st.session_state else "Laporan Custom"
            
            data_payload = {}
            if inc_kec: data_payload['df_kec'] = hitung_ranking(master_df, ['Kecamatan'], top_n=n_kec)
            if inc_pusk: data_payload['df_pusk'] = hitung_ranking(master_df, ['Puskesmas'], top_n=n_pusk)
            if inc_umum:
                tmp_pusk = hitung_ranking(master_df, ['Puskesmas'], top_n=10)
                data_payload['df_umum'] = cari_penyakit_umum(tmp_pusk, 'Puskesmas', top_n=n_umum)
            
            if inc_filter and f_entity:
                df_f = master_df[master_df[f_scope] == f_entity].copy()
                data_payload['df_filter'] = hitung_ranking(df_f, [f_scope], top_n=20)
                data_payload['filter_metrics'] = {'kasus': df_f['Total_Kasus'].sum()}
            
            if inc_compare and comp_p1 and comp_p2:
                 df1 = master_df[master_df['Puskesmas'] == comp_p1]
                 df2 = master_df[master_df['Puskesmas'] == comp_p2]
                 top1 = df1.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(10)
                 top2 = df2.groupby(['Jenis Penyakit', 'ICD X'])['Total_Kasus'].sum().reset_index().sort_values('Total_Kasus', ascending=False).head(10)
                 intersect = pd.merge(top1[['Jenis Penyakit', 'Total_Kasus']], top2[['Jenis Penyakit', 'Total_Kasus']], on='Jenis Penyakit', how='inner', suffixes=(f'_{comp_p1}', f'_{comp_p2}'))
                 data_payload['df_comp1'] = top1
                 data_payload['df_comp2'] = top2
                 data_payload['df_comp_intersect'] = intersect
        
            # 2. BUILD CONFIG
            config = {
                'title': report_title_val,
                'inc_kec': inc_kec, 'inc_pusk': inc_pusk, 'inc_umum': inc_umum,
                'inc_filter': inc_filter, 'filter_label': f"{f_entity} ({f_scope})" if f_entity else "",
                'inc_compare': inc_compare, 'comp_names': (comp_p1, comp_p2) if inc_compare else None
            }
            
            # 3. GENERATE PDF (Pass Theme)
            try:
                pdf_bytes = create_custom_pdf(config, data_payload, theme_name=pdf_theme)
                st.success(f"PDF Berhasil Dibuat dengan Tema: {pdf_theme}!")
                
                st.download_button(
                    label="⬇️ Download Custom PDF",
                    data=bytes(pdf_bytes),
                    file_name=f"Laporan_{pdf_theme.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Gagal generate PDF: {e}")

# ==============================================================================
# 4. MAIN APP EXECUTION
# ==============================================================================

def main():
    load_css("style.css")
    
    # --- SIDEBAR INPUT ---
    with st.sidebar:
        st.header("📂 1. Input Data")
        st.markdown("""
        <div class="sidebar-info">
            <b>📋 Ketentuan File Excel:</b><br>
            1. Format wajib <b>.xlsx</b><br>
            2. Header data harus di <b>Baris ke-2</b><br>
            3. Data Penyakit ada di kolom <b>D - AY</b><br>
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
            st.caption("Masukan file untuk lanjut.")

    # --- MAIN CONTENT LOGIC ---
    if not uploaded_files:
        st.empty()
        st.markdown("""
        <div style="text-align: center; padding: 50px; opacity: 0.7;">
            <h3>👋 Selamat Datang!</h3>
            <p>Silakan upload file Excel laporan puskesmas melalui panel di sebelah kiri.</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.data_processed = False
    else:
        # Load & Process
        # OPTIMASI 3: Parallel Processing (Multi-threading)

        
        with st.spinner(f'Memproses {len(uploaded_files)} file secara paralel... (Engine: Otomatis)'):
            all_dfs, all_logs = [], []
            
            # Helper function untuk threading (karena st.cache sudah handle concurrency, kita panggil wrapper-nya)
            # ThreadPoolExecutor sangat efektif untuk I/O bound task seperti baca file.
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = list(executor.map(process_single_file_v2, uploaded_files))
                
                # Pisahkan hasil DF dan Log
                for df_res, log_res in results:
                    all_logs.append(log_res)
                    if not df_res.empty:
                        all_dfs.append(df_res)
                        
            except Exception as e:
                st.error(f"Terjadi kesalahan sistem saat pemrosesan paralel: {e}")
            
            master_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        if not master_df.empty:
            # Navigation
            st.sidebar.markdown("---")
            mode = st.sidebar.radio("📌 Pilih Mode:", ["Dashboard Utama", "Filter Wilayah", "Komparasi", "Laporan Custom"])
            
            if mode == "Dashboard Utama":
                show_dashboard_recap(master_df, uploaded_files, all_logs)
            elif mode == "Filter Wilayah":
                show_regional_filter(master_df)
            elif mode == "Komparasi":
                show_comparison(master_df)
            elif mode == "Laporan Custom":
                show_custom_report(master_df)
        else:
            # Case where files are uploaded but empty content
            st.error("Tidak ada data valid yang dapat diolah.")
            show_quality_report(all_logs)

    # Reset
    st.markdown("---")
    if st.button("🔄 Reset / Proses File Baru", type="secondary"):
        reset_app()
        st.rerun()
    
    # Footer
    st.markdown('<div class="footer">Developed by <b>Muhammad Dzaky</b> & <b>Gian Adiansyah</b></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()