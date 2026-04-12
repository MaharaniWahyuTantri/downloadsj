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
.info-box {
    background:#0d1f2a; border:1px solid #58a6ff44;
    border-radius:8px; padding:14px 18px; margin:12px 0;
    font-size:0.85rem; color:#58a6ff; line-height:1.6;
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
    """Normalisasi nopol: hapus spasi berlebih, uppercase.
    BE1235AD -> BE 1235 AD (tambah spasi antar bagian)
    Handles: 'BE1235AD', 'BE 1235AD', 'BE1235 AD', 'BE 1235 AD' -> semua jadi 'BE 1235 AD'
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = str(v).strip().upper()
    # Hapus spasi berlebih dulu
    s = re.sub(r'\s+', ' ', s)
    # Tambah spasi antara huruf-angka dan angka-huruf jika belum ada
    # Misal: BE1235AD -> BE 1235 AD
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    # Hapus spasi berlebih lagi
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def norm_kuantum(v):
    """Normalisasi kuantum ke integer."""
    try:
        return int(float(str(v).replace(',', '.').strip()))
    except:
        return None

def find_col(df, kws):
    """Cari kolom berdasarkan keyword (case insensitive, flexible)."""
    for col in df.columns:
        c = col.lower().replace(' ', '').replace('_', '')
        for k in kws:
            if k.replace(' ', '').replace('_', '') in c:
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

def load_file1(df):
    """Load & normalisasi File 1 (NOPOL + KUANTUM)."""
    # Cari kolom NOPOL (berbagai nama)
    nc = find_col(df, ['nopol', 'nopol', 'nomor polisi', 'no pol', 'no.pol', 'nopolisi'])
    if not nc:
        nc = find_col(df, ['pol'])
    # Cari kolom KUANTUM (berbagai nama)
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

def load_file2(raw_df):
    """Load & normalisasi File 2 (NOPOL + KUANTUM + Link Surat Jalan)."""
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()

    # Deteksi apakah baris pertama adalah header duplikat
    first_row = df.iloc[0].tolist()
    has_header_row = any(str(v).upper().strip() in ['NOPOL', 'KUANTUM', 'FOTO SURAT JALAN'] for v in first_row)
    if has_header_row:
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)

    # Cari kolom NOPOL
    nc = find_col(df, ['nopol', 'nomor polisi', 'no pol', 'no.pol', 'nopolisi'])
    if not nc:
        nc = find_col(df, ['pol'])
    # Cari kolom KUANTUM
    kc = find_col(df, ['kuantum', 'quantum', 'tonase', 'tonage', 'qty', 'jumlah', 'volume', 'berat'])
    # Cari kolom Link Surat Jalan
    lc = find_col(df, ['surat jalan', 'suratjalan', 'foto surat', 'foto', 'link', 'url', 'drive', 'gdrive'])

    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM/TONASE tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not lc:
        st.error(f"❌ Kolom SURAT JALAN / link tidak ditemukan di File 2. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else '')
    out['kuantum']     = df[kc].apply(norm_kuantum)
    out['surat_jalan'] = df[lc].astype(str).str.strip()

    # Buang baris header yang ikut terbaca
    out = out[out['nopol'] != '']
    out = out[out['nopol'].str.upper() != 'NOPOL']
    out = out.dropna(subset=['kuantum'])
    out = out[out['kuantum'] > 0]

    # Hanya simpan baris dengan link yang valid (http atau nama file .jpg/.pdf)
    valid_link = (
        out['surat_jalan'].str.startswith('http') |
        out['surat_jalan'].str.lower().str.endswith('.jpg') |
        out['surat_jalan'].str.lower().str.endswith('.pdf') |
        out['surat_jalan'].str.lower().str.endswith('.png')
    )
    out = out[valid_link].reset_index(drop=True)
    return out


# ── SESSION STATE ──────────────────────────────────────────────────────────────
for k in ['result_df', 'missing_df', 'active_preview', 'df2_debug', 'df1_debug']:
    if k not in st.session_state:
        st.session_state[k] = None

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:2.2rem">🚛</div>
  <div>
    <h1>Surat Jalan Filter</h1>
    <p>Match NOPOL + KUANTUM (ketat) → Preview &amp; Download Surat Jalan</p>
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
            # df1 bisa punya duplikat (nopol+kuantum sama), df2 juga
            # Untuk setiap row di df1, cari SEMUA match di df2
            result_rows = []
            for idx, row1 in df1.iterrows():
                matches = df2[
                    (df2['nopol'] == row1['nopol']) &
                    (df2['kuantum'] == row1['kuantum'])
                ]
                # Filter hanya yang punya link http
                http_matches = matches[matches['surat_jalan'].str.startswith('http')]
                if len(http_matches) > 0:
                    for _, row2 in http_matches.iterrows():
                        result_rows.append({
                            'nopol': row1['nopol'],
                            'kuantum': row1['kuantum'],
                            'surat_jalan': row2['surat_jalan'],
                            '_f1_idx': idx
                        })
                else:
                    result_rows.append({
                        'nopol': row1['nopol'],
                        'kuantum': row1['kuantum'],
                        'surat_jalan': None,
                        '_f1_idx': idx
                    })

            result = pd.DataFrame(result_rows)
            found   = result[result['surat_jalan'].notna() & result['surat_jalan'].str.startswith('http', na=False)].copy().reset_index(drop=True)
            # Missing: baris file1 yang tidak punya match sama sekali (deduplicate by f1 idx)
            matched_f1_idx = set(found['_f1_idx'].tolist())
            missing_rows = []
            for idx, row1 in df1.iterrows():
                if idx not in matched_f1_idx:
                    missing_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum']})
            missing = pd.DataFrame(missing_rows).drop_duplicates(subset=['nopol','kuantum']).reset_index(drop=True)

            st.session_state.result_df      = found
            st.session_state.missing_df     = missing
            st.session_state.df2_debug      = df2
            st.session_state.df1_debug      = df1
            st.session_state.active_preview = None

            match_count = df1[df1.index.isin(matched_f1_idx)].drop_duplicates(subset=['nopol','kuantum']).shape[0]
            st.success(f'✅ Selesai! {len(found)} surat jalan ditemukan untuk {match_count} entri unik dari {len(df1)} data File 1.')

# ── RESULTS ────────────────────────────────────────────────────────────────────
if st.session_state.result_df is not None:
    found:   pd.DataFrame = st.session_state.result_df
    missing: pd.DataFrame = st.session_state.missing_df
    df2_all: pd.DataFrame = st.session_state.df2_debug
    df1_all: pd.DataFrame = st.session_state.df1_debug
    total_f1 = len(df1_all)

    # SUMMARY
    st.markdown('<div class="section-label">Ringkasan</div>', unsafe_allow_html=True)
    unique_matched = len(found[['nopol','kuantum']].drop_duplicates())
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num c-blue">{total_f1}</div><div class="stat-lbl">Total File 1</div></div>
      <div class="stat-card"><div class="stat-num c-green">{len(found)}</div><div class="stat-lbl">Surat Jalan Match</div></div>
      <div class="stat-card"><div class="stat-num c-red">{len(missing)}</div><div class="stat-lbl">Tidak Match</div></div>
      <div class="stat-card"><div class="stat-num c-yellow">{len(df2_all)}</div><div class="stat-lbl">Total File 2</div></div>
    </div>
    """, unsafe_allow_html=True)

    # INFO tentang cara kerja match
    st.markdown("""
    <div class="info-box">
    ℹ️ <b>Cara kerja match:</b> NOPOL <em>dan</em> KUANTUM harus <b>sama persis</b> di kedua file.
    Normalisasi otomatis: spasi ganda → 1 spasi, case insensitive (BE1235AD = BE 1235 AD).
    Satu NOPOL+KUANTUM di File 1 bisa menghasilkan <b>lebih dari satu surat jalan</b> jika di File 2 ada banyak baris yang cocok.
    </div>
    """, unsafe_allow_html=True)

    # DIAGNOSTIK
    if len(missing) > 0:
        with st.expander(f'🔍 Diagnostik: {len(missing)} kombinasi NOPOL+KUANTUM tidak match', expanded=(len(found) == 0)):
            nopol_beda_k = []
            nopol_tidak_ada = []

            for _, row in missing.iterrows():
                f2_match = df2_all[df2_all['nopol'] == row['nopol']]
                if len(f2_match) > 0:
                    kuantums = sorted(f2_match['kuantum'].dropna().astype(int).unique().tolist())
                    display  = ', '.join(map(str, kuantums[:8]))
                    if len(kuantums) > 8:
                        display += f' ... (+{len(kuantums)-8} lagi)'
                    nopol_beda_k.append({
                        'NOPOL': row['nopol'],
                        'KUANTUM di File 1': int(row['kuantum']),
                        'KUANTUM tersedia di File 2': display
                    })
                else:
                    nopol_tidak_ada.append({
                        'NOPOL': row['nopol'],
                        'KUANTUM di File 1': int(row['kuantum'])
                    })

            if nopol_beda_k:
                st.markdown(f'**⚠️ {len(nopol_beda_k)} NOPOL ditemukan di File 2, tapi KUANTUM tidak sama:**')
                st.markdown("""
                <div class="warn-box">
                💡 <b>Penyebab:</b> Nilai KUANTUM di File 1 berbeda dengan yang ada di File 2.
                Pastikan KUANTUM di File 1 sesuai dengan nilai nyata di File 2 agar bisa match.
                Match hanya terjadi jika NOPOL <em>DAN</em> KUANTUM sama persis.
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(nopol_beda_k), use_container_width=True, hide_index=True)

            if nopol_tidak_ada:
                st.markdown(f'**❌ {len(nopol_tidak_ada)} NOPOL tidak ditemukan sama sekali di File 2:**')
                st.dataframe(pd.DataFrame(nopol_tidak_ada), use_container_width=True, hide_index=True)

    # TABEL HASIL MATCH
    if len(found) > 0:
        st.markdown('<div class="section-label">Surat Jalan yang Ditemukan</div>', unsafe_allow_html=True)

        search = st.text_input('🔍 Filter NOPOL...', placeholder='Ketik NOPOL untuk filter...', label_visibility='collapsed')
        disp = found.copy()
        if search.strip():
            # Normalisasi input pencarian juga
            search_norm = norm_nopol(search.strip())
            disp = disp[disp['nopol'].str.contains(re.escape(search_norm), na=False, case=False)].reset_index(drop=True)

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
                fn = f'{row.nopol}_{int(row.kuantum)}.pdf'
                return fn, ct, row.nopol

            with ThreadPoolExecutor(max_workers=10) as ex:
                futs = {ex.submit(_worker, r): r for r in items}
                for fut in as_completed(futs):
                    fn, ct, np_val = fut.result()
                    if ct:
                        # Handle duplikat nama file
                        base_fn = fn
                        counter = 1
                        while fn in ok_files:
                            name_part = base_fn.rsplit('.', 1)[0]
                            fn = f'{name_part}_{counter}.pdf'
                            counter += 1
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
            kuantum = int(row['kuantum'])
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
                    st.download_button(
                        '⬇️ Download', ct,
                        f'{nopol}_{kuantum}.pdf', 'application/pdf',
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
        NOPOL <em>dan</em> KUANTUM harus sama persis di kedua file. Lihat diagnostik di atas untuk detail.
        </div>
        """, unsafe_allow_html=True)
