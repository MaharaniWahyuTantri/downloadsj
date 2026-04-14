import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Surat Jalan Bulk Downloader", page_icon="📦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  --bg:       #0f1117;
  --surface:  #1a1d27;
  --surface2: #222535;
  --border:   #2d3048;
  --accent:   #6366f1;
  --accent2:  #818cf8;
  --green:    #22c55e;
  --yellow:   #f59e0b;
  --red:      #ef4444;
  --text:     #e2e8f0;
  --muted:    #64748b;
  --radius:   12px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
}

.stApp { background: var(--bg); }
.main .block-container { padding: 1.5rem 2rem; max-width: 1300px; }

/* ── HEADER ── */
.app-header {
  display: flex; align-items: center; gap: 20px;
  padding: 28px 32px;
  background: linear-gradient(135deg, #1a1d27 0%, #222535 100%);
  border: 1px solid var(--border);
  border-radius: 16px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.app-header::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 0% 50%, rgba(99,102,241,.15) 0%, transparent 60%);
  pointer-events: none;
}
.app-header-icon { font-size: 3rem; flex-shrink: 0; }
.app-header-text h1 { font-size: 1.6rem; font-weight: 800; color: #fff; }
.app-header-text p  { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }

/* ── UPLOAD ZONE ── */
.upload-zone {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 8px;
}
.upload-zone-title {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: var(--accent2); margin-bottom: 6px;
}
.upload-zone-desc { font-size: 0.78rem; color: var(--muted); }

div[data-testid="stFileUploader"] {
  background: var(--surface2) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: 10px !important;
  transition: border-color .2s;
}
div[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
}

/* ── STAT CARDS ── */
.stats-row {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin: 24px 0;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 18px;
  text-align: center;
  position: relative; overflow: hidden;
}
.stat-card::after {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0;
}
.stat-card.blue::after  { background: var(--accent); }
.stat-card.green::after { background: var(--green); }
.stat-card.red::after   { background: var(--red); }
.stat-card.yellow::after{ background: var(--yellow); }

.stat-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2.4rem; font-weight: 700; line-height: 1;
}
.stat-num.blue   { color: var(--accent2); }
.stat-num.green  { color: var(--green); }
.stat-num.red    { color: var(--red); }
.stat-num.yellow { color: var(--yellow); }
.stat-label {
  font-size: 0.68rem; color: var(--muted); margin-top: 8px;
  text-transform: uppercase; letter-spacing: .8px; font-weight: 600;
}

