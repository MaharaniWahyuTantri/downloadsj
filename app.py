import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Tantri Imoet", page_icon="🚛", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #f5f7fa; color: #1a202c; }
.stApp { background: #f5f7fa; }
.main-header {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    border-radius: 14px; padding: 24px 32px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 4px 16px rgba(59,130,246,0.25);
}
.main-header h1 { font-size: 1.7rem; font-weight: 700; color: #fff; }
.main-header p  { font-size: 0.85rem; color: rgba(255,255,255,0.75); margin-top: 4px; }
.upload-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.upload-card h3 { font-size: 0.78rem; font-weight: 700; color: #3b82f6;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.upload-card p { font-size: 0.78rem; color: #64748b; }
.stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 16px 0; }
.stat-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 18px 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.stat-num { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-lbl { font-size: 0.7rem; color: #94a3b8; margin-top: 6px; text-transform: uppercase;
    letter-spacing: .6px; font-weight: 500; }
.c-blue{color:#3b82f6;} .c-green{color:#22c55e;} .c-red{color:#ef4444;} .c-yellow{color:#f59e0b;} .c-orange{color:#f97316;}
.warn-box    { background:#fffbeb; border:1px solid #fcd34d; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#92400e; line-height:1.6; }
.info-box    { background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#1e40af; line-height:1.6; }
.success-box { background:#f0fdf4; border:1px solid #86efac; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#14532d; line-height:1.6; }
.error-box   { background:#fef2f2; border:1px solid #fca5a5; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#7f1d1d; line-height:1.6; }
.section-label { font-size:0.7rem; font-weight:700; text-transform:uppercase;
    letter-spacing:1.5px; color:#94a3b8; margin:24px 0 12px;
    display:flex; align-items:center; gap:10px; }
.section-label::after { content:''; flex:1; height:1px; background:#e2e8f0; }
.table-card        { background:#fff; border:1px solid #e2e8f0; border-radius:12px;
    padding:20px; box-shadow:0 1px 6px rgba(0,0,0,0.06); margin:12px 0; }
.table-card-red    { background:#fff; border:1px solid #fca5a5; border-radius:12px;
    padding:20px; box-shadow:0 1px 6px rgba(239,68,68,0.08); margin:12px 0; }
.table-card-yellow { background:#fff; border:1px solid #fcd34d; border-radius:12px;
    padding:20px; box-shadow:0 1px 6px rgba(245,158,11,0.08); margin:12px 0; }
.table-title { font-size:0.92rem; font-weight:700; margin-bottom:14px; }
.table-title-red    { color:#dc2626; }
.table-title-yellow { color:#b45309; }
.stButton > button { background:#fff !important; color:#374151 !important;
    border:1px solid #d1d5db !important; border-radius:8px !important;
    font-size:0.82rem !important; font-weight:500 !important; padding:6px 14px !important;
    transition:all .15s !important; box-shadow:0 1px 3px rgba(0,0,0,0.06) !important; }
.stButton > button:hover { background:#eff6ff !important; border-color:#3b82f6 !important;
    color:#1d4ed8 !important; }
div[data-testid="stFileUploader"] { background:#fff; border:2px dashed #cbd5e1; border-radius:10px; }
.stProgress > div > div { background:#3b82f6 !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 6px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    color: #64748b !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #eff6ff !important;
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def norm_nopol(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = str(v).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm_kuantum(v):
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except:
        return None

def find_col(df, kws):
    for col in df.columns:
        c = col.lower().replace(' ', '').replace('_', '')
        for k in kws:
            if k.replace(' ', '').replace('_', '') in c:
                return col
    return None

def extract_fid(link):
    if not isinstance(link, str) or not link.strip():
        return None
    for p in [r'/file/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)',
              r'/d/([a-zA-Z0-9_-]+)', r'open\?id=([a-zA-Z0-9_-]+)']:
        m = re.search(p, link.strip())
        if m and len(m.group(1)) >= 15:
            return m.group(1)
    return None

def to_preview(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def detect_file_type(content):
    if not content or len(content) < 4:
        return 'unknown'
    sig = content[:8]
    if sig[:4] == b'%PDF':
        return 'pdf'
    if sig[:3] == b'\xff\xd8\xff':
        return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    try:
        snippet = content[:2000].decode('utf-8', errors='ignore').lower()
        if '<html' in snippet or '<!doctype' in snippet:
            return 'html'
    except Exception:
        pass
    return 'unknown'

def _get_bytes(resp):
    return b''.join(resp.iter_content(chunk_size=65536))

def download_gdrive(fid, retries=4, timeout=45):
    if not fid:
        return None
    session = requests.Session()
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
    })
    base_url = f'https://drive.google.com/uc?export=download&id={fid}'

    for attempt in range(retries):
        try:
            r1   = session.get(base_url, timeout=timeout, stream=True, allow_redirects=True)
            raw1 = _get_bytes(r1)
            if 'text/html' not in r1.headers.get('Content-Type', ''):
                if detect_file_type(raw1) != 'html' and len(raw1) > 512:
                    return raw1
            html = raw1.decode('utf-8', errors='ignore')
            m = re.search(r'name="confirm"\s+value="([^"]+)"', html)
            if m:
                r2 = session.get(f'{base_url}&confirm={m.group(1)}',
                                 timeout=timeout, stream=True, allow_redirects=True)
                raw2 = _get_bytes(r2)
                if detect_file_type(raw2) != 'html' and len(raw2) > 512:
                    return raw2
            r3   = session.get(f'{base_url}&confirm=t',
                               timeout=timeout, stream=True, allow_redirects=True)
            raw3 = _get_bytes(r3)
            if detect_file_type(raw3) != 'html' and len(raw3) > 512:
                return raw3
            r4   = session.get(f'https://drive.google.com/uc?id={fid}&export=download&confirm=t',
                               timeout=timeout, stream=True, allow_redirects=True)
            raw4 = _get_bytes(r4)
            if detect_file_type(raw4) != 'html' and len(raw4) > 512:
                return raw4
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
        r = requests.get(link.strip(), timeout=45, stream=True,
                         headers={'User-Agent': 'Mozilla/5.0'})
        raw = _get_bytes(r)
        if detect_file_type(raw) != 'html' and len(raw) > 512:
            return raw
    except Exception:
        pass
    return None

def infer_extension(content, fallback='pdf'):
    return {'pdf': 'pdf', 'jpg': 'jpg', 'png': 'png'}.get(
        detect_file_type(content) if content else 'x', fallback)

def make_safe_filename(nopol, kuantum, idx, ext):
    safe = re.sub(r'[\\/:*?"<>|]', '_', str(nopol))
    return f'{safe}_{kuantum}_{idx+1}.{ext}'

def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()

def img_bytes_to_pdf(img_bytes):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Image as RLImage
        from PIL import Image as PILImage

        pil = PILImage.open(io.BytesIO(img_bytes))
        w_px, h_px = pil.size
        a4_w, a4_h = A4
        scale = min(a4_w / w_px, a4_h / h_px)
        rl_w, rl_h = w_px * scale, h_px * scale

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=(rl_w + 20, rl_h + 20),
                                rightMargin=10, leftMargin=10,
                                topMargin=10, bottomMargin=10)
        doc.build([RLImage(io.BytesIO(img_bytes), width=rl_w, height=rl_h)])
        buf.seek(0)
        return buf.read()
    except Exception:
        return None

def merge_pdfs(content_list):
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfWriter, PdfReader
        except ImportError:
            return None

    writer = PdfWriter()
    for ct in content_list:
        if not ct:
            continue
        ftype = detect_file_type(ct)
        if ftype == 'pdf':
            try:
                for page in PdfReader(io.BytesIO(ct)).pages:
                    writer.add_page(page)
            except Exception:
                continue
        elif ftype in ('jpg', 'png'):
            converted = img_bytes_to_pdf(ct)
            if converted:
                try:
                    for page in PdfReader(io.BytesIO(converted)).pages:
                        writer.add_page(page)
                except Exception:
                    continue

    if len(writer.pages) == 0:
        return None
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def read_file(f):
    return pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)

def load_file1(df):
    nc = find_col(df, ['nopol','nomor polisi','no pol','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan. Tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan. Tersedia: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol']   = df[nc].apply(norm_nopol)
    out['kuantum'] = df[kc].apply(norm_kuantum)
    out = out[(out['nopol'] != '') & out['nopol'].notna()].dropna(subset=['kuantum'])
    return out[out['kuantum'] > 0].reset_index(drop=True)

def load_file2(raw_df):
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()
    frow = df.iloc[0].tolist()
    if any(str(v).upper().strip() in ['NOPOL','KUANTUM','FOTO SURAT JALAN','SURAT JALAN'] for v in frow):
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)
    nc = find_col(df, ['nopol','nomor polisi','no pol','no truk','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    lc = find_col(df, ['surat jalan','suratjalan','foto surat','foto','link','url','drive','gdrive'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 2. Tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan di File 2. Tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not lc:
        st.error(f"❌ Kolom SURAT JALAN tidak ditemukan di File 2. Tersedia: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else '')
    out['kuantum']     = df[kc].apply(norm_kuantum)
    out['surat_jalan'] = df[lc].astype(str).str.strip()
    out = out[out['nopol'] != '']
    out = out[out['nopol'].str.upper() != 'NOPOL']
    out = out.dropna(subset=['kuantum'])
    out = out[out['kuantum'] > 0]
    valid = (out['surat_jalan'].str.startswith('http') |
             out['surat_jalan'].str.lower().str.endswith('.jpg') |
             out['surat_jalan'].str.lower().str.endswith('.pdf') |
             out['surat_jalan'].str.lower().str.endswith('.png'))
    return out[valid].reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# THREAD-SAFE WORKERS
# ══════════════════════════════════════════════════════════════════════════════

def _worker(task, cache_snapshot):
    link = task['link']
    ct   = cache_snapshot.get(link)
    if ct is None:
        ct = download_file(link)
    return {
        'idx':     task['idx'],
        'nopol':   task['nopol'],
        'kuantum': task['kuantum'],
        'link':    link,
        'content': ct,
    }

def run_bulk_download(disp):
    cache_snapshot = dict(st.session_state.dl_cache)
    tasks = [
        {'idx': i, 'nopol': row['nopol'],
         'kuantum': int(row['kuantum']), 'link': row['surat_jalan']}
        for i, row in disp.iterrows()
    ]

    prog       = st.progress(0)
    stxt       = st.empty()
    ok_files   = {}
    new_cache  = {}
    fail_list  = []
    done_n     = 0
    total      = len(tasks)
    stxt.text(f'Mengunduh 0 / {total} file...')

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_worker, t, cache_snapshot): t for t in tasks}
        for fut in as_completed(futs):
            res = fut.result()
            ct  = res['content']
            if ct:
                new_cache[res['link']] = ct
                ext  = infer_extension(ct)
                fn   = make_safe_filename(res['nopol'], res['kuantum'], res['idx'], ext)
                base, c = fn, 1
                while fn in ok_files:
                    fn = base.rsplit('.', 1)[0] + f'_{c}.' + base.rsplit('.', 1)[-1]
                    c += 1
                ok_files[fn] = ct
            else:
                fail_list.append(f"{res['nopol']} ({res['kuantum']})")
            done_n += 1
            prog.progress(done_n / total)
            stxt.text(f'Mengunduh {done_n}/{total} — ✅ {len(ok_files)} | ❌ {len(fail_list)}')

    stxt.text(f'Selesai — ✅ {len(ok_files)} berhasil | ❌ {len(fail_list)} gagal')
    return ok_files, fail_list, new_cache

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
for _k in ['result_df','missing_df','nopol_diff_df','nopol_miss_df',
           'active_preview','df2_debug','df1_debug','dl_cache']:
    if _k not in st.session_state:
        st.session_state[_k] = None
if st.session_state.dl_cache is None:
    st.session_state.dl_cache = {}

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <div style="font-size:2.4rem">🚛</div>
  <div>
    <h1>Download Surat Jalan in Bulk</h1>
    <p>Match NOPOL + KUANTUM → Download ZIP atau Gabung 1 PDF — File dijamin bisa dibuka ✅</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)
_c1, _c2 = st.columns(2)
with _c1:
    st.markdown('<div class="upload-card"><h3>📋 File 1 — Target</h3>'
                '<p>Kolom: NOPOL, KUANTUM (atau: Nomor Polisi, Tonase, dll)</p></div>',
                unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv','xlsx','xls'],
                              key='f1', label_visibility='collapsed')
with _c2:
    st.markdown('<div class="upload-card"><h3>🗄️ File 2 — Database Surat Jalan</h3>'
                '<p>Kolom: NOPOL, KUANTUM, Foto Surat Jalan (link Google Drive)</p></div>',
                unsafe_allow_html=True)
    file2 = st.file_uploader("File 2", type=['csv','xlsx','xls'],
                              key='f2', label_visibility='collapsed')

_pb, _ = st.columns([2, 8])
with _pb:
    process = st.button('⚙️ Proses Data', use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS
# ══════════════════════════════════════════════════════════════════════════════
if process:
    if not file1 or not file2:
        st.warning('⚠️ Upload kedua file terlebih dahulu.')
    else:
        with st.spinner('Memproses data...'):
            df1 = load_file1(read_file(file1))
            df2 = load_file2(read_file(file2))
            if df1.empty or df2.empty:
                st.stop()

            result_rows = []
            for idx, row1 in df1.iterrows():
                m = df2[(df2['nopol'] == row1['nopol']) & (df2['kuantum'] == row1['kuantum'])]
                hm = m[m['surat_jalan'].str.startswith('http')]
                if len(hm) > 0:
                    for _, r2 in hm.iterrows():
                        result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                            'surat_jalan': r2['surat_jalan'], '_f1_idx': idx})
                else:
                    result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                        'surat_jalan': None, '_f1_idx': idx})

            result = pd.DataFrame(result_rows)
            found  = result[result['surat_jalan'].notna() &
                            result['surat_jalan'].str.startswith('http', na=False)
                            ].copy().reset_index(drop=True)

            matched = set(found['_f1_idx'].tolist())
            missing = pd.DataFrame(
                [{'nopol': r['nopol'], 'kuantum': r['kuantum']}
                 for i, r in df1.iterrows() if i not in matched]
            ).drop_duplicates(subset=['nopol','kuantum']).reset_index(drop=True)

            diff_rows, miss_rows = [], []
            for _, row in missing.iterrows():
                f2m = df2[df2['nopol'] == row['nopol']]
                if len(f2m) > 0:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique().tolist())
                    d  = ', '.join(map(str, ks[:8])) + (f' (+{len(ks)-8})' if len(ks) > 8 else '')
                    diff_rows.append({'NOPOL': row['nopol'], 'Kuantum File 1': int(row['kuantum']),
                                      'Kuantum di File 2': d, 'Status': '⚠️ Kuantum tidak cocok'})
                else:
                    miss_rows.append({'NOPOL': row['nopol'], 'Kuantum File 1': int(row['kuantum']),
                                      'Status': '❌ NOPOL tidak ada di File 2'})

            st.session_state.result_df      = found
            st.session_state.missing_df     = missing
            st.session_state.nopol_diff_df  = pd.DataFrame(diff_rows)
            st.session_state.nopol_miss_df  = pd.DataFrame(miss_rows)
            st.session_state.df2_debug      = df2
            st.session_state.df1_debug      = df1
            st.session_state.active_preview = None
            st.session_state.dl_cache       = {}

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

    # ── SUMMARY ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Ringkasan Hasil</div>', unsafe_allow_html=True)
    n_match     = len(found)
    n_diff_k    = len(nopol_diff) if nopol_diff is not None else 0
    n_miss_nopol= len(nopol_miss) if nopol_miss is not None else 0
    n_all_miss  = len(missing)

    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num c-green">{n_match}</div>
        <div class="stat-lbl">✅ Match (NOPOL + Kuantum)</div></div>
      <div class="stat-card"><div class="stat-num c-yellow">{n_diff_k}</div>
        <div class="stat-lbl">⚠️ NOPOL Ada, Kuantum Beda</div></div>
      <div class="stat-card"><div class="stat-num c-red">{n_miss_nopol}</div>
        <div class="stat-lbl">❌ NOPOL Tidak Ada</div></div>
      <div class="stat-card"><div class="stat-num c-orange">{n_all_miss}</div>
        <div class="stat-lbl">🔴 Total Tidak Match</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Match ketat:</b> NOPOL <em>dan</em> KUANTUM harus sama persis.
    Normalisasi otomatis spasi &amp; huruf besar/kecil.<br>
    🔧 <b>Download fix:</b> Auto-bypass Google Drive confirmation page.
    Tersedia <b>📦 ZIP</b> (file terpisah) dan <b>📄 Gabung 1 PDF</b>.
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        f"✅ Match Semua ({n_match})",
        f"⚠️ Tidak Match Kuantum ({n_diff_k})",
        f"❌ Tidak Match NOPOL ({n_miss_nopol})",
        f"🔴 Semua Tidak Match ({n_all_miss})",
    ])

    # ────────────────────────────────────────────────────────────────────────
    # TAB 1 — MATCH (NOPOL + KUANTUM)
    # ────────────────────────────────────────────────────────────────────────
    with tab1:
        if len(found) == 0:
            st.markdown("""
            <div class="warn-box">
            ⚠️ <strong>0 surat jalan ditemukan.</strong>
            Lihat tab lain untuk detail penyebabnya.
            </div>
            """, unsafe_allow_html=True)
        else:
            search = st.text_input('cari', placeholder='🔍  Ketik NOPOL untuk filter...',
                                   label_visibility='collapsed', key='search_found')
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(
                    re.escape(norm_nopol(search.strip())), na=False, case=False)
                ].reset_index(drop=True)

            st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

            # ── TOMBOL BULK ──────────────────────────────────────────────────
            bc1, bc2, bc3, _ = st.columns([2, 2, 2, 4])
            with bc1:
                do_zip    = st.button('📦 Download ZIP',    use_container_width=True,
                                      help='Semua file terpisah dalam satu ZIP', key='btn_zip')
            with bc2:
                do_merge  = st.button('📄 Gabung 1 PDF',    use_container_width=True,
                                      help='Gabungkan semua menjadi 1 file PDF', key='btn_merge')
            with bc3:
                do_preload = st.button('⚡ Pre-load Cache', use_container_width=True,
                                       help='Download semua ke memori agar tombol per baris instan',
                                       key='btn_preload')

            # ── PRE-LOAD ─────────────────────────────────────────────────────
            if do_preload and len(disp) > 0:
                links_needed = [row['surat_jalan'] for _, row in disp.iterrows()
                                if row['surat_jalan'] not in st.session_state.dl_cache]
                if not links_needed:
                    st.success('✅ Semua file sudah ada di cache!')
                else:
                    cache_snap = dict(st.session_state.dl_cache)
                    tasks_pre  = [{'idx': i, 'nopol': row['nopol'],
                                    'kuantum': int(row['kuantum']), 'link': row['surat_jalan']}
                                   for i, row in disp.iterrows()
                                   if row['surat_jalan'] not in cache_snap]
                    prog = st.progress(0)
                    stxt = st.empty()
                    ok_n, fail_n, done_n = 0, 0, 0
                    new_cache = {}
                    with ThreadPoolExecutor(max_workers=8) as ex:
                        futs = {ex.submit(_worker, t, cache_snap): t for t in tasks_pre}
                        for fut in as_completed(futs):
                            res = fut.result()
                            if res['content']:
                                new_cache[res['link']] = res['content']
                                ok_n += 1
                            else:
                                fail_n += 1
                            done_n += 1
                            prog.progress(done_n / len(tasks_pre))
                            stxt.text(f'Pre-load {done_n}/{len(tasks_pre)} — ✅ {ok_n} | ❌ {fail_n}')
                    st.session_state.dl_cache.update(new_cache)
                    stxt.text(f'Pre-load selesai: ✅ {ok_n} | ❌ {fail_n}')

            # ── DOWNLOAD ZIP ─────────────────────────────────────────────────
            if do_zip and len(disp) > 0:
                ok_files, fail_list, new_cache = run_bulk_download(disp)
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    st.download_button(
                        f'💾 Simpan ZIP ({len(ok_files)} file)',
                        make_zip(ok_files),
                        'surat_jalan_semua.zip',
                        'application/zip',
                        key='dl_zip_result'
                    )
                if fail_list:
                    with st.expander(f'❌ {len(fail_list)} file gagal diunduh'):
                        for f in fail_list:
                            st.write(f'• {f}')

            # ── GABUNG 1 PDF ─────────────────────────────────────────────────
            if do_merge and len(disp) > 0:
                ok_files, fail_list, new_cache = run_bulk_download(disp)
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    with st.spinner('Menggabungkan semua file menjadi 1 PDF...'):
                        ordered = []
                        for i, row in disp.iterrows():
                            ct = new_cache.get(row['surat_jalan']) or \
                                 st.session_state.dl_cache.get(row['surat_jalan'])
                            if ct:
                                ordered.append(ct)
                        merged = merge_pdfs(ordered)
                    if merged:
                        st.success(f'✅ {len(ordered)} file berhasil digabung menjadi 1 PDF '
                                   f'({len(merged)//1024:,} KB)')
                        st.download_button(
                            f'💾 Simpan PDF Gabungan ({len(ordered)} surat jalan)',
                            merged,
                            'surat_jalan_gabungan.pdf',
                            'application/pdf',
                            key='dl_merged_pdf'
                        )
                    else:
                        st.error(
                            '❌ Gagal membuat PDF gabungan. '
                            'Pastikan `pypdf` dan `reportlab` terinstall: '
                            '`pip install pypdf reportlab Pillow`'
                        )
                if fail_list:
                    with st.expander(f'❌ {len(fail_list)} file tidak bisa digabung'):
                        for f in fail_list:
                            st.write(f'• {f}')

            # ── TABEL DETAIL PER BARIS ────────────────────────────────────────
            st.markdown('<div class="section-label">Detail per Surat Jalan</div>',
                        unsafe_allow_html=True)
            hcols = st.columns([0.5, 2.5, 1.5, 2, 1.2, 1.8])
            for col, lbl in zip(hcols, ['No.', 'NOPOL', 'KUANTUM', 'Link GDrive', '👁 Preview', '⬇ Download']):
                col.markdown(f'**{lbl}**')
            st.divider()

            for i, row in disp.iterrows():
                nopol   = row['nopol']
                kuantum = int(row['kuantum'])
                link    = row['surat_jalan']
                fid     = extract_fid(link)
                cols    = st.columns([0.5, 2.5, 1.5, 2, 1.2, 1.8])

                cols[0].markdown(f'`#{i+1}`')
                cols[1].markdown(f'`{nopol}`')
                cols[2].markdown(f'**{kuantum:,}**')
                if fid:
                    cols[3].markdown(f'[🔗 Buka](https://drive.google.com/file/d/{fid}/view)')
                else:
                    cols[3].markdown(f'[🔗 Buka]({link})')

                with cols[4]:
                    if st.button('👁️ Lihat', key=f'v_{i}'):
                        st.session_state.active_preview = (
                            None if st.session_state.active_preview == i else i
                        )

                with cols[5]:
                    cached = st.session_state.dl_cache.get(link)
                    if cached:
                        ext   = infer_extension(cached)
                        fname = make_safe_filename(nopol, kuantum, i, ext)
                        mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                        st.download_button(f'⬇️ .{ext.upper()}', cached, fname, mime,
                                           key=f'd_{i}')
                    else:
                        if st.button('⬇️ Download', key=f'db_{i}'):
                            with st.spinner(f'Mengunduh {nopol}...'):
                                ct = download_file(link)
                            if ct:
                                st.session_state.dl_cache[link] = ct
                                ext   = infer_extension(ct)
                                fname = make_safe_filename(nopol, kuantum, i, ext)
                                mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                st.download_button(f'💾 Simpan .{ext.upper()}', ct,
                                                   fname, mime, key=f'ds_{i}')
                                st.success(f'✅ {fname} siap disimpan!')
                            else:
                                st.error(
                                    '❌ Gagal. Kemungkinan: file private, link expired, '
                                    'atau timeout. Coba buka link GDrive secara manual.'
                                )

                if st.session_state.active_preview == i:
                    purl = to_preview(link)
                    if purl:
                        import streamlit.components.v1 as components
                        components.html(
                            f'<iframe src="{purl}" width="100%" height="680" '
                            f'style="border:1px solid #e2e8f0;border-radius:10px;background:#fff" '
                            f'allow="autoplay"></iframe>',
                            height=700
                        )
                        st.caption(f'Preview kosong? → [buka di tab baru]({purl})')
                    else:
                        st.error('Link preview tidak valid.')

    # ────────────────────────────────────────────────────────────────────────
    # TAB 2 — TIDAK MATCH KUANTUM (NOPOL ADA, KUANTUM BEDA)
    # ────────────────────────────────────────────────────────────────────────
    with tab2:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown('<div class="success-box">🎉 <b>Tidak ada perbedaan kuantum!</b> '
                        'Semua NOPOL yang ada di File 1 juga memiliki kuantum yang cocok di File 2.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="warn-box">⚠️ <b>{len(nopol_diff)} data</b> — NOPOL ditemukan di File 2, '
                f'namun kuantumnya tidak cocok dengan File 1.</div>',
                unsafe_allow_html=True
            )
            sd = st.text_input('', placeholder='🔍 Filter berdasarkan NOPOL...',
                               label_visibility='collapsed', key='sd')
            dd = nopol_diff.copy()
            if sd.strip():
                dd = dd[dd['NOPOL'].str.contains(re.escape(norm_nopol(sd)), na=False, case=False)
                        ].reset_index(drop=True)
            st.dataframe(dd, use_container_width=True, hide_index=True)
            _ca, _ = st.columns([2, 8])
            with _ca:
                st.download_button('📥 Export CSV',
                                   dd.to_csv(index=False).encode('utf-8'),
                                   'tidak_match_kuantum.csv', 'text/csv', key='dl_a')

    # ────────────────────────────────────────────────────────────────────────
    # TAB 3 — TIDAK MATCH NOPOL (NOPOL TIDAK ADA DI FILE 2)
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        if nopol_miss is None or nopol_miss.empty:
            st.markdown('<div class="success-box">🎉 <b>Semua NOPOL ditemukan di File 2!</b></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="error-box">❌ <b>{len(nopol_miss)} data</b> — NOPOL sama sekali tidak '
                f'ada di File 2.</div>',
                unsafe_allow_html=True
            )
            sm = st.text_input('', placeholder='🔍 Filter berdasarkan NOPOL...',
                               label_visibility='collapsed', key='sm')
            dm = nopol_miss.copy()
            if sm.strip():
                dm = dm[dm['NOPOL'].str.contains(re.escape(norm_nopol(sm)), na=False, case=False)
                        ].reset_index(drop=True)
            st.dataframe(dm, use_container_width=True, hide_index=True)
            _cb, _ = st.columns([2, 8])
            with _cb:
                st.download_button('📥 Export CSV',
                                   dm.to_csv(index=False).encode('utf-8'),
                                   'tidak_match_nopol.csv', 'text/csv', key='dl_b')

    # ────────────────────────────────────────────────────────────────────────
    # TAB 4 — SEMUA TIDAK MATCH (GABUNGAN TAB 2 + TAB 3)
    # ────────────────────────────────────────────────────────────────────────
    with tab4:
        if missing.empty:
            st.markdown('<div class="success-box">🎉 <b>Semua data berhasil dicocokkan!</b> '
                        'Tidak ada data yang tidak match.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="error-box">🔴 <b>{len(missing)} total kombinasi tidak match</b> '
                f'(gabungan dari kuantum beda + NOPOL tidak ada).</div>',
                unsafe_allow_html=True
            )
            all_m = missing.rename(columns={'nopol': 'NOPOL', 'kuantum': 'Kuantum File 1'}).copy()
            all_m['Kuantum File 1'] = all_m['Kuantum File 1'].astype(int)

            # Tambah kolom Keterangan
            def get_keterangan(row):
                nopol = row['NOPOL']
                k_f1  = row['Kuantum File 1']
                f2m   = df2_all[df2_all['nopol'] == nopol]
                if len(f2m) > 0:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique().tolist())
                    d  = ', '.join(map(str, ks[:5])) + (f' (+{len(ks)-5} lagi)' if len(ks) > 5 else '')
                    return f'⚠️ Kuantum beda (di File 2: {d})'
                return '❌ NOPOL tidak ada di File 2'
            all_m['Keterangan'] = all_m.apply(get_keterangan, axis=1)

            sa = st.text_input('', placeholder='🔍 Filter...',
                               label_visibility='collapsed', key='sa')
            if sa.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(
                    re.escape(norm_nopol(sa)), na=False, case=False)].reset_index(drop=True)

            st.dataframe(all_m, use_container_width=True, hide_index=True)

            col_exp, col_dl, _ = st.columns([1.5, 1.5, 7])
            with col_exp:
                with st.expander('📊 Ringkasan'):
                    st.markdown(f"""
                    - ⚠️ **Kuantum beda:** {n_diff_k} data
                    - ❌ **NOPOL tidak ada:** {n_miss_nopol} data
                    - 🔴 **Total tidak match:** {n_all_miss} data
                    """)
            with col_dl:
                st.download_button('📥 Export CSV',
                                   all_m.to_csv(index=False).encode('utf-8'),
                                   'semua_tidak_match.csv', 'text/csv', key='dl_c')
