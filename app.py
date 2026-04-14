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

# ══════════════════════════════════════════════════════════════════════════════
# THEME INIT
# ══════════════════════════════════════════════════════════════════════════════
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

# ── THEME VARIABLES ───────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    THEME = {
        'bg':       '#0f1117',
        'surface':  '#1a1d27',
        'surface2': '#222535',
        'border':   '#2d3048',
        'accent':   '#6366f1',
        'accent2':  '#818cf8',
        'green':    '#22c55e',
        'yellow':   '#f59e0b',
        'red':      '#ef4444',
        'text':     '#e2e8f0',
        'muted':    '#64748b',
        'toggle_bg':'#222535',
        'toggle_border':'#2d3048',
        'toggle_icon':'☀️',
        'toggle_label':'Light Mode',
    }
else:
    THEME = {
        'bg':       '#f1f5f9',
        'surface':  '#ffffff',
        'surface2': '#f8fafc',
        'border':   '#e2e8f0',
        'accent':   '#4f46e5',
        'accent2':  '#6366f1',
        'green':    '#16a34a',
        'yellow':   '#d97706',
        'red':      '#dc2626',
        'text':     '#1e293b',
        'muted':    '#64748b',
        'toggle_bg':'#f8fafc',
        'toggle_border':'#e2e8f0',
        'toggle_icon':'🌙',
        'toggle_label':'Dark Mode',
    }

T = THEME

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root {{
  --bg:       {T['bg']};
  --surface:  {T['surface']};
  --surface2: {T['surface2']};
  --border:   {T['border']};
  --accent:   {T['accent']};
  --accent2:  {T['accent2']};
  --green:    {T['green']};
  --yellow:   {T['yellow']};
  --red:      {T['red']};
  --text:     {T['text']};
  --muted:    {T['muted']};
  --radius:   12px;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [class*="css"] {{
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
}}

.stApp {{ background: var(--bg); }}
.main .block-container {{ padding: 1.5rem 2rem; max-width: 1300px; }}

/* ── HEADER ── */
.app-header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 32px;
  background: {'linear-gradient(135deg, #1a1d27 0%, #222535 100%)' if T['bg'] == '#0f1117' else 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)'};
  border: 1px solid var(--border);
  border-radius: 16px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}}
.app-header::before {{
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 0% 50%, rgba(99,102,241,.12) 0%, transparent 60%);
  pointer-events: none;
}}
.app-header-left {{ display: flex; align-items: center; gap: 20px; position: relative; }}
.app-header-icon {{ font-size: 3rem; flex-shrink: 0; }}
.app-header-text h1 {{ font-size: 1.6rem; font-weight: 800; color: {'#fff' if T['bg'] == '#0f1117' else '#1e293b'}; }}
.app-header-text p  {{ font-size: 0.82rem; color: var(--muted); margin-top: 4px; }}

/* ── THEME TOGGLE ── */
.theme-toggle-wrap {{ position: relative; z-index: 1; }}
.theme-toggle-btn {{
  display: flex; align-items: center; gap: 8px;
  background: {T['toggle_bg']};
  border: 1.5px solid {T['toggle_border']};
  border-radius: 50px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  transition: all .2s;
  font-family: 'Plus Jakarta Sans', sans-serif;
}}
.theme-toggle-btn:hover {{
  border-color: var(--accent);
  background: rgba(99,102,241,.1);
  color: var(--accent2);
}}

/* ── UPLOAD ZONE ── */
.upload-zone {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 8px;
}}
.upload-zone-title {{
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: var(--accent2); margin-bottom: 6px;
}}
.upload-zone-desc {{ font-size: 0.78rem; color: var(--muted); }}

div[data-testid="stFileUploader"] {{
  background: var(--surface2) !important;
  border: 1.5px dashed var(--border) !important;
  border-radius: 10px !important;
  transition: border-color .2s;
}}
div[data-testid="stFileUploader"]:hover {{
  border-color: var(--accent) !important;
}}

/* ── STAT CARDS ── */
.stats-row {{
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 14px; margin: 24px 0;
}}
.stat-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 18px;
  text-align: center;
  position: relative; overflow: hidden;
}}
.stat-card::after {{
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  border-radius: 12px 12px 0 0;
}}
.stat-card.blue::after  {{ background: var(--accent); }}
.stat-card.green::after {{ background: var(--green); }}
.stat-card.red::after   {{ background: var(--red); }}
.stat-card.yellow::after{{ background: var(--yellow); }}

