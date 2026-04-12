# ... (kode sebelumnya sama sampai setelah st.success)

# Tampilkan hasil jika ada
if "matched_df" in st.session_state and st.session_state["matched_df"] is not None:
    matched = st.session_state["matched_df"]
    not_found = st.session_state["notfound_df"]

    # Pastikan kolom yang diperlukan ada
    if "KUANTUM" not in matched.columns:
        matched["KUANTUM"] = None  # tambahkan kolom dummy jika tidak ada
    if "KUANTUM_F1" not in matched.columns:
        matched["KUANTUM_F1"] = None

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

    # --- FILTER SECTION ---
    st.markdown("### 🔍 Filter Data")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        search = st.text_input("🔍 Cari NOPOL", placeholder="Ketik nopol...", key="search_nopol")
    with col_f2:
        link_filter = st.selectbox("Status Link", options=["Semua", "Valid", "Invalid"], key="link_filter")
    with col_f3:
        # Filter range kuantum (jika ada)
        min_q = st.number_input("Min Kuantum (kg)", value=0.0, step=100.0, key="min_q")
        max_q = st.number_input("Max Kuantum (kg)", value=float('inf'), step=100.0, key="max_q")
    
    # Terapkan filter
    filtered = matched.copy()
    if search:
        filtered = filtered[filtered["NOPOL_KEY"].str.contains(search.upper().replace(" ", ""), na=False)]
    if link_filter == "Valid":
        filtered = filtered[filtered["VALID_LINK"] == True]
    elif link_filter == "Invalid":
        filtered = filtered[filtered["VALID_LINK"] == False]
    # Filter kuantum (gunakan KUANTUM jika ada, fallback KUANTUM_F1)
    kuantum_col = "KUANTUM" if "KUANTUM" in filtered.columns and filtered["KUANTUM"].notna().any() else "KUANTUM_F1"
    if kuantum_col in filtered.columns:
        filtered = filtered[(filtered[kuantum_col] >= min_q) | (filtered[kuantum_col].isna())]
        if max_q != float('inf'):
            filtered = filtered[(filtered[kuantum_col] <= max_q) | (filtered[kuantum_col].isna())]
    
    # Pagination
    total_filtered = len(filtered)
    page = st.session_state.get("page", 0)
    total_pages = (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE if total_filtered > 0 else 1
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

    # Render data_editor dengan filtered dataframe
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, total_filtered)
    page_df = filtered.iloc[start_idx:end_idx].copy()
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
    selected_indices = edited_df[edited_df["Pilih"] == True].index.tolist()
    # Peta ke index asli di filtered
    original_global_indices = page_df.index.tolist()
    selected_global = [original_global_indices[i] for i in selected_indices if i < len(original_global_indices)]
    
    st.caption(f"Menampilkan {min(PAGE_SIZE, total_filtered)} dari {total_filtered} baris (setelah filter).")

    # Tombol batch download (sama seperti sebelumnya, menggunakan filtered untuk "Download Semua" sebaiknya menggunakan filtered yang sudah difilter? Biar user bisa download semua hasil filter)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        if st.button("📦 Download Semua (Valid)", use_container_width=True):
            # Gunakan filtered yang valid
            valid_items = [(idx, row["NOPOL_KEY"], row.get("KUANTUM",""), row["LINK"])
                           for idx, row in filtered[filtered["VALID_LINK"]==True].iterrows()]
            if not valid_items:
                st.warning("Tidak ada link valid pada hasil filter.")
            else:
                results, fails = batch_download(valid_items, max_workers=max_workers)
                if results:
                    files_dict = {fname: content for _, (fname, content) in results.items()}
                    zip_data = generate_zip(files_dict)
                    st.download_button("💾 Simpan ZIP (Semua Hasil Filter)", data=zip_data,
                                       file_name="semua_surat_jalan.zip", mime="application/zip")
                if fails:
                    st.warning(f"{len(fails)} file gagal: {', '.join(fails[:5])}{'...' if len(fails)>5 else ''}")
    with col_dl2:
        if st.button("⬇️ Download Terpilih", use_container_width=True):
            if not selected_global:
                st.warning("Pilih minimal satu baris dengan checklist.")
            else:
                selected_rows = filtered.loc[selected_global]
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

    # Tampilkan daftar invalid link di expander (dari filtered)
    invalid_df = filtered[filtered["VALID_LINK"]==False][["NOPOL_RAW","KUANTUM","LINK"]].drop_duplicates()
    if len(invalid_df) > 0:
        with st.expander(f"⚠️ {len(invalid_df)} surat jalan dengan link tidak valid (pada hasil filter)"):
            st.dataframe(invalid_df, use_container_width=True, hide_index=True)

    # Not found (tetap dari not_found asli)
    if not_found is not None and len(not_found) > 0:
        with st.expander(f"❌ {len(not_found)} nopol tidak ditemukan di database"):
            st.dataframe(not_found[["NOPOL_RAW","KUANTUM_F1"]].rename(columns={"KUANTUM_F1":"Target Kuantum"}), use_container_width=True, hide_index=True)

    # Tombol reset cache
    if st.button("🗑️ Reset Cache Download", help="Hapus file PDF yang tersimpan sementara"):
        st.session_state.download_cache.clear()
        st.success("Cache dibersihkan.")
