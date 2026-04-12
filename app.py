import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Surat Jalan Filter",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
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

/* Header */
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

/* Upload section */
.upload-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
}
.upload-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
}
.upload-card h3 {
    font-size: 0.85rem;
    font-weight: 600;
    color: #58a6ff;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.upload-card p { font-size: 0.8rem; color: #8b949e; margin-bottom: 12px; }

/* Summary cards */
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

/* Result card */
.result-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: border-color 0.2s;
}
.result-card:hover { border-color: #58a6ff44; }
.result-card.found { border-left: 3px solid #3fb950; }
.result-card.missing { border-left: 3px solid #f85149; opacity: 0.7; }

.rc-info { flex: 1; }
.rc-nopol {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1rem;
    font-weight: 600;
    color: #f0f6fc;
}
.rc-kuantum { font-size: 0.85rem; color: #8b949e; margin-top: 2px; }
.rc-status-found {
    display: inline-block;
    background: #1a3a2a;
    color: #3fb950;
    border: 1px solid #3fb95044;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 6px;
}
.rc-status-missing {
    display: inline-block;
    background: #3a1a1a;
    color: #f85149;
    border: 1px solid #f8514944;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 6px;
}

/* Search bar */
.search-wrap { margin: 16px 0; }

/* Divider */
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

/* Streamlit overrides */
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
.stCheckbox label { color: #c9d1d9 !important; font-size: 0.85rem !important; }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def normalize_nopol(val):
    if pd.isna(val):
        return ""
    return re.sub(r"\s+", "", str(val)).upper().strip()


def normalize_kuantum(val):
    try:
        return float(str(val).replace(",", ".").strip())
    except Exception:
        return None


def normalize_data(df: pd.DataFrame, has_link: bool = False) -> pd.DataFrame:
    df = df.copy()
    # Detect nopol column
    nopol_col = next((c for c in df.columns if "nopol" in c.lower() or "nomor polisi" in c.lower() or "no pol" in c.lower()), None)
    kuantum_col = next((c for c in df.columns if "kuantum" in c.lower() or "quantum" in c.lower()), None)
    link_col = next((c for c in df.columns if "link" in c.lower() or "url" in c.lower()), None) if has_link else None

    if not nopol_col or not kuantum_col:
        st.error(f"Kolom 'nopol' atau 'kuantum' tidak ditemukan. Kolom tersedia: {list(df.columns)}")
        return pd.DataFrame()

    df["_nopol"] = df[nopol_col].apply(normalize_nopol)
    df["_kuantum"] = df[kuantum_col].apply(normalize_kuantum)

    result = df[["_nopol", "_kuantum"]].rename(columns={"_nopol": "nopol", "_kuantum": "kuantum"})

    if has_link and link_col:
        result["link"] = df[link_col].values
    elif has_link:
        result["link"] = None

    return result.dropna(subset=["_nopol" if "_nopol" in result.columns else "nopol"])


def match_data(df_filter: pd.DataFrame, df_database: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(df_filter, df_database, on=["nopol", "kuantum"], how="left")
    return merged


def extract_file_id(link: str) -> str | None:
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


def convert_drive_download_link(link: str) -> str | None:
    fid = extract_file_id(link)
    if not fid:
        return None
    return f"https://drive.google.com/uc?export=download&id={fid}"


def convert_drive_preview_link(link: str) -> str | None:
    fid = extract_file_id(link)
    if not fid:
        return None
    return f"https://drive.google.com/file/d/{fid}/preview"


def download_file(url: str, retries: int = 3, timeout: int = 30) -> bytes | None:
    dl_url = convert_drive_download_link(url)
    if not dl_url:
        return None
    for attempt in range(retries):
        try:
            session = requests.Session()
            resp = session.get(dl_url, timeout=timeout, stream=True)
            # Handle Google Drive virus-scan warning page
            if "text/html" in resp.headers.get("Content-Type", ""):
                # Try to find confirm token
                token_match = re.search(r'name="confirm"\s+value="([^"]+)"', resp.text)
                if token_match:
                    confirm = token_match.group(1)
                    resp = session.get(dl_url + f"&confirm={confirm}", timeout=timeout, stream=True)
            if resp.status_code == 200:
                return resp.content
        except (requests.RequestException, Exception):
            if attempt < retries - 1:
                time.sleep(1)
    return None


def download_all_files(data_list: list, max_workers: int = 15) -> tuple[dict, list]:
    """Returns (dict of filename->bytes for success, list of failed nopols)"""
    results = {}
    failed = []

    def worker(item):
        idx, nopol, kuantum, link = item
        content = download_file(link)
        fname = f"{nopol}_{kuantum}_{idx}.pdf"
        return fname, content, nopol

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, item): item for item in data_list}
        for future in as_completed(futures):
            fname, content, nopol = future.result()
            if content:
                results[fname] = content
            else:
                failed.append(nopol)

    return results, failed


def generate_zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return buf.read()


def read_uploaded_file(f) -> pd.DataFrame:
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(f)
    else:
        st.error("Format file tidak didukung. Gunakan CSV atau Excel.")
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for key in ["result_df", "show_preview", "preview_url"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ─────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────

st.markdown("""
<div class="main-header">
  <div class="icon">🚛</div>
  <div>
    <h1>Surat Jalan Filter</h1>
    <p>Filter · Preview · Download — Google Drive Integration</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Upload Section ──────────────────────────
st.markdown('<div class="section-label">Upload File</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""<div class="upload-card">
        <h3>📋 File 1 — Filter Target</h3>
        <p>Berisi nopol & kuantum yang dicari (50–200 baris)</p>
    </div>""", unsafe_allow_html=True)
    file1 = st.file_uploader("Upload File 1", type=["csv", "xlsx", "xls"], key="f1", label_visibility="collapsed")

with col2:
    st.markdown("""<div class="upload-card">
        <h3>🗄️ File 2 — Database Mitra</h3>
        <p>Berisi nopol, kuantum & link Google Drive (500–1000 baris)</p>
    </div>""", unsafe_allow_html=True)
    file2 = st.file_uploader("Upload File 2", type=["csv", "xlsx", "xls"], key="f2", label_visibility="collapsed")

# ── Process Button ──────────────────────────
col_btn, col_reset = st.columns([2, 8])
with col_btn:
    process = st.button("⚙️ Proses Data", use_container_width=True)

if process:
    if not file1 or not file2:
        st.warning("Harap upload kedua file terlebih dahulu.")
    else:
        with st.spinner("Memproses data..."):
            df1_raw = read_uploaded_file(file1)
            df2_raw = read_uploaded_file(file2)

            if df1_raw.empty or df2_raw.empty:
                st.stop()

            df1 = normalize_data(df1_raw, has_link=False)
            df2 = normalize_data(df2_raw, has_link=True)

            if df1.empty or df2.empty:
                st.stop()

            result = match_data(df1, df2)
            st.session_state["result_df"] = result
            st.session_state["show_preview"] = None
            st.success("✅ Data berhasil diproses.")

# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state["result_df"] is not None:
    result: pd.DataFrame = st.session_state["result_df"]

    found = result[result["link"].notna()]
    missing = result[result["link"].isna()]

    # Summary
    st.markdown('<div class="section-label">Ringkasan</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="summary-grid">
      <div class="summary-card"><div class="num num-total">{len(result)}</div><div class="label">Total Data</div></div>
      <div class="summary-card"><div class="num num-found">{len(found)}</div><div class="label">Ditemukan</div></div>
      <div class="summary-card"><div class="num num-missing">{len(missing)}</div><div class="label">Tidak Ditemukan</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Search filter
    st.markdown('<div class="section-label">Hasil Filter</div>', unsafe_allow_html=True)
    search_q = st.text_input("🔍 Cari Nopol...", placeholder="Ketik nopol untuk filter...", label_visibility="collapsed")

    display_df = result.copy()
    if search_q:
        display_df = display_df[display_df["nopol"].str.contains(search_q.upper(), na=False)]

    # Bulk download
    if len(found) > 0:
        bulk_col1, bulk_col2 = st.columns([3, 7])
        with bulk_col1:
            do_bulk = st.button("📦 Download Semua (ZIP)", use_container_width=True)

        if do_bulk:
            valid = found[found["link"].notna()].copy()
            data_list = [(i, row["nopol"], row["kuantum"], row["link"]) for i, (_, row) in enumerate(valid.iterrows())]

            progress = st.progress(0)
            status_text = st.empty()
            status_text.text(f"Mengunduh 0 / {len(data_list)} file...")

            collected = {}
            failed_list = []
            completed = 0

            def worker_single(item):
                idx, nopol, kuantum, link = item
                content = download_file(link)
                fname = f"{nopol}_{kuantum}_{idx}.pdf"
                return fname, content, nopol

            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(worker_single, item): item for item in data_list}
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
                    file_name="surat_jalan.zip",
                    mime="application/zip",
                )

            if failed_list:
                with st.expander(f"❌ {len(failed_list)} file gagal diunduh"):
                    st.write(failed_list)

    # Preview toggle state
    if "active_preview" not in st.session_state:
        st.session_state["active_preview"] = None

    # Selected checkboxes
    if "selected_rows" not in st.session_state:
        st.session_state["selected_rows"] = set()

    # Selected download
    sel_col1, sel_col2 = st.columns([3, 7])
    with sel_col1:
        do_selected = st.button("☑️ Download Terpilih (ZIP)", use_container_width=True)

    # Render rows
    for i, row in display_df.iterrows():
        nopol = row["nopol"]
        kuantum = row["kuantum"]
        link = row.get("link", None)
        is_found = pd.notna(link) and link

        card_class = "result-card found" if is_found else "result-card missing"
        status_html = '<span class="rc-status-found">✓ Ditemukan</span>' if is_found else '<span class="rc-status-missing">✗ Tidak Ditemukan</span>'

        st.markdown(f"""
        <div class="{card_class}">
          <div class="rc-info">
            <div class="rc-nopol">{nopol}</div>
            <div class="rc-kuantum">Kuantum: {kuantum}</div>
            {status_html}
          </div>
        </div>
        """, unsafe_allow_html=True)

        if is_found:
            c1, c2, c3, _ = st.columns([1, 1, 1, 5])
            with c1:
                sel = st.checkbox("Pilih", key=f"sel_{i}", label_visibility="collapsed")
                if sel:
                    st.session_state["selected_rows"].add(i)
                else:
                    st.session_state["selected_rows"].discard(i)
            with c2:
                if st.button("👁️ View", key=f"view_{i}"):
                    if st.session_state["active_preview"] == i:
                        st.session_state["active_preview"] = None
                    else:
                        st.session_state["active_preview"] = i
            with c3:
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
                    st.button("⬇️ Gagal", key=f"dl_{i}_fail", disabled=True)

            if st.session_state["active_preview"] == i:
                preview_url = convert_drive_preview_link(link)
                if preview_url:
                    import streamlit.components.v1 as components
                    components.html(
                        f'<iframe src="{preview_url}" width="100%" height="600" style="border:none;border-radius:8px;"></iframe>',
                        height=620,
                    )
                else:
                    st.error("Link preview tidak valid.")
        else:
            st.write("")  # spacing

    # Download selected
    if do_selected:
        sel_indices = st.session_state.get("selected_rows", set())
        if not sel_indices:
            st.warning("Tidak ada file yang dipilih.")
        else:
            sel_data = [(j, display_df.loc[idx, "nopol"], display_df.loc[idx, "kuantum"], display_df.loc[idx, "link"])
                        for j, idx in enumerate(sel_indices) if pd.notna(display_df.loc[idx, "link"])]

            if sel_data:
                prog2 = st.progress(0)
                files2, fail2 = {}, []
                for k, item in enumerate(sel_data):
                    fname, content, nopol = f"{item[1]}_{item[2]}_{item[0]}.pdf", download_file(item[3]), item[1]
                    if content:
                        files2[fname] = content
                    else:
                        fail2.append(nopol)
                    prog2.progress((k + 1) / len(sel_data))

                if files2:
                    st.download_button(
                        label=f"💾 Simpan ZIP Terpilih ({len(files2)} file)",
                        data=generate_zip(files2),
                        file_name="surat_jalan_terpilih.zip",
                        mime="application/zip",
                    )
                if fail2:
                    st.warning(f"Gagal: {fail2}")

    # Missing data table
    if len(missing) > 0:
        with st.expander(f"⚠️ {len(missing)} data tidak ditemukan"):
            st.dataframe(
                missing[["nopol", "kuantum"]].rename(columns={"nopol": "Nopol", "kuantum": "Kuantum"}),
                use_container_width=True,
                hide_index=True,
            )
