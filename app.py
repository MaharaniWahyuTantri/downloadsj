import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import streamlit.components.v1 as components
from typing import Optional, Tuple, List, Dict, Set
from collections import defaultdict
import hashlib

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Surat Jalan - Optimal",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS SAMA (dipertahankan untuk gaya)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background: #0d1117 !important;
    color: #e6edf3 !important;
}
.stApp { background: #0d1117 !important; }
.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

.app-header {
    background: linear-gradient(135deg,#161b22,#1c2128);
    border:1px solid #30363d; border-radius:12px;
    padding:22px 28px; margin-bottom:18px;
    display:flex; align-items:center; gap:14px;
}
.app-header .icon { font-size:2rem; }
.app-header h1 { font-size:1.45rem; font-weight:700; color:#f0f6fc; margin:0; }
.app-header p  { font-size:0.78rem; color:#8b949e; margin:3px 0 0; }

.stats-bar { display:flex;gap:10px;margin:12px 0; }
.stat-card {
    flex:1;background:#161b22;border:1px solid #30363d;
    border-radius:10px;padding:11px 14px;text-align:center;
}
.stat-num   { font-family:'IBM Plex Mono',monospace;font-size:1.65rem;font-weight:600;line-height:1; }
.stat-label { font-size:0.66rem;color:#8b949e;margin-top:3px;text-transform:uppercase;letter-spacing:0.5px; }
.num-blue   { color:#58a6ff; }
.num-green  { color:#3fb950; }
.num-orange { color:#d29922; }
.num-red    { color:#f85149; }

.section-lbl {
    font-size:0.68rem;text-transform:uppercase;letter-spacing:1.2px;color:#8b949e;
    display:flex;align-items:center;gap:8px;margin:16px 0 9px;
}
.section-lbl::after { content:'';flex:1;height:1px;background:#21262d; }

/* Buttons */
.stButton > button {
    background:#21262d !important;color:#e6edf3 !important;
    border:1px solid #30363d !important;border-radius:7px !important;
    font-family:'IBM Plex Sans',sans-serif !important;
    font-size:0.76rem !important;padding:5px 11px !important;
}
.stDownloadButton > button {
    background:#1a3a2a !important;color:#3fb950 !important;
    border:1px solid #3fb95044 !important;
}
.stProgress > div > div { background:#58a6ff !important; }
div[data-testid="stExpander"] { border:1px solid #30363d !important;border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  KONSTANTA & KONFIGURASI
# ─────────────────────────────────────────────
MAX_DOWNLOAD_WORKERS = 3          # Turun dari 15 -> 3 untuk menghindari rate limit
MAX_PREVIEW_WORKERS = 1            # Preview cukup 1 thread
CACHE_TTL_SECONDS = 3600           # Cache file selama 1 jam (per session)
REQUEST_TIMEOUT = 45               # Timeout lebih panjang
MAX_RETRIES = 3
PAGE_SIZE = 50                     # Pagination: baris per halaman

# ─────────────────────────────────────────────
#  FUNGSI UTILITY
# ─────────────────────────────────────────────
def normalize_nopol(v):
    if pd.isna(v):
        return ""
    return re.sub(r"\s+", "", str(v)).upper().strip()

def normalize_kuantum(v):
    """Lebih robust untuk format Indonesia / Eropa."""
    if pd.isna(v):
        return None
    s = str(v).strip()
    # Hapus semua titik (pemisah ribuan) dan ganti koma dengan titik
    s = re.sub(r"\.", "", s)
    s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return None

def detect_col(df, keywords, allow_fallback=True):
    """Deteksi kolom dengan fuzzy sederhana, kembalikan nama kolom atau None."""
    lower_cols = {c: c.lower() for c in df.columns}
    for c, cl in lower_cols.items():
        if any(k in cl for k in keywords):
            return c
    return None

def extract_file_id(link):
    if not isinstance(link, str):
        return None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", link)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", link)
    if m:
        return m.group(1)
    return None

def is_valid_link(link):
    return bool(extract_file_id(str(link) if link else ""))

def to_download_url(link):
    fid = extract_file_id(str(link) if link else "")
    return f"https://drive.google.com/uc?export=download&id={fid}" if fid else None

def to_preview_url(link):
    fid = extract_file_id(str(link) if link else "")
    return f"https://drive.google.com/file/d/{fid}/preview" if fid else None

def is_pdf_content(content: bytes) -> bool:
    """Cek magic bytes PDF: %PDF"""
    return content.startswith(b'%PDF')

@retry(stop=stop_after_attempt(MAX_RETRIES),
       wait=wait_exponential(multiplier=1, min=2, max=10),
       retry=retry_if_exception_type((requests.RequestException, ConnectionError)))
def download_file(link: str, timeout=REQUEST_TIMEOUT) -> Optional[bytes]:
    """Download dengan retry exponential backoff dan validasi PDF."""
    dl_url = to_download_url(link)
    if not dl_url:
        return None
    session = requests.Session()
    resp = session.get(dl_url, timeout=timeout, allow_redirects=True)
    ct = resp.headers.get("Content-Type", "")
    # Handle Google Drive confirmation page
    if "text/html" in ct:
        confirm_match = re.search(rb'name="confirm"\s+value="([^"]+)"', resp.content)
        if confirm_match:
            confirm = confirm_match.group(1).decode()
            resp = session.get(dl_url + f"&confirm={confirm}", timeout=timeout)
    if resp.status_code != 200:
        return None
    content = resp.content
    # Validasi konten: minimal 1KB dan harus PDF
    if len(content) < 1024 or not is_pdf_content(content):
        return None
    return content

def safe_filename(nopol: str, kuantum, idx: int) -> str:
    clean = re.sub(r"[^\w]", "_", str(nopol))
    return f"{clean}_{kuantum}_{idx}.pdf"

def generate_zip(files_dict: Dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files_dict.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return buf.read()

def load_file(f) -> pd.DataFrame:
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    try:
        return pd.read_excel(f, engine="openpyxl")
    except:
        return pd.read_excel(f)

# ─────────────────────────────────────────────
#  PREPARASI DATA DENGAN PILIHAN KOLOM MANUAL
# ─────────────────────────────────────────────
def prepare_filter(df: pd.DataFrame, manual_cols: dict) -> pd.DataFrame:
    """Gunakan kolom yang dipilih user, atau fallback ke deteksi."""
    nopol_col = manual_cols.get("nopol") or detect_col(df, ["nopol","no pol","plat"])
    kuantum_col = manual_cols.get("kuantum") or detect_col(df, ["kuantum","qty","volume"])
    if not nopol_col:
        st.error("Kolom NOPOL tidak ditemukan. Silakan pilih manual di sidebar.")
        return pd.DataFrame()
    out = pd.DataFrame()
    out["NOPOL_RAW"] = df[nopol_col].astype(str)
    out["NOPOL_KEY"] = out["NOPOL_RAW"].apply(normalize_nopol)
    if kuantum_col:
        out["KUANTUM_F1"] = df[kuantum_col].apply(normalize_kuantum)
    else:
        out["KUANTUM_F1"] = None
    return out[out["NOPOL_KEY"] != ""].drop_duplicates(subset=["NOPOL_KEY"]).reset_index(drop=True)

def prepare_database(df: pd.DataFrame, manual_cols: dict) -> Tuple[pd.DataFrame, str]:
    nopol_col = manual_cols.get("nopol") or detect_col(df, ["nopol","no pol","plat"])
    kuantum_col = manual_cols.get("kuantum") or detect_col(df, ["kuantum","qty","volume"])
    link_col = manual_cols.get("link") or detect_col(df, ["foto","link","url","drive"])
    if not nopol_col:
        st.error("Kolom NOPOL tidak ditemukan di database.")
        return pd.DataFrame(), ""
    if not link_col:
        st.error("Kolom LINK tidak ditemukan di database.")
        return pd.DataFrame(), ""
    out = pd.DataFrame()
    out["NOPOL_RAW"] = df[nopol_col].astype(str)
    out["NOPOL_KEY"] = out["NOPOL_RAW"].apply(normalize_nopol)
    if kuantum_col:
        out["KUANTUM"] = df[kuantum_col].apply(normalize_kuantum)
    else:
        out["KUANTUM"] = None
    out["LINK"] = df[link_col].astype(str)
    out["VALID_LINK"] = out["LINK"].apply(is_valid_link)
    return out[out["NOPOL_KEY"] != ""].reset_index(drop=True), link_col

def match_by_nopol(df_filter, df_db):
    matched = pd.merge(
        df_filter[["NOPOL_RAW","NOPOL_KEY","KUANTUM_F1"]],
        df_db,
        on="NOPOL_KEY",
        how="inner"
    )
    found_keys = set(matched["NOPOL_KEY"])
    not_found = df_filter[~df_filter["NOPOL_KEY"].isin(found_keys)].copy()
    return matched.reset_index(drop=True), not_found.reset_index(drop=True)

# ─────────────────────────────────────────────
#  CACHE DOWNLOAD MANAGER (per session)
# ─────────────────────────────────────────────
class DownloadCache:
    def __init__(self):
        self.cache = {}  # key: hash(link) -> bytes
    def get(self, link):
        key = hashlib.md5(link.encode()).hexdigest()
        return self.cache.get(key)
    def set(self, link, content):
        key = hashlib.md5(link.encode()).hexdigest()
        self.cache[key] = content
    def clear(self):
        self.cache.clear()

# Inisialisasi cache di session state
if "download_cache" not in st.session_state:
    st.session_state.download_cache = DownloadCache()

def download_with_cache(link):
    cached = st.session_state.download_cache.get(link)
    if cached is not None:
        return cached
    content = download_file(link)
    if content:
        st.session_state.download_cache.set(link, content)
    return content

# ─────────────────────────────────────────────
#  BATCH DOWNLOAD DENGAN PROGRESS & CONCURRENT TERBATAS
# ─────────────────────────────────────────────
def batch_download(items: List[Tuple[int, str, str, str]], max_workers=MAX_DOWNLOAD_WORKERS):
    """items: list of (idx, nopol_key, kuantum_str, link)"""
    results = {}  # idx -> (filename, content)
    fails = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(items)
    done = 0

    def worker(item):
        idx, nopol, kuantum, link = item
        content = download_with_cache(link)
        if content:
            fname = safe_filename(nopol, kuantum, idx)
            return idx, fname, content, None
        else:
            return idx, None, None, nopol

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(worker, item): item for item in items}
        for future in as_completed(futures):
            idx, fname, content, fail_nopol = future.result()
            if content:
                results[idx] = (fname, content)
            else:
                fails.append(fail_nopol)
            done += 1
            progress_bar.progress(done / total)
            status_text.markdown(f"⬇️ **{done}/{total}** — ✅ {len(results)} berhasil | ❌ {len(fails)} gagal")
    progress_bar.empty()
    status_text.empty()
    return results, fails

# ─────────────────────────────────────────────
#  RENDER DATA DENGAN DATA_EDITOR (optimal)
# ─────────────────────────────────────────────
def render_matched_data(matched: pd.DataFrame, page: int, search: str):
    """Tampilkan data dengan st.data_editor untuk seleksi massal."""
    # Filter search
    if search:
        display_df = matched[matched["NOPOL_KEY"].str.contains(search.upper().replace(" ", ""), na=False)]
    else:
        display_df = matched
    total_rows = len(display_df)
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_rows)
    page_df = display_df.iloc[start_idx:end_idx].copy()
    # Tambahkan kolom seleksi
    page_df["Pilih"] = False
    # Tampilkan data editor
    edited_df = st.data_editor(
        page_df,
        column_config={
            "Pilih": st.column_config.CheckboxColumn("Pilih", default=False),
            "LINK": st.column_config.LinkColumn("Link", display_text="Buka"),
            "VALID_LINK": st.column_config.CheckboxColumn("Valid?", disabled=True),
            "KUANTUM": st.column_config.NumberColumn("Kuantum (kg)", format="%.0f"),
            "KUANTUM_F1": st.column_config.NumberColumn("Target Kuantum", format="%.0f"),
        },
        hide_index=True,
        use_container_width=True,
        height=400,
        key=f"data_editor_{page}"
    )
    # Kembalikan baris yang dipilih
    selected_indices = edited_df[edited_df["Pilih"] == True].index.tolist()
    # Peta dari index asli (dalam display_df) ke index global di matched
    original_global_indices = page_df.index.tolist()
    selected_global = [original_global_indices[i] for i in selected_indices if i < len(original_global_indices)]
    return selected_global, total_rows

# ─────────────────────────────────────────────
#  SIDEBAR UNTUK KOLOM MANUAL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Pengaturan Kolom")
    st.markdown("Jika deteksi otomatis gagal, pilih manual:")
    col_nopol_f1 = st.selectbox("Kolom NOPOL (File 1)", options=["(Auto)"] + list(st.session_state.get("cols_f1", [])), key="col_nopol_f1")
    col_kuantum_f1 = st.selectbox("Kolom KUANTUM (File 1)", options=["(Auto)"] + list(st.session_state.get("cols_f1", [])), key="col_kuantum_f1")
    col_nopol_f2 = st.selectbox("Kolom NOPOL (File 2)", options=["(Auto)"] + list(st.session_state.get("cols_f2", [])), key="col_nopol_f2")
    col_kuantum_f2 = st.selectbox("Kolom KUANTUM (File 2)", options=["(Auto)"] + list(st.session_state.get("cols_f2", [])), key="col_kuantum_f2")
    col_link_f2 = st.selectbox("Kolom LINK (File 2)", options=["(Auto)"] + list(st.session_state.get("cols_f2", [])), key="col_link_f2")
    st.markdown("---")
    st.markdown("### 🚀 Optimasi")
    max_workers = st.slider("Max concurrent download", 1, 8, MAX_DOWNLOAD_WORKERS)
    st.caption("Nilai kecil lebih stabil, hindari rate limit Google Drive.")

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
st.markdown('<div class="app-header"><div class="icon">🚛</div><div><h1>Surat Jalan — Filter & Download (Optimized)</h1><p>Batch download dengan cache, paginasi, dan seleksi massal</p></div></div>', unsafe_allow_html=True)

# Upload file
col1, col2 = st.columns(2)
with col1:
    f1 = st.file_uploader("📋 File 1 - Target (Nopol dicari)", type=["xlsx","xls","csv"], key="f1")
with col2:
    f2 = st.file_uploader("🗄️ File 2 - Database Surat Jalan", type=["xlsx","xls","csv"], key="f2")

# Simpan nama kolom untuk sidebar
if f1:
    df1_sample = load_file(f1)
    st.session_state["cols_f1"] = list(df1_sample.columns)
if f2:
    df2_sample = load_file(f2)
    st.session_state["cols_f2"] = list(df2_sample.columns)

do_process = st.button("⚙️ Proses & Filter", type="primary", use_container_width=False)

if do_process:
    if not f1 or not f2:
        st.warning("Upload kedua file terlebih dahulu.")
    else:
        with st.spinner("Memproses data..."):
            df1 = load_file(f1)
            df2 = load_file(f2)
            manual_f1 = {}
            if col_nopol_f1 != "(Auto)": manual_f1["nopol"] = col_nopol_f1
            if col_kuantum_f1 != "(Auto)": manual_f1["kuantum"] = col_kuantum_f1
            manual_f2 = {}
            if col_nopol_f2 != "(Auto)": manual_f2["nopol"] = col_nopol_f2
            if col_kuantum_f2 != "(Auto)": manual_f2["kuantum"] = col_kuantum_f2
            if col_link_f2 != "(Auto)": manual_f2["link"] = col_link_f2

            df_filter = prepare_filter(df1, manual_f1)
            df_db, _ = prepare_database(df2, manual_f2)
            if df_filter.empty or df_db.empty:
                st.stop()
            matched, not_found = match_by_nopol(df_filter, df_db)
            st.session_state["matched_df"] = matched
            st.session_state["notfound_df"] = not_found
            st.session_state["page"] = 0
            # Bersihkan cache seleksi (kita gunakan data_editor langsung)
        total_nopol = df_filter["NOPOL_KEY"].nunique()
        found_nopol = matched["NOPOL_KEY"].nunique() if len(matched) else 0
        st.success(f"✅ {found_nopol}/{total_nopol} nopol ditemukan, total {len(matched)} surat jalan.")
        if len(not_found) > 0:
            st.info(f"ℹ️ {len(not_found)} nopol tidak ditemukan.")

# Tampilkan hasil jika ada
if "matched_df" in st.session_state and st.session_state["matched_df"] is not None:
    matched = st.session_state["matched_df"]
    not_found = st.session_state["notfound_df"]

    # Statistik
    total_trips = len(matched)
    valid_trips = matched["VALID_LINK"].sum()
    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-card"><div class="stat-num num-blue">{total_trips}</div><div class="stat-label">Total Surat Jalan</div></div>
      <div class="stat-card"><div class="stat-num num-green">{valid_trips}</div><div class="stat-label">Link Valid</div></div>
      <div class="stat-card"><div class="stat-num num-red">{total_trips - valid_trips}</div><div class="stat-label">Link Invalid</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Search
    search = st.text_input("🔍 Cari NOPOL", placeholder="Ketik nopol...", key="search_nopol")
    # Pagination
    page = st.session_state.get("page", 0)
    total_pages = (len(matched) + PAGE_SIZE - 1) // PAGE_SIZE if len(matched) > 0 else 1
    col_prev, col_page_info, col_next = st.columns([1,3,1])
    with col_prev:
        if st.button("◀ Sebelumnya", disabled=(page==0)):
            st.session_state["page"] = max(0, page-1)
            st.rerun()
    with col_page_info:
        st.markdown(f"<div style='text-align:center'>Halaman {page+1} dari {total_pages}</div>", unsafe_allow_html=True)
    with col_next:
        if st.button("Berikutnya ▶", disabled=(page>=total_pages-1)):
            st.session_state["page"] = min(total_pages-1, page+1)
            st.rerun()

    # Render data_editor
    selected_global, total_rows = render_matched_data(matched, page, search)
    st.caption(f"Menampilkan {min(PAGE_SIZE, total_rows)} dari {total_rows} baris (filtered).")

    # Tombol batch download
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if st.button("📦 Download Semua (Valid)", use_container_width=True):
            valid_items = [(idx, row["NOPOL_KEY"], row.get("KUANTUM",""), row["LINK"])
                           for idx, row in matched[matched["VALID_LINK"]==True].iterrows()]
            if not valid_items:
                st.warning("Tidak ada link valid.")
            else:
                results, fails = batch_download(valid_items, max_workers=max_workers)
                if results:
                    files_dict = {fname: content for _, (fname, content) in results.items()}
                    zip_data = generate_zip(files_dict)
                    st.download_button("💾 Simpan ZIP (Semua)", data=zip_data,
                                       file_name="semua_surat_jalan.zip", mime="application/zip")
                if fails:
                    st.warning(f"{len(fails)} file gagal: {', '.join(fails[:5])}{'...' if len(fails)>5 else ''}")
    with col_dl2:
        if st.button("⬇️ Download Terpilih", use_container_width=True):
            if not selected_global:
                st.warning("Pilih minimal satu baris dengan checklist.")
            else:
                selected_rows = matched.loc[selected_global]
                selected_rows = selected_rows[selected_rows["VALID_LINK"]==True]
                if selected_rows.empty:
                    st.warning("Tidak ada link valid dari pilihan.")
                else:
                    items = [(idx, row["NOPOL_KEY"], row.get("KUANTUM",""), row["LINK"])
                             for idx, row in selected_rows.iterrows()]
                    results, fails = batch_download(items, max_workers=max_workers)
                    if results:
                        files_dict = {fname: content for _, (fname, content) in results.items()}
                        zip_data = generate_zip(files_dict)
                        st.download_button("💾 Simpan ZIP (Terpilih)", data=zip_data,
                                           file_name="terpilih_surat_jalan.zip", mime="application/zip")
                    if fails:
                        st.error(f"Gagal download {len(fails)} file.")

    # Tampilkan daftar invalid link di expander
    invalid_df = matched[matched["VALID_LINK"]==False][["NOPOL_RAW","KUANTUM","LINK"]].drop_duplicates()
    if len(invalid_df) > 0:
        with st.expander(f"⚠️ {len(invalid_df)} surat jalan dengan link tidak valid"):
            st.dataframe(invalid_df, use_container_width=True, hide_index=True)

    # Not found
    if not_found is not None and len(not_found) > 0:
        with st.expander(f"❌ {len(not_found)} nopol tidak ditemukan di database"):
            st.dataframe(not_found[["NOPOL_RAW","KUANTUM_F1"]].rename(columns={"KUANTUM_F1":"Target Kuantum"}), use_container_width=True, hide_index=True)

    # Tombol reset cache
    if st.button("🗑️ Reset Cache Download", help="Hapus file PDF yang tersimpan sementara"):
        st.session_state.download_cache.clear()
        st.success("Cache dibersihkan.")