/* ── ALERTS ── */
.alert {
  border-radius: var(--radius); padding: 14px 18px;
  margin: 12px 0; font-size: 0.83rem; line-height: 1.6;
  display: flex; align-items: flex-start; gap: 10px;
}
.alert-icon { flex-shrink: 0; font-size: 1rem; margin-top: 1px; }
.alert.info    { background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.3); color: #a5b4fc; }
.alert.success { background: rgba(34,197,94,.1);  border: 1px solid rgba(34,197,94,.3);  color: #86efac; }
.alert.warn    { background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.3); color: #fcd34d; }
.alert.error   { background: rgba(239,68,68,.1);  border: 1px solid rgba(239,68,68,.3);  color: #fca5a5; }

/* ── SECTION DIVIDER ── */
.section-label {
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; color: var(--muted);
  display: flex; align-items: center; gap: 12px;
  margin: 28px 0 16px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ── BUTTONS ── */
.stButton > button {
  background: var(--surface2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
  transition: all .15s !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stButton > button:hover {
  background: rgba(99,102,241,.15) !important;
  border-color: var(--accent) !important;
  color: var(--accent2) !important;
}

/* ── TABLE CARD ── */
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin: 12px 0;
}
.table-card.warn  { border-color: rgba(245,158,11,.4); }
.table-card.error { border-color: rgba(239,68,68,.4); }
.table-card-title { font-size: 0.9rem; font-weight: 700; margin-bottom: 14px; }
.table-card-title.warn  { color: var(--yellow); }
.table-card-title.error { color: var(--red); }

/* ── ROW ITEM ── */
.row-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: var(--surface2);
  border: 1px solid var(--border);
  margin-bottom: 6px;
}
.row-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem; color: var(--muted);
  background: var(--bg); border-radius: 4px;
  padding: 2px 6px; flex-shrink: 0;
}
.row-nopol {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700; color: var(--accent2);
  font-size: 0.88rem; flex: 1;
}
.row-qty {
  font-size: 0.82rem; color: var(--muted); flex-shrink: 0;
}

/* ── PROGRESS ── */
.stProgress > div > div { background: var(--accent) !important; border-radius: 4px !important; }

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── INPUTS ── */
.stTextInput > div > div > input {
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(99,102,241,.2) !important;
}

/* ── SPINNER ── */
.stSpinner { color: var(--accent2) !important; }

/* ── EXPANDER ── */
details { background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; }

/* ── DOWNLOAD BTN ── */
.stDownloadButton > button {
  background: linear-gradient(135deg, var(--accent), #4f46e5) !important;
  color: white !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  transition: opacity .15s !important;
}
.stDownloadButton > button:hover { opacity: 0.88 !important; }

/* ── SUCCESS/ERROR from streamlit ── */
.element-container .stAlert { border-radius: 10px !important; }

/* ── CHECKBOX ── */
.stCheckbox { color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def norm_nopol(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = re.sub(r'\s+', ' ', str(v).strip().upper())
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm_kuantum(v):
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except Exception:
        return None

def find_col(df, keywords):
    for col in df.columns:
        c = col.lower().replace(' ', '').replace('_', '')
        for k in keywords:
            if k.replace(' ', '').replace('_', '') in c:
                return col
    return None

def extract_fid(link):
    if not isinstance(link, str) or not link.strip():
        return None
    for pattern in [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
        r'open\?id=([a-zA-Z0-9_-]+)',
    ]:
        m = re.search(pattern, link.strip())
        if m and len(m.group(1)) >= 15:
            return m.group(1)
    return None

def to_preview_url(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def detect_filetype(content):
    if not content or len(content) < 8:
        return 'unknown'
    sig = content[:8]
    if sig[:4] == b'%PDF':   return 'pdf'
    if sig[:3] == b'\xff\xd8\xff': return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
    try:
        snippet = content[:2000].decode('utf-8', errors='ignore').lower()
        if '<html' in snippet or '<!doctype' in snippet:
            return 'html'
    except Exception:
        pass
    return 'unknown'

def _read_chunks(resp):
    return b''.join(resp.iter_content(chunk_size=65536))

def download_gdrive(fid, retries=3, timeout=40):
    """Multi-layer Google Drive download bypass."""
    if not fid:
        return None
    session = requests.Session()
    session.headers['User-Agent'] = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
    base = f'https://drive.google.com/uc?export=download&id={fid}'

    def try_url(url):
        r = session.get(url, timeout=timeout, stream=True, allow_redirects=True)
        raw = _read_chunks(r)
        if detect_filetype(raw) != 'html' and len(raw) > 512:
            return raw
        return None

    for attempt in range(retries):
        try:
            # Layer 1: direct
            r1  = session.get(base, timeout=timeout, stream=True, allow_redirects=True)
            raw = _read_chunks(r1)
            if detect_filetype(raw) != 'html' and len(raw) > 512:
                return raw

            html = raw.decode('utf-8', errors='ignore')

            # Layer 2: form confirm token
            m = re.search(r'name="confirm"\s+value="([^"]+)"', html)
            if m:
                result = try_url(f'{base}&confirm={m.group(1)}')
                if result: return result

            # Layer 3: confirm=t (modern GDrive)
            result = try_url(f'{base}&confirm=t')
            if result: return result

            # Layer 4: alternate URL form
            result = try_url(f'https://drive.google.com/uc?id={fid}&export=download&confirm=t')
            if result: return result

        except Exception:
            pass

        if attempt < retries - 1:
            time.sleep(2 ** attempt)

    return None

def download_file(link):
    if not isinstance(link, str) or not link.strip():
        return None
    fid = extract_fid(link)
    if fid:
        return download_gdrive(fid)
    try:
        r = requests.get(link.strip(), timeout=40, stream=True,
                         headers={'User-Agent': 'Mozilla/5.0'})
        raw = _read_chunks(r)
        if detect_filetype(raw) != 'html' and len(raw) > 512:
            return raw
    except Exception:
        pass
    return None

def ext_from_content(content, fallback='pdf'):
    return {'pdf': 'pdf', 'jpg': 'jpg', 'png': 'png'}.get(
        detect_filetype(content) if content else '', fallback)

def safe_filename(nopol, kuantum, idx, ext):
    safe = re.sub(r'[\\/:*?"<>|]', '_', str(nopol))
    return f'{safe}_{kuantum}_{idx+1}.{ext}'

def make_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()

def img_to_pdf(img_bytes):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Image as RLImage
        from PIL import Image as PILImage
        pil = PILImage.open(io.BytesIO(img_bytes))
        w_px, h_px = pil.size
        a4_w, a4_h = A4
        scale = min(a4_w / w_px, a4_h / h_px)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=(w_px*scale+20, h_px*scale+20),
                                rightMargin=10, leftMargin=10,
                                topMargin=10, bottomMargin=10)
        doc.build([RLImage(io.BytesIO(img_bytes), width=w_px*scale, height=h_px*scale)])
        return buf.getvalue()
    except Exception:
        return None

def merge_to_pdf(content_list):
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfWriter, PdfReader
        except ImportError:
            return None

    writer = PdfWriter()
    for ct in content_list:
        if not ct: continue
        ftype = detect_filetype(ct)
        if ftype == 'pdf':
            try:
                for page in PdfReader(io.BytesIO(ct)).pages:
                    writer.add_page(page)
            except Exception:
                continue
        elif ftype in ('jpg', 'png'):
            converted = img_to_pdf(ct)
            if converted:
                try:
                    for page in PdfReader(io.BytesIO(converted)).pages:
                        writer.add_page(page)
                except Exception:
                    continue

    if not writer.pages:
        return None
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

def read_uploaded(f):
    return pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════════════════════

def load_df1(df):
    nc = find_col(df, ['nopol','nomor polisi','no pol','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame({'nopol': df[nc].apply(norm_nopol),
                        'kuantum': df[kc].apply(norm_kuantum)})
    return out[(out['nopol'] != '') & out['nopol'].notna() &
               out['kuantum'].notna() & (out['kuantum'] > 0)].reset_index(drop=True)

def load_df2(raw_df):
    df = raw_df.copy()
    if df.empty: return pd.DataFrame()
    # Auto-detect header row
    first = df.iloc[0].tolist()
    if any(str(v).upper().strip() in ['NOPOL','KUANTUM','FOTO SURAT JALAN','SURAT JALAN']
           for v in first):
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)

    nc = find_col(df, ['nopol','nomor polisi','no pol','no truk','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    lc = find_col(df, ['surat jalan','suratjalan','foto surat','foto','link','url','drive','gdrive'])

    for col, label in [(nc, 'NOPOL'), (kc, 'KUANTUM'), (lc, 'SURAT JALAN')]:
        if not col:
            st.error(f"❌ Kolom {label} tidak ditemukan di File 2. Tersedia: {list(df.columns)}")
            return pd.DataFrame()

    out = pd.DataFrame({
        'nopol':       df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else ''),
        'kuantum':     df[kc].apply(norm_kuantum),
        'surat_jalan': df[lc].astype(str).str.strip(),
    })
    out = out[out['nopol'].ne('') & out['nopol'].str.upper().ne('NOPOL')]
    out = out.dropna(subset=['kuantum']).query('kuantum > 0')
    valid = (out['surat_jalan'].str.startswith('http') |
             out['surat_jalan'].str.lower().str.match(r'.*\.(jpg|pdf|png)$'))
    return out[valid].reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# PARALLEL DOWNLOADER
# ══════════════════════════════════════════════════════════════════════════════

def _worker(task, cache_snapshot):
    link = task['link']
    ct   = cache_snapshot.get(link) or download_file(link)
    return {**task, 'content': ct}

def run_downloads(disp, label='Mengunduh'):
    cache_snap = dict(st.session_state.dl_cache)
    tasks = [
        {'idx': i, 'nopol': row['nopol'],
         'kuantum': int(row['kuantum']), 'link': row['surat_jalan']}
        for i, row in disp.iterrows()
    ]
    total    = len(tasks)
    prog     = st.progress(0)
    status   = st.empty()
    ok_files = {}
    new_cache= {}
    fails    = []
    done     = 0

    status.markdown(f'`{label} 0 / {total}...`')
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_worker, t, cache_snap): t for t in tasks}
        for fut in as_completed(futs):
            res = fut.result()
            ct  = res['content']
            if ct:
                new_cache[res['link']] = ct
                ext  = ext_from_content(ct)
                fn   = safe_filename(res['nopol'], res['kuantum'], res['idx'], ext)
                # deduplicate
                base_fn, c = fn, 1
                while fn in ok_files:
                    fn = base_fn.rsplit('.', 1)[0] + f'_{c}.' + base_fn.rsplit('.', 1)[-1]
                    c += 1
                ok_files[fn] = ct
            else:
                fails.append(f"{res['nopol']} (qty: {res['kuantum']})")
            done += 1
            prog.progress(done / total)
            status.markdown(
                f'`{label} {done}/{total}` — '
                f'✅ **{len(ok_files)}** berhasil &nbsp;|&nbsp; ❌ **{len(fails)}** gagal'
            )

    status.markdown(f'✅ **{len(ok_files)}** berhasil &nbsp;|&nbsp; ❌ **{len(fails)}** gagal')
    return ok_files, fails, new_cache

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
_defaults = {
    'result_df': None, 'missing_df': None,
    'nopol_diff_df': None, 'nopol_miss_df': None,
    'active_preview': None,
    'df1_debug': None, 'df2_debug': None,
    'dl_cache': {},
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div class="app-header-icon">📦</div>
  <div class="app-header-text">
    <h1>Surat Jalan Bulk Downloader</h1>
    <p>Match NOPOL + KUANTUM → Download ZIP terpisah atau gabung 1 PDF sekaligus</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="upload-zone">
      <div class="upload-zone-title">📋 File 1 — Target</div>
      <div class="upload-zone-desc">Kolom yang diperlukan: NOPOL, KUANTUM</div>
    </div>
    """, unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv','xlsx','xls'],
                              key='f1', label_visibility='collapsed')

with col2:
    st.markdown("""
    <div class="upload-zone">
      <div class="upload-zone-title">🗄️ File 2 — Database Surat Jalan</div>
      <div class="upload-zone-desc">Kolom yang diperlukan: NOPOL, KUANTUM, Link Google Drive</div>
    </div>
    """, unsafe_allow_html=True)
    file2 = st.file_uploader("File 2", type=['csv','xlsx','xls'],
                              key='f2', label_visibility='collapsed')

_, btn_col, _ = st.columns([3, 2, 5])
with btn_col:
    process = st.button('⚙️  Proses Data', use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS
# ══════════════════════════════════════════════════════════════════════════════
if process:
    if not file1 or not file2:
        st.markdown('<div class="alert warn"><span class="alert-icon">⚠️</span>Upload kedua file terlebih dahulu.</div>',
                    unsafe_allow_html=True)
    else:
        with st.spinner('Memproses data...'):
            df1 = load_df1(read_uploaded(file1))
            df2 = load_df2(read_uploaded(file2))
            if df1.empty or df2.empty:
                st.stop()

            result_rows = []
            for i, row1 in df1.iterrows():
                matches = df2[(df2['nopol'] == row1['nopol']) &
                              (df2['kuantum'] == row1['kuantum'])]
                http_matches = matches[matches['surat_jalan'].str.startswith('http', na=False)]
                if not http_matches.empty:
                    for _, r2 in http_matches.iterrows():
                        result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                            'surat_jalan': r2['surat_jalan'], '_f1_idx': i})
                else:
                    result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                        'surat_jalan': None, '_f1_idx': i})

            result = pd.DataFrame(result_rows)
            found  = result[result['surat_jalan'].notna() &
                            result['surat_jalan'].str.startswith('http', na=False)
                            ].copy().reset_index(drop=True)

            matched_idx = set(found['_f1_idx'])
            missing     = df1[~df1.index.isin(matched_idx)].drop_duplicates(
                              subset=['nopol','kuantum']).reset_index(drop=True)

            diff_rows, miss_rows = [], []
            for _, row in missing.iterrows():
                f2m = df2[df2['nopol'] == row['nopol']]
                if not f2m.empty:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique())
                    d  = ', '.join(map(str, ks[:8])) + (f' …+{len(ks)-8}' if len(ks) > 8 else '')
                    diff_rows.append({'NOPOL': row['nopol'],
                                      'Kuantum (File 1)': int(row['kuantum']),
                                      'Kuantum tersedia di File 2': d,
                                      'Status': '⚠️ Kuantum tidak cocok'})
                else:
                    miss_rows.append({'NOPOL': row['nopol'],
                                      'Kuantum (File 1)': int(row['kuantum']),
                                      'Status': '❌ NOPOL tidak ditemukan di File 2'})

            st.session_state.update({
                'result_df':     found,
                'missing_df':    missing,
                'nopol_diff_df': pd.DataFrame(diff_rows),
                'nopol_miss_df': pd.DataFrame(miss_rows),
                'df1_debug':     df1,
                'df2_debug':     df2,
                'active_preview': None,
                'dl_cache':       {},
            })

        st.markdown(f'<div class="alert success"><span class="alert-icon">✅</span>'
                    f'Selesai! <b>{len(found)}</b> surat jalan ditemukan dari <b>{len(df1)}</b> data di File 1.</div>',
                    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.result_df is not None:
    found      = st.session_state.result_df
    missing    = st.session_state.missing_df
    nopol_diff = st.session_state.nopol_diff_df
    nopol_miss = st.session_state.nopol_miss_df
    df1_all    = st.session_state.df1_debug
    df2_all    = st.session_state.df2_debug

    # ── STATS ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Ringkasan</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card blue">
        <div class="stat-num blue">{len(df1_all)}</div>
        <div class="stat-label">Total File 1</div>
      </div>
      <div class="stat-card green">
        <div class="stat-num green">{len(found)}</div>
        <div class="stat-label">Berhasil Match</div>
      </div>
      <div class="stat-card red">
        <div class="stat-num red">{len(missing)}</div>
        <div class="stat-label">Tidak Match</div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-num yellow">{len(df2_all)}</div>
        <div class="stat-label">Total File 2</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alert info">
      <span class="alert-icon">ℹ️</span>
      <span>Match menggunakan <b>NOPOL</b> dan <b>KUANTUM</b> secara bersamaan.
      Normalisasi spasi dan huruf kapital diterapkan otomatis.
      Download otomatis bypass Google Drive confirmation page.</span>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — MATCHED DATA
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">✅ Data Berhasil Ditemukan</div>',
                unsafe_allow_html=True)

    if found.empty:
        st.markdown('<div class="alert warn"><span class="alert-icon">⚠️</span>'
                    '0 surat jalan ditemukan. Lihat tabel di bawah untuk detail penyebabnya.</div>',
                    unsafe_allow_html=True)
    else:
        # Search filter
        search = st.text_input('', placeholder='🔍  Filter NOPOL...',
                               label_visibility='collapsed', key='search_found')
        disp = found.copy()
        if search.strip():
            disp = disp[disp['nopol'].str.contains(
                re.escape(norm_nopol(search.strip())), na=False, case=False)
            ].reset_index(drop=True)

        st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

        # ── BULK ACTION BUTTONS ────────────────────────────────────────────────
        b1, b2, b3, _ = st.columns([2, 2, 2, 4])
        with b1:
            do_zip    = st.button('📦  Download ZIP',    use_container_width=True)
        with b2:
            do_merge  = st.button('📄  Gabung 1 PDF',    use_container_width=True)
        with b3:
            do_cache  = st.button('⚡  Pre-load Semua',  use_container_width=True,
                                  help='Download semua ke memori agar per-baris instan')

        # ── PRE-LOAD ───────────────────────────────────────────────────────────
        if do_cache and not disp.empty:
            need = [r['surat_jalan'] for _, r in disp.iterrows()
                    if r['surat_jalan'] not in st.session_state.dl_cache]
            if not need:
                st.markdown('<div class="alert success"><span class="alert-icon">✅</span>'
                            'Semua file sudah ada di cache!</div>', unsafe_allow_html=True)
            else:
                cache_snap = dict(st.session_state.dl_cache)
                tasks_pre  = [{'idx': i, 'nopol': r['nopol'],
                                'kuantum': int(r['kuantum']), 'link': r['surat_jalan']}
                               for i, r in disp.iterrows()
                               if r['surat_jalan'] not in cache_snap]
                _, _, new_cache = run_downloads(
                    disp[disp['surat_jalan'].isin(need)].reset_index(drop=True),
                    label='Pre-load'
                )
                st.session_state.dl_cache.update(new_cache)

        # ── ZIP DOWNLOAD ───────────────────────────────────────────────────────
        if do_zip and not disp.empty:
            ok_files, fails, new_cache = run_downloads(disp)
            st.session_state.dl_cache.update(new_cache)
            if ok_files:
                st.download_button(
                    f'💾  Simpan ZIP ({len(ok_files)} file)',
                    make_zip(ok_files),
                    'surat_jalan_bulk.zip', 'application/zip',
                    key='dl_zip'
                )
            if fails:
                with st.expander(f'❌ {len(fails)} file gagal'):
                    for f in fails: st.write(f'• {f}')

        # ── MERGE PDF ─────────────────────────────────────────────────────────
        if do_merge and not disp.empty:
            ok_files, fails, new_cache = run_downloads(disp)
            st.session_state.dl_cache.update(new_cache)
            if ok_files:
                with st.spinner('Menggabungkan file menjadi 1 PDF...'):
                    ordered = [
                        new_cache.get(r['surat_jalan']) or
                        st.session_state.dl_cache.get(r['surat_jalan'])
                        for _, r in disp.iterrows()
                    ]
                    merged = merge_to_pdf([c for c in ordered if c])
                if merged:
                    st.markdown(
                        f'<div class="alert success"><span class="alert-icon">✅</span>'
                        f'<b>{len([c for c in ordered if c])}</b> file digabung — '
                        f'ukuran: <b>{len(merged)//1024:,} KB</b></div>',
                        unsafe_allow_html=True
                    )
                    st.download_button(
                        f'💾  Simpan PDF Gabungan',
                        merged, 'surat_jalan_gabungan.pdf', 'application/pdf',
                        key='dl_merged'
                    )
                else:
                    st.markdown(
                        '<div class="alert error"><span class="alert-icon">❌</span>'
                        'Gagal membuat PDF gabungan. Pastikan <code>pypdf</code>, '
                        '<code>reportlab</code>, dan <code>Pillow</code> terinstall.</div>',
                        unsafe_allow_html=True
                    )
            if fails:
                with st.expander(f'❌ {len(fails)} file tidak bisa digabung'):
                    for f in fails: st.write(f'• {f}')

        # ── PER-ROW TABLE ──────────────────────────────────────────────────────
        st.markdown('<div class="section-label">Detail Surat Jalan</div>',
                    unsafe_allow_html=True)

        # Header
        h = st.columns([0.5, 2.5, 1.5, 2.5, 1, 1.8])
        for col, lbl in zip(h, ['#', 'NOPOL', 'KUANTUM', 'Link', '👁', '⬇']):
            col.markdown(f'<span style="font-size:.7rem;font-weight:700;text-transform:uppercase;'
                         f'letter-spacing:1px;color:#64748b">{lbl}</span>',
                         unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#2d3048;margin:6px 0 10px">', unsafe_allow_html=True)

        for i, row in disp.iterrows():
            nopol   = row['nopol']
            kuantum = int(row['kuantum'])
            link    = row['surat_jalan']
            fid     = extract_fid(link)
            view_url = (f'https://drive.google.com/file/d/{fid}/view' if fid else link)

            cols = st.columns([0.5, 2.5, 1.5, 2.5, 1, 1.8])
            cols[0].markdown(f'<span style="font-size:.75rem;color:#64748b;'
                             f'font-family:\'JetBrains Mono\',monospace">#{i+1}</span>',
                             unsafe_allow_html=True)
            cols[1].markdown(f'<code style="color:#818cf8;font-size:.82rem">{nopol}</code>',
                             unsafe_allow_html=True)
            cols[2].markdown(f'<b style="color:#e2e8f0">{kuantum:,}</b>', unsafe_allow_html=True)
            cols[3].markdown(f'[🔗 Buka di Drive]({view_url})')

            with cols[4]:
                if st.button('👁', key=f'v_{i}', help='Toggle preview'):
                    st.session_state.active_preview = (
                        None if st.session_state.active_preview == i else i
                    )

            with cols[5]:
                cached = st.session_state.dl_cache.get(link)
                if cached:
                    ext  = ext_from_content(cached)
                    mime = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                    st.download_button(f'⬇ .{ext.upper()}', cached,
                                       safe_filename(nopol, kuantum, i, ext),
                                       mime, key=f'd_{i}')
                else:
                    if st.button('⬇ Unduh', key=f'db_{i}'):
                        with st.spinner(f'Mengunduh {nopol}...'):
                            ct = download_file(link)
                        if ct:
                            st.session_state.dl_cache[link] = ct
                            ext  = ext_from_content(ct)
                            mime = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                            st.download_button(
                                f'💾 .{ext.upper()}', ct,
                                safe_filename(nopol, kuantum, i, ext),
                                mime, key=f'ds_{i}'
                            )
                            st.rerun()
                        else:
                            st.markdown(
                                '<div class="alert error" style="padding:8px 12px;font-size:.75rem">'
                                '❌ Gagal. File mungkin private, link expired, atau timeout.</div>',
                                unsafe_allow_html=True
                            )

            if st.session_state.active_preview == i:
                purl = to_preview_url(link)
                if purl:
                    import streamlit.components.v1 as components
                    components.html(
                        f'<iframe src="{purl}" width="100%" height="680" '
                        f'style="border:1px solid #2d3048;border-radius:10px;background:#1a1d27" '
                        f'allow="autoplay"></iframe>',
                        height=700
                    )
                    st.caption(f'Preview kosong? → [buka di tab baru]({purl})')
                else:
                    st.markdown('<div class="alert error"><span class="alert-icon">❌</span>'
                                'Link preview tidak valid.</div>', unsafe_allow_html=True)

            st.markdown('<hr style="border-color:#1e2233;margin:4px 0">', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — UNMATCHED DATA
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">❌ Data Tidak Berhasil Match</div>',
                unsafe_allow_html=True)

    if missing.empty:
        st.markdown('<div class="alert success"><span class="alert-icon">🎉</span>'
                    '<b>Semua data berhasil dicocokkan!</b></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="alert error"><span class="alert-icon">❌</span>'
            f'<b>{len(missing)}</b> kombinasi NOPOL + KUANTUM tidak ditemukan.</div>',
            unsafe_allow_html=True
        )

        # Table A — nopol ada tapi kuantum beda
        if nopol_diff is not None and not nopol_diff.empty:
            st.markdown(
                f'<div class="table-card warn">'
                f'<div class="table-card-title warn">'
                f'⚠️ Tabel A — {len(nopol_diff)} NOPOL ditemukan, namun KUANTUM tidak cocok'
                f'</div></div>', unsafe_allow_html=True
            )
            sa = st.text_input('', placeholder='🔍 Filter Tabel A...', key='sa',
                                label_visibility='collapsed')
            da = nopol_diff.copy()
            if sa.strip():
                da = da[da['NOPOL'].str.contains(re.escape(norm_nopol(sa)), na=False, case=False)]
            st.dataframe(da, use_container_width=True, hide_index=True)
            c1, _ = st.columns([2, 8])
            with c1:
                st.download_button('📥 Export CSV', da.to_csv(index=False).encode(),
                                   'tabel_a_kuantum_beda.csv', 'text/csv', key='dla')

        # Table B — nopol tidak ada
        if nopol_miss is not None and not nopol_miss.empty:
            st.markdown(
                f'<div class="table-card error">'
                f'<div class="table-card-title error">'
                f'❌ Tabel B — {len(nopol_miss)} NOPOL tidak ada di File 2'
                f'</div></div>', unsafe_allow_html=True
            )
            sb = st.text_input('', placeholder='🔍 Filter Tabel B...', key='sb',
                                label_visibility='collapsed')
            db = nopol_miss.copy()
            if sb.strip():
                db = db[db['NOPOL'].str.contains(re.escape(norm_nopol(sb)), na=False, case=False)]
            st.dataframe(db, use_container_width=True, hide_index=True)
            c2, _ = st.columns([2, 8])
            with c2:
                st.download_button('📥 Export CSV', db.to_csv(index=False).encode(),
                                   'tabel_b_nopol_tidak_ada.csv', 'text/csv', key='dlb')

        # Table C — all unmatched combined
        with st.expander('📋 Tabel C — Semua tidak match (gabungan)'):
            all_m = missing.rename(columns={'nopol': 'NOPOL',
                                            'kuantum': 'Kuantum (File 1)'}).copy()
            all_m['Kuantum (File 1)'] = all_m['Kuantum (File 1)'].astype(int)
            sc = st.text_input('', placeholder='🔍 Filter...', key='sc',
                                label_visibility='collapsed')
            if sc.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(
                    re.escape(norm_nopol(sc)), na=False, case=False)]
            st.dataframe(all_m, use_container_width=True, hide_index=True)
            c3, _ = st.columns([2, 8])
            with c3:
                st.download_button('📥 Export CSV', all_m.to_csv(index=False).encode(),
                                   'tabel_c_semua_tidak_match.csv', 'text/csv', key='dlc')
