# 📋 Dokumentasi Rekap Data Kesehatan

## Daftar Isi
- [Ringkasan Proyek](#ringkasan-proyek)
- [Struktur File](#struktur-file)
- [Dependencies](#dependencies)
- [Instalasi & Setup](#instalasi--setup)
- [Cara Kerja Aplikasi](#cara-kerja-aplikasi)
- [Modul & Fungsi](#modul--fungsi)
- [Interface & Fitur](#interface--fitur)
- [Flow Data](#flow-data)
- [Panduan Penggunaan](#panduan-penggunaan)
- [Troubleshooting](#troubleshooting)
- [Pengembang](#pengembang)

---

## Ringkasan Proyek

### Tujuan Aplikasi
**Rekap Data Kesehatan** adalah aplikasi web berbasis Python yang dirancang untuk menganalisis dan merekap data penyakit dari berbagai unit kesehatan (Puskesmas) di wilayah Semarang, Indonesia.

### Fitur Utama
✅ **Upload Data** - Mendukung multiple file Excel secara bersamaan  
✅ **Pembersihan Data** - Otomatis menghilangkan data sampah dan standarisasi format  
✅ **Analisis Ranking** - Menampilkan Top N penyakit per kecamatan dan puskesmas  
✅ **Analisis Dominasi** - Mengidentifikasi penyakit yang tersebar di berbagai wilayah  
✅ **Filter Fleksibel** - Include/exclude berdasarkan kategori penyakit  
✅ **Download Laporan** - Export hasil dalam format Excel atau CSV  

### Tech Stack
- **Frontend**: Streamlit (Web Framework)
- **Backend**: Python, Pandas (Data Processing)
- **Database**: File Excel (Input)
- **Output**: Excel, CSV, ZIP

---

## Struktur File

```
Rekap-Data/
├── app.py                 # Main aplikasi Streamlit
├── logic.py              # Modul pemrosesan data & logika bisnis
├── requirements.txt      # Dependencies Python
├── runtime.txt          # Informasi Python runtime
└── __pycache__/         # Cache Python (auto-generated)
```

### Penjelasan File:

| File | Fungsi | Deskripsi |
|------|--------|-----------|
| `app.py` | Main Application | Mengelola UI, state management, dan orchestration |
| `logic.py` | Business Logic | Fungsi data processing, ranking, dan analisis |
| `requirements.txt` | Dependencies | Library yang diperlukan untuk menjalankan aplikasi |
| `runtime.txt` | Runtime Config | Spesifikasi versi Python |

---

## Dependencies

### Library Python yang Digunakan:

```
pandas         - Data manipulation & analysis
openpyxl       - Read/write Excel files
streamlit      - Web framework & UI
altair<5       - Data visualization
```

### Versi Python
Python 3.8+

---

## Instalasi & Setup

### 1. Prasyarat
- Python 3.8 atau lebih tinggi
- pip (Python package manager)

### 2. Clone/Download Proyek
```bash
cd Rekap-Data
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Jalankan Aplikasi
```bash
streamlit run app.py
```

Aplikasi akan membuka di browser pada `http://localhost:8501`

---

## Cara Kerja Aplikasi

### Arsitektur Umum

```
┌─────────────────────────────────────────┐
│        USER INTERFACE (Streamlit)       │
│  - File Upload                          │
│  - Settings & Filter                    │
│  - Dashboard & Visualization            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      STATE MANAGEMENT (Session State)    │
│  - upload_key (reset uploader)          │
│  - data_processed (trigger processing)  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      DATA PROCESSING (logic.py)         │
│  - Baca & Bersihkan File                │
│  - Hitung Ranking                       │
│  - Analisis Dominasi Penyakit           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      OUTPUT & DOWNLOAD                   │
│  - Tampilkan Dashboard                  │
│  - Export Excel/CSV                     │
└─────────────────────────────────────────┘
```

### Workflow Aplikasi

```
1. WELCOME SCREEN
   └─> User upload file Excel

2. DATA LOADED
   └─> System membaca & bersihkan data
   └─> Prepare filter options
   └─> Show preview data

3. CONFIGURATION
   └─> User atur ranking & filter
   └─> Click "MULAI REKAPITULASI"

4. DATA PROCESSING
   └─> Terapkan filter (include/exclude)
   └─> Hitung ranking per kecamatan
   └─> Hitung ranking per puskesmas
   └─> Analisis penyakit umum

5. DISPLAY RESULTS
   └─> Show 4 tabs (Kecamatan, Puskesmas, Analisis, Data)
   └─> Enable download section

6. DOWNLOAD & RESET
   └─> User download hasil
   └─> User bisa reset & upload file baru
```

---

## Modul & Fungsi

### File: `logic.py`

#### 1. MAPPING_KECAMATAN (Dictionary)
**Fungsi**: Memetakan nama Puskesmas ke nama Kecamatan

**Struktur**:
```python
MAPPING_KECAMATAN = {
    'PUSKESMAS_NAME': 'KECAMATAN_NAME',
    ...
}
```

**Contoh**:
```python
'PONCOL': 'SEMARANG TENGAH'
'HALMAHERA': 'SEMARANG TIMUR'
```

**Cakupan**: 30+ Puskesmas di Semarang

---

#### 2. `baca_dan_bersihkan_file(uploaded_file)`

**Fungsi**: Membaca file Excel, membersihkan data, dan menambahkan informasi wilayah

**Input**:
- `uploaded_file`: File Excel yang di-upload (Streamlit UploadedFile object)

**Proses**:
1. **Ekstrak nama Puskesmas** dari nama file
2. **Mapping ke Kecamatan** menggunakan MAPPING_KECAMATAN
3. **Baca Excel** dengan header di baris ke-2 (index 1)
4. **Filter baris sampah** yang mengandung "TOTAL", "JUMLAH", "SUB TOTAL"
5. **Hitung total kasus** dari kolom D s/d AY (48 kolom data bulanan)
6. **Standardisasi teks** (uppercase, strip whitespace)
7. **Pilih kolom penting**: Jenis Penyakit, ICD X, Total_Kasus, Puskesmas, Kecamatan
8. **Filter data kosong**: Hanya ambil baris dengan Total_Kasus > 0

**Output**:
```python
DataFrame dengan kolom:
- Jenis Penyakit (str): Nama penyakit (uppercase)
- ICD X (str): Kode ICD-X (uppercase)
- Total_Kasus (int): Jumlah total kasus
- Puskesmas (str): Nama Puskesmas
- Kecamatan (str): Nama Kecamatan
```

**Error Handling**: 
- Jika file bermasalah, display pesan error di Streamlit tanpa crash aplikasi
- Return DataFrame kosong jika gagal

**Contoh Hasil**:
```
   Jenis Penyakit          ICD X  Total_Kasus      Puskesmas        Kecamatan
0      DEMAM BERDARAH      A90         15        PONCOL          SEMARANG TENGAH
1      MALARIA              B54         8         PONCOL          SEMARANG TENGAH
```

---

#### 3. `hitung_ranking(df, group_cols, top_n=10)`

**Fungsi**: Menghitung Top N penyakit berdasarkan grup (Kecamatan/Puskesmas)

**Input**:
- `df`: DataFrame dengan minimal kolom: Jenis Penyakit, ICD X, Total_Kasus, dan kolom group
- `group_cols`: List nama kolom grup (contoh: ['Kecamatan'] atau ['Puskesmas'])
- `top_n`: Jumlah ranking yang ditampilkan (default: 10)

**Proses**:
1. **Group by grup + Jenis Penyakit + ICD X**
2. **Sum Total_Kasus** untuk setiap kombinasi (menggabungkan data yang sama)
3. **Sort by Total_Kasus descending** dalam setiap grup
4. **Ambil Top N** dari setiap grup
5. **Reset index mulai dari 1** (bukan 0)

**Output**:
```python
DataFrame terindeks 1 dengan kolom:
- (Kolom grup): Nama kecamatan/puskesmas
- Jenis Penyakit: Nama penyakit
- ICD X: Kode ICD-X
- Total_Kasus: Jumlah kasus (total per grup)
```

**Contoh Hasil** (group_cols=['Kecamatan'], top_n=3):
```
  Kecamatan           Jenis Penyakit  ICD X  Total_Kasus
1 SEMARANG TENGAH    DEMAM BERDARAH   A90     120
2 SEMARANG TENGAH    MALARIA          B54      85
3 SEMARANG TENGAH    DIARE            A09      45
4 SEMARANG TIMUR     DEMAM BERDARAH   A90     150
5 SEMARANG TIMUR     ISPA             J06     100
6 SEMARANG TIMUR     PNEUMONIA        J18      60
```

---

#### 4. `cari_penyakit_umum(df_ranking, group_col, top_n=5)`

**Fungsi**: Mencari penyakit yang paling sering muncul di Top N berbagai wilayah

**Input**:
- `df_ranking`: DataFrame hasil dari `hitung_ranking()` (sudah ranked)
- `group_col`: Nama kolom grup (string) - 'Kecamatan' atau 'Puskesmas'
- `top_n`: Jumlah hasil yang ditampilkan (default: 5)

**Proses**:
1. **Hitung total grup** (jumlah unik kecamatan/puskesmas)
2. **Count frekuensi** penyakit muncul di berbagai grup
3. **Sum total kasus** per penyakit dari semua grup
4. **Buat status**:
   - "LOLOS (Ada di SEMUA)" jika muncul di semua grup
   - "HAMPIR (Absen di X unit)" jika tidak di semua grup
5. **Sort by frekuensi dan total kasus descending**
6. **Ambil Top N penyakit**
7. **Reset index mulai dari 1**

**Output**:
```python
DataFrame terindeks 1 dengan kolom:
- Jenis Penyakit: Nama penyakit
- ICD X: Kode ICD-X
- Frekuensi: Berapa kali muncul di ranking
- Total_Kasus: Total kasus dari semua grup
- Status: LOLOS atau HAMPIR
```

**Contoh Hasil** (group_col='Kecamatan', total_groups=16):
```
  Jenis Penyakit  ICD X  Frekuensi  Total_Kasus  Status
1 DEMAM BERDARAH  A90      16       2500         LOLOS (Ada di SEMUA)
2 MALARIA         B54      15       1800         HAMPIR (Absen di 1 unit)
3 DIARE           A09      14       1200         HAMPIR (Absen di 2 unit)
```

**Interpretasi Status**:
- **LOLOS**: Penyakit yang ada di semua wilayah (penyakit endemic/umum)
- **HAMPIR**: Penyakit yang hampir di semua wilayah (nearly endemic)

---

### File: `app.py`

#### State Management
**Variables**:
- `st.session_state.upload_key`: Counter untuk reset uploader (default: 0)
- `st.session_state.data_processed`: Flag proses (default: False)

**Fungsi `reset_app()`**:
- Increment `upload_key` (reset file uploader)
- Set `data_processed` ke False
- Clear cache

---

#### Konfigurasi Halaman
```python
st.set_page_config(
    page_title="Rekap Data Kesehatan",
    page_icon="🏥",
    layout="wide"
)
```

**Parameters**:
- `page_title`: Judul di browser tab
- `page_icon`: Emoji di browser tab
- `layout`: Layout wide untuk lebih banyak ruang

---

#### Custom CSS Styling
Aplikasi menggunakan custom CSS untuk styling:

**Elemen yang di-style**:
1. **Typography**: Font, ukuran, warna heading
2. **Metrics Box**: Background, border, padding
3. **Sidebar**: Dark theme (#2C3E50)
4. **Buttons**: Primary & secondary style
5. **Sidebar Info Box**: Info styling dengan border left
6. **Footer**: Fixed position di bawah

**Color Scheme**:
- Primary: #2C3E50 (dark blue)
- Accent: #1ABC9C (teal)
- Background: #F0F2F6, #ECF0F1
- Text: #31333F, #555

---

#### Fungsi `style_zigzag_groups(df, group_col)`

**Fungsi**: Styling alternating row colors untuk visual grouping

**Parameter**:
- `df`: DataFrame untuk di-style
- `group_col`: Nama kolom untuk grouping

**Output**:
- DataFrame.style object dengan alternating background colors (#1A1A1A, #333333)

**Error Handling**: Jika group_col tidak ada, return df tanpa style

---

#### Fungsi `process_single_file(file)` [CACHED]

**Decorator**: `@st.cache_data(show_spinner=False)`

**Fungsi**: Wrapper untuk caching hasil proses file individual

**Parameter**: `file` (UploadedFile dari Streamlit)

**Process**:
1. Reset file pointer ke awal (`file.seek(0)`)
2. Call `baca_dan_bersihkan_file(file)` dari logic.py

**Keuntungan Caching**:
- Menghindar proses file yang sama berkali-kali
- Mempercepat load data ketika settings berubah
- Hemat resource

---

## Interface & Fitur

### 1. Sidebar - Input Data Section

**Header**: "📂 1. Input Data"

**Komponen**:
```
┌─────────────────────────────────────┐
│ Ketentuan File Excel (Info Box):    │
│ 1. Format wajib .xlsx               │
│ 2. Header di Baris ke-2 (Index 1)   │
│ 3. Data Penyakit kolom D s/d AY     │
│ 4. Nama file = Nama Puskesmas       │
└─────────────────────────────────────┘
│ File Uploader (Multiple)            │
└─────────────────────────────────────┘
│ Status: "✅ X File Terbaca"         │
└─────────────────────────────────────┘
```

**Validasi File**:
- Type: .xlsx only
- Multiple files: Ya
- Feedback: Success/Caption message

---

### 2. Main Content - Welcome Screen

**Tampil jika**: File belum di-upload

```
┌─────────────────────────────────────┐
│                                     │
│    🏥 Rekap Data Penyakit           │
│    Dashboard rekapitulasi data      │
│    penyakit per kecamatan dan...    │
│                                     │
├─────────────────────────────────────┤
│                                     │
│    Welcome!                         │
│    Silakan upload file Excel...     │
│                                     │
└─────────────────────────────────────┘
```

---

### 3. Sidebar - Settings & Filter Section

**Header**: "⚙️ 2. Pengaturan & Filter"

**Muncul setelah**: File di-upload

#### 3a. Ranking Settings
```
┌─ Ranking (Top N) ──────────┐
│ Kecamatan:  [10] spinner   │
│ Puskesmas:  [10] spinner   │
│ Analisis Umum: [5] spinner │
└────────────────────────────┘
```

**Parameter**:
- `top_n_kec_val`: Ranking per kecamatan (1-25, default 10)
- `top_n_pusk_val`: Ranking per puskesmas (1-25, default 10)
- `top_n_common_val`: Penyakit umum (1-25, default 5)

---

#### 3b. Data Filter

**Tab 1: Include Filter**
```
┌─ ✅ Include ────────────────┐
│ HANYA tampilkan:            │
│ Huruf Awal: [M] [A] [B]     │
│ Penyakit: [A90-DEMAM BD]    │
│            [B54-MALARIA]    │
└─────────────────────────────┘
```

**Tab 2: Exclude Filter**
```
┌─ ❌ Exclude ────────────────┐
│ SEMBUNYIKAN data:           │
│ Huruf Awal: [C] [D]         │
│ Penyakit: [J06-ISPA]        │
└─────────────────────────────┘
```

**Filter Logic**:
- **Include**: OR logic (Huruf ATAU Penyakit)
  - Jika include aktif: tampilkan HANYA yang dipilih
  - Jika include kosong: tampilkan SEMUA

- **Exclude**: AND logic (hapus semua yang dipilih)
  - Dikerjakan SETELAH include

**Example Filter Hasil**:
- Include: [Huruf A] → Hanya penyakit huruf A
- Exclude: [A90] → Exclude A90 specific
- Hasil: Penyakit huruf A kecuali A90

---

#### 3c. Submit Button

```
┌────────────────────────────┐
│ MULAI REKAPITULASI         │
│ [Primary Button]           │
└────────────────────────────┘
```

**Action**:
- Set `st.session_state.data_processed = True`
- Trigger dashboard display & calculation

---

### 4. Main Content - Ready State

**Tampil jika**: File di-upload TAPI tombol belum ditekan

```
┌─ Ready Box ───────────────────┐
│ ✅ X File Berhasil Dimuat     │
│ Data siap diproses. Silakan   │
│ atur Ranking dan Filter,      │
│ lalu klik "MULAI REKAPITULASI"│
└───────────────────────────────┘

┌─ Preview Data (Expander) ─────┐
│ 📊 [Preview 5 Baris Awal]     │
│ ┌─────────────────────────┐   │
│ │ Jenis Penyakit | ...    │   │
│ │ DEMAM BERDARAH | ...    │   │
│ └─────────────────────────┘   │
└───────────────────────────────┘
```

---

### 5. Main Content - Dashboard

**Tampil jika**: Tombol "MULAI REKAPITULASI" ditekan

#### 5a. Metrics Row
```
┌──────────────┬──────────────┬──────────────┐
│  Total File  │ Unit Puskesmas│ Total Kasus  │
│      5       │      22       │    2,500     │
└──────────────┴──────────────┴──────────────┘
```

**Metrics**:
- Total File: Jumlah file yang di-upload
- Unit Puskesmas: Unique puskesmas setelah filter
- Total Kasus: Sum semua kasus setelah filter

---

#### 5b. Filter Status Info
```
ℹ️ Filter: Aktif | Ranking: Kec(10), Pusk(10), Umum(5)
```

**Info**:
- Status filter: Aktif/Non-Aktif
- Current settings display

---

#### 5c. Dashboard Tabs

```
┌─ Tab Navigation ──────────────────────┐
│ 🏢 Top 10 Kecamatan
│ 🏥 Top 10 Puskesmas
│ 🦠 Top 5 Umum
│ 📂 Data Mentah
└───────────────────────────────────────┘
```

**Tab 1: Top N Kecamatan**
```
Kolom:
- Index (1-based)
- Kecamatan: Nama kecamatan
- Jenis Penyakit: Nama penyakit
- ICD X: Kode ICD-X
- Total_Kasus: Jumlah kasus

Styling: Alternating row colors per kecamatan (zigzag)
Height: 500px dengan scroll
```

**Tab 2: Top N Puskesmas**
```
Kolom:
- Index (1-based)
- Puskesmas: Nama puskesmas
- Jenis Penyakit: Nama penyakit
- ICD X: Kode ICD-X
- Total_Kasus: Jumlah kasus

Styling: Alternating row colors per puskesmas (zigzag)
Height: 500px dengan scroll
```

**Tab 3: Top N Umum (Analisis Dominasi)**
```
Dua kolom side-by-side:

[Kolom Kiri]                [Kolom Kanan]
Persebaran di Kecamatan     Persebaran di Puskesmas
┌──────────────────┐        ┌──────────────────┐
│ Jenis Penyakit   │        │ Jenis Penyakit   │
│ ICD X            │        │ ICD X            │
│ Frekuensi        │        │ Frekuensi        │
│ Total_Kasus      │        │ Total_Kasus      │
│ Status           │        │ Status           │
└──────────────────┘        └──────────────────┘
```

**Status Values**:
- "LOLOS (Ada di SEMUA)" - Present everywhere
- "HAMPIR (Absen di X unit)" - Missing from X locations

**Tab 4: Data Mentah (Terfilter)**
```
Menampilkan full filtered data:
- Jenis Penyakit
- ICD X
- Total_Kasus
- Puskesmas
- Kecamatan

(Tidak termasuk Label_Filter dan Alpha_Filter - internal use only)
```

---

#### 5d. Download Section

```
┌─ Download Hasil ──────────────────┐
│ Pilih Data:                       │
│ ☑ Semua Data                     │
│ ☐ Data Mentah                    │
│ ☐ Top 10 Kecamatan               │
│ ☐ Top 10 Puskesmas               │
│ ☐ Analisis Umum                  │
│                                   │
│ Format:                           │
│ ◉ Excel (.xlsx)  ○ CSV (.csv)    │
│                                   │
│ [Download Excel] (Primary Button) │
└───────────────────────────────────┘
```

**Logic**:
- **Pilih Data**: Default "Semua Data"
- **Format Options**:
  - Excel: Single file .xlsx dengan multiple sheets
  - CSV Single: 1 file CSV (jika 1 data dipilih)
  - CSV Multiple: .zip berisi multiple CSV files

**Sheet Names** (Excel):
- Nama asli dipotong 30 char, spasi → underscore, uppercase
- Contoh: "Top 10 Kecamatan" → "TOP_10_KECAMATAN"

---

### 6. Reset Button

```
┌────────────────────────────┐
│ Reset / Proses File Baru   │
│ [Secondary Button]         │
└────────────────────────────┘
```

**Action**:
- Call `reset_app()`
- Reset upload_key (clear uploader)
- Reset data_processed flag
- Clear cache
- Rerun aplikasi

---

### 7. Footer

```
Developed by Muhammad Dzaky & Gian Adiansyah
```

---

## Flow Data

### Alur Lengkap Upload hingga Download

```
START
  │
  ├─> [1] USER UPLOAD FILE
  │   └─> Streamlit menerima file(s) .xlsx
  │
  ├─> [2] SYSTEM LOAD DATA
  │   ├─> For each file:
  │   │  ├─> process_single_file(file)
  │   │  │  └─> baca_dan_bersihkan_file()
  │   │  │     ├─ Read Excel (header=1)
  │   │  │     ├─ Extract puskesmas name
  │   │  │     ├─ Map to kecamatan
  │   │  │     ├─ Remove trash rows
  │   │  │     ├─ Sum columns D-AY
  │   │  │     ├─ Standardize text
  │   │  │     ├─ Select columns
  │   │  │     └─ Filter zero cases
  │   │  └─> Return cleaned DataFrame
  │   └─> Concat all DataFrames
  │
  ├─> [3] PREPARE FILTER OPTIONS
  │   ├─> Create Label_Filter (ICD X + Jenis Penyakit)
  │   ├─> Create Alpha_Filter (First char of ICD X)
  │   └─> Get unique values for multiselect
  │
  ├─> [4] SHOW PREVIEW
  │   └─> Display preview 5 rows in expander
  │
  ├─> [5] USER CONFIGURE SETTINGS
  │   ├─> Set top_n_kec_val (1-25)
  │   ├─> Set top_n_pusk_val (1-25)
  │   ├─> Set top_n_common_val (1-25)
  │   ├─> Set include filters
  │   └─> Set exclude filters
  │
  ├─> [6] USER CLICK "MULAI REKAPITULASI"
  │   └─> data_processed = True
  │
  ├─> [7] APPLY FILTERS
  │   ├─> Include Logic: OR conditions
  │   │  ├─ If include_alpha: mask |= alpha match
  │   │ └─ If include_list: mask |= penyakit match
  │   └─> Exclude Logic: AND remove
  │      ├─ Remove matching alpha
  │      └─ Remove matching penyakit
  │
  ├─> [8] CHECK FILTER RESULT
  │   ├─> If empty: Show error → back to [5]
  │   └─> If not empty: Continue
  │
  ├─> [9] CALCULATE RANKINGS
  │   ├─> hitung_ranking(filtered_df, ['Kecamatan'], top_n)
  │   ├─> hitung_ranking(filtered_df, ['Puskesmas'], top_n)
  │   ├─> cari_penyakit_umum(ranking_pusk, 'Puskesmas', top_n)
  │   └─> cari_penyakit_umum(ranking_kec, 'Kecamatan', top_n)
  │
  ├─> [10] DISPLAY DASHBOARD
  │   ├─> Show metrics (Files, Units, Cases)
  │   ├─> Show filter status
  │   ├─> Show 4 tabs with data & styling
  │   └─> Show download section
  │
  ├─> [11] USER SELECT DATA FOR DOWNLOAD
  │   ├─> Choose what to download (default: Semua Data)
  │   └─> Choose format (Excel or CSV)
  │
  ├─> [12] USER CLICK DOWNLOAD BUTTON
  │   ├─> If Excel: Create .xlsx with multiple sheets
  │   ├─> If CSV single: Download .csv
  │   └─> If CSV multiple: Create .zip with CSVs
  │
  ├─> [13] USER CLICK RESET
  │   └─> reset_app() → Back to START
  │
END
```

### Data Transformation Mapping

```
RAW EXCEL FILE
  │
  ├─> Read (header=1)
  │
  ├─> Clean Columns & Rows
  │   ├─ Remove trash rows
  │   ├─ Sum D-AY columns
  │   └─ Standardize text
  │
  ├─> Add Derived Columns
  │   ├─ Total_Kasus (sum)
  │   ├─ Puskesmas (from filename)
  │   ├─ Kecamatan (from mapping)
  │   ├─ Label_Filter (ICD + Penyakit)
  │   └─ Alpha_Filter (first char)
  │
INTERMEDIATE DATA (master_df)
  │
  ├─> Apply Filters
  │   ├─ Include filters
  │   └─ Exclude filters
  │
FILTERED DATA (filtered_df)
  │
  ├─> Group & Rank
  │   ├─ Group by Kecamatan
  │   ├─ Group by Puskesmas
  │   └─ Group by (Jenis + ICD) for dominasi
  │
FINAL RANKED DATA
  │
  ├─> Display in Dashboard
  │   ├─ Metrics
  │   ├─ Tab: Kecamatan
  │   ├─ Tab: Puskesmas
  │   ├─ Tab: Analisis Umum
  │   └─ Tab: Data Mentah
  │
  └─> Download (Excel/CSV)
```

---

## Panduan Penggunaan

### Scenario 1: Upload & View Basic Report

**Step-by-step**:

1. **Start aplikasi**
   ```bash
   streamlit run app.py
   ```

2. **Upload file**
   - Klik upload area di sidebar kiri
   - Pilih file Excel (.xlsx)
   - Bisa multiple files sekaligus
   - Tunggu loading selesai

3. **Lihat preview**
   - Expand "Intip Data Mentah"
   - Review 5 baris awal data

4. **Biarkan setting default**
   - Top Kecamatan: 10
   - Top Puskesmas: 10
   - Top Analisis: 5
   - Filter: (kosong)

5. **Klik "MULAI REKAPITULASI"**
   - Tunggu dashboard render
   - Lihat 4 tabs hasil

6. **Download hasil**
   - Select data: "Semua Data"
   - Select format: "Excel (.xlsx)"
   - Click "Download Excel"

---

### Scenario 2: Filter Specific Diseases

**Tujuan**: Lihat hanya penyakit huruf A (kategori Infections)

**Steps**:

1. Upload file (seperti Scenario 1)

2. Di sidebar, section "⚙️ 2. Pengaturan & Filter":
   - Klik tab "✅ Include"
   - Di "Huruf Awal": select "[A]"
   - (Penyakit field: kosongkan)

3. Klik "MULAI REKAPITULASI"

4. Result: Dashboard hanya tampilkan penyakit kategori A

5. Download hasil dengan penyakit A saja

---

### Scenario 3: Exclude Tertentu & High Top N

**Tujuan**: Lihat Top 15 per puskesmas, exclude penyakit J06 & J18

**Steps**:

1. Upload file

2. Di sidebar settings:
   - Ranking: Ubah "Puskesmas" dari 10 ke 15
   - Filter tab "❌ Exclude"
   - Di "Penyakit": Cari dan select "J06 - ISPA" dan "J18 - PNEUMONIA"

3. Klik "MULAI REKAPITULASI"

4. Result: Top 15 per puskesmas tanpa ISPA dan PNEUMONIA

5. Download hasil

---

### Scenario 4: Analisis Penyakit Umum

**Tujuan**: Temukan penyakit yang muncul di semua kecamatan (endemic)

**Steps**:

1. Upload file

2. Di sidebar settings:
   - Top Analisis Umum: Ubah ke 15 (lebih banyak)
   - Filter: (kosongkan - lihat semua)

3. Klik "MULAI REKAPITULASI"

4. Buka tab "🦠 Top 5 Umum"

5. Lihat kolom "Status":
   - "LOLOS (Ada di SEMUA)" = Penyakit endemic
   - "HAMPIR (Absen di X unit)" = Near endemic

6. Lihat "Frekuensi" untuk melihat di berapa unit penyakit tersebut ada

---

### Format Ketentuan File Excel

**Struktur file yang diterima**:

```
Row 1 (skipped):     Bisa header atau title bebas
Row 2 (header):      Jenis Penyakit | ICD X | Kolom A | Kolom B | ... | Kolom AY
Row 3-N (data):      Data penyakit dengan kasus per kolom

Kolom mapping:
- Column A: Jenis Penyakit (required)
- Column B: ICD X (required)
- Column C: Bisa apa saja (ignored)
- Column D-AY: Data kasus (48 kolom = 12 bulan x 4 minggu)
```

**Contoh struktur file**:

```
Laporan Puskesmas PONCOL - Tahun 2024
Jenis Penyakit | ICD X | Data Awal | Data 1 | Data 2 | ... | Data AY
DEMAM BERDARAH | A90   | 5 | 3 | 7 | ... | 2
MALARIA | B54 | 0 | 2 | 1 | ... | 0
TOTAL | | 5 | 5 | 8 | ... | 2        <-- DIHAPUS (trash row)
```

**Validasi**:
- File HARUS .xlsx (Excel modern)
- Header HARUS di baris ke-2
- Kolom D-AY HARUS berisi angka (atau dikosongkan)
- Nama file harus berisi nama Puskesmas yang ada di MAPPING_KECAMATAN

**Error yang mungkin**:
- ❌ .xls atau .csv: Tidak diterima
- ❌ Header bukan di baris 2: Data akan salah
- ❌ Nama puskesmas tidak terdaftar: Kecamatan jadi "TIDAK TERDAFTAR"
- ❌ Kolom D-AY kosong/text: Akan direset jadi 0

---

## Troubleshooting

### Error: "File tidak terbaca"

**Penyebab**:
1. Format file bukan .xlsx
2. File corrupt/tercemar

**Solusi**:
- Cek format file (.xlsx?)
- Buka file di Excel, save ulang as .xlsx
- Coba file lain dulu

---

### Error: "Kolom 'Jenis Penyakit' tidak ditemukan"

**Penyebab**:
- Header bukan di baris ke-2
- Nama kolom berbeda (case sensitive)

**Solusi**:
- Pastikan header di Row 2 (index 1)
- Kolom A harus dynamically named (bukan dengan header custom)
- Check file format ulang

---

### Error: "Gagal memproses file [nama file]"

**Penyebab**:
- File corrupted
- Data format salah
- Kolom tidak standard

**Solusi**:
- Lihat error message di alert
- Check struktur file vs ketentuan
- Edit file sesuai template
- Upload file lain untuk test

---

### Dashboard kosong / Filter result 0

**Penyebab**:
- Filter terlalu ketat
- Data tidak ada setelah filter
- Include + Exclude conflict

**Solusi**:
- Clear filter (biarkan kosong)
- Click "MULAI REKAPITULASI" lagi
- Cek apakah file ada data

---

### Download tidak bisa / file corrupt

**Penyebab**:
- Browser block download
- Format salah selected
- Memory issue (file terlalu besar)

**Solusi**:
- Allow popup/download di browser
- Coba format lain (CSV vs Excel)
- Filter lebih sedikit data dulu
- Restart browser

---

### Aplikasi lambat / freeze

**Penyebab**:
- File terlalu besar (1000+ rows)
- Banyak file di-load
- Cache belum clear

**Solusi**:
- Reduce file size
- Upload 5 file at a time dulu
- Click "Reset" untuk clear cache
- Restart aplikasi

---

## Pengembang

### Tim Developer:
- **Muhammad Dzaky** - Backend Logic & Data Processing
- **Gian Adiansyah** - Frontend UI & Streamlit Integration

### Informasi Kontak:
- Lokasi: BKPTK, Semarang
- Tahun: 2024-2025

### Teknologi Stack:
- **Language**: Python 3.8+
- **Web Framework**: Streamlit
- **Data Processing**: Pandas, OpenPyXL
- **Deployment**: Streamlit Cloud atau Local

### Future Enhancement Ideas:
1. Database integration (PostgreSQL/MySQL)
2. User authentication & role management
3. Automated report scheduling
4. Advanced visualization (Plotly/Altair)
5. API integration dengan sistem kesehatan
6. Mobile app version
7. Real-time data sync
8. Export to PDF format

---

## License & Terms

Aplikasi ini dikembangkan khusus untuk keperluan rekapitulasi data kesehatan di Semarang. Penggunaan dan modifikasi sesuai kebutuhan internal organisasi.

---

**Dokumentasi Terakhir Di-update**: 26 Januari 2026  
**Versi Dokumentasi**: 1.0