.stat-num {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 2.4rem; font-weight: 700; line-height: 1;
}}
.stat-num.blue   {{ color: var(--accent2); }}
.stat-num.green  {{ color: var(--green); }}
.stat-num.red    {{ color: var(--red); }}
.stat-num.yellow {{ color: var(--yellow); }}
.stat-label {{
  font-size: 0.68rem; color: var(--muted); margin-top: 8px;
  text-transform: uppercase; letter-spacing: .8px; font-weight: 600;
}}

/* ── ALERTS ── */
.alert {{
  border-radius: var(--radius); padding: 14px 18px;
  margin: 12px 0; font-size: 0.83rem; line-height: 1.6;
  display: flex; align-items: flex-start; gap: 10px;
}}
.alert-icon {{ flex-shrink: 0; font-size: 1rem; margin-top: 1px; }}
.alert.info    {{ background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.3); color: {'#a5b4fc' if T['bg'] == '#0f1117' else '#4338ca'}; }}
.alert.success {{ background: rgba(34,197,94,.1);  border: 1px solid rgba(34,197,94,.3);  color: {'#86efac' if T['bg'] == '#0f1117' else '#15803d'}; }}
.alert.warn    {{ background: rgba(245,158,11,.1); border: 1px solid rgba(245,158,11,.3); color: {'#fcd34d' if T['bg'] == '#0f1117' else '#b45309'}; }}
.alert.error   {{ background: rgba(239,68,68,.1);  border: 1px solid rgba(239,68,68,.3);  color: {'#fca5a5' if T['bg'] == '#0f1117' else '#b91c1c'}; }}

/* ── SECTION DIVIDER ── */
.section-label {{
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; color: var(--muted);
  display: flex; align-items: center; gap: 12px;
  margin: 28px 0 16px;
}}
.section-label::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}

/* ── BUTTONS ── */
.stButton > button {{
  background: var(--surface2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-size: 0.82rem !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
  transition: all .15s !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stButton > button:hover {{
  background: rgba(99,102,241,.15) !important;
  border-color: var(--accent) !important;
  color: var(--accent2) !important;
}}

/* ── TABLE CARD ── */
.table-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin: 12px 0;
}}
.table-card.warn  {{ border-color: rgba(245,158,11,.4); }}
.table-card.error {{ border-color: rgba(239,68,68,.4); }}
.table-card-title {{ font-size: 0.9rem; font-weight: 700; margin-bottom: 14px; }}
.table-card-title.warn  {{ color: var(--yellow); }}
.table-card-title.error {{ color: var(--red); }}

/* ── TABS ── */
div[data-testid="stTabs"] button {{
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
}}
div[data-testid="stTabs"] button[aria-selected="true"] {{
  color: var(--accent2) !important;
  border-bottom-color: var(--accent) !important;
}}

/* ── PROGRESS ── */
.stProgress > div > div {{ background: var(--accent) !important; border-radius: 4px !important; }}

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}
div[data-testid="stDataFrame"] * {{ color: var(--text) !important; background: var(--surface2) !important; }}

