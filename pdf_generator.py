from fpdf import FPDF
from datetime import datetime
import pandas as pd

class PDFReport(FPDF):
    def header(self):
        # Title
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, 'Laporan Rekapitulasi Data Penyakit', align='C', new_x="LMARGIN", new_y="NEXT")
        
        # Subtitle
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()}/{{nb}}', align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def add_dataframe_table(self, df):
        """
        Render dataframe as a table using fpdf2's table context manager.
        """
        if df.empty:
            self.cell(0, 10, "Tidak ada data.", new_x="LMARGIN", new_y="NEXT")
            return

        self.set_font("helvetica", size=9)
        
        # Convert all data to string
        vals = [df.columns.tolist()] + df.astype(str).values.tolist()
        
        with self.table() as table:
            for data_row in vals:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)

def create_pdf_report(metrics, df_kec, df_pusk, df_common, n_stats):
    pdf = PDFReport()
    pdf.add_page()
    
    # 1. Ringkasan
    pdf.chapter_title("1. Ringkasan Eksekutif")
    summary = (
        f"Total File: {metrics['total_file']}\n"
        f"Total Unit Puskesmas: {metrics['total_pusk']}\n"
        f"Total Kasus: {metrics['total_kasus']:,}\n"
    )
    pdf.chapter_body(summary)
    
    # 2. Top Kecamatan
    title_kec = f"2. Top {n_stats['kec']} Penyakit per Kecamatan"
    pdf.chapter_title(title_kec)
    if not df_kec.empty:
        # Ambil kolom esensial. Kita TIDAK melimit head(20) lagi, melainkan semua data sesuai N user.
        df_view = df_kec[['Kecamatan', 'Jenis Penyakit', 'Total_Kasus']]
        pdf.add_dataframe_table(df_view)
        
    # 3. Top Puskesmas
    pdf.add_page()
    title_pusk = f"3. Top {n_stats['pusk']} Penyakit per Puskesmas"
    pdf.chapter_title(title_pusk)
    if not df_pusk.empty:
        df_view = df_pusk[['Puskesmas', 'Jenis Penyakit', 'Total_Kasus']]
        pdf.add_dataframe_table(df_view)

    # 4. Analisis Umum
    pdf.ln(5)
    title_umum = f"4. Analisis Penyakit Dominan (Top {n_stats['umum']})"
    pdf.chapter_title(title_umum)
    if not df_common.empty:
        df_view = df_common[['Jenis Penyakit', 'Frekuensi', 'Status']]
        pdf.add_dataframe_table(df_view)

    return pdf.output()
