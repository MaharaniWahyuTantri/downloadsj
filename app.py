import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

st.set_page_config(
    page_title="Tantri Imoet — Surat Jalan Bulk Downloader",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #f0f4f8; color: #1a202c; }
.stApp { background: #f0f4f8; }

/* ── HEADER ── */
.main-header {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 20px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.30);
    position: relative; overflow: hidden;
}
.main-header::before {
    content: ''; position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px; border-radius: 50%;
    background: rgba(255,255,255,0.06);
}
.main-header::after {
    content: ''; position: absolute; bottom: -30px; right: 120px;
    width: 120px; height: 120px; border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.main-header .truck-icon { font-size: 3rem; filter: drop-shadow(0 2px 8px rgba(0,0,0,.2)); }
.main-header h1 { font-size: 1.75rem; font-weight: 800; color: #fff; line-height: 1.2; }
.main-header p  { font-size: 0.875rem; color: rgba(255,255,255,0.80); margin-top: 6px; line-height: 1.5; }
.header-badge {
    background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px; padding: 4px 12px; font-size: 0.72rem; color: #fff;
    font-weight: 600; letter-spacing: 0.5px; display: inline-block; margin-top: 8px;
    backdrop-filter: blur(4px);
}

/* ── STEP INDICATOR ── */
.step-bar {
    display: flex; align-items: center; gap: 0; margin: 16px 0 24px;
    background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 16px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.05);
    overflow: hidden;
}
.step-item {
    display: flex; align-items: center; gap: 10px; flex: 1;
    position: relative;
}
.step-item:not(:last-child)::after {
    content: ''; position: absolute; right: 0; top: 50%;
    transform: translateY(-50%); width: 100%; height: 2px;
    background: #e2e8f0; z-index: 0;
}
.step-circle {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; flex-shrink: 0; position: relative; z-index: 1;
}
.step-circle.done   { background: #22c55e; color: #fff; }
.step-circle.active { background: #3b82f6; color: #fff; box-shadow: 0 0 0 4px rgba(59,130,246,0.20); }
.step-circle.idle   { background: #f1f5f9; color: #94a3b8; border: 2px solid #e2e8f0; }
.step-label { font-size: 0.78rem; font-weight: 600; }
.step-label.done   { color: #16a34a; }
.step-label.active { color: #1d4ed8; }
.step-label.idle   { color: #94a3b8; }
.step-desc { font-size: 0.68rem; color: #94a3b8; margin-top: 1px; }
.step-connector { flex: 1; height: 2px; background: #e2e8f0; }
.step-connector.done { background: #22c55e; }

/* ── UPLOAD CARDS ── */
.upload-card {
    background: #fff; border: 2px solid #e2e8f0; border-radius: 14px;
    padding: 20px 22px; margin-bottom: 12px; transition: border-color .2s, box-shadow .2s;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.upload-card:hover { border-color: #93c5fd; box-shadow: 0 4px 16px rgba(59,130,246,.10); }
.upload-card.has-file { border-color: #86efac; background: #f0fdf4; }
.upload-card-header {
    display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
}
.upload-card-icon {
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
}
.upload-card-icon.blue { background: #eff6ff; }
.upload-card-icon.green { background: #f0fdf4; }
.upload-card-title { font-size: 0.9rem; font-weight: 700; color: #1e293b; }
.upload-card-sub   { font-size: 0.75rem; color: #64748b; margin-top: 2px; }
.col-badge {
    display: inline-block; background: #f1f5f9; border: 1px solid #e2e8f0;
    border-radius: 4px; padding: 2px 7px; font-size: 0.68rem; font-family: monospace;
    color: #475569; margin: 2px;
}
.col-badge.required { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }

/* ── STAT CARDS ── */
.stat-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 14px; margin: 20px 0; }
.stat-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
    padding: 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.05);
    transition: transform .15s, box-shadow .15s; cursor: default;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.08); }
.stat-card-icon { font-size: 1.4rem; margin-bottom: 8px; }
.stat-num {
    font-family: 'JetBrains Mono', monospace; font-size: 2.2rem;
    font-weight: 700; line-height: 1;
}
.stat-lbl { font-size: 0.68rem; color: #94a3b8; margin-top: 8px;
    text-transform: uppercase; letter-spacing: .7px; font-weight: 600; }
.stat-card.green { border-top: 3px solid #22c55e; }
.stat-card.purple{ border-top: 3px solid #a855f7; }
.stat-card.yellow{ border-top: 3px solid #f59e0b; }
.stat-card.red   { border-top: 3px solid #ef4444; }
.stat-card.orange{ border-top: 3px solid #f97316; }
.c-blue{color:#3b82f6;} .c-green{color:#22c55e;} .c-red{color:#ef4444;}
.c-yellow{color:#f59e0b;} .c-orange{color:#f97316;} .c-purple{color:#a855f7;}

/* ── ALERT BOXES ── */
.alert {
    border-radius: 12px; padding: 14px 18px; margin: 12px 0;
    font-size: 0.855rem; line-height: 1.65; display: flex; gap: 10px;
    align-items: flex-start;
}
.alert-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
.alert.warn    { background:#fffbeb; border:1px solid #fcd34d; color:#78350f; }
.alert.info    { background:#eff6ff; border:1px solid #bfdbfe; color:#1e3a8a; }
.alert.success { background:#f0fdf4; border:1px solid #86efac; color:#14532d; }
.alert.error   { background:#fef2f2; border:1px solid #fca5a5; color:#7f1d1d; }
.alert.purple  { background:#fdf4ff; border:1px solid #e9d5ff; color:#581c87; }
.alert.sky     { background:#f0f9ff; border:1px solid #7dd3fc; color:#0c4a6e; }

/* ── SECTION LABEL ── */
.section-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #94a3b8; margin: 28px 0 14px;
    display: flex; align-items: center; gap: 10px;
}
.section-label::after { content:''; flex:1; height:1px; background:#e2e8f0; }

/* ── TABLE HEADER ── */
.tbl-header {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px 8px 0 0;
    padding: 10px 12px; font-size: 0.72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px; color: #64748b;
}
.tbl-row {
    background: #fff; border: 1px solid #e2e8f0; border-top: none;
    padding: 10px 12px; transition: background .1s;
}
.tbl-row:hover { background: #f8fafc; }
.tbl-row:last-child { border-radius: 0 0 8px 8px; }

/* ── NOPOL PILL ── */
.nopol-pill {
    display: inline-block; background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe; border-radius: 6px;
    padding: 3px 10px; font-family: monospace; font-size: 0.82rem; font-weight: 600;
}
.nopol-pill.dup { background: #fdf4ff; color: #7c3aed; border-color: #d8b4fe; }

/* ── BUTTONS ── */
.stButton > button {
    background: #fff !important; color: #374151 !important;
    border: 1px solid #d1d5db !important; border-radius: 8px !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    padding: 7px 16px !important; transition: all .15s !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.06) !important;
}
.stButton > button:hover {
    background: #eff6ff !important; border-color: #3b82f6 !important;
    color: #1d4ed8 !important; box-shadow: 0 2px 8px rgba(59,130,246,.12) !important;
}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"] {
    background: #fff; border: 2px dashed #cbd5e1; border-radius: 10px;
}
div[data-testid="stFileUploader"]:hover { border-color: #93c5fd; }

/* ── PROGRESS ── */
.stProgress > div > div { background: linear-gradient(90deg,#3b82f6,#6366f1) !important; border-radius: 8px !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #fff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 6px; margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-size: 0.82rem !important;
    font-weight: 500 !important; padding: 8px 14px !important;
    color: #64748b !important; border: none !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #eff6ff !important; color: #1d4ed8 !important; font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── ACTION BUTTON ROW ── */
.action-bar {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 14px 18px; margin: 14px 0; display: flex; gap: 10px;
    align-items: center; flex-wrap: wrap;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

/* ── DUP GROUP BANNER ── */
.dup-group-banner {
    background: linear-gradient(135deg,#fdf4ff,#f5f3ff);
    border: 1px solid #d8b4fe; border-radius: 10px;
    padding: 12px 18px; margin: 14px 0 6px;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}

/* ── SIDEBAR HELP ── */
.help-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px; font-size: 0.8rem;
}
.help-card h4 { font-size: 0.8rem; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.help-card p, .help-card li { color: #475569; line-height: 1.6; }
.help-card ul { padding-left: 16px; }

/* ── EMPTY STATE ── */
.empty-state {
    text-align: center; padding: 48px 24px; color: #94a3b8;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 12px; }
.empty-state h3 { font-size: 1rem; font-weight: 600; color: #64748b; margin-bottom: 8px; }
.empty-state p  { font-size: 0.82rem; line-height: 1.6; max-width: 320px; margin: 0 auto; }

/* ── SEARCH BOX ── */
.stTextInput > div > div > input {
    border-radius: 8px !important; border: 1px solid #e2e8f0 !important;
    font-size: 0.85rem !important; padding: 10px 14px !important;
    background: #fff !important;
}
.stTextInput > div > div > input:focus { border-color: #93c5fd !important; box-shadow: 0 0 0 3px rgba(147,197,253,.25) !important; }

/* ── SIMILARITY BADGE ── */
.sim-badge {
    display: inline-block; border-radius: 6px;
    padding: 3px 10px; font-size: 0.75rem; font-weight: 700;
}
.sim-high   { background: #dcfce7; color: #16a34a; }
.sim-medium { background: #fef9c3; color: #854d0e; }
.sim-low    { background: #fee2e2; color: #b91c1c; }

/* ── SCROLLABLE TABLE WRAPPER ── */
.table-scroll { max-height: 600px; overflow-y: auto; }

/* ── DIVIDER ── */
.styled-divider { border: none; border-top: 1px solid #e2e8f0; margin: 8px 0; }

/* hide streamlit branding */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES (unchanged logic, same as before)
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
    if sig[:4] == b'%PDF':              return 'pdf'
    if sig[:3] == b'\xff\xd8\xff':      return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
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
    session.headers.update({'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
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
            for extra in ['&confirm=t', '']:
                r   = session.get(f'{base_url}{extra}', timeout=timeout,
                                  stream=True, allow_redirects=True)
                raw = _get_bytes(r)
                if detect_file_type(raw) != 'html' and len(raw) > 512:
                    return raw
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
        r   = requests.get(link.strip(), timeout=45, stream=True,
                           headers={'User-Agent': 'Mozilla/5.0'})
        raw = _get_bytes(r)
        if detect_file_type(raw) != 'html' and len(raw) > 512:
            return raw
    except Exception:
        pass
    return None

def infer_extension(content, fallback='pdf'):
    return {'pdf':'pdf','jpg':'jpg','png':'png'}.get(
        detect_file_type(content) if content else 'x', fallback)

def make_safe_filename(nopol, kuantum, idx, ext, total=999, dup_label=''):
    safe = re.sub(r'[\\/:*?"<>|]', '_', str(nopol))
    pad  = len(str(max(total, 1)))
    no   = str(idx + 1).zfill(pad)
    return f'{no}_{safe}_{kuantum}{dup_label}.{ext}'

def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()

def img_bytes_to_pdf(img_bytes):
    tmp_path = None
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image as PILImage
        pil = PILImage.open(io.BytesIO(img_bytes))
        if pil.mode not in ('RGB', 'L'):
            pil = pil.convert('RGB')
        w_px, h_px = pil.size
        a4_w, a4_h = A4
        margin = 20
        scale  = min((a4_w - 2 * margin) / w_px, (a4_h - 2 * margin) / h_px)
        draw_w, draw_h = w_px * scale, h_px * scale
        x = (a4_w - draw_w) / 2
        y = (a4_h - draw_h) / 2
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            pil.save(tmp_path, format='PNG')
        pdf_buf = io.BytesIO()
        c = rl_canvas.Canvas(pdf_buf, pagesize=(a4_w, a4_h))
        c.drawImage(tmp_path, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        c.save()
        pdf_buf.seek(0)
        return pdf_buf.read()
    except Exception:
        return None
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except: pass

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
        ftype    = detect_file_type(ct)
        pdf_data = ct if ftype == 'pdf' else (
            img_bytes_to_pdf(ct) if ftype in ('jpg', 'png') else None)
        if pdf_data:
            try:
                for page in PdfReader(io.BytesIO(pdf_data)).pages:
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
        st.error(f"❌ Kolom **NOPOL** tidak ditemukan. Kolom tersedia: `{'`, `'.join(df.columns)}`")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom **KUANTUM** tidak ditemukan. Kolom tersedia: `{'`, `'.join(df.columns)}`")
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
    if any(str(v).upper().strip() in ['NOPOL','KUANTUM','FOTO SURAT JALAN','SURAT JALAN']
           for v in frow):
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)
    nc = find_col(df, ['nopol','nomor polisi','no pol','no truk','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    lc = find_col(df, ['surat jalan','suratjalan','foto surat','foto','link','url','drive','gdrive'])
    if not nc:
        st.error(f"❌ Kolom **NOPOL** tidak ditemukan di File 2. Kolom tersedia: `{'`, `'.join(df.columns)}`")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom **KUANTUM** tidak ditemukan di File 2.")
        return pd.DataFrame()
    if not lc:
        st.error(f"❌ Kolom **SURAT JALAN** tidak ditemukan di File 2.")
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

def nopol_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_nopol_suggestions(nopol_f1, kuantum, df2, top_n=5, min_similarity=0.5):
    same_kuantum = df2[df2['kuantum'] == kuantum].copy()
    if same_kuantum.empty:
        return []
    results = []
    for _, row in same_kuantum.iterrows():
        sim = nopol_similarity(nopol_f1, row['nopol'])
        if sim >= min_similarity:
            results.append({
                'nopol_f2':    row['nopol'],
                'kuantum':     int(row['kuantum']),
                'surat_jalan': row['surat_jalan'],
                'similarity':  round(sim * 100, 1),
            })
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]

def build_missing_with_suggestions(missing_df, df1, df2):
    rows = []
    for _, row in missing_df.iterrows():
        nopol   = row['nopol']
        kuantum = int(row['kuantum'])
        f2_match = df2[df2['nopol'] == nopol]
        if len(f2_match) > 0:
            ks = sorted(f2_match['kuantum'].dropna().astype(int).unique().tolist())
            d  = ', '.join(map(str, ks[:8])) + (f' (+{len(ks)-8})' if len(ks) > 8 else '')
            rows.append({'nopol': nopol, 'kuantum': kuantum,
                         'kategori': 'kuantum_beda', 'info': d, 'saran': []})
        else:
            saran    = find_nopol_suggestions(nopol, kuantum, df2)
            kategori = 'nopol_mirip' if saran else 'tidak_ada'
            rows.append({'nopol': nopol, 'kuantum': kuantum,
                         'kategori': kategori, 'info': '', 'saran': saran})
    return rows

def detect_duplicates_f1(df1):
    key    = ['nopol', 'kuantum']
    counts = df1.groupby(key).size().reset_index(name='jumlah_duplikat')
    dup_keys = counts[counts['jumlah_duplikat'] > 1][key]
    if dup_keys.empty:
        return pd.DataFrame()
    merged = df1.merge(dup_keys, on=key, how='inner')
    merged = merged.merge(counts, on=key, how='left')
    merged['baris_ke'] = merged.groupby(key).cumcount() + 1
    return merged.reset_index(drop=True)

def match_files(df1, df2):
    df2_valid = df2[df2['surat_jalan'].str.startswith('http', na=False)].copy()
    result_rows = []
    for idx, row1 in df1.iterrows():
        matches = df2_valid[
            (df2_valid['nopol']   == row1['nopol']) &
            (df2_valid['kuantum'] == row1['kuantum'])
        ]
        if len(matches) > 0:
            for link_no, (_, mrow) in enumerate(matches.iterrows(), start=1):
                result_rows.append({
                    'nopol':       row1['nopol'],
                    'kuantum':     row1['kuantum'],
                    'surat_jalan': mrow['surat_jalan'],
                    '_f1_idx':     idx,
                    '_link_no':    link_no,
                })
        else:
            result_rows.append({
                'nopol':       row1['nopol'],
                'kuantum':     row1['kuantum'],
                'surat_jalan': None,
                '_f1_idx':     idx,
                '_link_no':    0,
            })
    return pd.DataFrame(result_rows)

def _worker(task, cache_snapshot):
    link = task['link']
    ct   = cache_snapshot.get(link)
    if ct is None:
        ct = download_file(link)
    return {**task, 'content': ct}

def run_bulk_download(rows, label=''):
    cache_snapshot = dict(st.session_state.dl_cache)
    tasks = [{'idx': r['idx'], 'nopol': r['nopol'], 'kuantum': r['kuantum'],
               'link': r['link'], 'dup_label': r.get('dup_label', '')}
             for r in rows]

    prog_container = st.empty()
    with prog_container.container():
        prog_bar = st.progress(0)
        st.markdown(f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
        padding:12px 18px;font-size:0.85rem;color:#1e40af">
        ⏳ <b>Mengunduh {label}…</b> Harap tunggu, proses ini otomatis.
        </div>""", unsafe_allow_html=True)
        status_txt = st.empty()

    ok_files  = {}
    new_cache = {}
    fail_list = []
    done_n    = 0
    total     = len(tasks)

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_worker, t, cache_snapshot): t for t in tasks}
        for fut in as_completed(futs):
            res = fut.result()
            ct  = res['content']
            if ct:
                new_cache[res['link']] = ct
                ext  = infer_extension(ct)
                fn   = make_safe_filename(res['nopol'], res['kuantum'], res['idx'],
                                          ext, total=total, dup_label=res['dup_label'])
                base, c = fn, 1
                while fn in ok_files:
                    fn = base.rsplit('.', 1)[0] + f'_{c}.' + base.rsplit('.', 1)[-1]
                    c += 1
                ok_files[fn] = ct
            else:
                fail_list.append(f"{res['nopol']} ({res['kuantum']}){res['dup_label']}")
            done_n += 1
            prog_bar.progress(done_n / total)
            pct = int(done_n / total * 100)
            status_txt.markdown(
                f"**{pct}%** — {done_n}/{total} diproses &nbsp;|&nbsp; "
                f"✅ **{len(ok_files)}** berhasil &nbsp;|&nbsp; "
                f"❌ **{len(fail_list)}** gagal")

    prog_container.empty()
    return ok_files, fail_list, new_cache

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for _k in ['result_df','missing_df','nopol_diff_df','nopol_miss_df',
           'active_preview','df2_debug','df1_debug','dl_cache',
           'dup_df','missing_detail','saran_preview','dup_prev_active','processed']:
    if _k not in st.session_state:
        st.session_state[_k] = None
if st.session_state.dl_cache      is None: st.session_state.dl_cache      = {}
if st.session_state.saran_preview  is None: st.session_state.saran_preview  = {}
if st.session_state.dup_prev_active is None: st.session_state.dup_prev_active = {}
if st.session_state.processed      is None: st.session_state.processed      = False

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — PANDUAN & INFO
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px">
      <div style="font-size:2.5rem">🚛</div>
      <div style="font-weight:800;font-size:1.05rem;color:#1e293b">Tantri Imoet</div>
      <div style="font-size:0.72rem;color:#94a3b8;margin-top:4px">Bulk Surat Jalan Downloader</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    with st.expander("📋 Cara Penggunaan", expanded=True):
        st.markdown("""
        **Langkah-langkah:**

        1. **Upload File 1** — Daftar target yang ingin dicocokkan *(NOPOL + Kuantum)*
        2. **Upload File 2** — Database surat jalan dengan link Google Drive
        3. Klik **⚙️ Proses Data**
        4. Di tab **✅ Match**, download ZIP atau Gabung 1 PDF
        """)

    with st.expander("📂 Format File yang Diterima"):
        st.markdown("""
        **File 1 — Target:**
        - Kolom wajib: `NOPOL` dan `KUANTUM`
        - Format: `.xlsx`, `.xls`, `.csv`

        **File 2 — Database:**
        - Kolom wajib: `NOPOL`, `KUANTUM`, `Link/URL Surat Jalan`
        - Link harus berupa Google Drive URL

        **Nama kolom fleksibel:**
        - NOPOL: *nomor polisi, no pol, no truk…*
        - Kuantum: *tonase, qty, jumlah, volume…*
        - Link: *surat jalan, foto, url, drive…*
        """)

    with st.expander("❓ FAQ"):
        st.markdown("""
        **Mengapa beberapa file gagal?**
        File mungkin *private* atau link sudah *expired* di Google Drive.

        **Apa itu Duplikat File 1?**
        Kombinasi NOPOL+Kuantum yang muncul lebih dari sekali. Setiap baris tetap bisa didownload dengan label berbeda.

        **Bagaimana cara kerja Saran NOPOL?**
        Sistem membandingkan kemiripan teks antar NOPOL menggunakan algoritma *fuzzy matching* untuk menemukan kemungkinan salah ketik.

        **Berapa batas file?**
        Tidak ada batas jumlah baris. Download paralel dengan 8 thread secara bersamaan.
        """)

    st.divider()

    if st.session_state.processed and st.session_state.result_df is not None:
        found = st.session_state.result_df
        n_cached = len(st.session_state.dl_cache)
        total_link = len(found)

        st.markdown("**📊 Status Cache**")
        pct_cached = (n_cached / total_link * 100) if total_link > 0 else 0
        st.progress(min(pct_cached / 100, 1.0))
        st.caption(f"{n_cached} / {total_link} file di-cache ({pct_cached:.0f}%)")

        if n_cached > 0:
            total_size = sum(len(v) for v in st.session_state.dl_cache.values())
            st.caption(f"Ukuran cache: {total_size/1024/1024:.1f} MB")

        if st.button("🗑️ Bersihkan Cache", use_container_width=True):
            st.session_state.dl_cache = {}
            st.rerun()

    st.divider()
    st.caption("v2.0 · Made with ❤️ · Streamlit")

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
  <div class="truck-icon">🚛</div>
  <div>
    <h1>Download Surat Jalan in Bulk</h1>
    <p>Cocokkan NOPOL + Kuantum secara otomatis, lalu unduh sebagai ZIP atau PDF gabungan.<br>
       Dilengkapi deteksi duplikat, saran NOPOL mirip, dan preview langsung.</p>
    <span class="header-badge">✅ File dijamin bisa dibuka</span>
    <span class="header-badge" style="margin-left:6px">⚡ 8 Thread Paralel</span>
    <span class="header-badge" style="margin-left:6px">🔍 Fuzzy NOPOL Match</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP INDICATOR
# ══════════════════════════════════════════════════════════════════════════════
def render_step_bar(step):
    steps = [
        {"n": "1", "label": "Upload File", "desc": "File 1 & File 2"},
        {"n": "2", "label": "Proses Data", "desc": "Matching otomatis"},
        {"n": "3", "label": "Download",    "desc": "ZIP atau PDF"},
    ]
    circles, labels = [], []
    for i, s in enumerate(steps):
        idx = i + 1
        if idx < step:
            status = "done"
            icon   = "✓"
        elif idx == step:
            status = "active"
            icon   = s["n"]
        else:
            status = "idle"
            icon   = s["n"]
        circles.append(f'<div class="step-circle {status}">{icon}</div>')
        labels.append(
            f'<div><div class="step-label {status}">{s["label"]}</div>'
            f'<div class="step-desc">{s["desc"]}</div></div>')

    conn_1 = "done" if step > 1 else ""
    conn_2 = "done" if step > 2 else ""

    st.markdown(f"""
    <div class="step-bar">
      <div class="step-item">{circles[0]}{labels[0]}</div>
      <div class="step-connector {conn_1}"></div>
      <div class="step-item">{circles[1]}{labels[1]}</div>
      <div class="step-connector {conn_2}"></div>
      <div class="step-item">{circles[2]}{labels[2]}</div>
    </div>
    """, unsafe_allow_html=True)

current_step = 1
if st.session_state.get('file1_uploaded') or st.session_state.get('file2_uploaded'):
    current_step = 1
if st.session_state.processed:
    current_step = 3
render_step_bar(current_step)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">① Upload File</div>', unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2, gap="large")

with col_f1:
    has_f1_class = "has-file" if st.session_state.get('f1') else ""
    st.markdown(f"""
    <div class="upload-card {has_f1_class}">
      <div class="upload-card-header">
        <div class="upload-card-icon blue">📋</div>
        <div>
          <div class="upload-card-title">File 1 — Daftar Target</div>
          <div class="upload-card-sub">Data yang ingin Anda cocokkan & download</div>
        </div>
      </div>
      <div style="font-size:0.73rem;color:#64748b;margin-bottom:6px">Kolom yang dikenali:</div>
      <div>
        <span class="col-badge required">NOPOL <sup>*</sup></span>
        <span class="col-badge required">KUANTUM <sup>*</sup></span>
        <span class="col-badge">nomor polisi</span>
        <span class="col-badge">tonase</span>
        <span class="col-badge">qty</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    file1 = st.file_uploader(
        "Upload File 1",
        type=['csv', 'xlsx', 'xls'],
        key='f1',
        label_visibility='collapsed',
        help="Format: .xlsx, .xls, atau .csv. Harus punya kolom NOPOL dan KUANTUM."
    )
    if file1:
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
        padding:8px 14px;font-size:0.8rem;color:#16a34a;margin-top:6px">
        ✅ <b>{file1.name}</b> — {file1.size/1024:.1f} KB
        </div>""", unsafe_allow_html=True)

with col_f2:
    has_f2_class = "has-file" if st.session_state.get('f2') else ""
    st.markdown(f"""
    <div class="upload-card {has_f2_class}">
      <div class="upload-card-header">
        <div class="upload-card-icon green">🗄️</div>
        <div>
          <div class="upload-card-title">File 2 — Database Surat Jalan</div>
          <div class="upload-card-sub">Berisi link Google Drive ke setiap surat jalan</div>
        </div>
      </div>
      <div style="font-size:0.73rem;color:#64748b;margin-bottom:6px">Kolom yang dikenali:</div>
      <div>
        <span class="col-badge required">NOPOL <sup>*</sup></span>
        <span class="col-badge required">KUANTUM <sup>*</sup></span>
        <span class="col-badge required">Link/URL <sup>*</sup></span>
        <span class="col-badge">surat jalan</span>
        <span class="col-badge">foto</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    file2 = st.file_uploader(
        "Upload File 2",
        type=['csv', 'xlsx', 'xls'],
        key='f2',
        label_visibility='collapsed',
        help="Format: .xlsx, .xls, atau .csv. Harus punya NOPOL, KUANTUM, dan link Google Drive."
    )
    if file2:
        st.markdown(f"""
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
        padding:8px 14px;font-size:0.8rem;color:#16a34a;margin-top:6px">
        ✅ <b>{file2.name}</b> — {file2.size/1024:.1f} KB
        </div>""", unsafe_allow_html=True)

# ── PROCESS BUTTON ─────────────────────────────────────────────────────────
st.markdown("")
col_btn, col_hint, _ = st.columns([2, 5, 3])
with col_btn:
    both_ready = file1 is not None and file2 is not None
    process = st.button(
        '⚙️ Proses & Cocokkan Data',
        use_container_width=True,
        disabled=not both_ready,
        help="Upload kedua file terlebih dahulu" if not both_ready else "Klik untuk memulai proses matching"
    )
with col_hint:
    if not both_ready:
        missing_files = []
        if not file1: missing_files.append("File 1")
        if not file2: missing_files.append("File 2")
        st.markdown(f"""
        <div style="padding:10px 0;font-size:0.82rem;color:#94a3b8">
        ℹ️ Upload <b>{' dan '.join(missing_files)}</b> untuk melanjutkan
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:10px 0;font-size:0.82rem;color:#16a34a">
        ✅ Kedua file siap — klik tombol untuk memproses
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROSES DATA
# ══════════════════════════════════════════════════════════════════════════════
if process:
    with st.spinner('🔄 Memproses dan mencocokkan data…'):
        df1 = load_file1(read_file(file1))
        df2 = load_file2(read_file(file2))
        if df1.empty or df2.empty:
            st.stop()

        dup_df = detect_duplicates_f1(df1)
        st.session_state.dup_df = dup_df

        result_all = match_files(df1, df2)

        found = result_all[
            result_all['surat_jalan'].notna() &
            result_all['surat_jalan'].str.startswith('http', na=False)
        ].copy().reset_index(drop=True)

        matched_f1_idx = set(found['_f1_idx'].tolist())
        missing_rows   = df1[~df1.index.isin(matched_f1_idx)].copy()
        missing        = missing_rows.drop_duplicates(
            subset=['nopol','kuantum']).reset_index(drop=True)

        missing_detail = build_missing_with_suggestions(missing, df1, df2)
        st.session_state.missing_detail = missing_detail

        diff_rows, miss_rows = [], []
        for item in missing_detail:
            if item['kategori'] == 'kuantum_beda':
                diff_rows.append({
                    'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                    'Kuantum di File 2': item['info'], 'Status': '⚠️ Kuantum tidak cocok'
                })
            else:
                miss_rows.append({
                    'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                    'Status': '❌ NOPOL tidak ada di File 2',
                    'Saran NOPOL (Kuantum Cocok)': (
                        ', '.join([f"{s['nopol_f2']} ({s['similarity']}%)"
                                   for s in item['saran']]) if item['saran'] else '-')
                })

        st.session_state.result_df      = found
        st.session_state.missing_df     = missing
        st.session_state.nopol_diff_df  = pd.DataFrame(diff_rows)
        st.session_state.nopol_miss_df  = pd.DataFrame(miss_rows)
        st.session_state.df2_debug      = df2
        st.session_state.df1_debug      = df1
        st.session_state.active_preview  = None
        st.session_state.dl_cache        = {}
        st.session_state.saran_preview   = {}
        st.session_state.dup_prev_active = {}
        st.session_state.processed       = True

    n_dup_groups = (len(dup_df[['nopol','kuantum']].drop_duplicates())
                    if not dup_df.empty else 0)
    n_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')

    st.balloons()

    msg_parts = [f"✅ **{len(found)} link surat jalan** ditemukan dari **{len(df1)} data** File 1"]
    if len(missing) > 0:
        msg_parts.append(f"⚠️ **{len(missing)} data** tidak match")
    if n_dup_groups > 0:
        msg_parts.append(f"🔁 **{n_dup_groups} kombinasi duplikat** terdeteksi")
    if n_mirip > 0:
        msg_parts.append(f"🔍 **{n_mirip} saran NOPOL mirip** tersedia")

    st.success("  ·  ".join(msg_parts))
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS SECTION
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.result_df is not None:
    found          = st.session_state.result_df
    missing        = st.session_state.missing_df
    nopol_diff     = st.session_state.nopol_diff_df
    nopol_miss     = st.session_state.nopol_miss_df
    df2_all        = st.session_state.df2_debug
    df1_all        = st.session_state.df1_debug
    dup_df         = st.session_state.dup_df if st.session_state.dup_df is not None else pd.DataFrame()
    missing_detail = st.session_state.missing_detail or []

    n_match      = len(found)
    n_diff_k     = len(nopol_diff) if nopol_diff is not None else 0
    n_miss_nopol = len(nopol_miss) if nopol_miss is not None else 0
    n_all_miss   = len(missing)
    n_dup_groups = (len(dup_df[['nopol','kuantum']].drop_duplicates())
                    if not dup_df.empty else 0)
    n_dup_rows   = len(dup_df) if not dup_df.empty else 0
    n_nopol_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')
    match_rate   = int(n_match / max(len(df1_all), 1) * 100) if df1_all is not None else 0

    # ── SUMMARY STATS ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">② Ringkasan Hasil</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card green">
        <div class="stat-card-icon">✅</div>
        <div class="stat-num c-green">{n_match}</div>
        <div class="stat-lbl">Link Ditemukan</div>
        <div style="font-size:0.68rem;color:#22c55e;margin-top:4px;font-weight:600">
          {match_rate}% match rate
        </div>
      </div>
      <div class="stat-card purple">
        <div class="stat-card-icon">🔁</div>
        <div class="stat-num c-purple">{n_dup_groups}</div>
        <div class="stat-lbl">Duplikat File 1</div>
        <div style="font-size:0.68rem;color:#a855f7;margin-top:4px;font-weight:600">
          {n_dup_rows} baris total
        </div>
      </div>
      <div class="stat-card yellow">
        <div class="stat-card-icon">⚠️</div>
        <div class="stat-num c-yellow">{n_diff_k}</div>
        <div class="stat-lbl">Kuantum Beda</div>
        <div style="font-size:0.68rem;color:#f59e0b;margin-top:4px;font-weight:600">
          NOPOL ada, qty ≠
        </div>
      </div>
      <div class="stat-card red">
        <div class="stat-card-icon">❌</div>
        <div class="stat-num c-red">{n_miss_nopol}</div>
        <div class="stat-lbl">NOPOL Tidak Ada</div>
        <div style="font-size:0.68rem;color:#ef4444;margin-top:4px;font-weight:600">
          {n_nopol_mirip} ada saran mirip
        </div>
      </div>
      <div class="stat-card orange">
        <div class="stat-card-icon">🔴</div>
        <div class="stat-num c-orange">{n_all_miss}</div>
        <div class="stat-lbl">Total Tidak Match</div>
        <div style="font-size:0.68rem;color:#f97316;margin-top:4px;font-weight:600">
          dari {len(df1_all)} data File 1
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SMART ALERTS ────────────────────────────────────────────────────────
    if n_dup_groups > 0:
        st.markdown(f"""
        <div class="alert purple">
          <span class="alert-icon">🔁</span>
          <div><b>{n_dup_groups} kombinasi NOPOL+Kuantum duplikat</b> ({n_dup_rows} baris total) di File 1.
          Setiap baris <b>tetap bisa didownload</b> dengan label <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.
          Cocok untuk data NOPOL+Kuantum sama dengan <b>tanggal berbeda</b>. Lihat tab 🔁 Duplikat.</div>
        </div>
        """, unsafe_allow_html=True)

    if n_nopol_mirip > 0:
        st.markdown(f"""
        <div class="alert sky">
          <span class="alert-icon">🔍</span>
          <div><b>{n_nopol_mirip} data</b> punya saran NOPOL mirip dengan kuantum cocok di File 2.
          Kemungkinan ada <b>salah ketik 1–2 karakter</b>. Cek tab ❌ Tidak Match NOPOL.</div>
        </div>
        """, unsafe_allow_html=True)

    if n_match == 0:
        st.markdown("""
        <div class="alert error">
          <span class="alert-icon">⚠️</span>
          <div><b>Tidak ada data yang match.</b> Pastikan format NOPOL dan KUANTUM di kedua file konsisten.
          Sistem akan melakukan normalisasi spasi dan huruf kapital secara otomatis.</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-label">③ Detail & Download</div>', unsafe_allow_html=True)

    tab1, tab_dup, tab2, tab3, tab4 = st.tabs([
        f"✅ Match ({n_match})",
        f"🔁 Duplikat ({n_dup_groups} grup · {n_dup_rows} baris)",
        f"⚠️ Kuantum Beda ({n_diff_k})",
        f"❌ NOPOL Tidak Ada ({n_miss_nopol})",
        f"🔴 Semua Tidak Match ({n_all_miss})",
    ])

    # ────────────────────────────────────────────────────────────────────────
    # TAB 1 — MATCH SEMUA
    # ────────────────────────────────────────────────────────────────────────
    with tab1:
        if len(found) == 0:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🔍</div>
              <h3>Tidak Ada Data yang Match</h3>
              <p>Tidak ada kombinasi NOPOL + Kuantum yang cocok antara File 1 dan File 2.
                 Periksa format data Anda.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # ── SEARCH & FILTER ──────────────────────────────────────────────
            sc1, sc2 = st.columns([3, 7])
            with sc1:
                search = st.text_input(
                    'Filter NOPOL',
                    placeholder='🔍  Ketik NOPOL untuk filter…',
                    label_visibility='collapsed',
                    key='search_found'
                )
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(
                    re.escape(norm_nopol(search.strip())), na=False, case=False)
                ].reset_index(drop=True)

            with sc2:
                if search.strip():
                    st.markdown(f"""
                    <div style="padding:10px 4px;font-size:0.82rem;color:#64748b">
                    Menampilkan <b>{len(disp)}</b> dari <b>{len(found)}</b> link surat jalan
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="padding:10px 4px;font-size:0.82rem;color:#64748b">
                    Total <b>{len(found)}</b> link surat jalan siap didownload
                    </div>""", unsafe_allow_html=True)

            # ── ACTION BAR ──────────────────────────────────────────────────
            st.markdown("""
            <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
            letter-spacing:1px;color:#94a3b8;margin:16px 0 8px">
            Aksi Bulk Download
            </div>""", unsafe_allow_html=True)

            ac1, ac2, ac3, ac4 = st.columns([2.2, 2.2, 2.2, 3.4])
            with ac1:
                do_zip = st.button(
                    '📦 Download ZIP',
                    use_container_width=True,
                    key='btn_zip',
                    help=f"Download {len(disp)} surat jalan sebagai file ZIP terpisah"
                )
            with ac2:
                do_merge = st.button(
                    '📄 Gabung 1 PDF',
                    use_container_width=True,
                    key='btn_merge',
                    help=f"Gabungkan {len(disp)} surat jalan menjadi 1 file PDF"
                )
            with ac3:
                do_preload = st.button(
                    '⚡ Pre-load Cache',
                    use_container_width=True,
                    key='btn_preload',
                    help="Download semua file ke cache agar download individual lebih cepat"
                )
            with ac4:
                n_cached_tab = sum(1 for _, r in disp.iterrows()
                                   if r['surat_jalan'] in st.session_state.dl_cache)
                pct_cached_tab = int(n_cached_tab / max(len(disp), 1) * 100)
                cache_color = "#22c55e" if pct_cached_tab == 100 else ("#f59e0b" if pct_cached_tab > 0 else "#94a3b8")
                st.markdown(f"""
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                padding:8px 14px;font-size:0.8rem;color:#475569;line-height:1.5">
                🗃️ Cache: <b style="color:{cache_color}">{n_cached_tab}/{len(disp)}</b>
                file ({pct_cached_tab}%) · {'Semua siap ✅' if pct_cached_tab == 100 else 'Gunakan ⚡ Pre-load'}
                </div>""", unsafe_allow_html=True)

            # ── PRE-LOAD ─────────────────────────────────────────────────────
            if do_preload and len(disp) > 0:
                links_needed = [row['surat_jalan'] for _, row in disp.iterrows()
                                if row['surat_jalan'] not in st.session_state.dl_cache]
                if not links_needed:
                    st.success('✅ Semua file sudah ada di cache!')
                else:
                    cache_snap = dict(st.session_state.dl_cache)
                    tasks_pre  = [{'idx': i, 'nopol': row['nopol'],
                                   'kuantum': int(row['kuantum']),
                                   'link': row['surat_jalan'], 'dup_label': ''}
                                  for i, row in disp.iterrows()
                                  if row['surat_jalan'] not in cache_snap]
                    prog = st.progress(0)
                    stxt = st.empty()
                    ok_n = fail_n = done_n = 0
                    new_cache = {}
                    with ThreadPoolExecutor(max_workers=8) as ex:
                        futs = {ex.submit(_worker, t, cache_snap): t for t in tasks_pre}
                        for fut in as_completed(futs):
                            res = fut.result()
                            if res['content']:
                                new_cache[res['link']] = res['content']; ok_n += 1
                            else:
                                fail_n += 1
                            done_n += 1
                            prog.progress(done_n / len(tasks_pre))
                            stxt.markdown(
                                f"Pre-load **{done_n}/{len(tasks_pre)}** — "
                                f"✅ {ok_n} berhasil &nbsp;|&nbsp; ❌ {fail_n} gagal")
                    st.session_state.dl_cache.update(new_cache)
                    stxt.success(f'✅ Pre-load selesai: {ok_n} berhasil, {fail_n} gagal')

            # ── ZIP DOWNLOAD ─────────────────────────────────────────────────
            if do_zip and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_list, new_cache = run_bulk_download(rows_dl, 'ZIP')
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    zip_data = make_zip(ok_files)
                    st.markdown(f"""
                    <div class="alert success">
                      <span class="alert-icon">📦</span>
                      <div><b>{len(ok_files)} file berhasil diunduh</b> · ZIP siap · 
                      Ukuran: {len(zip_data)/1024:.0f} KB</div>
                    </div>""", unsafe_allow_html=True)
                    st.download_button(
                        f'💾 Simpan ZIP ({len(ok_files)} file · {len(zip_data)/1024:.0f} KB)',
                        zip_data, 'surat_jalan_semua.zip', 'application/zip', key='dl_zip_result')
                if fail_list:
                    with st.expander(f'⚠️ {len(fail_list)} file gagal diunduh — klik untuk detail'):
                        for f in fail_list:
                            st.markdown(f'• `{f}`')

            # ── MERGE PDF ──────────────────────────────────────────────────
            if do_merge and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_dl, new_cache = run_bulk_download(rows_dl, 'PDF')
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    with st.spinner('📄 Menggabungkan semua file menjadi 1 PDF…'):
                        ordered = [new_cache.get(row['surat_jalan']) or
                                   st.session_state.dl_cache.get(row['surat_jalan'])
                                   for _, row in disp.iterrows()]
                        ordered = [x for x in ordered if x]
                        merged  = merge_pdfs(ordered)
                    if merged:
                        st.markdown(f"""
                        <div class="alert success">
                          <span class="alert-icon">📄</span>
                          <div><b>{len(ordered)} file berhasil digabung</b> · 
                          Ukuran PDF: {len(merged)/1024:.0f} KB</div>
                        </div>""", unsafe_allow_html=True)
                        st.download_button(
                            f'💾 Simpan PDF Gabungan ({len(ordered)} halaman · {len(merged)/1024:.0f} KB)',
                            merged, 'surat_jalan_gabungan.pdf', 'application/pdf', key='dl_merged_pdf')
                        if fail_dl:
                            with st.expander(f'⚠️ {len(fail_dl)} file tidak ikut digabung'):
                                for f in fail_dl: st.markdown(f'• `{f}`')
                    else:
                        st.error('❌ Gagal membuat PDF gabungan. Pastikan `pypdf`, `reportlab`, `Pillow` terinstall.')
                elif fail_dl:
                    st.error(f'❌ Semua {len(fail_dl)} file gagal diunduh.')

            # ── TABEL DETAIL ──────────────────────────────────────────────
            st.markdown('<div class="section-label">Detail per Surat Jalan</div>',
                        unsafe_allow_html=True)

            # Header baris
            h0, h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2.5, 1.2, 0.8, 1.8, 0.8, 1.8])
            for col, lbl in zip([h0,h1,h2,h3,h4,h5,h6],
                                 ['No.','NOPOL','Kuantum','Link #','Google Drive','Preview','Download']):
                col.markdown(f'<span style="font-size:0.72rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.8px">{lbl}</span>', unsafe_allow_html=True)

            st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

            for i, row in disp.iterrows():
                nopol   = row['nopol']
                kuantum = int(row['kuantum'])
                link    = row['surat_jalan']
                link_no = int(row.get('_link_no', 1))
                fid     = extract_fid(link)
                is_dup  = not dup_df.empty and (
                    ((dup_df['nopol'] == nopol) & (dup_df['kuantum'] == kuantum)).any())

                cols = st.columns([0.5, 2.5, 1.2, 0.8, 1.8, 0.8, 1.8])
                cols[0].markdown(f'<span style="font-size:0.8rem;color:#94a3b8">#{i+1}</span>', unsafe_allow_html=True)

                dup_badge = '<span style="background:#ede9fe;color:#7c3aed;font-size:0.65rem;padding:1px 5px;border-radius:4px;margin-left:4px">DUP</span>' if is_dup else ''
                cols[1].markdown(f'<span class="nopol-pill {"dup" if is_dup else ""}">{nopol}</span>{dup_badge}', unsafe_allow_html=True)
                cols[2].markdown(f'<b>{kuantum:,}</b>')
                cols[3].markdown(f'<span style="font-size:0.78rem;color:#94a3b8">#{link_no}</span>', unsafe_allow_html=True)

                if fid:
                    cols[4].markdown(f'[🔗 Buka Drive](https://drive.google.com/file/d/{fid}/view)')
                else:
                    cols[4].markdown(f'[🔗 Buka]({link})')

                with cols[5]:
                    btn_lbl = '👁️ ✕' if st.session_state.active_preview == i else '👁️'
                    if st.button(btn_lbl, key=f'v_{i}', help="Toggle preview"):
                        st.session_state.active_preview = (
                            None if st.session_state.active_preview == i else i)
                        st.rerun()

                with cols[6]:
                    dup_label = f'_DUPLIKAT{link_no}' if link_no > 1 else ''
                    cached = st.session_state.dl_cache.get(link)
                    if cached:
                        ext   = infer_extension(cached)
                        fname = make_safe_filename(nopol, kuantum, i, ext,
                                                   total=len(disp), dup_label=dup_label)
                        mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                        st.download_button(f'⬇️ .{ext.upper()}', cached, fname, mime, key=f'd_{i}')
                    else:
                        if st.button('⬇️ Unduh', key=f'db_{i}', help=f"Download surat jalan {nopol}"):
                            with st.spinner(f'Mengunduh {nopol}…'):
                                ct = download_file(link)
                            if ct:
                                st.session_state.dl_cache[link] = ct
                                ext   = infer_extension(ct)
                                fname = make_safe_filename(nopol, kuantum, i, ext,
                                                           total=len(disp), dup_label=dup_label)
                                mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                st.download_button(f'💾 Simpan .{ext.upper()}', ct,
                                                   fname, mime, key=f'ds_{i}')
                            else:
                                st.error('❌ Gagal. File private/expired.')

                if st.session_state.active_preview == i:
                    purl = to_preview(link)
                    if purl:
                        import streamlit.components.v1 as components
                        st.markdown(f"""
                        <div class="alert sky" style="margin-top:8px">
                          <span class="alert-icon">👁️</span>
                          <div>Preview — <b>{nopol}</b> · Kuantum: <b>{kuantum:,}</b>
                          <a href="{purl}" target="_blank" style="margin-left:8px;font-size:0.78rem">
                          ↗ Buka di tab baru</a></div>
                        </div>""", unsafe_allow_html=True)
                        components.html(
                            f'<iframe src="{purl}" width="100%" height="680" '
                            f'style="border:1px solid #bfdbfe;border-radius:12px;background:#fff" '
                            f'allow="autoplay"></iframe>', height=700)
                    else:
                        st.error('Link preview tidak valid.')

                if i < len(disp) - 1:
                    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB DUPLIKAT
    # ────────────────────────────────────────────────────────────────────────
    with tab_dup:
        if dup_df.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Tidak Ada Duplikat!</h3>
              <p>Semua kombinasi NOPOL + Kuantum di File 1 adalah unik.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert purple">
              <span class="alert-icon">🔁</span>
              <div><b>{n_dup_groups} kombinasi NOPOL+Kuantum muncul lebih dari sekali</b> 
              di File 1 ({n_dup_rows} baris total). Setiap baris <b>tetap bisa didownload</b> secara 
              individual — nama file dibedakan dengan label <code>_DUPLIKAT1</code>, 
              <code>_DUPLIKAT2</code>, dst.</div>
            </div>
            """, unsafe_allow_html=True)

            sd_dup = st.text_input(
                '', placeholder='🔍  Filter NOPOL duplikat…',
                label_visibility='collapsed', key='sd_dup')

            dza, dzb, _ = st.columns([2.5, 2.5, 5])
            with dza:
                do_zip_dup = st.button('📦 ZIP Semua Duplikat', use_container_width=True, key='btn_zip_dup')
            with dzb:
                do_merge_dup = st.button('📄 Gabung PDF Duplikat', use_container_width=True, key='btn_merge_dup')

            # Build list
            all_dup_rows = []
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)
                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    baris_ke  = int(drow['baris_ke'])
                    dup_label = f'_DUPLIKAT{baris_ke}'
                    if n_links == 0:
                        link = None
                    elif i_row <= n_links:
                        link = links_found[i_row - 1]
                    else:
                        link = links_found[0]
                    all_dup_rows.append({
                        'nopol': nopol, 'kuantum': int(kuantum),
                        'baris_ke': baris_ke, 'dup_label': dup_label, 'link': link,
                    })

            if do_zip_dup:
                valid_rows = [r for r in all_dup_rows if r['link']]
                if not valid_rows:
                    st.warning('⚠️ Tidak ada link tersedia.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']}
                                for i, r in enumerate(valid_rows)]
                    ok_files, fail_list, new_cache = run_bulk_download(rows_dl, 'Duplikat ZIP')
                    st.session_state.dl_cache.update(new_cache)
                    if ok_files:
                        st.download_button(f'💾 Simpan ZIP Duplikat ({len(ok_files)} file)',
                                           make_zip(ok_files), 'duplikat_semua.zip',
                                           'application/zip', key='dl_zip_dup_result')
                    if fail_list:
                        with st.expander(f'❌ {len(fail_list)} gagal'):
                            for f in fail_list: st.markdown(f'• `{f}`')

            if do_merge_dup:
                valid_rows = [r for r in all_dup_rows if r['link']]
                if not valid_rows:
                    st.warning('⚠️ Tidak ada link tersedia.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']}
                                for i, r in enumerate(valid_rows)]
                    ok_files, fail_dl, new_cache = run_bulk_download(rows_dl, 'Duplikat PDF')
                    st.session_state.dl_cache.update(new_cache)
                    if ok_files:
                        with st.spinner('Menggabungkan PDF duplikat…'):
                            ordered = [new_cache.get(r['link']) or
                                       st.session_state.dl_cache.get(r['link'])
                                       for r in valid_rows]
                            ordered = [x for x in ordered if x]
                            merged  = merge_pdfs(ordered)
                        if merged:
                            st.success(f'✅ {len(ordered)} file digabung · {len(merged)//1024:,} KB')
                            st.download_button('💾 Simpan PDF Duplikat', merged,
                                               'duplikat_gabungan.pdf', 'application/pdf',
                                               key='dl_merge_dup_result')
                        else:
                            st.error('❌ Gagal membuat PDF.')
                    if fail_dl:
                        with st.expander(f'⚠️ {len(fail_dl)} file gagal'):
                            for f in fail_dl: st.markdown(f'• `{f}`')

            # ── Tabel duplikat ──────────────────────────────────────────────
            st.markdown('<div class="section-label">Detail Setiap Baris Duplikat</div>',
                        unsafe_allow_html=True)

            row_counter = 0
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                if sd_dup.strip() and norm_nopol(sd_dup.strip()) not in nopol:
                    continue

                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)

                st.markdown(f"""
                <div class="dup-group-banner">
                  <span style="font-size:1.2rem">🚛</span>
                  <span class="nopol-pill dup">{nopol}</span>
                  <span style="color:#64748b;font-size:0.82rem">Kuantum: <b>{int(kuantum):,}</b></span>
                  <span style="background:#fee2e2;color:#991b1b;border-radius:6px;
                  padding:2px 10px;font-size:0.75rem;font-weight:700">
                  Muncul {len(grp)}× di File 1</span>
                  <span style="background:#e0f2fe;color:#0369a1;border-radius:6px;
                  padding:2px 10px;font-size:0.75rem;font-weight:700">
                  {n_links} link di File 2</span>
                </div>
                """, unsafe_allow_html=True)

                dh0,dh1,dh2,dh3,dh4,dh5 = st.columns([0.6, 1.8, 2, 1.8, 0.8, 1.8])
                for col, lbl in zip([dh0,dh1,dh2,dh3,dh4,dh5],
                                     ['Baris','NOPOL','Label File','Link GDrive','👁','⬇']):
                    col.markdown(f'<span style="font-size:0.7rem;color:#94a3b8;font-weight:700">{lbl}</span>',
                                 unsafe_allow_html=True)

                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    baris_ke  = int(drow['baris_ke'])
                    dup_label = f'_DUPLIKAT{baris_ke}'
                    if n_links == 0:
                        link = None
                    elif i_row <= n_links:
                        link = links_found[i_row - 1]
                    else:
                        link = links_found[0]
                    fid = extract_fid(link) if link else None
                    uid = f'dup_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}_{baris_ke}'

                    cols = st.columns([0.6, 1.8, 2, 1.8, 0.8, 1.8])
                    cols[0].markdown(f'<b>ke-{baris_ke}</b>')
                    cols[1].markdown(f'<span class="nopol-pill dup">{nopol}</span>', unsafe_allow_html=True)
                    cols[2].markdown(
                        f'<code style="background:#ede9fe;color:#7c3aed;padding:3px 10px;'
                        f'border-radius:6px;font-size:0.8rem">{dup_label}</code>',
                        unsafe_allow_html=True)

                    if link and fid:
                        cols[3].markdown(f'[🔗 Buka Drive](https://drive.google.com/file/d/{fid}/view)')
                    elif link:
                        cols[3].markdown(f'[🔗 Buka]({link})')
                    else:
                        cols[3].markdown('<span style="color:#94a3b8">— Tidak ada link</span>', unsafe_allow_html=True)

                    with cols[4]:
                        if link:
                            prev_grp_key = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                            is_active    = (st.session_state.dup_prev_active.get(prev_grp_key) == baris_ke)
                            if st.button('👁️ ✕' if is_active else '👁️', key=f'dprev_{uid}'):
                                st.session_state.dup_prev_active[prev_grp_key] = (
                                    None if is_active else baris_ke)
                                st.rerun()

                    with cols[5]:
                        if link:
                            cached = st.session_state.dl_cache.get(link)
                            if cached:
                                ext   = infer_extension(cached)
                                fname = make_safe_filename(nopol, kuantum, row_counter, ext,
                                                           total=n_dup_rows, dup_label=dup_label)
                                mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                st.download_button(f'⬇️ .{ext.upper()}', cached, fname, mime, key=f'ddl_{uid}')
                            else:
                                if st.button('⬇️ Unduh', key=f'ddlb_{uid}'):
                                    with st.spinner(f'Mengunduh {nopol}{dup_label}…'):
                                        ct = download_file(link)
                                    if ct:
                                        st.session_state.dl_cache[link] = ct
                                        ext   = infer_extension(ct)
                                        fname = make_safe_filename(nopol, kuantum, row_counter, ext,
                                                                   total=n_dup_rows, dup_label=dup_label)
                                        mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                        st.download_button(f'💾 Simpan .{ext.upper()}', ct,
                                                           fname, mime, key=f'ddls_{uid}')
                                    else:
                                        st.error('❌ Gagal mengunduh.')
                        else:
                            st.markdown('`—`')

                    prev_grp_key = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                    if link and st.session_state.dup_prev_active.get(prev_grp_key) == baris_ke:
                        purl = to_preview(link)
                        if purl:
                            import streamlit.components.v1 as components
                            st.markdown(f"""
                            <div class="alert sky" style="margin-top:8px">
                              <span class="alert-icon">👁️</span>
                              <div>Preview — <b>{nopol}</b> ·
                              <code style="color:#7c3aed">{dup_label}</code> ·
                              <a href="{purl}" target="_blank" style="font-size:0.78rem">↗ Buka di tab baru</a>
                              </div>
                            </div>""", unsafe_allow_html=True)
                            components.html(
                                f'<iframe src="{purl}" width="100%" height="680" '
                                f'style="border:1px solid #d8b4fe;border-radius:12px;background:#fff" '
                                f'allow="autoplay"></iframe>', height=700)
                        else:
                            st.error('Link preview tidak valid.')

                    row_counter += 1

                st.markdown("")

            # Export
            st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
            export_dup = dup_df[['nopol','kuantum','baris_ke','jumlah_duplikat']].copy()
            export_dup.columns = ['NOPOL','Kuantum','Baris ke-','Total Duplikat']
            export_dup['Label File'] = export_dup['Baris ke-'].apply(lambda x: f'_DUPLIKAT{int(x)}')
            _de, _ = st.columns([2, 8])
            with _de:
                st.download_button('📥 Export CSV Duplikat',
                                   export_dup.to_csv(index=False).encode('utf-8'),
                                   'duplikat_file1.csv', 'text/csv', key='dl_dup')
            st.dataframe(export_dup, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 2 — TIDAK MATCH KUANTUM
    # ────────────────────────────────────────────────────────────────────────
    with tab2:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Semua Kuantum Cocok!</h3>
              <p>Tidak ada data dengan NOPOL yang sama tapi kuantum berbeda.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert warn">
              <span class="alert-icon">⚠️</span>
              <div><b>{len(nopol_diff)} data</b> — NOPOL ditemukan di File 2 namun nilai 
              kuantumnya tidak cocok. Kemungkinan ada perbedaan satuan atau input data.</div>
            </div>
            """, unsafe_allow_html=True)

            sd2c, sd2_ = st.columns([3, 7])
            with sd2c:
                sd = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sd')
            dd = nopol_diff.copy()
            if sd.strip():
                dd = dd[dd['NOPOL'].str.contains(
                    re.escape(norm_nopol(sd)), na=False, case=False)].reset_index(drop=True)

            st.dataframe(dd, use_container_width=True, hide_index=True,
                         column_config={
                             "Status": st.column_config.TextColumn(width="medium"),
                             "Kuantum di File 2": st.column_config.TextColumn(width="large"),
                         })
            _ca, _ = st.columns([2, 8])
            with _ca:
                st.download_button('📥 Export CSV', dd.to_csv(index=False).encode('utf-8'),
                                   'tidak_match_kuantum.csv', 'text/csv', key='dl_a')

    # ────────────────────────────────────────────────────────────────────────
    # TAB 3 — TIDAK MATCH NOPOL + SARAN FUZZY
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        miss_items = [x for x in missing_detail
                      if x['kategori'] in ('nopol_mirip', 'tidak_ada')]
        if not miss_items:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Semua NOPOL Ditemukan!</h3>
              <p>Tidak ada NOPOL dari File 1 yang tidak ada di File 2.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            n_mirip   = sum(1 for x in miss_items if x['kategori'] == 'nopol_mirip')
            n_tdk_ada = sum(1 for x in miss_items if x['kategori'] == 'tidak_ada')

            st.markdown(f"""
            <div class="alert error">
              <span class="alert-icon">❌</span>
              <div><b>{len(miss_items)} NOPOL tidak ada di File 2.</b><br>
              🔍 <b>{n_mirip} data</b> punya saran NOPOL mirip (kemungkinan salah ketik) &nbsp;·&nbsp;
              🚫 <b>{n_tdk_ada} data</b> tanpa saran sama sekali</div>
            </div>
            """, unsafe_allow_html=True)

            fc1, fc2 = st.columns([3, 4])
            with fc1:
                sm = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sm')
            with fc2:
                min_sim = st.slider('🎚️ Threshold Kemiripan (%)',
                                    min_value=30, max_value=90, value=50, step=5,
                                    key='sim_slider',
                                    help="Semakin tinggi = saran lebih ketat/akurat")

            for item_idx, item in enumerate(miss_items):
                nopol   = item['nopol']
                kuantum = item['kuantum']
                if sm.strip() and norm_nopol(sm.strip()) not in nopol:
                    continue

                saran_filtered = [s for s in item['saran'] if s['similarity'] >= min_sim]
                has_saran      = bool(saran_filtered)

                st.markdown(f"""
                <div style="background:#fff;border:1px solid {'#bfdbfe' if has_saran else '#fca5a5'};
                border-left: 4px solid {'#3b82f6' if has_saran else '#ef4444'};
                border-radius:10px;padding:14px 18px;margin:12px 0">
                  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
                    <span class="nopol-pill">{nopol}</span>
                    <span style="color:#64748b;font-size:0.82rem">Kuantum: <b>{kuantum:,}</b></span>
                    <span style="background:{'#dbeafe' if has_saran else '#fee2e2'};
                    color:{'#1d4ed8' if has_saran else '#991b1b'};border-radius:6px;
                    padding:2px 10px;font-size:0.75rem;font-weight:700">
                    {'🔍 ' + str(len(saran_filtered)) + ' saran ditemukan' if has_saran else '🚫 Tidak ada saran'}
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                if saran_filtered:
                    sh0,sh1,sh2,sh3,sh4 = st.columns([0.4, 2.5, 1.5, 1.3, 2.2])
                    for col, lbl in zip([sh0,sh1,sh2,sh3,sh4],
                                         ['#','NOPOL File 2','Kemiripan','Kuantum','Aksi']):
                        col.markdown(f'<span style="font-size:0.7rem;color:#94a3b8;font-weight:700">{lbl}</span>',
                                     unsafe_allow_html=True)

                    for s_idx, saran in enumerate(saran_filtered):
                        saran_key = f'saran_{item_idx}_{s_idx}'
                        sc0,sc1,sc2,sc3,sc4 = st.columns([0.4, 2.5, 1.5, 1.3, 2.2])

                        sim       = saran['similarity']
                        sim_class = 'sim-high' if sim >= 80 else ('sim-medium' if sim >= 65 else 'sim-low')

                        sc0.markdown(f'`{s_idx+1}`')
                        sc1.markdown(f'<span class="nopol-pill">{saran["nopol_f2"]}</span>', unsafe_allow_html=True)
                        sc2.markdown(f'<span class="sim-badge {sim_class}">{sim}%</span>', unsafe_allow_html=True)
                        sc3.markdown(f'{saran["kuantum"]:,}')

                        with sc4:
                            col_p, col_d = st.columns(2)
                            with col_p:
                                prev_active = st.session_state.saran_preview.get(f'item_{item_idx}')
                                is_ap       = (prev_active == s_idx)
                                if st.button('👁️ ✕' if is_ap else '👁️ Preview',
                                             key=f'sprev_{saran_key}', use_container_width=True):
                                    st.session_state.saran_preview[f'item_{item_idx}'] = (
                                        None if is_ap else s_idx)
                                    st.rerun()
                            with col_d:
                                link_saran = saran['surat_jalan']
                                cached_s   = st.session_state.dl_cache.get(link_saran)
                                if cached_s:
                                    ext_s   = infer_extension(cached_s)
                                    fname_s = make_safe_filename(
                                        saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                    mime_s  = 'application/pdf' if ext_s == 'pdf' else f'image/{ext_s}'
                                    st.download_button(f'⬇️ .{ext_s.upper()}', cached_s,
                                                       fname_s, mime_s,
                                                       key=f'sdl_cached_{saran_key}',
                                                       use_container_width=True)
                                else:
                                    if st.button('⬇️ Unduh', key=f'sdl_{saran_key}',
                                                 use_container_width=True):
                                        with st.spinner(f'Mengunduh…'):
                                            ct_s = download_file(link_saran)
                                        if ct_s:
                                            st.session_state.dl_cache[link_saran] = ct_s
                                            ext_s   = infer_extension(ct_s)
                                            fname_s = make_safe_filename(
                                                saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                            mime_s  = 'application/pdf' if ext_s == 'pdf' else f'image/{ext_s}'
                                            st.download_button(f'💾 Simpan .{ext_s.upper()}', ct_s,
                                                               fname_s, mime_s,
                                                               key=f'sdl_save_{saran_key}',
                                                               use_container_width=True)
                                        else:
                                            st.error('❌ Gagal.')

                        # Preview inline
                        if st.session_state.saran_preview.get(f'item_{item_idx}') == s_idx:
                            purl_s = to_preview(saran['surat_jalan'])
                            if purl_s:
                                import streamlit.components.v1 as components
                                sim_class_c = '#16a34a' if sim >= 80 else ('#b45309' if sim >= 65 else '#dc2626')
                                st.markdown(f"""
                                <div class="alert sky" style="margin:8px 0">
                                  <span class="alert-icon">👁️</span>
                                  <div>Preview — NOPOL: <b>{saran['nopol_f2']}</b> · 
                                  Kemiripan: <b style="color:{sim_class_c}">{sim}%</b> ·
                                  <a href="{purl_s}" target="_blank" style="font-size:0.78rem">↗ Buka di tab baru</a>
                                  </div>
                                </div>""", unsafe_allow_html=True)
                                components.html(
                                    f'<iframe src="{purl_s}" width="100%" height="680" '
                                    f'style="border:1px solid #7dd3fc;border-radius:12px;background:#fff" '
                                    f'allow="autoplay"></iframe>', height=700)
                            else:
                                st.error('Link preview tidak valid.')
                else:
                    msg = ('🚫 Tidak ada NOPOL di File 2 dengan kuantum sama dan kemiripan cukup.'
                           if item['kategori'] == 'tidak_ada'
                           else f'🔽 Kurangi threshold (saat ini {min_sim}%) untuk lebih banyak saran.')
                    st.caption(f'  {msg}')

            # Export
            st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
            if nopol_miss is not None and not nopol_miss.empty:
                _cb, _ = st.columns([2, 8])
                with _cb:
                    st.download_button('📥 Export CSV NOPOL Tidak Ada',
                                       nopol_miss.to_csv(index=False).encode('utf-8'),
                                       'tidak_match_nopol.csv', 'text/csv', key='dl_b')
                st.dataframe(nopol_miss, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 4 — SEMUA TIDAK MATCH
    # ────────────────────────────────────────────────────────────────────────
    with tab4:
        if missing.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🏆</div>
              <h3>Sempurna! Semua Data Match!</h3>
              <p>Setiap baris di File 1 berhasil dicocokkan dengan data di File 2.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert error">
              <span class="alert-icon">🔴</span>
              <div><b>{n_all_miss} total kombinasi tidak match</b> 
              (NOPOL tidak ada + kuantum beda).</div>
            </div>
            """, unsafe_allow_html=True)

            # Mini stat summary
            t4c1, t4c2, t4c3, t4c4 = st.columns(4)
            t4c1.metric("Total Tidak Match", n_all_miss)
            t4c2.metric("⚠️ Kuantum Beda",   n_diff_k)
            t4c3.metric("❌ NOPOL Tidak Ada", n_miss_nopol)
            t4c4.metric("🔍 Ada Saran Mirip", n_nopol_mirip)

            all_m = missing.rename(
                columns={'nopol':'NOPOL','kuantum':'Kuantum File 1'}).copy()
            all_m['Kuantum File 1'] = all_m['Kuantum File 1'].astype(int)

            def get_keterangan(row):
                nopol = row['NOPOL']
                f2m   = df2_all[df2_all['nopol'] == nopol]
                if len(f2m) > 0:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique().tolist())
                    d  = ', '.join(map(str, ks[:5])) + (f' (+{len(ks)-5} lagi)' if len(ks) > 5 else '')
                    return f'⚠️ Kuantum beda (di File 2: {d})'
                saran = find_nopol_suggestions(nopol, int(row['Kuantum File 1']), df2_all, top_n=3)
                if saran:
                    top = saran[0]
                    return f'🔍 Saran: {top["nopol_f2"]} ({top["similarity"]}%)'
                return '❌ NOPOL tidak ada di File 2'

            with st.spinner('Menganalisis penyebab ketidakcocokan…'):
                all_m['Keterangan'] = all_m.apply(get_keterangan, axis=1)

            sa4c, _ = st.columns([3, 7])
            with sa4c:
                sa = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sa')
            if sa.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(
                    re.escape(norm_nopol(sa)), na=False, case=False)].reset_index(drop=True)

            st.dataframe(all_m, use_container_width=True, hide_index=True,
                         column_config={
                             "Keterangan": st.column_config.TextColumn(width="large"),
                         })

            _cde, _ = st.columns([2, 8])
            with _cde:
                st.download_button('📥 Export CSV Semua Tidak Match',
                                   all_m.to_csv(index=False).encode('utf-8'),
                                   'semua_tidak_match.csv', 'text/csv', key='dl_c')

# ══════════════════════════════════════════════════════════════════════════════
# EMPTY STATE — Belum upload
# ══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.processed:
    st.markdown("""
    <div style="text-align:center;padding:48px 24px;margin-top:16px">
      <div style="font-size:3.5rem;margin-bottom:16px">📂</div>
      <h3 style="color:#374151;font-size:1.2rem;font-weight:700;margin-bottom:8px">
        Upload File untuk Memulai
      </h3>
      <p style="color:#94a3b8;font-size:0.875rem;line-height:1.7;max-width:420px;margin:0 auto">
        Upload <b>File 1</b> (daftar target) dan <b>File 2</b> (database surat jalan) di atas,
        lalu klik <b>⚙️ Proses & Cocokkan Data</b> untuk memulai.
        <br><br>
        Butuh bantuan? Lihat panduan di sidebar kiri.
      </p>
    </div>
    """, unsafe_allow_html=True)
