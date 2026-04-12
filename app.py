import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="Surat Jalan Filter",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background: #0d1117;
    color: #e6edf3;
}

.stApp { background: #0d1117; }

.main-header {
    background: linear-gradient(135deg, #161b22 0%, #1c2128 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.main-header .icon { font-size: 2.4rem; }
.main-header h1 { font-size: 1.8rem; font-weight: 700; color: #f0f6fc; letter-spacing: -0.5px; }
.main-header p { font-size: 0.9rem; color: #8b949e; margin-top: 4px; }

.upload-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 8px;
}
.upload-card h3 {
    font-size: 0.85rem;
    font-weight: 600;
    color: #58a6ff;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.upload-card p { font-size: 0.8rem; color: #8b949e; margin-bottom: 0; }

.summary-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 20px 0;
}
.summary-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
}
.summary-card .num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
}
.summary-card .label { font-size: 0.78rem; color: #8b949e; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
.num-total { color: #58a6ff; }
.num-found { color: #3fb950; }
.num-missing { color: #f85149; }

.section-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #8b949e;
    margin: 24px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: #30363d; }

.stButton > button {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #30363d !important;
    border-color: #58a6ff !important;
    color: #58a6ff !important;
}
div[data-testid="stFileUploader"] {
    background: #0d1117;
    border: 1px dashed #30363d;
    border-radius: 8px;
}
.stProgress > div > div { background: #58a6ff !important; }
.stTextInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UTILITY
# ─────────────────────────────────────────────

def normalize_nopol(val):
    if pd.isna(val):
        return ""
    return re.sub(r"\s+", " ", str(val)).upper().strip()


def normalize_kuantum(val):
    try:
        return int(float(str(val).replace(",", ".").strip()))
    except Exception:
        return None


def extract_file_id(link):
    if not isinstance(link, str):
        return None
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, link)
        if m:
            return m.group(1)
    return None


def convert_drive_download_link(link):
    fid = extract_file_id(link)
    if not fid:
        return None
    return f"https://drive.google.com/uc?export=download&id={fid}"


def convert_drive_preview_link(link):
    fid = extract_file_id(link)
    if not fid:
        return None
    return f"https://drive.google.com/file/d/{fid}/preview"


def download_file(url, retries=3, timeout=30):
    dl_url = convert_drive_download_link(url)
    if not dl_url:
        return None
    for attempt in range(retries):
        try:
            session = requests.Session()
            resp = session.get(dl_url, timeout=timeout, stream=True)
            if "text/html" in resp.headers.get("Content-Type", ""):
                token_match = re.search(r'name="confirm"\s+value="([^"]+)"', resp.text)
                if token_match:
                    confirm = token_match.group(1)
                    resp = session.get(dl_url + f"&confirm={confirm}", timeout=timeout, stream=True)
            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None


def generate_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return buf.read()


def find_col(df, keywords):
    """Find column name by keywords (case-insensitive)."""
    for col in df.columns:
        if any(k.lower() in col.lower() for k in keywords):
            return col
    return None


def read_file(f):
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(f)
    else:
        st.error("Format file tidak didukung. Gunakan CSV atau Excel.")
        return pd.DataFrame()


def load_and_normalize(df, has_link=False):
    nopol_col = find_col(df, ["nopol", "nomor polisi", "no pol", "no. pol"])
    kuantum_col = find_col(df, ["kuantum", "quantum", "qty", "jumlah"])
    link_col = find_col(df, ["surat jalan", "link", "url", "drive", "gdrive"]) if has_link else None

    if not nopol_col:
        st.error(f"❌ Kolom NOPOL tidak ditemukan. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()
    if not kuantum_col:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    result = pd.DataFrame()
    result["nopol"] = df[nopol_col].apply(normalize_nopol)
    result["kuantum"] = df[kuantum_col].apply(normalize_kuantum)

    if has_link and link_col:
        result["link"] = df[link_col].values
    elif has_link:
        result["link"] = None

    result = result[result["nopol"] != ""]
    result = result.dropna(subset=["kuantum"])
    return result


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for key in ["result_df", "active_preview"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div class="icon">🚛</div>
  <div>
    <h1>Surat Jalan Filter</h1>
    <p>Match NOPOL &amp; KUANTUM → Preview &amp; Download Surat Jalan</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""<div class="upload-card">
        <h3>📋 File 1 — Data Target</h3>
        <p>Berisi NOPOL &amp; KUANTUM yang dicari</p>
    </div>""", unsafe_allow_html=True)
    file1 = st.file_uploader("Upload File 1", type=["csv", "xlsx", "xls"], key="f1", label_visibility="collapsed")

with col2:
    st.markdown("""<div class="upload-card">
        <h3>🗄️ File 2 — Database Surat Jalan</h3>
        <p>Berisi NOPOL, KUANTUM &amp; link Google Drive Surat Jalan</p>
    </div>""", unsafe_allow_html=True)
    file2 = st.file_uploader("Upload File 2", type=["csv", "xlsx", "xls"], key="f2", label_visibility="collapsed")

col_btn, _ = st.columns([2, 8])
with col_btn:
    process = st.button("⚙️ Proses Data", use_container_width=True)

# ─────────────────────────────────────────────
#  PROCESS
# ─────────────────────────────────────────────
if process:
    if not file1 or not file2:
        st.warning("⚠️ Harap upload kedua file terlebih dahulu.")
    else:
        with st.spinner("Memproses data..."):
            df1_raw = read_file(file1)
            df2_raw = read_file(file2)

            if df1_raw.empty or df2_raw.empty:
                st.stop()

            df1 = load_and_normalize(df1_raw, has_link=False)
            df2 = load_and_normalize(df2_raw, has_link=True)

            if df1.empty or df2.empty:
                st.stop()

            # Match on NOPOL + KUANTUM (both must match)
            result = pd.merge(df1, df2, on=["nopol", "kuantum"], how="left")
            st.session_state["result_df"] = result
            st.session_state["active_preview"] = None
            st.success(f"✅ Data berhasil diproses. {len(result)} baris dari File 1 dicocokkan.")

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state["result_df"] is not None:
    result: pd.DataFrame = st.session_state["result_df"]

    found = result[result["link"].notna() & (result["link"].astype(str).str.strip() != "")]
    missing = result[~result.index.isin(found.index)]

    # Summary
    st.markdown('<div class="section-label">Ringkasan</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="summary-grid">
      <div class="summary-card"><div class="num num-total">{len(result)}</div><div class="label">Total Data</div></div>
      <div class="summary-card"><div class="num num-found">{len(found)}</div><div class="label">Ditemukan</div></div>
      <div class="summary-card"><div class="num num-missing">{len(missing)}</div><div class="label">Tidak Ditemukan</div></div>
    </div>
    """, unsafe_allow_html=True)

    if len(found) == 0:
        st.warning("""
        ⚠️ **Tidak ada data yang cocok.**
        
        Pastikan NOPOL dan KUANTUM di File 1 **sama persis** dengan File 2 (nilai harus identik di kedua kolom).
        """)

        with st.expander("🔍 Debug: Lihat data yang diproses"):
            c1, c2 = st.columns(2)
            with c1:
                st.write("**File 1 (setelah normalisasi):**")
                st.dataframe(result[["nopol","kuantum"]], use_container_width=True, hide_index=True)
            with c2:
                st.write("**File 2 (setelah normalisasi):**")
                df2_norm = load_and_normalize(read_file(st.session_state.get("f2_cache", file2) if False else
                    __import__('io').BytesIO()), has_link=True) if False else None
                st.info("Upload ulang untuk melihat debug File 2")
        st.stop()

    # Search filter
    st.markdown('<div class="section-label">Hasil Match — Surat Jalan</div>', unsafe_allow_html=True)
    search_q = st.text_input("🔍 Cari Nopol...", placeholder="Ketik nopol untuk filter...", label_visibility="collapsed")

    display_df = found.copy().reset_index(drop=True)
    if search_q:
        display_df = display_df[display_df["nopol"].str.contains(search_q.strip().upper(), na=False)]

    # ── BULK DOWNLOAD BUTTON ──
    bulk_col, _ = st.columns([3, 7])
    with bulk_col:
        do_bulk = st.button("📦 Download Semua (ZIP)", use_container_width=True)

    if do_bulk:
        data_list = [(i, row["nopol"], row["kuantum"], row["link"]) for i, row in display_df.iterrows()]
        progress = st.progress(0)
        status_text = st.empty()
        collected = {}
        failed_list = []
        completed = 0
        status_text.text(f"Mengunduh 0 / {len(data_list)} file...")

        def worker(item):
            idx, nopol, kuantum, link = item
            content = download_file(link)
            fname = f"{nopol}_{kuantum}.pdf"
            return fname, content, nopol

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(worker, item): item for item in data_list}
            for future in as_completed(futures):
                fname, content, nopol = future.result()
                if content:
                    collected[fname] = content
                else:
                    failed_list.append(nopol)
                completed += 1
                progress.progress(completed / len(data_list))
                status_text.text(f"Mengunduh {completed} / {len(data_list)} file...")

        status_text.text(f"✅ Berhasil: {len(collected)} | ❌ Gagal: {len(failed_list)}")

        if collected:
            zip_bytes = generate_zip(collected)
            st.download_button(
                label=f"💾 Simpan ZIP ({len(collected)} file)",
                data=zip_bytes,
                file_name="surat_jalan_semua.zip",
                mime="application/zip",
            )
        if failed_list:
            with st.expander(f"❌ {len(failed_list)} file gagal diunduh"):
                st.write(failed_list)

    # ── TABLE WITH INDIVIDUAL BUTTONS ──
    st.markdown(f"**{len(display_df)} surat jalan ditemukan:**")

    # Table header
    hc = st.columns([2, 2, 2, 2, 1])
    hc[0].markdown("**NOPOL**")
    hc[1].markdown("**KUANTUM**")
    hc[2].markdown("**Lihat Surat Jalan**")
    hc[3].markdown("**Download**")
    hc[4].markdown("**No.**")
    st.divider()

    for i, row in display_df.iterrows():
        nopol = row["nopol"]
        kuantum = row["kuantum"]
        link = row["link"]

        cols = st.columns([2, 2, 2, 2, 1])
        cols[0].markdown(f"`{nopol}`")
        cols[1].markdown(f"{int(kuantum):,}")
        cols[4].markdown(f"#{i+1}")

        with cols[2]:
            if st.button("👁️ Lihat", key=f"view_{i}"):
                if st.session_state["active_preview"] == i:
                    st.session_state["active_preview"] = None
                else:
                    st.session_state["active_preview"] = i

        with cols[3]:
            content = download_file(link)
            if content:
                st.download_button(
                    label="⬇️ Download",
                    data=content,
                    file_name=f"{nopol}_{kuantum}.pdf",
                    mime="application/pdf",
                    key=f"dl_{i}",
                )
            else:
                st.button("⬇️ Gagal", key=f"dl_fail_{i}", disabled=True)

        # Preview iframe (show below the row)
        if st.session_state["active_preview"] == i:
            preview_url = convert_drive_preview_link(link)
            if preview_url:
                import streamlit.components.v1 as components
                components.html(
                    f'<iframe src="{preview_url}" width="100%" height="650" style="border:1px solid #30363d;border-radius:8px;"></iframe>',
                    height=670,
                )
            else:
                st.error("Link preview tidak valid.")

    # ── MISSING DATA ──
    if len(missing) > 0:
        with st.expander(f"⚠️ {len(missing)} data dari File 1 tidak ditemukan di File 2"):
            st.dataframe(
                missing[["nopol", "kuantum"]].rename(columns={"nopol": "NOPOL", "kuantum": "KUANTUM"}),
                use_container_width=True,
                hide_index=True,
            )
