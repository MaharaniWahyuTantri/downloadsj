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
.stat-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 12px; margin: 16px 0; }
.stat-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 18px 20px; text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.stat-num { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; line-height: 1; }
.stat-lbl { font-size: 0.7rem; color: #94a3b8; margin-top: 6px; text-transform: uppercase;
    letter-spacing: .6px; font-weight: 500; }
.c-blue{color:#3b82f6;} .c-green{color:#22c55e;} .c-red{color:#ef4444;}
.c-yellow{color:#f59e0b;} .c-orange{color:#f97316;} .c-purple{color:#a855f7;}
.warn-box    { background:#fffbeb; border:1px solid #fcd34d; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#92400e; line-height:1.6; }
.info-box    { background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#1e40af; line-height:1.6; }
.success-box { background:#f0fdf4; border:1px solid #86efac; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#14532d; line-height:1.6; }
.error-box   { background:#fef2f2; border:1px solid #fca5a5; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#7f1d1d; line-height:1.6; }
.dup-box     { background:#fdf4ff; border:1px solid #e9d5ff; border-radius:10px;
    padding:14px 18px; margin:12px 0; font-size:0.85rem; color:#581c87; line-height:1.6; }
.suggestion-box { background:#f0f9ff; border:1px solid #7dd3fc; border-radius:10px;
    padding:14px 18px; margin:8px 0; font-size:0.85rem; color:#0c4a6e; line-height:1.6; }
.section-label { font-size:0.7rem; font-weight:700; text-transform:uppercase;
    letter-spacing:1.5px; color:#94a3b8; margin:24px 0 12px;
    display:flex; align-items:center; gap:10px; }
.section-label::after { content:''; flex:1; height:1px; background:#e2e8f0; }
.stButton > button { background:#fff !important; color:#374151 !important;
    border:1px solid #d1d5db !important; border-radius:8px !important;
    font-size:0.82rem !important; font-weight:500 !important; padding:6px 14px !important;
    transition:all .15s !important; box-shadow:0 1px 3px rgba(0,0,0,0.06) !important; }
.stButton > button:hover { background:#eff6ff !important; border-color:#3b82f6 !important;
    color:#1d4ed8 !important; }
div[data-testid="stFileUploader"] { background:#fff; border:2px dashed #cbd5e1; border-radius:10px; }
.stProgress > div > div { background:#3b82f6 !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 6px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; font-size: 0.82rem !important;
    font-weight: 500 !important; padding: 8px 16px !important;
    color: #64748b !important; border: none !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #eff6ff !important; color: #1d4ed8 !important; font-weight: 600 !important;
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
    if sig[:4] == b'%PDF':            return 'pdf'
    if sig[:3] == b'\xff\xd8\xff':    return 'jpg'
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

# ── PDF: img → pdf (pakai temp file agar reportlab tidak error BytesIO) ───────

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

# ══════════════════════════════════════════════════════════════════════════════
# FILE LOADING
# ══════════════════════════════════════════════════════════════════════════════

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
    if any(str(v).upper().strip() in ['NOPOL','KUANTUM','FOTO SURAT JALAN','SURAT JALAN']
           for v in frow):
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
# FUZZY NOPOL SUGGESTION
# ══════════════════════════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════════════════════════
# DETEKSI DUPLIKAT FILE 1
# ══════════════════════════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════════════════════════
# MATCHING — satu baris f1 bisa dapat banyak link dari f2
# ══════════════════════════════════════════════════════════════════════════════

def match_files(df1, df2):
    """
    Setiap baris df1 di-match ke SEMUA link di df2 yang NOPOL+KUANTUM sama.
    Kolom hasil: nopol, kuantum, surat_jalan, _f1_idx, _link_no
    """
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

# ══════════════════════════════════════════════════════════════════════════════
# THREAD-SAFE DOWNLOAD WORKER
# ══════════════════════════════════════════════════════════════════════════════

def _worker(task, cache_snapshot):
    link = task['link']
    ct   = cache_snapshot.get(link)
    if ct is None:
        ct = download_file(link)
    return {**task, 'content': ct}

def run_bulk_download(rows, label=''):
    """
    rows: list of dict {idx, nopol, kuantum, link, dup_label}
    """
    cache_snapshot = dict(st.session_state.dl_cache)
    tasks = [{'idx': r['idx'], 'nopol': r['nopol'], 'kuantum': r['kuantum'],
               'link': r['link'], 'dup_label': r.get('dup_label', '')}
             for r in rows]

    prog      = st.progress(0)
    stxt      = st.empty()
    ok_files  = {}
    new_cache = {}
    fail_list = []
    done_n    = 0
    total     = len(tasks)
    stxt.text(f'Mengunduh {label} 0 / {total} file...')

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
            prog.progress(done_n / total)
            stxt.text(f'Mengunduh {done_n}/{total} — ✅ {len(ok_files)} | ❌ {len(fail_list)}')

    stxt.text(f'Selesai — ✅ {len(ok_files)} berhasil | ❌ {len(fail_list)} gagal')
    return ok_files, fail_list, new_cache

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
for _k in ['result_df','missing_df','nopol_diff_df','nopol_miss_df',
           'active_preview','df2_debug','df1_debug','dl_cache',
           'dup_df','missing_detail','saran_preview','dup_prev_active']:
    if _k not in st.session_state:
        st.session_state[_k] = None
if st.session_state.dl_cache      is None: st.session_state.dl_cache      = {}
if st.session_state.saran_preview  is None: st.session_state.saran_preview  = {}
if st.session_state.dup_prev_active is None: st.session_state.dup_prev_active = {}

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

        n_dup_groups = (len(dup_df[['nopol','kuantum']].drop_duplicates())
                        if not dup_df.empty else 0)
        msg = f'✅ Selesai! {len(found)} link surat jalan ditemukan dari {len(df1)} data File 1.'
        if n_dup_groups > 0:
            msg += (f'  ⚠️ **{n_dup_groups} kombinasi duplikat** terdeteksi di File 1 — '
                    f'cek tab Duplikat!')
        st.success(msg)

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
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

    n_match       = len(found)
    n_diff_k      = len(nopol_diff) if nopol_diff is not None else 0
    n_miss_nopol  = len(nopol_miss) if nopol_miss is not None else 0
    n_all_miss    = len(missing)
    n_dup_groups  = (len(dup_df[['nopol','kuantum']].drop_duplicates())
                     if not dup_df.empty else 0)
    n_dup_rows    = len(dup_df) if not dup_df.empty else 0
    n_nopol_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Ringkasan Hasil</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num c-green">{n_match}</div>
        <div class="stat-lbl">✅ Link Ditemukan</div></div>
      <div class="stat-card"><div class="stat-num c-purple">{n_dup_groups}</div>
        <div class="stat-lbl">🔁 Kombinasi Duplikat File 1</div></div>
      <div class="stat-card"><div class="stat-num c-yellow">{n_diff_k}</div>
        <div class="stat-lbl">⚠️ NOPOL Ada, Kuantum Beda</div></div>
      <div class="stat-card"><div class="stat-num c-red">{n_miss_nopol}</div>
        <div class="stat-lbl">❌ NOPOL Tidak Ada</div></div>
      <div class="stat-card"><div class="stat-num c-orange">{n_all_miss}</div>
        <div class="stat-lbl">🔴 Total Tidak Match</div></div>
    </div>
    """, unsafe_allow_html=True)

    if n_dup_groups > 0:
        st.markdown(
            f'<div class="dup-box">🔁 <b>{n_dup_groups} kombinasi NOPOL+Kuantum duplikat '
            f'({n_dup_rows} baris total) ditemukan di File 1.</b> '
            f'Setiap baris duplikat <b>tetap bisa didownload secara individual</b> di tab '
            f'<b>🔁 Duplikat</b> dengan nama file dibedakan: '
            f'<code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst. '
            f'Berguna jika data yang sama muncul untuk tanggal yang berbeda.</div>',
            unsafe_allow_html=True
        )
    if n_nopol_mirip > 0:
        st.markdown(
            f'<div class="suggestion-box">🔍 <b>{n_nopol_mirip} data memiliki saran NOPOL mirip</b> '
            f'dengan kuantum yang cocok di File 2. '
            f'Cek tab <b>❌ Tidak Match NOPOL</b> untuk melihat saran dan preview.</div>',
            unsafe_allow_html=True
        )

    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Match ketat:</b> NOPOL <em>dan</em> KUANTUM harus sama persis. Normalisasi otomatis spasi
    &amp; huruf kapital.<br>
    🔁 <b>Duplikat File 1:</b> Setiap baris duplikat tetap bisa didownload sendiri-sendiri dengan
    label <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.<br>
    🔧 <b>Multi-link di File 2:</b> Jika satu NOPOL+Kuantum punya beberapa link, semua link
    ditampilkan dan bisa didownload.<br>
    🔍 <b>Saran NOPOL:</b> Jika NOPOL tidak ada namun KUANTUM cocok, sistem mencari NOPOL mirip
    (kemungkinan salah ketik 1–2 huruf).<br>
    📦 Tersedia <b>ZIP</b> (file terpisah) dan <b>Gabung 1 PDF</b>.
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab1, tab_dup, tab2, tab3, tab4 = st.tabs([
        f"✅ Match Semua ({n_match})",
        f"🔁 Duplikat File 1 ({n_dup_groups} kombinasi / {n_dup_rows} baris)",
        f"⚠️ Tidak Match Kuantum ({n_diff_k})",
        f"❌ Tidak Match NOPOL ({n_miss_nopol})",
        f"🔴 Semua Tidak Match ({n_all_miss})",
    ])

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 1 — MATCH SEMUA
    # ──────────────────────────────────────────────────────────────────────────
    with tab1:
        if len(found) == 0:
            st.markdown('<div class="warn-box">⚠️ <b>0 surat jalan ditemukan.</b> '
                        'Lihat tab lain untuk detail.</div>', unsafe_allow_html=True)
        else:
            search = st.text_input('cari', placeholder='🔍  Ketik NOPOL untuk filter...',
                                   label_visibility='collapsed', key='search_found')
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(
                    re.escape(norm_nopol(search.strip())), na=False, case=False)
                ].reset_index(drop=True)

            st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** link surat jalan.')

            bc1, bc2, bc3, _ = st.columns([2, 2, 2, 4])
            with bc1:
                do_zip    = st.button('📦 Download ZIP', use_container_width=True, key='btn_zip')
            with bc2:
                do_merge  = st.button('📄 Gabung 1 PDF', use_container_width=True, key='btn_merge')
            with bc3:
                do_preload = st.button('⚡ Pre-load Cache', use_container_width=True, key='btn_preload')

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
                    prog = st.progress(0); stxt = st.empty()
                    ok_n = fail_n = done_n = 0; new_cache = {}
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
                            stxt.text(f'Pre-load {done_n}/{len(tasks_pre)} — ✅ {ok_n} | ❌ {fail_n}')
                    st.session_state.dl_cache.update(new_cache)
                    stxt.text(f'Pre-load selesai: ✅ {ok_n} | ❌ {fail_n}')

            if do_zip and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_list, new_cache = run_bulk_download(rows_dl, 'ZIP')
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    st.download_button(f'💾 Simpan ZIP ({len(ok_files)} file)',
                                       make_zip(ok_files), 'surat_jalan_semua.zip',
                                       'application/zip', key='dl_zip_result')
                if fail_list:
                    with st.expander(f'❌ {len(fail_list)} file gagal'):
                        for f in fail_list: st.write(f'• {f}')

            if do_merge and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_dl, new_cache = run_bulk_download(rows_dl, 'PDF')
                st.session_state.dl_cache.update(new_cache)
                if ok_files:
                    with st.spinner('Menggabungkan semua file menjadi 1 PDF...'):
                        ordered = [new_cache.get(row['surat_jalan']) or
                                   st.session_state.dl_cache.get(row['surat_jalan'])
                                   for _, row in disp.iterrows()]
                        ordered = [x for x in ordered if x]
                        merged  = merge_pdfs(ordered)
                    if merged:
                        st.success(f'✅ **{len(ordered)} file berhasil digabung** · '
                                   f'Ukuran: **{len(merged)//1024:,} KB**')
                        st.download_button(f'💾 Simpan PDF Gabungan ({len(ordered)} surat jalan)',
                                           merged, 'surat_jalan_gabungan.pdf',
                                           'application/pdf', key='dl_merged_pdf')
                        if fail_dl:
                            with st.expander(f'⚠️ {len(fail_dl)} file tidak ikut digabung'):
                                for f in fail_dl: st.write(f'• {f}')
                    else:
                        st.error('❌ Gagal membuat PDF gabungan. '
                                 'Pastikan `pypdf`, `reportlab`, `Pillow` terinstall.')
                elif fail_dl:
                    st.error(f'❌ Semua {len(fail_dl)} file gagal diunduh.')

            # ── Tabel detail ──────────────────────────────────────────────────
            st.markdown('<div class="section-label">Detail per Surat Jalan</div>',
                        unsafe_allow_html=True)
            hcols = st.columns([0.4, 2.2, 1.3, 1.0, 1.8, 1.0, 1.8])
            for col, lbl in zip(hcols,
                    ['No.','NOPOL','KUANTUM','Link ke-','Link GDrive','👁','⬇ Download']):
                col.markdown(f'**{lbl}**')
            st.divider()

            for i, row in disp.iterrows():
                nopol   = row['nopol']
                kuantum = int(row['kuantum'])
                link    = row['surat_jalan']
                link_no = int(row.get('_link_no', 1))
                fid     = extract_fid(link)
                is_dup  = not dup_df.empty and (
                    ((dup_df['nopol'] == nopol) & (dup_df['kuantum'] == kuantum)).any())
                dup_badge = ' 🔁' if is_dup else ''
                cols = st.columns([0.4, 2.2, 1.3, 1.0, 1.8, 1.0, 1.8])
                cols[0].markdown(f'`#{i+1}`')
                cols[1].markdown(f'`{nopol}`{dup_badge}')
                cols[2].markdown(f'**{kuantum:,}**')
                cols[3].markdown(f'#{link_no}')
                if fid:
                    cols[4].markdown(f'[🔗 Buka](https://drive.google.com/file/d/{fid}/view)')
                else:
                    cols[4].markdown(f'[🔗 Buka]({link})')
                with cols[5]:
                    if st.button('👁️', key=f'v_{i}'):
                        st.session_state.active_preview = (
                            None if st.session_state.active_preview == i else i)
                with cols[6]:
                    dup_label = f'_DUPLIKAT{link_no}' if link_no > 1 else ''
                    cached = st.session_state.dl_cache.get(link)
                    if cached:
                        ext   = infer_extension(cached)
                        fname = make_safe_filename(nopol, kuantum, i, ext,
                                                   total=len(disp), dup_label=dup_label)
                        mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                        st.download_button(f'⬇️ .{ext.upper()}', cached,
                                           fname, mime, key=f'd_{i}')
                    else:
                        if st.button('⬇️ Download', key=f'db_{i}'):
                            with st.spinner(f'Mengunduh {nopol}...'):
                                ct = download_file(link)
                            if ct:
                                st.session_state.dl_cache[link] = ct
                                ext   = infer_extension(ct)
                                fname = make_safe_filename(nopol, kuantum, i, ext,
                                                           total=len(disp), dup_label=dup_label)
                                mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                st.download_button(f'💾 Simpan .{ext.upper()}', ct,
                                                   fname, mime, key=f'ds_{i}')
                                st.success(f'✅ {fname} siap disimpan!')
                            else:
                                st.error('❌ Gagal. File mungkin private/expired.')

                if st.session_state.active_preview == i:
                    purl = to_preview(link)
                    if purl:
                        import streamlit.components.v1 as components
                        components.html(
                            f'<iframe src="{purl}" width="100%" height="680" '
                            f'style="border:1px solid #e2e8f0;border-radius:10px;background:#fff" '
                            f'allow="autoplay"></iframe>', height=700)
                        st.caption(f'Preview kosong? → [buka di tab baru]({purl})')
                    else:
                        st.error('Link preview tidak valid.')

    # ──────────────────────────────────────────────────────────────────────────
    # TAB DUPLIKAT — Download per baris dengan label _DUPLIKAT1/_DUPLIKAT2
    # ──────────────────────────────────────────────────────────────────────────
    with tab_dup:
        if dup_df.empty:
            st.markdown('<div class="success-box">🎉 <b>Tidak ada duplikat di File 1!</b> '
                        'Semua kombinasi NOPOL + Kuantum unik.</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="dup-box">🔁 <b>{n_dup_groups} kombinasi NOPOL+Kuantum muncul '
                f'lebih dari sekali</b> di File 1 ({n_dup_rows} baris total).<br>'
                f'Setiap baris <b>tetap bisa didownload</b> secara individual — nama file '
                f'dibedakan dengan label <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.<br>'
                f'Cocok untuk kasus data NOPOL+Kuantum sama tapi <b>tanggal berbeda</b>.</div>',
                unsafe_allow_html=True
            )

            # Filter pencarian
            sd_dup = st.text_input('', placeholder='🔍 Filter NOPOL duplikat...',
                                   label_visibility='collapsed', key='sd_dup')

            # Tombol bulk duplikat
            _dza, _dzb, _ = st.columns([2.5, 2.5, 5])
            with _dza:
                do_zip_dup = st.button('📦 Download ZIP Semua Duplikat',
                                       use_container_width=True, key='btn_zip_dup')
            with _dzb:
                do_merge_dup = st.button('📄 Gabung 1 PDF Semua Duplikat',
                                         use_container_width=True, key='btn_merge_dup')

            # Bangun daftar semua baris duplikat beserta link dan label
            # Setiap baris di dup_df → link ke baris ke-N di found (atau link ke-1 jika tidak ada)
            all_dup_rows = []  # list of {nopol, kuantum, baris_ke, dup_label, link}
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)
                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    baris_ke  = int(drow['baris_ke'])
                    dup_label = f'_DUPLIKAT{baris_ke}'
                    # Assign link: baris ke-1 → link ke-1, baris ke-2 → link ke-2 (atau link ke-1 jika hanya ada 1)
                    if n_links == 0:
                        link = None
                    elif i_row <= n_links:
                        link = links_found[i_row - 1]
                    else:
                        link = links_found[0]  # fallback ke link pertama
                    all_dup_rows.append({
                        'nopol':     nopol,
                        'kuantum':   int(kuantum),
                        'baris_ke':  baris_ke,
                        'dup_label': dup_label,
                        'link':      link,
                    })

            # Bulk ZIP duplikat
            if do_zip_dup:
                valid_rows = [r for r in all_dup_rows if r['link']]
                if not valid_rows:
                    st.warning('⚠️ Tidak ada link yang tersedia untuk didownload.')
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
                        with st.expander(f'❌ {len(fail_list)} file gagal'):
                            for f in fail_list: st.write(f'• {f}')

            # Bulk Gabung PDF duplikat
            if do_merge_dup:
                valid_rows = [r for r in all_dup_rows if r['link']]
                if not valid_rows:
                    st.warning('⚠️ Tidak ada link yang tersedia.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']}
                                for i, r in enumerate(valid_rows)]
                    ok_files, fail_dl, new_cache = run_bulk_download(rows_dl, 'Duplikat PDF')
                    st.session_state.dl_cache.update(new_cache)
                    if ok_files:
                        with st.spinner('Menggabungkan PDF duplikat...'):
                            ordered = [new_cache.get(r['link']) or
                                       st.session_state.dl_cache.get(r['link'])
                                       for r in valid_rows]
                            ordered = [x for x in ordered if x]
                            merged  = merge_pdfs(ordered)
                        if merged:
                            st.success(f'✅ **{len(ordered)} file berhasil digabung** · '
                                       f'{len(merged)//1024:,} KB')
                            st.download_button('💾 Simpan PDF Duplikat Gabungan',
                                               merged, 'duplikat_gabungan.pdf',
                                               'application/pdf', key='dl_merge_dup_result')
                        else:
                            st.error('❌ Gagal membuat PDF gabungan.')
                    if fail_dl:
                        with st.expander(f'⚠️ {len(fail_dl)} file gagal'):
                            for f in fail_dl: st.write(f'• {f}')

            # ── Tabel detail per baris duplikat ─────────────────────────────
            st.markdown('<div class="section-label">Detail Setiap Baris Duplikat</div>',
                        unsafe_allow_html=True)
            dh0, dh1, dh2, dh3, dh4, dh5, dh6 = st.columns([0.5, 2.2, 1.3, 1.5, 1.8, 1.0, 1.8])
            dh0.markdown('**Baris ke-**')
            dh1.markdown('**NOPOL**')
            dh2.markdown('**Kuantum**')
            dh3.markdown('**Label File**')
            dh4.markdown('**Link GDrive**')
            dh5.markdown('**👁**')
            dh6.markdown('**⬇ Download**')
            st.divider()

            row_counter = 0
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                if sd_dup.strip() and norm_nopol(sd_dup.strip()) not in nopol:
                    continue

                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)

                # Banner grup
                st.markdown(
                    f'<div style="background:#fdf4ff;border:1px solid #d8b4fe;border-radius:8px;'
                    f'padding:8px 16px;margin:12px 0 4px;">'
                    f'<b style="color:#7c3aed">🚛 {nopol}</b>'
                    f'<span style="color:#94a3b8;margin:0 8px">|</span>'
                    f'<b style="color:#1e40af">Kuantum: {int(kuantum):,}</b>'
                    f'<span style="color:#94a3b8;margin:0 8px">|</span>'
                    f'<span style="color:#dc2626;font-size:0.8rem">'
                    f'Muncul {len(grp)}x di File 1</span>'
                    f'<span style="color:#94a3b8;margin:0 8px">|</span>'
                    f'<span style="color:#0369a1;font-size:0.8rem">'
                    f'{n_links} link tersedia di File 2</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

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

                    uid  = f'dup_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}_{baris_ke}'
                    cols = st.columns([0.5, 2.2, 1.3, 1.5, 1.8, 1.0, 1.8])

                    cols[0].markdown(f'**ke-{baris_ke}**')
                    cols[1].markdown(f'`{nopol}`')
                    cols[2].markdown(f'{int(kuantum):,}')
                    cols[3].markdown(
                        f'<code style="background:#ede9fe;color:#7c3aed;'
                        f'padding:2px 8px;border-radius:4px">{dup_label}</code>',
                        unsafe_allow_html=True)

                    if link and fid:
                        cols[4].markdown(f'[🔗 Buka](https://drive.google.com/file/d/{fid}/view)')
                    elif link:
                        cols[4].markdown(f'[🔗 Buka]({link})')
                    else:
                        cols[4].markdown('`—` Tidak ada link')

                    # Tombol preview
                    with cols[5]:
                        if link:
                            prev_grp_key = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                            is_active    = (st.session_state.dup_prev_active.get(prev_grp_key)
                                            == baris_ke)
                            btn_lbl      = '👁️ ✕' if is_active else '👁️'
                            if st.button(btn_lbl, key=f'dprev_{uid}'):
                                st.session_state.dup_prev_active[prev_grp_key] = (
                                    None if is_active else baris_ke)
                                st.rerun()

                    # Tombol download
                    with cols[6]:
                        if link:
                            cached = st.session_state.dl_cache.get(link)
                            if cached:
                                ext   = infer_extension(cached)
                                fname = make_safe_filename(nopol, kuantum, row_counter, ext,
                                                           total=n_dup_rows, dup_label=dup_label)
                                mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                st.download_button(f'⬇️ .{ext.upper()}', cached,
                                                   fname, mime, key=f'ddl_{uid}')
                            else:
                                if st.button('⬇️ Download', key=f'ddlb_{uid}'):
                                    with st.spinner(f'Mengunduh {nopol}{dup_label}...'):
                                        ct = download_file(link)
                                    if ct:
                                        st.session_state.dl_cache[link] = ct
                                        ext   = infer_extension(ct)
                                        fname = make_safe_filename(
                                            nopol, kuantum, row_counter, ext,
                                            total=n_dup_rows, dup_label=dup_label)
                                        mime  = 'application/pdf' if ext == 'pdf' else f'image/{ext}'
                                        st.download_button(f'💾 Simpan .{ext.upper()}', ct,
                                                           fname, mime, key=f'ddls_{uid}')
                                        st.success(f'✅ {fname} siap disimpan!')
                                    else:
                                        st.error('❌ Gagal mengunduh.')
                        else:
                            st.markdown('`—`')

                    # Preview inline
                    prev_grp_key = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                    if link and st.session_state.dup_prev_active.get(prev_grp_key) == baris_ke:
                        purl = to_preview(link)
                        if purl:
                            import streamlit.components.v1 as components
                            st.markdown(
                                f'<div class="suggestion-box">👁️ <b>Preview</b> — '
                                f'<code>{nopol}</code> · Kuantum: <b>{int(kuantum):,}</b> · '
                                f'Label: <code style="color:#7c3aed">{dup_label}</code></div>',
                                unsafe_allow_html=True)
                            components.html(
                                f'<iframe src="{purl}" width="100%" height="680" '
                                f'style="border:1px solid #d8b4fe;border-radius:10px;'
                                f'background:#fff" allow="autoplay"></iframe>', height=700)
                            st.caption(f'Preview kosong? → [buka di tab baru]({purl})')
                        else:
                            st.error('Link preview tidak valid.')

                    row_counter += 1

            # Export CSV duplikat
            st.markdown('<div class="section-label">Export Daftar Duplikat</div>',
                        unsafe_allow_html=True)
            export_dup = dup_df[['nopol','kuantum','baris_ke','jumlah_duplikat']].copy()
            export_dup.columns = ['NOPOL','Kuantum','Baris ke-','Total Duplikat']
            export_dup['Label File'] = export_dup['Baris ke-'].apply(lambda x: f'_DUPLIKAT{int(x)}')
            _de, _ = st.columns([2, 8])
            with _de:
                st.download_button('📥 Export CSV Duplikat',
                                   export_dup.to_csv(index=False).encode('utf-8'),
                                   'duplikat_file1.csv', 'text/csv', key='dl_dup')
            st.dataframe(export_dup, use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 2 — TIDAK MATCH KUANTUM
    # ──────────────────────────────────────────────────────────────────────────
    with tab2:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown('<div class="success-box">🎉 <b>Tidak ada perbedaan kuantum!</b></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="warn-box">⚠️ <b>{len(nopol_diff)} data</b> — NOPOL ditemukan di '
                f'File 2 namun kuantumnya tidak cocok.</div>', unsafe_allow_html=True)
            sd = st.text_input('', placeholder='🔍 Filter berdasarkan NOPOL...',
                               label_visibility='collapsed', key='sd')
            dd = nopol_diff.copy()
            if sd.strip():
                dd = dd[dd['NOPOL'].str.contains(
                    re.escape(norm_nopol(sd)), na=False, case=False)].reset_index(drop=True)
            st.dataframe(dd, use_container_width=True, hide_index=True)
            _ca, _ = st.columns([2, 8])
            with _ca:
                st.download_button('📥 Export CSV', dd.to_csv(index=False).encode('utf-8'),
                                   'tidak_match_kuantum.csv', 'text/csv', key='dl_a')

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 3 — TIDAK MATCH NOPOL + SARAN FUZZY
    # ──────────────────────────────────────────────────────────────────────────
    with tab3:
        miss_items = [x for x in missing_detail
                      if x['kategori'] in ('nopol_mirip', 'tidak_ada')]
        if not miss_items:
            st.markdown('<div class="success-box">🎉 <b>Semua NOPOL ditemukan di File 2!</b></div>',
                        unsafe_allow_html=True)
        else:
            n_mirip   = sum(1 for x in miss_items if x['kategori'] == 'nopol_mirip')
            n_tdk_ada = sum(1 for x in miss_items if x['kategori'] == 'tidak_ada')
            st.markdown(
                f'<div class="error-box">❌ <b>{len(miss_items)} data</b> — NOPOL tidak ada '
                f'di File 2.<br>🔍 <b>{n_mirip} data</b> punya saran NOPOL mirip · '
                f'🚫 <b>{n_tdk_ada} data</b> tanpa saran.</div>', unsafe_allow_html=True)

            sm = st.text_input('', placeholder='🔍 Filter berdasarkan NOPOL...',
                               label_visibility='collapsed', key='sm')
            min_sim = st.slider('🎚️ Threshold Kemiripan NOPOL (%)',
                                min_value=30, max_value=90, value=50, step=5,
                                key='sim_slider')

            for item_idx, item in enumerate(miss_items):
                nopol   = item['nopol']
                kuantum = item['kuantum']
                if sm.strip() and norm_nopol(sm.strip()) not in nopol:
                    continue
                saran_filtered = [s for s in item['saran'] if s['similarity'] >= min_sim]
                badge_color    = '#0c4a6e' if saran_filtered else '#7f1d1d'
                badge_bg       = '#e0f2fe' if saran_filtered else '#fee2e2'
                badge_text     = (f'🔍 {len(saran_filtered)} saran'
                                  if saran_filtered else '🚫 Tidak ada saran')
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;'
                    f'padding:14px 18px;margin:10px 0;">'
                    f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
                    f'<span style="font-family:monospace;font-weight:700;color:#1e40af;'
                    f'font-size:1rem">🚛 {nopol}</span>'
                    f'<span style="color:#64748b">Kuantum: <b>{kuantum:,}</b></span>'
                    f'<span style="background:{badge_bg};color:{badge_color};border-radius:6px;'
                    f'padding:2px 10px;font-size:0.78rem;font-weight:600">{badge_text}</span>'
                    f'</div></div>', unsafe_allow_html=True)

                if saran_filtered:
                    sh0, sh1, sh2, sh3, sh4 = st.columns([0.4, 2.5, 1.5, 1.5, 2])
                    sh0.markdown('<small><b>#</b></small>', unsafe_allow_html=True)
                    sh1.markdown('<small><b>NOPOL di File 2</b></small>', unsafe_allow_html=True)
                    sh2.markdown('<small><b>Kemiripan</b></small>', unsafe_allow_html=True)
                    sh3.markdown('<small><b>Kuantum</b></small>', unsafe_allow_html=True)
                    sh4.markdown('<small><b>Aksi</b></small>', unsafe_allow_html=True)

                    for s_idx, saran in enumerate(saran_filtered):
                        saran_key = f'saran_{item_idx}_{s_idx}'
                        sc0,sc1,sc2,sc3,sc4 = st.columns([0.4, 2.5, 1.5, 1.5, 2])
                        sim       = saran['similarity']
                        sim_color = ('#16a34a' if sim >= 80 else
                                     '#b45309' if sim >= 65 else '#dc2626')
                        sc0.markdown(f'`{s_idx+1}`')
                        sc1.markdown(f'`{saran["nopol_f2"]}`')
                        sc2.markdown(
                            f'<span style="color:{sim_color};font-weight:700">{sim}%</span>',
                            unsafe_allow_html=True)
                        sc3.markdown(f'{saran["kuantum"]:,}')
                        with sc4:
                            col_prev, col_dl = st.columns(2)
                            with col_prev:
                                prev_key_active = st.session_state.saran_preview.get(
                                    f'item_{item_idx}')
                                is_active_prev  = (prev_key_active == s_idx)
                                if st.button('👁️ ✕' if is_active_prev else '👁️ Lihat',
                                             key=f'sprev_{saran_key}'):
                                    st.session_state.saran_preview[f'item_{item_idx}'] = (
                                        None if is_active_prev else s_idx)
                                    st.rerun()
                            with col_dl:
                                link_saran = saran['surat_jalan']
                                cached_s   = st.session_state.dl_cache.get(link_saran)
                                if cached_s:
                                    ext_s   = infer_extension(cached_s)
                                    fname_s = make_safe_filename(
                                        saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                    mime_s  = ('application/pdf' if ext_s == 'pdf'
                                               else f'image/{ext_s}')
                                    st.download_button(f'⬇️ .{ext_s.upper()}', cached_s,
                                                       fname_s, mime_s,
                                                       key=f'sdl_cached_{saran_key}')
                                else:
                                    if st.button('⬇️ Download', key=f'sdl_{saran_key}'):
                                        with st.spinner(f'Mengunduh {saran["nopol_f2"]}...'):
                                            ct_s = download_file(link_saran)
                                        if ct_s:
                                            st.session_state.dl_cache[link_saran] = ct_s
                                            ext_s   = infer_extension(ct_s)
                                            fname_s = make_safe_filename(
                                                saran['nopol_f2'], saran['kuantum'],
                                                s_idx, ext_s)
                                            mime_s  = ('application/pdf' if ext_s == 'pdf'
                                                       else f'image/{ext_s}')
                                            st.download_button(
                                                f'💾 Simpan .{ext_s.upper()}', ct_s,
                                                fname_s, mime_s,
                                                key=f'sdl_save_{saran_key}')
                                            st.success(f'✅ {fname_s} siap disimpan!')
                                        else:
                                            st.error('❌ Gagal mengunduh.')

                        active_s_idx = st.session_state.saran_preview.get(f'item_{item_idx}')
                        if active_s_idx == s_idx:
                            purl_s = to_preview(saran['surat_jalan'])
                            if purl_s:
                                import streamlit.components.v1 as components
                                st.markdown(
                                    f'<div class="suggestion-box">👁️ <b>Preview</b> — '
                                    f'NOPOL: <code>{saran["nopol_f2"]}</code> | '
                                    f'Kuantum: <b>{saran["kuantum"]:,}</b> | '
                                    f'Kemiripan: <b style="color:{sim_color}">{sim}%</b></div>',
                                    unsafe_allow_html=True)
                                components.html(
                                    f'<iframe src="{purl_s}" width="100%" height="680" '
                                    f'style="border:1px solid #7dd3fc;border-radius:10px;'
                                    f'background:#fff" allow="autoplay"></iframe>', height=700)
                                st.caption(f'Preview kosong? → [buka di tab baru]({purl_s})')
                            else:
                                st.error('Link preview tidak valid.')
                else:
                    msg = ('🚫 Tidak ada NOPOL di File 2 yang memiliki kuantum sama dan kemiripan cukup.'
                           if item['kategori'] == 'tidak_ada'
                           else f'🔽 Kurangi threshold (saat ini {min_sim}%) untuk lebih banyak saran.')
                    st.markdown(
                        f'<div style="padding:6px 18px;color:#94a3b8;font-size:0.82rem">'
                        f'{msg}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">Export Tabel</div>', unsafe_allow_html=True)
            if nopol_miss is not None and not nopol_miss.empty:
                _cb, _ = st.columns([2, 8])
                with _cb:
                    st.download_button('📥 Export CSV',
                                       nopol_miss.to_csv(index=False).encode('utf-8'),
                                       'tidak_match_nopol.csv', 'text/csv', key='dl_b')
                st.dataframe(nopol_miss, use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────────────────────────────────────
    # TAB 4 — SEMUA TIDAK MATCH
    # ──────────────────────────────────────────────────────────────────────────
    with tab4:
        if missing.empty:
            st.markdown('<div class="success-box">🎉 <b>Semua data berhasil dicocokkan!</b></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="error-box">🔴 <b>{n_all_miss} total kombinasi tidak match</b> '
                f'(kuantum beda + NOPOL tidak ada).</div>', unsafe_allow_html=True)
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
                    return f'🔍 NOPOL tidak ada — Saran: {top["nopol_f2"]} ({top["similarity"]}%)'
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
                    - 🔍 **Ada saran NOPOL mirip:** {n_nopol_mirip} data
                    - 🔴 **Total tidak match:** {n_all_miss} data
                    """)
            with col_dl:
                st.download_button('📥 Export CSV',
                                   all_m.to_csv(index=False).encode('utf-8'),
                                   'semua_tidak_match.csv', 'text/csv', key='dl_c')
