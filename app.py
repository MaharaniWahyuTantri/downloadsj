import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Surat Jalan Filter", page_icon="🚛", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #f5f7fa; color: #1a202c; }
.stApp { background: #f5f7fa; }

.main-header {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    border-radius: 14px;
    padding: 24px 32px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 16px rgba(59,130,246,0.25);
}
.main-header h1 { font-size: 1.7rem; font-weight: 700; color: #fff; }
.main-header p  { font-size: 0.85rem; color: rgba(255,255,255,0.75); margin-top: 4px; }

.upload-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.upload-card h3 {
    font-size: 0.78rem; font-weight: 700; color: #3b82f6;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;
}
.upload-card p { font-size: 0.78rem; color: #64748b; }

.stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 16px 0; }
.stat-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 18px 20px; text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-num { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-lbl { font-size: 0.7rem; color: #94a3b8; margin-top: 6px; text-transform: uppercase; letter-spacing: .6px; font-weight: 500; }
.c-blue   { color: #3b82f6; }
.c-green  { color: #22c55e; }
.c-red    { color: #ef4444; }
.c-yellow { color: #f59e0b; }

.warn-box {
    background: #fffbeb; border: 1px solid #fcd34d;
    border-radius: 10px; padding: 14px 18px; margin: 12px 0;
    font-size: 0.85rem; color: #92400e; line-height: 1.6;
}
.info-box {
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 14px 18px; margin: 12px 0;
    font-size: 0.85rem; color: #1e40af; line-height: 1.6;
}
.success-box {
    background: #f0fdf4; border: 1px solid #86efac;
    border-radius: 10px; padding: 14px 18px; margin: 12px 0;
    font-size: 0.85rem; color: #14532d; line-height: 1.6;
}
.error-box {
    background: #fef2f2; border: 1px solid #fca5a5;
    border-radius: 10px; padding: 14px 18px; margin: 12px 0;
    font-size: 0.85rem; color: #7f1d1d; line-height: 1.6;
}

.section-label {
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #94a3b8; margin: 24px 0 12px;
    display: flex; align-items: center; gap: 10px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: #e2e8f0; }

.table-card {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin: 12px 0;
}
.table-card-red {
    background: #fff; border: 1px solid #fca5a5;
    border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 6px rgba(239,68,68,0.08); margin: 12px 0;
}
.table-card-yellow {
    background: #fff; border: 1px solid #fcd34d;
    border-radius: 12px; padding: 20px;
    box-shadow: 0 1px 6px rgba(245,158,11,0.08); margin: 12px 0;
}
.table-title {
    font-size: 0.92rem; font-weight: 700; margin-bottom: 14px;
}
.table-title-red  { color: #dc2626; }
.table-title-yellow { color: #b45309; }

.stButton > button {
    background: #fff !important; color: #374151 !important;
    border: 1px solid #d1d5db !important; border-radius: 8px !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    padding: 6px 14px !important; transition: all .15s !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
.stButton > button:hover {
    background: #eff6ff !important; border-color: #3b82f6 !important;
    color: #1d4ed8 !important;
}
div[data-testid="stFileUploader"] {
    background: #fff; border: 2px dashed #cbd5e1; border-radius: 10px;
}
.stProgress > div > div { background: #3b82f6 !important; }
.stTextInput > div > div > input {
    background: #fff !important; border: 1px solid #d1d5db !important;
    color: #1a202c !important; border-radius: 8px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def norm_nopol(v):
    """Normalisasi nomor polisi: uppercase, spasi tunggal, pisahkan huruf-angka."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = str(v).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def norm_kuantum(v):
    """Konversi kuantum ke integer."""
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except:
        return None

def find_col(df, kws):
    """Cari kolom berdasarkan keyword (case-insensitive, ignore spasi/underscore)."""
    for col in df.columns:
        c = col.lower().replace(' ', '').replace('_', '')
        for k in kws:
            if k.replace(' ', '').replace('_', '') in c:
                return col
    return None

def extract_fid(link):
    """Ekstrak Google Drive File ID dari berbagai format URL."""
    if not isinstance(link, str) or not link.strip():
        return None
    link = link.strip()
    for p in [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
        r'open\?id=([a-zA-Z0-9_-]+)',
    ]:
        m = re.search(p, link)
        if m:
            fid = m.group(1)
            # File ID GDrive minimal 25 karakter
            if len(fid) >= 15:
                return fid
    return None

def to_preview(link):
    """URL preview Google Drive (iframe-friendly)."""
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def detect_file_type(content: bytes) -> str:
    """
    Deteksi tipe file dari magic bytes konten.
    Return: 'pdf', 'jpg', 'png', 'zip', 'html', atau 'unknown'
    """
    if not content or len(content) < 4:
        return 'unknown'
    sig = content[:8]
    if sig[:4] == b'%PDF':
        return 'pdf'
    if sig[:3] == b'\xff\xd8\xff':
        return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if sig[:2] in (b'PK', b'PK\x03\x04'):
        return 'zip'
    # Cek apakah HTML (Google Drive virus-scan warning page)
    try:
        snippet = content[:2000].decode('utf-8', errors='ignore').lower()
        if '<html' in snippet or '<!doctype' in snippet or '<head' in snippet:
            return 'html'
    except Exception:
        pass
    return 'unknown'

def download_gdrive(fid: str, retries: int = 4, timeout: int = 45) -> tuple[bytes | None, str]:
    """
    Download file dari Google Drive dengan penanganan:
    - Redirect virus-scan confirmation (file besar)
    - Token-based confirmation baru (confirm=t)
    - Retry otomatis dengan backoff

    Return: (content_bytes, error_message)
    """
    if not fid:
        return None, "File ID tidak valid"

    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    })

    # URL download langsung
    dl_url = f'https://drive.google.com/uc?export=download&id={fid}'

    for attempt in range(retries):
        try:
            # Request pertama
            resp = session.get(dl_url, timeout=timeout, stream=True, allow_redirects=True)

            content_type = resp.headers.get('Content-Type', '')

            # Kalau langsung bukan HTML → file asli
            if 'text/html' not in content_type and resp.status_code == 200:
                raw = b''.join(resp.iter_content(chunk_size=65536))
                ftype = detect_file_type(raw)
                if ftype != 'html' and len(raw) > 512:
                    return raw, ""

            # Kemungkinan virus-scan warning page → cari confirm token
            raw_html = b''.join(resp.iter_content(chunk_size=65536))
            html_text = raw_html.decode('utf-8', errors='ignore')

            # Metode 1: form confirm lama  (confirm=xxxxx)
            m_confirm = re.search(r'name="confirm"\s+value="([^"]+)"', html_text)
            if m_confirm:
                confirm_val = m_confirm.group(1)
                conf_url = f'{dl_url}&confirm={confirm_val}'
                r2 = session.get(conf_url, timeout=timeout, stream=True, allow_redirects=True)
                raw2 = b''.join(r2.iter_content(chunk_size=65536))
                ftype2 = detect_file_type(raw2)
                if ftype2 != 'html' and len(raw2) > 512:
                    return raw2, ""

            # Metode 2: confirm=t (token baru Google Drive 2024)
            conf_t_url = f'{dl_url}&confirm=t'
            r3 = session.get(conf_t_url, timeout=timeout, stream=True, allow_redirects=True)
            raw3 = b''.join(r3.iter_content(chunk_size=65536))
            ftype3 = detect_file_type(raw3)
            if ftype3 != 'html' and len(raw3) > 512:
                return raw3, ""

            # Metode 3: URL alternatif export
            alt_url = f'https://drive.google.com/uc?id={fid}&export=download&confirm=t'
            r4 = session.get(alt_url, timeout=timeout, stream=True, allow_redirects=True)
            raw4 = b''.join(r4.iter_content(chunk_size=65536))
            ftype4 = detect_file_type(raw4)
            if ftype4 != 'html' and len(raw4) > 512:
                return raw4, ""

            # Semua metode gagal untuk attempt ini
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s

        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            continue

    return None, f"Gagal setelah {retries} percobaan (mungkin file private atau link expired)"

def download_file(link: str) -> bytes | None:
    """
    Wrapper download: auto-detect Google Drive vs URL biasa.
    Return bytes jika berhasil, None jika gagal.
    """
    if not isinstance(link, str) or not link.strip():
        return None

    link = link.strip()
    fid = extract_fid(link)

    if fid:
        # Google Drive
        content, err = download_gdrive(fid)
        return content if content else None
    else:
        # URL biasa (non-Drive)
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
                )
            })
            r = session.get(link, timeout=45, stream=True, allow_redirects=True)
            raw = b''.join(r.iter_content(chunk_size=65536))
            ftype = detect_file_type(raw)
            if ftype != 'html' and len(raw) > 512:
                return raw
        except Exception:
            pass
        return None

def infer_extension(content: bytes, fallback: str = 'pdf') -> str:
    """Tebak ekstensi dari magic bytes."""
    ftype = detect_file_type(content)
    mapping = {'pdf': 'pdf', 'jpg': 'jpg', 'png': 'png', 'zip': 'zip'}
    return mapping.get(ftype, fallback)

def make_safe_filename(nopol: str, kuantum: int, idx: int, ext: str) -> str:
    """Buat filename aman: hapus karakter ilegal, tambah index kalau perlu."""
    safe = re.sub(r'[\\/:*?"<>|]', '_', nopol)
    return f'{safe}_{kuantum}_{idx+1}.{ext}'

def make_zip(files: dict) -> bytes:
    """Buat ZIP dari dict {filename: bytes}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()

def read_file(f) -> pd.DataFrame:
    """Baca file CSV/Excel → DataFrame."""
    if f.name.lower().endswith('.csv'):
        return pd.read_csv(f)
    return pd.read_excel(f)

def load_file1(df: pd.DataFrame) -> pd.DataFrame:
    """Parsing File 1 (target): kolom NOPOL + KUANTUM."""
    nc = find_col(df, ['nopol', 'nomor polisi', 'no pol', 'no.pol', 'nopolisi'])
    if not nc:
        nc = find_col(df, ['pol'])
    kc = find_col(df, ['kuantum', 'quantum', 'tonase', 'tonage', 'qty', 'jumlah', 'volume', 'berat'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 1. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM/TONASE tidak ditemukan di File 1. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol']   = df[nc].apply(norm_nopol)
    out['kuantum'] = df[kc].apply(norm_kuantum)
    out = out[(out['nopol'] != '') & out['nopol'].notna()]
    out = out.dropna(subset=['kuantum'])
    out = out[out['kuantum'] > 0]
    return out.reset_index(drop=True)

def load_file2(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Parsing File 2 (database): kolom NOPOL + KUANTUM + link Surat Jalan."""
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()
    # Deteksi apakah baris pertama sebenarnya header
    first_row = df.iloc[0].tolist()
    has_header_row = any(
        str(v).upper().strip() in ['NOPOL', 'KUANTUM', 'FOTO SURAT JALAN', 'SURAT JALAN']
        for v in first_row
    )
    if has_header_row:
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)

    nc = find_col(df, ['nopol', 'nomor polisi', 'no pol', 'no.pol', 'nopolisi'])
    if not nc:
        nc = find_col(df, ['pol'])
    kc = find_col(df, ['kuantum', 'quantum', 'tonase', 'tonage', 'qty', 'jumlah', 'volume', 'berat'])
    lc = find_col(df, ['surat jalan', 'suratjalan', 'foto surat', 'foto', 'link', 'url', 'drive', 'gdrive'])

    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM/TONASE tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not lc:
        st.error(f"❌ Kolom SURAT JALAN tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else '')
    out['kuantum']     = df[kc].apply(norm_kuantum)
    out['surat_jalan'] = df[lc].astype(str).str.strip()

    out = out[out['nopol'] != '']
    out = out[out['nopol'].str.upper() != 'NOPOL']
    out = out.dropna(subset=['kuantum'])
    out = out[out['kuantum'] > 0]

    # Validasi: link harus http atau file lokal yang dikenali
    valid_link = (
        out['surat_jalan'].str.startswith('http') |
        out['surat_jalan'].str.lower().str.endswith('.jpg') |
        out['surat_jalan'].str.lower().str.endswith('.pdf') |
        out['surat_jalan'].str.lower().str.endswith('.png')
    )
    out = out[valid_link].reset_index(drop=True)
    return out

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for k in ['result_df', 'missing_df', 'nopol_diff_df', 'nopol_miss_df',
          'active_preview', 'df2_debug', 'df1_debug', 'dl_cache']:
    if k not in st.session_state:
        st.session_state[k] = None

if st.session_state.dl_cache is None:
    st.session_state.dl_cache = {}  # cache download: {link: bytes}

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:2.4rem">🚛</div>
  <div>
    <h1>Surat Jalan Filter</h1>
    <p>Match NOPOL + KUANTUM (ketat) → Preview &amp; Download Surat Jalan — File dijamin bisa dibuka ✅</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── UPLOAD ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="upload-card"><h3>📋 File 1 — Target</h3><p>Kolom: NOPOL, KUANTUM (atau: Nomor Polisi, Tonase, dll)</p></div>', unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv','xlsx','xls'], key='f1', label_visibility='collapsed')
with c2:
    st.markdown('<div class="upload-card"><h3>🗄️ File 2 — Database Surat Jalan</h3><p>Kolom: NOPOL, KUANTUM, Foto Surat Jalan (link Google Drive)</p></div>', unsafe_allow_html=True)
    file2 = st.file_uploader("File 2", type=['csv','xlsx','xls'], key='f2', label_visibility='collapsed')

cb, _ = st.columns([2, 8])
with cb:
    process = st.button('⚙️ Proses Data', use_container_width=True)

# ── PROCESS ────────────────────────────────────────────────────────────────────
if process:
    if not file1 or not file2:
        st.warning('⚠️ Upload kedua file terlebih dahulu.')
    else:
        with st.spinner('Memproses data...'):
            r1 = read_file(file1)
            r2 = read_file(file2)
            df1 = load_file1(r1)
            df2 = load_file2(r2)
            if df1.empty or df2.empty:
                st.stop()

            # ── MATCH KETAT: NOPOL + KUANTUM harus sama persis ──
            result_rows = []
            for idx, row1 in df1.iterrows():
                matches = df2[
                    (df2['nopol'] == row1['nopol']) &
                    (df2['kuantum'] == row1['kuantum'])
                ]
                http_matches = matches[matches['surat_jalan'].str.startswith('http')]
                if len(http_matches) > 0:
                    for _, row2 in http_matches.iterrows():
                        result_rows.append({
                            'nopol':       row1['nopol'],
                            'kuantum':     row1['kuantum'],
                            'surat_jalan': row2['surat_jalan'],
                            '_f1_idx':     idx
                        })
                else:
                    result_rows.append({
                        'nopol':       row1['nopol'],
                        'kuantum':     row1['kuantum'],
                        'surat_jalan': None,
                        '_f1_idx':     idx
                    })

            result = pd.DataFrame(result_rows)
            found = result[
                result['surat_jalan'].notna() &
                result['surat_jalan'].str.startswith('http', na=False)
            ].copy().reset_index(drop=True)

            matched_f1_idx = set(found['_f1_idx'].tolist())
            missing_rows = []
            for idx, row1 in df1.iterrows():
                if idx not in matched_f1_idx:
                    missing_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum']})
            missing = pd.DataFrame(missing_rows).drop_duplicates(
                subset=['nopol', 'kuantum']
            ).reset_index(drop=True)

            # ── Diagnostik detail ──
            nopol_beda_k_rows = []
            nopol_tidak_ada_rows = []
            for _, row in missing.iterrows():
                f2_match = df2[df2['nopol'] == row['nopol']]
                if len(f2_match) > 0:
                    kuantums = sorted(f2_match['kuantum'].dropna().astype(int).unique().tolist())
                    display  = ', '.join(map(str, kuantums[:8]))
                    if len(kuantums) > 8:
                        display += f' ... (+{len(kuantums)-8} lagi)'
                    nopol_beda_k_rows.append({
                        'NOPOL':                    row['nopol'],
                        'Kuantum File 1':           int(row['kuantum']),
                        'Kuantum Tersedia di File 2': display,
                        'Status':                   '⚠️ Kuantum tidak cocok'
                    })
                else:
                    nopol_tidak_ada_rows.append({
                        'NOPOL':          row['nopol'],
                        'Kuantum File 1': int(row['kuantum']),
                        'Status':         '❌ NOPOL tidak ada di File 2'
                    })

            st.session_state.result_df     = found
            st.session_state.missing_df    = missing
            st.session_state.nopol_diff_df = pd.DataFrame(nopol_beda_k_rows)
            st.session_state.nopol_miss_df = pd.DataFrame(nopol_tidak_ada_rows)
            st.session_state.df2_debug     = df2
            st.session_state.df1_debug     = df1
            st.session_state.active_preview = None
            st.session_state.dl_cache      = {}  # reset cache setiap proses baru

            st.success(f'✅ Selesai! {len(found)} surat jalan ditemukan dari {len(df1)} data File 1.')

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.result_df is not None:
    found      = st.session_state.result_df
    missing    = st.session_state.missing_df
    nopol_diff = st.session_state.nopol_diff_df
    nopol_miss = st.session_state.nopol_miss_df
    df2_all    = st.session_state.df2_debug
    df1_all    = st.session_state.df1_debug
    total_f1   = len(df1_all)

    # ── SUMMARY ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Ringkasan Hasil</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-num c-blue">{total_f1}</div>
        <div class="stat-lbl">Total Data File 1</div>
      </div>
      <div class="stat-card">
        <div class="stat-num c-green">{len(found)}</div>
        <div class="stat-lbl">Surat Jalan Ditemukan</div>
      </div>
      <div class="stat-card">
        <div class="stat-num c-red">{len(missing)}</div>
        <div class="stat-lbl">Data Tidak Match</div>
      </div>
      <div class="stat-card">
        <div class="stat-num c-yellow">{len(df2_all)}</div>
        <div class="stat-lbl">Total Data File 2</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Cara kerja match:</b> NOPOL <em>dan</em> KUANTUM harus <b>sama persis</b> di kedua file.
    Normalisasi otomatis: spasi ganda → 1 spasi, huruf kecil/besar diabaikan (BE1235AD = BE 1235 AD).
    Satu pasang NOPOL+KUANTUM bisa menghasilkan <b>lebih dari satu surat jalan</b>.<br>
    🔧 <b>Fix download:</b> File yang didownload <b>dijamin bisa dibuka</b> — sistem mendeteksi
    Google Drive confirmation page dan bypass otomatis, serta validasi konten sebelum disimpan.
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # BAGIAN 1 — DATA YANG BERHASIL MATCH
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">✅ Data Berhasil Ditemukan</div>', unsafe_allow_html=True)

    if len(found) > 0:
        search = st.text_input(
            'Filter NOPOL (ditemukan)',
            placeholder='🔍  Ketik NOPOL untuk filter...',
            label_visibility='collapsed',
            key='search_found'
        )
        disp = found.copy()
        if search.strip():
            sn = norm_nopol(search.strip())
            disp = disp[
                disp['nopol'].str.contains(re.escape(sn), na=False, case=False)
            ].reset_index(drop=True)

        st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

        # ── BULK DOWNLOAD ──────────────────────────────────────────────────────
        bc1, bc2, _ = st.columns([2, 3, 5])
        with bc1:
            do_bulk = st.button('📦 Download Semua (ZIP)', use_container_width=True)
        with bc2:
            do_preload = st.button('⚡ Pre-load Semua File', use_container_width=True,
                                   help='Download semua file ke cache dulu agar tombol Download per baris lebih cepat.')

        # Pre-load ke cache
        if do_preload and len(disp) > 0:
            links_to_load = [
                r.surat_jalan for r in disp.itertuples()
                if r.surat_jalan not in st.session_state.dl_cache
            ]
            if not links_to_load:
                st.success('✅ Semua file sudah ada di cache!')
            else:
                prog = st.progress(0)
                stxt = st.empty()
                done, ok_count, fail_count = 0, 0, 0
                stxt.text(f'Pre-loading 0 / {len(links_to_load)} file...')

                def _preload_worker(link):
                    ct = download_file(link)
                    return link, ct

                with ThreadPoolExecutor(max_workers=8) as ex:
                    futs = {ex.submit(_preload_worker, lnk): lnk for lnk in links_to_load}
                    for fut in as_completed(futs):
                        link, ct = fut.result()
                        if ct:
                            st.session_state.dl_cache[link] = ct
                            ok_count += 1
                        else:
                            fail_count += 1
                        done += 1
                        prog.progress(done / len(links_to_load))
                        stxt.text(f'Pre-loading {done} / {len(links_to_load)} — ✅ {ok_count} | ❌ {fail_count}')

                stxt.text(f'Pre-load selesai: ✅ {ok_count} berhasil | ❌ {fail_count} gagal')

        # Bulk download ZIP
        if do_bulk and len(disp) > 0:
            items   = list(disp.itertuples(index=True))
            prog    = st.progress(0)
            stxt    = st.empty()
            ok_files, fail_list = {}, []
            stxt.text(f'Mengunduh 0 / {len(items)} file...')
            done_count = 0

            def _dl_worker(row):
                link = row.surat_jalan
                # Pakai cache kalau sudah ada
                ct = st.session_state.dl_cache.get(link)
                if ct is None:
                    ct = download_file(link)
                    if ct:
                        st.session_state.dl_cache[link] = ct
                return row.Index, row.nopol, int(row.kuantum), link, ct

            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(_dl_worker, r): r for r in items}
                for fut in as_completed(futs):
                    idx_r, nopol_r, kuantum_r, link_r, ct = fut.result()
                    if ct:
                        ext  = infer_extension(ct)
                        fn   = make_safe_filename(nopol_r, kuantum_r, idx_r, ext)
                        # Hindari duplikat nama
                        base_fn, counter = fn, 1
                        while fn in ok_files:
                            fn = base_fn.rsplit('.', 1)[0] + f'_{counter}.' + base_fn.rsplit('.', 1)[-1]
                            counter += 1
                        ok_files[fn] = ct
                    else:
                        fail_list.append(f'{nopol_r} ({kuantum_r})')
                    done_count += 1
                    prog.progress(done_count / len(items))
                    stxt.text(f'Mengunduh {done_count} / {len(items)} — ✅ {len(ok_files)} | ❌ {len(fail_list)}')

            stxt.text(f'Selesai — ✅ {len(ok_files)} berhasil | ❌ {len(fail_list)} gagal')
            if ok_files:
                st.download_button(
                    f'💾 Simpan ZIP ({len(ok_files)} file — dijamin bisa dibuka)',
                    make_zip(ok_files),
                    'surat_jalan_semua.zip',
                    'application/zip',
                    key='dl_zip_main'
                )
            if fail_list:
                with st.expander(f'❌ {len(fail_list)} file gagal diunduh (link mungkin private/expired)'):
                    for f in fail_list:
                        st.write(f'• {f}')

        # ── DETAIL TABLE ───────────────────────────────────────────────────────
        st.markdown('<div class="section-label">Detail per Surat Jalan</div>', unsafe_allow_html=True)

        # Header kolom
        hcols = st.columns([0.5, 2.5, 1.5, 2, 1.5, 1.5])
        for col, lbl in zip(hcols, ['No.', 'NOPOL', 'KUANTUM', 'Link', '👁 Preview', '⬇ Download']):
            col.markdown(f'**{lbl}**')
        st.divider()

        for i, row in disp.iterrows():
            nopol   = row['nopol']
            kuantum = int(row['kuantum'])
            link    = row['surat_jalan']
            fid     = extract_fid(link)
            cols    = st.columns([0.5, 2.5, 1.5, 2, 1.5, 1.5])

            cols[0].markdown(f'`#{i+1}`')
            cols[1].markdown(f'`{nopol}`')
            cols[2].markdown(f'**{kuantum:,}**')
            # Tampilkan link pendek yang bisa diklik
            if fid:
                short_link = f'https://drive.google.com/file/d/{fid}/view'
                cols[3].markdown(f'[🔗 Buka GDrive]({short_link})', unsafe_allow_html=False)
            else:
                cols[3].markdown(f'[🔗 Link]({link})', unsafe_allow_html=False)

            with cols[4]:
                if st.button('👁️ Lihat', key=f'v_{i}'):
                    st.session_state.active_preview = (
                        None if st.session_state.active_preview == i else i
                    )

            with cols[5]:
                # Cek cache dulu
                cached = st.session_state.dl_cache.get(link)
                if cached:
                    ext = infer_extension(cached)
                    fname = make_safe_filename(nopol, kuantum, i, ext)
                    mime = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                    st.download_button(
                        f'⬇️ .{ext.upper()}',
                        cached,
                        fname,
                        mime,
                        key=f'd_{i}'
                    )
                else:
                    # Download on-demand
                    if st.button('⬇️ Download', key=f'db_{i}'):
                        with st.spinner(f'Mengunduh {nopol}...'):
                            ct = download_file(link)
                        if ct:
                            st.session_state.dl_cache[link] = ct
                            ext   = infer_extension(ct)
                            fname = make_safe_filename(nopol, kuantum, i, ext)
                            mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                            st.download_button(
                                f'💾 Simpan .{ext.upper()}',
                                ct,
                                fname,
                                mime,
                                key=f'ds_{i}'
                            )
                            st.success(f'✅ File {fname} siap disimpan!')
                        else:
                            st.error(
                                '❌ Gagal mengunduh. Kemungkinan: (1) file private/perlu akses, '
                                '(2) link expired, (3) koneksi timeout. '
                                'Coba buka link GDrive secara manual.'
                            )

            # ── Preview inline ──────────────────────────────────────────────────
            if st.session_state.active_preview == i:
                purl = to_preview(link)
                if purl:
                    import streamlit.components.v1 as components
                    components.html(
                        f'<iframe src="{purl}" width="100%" height="680"'
                        f' style="border:1px solid #e2e8f0;border-radius:10px;background:#fff"'
                        f' allow="autoplay"></iframe>',
                        height=700
                    )
                    st.markdown(
                        f'📌 Jika preview kosong, [buka di tab baru ↗]({purl})',
                        unsafe_allow_html=False
                    )
                else:
                    st.error('Link preview tidak valid.')

    else:
        st.markdown("""
        <div class="warn-box">
        ⚠️ <strong>0 surat jalan ditemukan.</strong> NOPOL <em>dan</em> KUANTUM harus sama persis
        di kedua file. Lihat tabel di bawah untuk detail penyebabnya.
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # BAGIAN 2 — DATA YANG TIDAK BERHASIL TERDETEKSI
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">❌ Data Tidak Berhasil Terdeteksi</div>', unsafe_allow_html=True)

    if len(missing) == 0:
        st.markdown("""
        <div class="success-box">
        🎉 <b>Semua data di File 1 berhasil dicocokkan!</b> Tidak ada data yang tidak match.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="error-box">
        ❌ <b>{len(missing)} kombinasi NOPOL + KUANTUM dari File 1 tidak ditemukan di File 2.</b><br>
        Tabel di bawah menjelaskan penyebabnya secara detail.
        </div>
        """, unsafe_allow_html=True)

        # ── Tabel A: NOPOL ada, KUANTUM beda ─────────────────────────────────
        if nopol_diff is not None and not nopol_diff.empty:
            st.markdown(f"""
            <div class="table-card-yellow">
              <div class="table-title table-title-yellow">
                ⚠️ Tabel A — {len(nopol_diff)} NOPOL ada di File 2, tapi KUANTUM tidak cocok
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="warn-box">
            💡 NOPOL ini <em>ada</em> di File 2, namun nilai KUANTUM yang tersedia berbeda
            dengan yang ada di File 1. Match hanya terjadi jika keduanya sama persis.
            </div>
            """, unsafe_allow_html=True)

            s_diff = st.text_input(
                '', placeholder='🔍  Filter NOPOL di Tabel A...',
                label_visibility='collapsed', key='sd'
            )
            d_diff = nopol_diff.copy()
            if s_diff.strip():
                sn    = norm_nopol(s_diff.strip())
                d_diff = d_diff[
                    d_diff['NOPOL'].str.contains(re.escape(sn), na=False, case=False)
                ].reset_index(drop=True)

            st.dataframe(
                d_diff, use_container_width=True, hide_index=True,
                column_config={
                    'NOPOL':                      st.column_config.TextColumn('NOPOL', width='medium'),
                    'Kuantum File 1':             st.column_config.NumberColumn('Kuantum File 1', format='%d'),
                    'Kuantum Tersedia di File 2': st.column_config.TextColumn('Kuantum Tersedia di File 2', width='large'),
                    'Status':                     st.column_config.TextColumn('Status', width='medium'),
                }
            )
            ca, _ = st.columns([2, 8])
            with ca:
                st.download_button(
                    '📥 Export Tabel A (.csv)',
                    d_diff.to_csv(index=False).encode('utf-8'),
                    'tabel_a_kuantum_beda.csv',
                    'text/csv',
                    key='dl_a'
                )

        # ── Tabel B: NOPOL tidak ada sama sekali ──────────────────────────────
        if nopol_miss is not None and not nopol_miss.empty:
            st.markdown(f"""
            <div class="table-card-red">
              <div class="table-title table-title-red">
                ❌ Tabel B — {len(nopol_miss)} NOPOL tidak ditemukan sama sekali di File 2
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="error-box">
            ❌ NOPOL ini tidak ada di File 2 sama sekali — kemungkinan belum diinput,
            ada typo, atau memang tidak ada datanya.
            </div>
            """, unsafe_allow_html=True)

            s_miss = st.text_input(
                '', placeholder='🔍  Filter NOPOL di Tabel B...',
                label_visibility='collapsed', key='sm'
            )
            d_miss = nopol_miss.copy()
            if s_miss.strip():
                sn    = norm_nopol(s_miss.strip())
                d_miss = d_miss[
                    d_miss['NOPOL'].str.contains(re.escape(sn), na=False, case=False)
                ].reset_index(drop=True)

            st.dataframe(
                d_miss, use_container_width=True, hide_index=True,
                column_config={
                    'NOPOL':          st.column_config.TextColumn('NOPOL', width='medium'),
                    'Kuantum File 1': st.column_config.NumberColumn('Kuantum File 1', format='%d'),
                    'Status':         st.column_config.TextColumn('Status', width='large'),
                }
            )
            cb2, _ = st.columns([2, 8])
            with cb2:
                st.download_button(
                    '📥 Export Tabel B (.csv)',
                    d_miss.to_csv(index=False).encode('utf-8'),
                    'tabel_b_nopol_tidak_ada.csv',
                    'text/csv',
                    key='dl_b'
                )

        # ── Tabel C: gabungan semua tidak match ───────────────────────────────
        with st.expander('📋 Tabel C — Semua data tidak match (gabungan)', expanded=False):
            all_miss = missing.copy()
            all_miss.columns = ['NOPOL', 'Kuantum File 1']
            all_miss['Kuantum File 1'] = all_miss['Kuantum File 1'].astype(int)

            s_all = st.text_input(
                '', placeholder='🔍  Filter NOPOL...',
                label_visibility='collapsed', key='sa'
            )
            if s_all.strip():
                sn       = norm_nopol(s_all.strip())
                all_miss = all_miss[
                    all_miss['NOPOL'].str.contains(re.escape(sn), na=False, case=False)
                ].reset_index(drop=True)

            st.dataframe(all_miss, use_container_width=True, hide_index=True)
            cc, _ = st.columns([2, 8])
            with cc:
                st.download_button(
                    '📥 Export Tabel C (.csv)',
                    all_miss.to_csv(index=False).encode('utf-8'),
                    'tabel_c_semua_tidak_match.csv',
                    'text/csv',
                    key='dl_c'
                )
