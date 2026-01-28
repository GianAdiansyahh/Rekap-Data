from fpdf import FPDF
from datetime import datetime
import pandas as pd

class PDFReport(FPDF):
    """
    Custom FPDF class for generating Recap Reports.
    Includes custom header, footer, and utility methods for tables.
    """
    
    def header(self):
        # Title
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Laporan Rekapitulasi Data Penyakit', align='C', new_x="LMARGIN", new_y="NEXT")
        
        # Subtitle
        self.set_font('helvetica', 'I', 10)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f'Generated on: {timestamp}', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}/{{nb}}', align='C')

    def chapter_title(self, title):
        """Render a chapter title with background fill."""
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def chapter_body(self, body):
        """Render a text body paragraph."""
        self.set_font('helvetica', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def add_dataframe_table(self, df):
        """
        Render a pandas DataFrame as a PDF table.
        Uses fpdf2's robust table context manager.
        """
        if df.empty:
            self.cell(0, 10, "Tidak ada data availabel.", new_x="LMARGIN", new_y="NEXT")
            return

        self.set_font("helvetica", size=9)
        
        # Prepare data: Header + Rows (converted to string)
        table_data = [df.columns.tolist()] + df.astype(str).values.tolist()
        
        # Render table
        with self.table() as table:
            for data_row in table_data:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

def create_pdf_report(metrics: dict, df_kec: pd.DataFrame, df_pusk: pd.DataFrame, df_common: pd.DataFrame, n_stats: dict) -> bytes:
    """
    Main entry point to generate the PDF report.
    Returns the PDF content as bytes.
    """
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Ringkasan Eksekutif
    pdf.chapter_title("1. Ringkasan Eksekutif")
    summary = (
        f"Total File Report: {metrics.get('total_file', 0)}\n"
        f"Total Unit Puskesmas: {metrics.get('total_pusk', 0)}\n"
        f"Total Kasus Terdata: {metrics.get('total_kasus', 0):,}\n"
    )
    pdf.chapter_body(summary)
    
    # 2. Top Kecamatan
    title_kec = f"2. Top {n_stats['kec']} Penyakit per Kecamatan"
    pdf.chapter_title(title_kec)
    if not df_kec.empty:
        # Select valid columns for view
        cols = ['Kecamatan', 'Jenis Penyakit', 'Total_Kasus']
        # Filter existing columns to avoid key error if schema changes
        valid_cols = [c for c in cols if c in df_kec.columns]
        pdf.add_dataframe_table(df_kec[valid_cols])
        
    # 3. Top Puskesmas
    pdf.add_page()
    title_pusk = f"3. Top {n_stats['pusk']} Penyakit per Puskesmas"
    pdf.chapter_title(title_pusk)
    if not df_pusk.empty:
        cols = ['Puskesmas', 'Jenis Penyakit', 'Total_Kasus']
        valid_cols = [c for c in cols if c in df_pusk.columns]
        pdf.add_dataframe_table(df_pusk[valid_cols])

    # 4. Analisis Umum
    pdf.ln(5)
    title_umum = f"4. Analisis Penyakit Dominan (Top {n_stats['umum']})"
    pdf.chapter_title(title_umum)
    if not df_common.empty:
        cols = ['Jenis Penyakit', 'Frekuensi', 'Status']
        valid_cols = [c for c in cols if c in df_common.columns]
        pdf.add_dataframe_table(df_common[valid_cols])

    return pdf.output()
