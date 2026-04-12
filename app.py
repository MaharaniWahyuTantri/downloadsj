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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; background: #0d1117; color: #e6edf3; }
.stApp { background: #0d1117; }

.main-header {
    background: linear-gradient(135deg,#161b22,#1c2128);
    border:1px solid #30363d; border-radius:12px;
    padding:24px 32px; margin-bottom:20px;
    display:flex; align-items:center; gap:16px;
}
.main-header h1 { font-size:1.7rem; font-weight:700; color:#f0f6fc; }
.main-header p  { font-size:0.85rem; color:#8b949e; margin-top:4px; }

.upload-card {
    background:#161b22; border:1px solid #30363d;
    border-radius:10px; padding:16px 20px; margin-bottom:8px;
}
.upload-card h3 {
    font-size:0.8rem; font-weight:700; color:#58a6ff;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;
}
.upload-card p { font-size:0.78rem; color:#8b949e; }

.stat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:16px 0; }
.stat-card {
    background:#161b22; border:1px solid #30363d;
    border-radius:10px; padding:14px 18px; text-align:center;
}
.stat-num { font-family:'IBM Plex Mono',monospace; font-size:1.8rem; font-weight:700; line-height:1; }
.stat-lbl { font-size:0.72rem; color:#8b949e; margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }
.c-blue{color:#58a6ff} .c-green{color:#3fb950} .c-red{color:#f85149} .c-yellow{color:#d29922}

.warn-box {
    background:#2a1f0a; border:1px solid #d2992244;
    border-radius:8px; padding:14px 18px; margin:12px 0;
    font-size:0.85rem; color:#d29922; line-height:1.6;
}
.section-label {
    font-size:0.72rem; text-transform:uppercase; letter-spacing:1.5px;
    color:#8b949e; margin:20px 0 10px; display:flex; align-items:center; gap:8px;
}
.section-label::after { content:''; flex:1; height:1px; background:#30363d; }

.stButton > button {
    background:#21262d !important; color:#e6edf3 !important;
    border:1px solid #30363d !important; border-radius:7px !important;
    font-size:0.8rem !important; padding:5px 12px !important; transition:all .15s !important;
}
.stButton > button:hover {
    background:#30363d !important; border-color:#58a6ff !important; color:#58a6ff !important;
}
div[data-testid="stFileUploader"] { background:#0d1117; border:1px dashed #30363d; border-radius:8px; }
.stProgress > div > div { background:#58a6ff !important; }
.stTextInput > div > div > input {
    background:#161b22 !important; border:1px solid #30363d !important;
    color:#e6edf3 !important; border-radius:7px !important;
}
</style>
""", unsafe_allow_html=True)

# ── UTILITIES ──────────────────────────────────────────────────────────────────

def norm_nopol(v):
    """Normalize plate number: uppercase, collapse whitespace, remove internal spaces for comparison."""
    s = re.sub(r'\s+', ' ', str(v)).strip().upper()
    return s

def norm_nopol_key(v):
    """Normalized key for matching: remove ALL spaces so 'BE1235AD' == 'BE 1235 AD'."""
    return re.sub(r'\s+', '', str(v)).upper()

def norm_kuantum(v):
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except:
        return None

def find_col(df, kws):
    """
    Find column matching any keyword (case-insensitive, space/underscore-insensitive).
    kws is a list of possible keyword fragments.
    """
    for col in df.columns:
        c = str(col).lower().replace(' ', '').replace('_', '')
        for k in kws:
            k_clean = k.lower().replace(' ', '').replace('_', '')
            if k_clean in c:
                return col
    return None

def extract_fid(link):
    if not isinstance(link, str):
        return None
    for p in [r'/file/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)', r'/d/([a-zA-Z0-9_-]+)']:
        m = re.search(p, link)
        if m:
            return m.group(1)
    return None

def to_preview(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def to_dl(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/uc?export=download&id={fid}' if fid else None

def download_file(url, retries=3, timeout=30):
    dl = to_dl(url)
    if not dl:
        return None
    for attempt in range(retries):
        try:
            s = requests.Session()
            r = s.get(dl, timeout=timeout, stream=True)
            if 'text/html' in r.headers.get('Content-Type', ''):
                m = re.search(r'name="confirm"\s+value="([^"]+)"', r.text)
                if m:
                    r = s.get(dl + f'&confirm={m.group(1)}', timeout=timeout, stream=True)
            if r.status_code == 200 and len(r.content) > 500:
                return r.content
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None

def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()

def read_file(f):
    return pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)

# ── LOAD FILE 1 ────────────────────────────────────────────────────────────────

def load_file1(df):
    # Keywords for NOPOL column (flexible)
    nopol_kws = ['nopol', 'no pol', 'nomor polisi', 'nopelat', 'pelat', 'plat', 'plate']
    # Keywords for KUANTUM column (flexible)
    kuantum_kws = ['kuantum', 'quantum', 'tonase', 'tonasa', 'qty', 'jumlah', 'volume', 'berat', 'kg']

    nc = find_col(df, nopol_kws)
    kc = find_col(df, kuantum_kws)

    if not nc:
        st.error(f"Kolom NOPOL tidak ditemukan di File 1. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"Kolom KUANTUM/TONASE tidak ditemukan di File 1. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(norm_nopol)
    out['nopol_key']   = df[nc].apply(norm_nopol_key)   # for matching
    out['kuantum']     = df[kc].apply(norm_kuantum)

    out = out[out['nopol'].notna() & (out['nopol'] != '') & (out['nopol_key'] != '')]
    out = out.dropna(subset=['kuantum'])
    return out.reset_index(drop=True)

# ── LOAD FILE 2 ────────────────────────────────────────────────────────────────

def load_file2(raw_df):
    df = raw_df.copy()

    if df.empty:
        return pd.DataFrame()

    # Check if first row is actually a header row embedded in data
    first_row = df.iloc[0].tolist()
    has_header_row = any('NOPOL' in str(v).upper() for v in first_row)
    if has_header_row:
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)

    nopol_kws   = ['nopol', 'no pol', 'nomor polisi', 'nopelat', 'pelat', 'plat', 'plate']
    kuantum_kws = ['kuantum', 'quantum', 'tonase', 'tonasa', 'qty', 'jumlah', 'volume', 'berat', 'kg']
    link_kws    = ['surat jalan', 'suratjalan', 'foto surat', 'link', 'url', 'drive', 'foto', 'gdrive']

    nc = find_col(df, nopol_kws)
    kc = find_col(df, kuantum_kws)
    lc = find_col(df, link_kws)

    if not nc:
        st.error(f"Kolom NOPOL tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"Kolom KUANTUM/TONASE tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not lc:
        st.error(f"Kolom SURAT JALAN / link tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(norm_nopol)
    out['nopol_key']   = df[nc].apply(norm_nopol_key)   # for matching (no spaces)
    out['kuantum']     = df[kc].apply(norm_kuantum)
    out['surat_jalan'] = df[lc].astype(str).str.strip()

    # Drop header rows that leaked in, drop empty nopol
    out = out[
        out['nopol'].notna() &
        (out['nopol'] != '') &
        (out['nopol_key'] != '') &
        (out['nopol'].str.upper() != 'NOPOL')
    ]
    out = out.dropna(subset=['kuantum'])

    # Keep only rows with valid Google Drive links
    out = out[out['surat_jalan'].str.startswith('http')].reset_index(drop=True)
    return out

# ── SESSION STATE ──────────────────────────────────────────────────────────────
for k in ['result_df', 'missing_df', 'active_preview', 'df2_debug']:
    if k not in st.session_state:
        st.session_state[k] = None

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:2.2rem">🚛</div>
  <div>
    <h1>Surat Jalan Filter</h1>
    <p>Match NOPOL (fleksibel spasi &amp; huruf kapital) → Preview &amp; Download Surat Jalan</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── UPLOAD ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown('<div class="upload-card"><h3>📋 File 1 — Target</h3><p>Kolom: NOPOL / Nomor Polisi, KUANTUM / TONASE</p></div>', unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv','xlsx','xls'], key='f1', label_visibility='collapsed')
with c2:
    st.markdown('<div class="upload-card"><h3>🗄️ File 2 — Database Surat Jalan</h3><p>Kolom: NOPOL, KUANTUM / TONASE, Foto Surat Jalan (link Google Drive)</p></div>', unsafe_allow_html=True)
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

            # ── MATCH LOGIC ────────────────────────────────────────────────────
            # Match hanya berdasarkan NOPOL (tanpa spasi, case-insensitive)
            # Satu NOPOL di File 1 bisa punya BANYAK surat jalan di File 2
            # Ambil SEMUA surat jalan yang nopol_key-nya cocok

            # Build lookup: nopol_key -> list of rows from df2
            df2_lookup = df2.groupby('nopol_key')

            result_rows = []
            missing_rows = []

            for _, row1 in df1.iterrows():
                key = row1['nopol_key']
                if key in df2_lookup.groups:
                    matches = df2_lookup.get_group(key)
                    for _, row2 in matches.iterrows():
                        result_rows.append({
                            'nopol':       row1['nopol'],       # tampilkan format dari File 1
                            'kuantum':     row2['kuantum'],     # kuantum dari File 2
                            'surat_jalan': row2['surat_jalan']
                        })
                else:
                    missing_rows.append({
                        'nopol':   row1['nopol'],
                        'kuantum': row1['kuantum']
                    })

            found   = pd.DataFrame(result_rows).reset_index(drop=True)
            missing = pd.DataFrame(missing_rows).reset_index(drop=True) if missing_rows else pd.DataFrame(columns=['nopol','kuantum'])

            st.session_state.result_df      = found
            st.session_state.missing_df     = missing
            st.session_state.df2_debug      = df2
            st.session_state.active_preview = None

            n_f1_unique = df1['nopol_key'].nunique()
            n_matched   = found['nopol'].nunique() if not found.empty else 0
            st.success(f'✅ Selesai. {len(found)} surat jalan ditemukan dari {len(df1)} baris File 1 ({n_matched}/{n_f1_unique} NOPOL unik cocok).')

# ── RESULTS ────────────────────────────────────────────────────────────────────
if st.session_state.result_df is not None:
    found:   pd.DataFrame = st.session_state.result_df
    missing: pd.DataFrame = st.session_state.missing_df
    df2_all: pd.DataFrame = st.session_state.df2_debug

    total_f1 = len(found) + len(missing)

    # SUMMARY
    st.markdown('<div class="section-label">Ringkasan</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num c-blue">{total_f1}</div><div class="stat-lbl">Total Baris File 1</div></div>
      <div class="stat-card"><div class="stat-num c-green">{len(found)}</div><div class="stat-lbl">Surat Jalan Ditemukan</div></div>
      <div class="stat-card"><div class="stat-num c-red">{len(missing)}</div><div class="stat-lbl">NOPOL Tidak Match</div></div>
      <div class="stat-card"><div class="stat-num c-yellow">{len(df2_all)}</div><div class="stat-lbl">Total File 2</div></div>
    </div>
    """, unsafe_allow_html=True)

    # DIAGNOSTIK
    if len(missing) > 0:
        with st.expander(f'🔍 Diagnostik: {len(missing)} NOPOL tidak ditemukan di File 2', expanded=(len(found) == 0)):
            st.markdown(f'**❌ NOPOL berikut tidak ditemukan sama sekali di File 2:**')
            st.markdown("""
            <div class="warn-box">
            💡 <b>Kemungkinan penyebab:</b> NOPOL di File 1 tidak ada di database File 2 sama sekali.
            Pastikan format NOPOL benar (spasi/tanpa spasi tidak masalah, huruf kapital tidak masalah).
            </div>
            """, unsafe_allow_html=True)
            st.dataframe(missing, use_container_width=True, hide_index=True)

    # TABEL HASIL MATCH
    if len(found) > 0:
        st.markdown('<div class="section-label">Surat Jalan yang Ditemukan</div>', unsafe_allow_html=True)

        search = st.text_input('🔍 Filter NOPOL...', placeholder='Ketik NOPOL untuk filter...', label_visibility='collapsed')
        disp = found.copy()
        if search.strip():
            disp = disp[disp['nopol'].str.contains(re.sub(r'\s+', '', search.strip()).upper(), na=False, regex=False)].reset_index(drop=True)
            if disp.empty:
                # Coba match dengan spasi
                disp = found[found['nopol'].str.upper().str.contains(search.strip().upper(), na=False)].reset_index(drop=True)

        st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

        # BULK DOWNLOAD
        bc, _ = st.columns([3, 7])
        with bc:
            do_bulk = st.button('📦 Download Semua (ZIP)', use_container_width=True)

        if do_bulk and len(disp) > 0:
            items = list(disp[['nopol','kuantum','surat_jalan']].itertuples(index=True))
            prog = st.progress(0)
            stxt = st.empty()
            done, ok_files, fail_list = 0, {}, []
            stxt.text(f'Mengunduh 0 / {len(items)} file...')

            def _worker(row):
                ct = download_file(row.surat_jalan)
                kuantum_val = int(row.kuantum) if row.kuantum and not pd.isna(row.kuantum) else 0
                fname = f'{row.nopol}_{kuantum_val}.pdf'
                # sanitize filename
                fname = re.sub(r'[\\/*?:"<>|]', '_', fname)
                return fname, ct, row.nopol

            with ThreadPoolExecutor(max_workers=10) as ex:
                futs = {ex.submit(_worker, r): r for r in items}
                for fut in as_completed(futs):
                    fn, ct, np_val = fut.result()
                    if ct:
                        ok_files[fn] = ct
                    else:
                        fail_list.append(np_val)
                    done += 1
                    prog.progress(done / len(items))
                    stxt.text(f'Mengunduh {done} / {len(items)} file...')

            stxt.text(f'✅ Berhasil: {len(ok_files)} | ❌ Gagal: {len(fail_list)}')
            if ok_files:
                st.download_button(
                    f'💾 Simpan ZIP ({len(ok_files)} file)',
                    make_zip(ok_files),
                    'surat_jalan_semua.zip',
                    'application/zip'
                )
            if fail_list:
                with st.expander(f'❌ {len(fail_list)} gagal'):
                    st.write(fail_list)

        # TABEL INDIVIDUAL
        st.markdown('<div class="section-label">Detail per Surat Jalan</div>', unsafe_allow_html=True)
        hcols = st.columns([1, 3, 2, 2, 2])
        for col, lbl in zip(hcols, ['No.', 'NOPOL', 'KUANTUM', '👁 Lihat', '⬇ Download']):
            col.markdown(f'**{lbl}**')
        st.divider()

        for i, row in disp.iterrows():
            nopol   = row['nopol']
            kuantum = int(row['kuantum']) if row['kuantum'] and not pd.isna(row['kuantum']) else 0
            link    = row['surat_jalan']

            cols = st.columns([1, 3, 2, 2, 2])
            cols[0].markdown(f'`#{i+1}`')
            cols[1].markdown(f'`{nopol}`')
            cols[2].markdown(f'**{kuantum:,}**')

            with cols[3]:
                if st.button('👁️ Lihat', key=f'v_{i}'):
                    st.session_state.active_preview = None if st.session_state.active_preview == i else i

            with cols[4]:
                ct = download_file(link)
                if ct:
                    fname = re.sub(r'[\\/*?:"<>|]', '_', f'{nopol}_{kuantum}.pdf')
                    st.download_button(
                        '⬇️ Download', ct, fname, 'application/pdf',
                        key=f'd_{i}'
                    )
                else:
                    st.button('⬇️ Gagal', key=f'df_{i}', disabled=True)

            # Preview iframe tepat di bawah baris
            if st.session_state.active_preview == i:
                purl = to_preview(link)
                if purl:
                    import streamlit.components.v1 as components
                    components.html(
                        f'<iframe src="{purl}" width="100%" height="680"'
                        f' style="border:1px solid #30363d;border-radius:8px;background:#fff"></iframe>',
                        height=700
                    )
                else:
                    st.error('Link preview tidak valid.')

    else:
        st.markdown("""
        <div class="warn-box">
        ⚠️ <strong>0 surat jalan ditemukan.</strong><br>
        Tidak ada NOPOL dari File 1 yang cocok di File 2. Lihat diagnostik di atas.
        </div>
        """, unsafe_allow_html=True)
