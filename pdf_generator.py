from fpdf import FPDF
from datetime import datetime
import pandas as pd

# --- THEME CONFIGURATION ---
# --- THEME CONFIGURATION ---
THEMES = {
    'Modern Minimalist': {
        'font_header': 'helvetica',
        'font_body': 'helvetica',
        'header_bg': (44, 62, 80),      # #2C3E50 (Midnight Blue)
        'header_txt': (255, 255, 255),  # White
        'stripe_bg': (242, 242, 242),   # #F2F2F2 (Light Grey)
        'table_fill_header': True,
        'table_borders': 'MINIMAL',     # Correct value for horizontal lines
        'title_size': 20
    },
    'Formal Monochrome': {
        'font_header': 'times',
        'font_body': 'times',
        'header_bg': (255, 255, 255),   # White
        'header_txt': (0, 0, 0),        # Black
        'stripe_bg': None,              # No zebra
        'table_fill_header': False,     # No colored header
        'table_borders': 'ALL',         # Grid formatting
        'title_size': 16
    },
    'Medical Fresh': {
        'font_header': 'helvetica',
        'font_body': 'helvetica',
        'header_bg': (22, 160, 133),    # #16A085 (Teal)
        'header_txt': (255, 255, 255),  # White
        'stripe_bg': None,              # Clean white body
        'table_fill_header': True,
        'table_borders': 'MINIMAL',     # Correct value for horizontal lines
        'title_size': 20
    }
}

class PDFReport(FPDF):
    """
    Custom FPDF class for generating Recap Reports.
    Includes custom header, footer, and utility methods for tables.
    """
    
    def __init__(self, theme_name='Modern Minimalist'):
        super().__init__()
        self.theme_name = theme_name
        self.theme = THEMES.get(theme_name, THEMES['Modern Minimalist'])

    def header(self):
        # Set Font based on Theme
        self.set_font(self.theme['font_header'], 'B', 15)
        
        # Color Config
        bg_r, bg_g, bg_b = self.theme['header_bg']
        txt_r, txt_g, txt_b = self.theme['header_txt']

        # Theme Handling
        if self.theme_name == 'Formal Monochrome':
            # Classic style: Simple Text
            self.set_text_color(txt_r, txt_g, txt_b)
            self.cell(0, 10, 'Laporan Rekapitulasi Data Penyakit', align='C', new_x="LMARGIN", new_y="NEXT")
            self.ln(5)
        else:
            # Modern/Fresh style: Colored Block
            self.set_fill_color(bg_r, bg_g, bg_b)
            self.set_text_color(txt_r, txt_g, txt_b)
            self.cell(0, 15, '   Laporan Rekapitulasi Data Penyakit', fill=True, align='L', new_x="LMARGIN", new_y="NEXT")
            self.ln(10)
        
        # Reset text color for body
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.theme['font_body'], 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Dicetak otomatis oleh Sistem Rekap Kesehatan', align='C')

    def chapter_title(self, title):
        self.set_font(self.theme['font_header'], 'B', 12)
        
        # Accent Color for Title
        if self.theme_name == 'Formal Monochrome':
            self.set_text_color(0, 0, 0)
        else:
            # Match header color for accent
            bg_r, bg_g, bg_b = self.theme['header_bg']
            self.set_text_color(bg_r, bg_g, bg_b)
            
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0) # Reset

    def chapter_body(self, body):
        self.set_font(self.theme['font_body'], '', 10)
        self.multi_cell(0, 6, body)
        self.ln()

    def add_dataframe_table(self, df):
        if df.empty:
            self.cell(0, 10, "Tidak ada data availabel.", new_x="LMARGIN", new_y="NEXT")
            return

        self.set_font(self.theme['font_body'], size=9)
        
        # Theme Settings
        bg_header = self.theme['header_bg'] if self.theme['table_fill_header'] else None
        txt_header = self.theme['header_txt'] if self.theme['table_fill_header'] else (0,0,0)
        
        # Zebra Striping
        stripe_color = self.theme['stripe_bg']
        
        # Prepare data
        table_data = [df.columns.tolist()] + df.astype(str).values.tolist()
        
        # Render Table
        with self.table(
            borders_layout=self.theme['table_borders'],
            cell_fill_color=stripe_color,
            cell_fill_mode="ROWS", # Zebra striping
            text_align="LEFT"
        ) as table:
            # Header Row
            header = table.row()
            for col_name in table_data[0]:
                cell = header.cell(col_name)
                # Apply Header Style manually if needed for specialized font color
                if self.theme['table_fill_header']:
                    # fpdf2 table headers auto-style is tricky, we rely on general settings or simple render
                    pass 
            
            # Data Rows
            for data_row in table_data[1:]:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

    def add_chapter_section(self, title, df=None, columns=None, body_text=None, new_page=False):
        """Helper to add a standard report section (Title + Body/Table)."""
        if new_page and self.get_y() > 250:
            self.add_page()
        elif new_page and self.page_no() > 1:
            # Smart page break if strictly required, but usually handled by flow
            pass
            
        self.chapter_title(title)
        
        if body_text:
            self.chapter_body(body_text)
            
        if df is not None and not df.empty:
            valid_cols = [c for c in columns if c in df.columns] if columns else df.columns.tolist()
            self.add_dataframe_table(df[valid_cols])