/* ── INPUTS ── */
.stTextInput > div > div > input {{
  background: var(--surface2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stTextInput > div > div > input:focus {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(99,102,241,.2) !important;
}}

/* ── EXPANDER ── */
details {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}}

/* ── DOWNLOAD BTN ── */
.stDownloadButton > button {{
  background: linear-gradient(135deg, var(--accent), #4f46e5) !important;
  color: white !important;
  border: none !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
  transition: opacity .15s !important;
}}
.stDownloadButton > button:hover {{ opacity: 0.88 !important; }}

/* ── GENERAL TEXT COLOR FIX FOR LIGHT ── */
p, span, label, div {{ color: var(--text); }}
code {{ background: var(--surface2); color: var(--accent2); border-radius: 4px; padding: 2px 5px; }}
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
            r1  = session.get(base, timeout=timeout, stream=True, allow_redirects=True)
            raw = _read_chunks(r1)
            if detect_filetype(raw) != 'html' and len(raw) > 512:
                return raw
            html = raw.decode('utf-8', errors='ignore')
            m = re.search(r'name="confirm"\s+value="([^"]+)"', html)
            if m:
                result = try_url(f'{base}&confirm={m.group(1)}')
                if result: return result
            result = try_url(f'{base}&confirm=t')
            if result: return result
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
# HEADER + THEME TOGGLE
# ══════════════════════════════════════════════════════════════════════════════
header_left, header_right = st.columns([8, 2])

with header_left:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:20px;padding:20px 0 10px">
      <div style="font-size:3rem">📦</div>
      <div>
        <div style="font-size:1.6rem;font-weight:800">Surat Jalan Bulk Downloader</div>
        <div style="font-size:0.82rem;color:var(--muted);margin-top:4px">
          Match NOPOL + KUANTUM → Download ZIP terpisah atau gabung 1 PDF sekaligus
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with header_right:
    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
    toggle_label = f"{T['toggle_icon']}  {T['toggle_label']}"
    if st.button(toggle_label, key='theme_toggle', use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

st.markdown('<hr style="border-color:var(--border);margin:0 0 24px">', unsafe_allow_html=True)

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
    # TABS — MATCHED  |  UNMATCHED A  |  UNMATCHED B  |  SEMUA TIDAK MATCH
    # ══════════════════════════════════════════════════════════════════════════
    n_diff = len(nopol_diff) if nopol_diff is not None else 0
    n_miss = len(nopol_miss) if nopol_miss is not None else 0
    n_all  = len(missing)

    tab_matched, tab_a, tab_b, tab_all = st.tabs([
        f"✅ Berhasil Match  ({len(found)})",
        f"⚠️ Kuantum Beda  ({n_diff})",
        f"❌ NOPOL Tidak Ada  ({n_miss})",
        f"📋 Semua Tidak Match  ({n_all})",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — MATCHED DATA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_matched:
        if found.empty:
            st.markdown('<div class="alert warn"><span class="alert-icon">⚠️</span>'
                        '0 surat jalan ditemukan. Lihat tab lain untuk detail penyebabnya.</div>',
                        unsafe_allow_html=True)
        else:
            search = st.text_input('', placeholder='🔍  Filter NOPOL...',
                                   label_visibility='collapsed', key='search_found')
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(
                    re.escape(norm_nopol(search.strip())), na=False, case=False)
                ].reset_index(drop=True)

            st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

            # ── BULK ACTION BUTTONS ────────────────────────────────────────────
            b1, b2, b3, _ = st.columns([2, 2, 2, 4])
            with b1:
                do_zip    = st.button('📦  Download ZIP',    use_container_width=True)
            with b2:
                do_merge  = st.button('📄  Gabung 1 PDF',    use_container_width=True)
            with b3:
                do_cache  = st.button('⚡  Pre-load Semua',  use_container_width=True,
                                      help='Download semua ke memori agar per-baris instan')

            if do_cache and not disp.empty:
                need = [r['surat_jalan'] for _, r in disp.iterrows()
                        if r['surat_jalan'] not in st.session_state.dl_cache]
                if not need:
                    st.markdown('<div class="alert success"><span class="alert-icon">✅</span>'
                                'Semua file sudah ada di cache!</div>', unsafe_allow_html=True)
                else:
                    _, _, new_cache = run_downloads(
                        disp[disp['surat_jalan'].isin(need)].reset_index(drop=True),
                        label='Pre-load'
                    )
                    st.session_state.dl_cache.update(new_cache)

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

            # ── PER-ROW TABLE ──────────────────────────────────────────────────
            st.markdown('<div class="section-label">Detail Surat Jalan</div>',
                        unsafe_allow_html=True)

            h = st.columns([0.5, 2.5, 1.5, 2.5, 1, 1.8])
            for col, lbl in zip(h, ['#', 'NOPOL', 'KUANTUM', 'Link', '👁', '⬇']):
                col.markdown(f'<span style="font-size:.7rem;font-weight:700;text-transform:uppercase;'
                             f'letter-spacing:1px;color:#64748b">{lbl}</span>',
                             unsafe_allow_html=True)
            st.markdown('<hr style="border-color:var(--border);margin:6px 0 10px">', unsafe_allow_html=True)

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
                cols[2].markdown(f'<b style="color:var(--text)">{kuantum:,}</b>', unsafe_allow_html=True)
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
                            f'style="border:1px solid var(--border);border-radius:10px" '
                            f'allow="autoplay"></iframe>',
                            height=700
                        )
                        st.caption(f'Preview kosong? → [buka di tab baru]({purl})')
                    else:
                        st.markdown('<div class="alert error"><span class="alert-icon">❌</span>'
                                    'Link preview tidak valid.</div>', unsafe_allow_html=True)

                st.markdown('<hr style="border-color:var(--border);margin:4px 0">', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — NOPOL ADA, KUANTUM BEDA
    # ══════════════════════════════════════════════════════════════════════════
    with tab_a:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown('<div class="alert success"><span class="alert-icon">🎉</span>'
                        'Tidak ada perbedaan kuantum — semua kuantum cocok!</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="alert warn"><span class="alert-icon">⚠️</span>'
                f'<b>{len(nopol_diff)}</b> NOPOL ditemukan di File 2 namun kuantumnya tidak cocok dengan File 1. '
                f'Cek kemungkinan salah input kuantum.</div>',
                unsafe_allow_html=True
            )
            sa = st.text_input('', placeholder='🔍 Filter NOPOL...', key='sa',
                                label_visibility='collapsed')
            da = nopol_diff.copy()
            if sa.strip():
                da = da[da['NOPOL'].str.contains(re.escape(norm_nopol(sa)), na=False, case=False)]
            st.dataframe(da, use_container_width=True, hide_index=True)
            c1, _ = st.columns([2, 8])
            with c1:
                st.download_button('📥 Export CSV', da.to_csv(index=False).encode(),
                                   'tabel_a_kuantum_beda.csv', 'text/csv', key='dla')

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — NOPOL TIDAK ADA DI FILE 2
    # ══════════════════════════════════════════════════════════════════════════
    with tab_b:
        if nopol_miss is None or nopol_miss.empty:
            st.markdown('<div class="alert success"><span class="alert-icon">🎉</span>'
                        'Semua NOPOL ditemukan di File 2!</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="alert error"><span class="alert-icon">❌</span>'
                f'<b>{len(nopol_miss)}</b> NOPOL dari File 1 tidak ada sama sekali di File 2. '
                f'Kemungkinan data belum diinput atau NOPOL salah tulis.</div>',
                unsafe_allow_html=True
            )
            sb = st.text_input('', placeholder='🔍 Filter NOPOL...', key='sb',
                                label_visibility='collapsed')
            db = nopol_miss.copy()
            if sb.strip():
                db = db[db['NOPOL'].str.contains(re.escape(norm_nopol(sb)), na=False, case=False)]
            st.dataframe(db, use_container_width=True, hide_index=True)
            c2, _ = st.columns([2, 8])
            with c2:
                st.download_button('📥 Export CSV', db.to_csv(index=False).encode(),
                                   'tabel_b_nopol_tidak_ada.csv', 'text/csv', key='dlb')

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — SEMUA TIDAK MATCH (GABUNGAN)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_all:
        if missing.empty:
            st.markdown('<div class="alert success"><span class="alert-icon">🎉</span>'
                        '<b>Semua data berhasil dicocokkan!</b> Tidak ada yang tidak match.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="alert error"><span class="alert-icon">❌</span>'
                f'<b>{len(missing)}</b> kombinasi NOPOL + KUANTUM dari File 1 tidak berhasil dicocokkan.</div>',
                unsafe_allow_html=True
            )
            all_m = missing.rename(columns={'nopol': 'NOPOL',
                                            'kuantum': 'Kuantum (File 1)'}).copy()
            all_m['Kuantum (File 1)'] = all_m['Kuantum (File 1)'].astype(int)
            sc = st.text_input('', placeholder='🔍 Filter NOPOL...', key='sc',
                                label_visibility='collapsed')
            if sc.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(
                    re.escape(norm_nopol(sc)), na=False, case=False)]
            st.dataframe(all_m, use_container_width=True, hide_index=True)
            c3, _ = st.columns([2, 8])
            with c3:
                st.download_button('📥 Export CSV', all_m.to_csv(index=False).encode(),
                                   'tabel_c_semua_tidak_match.csv', 'text/csv', key='dlc')
