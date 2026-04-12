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
#  CSS
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

.upload-box {
    background:#161b22; border:1.5px dashed #30363d;
    border-radius:10px; padding:14px 16px; margin-bottom:10px;
}
.upload-box h4 { font-size:0.73rem;font-weight:600;color:#58a6ff;text-transform:uppercase;letter-spacing:1px;margin-bottom:3px; }
.upload-box p  { font-size:0.73rem;color:#8b949e;margin:0 0 6px; }

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

/* Nopol group header */
.nopol-group {
    background:#1c2128;border:1px solid #30363d;
    border-radius:9px 9px 0 0;padding:10px 16px;
    display:flex;align-items:center;gap:10px;margin-top:14px;
}
.nopol-group .np-tag {
    font-family:'IBM Plex Mono',monospace;font-weight:700;
    font-size:1rem;color:#f0f6fc;
}
.nopol-group .np-kuantum { font-size:0.78rem;color:#8b949e;margin-left:4px; }
.badge-count {
    background:#21262d;border:1px solid #30363d;
    color:#8b949e;font-size:0.68rem;font-weight:600;
    padding:2px 8px;border-radius:12px;
}
.badge-notfound {
    background:#3a1a1a;border:1px solid #f8514933;
    color:#f85149;font-size:0.68rem;font-weight:600;
    padding:2px 8px;border-radius:12px;
}

/* Trip row */
.trip-row {
    background:#161b22;border:1px solid #30363d;border-top:none;
    padding:10px 16px;
}
.trip-row:last-child { border-radius:0 0 9px 9px; }
.trip-row:hover { background:#1a1f28; }
.kuantum-badge {
    font-family:'IBM Plex Mono',monospace;font-size:0.82rem;
    color:#c9d1d9;background:#21262d;border:1px solid #30363d;
    padding:2px 9px;border-radius:6px;
}
.status-ok  { display:inline-flex;align-items:center;gap:3px;background:#1a3a2a;color:#3fb950;border:1px solid #3fb95033;padding:2px 8px;border-radius:20px;font-size:0.68rem;font-weight:600; }
.status-err { display:inline-flex;align-items:center;gap:3px;background:#3a1a1a;color:#f85149;border:1px solid #f8514933;padding:2px 8px;border-radius:20px;font-size:0.68rem;font-weight:600; }

/* Buttons */
.stButton > button {
    background:#21262d !important;color:#e6edf3 !important;
    border:1px solid #30363d !important;border-radius:7px !important;
    font-family:'IBM Plex Sans',sans-serif !important;
    font-size:0.76rem !important;padding:5px 11px !important;
    transition:all 0.15s !important;
}
.stButton > button:hover {
    background:#30363d !important;border-color:#58a6ff !important;color:#58a6ff !important;
}
.stDownloadButton > button {
    background:#1a3a2a !important;color:#3fb950 !important;
    border:1px solid #3fb95044 !important;border-radius:7px !important;
    font-family:'IBM Plex Sans',sans-serif !important;
    font-size:0.76rem !important;padding:5px 11px !important;
}
.stProgress > div > div { background:#58a6ff !important; }
.stTextInput > div > div > input {
    background:#161b22 !important;border:1px solid #30363d !important;
    color:#e6edf3 !important;border-radius:8px !important;
    font-family:'IBM Plex Sans',sans-serif !important;
}
.stCheckbox label { color:#c9d1d9 !important;font-size:0.78rem !important; }
div[data-testid="stExpander"] { border:1px solid #30363d !important;border-radius:8px !important; }
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

def detect_col(df, keywords):
    """Find column by keyword match (case-insensitive)."""
    for c in df.columns:
        cl = c.lower()
        if any(k in cl for k in keywords):
            return c
    return None

def extract_file_id(link):
    if not isinstance(link, str): return None
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", link)
    if m: return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", link)
    if m: return m.group(1)
    return None

def is_valid_link(link):
    return bool(extract_file_id(str(link) if link else ""))

def to_download_url(link):
    fid = extract_file_id(str(link) if link else "")
    return f"https://drive.google.com/uc?export=download&id={fid}" if fid else None

def to_preview_url(link):
    fid = extract_file_id(str(link) if link else "")
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
            if resp.status_code == 200 and len(resp.content) > 500:
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

def load_file(f):
    name = f.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(f)
    try:
        return pd.read_excel(f, engine="openpyxl")
    except Exception:
        return pd.read_excel(f)

def prepare_filter(df):
    """Extract and normalize nopol list from File 1."""
    df = df.copy()
    nopol_col = detect_col(df, ["nopol","no pol","nomor pol","plat","kendaraan"])
    kuantum_col = detect_col(df, ["kuantum","quantum","qty","jumlah","volume","tonase"])
    if not nopol_col:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 1. Kolom: {list(df.columns)}")
        return pd.DataFrame()
    out = pd.DataFrame()
    out["NOPOL_RAW"] = df[nopol_col].astype(str)
    out["NOPOL_KEY"] = df[nopol_col].apply(normalize_nopol)
    out["KUANTUM_F1"] = df[kuantum_col].apply(normalize_kuantum) if kuantum_col else None
    return out[out["NOPOL_KEY"] != ""].drop_duplicates(subset=["NOPOL_KEY"]).reset_index(drop=True)

def prepare_database(df):
    """Extract and normalize database from File 2."""
    df = df.copy()
    nopol_col   = detect_col(df, ["nopol","no pol","nomor pol","plat","kendaraan"])
    kuantum_col = detect_col(df, ["kuantum","quantum","qty","jumlah","volume","tonase"])
    link_col    = detect_col(df, ["foto","link","url","surat","drive","file","gambar"])
    if not nopol_col:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 2. Kolom: {list(df.columns)}")
        return pd.DataFrame(), ""
    if not link_col:
        st.error(f"❌ Kolom LINK/FOTO tidak ditemukan di File 2. Kolom: {list(df.columns)}")
        return pd.DataFrame(), ""
    out = pd.DataFrame()
    out["NOPOL_RAW"] = df[nopol_col].astype(str)
    out["NOPOL_KEY"] = df[nopol_col].apply(normalize_nopol)
    out["KUANTUM"]   = df[kuantum_col].apply(normalize_kuantum) if kuantum_col else None
    out["LINK"]      = df[link_col].astype(str)
    out["VALID_LINK"]= out["LINK"].apply(is_valid_link)
    out = out[out["NOPOL_KEY"] != ""].reset_index(drop=True)
    return out, link_col

def match_by_nopol(df_filter, df_db):
    """
    Match File1 against File2 by NOPOL only.
    Returns: (matched_df, not_found_list)
    """
    matched = pd.merge(
        df_filter[["NOPOL_RAW","NOPOL_KEY","KUANTUM_F1"]],
        df_db,
        on="NOPOL_KEY",
        how="inner"
    )
    found_keys = set(matched["NOPOL_KEY"].unique())
    not_found  = df_filter[~df_filter["NOPOL_KEY"].isin(found_keys)].copy()
    return matched.reset_index(drop=True), not_found.reset_index(drop=True)


# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
for k, v in [
    ("matched_df", None), ("notfound_df", None),
    ("active_preview", None), ("selected", set()),
]:
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
    <p>Filter berdasarkan NOPOL · Preview PDF · Download per file atau ZIP semua sekaligus</p>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────
st.markdown('<div class="section-lbl">Upload File</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("""<div class="upload-box">
        <h4>📋 File 1 — Target (Nopol yang dicari)</h4>
        <p>Kolom: NOPOL, KUANTUM</p>
    </div>""", unsafe_allow_html=True)
    f1 = st.file_uploader("File 1", type=["xlsx","xls","csv"], key="uf1", label_visibility="collapsed")
with c2:
    st.markdown("""<div class="upload-box">
        <h4>🗄️ File 2 — Database Surat Jalan</h4>
        <p>Kolom: NOPOL, KUANTUM, LINK/FOTO Google Drive</p>
    </div>""", unsafe_allow_html=True)
    f2 = st.file_uploader("File 2", type=["xlsx","xls","csv"], key="uf2", label_visibility="collapsed")

col_btn, _ = st.columns([2.5, 7.5])
with col_btn:
    do_process = st.button("⚙️ Proses & Filter", use_container_width=True)

if do_process:
    if not f1 or not f2:
        st.warning("⚠️ Upload kedua file terlebih dahulu.")
    else:
        with st.spinner("Memproses data..."):
            df_filter         = prepare_filter(load_file(f1))
            df_db, _link_col  = prepare_database(load_file(f2))

            if df_filter.empty or df_db.empty:
                st.stop()

            matched, not_found = match_by_nopol(df_filter, df_db)

            st.session_state["matched_df"]    = matched
            st.session_state["notfound_df"]   = not_found
            st.session_state["active_preview"] = None
            st.session_state["selected"]       = set()

        total_nopol   = df_filter["NOPOL_KEY"].nunique()
        found_nopol   = matched["NOPOL_KEY"].nunique() if len(matched) else 0
        total_trips   = len(matched)
        valid_trips   = matched["VALID_LINK"].sum() if len(matched) else 0

        st.success(
            f"✅ **{found_nopol}/{total_nopol}** nopol ditemukan → "
            f"**{total_trips}** surat jalan ({valid_trips} link valid)"
        )
        if len(not_found) > 0:
            st.info(f"ℹ️ {len(not_found)} nopol tidak ditemukan di database")


# ─────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────
if st.session_state["matched_df"] is not None:
    matched: pd.DataFrame = st.session_state["matched_df"]
    not_found: pd.DataFrame = st.session_state["notfound_df"]

    total_nopols  = matched["NOPOL_KEY"].nunique()
    total_trips   = len(matched)
    valid_trips   = int(matched["VALID_LINK"].sum())
    invalid_trips = total_trips - valid_trips
    selected_cnt  = len(st.session_state["selected"])

    # Stats
    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-card"><div class="stat-num num-blue">{total_nopols}</div><div class="stat-label">Nopol Match</div></div>
      <div class="stat-card"><div class="stat-num num-blue">{total_trips}</div><div class="stat-label">Total Surat Jalan</div></div>
      <div class="stat-card"><div class="stat-num num-green">{valid_trips}</div><div class="stat-label">Link Valid</div></div>
      <div class="stat-card"><div class="stat-num num-red">{invalid_trips}</div><div class="stat-label">Link Invalid</div></div>
      <div class="stat-card"><div class="stat-num num-orange">{selected_cnt}</div><div class="stat-label">Dipilih</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Bulk actions ───────────────────────
    st.markdown('<div class="section-lbl">Aksi Bulk</div>', unsafe_allow_html=True)
    ba1, ba2, ba3, ba4 = st.columns([2,2,2.5,2.5])
    with ba1:
        if st.button("☑️ Pilih Semua", use_container_width=True):
            valid_idx = matched[matched["VALID_LINK"] == True].index.tolist()
            st.session_state["selected"] = set(valid_idx)
            st.rerun()
    with ba2:
        if st.button("✖️ Hapus Pilihan", use_container_width=True):
            st.session_state["selected"] = set()
            st.rerun()
    with ba3:
        do_dl_all = st.button("📦 Download Semua (ZIP)", use_container_width=True)
    with ba4:
        do_dl_sel = st.button("⬇️ Download Terpilih (ZIP)", use_container_width=True)

    # ── Download ALL ───────────────────────
    if do_dl_all:
        target = matched[matched["VALID_LINK"] == True]
        if len(target) == 0:
            st.warning("Tidak ada link valid untuk diunduh.")
        else:
            prog = st.progress(0)
            stat_txt = st.empty()
            ok_files, fail_list = {}, []

            def _worker(args):
                i, nopol, kuantum, link = args
                content = download_file(link)
                return safe_filename(nopol, kuantum, i), content, nopol

            items = [
                (i, row["NOPOL_KEY"], row.get("KUANTUM",""), row["LINK"])
                for i, (_, row) in enumerate(target.iterrows())
            ]
            with ThreadPoolExecutor(max_workers=15) as ex:
                futs = {ex.submit(_worker, item): item for item in items}
                done = 0
                for fut in as_completed(futs):
                    fname, content, nopol = fut.result()
                    if content:
                        ok_files[fname] = content
                    else:
                        fail_list.append(nopol)
                    done += 1
                    prog.progress(done / len(items))
                    stat_txt.markdown(
                        f"⬇️ **{done}/{len(items)}** — ✅ {len(ok_files)} berhasil | ❌ {len(fail_list)} gagal"
                    )

            if ok_files:
                zb = generate_zip(ok_files)
                st.download_button(
                    f"💾 Simpan ZIP — {len(ok_files)} file ({len(zb)//1024} KB)",
                    data=zb, file_name="semua_surat_jalan.zip", mime="application/zip"
                )
            if fail_list:
                with st.expander(f"❌ {len(fail_list)} file gagal diunduh"):
                    st.write(fail_list)

    # ── Download SELECTED ──────────────────
    if do_dl_sel:
        sel = st.session_state.get("selected", set())
        if not sel:
            st.warning("Pilih baris terlebih dahulu dengan mencentang checkbox.")
        else:
            target_sel = matched.loc[list(sel)]
            target_sel = target_sel[target_sel["VALID_LINK"] == True]
            if len(target_sel) == 0:
                st.warning("Tidak ada link valid dari baris yang dipilih.")
            else:
                prog2 = st.progress(0)
                ok2, fail2 = {}, []
                items2 = [
                    (i, row["NOPOL_KEY"], row.get("KUANTUM",""), row["LINK"])
                    for i, (_, row) in enumerate(target_sel.iterrows())
                ]
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs2 = {ex.submit(_worker, item): item for item in items2}
                    d2 = 0
                    for fut in as_completed(futs2):
                        fname, content, nopol = fut.result()
                        if content: ok2[fname] = content
                        else: fail2.append(nopol)
                        d2 += 1
                        prog2.progress(d2 / len(items2))
                if ok2:
                    zb2 = generate_zip(ok2)
                    st.download_button(
                        f"💾 Simpan ZIP terpilih — {len(ok2)} file",
                        data=zb2, file_name="terpilih_surat_jalan.zip", mime="application/zip"
                    )

    # ── Search ────────────────────────────
    st.markdown('<div class="section-lbl">Daftar Surat Jalan per Nopol</div>', unsafe_allow_html=True)
    search = st.text_input(
        "🔍 Cari NOPOL...", placeholder="Ketik nomor polisi untuk filter...",
        label_visibility="collapsed"
    )

    # Group by NOPOL_KEY
    if search:
        display_df = matched[matched["NOPOL_KEY"].str.contains(search.upper().replace(" ",""), na=False)]
    else:
        display_df = matched

    if len(display_df) == 0:
        st.info("Tidak ada data sesuai pencarian.")
    else:
        grouped = display_df.groupby("NOPOL_KEY", sort=False)

        for nopol_key, group in grouped:
            group = group.reset_index()  # preserve orig index in 'index' col
            nopol_raw  = group.iloc[0]["NOPOL_RAW"]
            kuantum_f1 = group.iloc[0].get("KUANTUM_F1", None)
            trip_count = len(group)
            valid_count_g = int(group["VALID_LINK"].sum())

            k_display = f"{int(kuantum_f1):,}" if isinstance(kuantum_f1, float) and not pd.isna(kuantum_f1) else "—"

            # Nopol group header
            st.markdown(f"""
            <div class="nopol-group">
              <span class="np-tag">{nopol_raw}</span>
              <span class="np-kuantum">Target kuantum: {k_display}</span>
              <span class="badge-count">{trip_count} surat jalan</span>
            </div>
            """, unsafe_allow_html=True)

            # Trip rows
            for _, row in group.iterrows():
                orig_idx  = row["index"]
                kuantum   = row.get("KUANTUM", None)
                link      = str(row.get("LINK",""))
                valid     = bool(row.get("VALID_LINK", False))
                k_str     = f"{int(kuantum):,}" if isinstance(kuantum, float) and not pd.isna(kuantum) else str(kuantum)

                st.markdown('<div class="trip-row">', unsafe_allow_html=True)

                c_chk, c_kuantum, c_status, c_view, c_dl = st.columns([1, 3, 2, 2, 2])

                with c_chk:
                    checked = orig_idx in st.session_state["selected"]
                    new_val = st.checkbox("", value=checked, key=f"chk_{orig_idx}", disabled=not valid)
                    if new_val:
                        st.session_state["selected"].add(orig_idx)
                    elif orig_idx in st.session_state["selected"]:
                        st.session_state["selected"].discard(orig_idx)

                with c_kuantum:
                    st.markdown(f'<span class="kuantum-badge">⚖️ {k_str} kg</span>', unsafe_allow_html=True)

                with c_status:
                    if valid:
                        st.markdown('<span class="status-ok">✓ Valid</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-err">✗ Invalid</span>', unsafe_allow_html=True)

                with c_view:
                    if valid:
                        if st.button("👁️ Lihat", key=f"view_{orig_idx}"):
                            st.session_state["active_preview"] = (
                                None if st.session_state["active_preview"] == orig_idx else orig_idx
                            )
                            st.rerun()
                    else:
                        st.button("👁️ —", key=f"view_{orig_idx}", disabled=True)

                with c_dl:
                    if valid:
                        content = download_file(link)
                        if content:
                            st.download_button(
                                "⬇️ Unduh",
                                data=content,
                                file_name=safe_filename(nopol_key, k_str.replace(",",""), orig_idx),
                                mime="application/pdf",
                                key=f"dl_{orig_idx}",
                            )
                        else:
                            st.button("⬇️ Gagal", key=f"dl_{orig_idx}", disabled=True)
                    else:
                        st.button("⬇️ —", key=f"dl_{orig_idx}", disabled=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # Inline PDF preview
                if st.session_state["active_preview"] == orig_idx and valid:
                    purl = to_preview_url(link)
                    if purl:
                        components.html(
                            f'<iframe src="{purl}" width="100%" height="660" '
                            f'style="border:none;border-radius:8px;background:#fff;"></iframe>',
                            height=670, scrolling=False,
                        )

    # ── Not found section ─────────────────
    if st.session_state["notfound_df"] is not None and len(st.session_state["notfound_df"]) > 0:
        nf = st.session_state["notfound_df"]
        with st.expander(f"⚠️ {len(nf)} nopol dari File 1 tidak ditemukan di database"):
            show_cols = [c for c in ["NOPOL_RAW","KUANTUM_F1"] if c in nf.columns]
            st.dataframe(
                nf[show_cols].rename(columns={"NOPOL_RAW":"NOPOL","KUANTUM_F1":"KUANTUM (File1)"}),
                use_container_width=True, hide_index=True
            )

    # ── Invalid links summary ─────────────
    if st.session_state["matched_df"] is not None:
        inv = matched[matched["VALID_LINK"] == False]
        if len(inv) > 0:
            with st.expander(f"🔗 {len(inv)} surat jalan dengan link tidak valid"):
                show = [c for c in ["NOPOL_RAW","KUANTUM","LINK"] if c in inv.columns]
                st.dataframe(inv[show].reset_index(drop=True), use_container_width=True, hide_index=True)