def create_pdf_report(metrics: dict, df_kec: pd.DataFrame, df_pusk: pd.DataFrame, df_common: pd.DataFrame, n_stats: dict, theme_name='Modern Minimalist') -> bytes:
    """Legacy function for Standard Dashboard Report."""
    pdf = PDFReport(theme_name=theme_name)
    pdf.add_page()
    
    # 1. Ringkasan Eksekutif
    summary = (
        f"Total File Report: {metrics.get('total_file', 0)}\n"
        f"Total Unit Puskesmas: {metrics.get('total_pusk', 0)}\n"
        f"Total Kasus Terdata: {metrics.get('total_kasus', 0):,}\n"
    )
    pdf.add_chapter_section("1. Ringkasan Eksekutif", body_text=summary)
    
    # 2. Top Kecamatan
    pdf.add_chapter_section(
        f"2. Top {n_stats['kec']} Penyakit per Kecamatan", 
        df=df_kec, 
        columns=['Kecamatan', 'Jenis Penyakit', 'Total_Kasus']
    )
        
    # 3. Top Puskesmas
    pdf.add_page()
    pdf.add_chapter_section(
        f"3. Top {n_stats['pusk']} Penyakit per Puskesmas",
        df=df_pusk,
        columns=['Puskesmas', 'Jenis Penyakit', 'Total_Kasus']
    )

    # 4. Analisis Umum
    pdf.ln(5)
    pdf.add_chapter_section(
        f"4. Analisis Penyakit Dominan (Top {n_stats['umum']})",
        df=df_common,
        columns=['Jenis Penyakit', 'Frekuensi', 'Status']
    )

    return pdf.output()

def create_custom_pdf(config: dict, data: dict, theme_name='Modern Minimalist') -> bytes:
    """
    Generate Custom PDF based on user configuration.
    Refactored for cleanliness and modularity.
    """
    pdf = PDFReport(theme_name=theme_name)
    pdf.add_page()

    # --- COVER / TITLE PAGE ---
    title = config.get('title', 'Laporan Custom Rekap Data')
    
    # Manual Title Rendering for Cover
    pdf.set_y(pdf.get_y() + 10)
    pdf.set_font(pdf.theme['font_header'], 'B', 18)
    
    # Title Color Logic
    if theme_name == 'Formal Monochrome':
        pdf.set_text_color(0, 0, 0)
    else:
        r,g,b = pdf.theme['header_bg']
        pdf.set_text_color(r,g,b)
        
    pdf.cell(0, 10, title, align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_text_color(0,0,0) # Reset color

    # --- DYNAMIC CHAPTERS ---
    chapter_num = 1
    
    # Helper to condense logic
    def process_section(key, df_key, title_fmt, cols=None, force_new_page=False):
        nonlocal chapter_num
        if config.get(key) and df_key in data and not data[df_key].empty:
            if force_new_page and pdf.get_y() > 240: pdf.add_page()
            
            pdf.add_chapter_section(
                f"{chapter_num}. {title_fmt}",
                df=data[df_key],
                columns=cols
            )
            chapter_num += 1

    # 1. Top N Kecamatan
    process_section('inc_kec', 'df_kec', "Top Penyakit per Kecamatan", ['Kecamatan', 'Jenis Penyakit', 'Total_Kasus'])

    # 2. Top N Puskesmas
    process_section('inc_pusk', 'df_pusk', "Top Penyakit per Puskesmas", ['Puskesmas', 'Jenis Penyakit', 'Total_Kasus'], force_new_page=True)

    # 3. Top N Umum
    process_section('inc_umum', 'df_umum', "Analisis Penyakit Dominan (Umum)", ['Jenis Penyakit', 'Frekuensi', 'Status'], force_new_page=True)

    # 4. Filter Wilayah (Drill Down)
    if config.get('inc_filter') and not data.get('df_filter', pd.DataFrame()).empty:
        pdf.add_page()
        label = config.get('filter_label', 'Wilayah')
        info = f"Wilayah: {label}\nTotal Kasus: {data['filter_metrics']['kasus']:,}\n"
        
        # Dynamic Columns
        cols = ['Jenis Penyakit', 'Total_Kasus']
        if 'Kecamatan' in data['df_filter'].columns: cols.insert(0, 'Kecamatan')
        if 'Puskesmas' in data['df_filter'].columns: cols.insert(0, 'Puskesmas')
        
        pdf.add_chapter_section(
            f"{chapter_num}. Laporan Spesifik: {label}",
            body_text=info,
            df=data['df_filter'],
            columns=cols
        )
        chapter_num += 1

    # 5. Komparasi
    if config.get('inc_compare'):
        pdf.add_page()
        pdf.chapter_title(f"{chapter_num}. Komparasi Puskesmas")
        p1, p2 = config.get('comp_names', ('A', 'B'))
        
        def sub_header(text):
            pdf.set_font(pdf.theme['font_header'], 'B', 10) # Use theme font
            pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        
        # Part A
        sub_header(f"A. {p1} (Top 10)")
        if not data['df_comp1'].empty:
            pdf.add_dataframe_table(data['df_comp1'][['Jenis Penyakit', 'Total_Kasus']])
        
        pdf.ln(5)
        # Part B
        sub_header(f"B. {p2} (Top 10)")
        if not data['df_comp2'].empty:
            pdf.add_dataframe_table(data['df_comp2'][['Jenis Penyakit', 'Total_Kasus']])
        
        pdf.ln(5)
        # Part C
        sub_header(f"C. Irisan Penyakit (Sama-sama muncul di Top 10)")
        if not data['df_comp_intersect'].empty:
            pdf.add_dataframe_table(data['df_comp_intersect'])
        else:
            pdf.chapter_body("Tidak ada irisan penyakit signifikan.")
            
        chapter_num += 1

    return pdf.output()
