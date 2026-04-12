import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Surat Jalan",
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

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    background: #0d1117 !important;
    color: #e6edf3 !important;
}
.stApp { background: #0d1117 !important; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.app-header {
    background: linear-gradient(135deg, #161b22, #1c2128);
    border: 1px solid #30363d; border-radius: 12px;
    padding: 24px 28px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 14px;
}
.app-header .icon { font-size: 2rem; }
.app-header h1 { font-size: 1.5rem; font-weight: 700; color: #f0f6fc; margin: 0; }
.app-header p  { font-size: 0.8rem; color: #8b949e; margin: 3px 0 0; }

.upload-box {
    background: #161b22; border: 1.5px dashed #30363d;
    border-radius: 10px; padding: 16px 18px; margin-bottom: 12px;
}
.upload-box h4 {
    font-size: 0.75rem; font-weight: 600; color: #58a6ff;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;
}
.upload-box p { font-size: 0.75rem; color: #8b949e; margin: 0 0 8px; }

.stats-bar { display: flex; gap: 10px; margin: 14px 0; }
.stat-card {
    flex: 1; background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 12px 14px; text-align: center;
}
.stat-num { font-family: 'IBM Plex Mono', monospace; font-size: 1.7rem; font-weight: 600; line-height: 1; }
.stat-label { font-size: 0.68rem; color: #8b949e; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.5px; }
.num-blue { color: #58a6ff; } .num-green { color: #3fb950; }
.num-orange { color: #d29922; } .num-red { color: #f85149; }

.section-lbl {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.2px; color: #8b949e;
    display: flex; align-items: center; gap: 8px; margin: 18px 0 10px;
}
.section-lbl::after { content: ''; flex: 1; height: 1px; background: #21262d; }

.nopol-tag { font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.88rem; color: #f0f6fc; }
.kuantum-tag { font-size: 0.78rem; color: #8b949e; margin-top: 1px; }
.status-ok  { display:inline-flex;align-items:center;gap:4px;background:#1a3a2a;color:#3fb950;border:1px solid #3fb95033;padding:2px 8px;border-radius:20px;font-size:0.7rem;font-weight:600; }
.status-err { display:inline-flex;align-items:center;gap:4px;background:#3a1a1a;color:#f85149;border:1px solid #f8514933;padding:2px 8px;border-radius:20px;font-size:0.7rem;font-weight:600; }

.stButton > button {
    background: #21262d !important; color: #e6edf3 !important;
    border: 1px solid #30363d !important; border-radius: 7px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.78rem !important; padding: 5px 12px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #30363d !important; border-color: #58a6ff !important; color: #58a6ff !important;
}
.stDownloadButton > button {
    background: #1a3a2a !important; color: #3fb950 !important;
    border: 1px solid #3fb95044 !important; border-radius: 7px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.78rem !important; padding: 5px 12px !important;
}
.stProgress > div > div { background: #58a6ff !important; }
.stTextInput > div > div > input {
    background: #161b22 !important; border: 1px solid #30363d !important;
    color: #e6edf3 !important; border-radius: 8px !important;
}
.stCheckbox label { color: #c9d1d9 !important; font-size: 0.78rem !important; }
div[data-testid="stExpander"] { border: 1px solid #30363d !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CORE FUNCTIONS
# ─────────────────────────────────────────────

def normalize_nopol(v):
    if pd.isna(v): return ""
    return re.sub(r"\s+", "", str(v)).upper().strip()

def normalize_kuantum(v):
    try:
        cleaned = re.sub(r"[^\d.,]", "", str(v)).replace(",", ".")
        return float(cleaned)
    except Exception:
        return None

def extract_file_id(link):
    if not isinstance(link, str): return None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", link)
    if m: return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", link)
    if m: return m.group(1)
    return None

def is_valid_drive_link(link):
    return bool(extract_file_id(link))

def to_download_url(link):
    fid = extract_file_id(link)
    return f"https://drive.google.com/uc?export=download&id={fid}" if fid else None

def to_preview_url(link):
    fid = extract_file_id(link)
    return f"https://drive.google.com/file/d/{fid}/preview" if fid else None

def download_file(link, retries=3, timeout=30):
    dl_url = to_download_url(link)
    if not dl_url: return None
    session = requests.Session()
    for attempt in range(retries):
        try:
            resp = session.get(dl_url, timeout=timeout, allow_redirects=True)
            ct = resp.headers.get("Content-Type", "")
            if "text/html" in ct:
                tok = re.search(rb'name="confirm"\s+value="([^"]+)"', resp.content)
                if tok:
                    confirm = tok.group(1).decode()
                    resp = session.get(dl_url + f"&confirm={confirm}", timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 100:
                return resp.content
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
    return None

def safe_filename(nopol, kuantum, idx):
    clean = re.sub(r"[^\w]", "_", str(nopol))
    return f"{clean}_{kuantum}_{idx}.pdf"

def generate_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return buf.read()

def load_excel(f):
    try:
        return pd.read_excel(f, engine="openpyxl")
    except Exception:
        return pd.read_excel(f)

def detect_col(df, keywords):
    for c in df.columns:
        if any(k in c.lower() for k in keywords):
            return c
    return None

def prepare_database(df):
    df = df.copy()
    nopol_col   = detect_col(df, ["nopol","no pol","nomor pol","plat"])
    kuantum_col = detect_col(df, ["kuantum","quantum","qty","jumlah","volume"])
    link_col    = detect_col(df, ["link","url","surat","drive"])
    if not nopol_col:
        st.error(f"Kolom NOPOL tidak ditemukan di File 2. Kolom: {list(df.columns)}")
        return pd.DataFrame()
    if not link_col:
        st.error(f"Kolom LINK tidak ditemukan di File 2. Kolom: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out["NOPOL_RAW"] = df[nopol_col].astype(str)
    out["NOPOL"]     = df[nopol_col].apply(normalize_nopol)
    out["KUANTUM"]   = df[kuantum_col].apply(normalize_kuantum) if kuantum_col else None
    out["LINK"]      = df[link_col].astype(str)
    out["VALID_LINK"]= out["LINK"].apply(is_valid_drive_link)
    return out[out["NOPOL"] != ""].reset_index(drop=True)

def prepare_filter(df):
    df = df.copy()
    nopol_col   = detect_col(df, ["nopol","no pol","nomor pol","plat"])
    kuantum_col = detect_col(df, ["kuantum","quantum","qty","jumlah","volume"])
    if not nopol_col:
        st.error(f"Kolom NOPOL tidak ditemukan di File 1. Kolom: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out["NOPOL"]   = df[nopol_col].apply(normalize_nopol)
    out["KUANTUM"] = df[kuantum_col].apply(normalize_kuantum) if kuantum_col else None
    return out[out["NOPOL"] != ""].reset_index(drop=True)

def match_data(df_filter, df_db):
    """
    Priority:
    1. Match nopol + kuantum (exact)
    2. Fallback: match nopol only
    3. Last resort: return all db rows (if zero match)
    """
    # Attempt 1: nopol + kuantum
    if "KUANTUM" in df_filter.columns and df_filter["KUANTUM"].notna().any():
        m1 = pd.merge(df_filter, df_db, on=["NOPOL","KUANTUM"], how="inner")
        if len(m1) > 0:
            m1["MATCH_TYPE"] = "nopol+kuantum"
            return m1, "nopol+kuantum"

    # Attempt 2: nopol only
    m2 = pd.merge(df_filter[["NOPOL"]].drop_duplicates(), df_db, on="NOPOL", how="inner")
    if len(m2) > 0:
        m2["MATCH_TYPE"] = "nopol only"
        return m2, "nopol only"

    # Fallback: return all db
    df_db_copy = df_db.copy()
    df_db_copy["MATCH_TYPE"] = "no match — showing all db"
    return df_db_copy, "none"


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("result_df", None), ("active_preview", None), ("selected", set()), ("match_type","")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="icon">🚛</div>
  <div>
    <h1>Surat Jalan — Filter & Download</h1>
    <p>Upload file target + database → filter otomatis → preview & download per file atau semua sekaligus</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────
st.markdown('<div class="section-lbl">Upload File</div>', unsafe_allow_html=True)

col_u1, col_u2 = st.columns(2)
with col_u1:
    st.markdown("""<div class="upload-box">
        <h4>📋 File 1 — Target Filter</h4>
        <p>Kolom wajib: NOPOL, KUANTUM</p>
    </div>""", unsafe_allow_html=True)
    f1 = st.file_uploader("File 1", type=["xlsx","xls","csv"], key="uf1", label_visibility="collapsed")

with col_u2:
    st.markdown("""<div class="upload-box">
        <h4>🗄️ File 2 — Database Surat Jalan</h4>
        <p>Kolom wajib: NOPOL, KUANTUM, LINK (Google Drive)</p>
    </div>""", unsafe_allow_html=True)
    f2 = st.file_uploader("File 2", type=["xlsx","xls","csv"], key="uf2", label_visibility="collapsed")

col_btn, _ = st.columns([2, 8])
with col_btn:
    do_process = st.button("⚙️ Proses & Filter", use_container_width=True)

if do_process:
    if not f1 or not f2:
        st.warning("⚠️ Upload kedua file terlebih dahulu.")
    else:
        with st.spinner("Memproses..."):
            df_filter = prepare_filter(load_excel(f1))
            df_db     = prepare_database(load_excel(f2))
            if df_filter.empty or df_db.empty:
                st.stop()
            result, mtype = match_data(df_filter, df_db)
            st.session_state["result_df"]   = result.reset_index(drop=True)
            st.session_state["match_type"]  = mtype
            st.session_state["active_preview"] = None
            st.session_state["selected"]    = set()

        if mtype == "nopol+kuantum":
            st.success(f"✅ {len(result)} surat jalan cocok (filter: nopol + kuantum)")
        elif mtype == "nopol only":
            st.info(f"ℹ️ {len(result)} surat jalan cocok (filter: nopol saja — kuantum tidak match)")
        else:
            st.warning(
                f"⚠️ Tidak ada nopol yang cocok antara File 1 dan File 2.\n\n"
                f"**Sample NOPOL File 1:** {df_filter['NOPOL'].head(3).tolist()}\n\n"
                f"**Sample NOPOL File 2:** {df_db['NOPOL'].head(3).tolist()}\n\n"
                "Menampilkan **seluruh data File 2** sebagai gantinya."
            )


# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state["result_df"] is not None:
    df: pd.DataFrame = st.session_state["result_df"]

    valid_mask   = df["VALID_LINK"] == True if "VALID_LINK" in df.columns else pd.Series([True]*len(df))
    valid_count  = valid_mask.sum()
    invalid_count = (~valid_mask).sum()

    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-card"><div class="stat-num num-blue">{len(df)}</div><div class="stat-label">Total</div></div>
      <div class="stat-card"><div class="stat-num num-green">{valid_count}</div><div class="stat-label">Siap Download</div></div>
      <div class="stat-card"><div class="stat-num num-red">{invalid_count}</div><div class="stat-label">Link Invalid</div></div>
      <div class="stat-card"><div class="stat-num num-orange">{len(st.session_state['selected'])}</div><div class="stat-label">Dipilih</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bulk action buttons ────────────────
    st.markdown('<div class="section-lbl">Aksi Bulk</div>', unsafe_allow_html=True)
    ba1, ba2, ba3, ba4 = st.columns([2,2,2,4])
    with ba1:
        if st.button("☑️ Pilih Semua", use_container_width=True):
            st.session_state["selected"] = set(df[valid_mask].index.tolist())
            st.rerun()
    with ba2:
        if st.button("✖️ Hapus Pilihan", use_container_width=True):
            st.session_state["selected"] = set()
            st.rerun()
    with ba3:
        do_dl_all = st.button("📦 Download Semua ZIP", use_container_width=True)
    with ba4:
        do_dl_sel = st.button("⬇️ Download Terpilih ZIP", use_container_width=True)

    # ── Download All ───────────────────────
    if do_dl_all:
        target = df[valid_mask & df["LINK"].notna()]
        if len(target) == 0:
            st.warning("Tidak ada file valid.")
        else:
            prog = st.progress(0)
            stat = st.empty()
            ok, fail = {}, []

            def _dl(args):
                i, nopol, kuantum, link = args
                c = download_file(link)
                return safe_filename(nopol, kuantum, i), c, nopol

            items = [(i, r["NOPOL"], r.get("KUANTUM",""), r["LINK"])
                     for i, (_, r) in enumerate(target.iterrows())]

            with ThreadPoolExecutor(max_workers=15) as ex:
                futs = {ex.submit(_dl, item): item for item in items}
                done = 0
                for fut in as_completed(futs):
                    fname, content, nopol = fut.result()
                    (ok if content else fail).__setitem__(fname, content) if content else fail.append(nopol)
                    done += 1
                    prog.progress(done / len(items))
                    stat.markdown(f"⬇️ **{done}/{len(items)}** — ✅ {len(ok)} berhasil, ❌ {len(fail)} gagal")

            if ok:
                st.download_button(
                    f"💾 Simpan semua_surat_jalan.zip ({len(ok)} file, {len(generate_zip(ok))//1024} KB)",
                    data=generate_zip(ok), file_name="semua_surat_jalan.zip", mime="application/zip"
                )
            if fail:
                with st.expander(f"❌ {len(fail)} gagal"):
                    st.write(fail)

    # ── Download Selected ──────────────────
    if do_dl_sel:
        sel = st.session_state.get("selected", set())
        if not sel:
            st.warning("Pilih file terlebih dahulu dengan centang checkbox.")
        else:
            target_sel = df.loc[list(sel)]
            target_sel = target_sel[target_sel["VALID_LINK"] == True] if "VALID_LINK" in target_sel.columns else target_sel
            if len(target_sel) == 0:
                st.warning("File terpilih tidak memiliki link valid.")
            else:
                prog2 = st.progress(0)
                ok2, fail2 = {}, []
                items2 = [(i, r["NOPOL"], r.get("KUANTUM",""), r["LINK"])
                          for i,(_, r) in enumerate(target_sel.iterrows())]

                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs2 = {ex.submit(_dl, item): item for item in items2}
                    d2 = 0
                    for fut in as_completed(futs2):
                        fname, content, nopol = fut.result()
                        (ok2.__setitem__(fname, content) if content else fail2.append(nopol))
                        d2 += 1
                        prog2.progress(d2 / len(items2))

                if ok2:
                    st.download_button(
                        f"💾 Simpan terpilih_surat_jalan.zip ({len(ok2)} file)",
                        data=generate_zip(ok2), file_name="terpilih_surat_jalan.zip", mime="application/zip"
                    )

    # ── Search ────────────────────────────
    st.markdown('<div class="section-lbl">Daftar Surat Jalan</div>', unsafe_allow_html=True)
    search = st.text_input("🔍 Cari NOPOL...", placeholder="Filter berdasarkan nomor polisi...",
                            label_visibility="collapsed")
    display_df = df[df["NOPOL"].str.contains(search.upper(), na=False)] if search else df

    if len(display_df) == 0:
        st.info("Tidak ada data sesuai pencarian.")
    else:
        for _, row in display_df.iterrows():
            orig_idx = row.name
            nopol     = row.get("NOPOL", "—")
            nopol_raw = row.get("NOPOL_RAW", nopol)
            kuantum   = row.get("KUANTUM", "—")
            link      = str(row.get("LINK", ""))
            valid     = bool(row.get("VALID_LINK", False))

            kuantum_str = f"{kuantum:,.0f}" if isinstance(kuantum, float) else str(kuantum)

            c1, c2, c3, c4, c5 = st.columns([1, 4, 2, 2, 2])

            with c1:
                checked = orig_idx in st.session_state["selected"]
                if st.checkbox("", value=checked, key=f"c{orig_idx}", disabled=not valid):
                    st.session_state["selected"].add(orig_idx)
                else:
                    st.session_state["selected"].discard(orig_idx)

            with c2:
                st.markdown(
                    f'<div class="nopol-tag">{nopol_raw}</div>'
                    f'<div class="kuantum-tag">Kuantum: {kuantum_str}</div>',
                    unsafe_allow_html=True
                )

            with c3:
                if valid:
                    st.markdown('<span class="status-ok">✓ Valid</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="status-err">✗ Invalid</span>', unsafe_allow_html=True)

            with c4:
                if valid:
                    if st.button("👁️ Lihat", key=f"v{orig_idx}"):
                        st.session_state["active_preview"] = None if st.session_state["active_preview"] == orig_idx else orig_idx
                        st.rerun()
                else:
                    st.button("👁️ —", key=f"v{orig_idx}", disabled=True)

            with c5:
                if valid:
                    content = download_file(link)
                    if content:
                        st.download_button(
                            "⬇️ Unduh",
                            data=content,
                            file_name=safe_filename(nopol, kuantum, orig_idx),
                            mime="application/pdf",
                            key=f"d{orig_idx}",
                        )
                    else:
                        st.button("⬇️ Gagal", key=f"d{orig_idx}", disabled=True)
                else:
                    st.button("⬇️ —", key=f"d{orig_idx}", disabled=True)

            # Inline PDF preview
            if st.session_state["active_preview"] == orig_idx and valid:
                purl = to_preview_url(link)
                if purl:
                    components.html(
                        f'<iframe src="{purl}" width="100%" height="650" '
                        f'style="border:none;border-radius:8px;background:#fff;"></iframe>',
                        height=660, scrolling=False,
                    )

            st.divider()

    # ── Invalid links summary ─────────────
    if "VALID_LINK" in df.columns:
        inv = df[df["VALID_LINK"] == False]
        if len(inv) > 0:
            with st.expander(f"⚠️ {len(inv)} baris dengan link tidak valid"):
                show = [c for c in ["NOPOL_RAW","NOPOL","KUANTUM","LINK"] if c in inv.columns]
                st.dataframe(inv[show].reset_index(drop=True), use_container_width=True, hide_index=True)
