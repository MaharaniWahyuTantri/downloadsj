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

# ── UTILITIES ──────────────────────────────────────────────────────────────────

def norm_nopol(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = str(v).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

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

def load_file2(raw_df):
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()
    first_row = df.iloc[0].tolist()
    has_header_row = any(str(v).upper().strip() in ['NOPOL', 'KUANTUM', 'FOTO SURAT JALAN'] for v in first_row)
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
          'active_preview', 'df2_debug', 'df1_debug']:
    if k not in st.session_state:
        st.session_state[k] = None

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div style="font-size:2.4rem">🚛</div>
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
            found = result[result['surat_jalan'].notna() & result['surat_jalan'].str.startswith('http', na=False)].copy().reset_index(drop=True)

            matched_f1_idx = set(found['_f1_idx'].tolist())
            missing_rows = []
            for idx, row1 in df1.iterrows():
                if idx not in matched_f1_idx:
                    missing_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum']})
            missing = pd.DataFrame(missing_rows).drop_duplicates(subset=['nopol','kuantum']).reset_index(drop=True)

            # Diagnostik detail
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
                        'NOPOL': row['nopol'],
                        'Kuantum File 1': int(row['kuantum']),
                        'Kuantum Tersedia di File 2': display,
                        'Status': '⚠️ Kuantum tidak cocok'
                    })
                else:
                    nopol_tidak_ada_rows.append({
                        'NOPOL': row['nopol'],
                        'Kuantum File 1': int(row['kuantum']),
                        'Status': '❌ NOPOL tidak ada di File 2'
                    })

            st.session_state.result_df     = found
            st.session_state.missing_df    = missing
            st.session_state.nopol_diff_df = pd.DataFrame(nopol_beda_k_rows)
            st.session_state.nopol_miss_df = pd.DataFrame(nopol_tidak_ada_rows)
            st.session_state.df2_debug     = df2
            st.session_state.df1_debug     = df1
            st.session_state.active_preview = None

            st.success(f'✅ Selesai! {len(found)} surat jalan ditemukan dari {len(df1)} data File 1.')

# ── RESULTS ────────────────────────────────────────────────────────────────────
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
    Satu pasang NOPOL+KUANTUM bisa menghasilkan <b>lebih dari satu surat jalan</b>.
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
            disp = disp[disp['nopol'].str.contains(re.escape(sn), na=False, case=False)].reset_index(drop=True)

        st.markdown(f'Menampilkan **{len(disp)}** dari **{len(found)}** surat jalan.')

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
                    make_zip(ok_files), 'surat_jalan_semua.zip', 'application/zip'
                )
            if fail_list:
                with st.expander(f'❌ {len(fail_list)} file gagal diunduh'):
                    st.write(fail_list)

        st.markdown('<div class="section-label">Detail per Surat Jalan</div>', unsafe_allow_html=True)
        hcols = st.columns([1, 3, 2, 2, 2])
        for col, lbl in zip(hcols, ['No.', 'NOPOL', 'KUANTUM', '👁 Lihat', '⬇ Download']):
            col.markdown(f'**{lbl}**')
        st.divider()

        for i, row in disp.iterrows():
            nopol   = row['nopol']
            kuantum = int(row['kuantum'])
            link    = row['surat_jalan']
            cols    = st.columns([1, 3, 2, 2, 2])
            cols[0].markdown(f'`#{i+1}`')
            cols[1].markdown(f'`{nopol}`')
            cols[2].markdown(f'**{kuantum:,}**')

            with cols[3]:
                if st.button('👁️ Lihat', key=f'v_{i}'):
                    st.session_state.active_preview = None if st.session_state.active_preview == i else i
            with cols[4]:
                ct = download_file(link)
                if ct:
                    st.download_button('⬇️ Download', ct, f'{nopol}_{kuantum}.pdf',
                                       'application/pdf', key=f'd_{i}')
                else:
                    st.button('⬇️ Gagal', key=f'df_{i}', disabled=True)

            if st.session_state.active_preview == i:
                purl = to_preview(link)
                if purl:
                    import streamlit.components.v1 as components
                    components.html(
                        f'<iframe src="{purl}" width="100%" height="680"'
                        f' style="border:1px solid #e2e8f0;border-radius:10px;background:#fff"></iframe>',
                        height=700
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
            💡 NOPOL ini <em>ada</em> di File 2, namun nilai KUANTUM yang tersedia berbeda dengan
            yang ada di File 1. Match hanya terjadi jika keduanya sama persis.
            </div>
            """, unsafe_allow_html=True)

            s_diff = st.text_input('', placeholder='🔍  Filter NOPOL di Tabel A...', label_visibility='collapsed', key='sd')
            d_diff = nopol_diff.copy()
            if s_diff.strip():
                sn = norm_nopol(s_diff.strip())
                d_diff = d_diff[d_diff['NOPOL'].str.contains(re.escape(sn), na=False, case=False)].reset_index(drop=True)

            st.dataframe(
                d_diff, use_container_width=True, hide_index=True,
                column_config={
                    'NOPOL': st.column_config.TextColumn('NOPOL', width='medium'),
                    'Kuantum File 1': st.column_config.NumberColumn('Kuantum File 1', format='%d'),
                    'Kuantum Tersedia di File 2': st.column_config.TextColumn('Kuantum Tersedia di File 2', width='large'),
                    'Status': st.column_config.TextColumn('Status', width='medium'),
                }
            )
            ca, _ = st.columns([2, 8])
            with ca:
                st.download_button(
                    '📥 Export Tabel A (.csv)',
                    d_diff.to_csv(index=False).encode('utf-8'),
                    'tabel_a_kuantum_beda.csv', 'text/csv', key='dl_a'
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

            s_miss = st.text_input('', placeholder='🔍  Filter NOPOL di Tabel B...', label_visibility='collapsed', key='sm')
            d_miss = nopol_miss.copy()
            if s_miss.strip():
                sn = norm_nopol(s_miss.strip())
                d_miss = d_miss[d_miss['NOPOL'].str.contains(re.escape(sn), na=False, case=False)].reset_index(drop=True)

            st.dataframe(
                d_miss, use_container_width=True, hide_index=True,
                column_config={
                    'NOPOL': st.column_config.TextColumn('NOPOL', width='medium'),
                    'Kuantum File 1': st.column_config.NumberColumn('Kuantum File 1', format='%d'),
                    'Status': st.column_config.TextColumn('Status', width='large'),
                }
            )
            cb2, _ = st.columns([2, 8])
            with cb2:
                st.download_button(
                    '📥 Export Tabel B (.csv)',
                    d_miss.to_csv(index=False).encode('utf-8'),
                    'tabel_b_nopol_tidak_ada.csv', 'text/csv', key='dl_b'
                )

        # ── Tabel C: Semua tidak match (gabungan) ─────────────────────────────
        with st.expander('📋 Tabel C — Semua data tidak match (gabungan)', expanded=False):
            all_miss = missing.copy()
            all_miss.columns = ['NOPOL', 'Kuantum File 1']
            all_miss['Kuantum File 1'] = all_miss['Kuantum File 1'].astype(int)

            s_all = st.text_input('', placeholder='🔍  Filter NOPOL...', label_visibility='collapsed', key='sa')
            if s_all.strip():
                sn = norm_nopol(s_all.strip())
                all_miss = all_miss[all_miss['NOPOL'].str.contains(re.escape(sn), na=False, case=False)].reset_index(drop=True)

            st.dataframe(all_miss, use_container_width=True, hide_index=True)

            cc, _ = st.columns([2, 8])
            with cc:
                st.download_button(
                    '📥 Export Tabel C (.csv)',
                    all_miss.to_csv(index=False).encode('utf-8'),
                    'tabel_c_semua_tidak_match.csv', 'text/csv', key='dl_c'
                )
