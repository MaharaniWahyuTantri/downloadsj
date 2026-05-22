import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
import os
import gc
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

st.set_page_config(
    page_title="SuratJalan — Bulk Downloader",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,700&family=Sora:wght@400;500;600;700;800&family=Fira+Code:wght@400;500;600&display=swap');

:root {
  /* === PALETTE === */
  --bg:          #f0f4ff;
  --bg2:         #e8eeff;
  --surface:     #ffffff;
  --surface2:    #f5f7ff;
  --surface3:    #eef1ff;

  --blue:        #3b5bdb;
  --blue-dk:     #2f4ac9;
  --blue-lt:     #dce4ff;
  --blue-pale:   #eef1ff;
  --blue-glow:   rgba(59,91,219,.18);

  --orange:      #f76707;
  --orange-dk:   #e05c00;
  --orange-lt:   #fff4eb;
  --orange-pale: #ffe8d6;
  --orange-glow: rgba(247,103,7,.18);

  --sky:         #4dabf7;
  --sky-lt:      #e7f5ff;

  --green:       #2f9e44;
  --green-lt:    #ebfbee;
  --green-pale:  #d3f9d8;

  --red:         #e03131;
  --red-lt:      #fff5f5;
  --red-pale:    #ffe3e3;

  --amber:       #e67700;
  --amber-lt:    #fff9db;
  --amber-pale:  #ffec99;

  --violet:      #7048e8;
  --violet-lt:   #f3f0ff;
  --violet-pale: #e5dbff;

  --text:        #1a1d2e;
  --text2:       #3d4066;
  --text3:       #7b82b8;
  --text4:       #a8aed6;

  --border:      #d9dfff;
  --border2:     #c5ccf5;

  --radius-sm:   8px;
  --radius:      14px;
  --radius-lg:   20px;
  --radius-xl:   28px;

  --shadow-sm:   0 1px 3px rgba(59,91,219,.08), 0 1px 2px rgba(0,0,0,.04);
  --shadow:      0 4px 16px rgba(59,91,219,.10), 0 2px 6px rgba(0,0,0,.05);
  --shadow-lg:   0 12px 40px rgba(59,91,219,.14), 0 4px 12px rgba(0,0,0,.06);
  --shadow-orange: 0 6px 22px rgba(247,103,7,.28);
  --shadow-blue:   0 6px 22px rgba(59,91,219,.28);

  --font: 'Nunito', sans-serif;
  --font-head: 'Sora', sans-serif;
  --mono: 'Fira Code', monospace;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: var(--font) !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
.main .block-container {
  padding: clamp(16px,3vw,40px) clamp(16px,3.5vw,56px) 80px !important;
  max-width: 1320px !important;
}

/* ── TOPBAR ── */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 0 20px; flex-wrap: wrap; gap: 12px;
  border-bottom: 2px dashed var(--border); margin-bottom: 4px;
}
.topbar-brand { display: flex; align-items: center; gap: 12px; }
.topbar-logo {
  width: 44px; height: 44px; border-radius: 14px;
  background: linear-gradient(135deg, var(--orange) 0%, #fd9a3c 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem; box-shadow: var(--shadow-orange);
  position: relative; overflow: hidden;
}
.topbar-logo::after {
  content: ''; position: absolute; top: -8px; right: -8px;
  width: 24px; height: 24px; border-radius: 50%;
  background: rgba(255,255,255,.25);
}
.topbar-name {
  font-family: var(--font-head); font-size: 1.05rem;
  font-weight: 800; color: var(--text); letter-spacing: -.4px;
}
.topbar-ver {
  font-size: .62rem; color: var(--text3); font-weight: 600;
  letter-spacing: .8px; text-transform: uppercase; margin-top: 1px;
}
.topbar-chips { display: flex; gap: 7px; flex-wrap: wrap; }
.chip {
  font-size: .67rem; font-weight: 800; padding: 4px 10px;
  border-radius: 100px; letter-spacing: .2px; font-family: var(--font);
}
.chip-blue  { background: var(--blue-lt);   color: var(--blue);   border: 1.5px solid var(--border2); }
.chip-orange{ background: var(--orange-pale);color: var(--orange-dk);border: 1.5px solid #ffc29d; }
.chip-green { background: var(--green-lt);  color: var(--green);  border: 1.5px solid var(--green-pale); }
.chip-violet{ background: var(--violet-lt); color: var(--violet); border: 1.5px solid var(--violet-pale); }

/* ── HERO ── */
.hero {
  background: linear-gradient(135deg, #3b5bdb 0%, #4c6ef5 50%, #5c7cfa 100%);
  border-radius: var(--radius-xl); padding: clamp(24px,5vw,40px) clamp(24px,5vw,48px);
  margin: 20px 0 8px; position: relative; overflow: hidden;
  box-shadow: 0 16px 48px rgba(59,91,219,.30);
}
.hero::before {
  content: ''; position: absolute; top: -60px; right: -60px;
  width: 220px; height: 220px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,.12) 0%, transparent 70%);
}
.hero::after {
  content: '🚚'; position: absolute; right: clamp(12px,4vw,36px);
  bottom: -18px; font-size: clamp(70px,14vw,120px);
  opacity: .12; pointer-events: none; transform: scaleX(-1) rotate(-6deg);
  filter: drop-shadow(0 4px 8px rgba(0,0,0,.2));
}
.hero-eyebrow {
  font-size: .65rem; font-weight: 800; letter-spacing: 3px;
  text-transform: uppercase; color: rgba(255,255,255,.55);
  margin-bottom: 8px; font-family: var(--font-head);
}
.hero-title {
  font-family: var(--font-head); font-size: clamp(1.5rem,4vw,2.3rem);
  font-weight: 800; color: #fff; line-height: 1.12;
  margin-bottom: 10px; letter-spacing: -.5px;
}
.hero-title span {
  background: linear-gradient(90deg, #ffd43b, #ffa94d);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  font-size: clamp(.78rem,1.8vw,.9rem); color: rgba(255,255,255,.75);
  line-height: 1.75; max-width: 530px;
}
.hero-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.hero-badge {
  font-size: .68rem; font-weight: 700; padding: 4px 12px; border-radius: 100px;
  background: rgba(255,255,255,.15); color: rgba(255,255,255,.9);
  border: 1px solid rgba(255,255,255,.2); backdrop-filter: blur(4px);
}

/* ── STEP TRACKER ── */
.steps-wrap {
  display: flex; align-items: center; gap: 0;
  background: var(--surface); border: 2px solid var(--border);
  border-radius: 100px; padding: 6px 8px; margin: 20px 0;
  box-shadow: var(--shadow-sm); overflow-x: auto; width: fit-content;
  max-width: 100%;
}
.step-item { display: flex; align-items: center; gap: 7px; padding: 5px 14px; border-radius: 100px; font-size: .75rem; font-weight: 700; white-space: nowrap; transition: all .2s; font-family: var(--font-head); }
.step-item.done   { background: var(--green-lt); color: var(--green); }
.step-item.active { background: linear-gradient(135deg, var(--orange), #fd9a3c); color: #fff; box-shadow: var(--shadow-orange); }
.step-item.idle   { color: var(--text4); }
.step-num { width: 20px; height: 20px; border-radius: 50%; font-size: .65rem; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-item.done   .step-num { background: var(--green);  color: #fff; }
.step-item.active .step-num { background: rgba(255,255,255,.25); color: #fff; }
.step-item.idle   .step-num { background: var(--surface2); color: var(--text4); }
.step-sep { color: var(--border2); font-size: .7rem; padding: 0 3px; flex-shrink: 0; }

/* ── SECTION HEADER ── */
.sec-hdr { display: flex; align-items: center; gap: 12px; margin: clamp(24px,4vw,36px) 0 clamp(14px,2.5vw,20px); }
.sec-num {
  font-family: var(--font-head); font-size: .62rem; font-weight: 800;
  letter-spacing: 2px; text-transform: uppercase; padding: 4px 10px;
  background: linear-gradient(135deg, var(--blue), #4c6ef5);
  color: #fff; border-radius: 7px; box-shadow: var(--shadow-blue);
}
.sec-title { font-family: var(--font-head); font-size: 1rem; font-weight: 700; color: var(--text); letter-spacing: -.3px; }
.sec-line { flex: 1; height: 2px; background: linear-gradient(90deg, var(--border), transparent); border-radius: 100px; }

/* ── UPLOAD CARDS ── */
.ucard {
  background: var(--surface); border: 2px solid var(--border);
  border-radius: var(--radius-lg); padding: clamp(16px,2.5vw,24px);
  box-shadow: var(--shadow-sm); transition: all .25s;
  position: relative; overflow: hidden;
}
.ucard::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
  border-radius: 4px 4px 0 0;
}
.ucard-a::before { background: linear-gradient(90deg, var(--orange), #fda94c); }
.ucard-b::before { background: linear-gradient(90deg, var(--blue), #74c0fc); }
.ucard:hover { border-color: var(--blue); box-shadow: var(--shadow); transform: translateY(-2px); }
.ucard.ready { border-color: var(--green); background: var(--green-lt); }
.ucard-head { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.ucard-icon {
  width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
}
.ucard-icon-a { background: var(--orange-pale); border: 2px solid #ffc29d; }
.ucard-icon-b { background: var(--blue-pale);   border: 2px solid var(--blue-lt); }
.ucard-ttl { font-family: var(--font-head); font-size: .9rem; font-weight: 700; color: var(--text); }
.ucard-sub { font-size: .72rem; color: var(--text3); margin-top: 3px; line-height: 1.45; }
.tag-row { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.tag-r { font-size: .63rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; font-family: var(--mono); background: var(--orange-pale); color: var(--orange-dk); border: 1px solid #ffc29d; }
.tag-o { font-size: .63rem; font-weight: 700; padding: 3px 8px; border-radius: 6px; font-family: var(--mono); background: var(--blue-pale); color: var(--blue); border: 1px solid var(--blue-lt); }
.file-pill { display: flex; align-items: center; gap: 8px; background: var(--green-lt); border: 1.5px solid var(--green-pale); border-radius: 8px; padding: 7px 12px; margin-top: 10px; font-size: .76rem; color: var(--green); font-weight: 700; }

/* ── BUTTONS ── */
.stButton > button {
  font-family: var(--font) !important; font-weight: 700 !important;
  font-size: .83rem !important; border-radius: 12px !important;
  padding: 10px 18px !important; transition: all .2s !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--orange), #fd9a3c) !important;
  color: #fff !important; border: none !important;
  box-shadow: var(--shadow-orange) !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--orange-dk), var(--orange)) !important;
  box-shadow: 0 8px 28px rgba(247,103,7,.4) !important;
  transform: translateY(-2px) !important;
}
.stButton > button[kind="primary"]:disabled {
  background: var(--surface2) !important; color: var(--text4) !important;
  box-shadow: none !important; transform: none !important;
}
.stButton > button:not([kind="primary"]) {
  background: var(--surface) !important; color: var(--text2) !important;
  border: 2px solid var(--border) !important; box-shadow: var(--shadow-sm) !important;
}
.stButton > button:not([kind="primary"]):hover {
  border-color: var(--blue) !important; color: var(--blue) !important;
  background: var(--blue-pale) !important; transform: translateY(-1px) !important;
}

/* ── STAT CARDS ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(150px,100%), 1fr));
  gap: clamp(10px,2vw,14px); margin: clamp(14px,2.5vw,22px) 0;
}
.stat-card {
  background: var(--surface); border: 2px solid var(--border);
  border-radius: var(--radius-lg); padding: clamp(14px,2.2vw,20px);
  box-shadow: var(--shadow-sm); position: relative; overflow: hidden;
  transition: box-shadow .2s, transform .2s; cursor: default;
}
.stat-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); }
.stat-top-bar { position: absolute; top: 0; left: 0; right: 0; height: 4px; border-radius: 4px 4px 0 0; }
.stat-bg-icon { position: absolute; right: -6px; bottom: -10px; font-size: 2.8rem; opacity: .07; pointer-events: none; }
.stat-lbl { font-size: .62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.4px; color: var(--text3); margin-bottom: 6px; font-family: var(--font-head); }
.stat-val { font-family: var(--mono); font-size: clamp(1.6rem,3.8vw,2.4rem); font-weight: 600; line-height: 1; }
.stat-sub { font-size: .66rem; font-weight: 700; margin-top: 5px; }

/* ── ALERTS ── */
.alert {
  border-radius: var(--radius); padding: clamp(10px,2vw,14px) clamp(12px,2vw,18px);
  margin: 10px 0; font-size: .82rem; line-height: 1.7;
  display: flex; gap: 12px; align-items: flex-start;
}
.alert-ico { font-size: .95rem; flex-shrink: 0; margin-top: 1px; }
.a-success { background: var(--green-lt);  border: 1.5px solid var(--green-pale); border-left: 3.5px solid var(--green);  color: #1a5c2e; }
.a-warn    { background: var(--amber-lt);  border: 1.5px solid var(--amber-pale); border-left: 3.5px solid var(--amber);  color: #6b3c00; }
.a-error   { background: var(--red-lt);    border: 1.5px solid var(--red-pale);   border-left: 3.5px solid var(--red);    color: #7c1212; }
.a-info    { background: var(--blue-pale); border: 1.5px solid var(--blue-lt);    border-left: 3.5px solid var(--blue);   color: #1e2f8a; }
.a-violet  { background: var(--violet-lt); border: 1.5px solid var(--violet-pale);border-left: 3.5px solid var(--violet); color: #3b1d8a; }
.a-sky     { background: var(--sky-lt);    border: 1.5px solid #a5d8ff;           border-left: 3.5px solid var(--sky);    color: #0c4a6e; }
.a-orange  { background: var(--orange-lt); border: 1.5px solid var(--orange-pale);border-left: 3.5px solid var(--orange); color: #6b2600; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface2) !important; border: 2px solid var(--border) !important;
  border-radius: 14px !important; padding: 5px !important; gap: 3px !important;
  box-shadow: var(--shadow-sm) !important; overflow-x: auto !important;
  flex-wrap: nowrap !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important; font-size: clamp(.68rem,1.6vw,.8rem) !important;
  font-weight: 700 !important; padding: clamp(6px,1.5vw,9px) clamp(9px,2vw,15px) !important;
  color: var(--text3) !important; border: none !important;
  background: transparent !important; white-space: nowrap !important;
  font-family: var(--font) !important; transition: all .18s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--blue) !important; background: var(--blue-pale) !important; }
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--blue), #4c6ef5) !important;
  color: #fff !important; font-weight: 800 !important;
  box-shadow: var(--shadow-blue) !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── PROGRESS ── */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--orange), #fda94c) !important;
  border-radius: 100px !important;
}
.stProgress > div > div {
  background: var(--surface2) !important; border-radius: 100px !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input {
  background: var(--surface) !important; border: 2px solid var(--border) !important;
  border-radius: 10px !important; color: var(--text) !important;
  font-family: var(--font) !important; font-size: .82rem !important;
  padding: 9px 13px !important; transition: all .18s !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px var(--blue-glow) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--text4) !important; }

/* ── SLIDER ── */
.stSlider > div > div > div > div { background: var(--orange) !important; }
.stSlider > div > div > div { background: var(--border) !important; }

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] > div {
  background: var(--surface) !important; border: 2px solid var(--border) !important;
  border-radius: var(--radius-lg) !important; box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stMetric"] {
  background: var(--surface) !important; border: 2px solid var(--border) !important;
  border-radius: var(--radius-lg) !important; padding: 16px !important;
  box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stMetricLabel"] { color: var(--text3) !important; font-size: .72rem !important; font-family: var(--font-head) !important; }
div[data-testid="stMetricValue"] { color: var(--text) !important; font-family: var(--mono) !important; }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
  font-family: var(--font) !important; font-weight: 800 !important;
  font-size: .78rem !important;
  background: linear-gradient(135deg, var(--green-lt), #c3fad5) !important;
  border: 2px solid var(--green-pale) !important; border-radius: 10px !important;
  color: var(--green) !important; padding: 8px 14px !important;
  transition: all .2s !important; box-shadow: 0 2px 8px rgba(47,158,68,.15) !important;
}
.stDownloadButton > button:hover {
  background: var(--green-pale) !important; border-color: var(--green) !important;
  box-shadow: 0 4px 14px rgba(47,158,68,.25) !important; transform: translateY(-1px) !important;
}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploaderDropzone"] {
  background: var(--surface2) !important; border: 2px dashed var(--border2) !important;
  border-radius: 12px !important; transition: all .2s !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--orange) !important; background: var(--orange-lt) !important;
}
div[data-testid="stFileUploaderDropzone"] p { color: var(--text3) !important; font-size: .8rem !important; font-family: var(--font) !important; }
button[data-testid="baseButton-secondary"] {
  background: var(--blue-pale) !important; border: 2px solid var(--blue-lt) !important;
  color: var(--blue) !important; border-radius: 9px !important; font-family: var(--font) !important;
}

/* ── INLINE TAGS ── */
.np {
  display: inline-block; background: var(--blue-pale);
  border: 1.5px solid var(--blue-lt); color: var(--blue);
  border-radius: 7px; padding: 2px 9px;
  font-family: var(--mono); font-size: .78rem; font-weight: 500;
}
.np-dup {
  background: var(--violet-lt); border-color: var(--violet-pale); color: var(--violet);
}
.sim { display: inline-block; border-radius: 7px; padding: 2px 8px; font-size: .71rem; font-weight: 800; font-family: var(--mono); }
.sim-hi  { background: var(--green-lt);  color: var(--green);  border: 1.5px solid var(--green-pale); }
.sim-md  { background: var(--amber-lt);  color: var(--amber);  border: 1.5px solid var(--amber-pale); }
.sim-lo  { background: var(--red-lt);    color: var(--red);    border: 1.5px solid var(--red-pale); }
.dup-group {
  background: var(--violet-lt); border: 2px solid var(--violet-pale);
  border-radius: var(--radius-lg); padding: 16px 18px; margin: 12px 0 6px;
}
.dup-group-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.col-hdr { font-size: .62rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1.4px; color: var(--text3); font-family: var(--font-head); }
.row-div { border: none; border-top: 1.5px dashed var(--border); margin: 8px 0; }
.cache-info {
  background: linear-gradient(135deg, var(--blue-pale), var(--surface2));
  border: 1.5px solid var(--blue-lt); border-radius: 10px;
  padding: 8px 14px; font-size: .77rem; color: var(--text2); line-height: 1.5;
}
.empty-state {
  text-align: center; padding: clamp(36px,5vw,60px) 28px;
  color: var(--text3); background: var(--surface);
  border: 2px dashed var(--border); border-radius: var(--radius-xl); margin: 10px 0;
}
.empty-state .ico { font-size: clamp(2rem,4.5vw,3rem); margin-bottom: 12px; opacity: .5; }
.empty-state h3 { font-family: var(--font-head); font-size: 1rem; font-weight: 700; color: var(--text2); margin-bottom: 6px; }
.empty-state p { font-size: .82rem; line-height: 1.7; max-width: 320px; margin: 0 auto; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 2px solid var(--border) !important; }
section[data-testid="stSidebar"] * { font-family: var(--font) !important; color: var(--text2) !important; }
details { background: var(--surface) !important; border-radius: 12px !important; border: 2px solid var(--border) !important; }
summary { font-size: .82rem !important; color: var(--text2) !important; padding: 10px 14px !important; font-family: var(--font-head) !important; font-weight: 700 !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--surface2); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 100px; }
::-webkit-scrollbar-thumb:hover { background: var(--blue); }

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── FLOATING DECO DOTS ── */
.deco-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  margin: 0 2px; vertical-align: middle;
}

@media (max-width: 640px) {
  .stat-grid { grid-template-columns: repeat(2,1fr); }
  .topbar-chips { display: none; }
  .hero::after { display: none; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
MAX_CACHE_BYTES   = 200 * 1024 * 1024
MAX_CACHE_ENTRIES = 300
DOWNLOAD_WORKERS  = 6
DOWNLOAD_BATCH_SIZE = 50
CHUNK_SIZE        = 64 * 1024


# ══════════════════════════════════════════════════════════════════════════════
# DISK CACHE
# ══════════════════════════════════════════════════════════════════════════════
def _get_tmp_dir() -> Path:
    if 'tmp_dir' not in st.session_state or not Path(st.session_state.tmp_dir).exists():
        td = tempfile.mkdtemp(prefix='sj_')
        st.session_state.tmp_dir = td
    return Path(st.session_state.tmp_dir)

def _cache_path(link: str) -> Path:
    import hashlib
    h = hashlib.md5(link.encode()).hexdigest()
    return _get_tmp_dir() / f"dl_{h}.bin"

def cache_has(link: str) -> bool:   return _cache_path(link).exists()
def cache_put(link: str, data: bytes) -> None: _cache_path(link).write_bytes(data)
def cache_get(link: str) -> bytes | None:
    p = _cache_path(link)
    if p.exists():
        try: return p.read_bytes()
        except: return None
    return None
def cache_size_bytes() -> int:
    td = _get_tmp_dir()
    return sum(f.stat().st_size for f in td.glob('dl_*.bin') if f.is_file())
def cache_count() -> int: return len(list(_get_tmp_dir().glob('dl_*.bin')))
def cache_clear() -> None:
    td = _get_tmp_dir()
    for f in td.glob('dl_*.bin'):
        try: f.unlink()
        except: pass


# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def norm_nopol(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return ''
    s = str(v).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    return re.sub(r'\s+', ' ', s).strip()

def norm_kuantum(v):
    try: return int(float(str(v).replace(',', '.').strip()))
    except: return None

def find_col(df, kws):
    for col in df.columns:
        c = col.lower().replace(' ', '').replace('_', '')
        for k in kws:
            if k.replace(' ', '').replace('_', '') in c: return col
    return None

def extract_fid(link):
    if not isinstance(link, str) or not link.strip(): return None
    for p in [r'/file/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)',
              r'/d/([a-zA-Z0-9_-]+)', r'open\?id=([a-zA-Z0-9_-]+)']:
        m = re.search(p, link.strip())
        if m and len(m.group(1)) >= 15: return m.group(1)
    return None

def to_preview(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def detect_file_type(content: bytes | None) -> str:
    if not content or len(content) < 4: return 'unknown'
    sig = content[:8]
    if sig[:4] == b'%PDF': return 'pdf'
    if sig[:3] == b'\xff\xd8\xff': return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
    try:
        snippet = content[:2000].decode('utf-8', errors='ignore').lower()
        if '<html' in snippet or '<!doctype' in snippet: return 'html'
    except: pass
    return 'unknown'

def _stream_bytes(resp) -> bytes:
    buf = bytearray()
    for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
        if chunk: buf.extend(chunk)
    return bytes(buf)

def download_gdrive(fid: str, retries: int = 4, timeout: int = 60) -> bytes | None:
    if not fid: return None
    session = requests.Session()
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    base_url = f'https://drive.google.com/uc?export=download&id={fid}'
    for attempt in range(retries):
        try:
            r1 = session.get(base_url, timeout=timeout, stream=True, allow_redirects=True)
            raw1 = _stream_bytes(r1)
            if 'text/html' not in r1.headers.get('Content-Type', ''):
                ft = detect_file_type(raw1)
                if ft != 'html' and len(raw1) > 512: return raw1
            html = raw1.decode('utf-8', errors='ignore')
            m = re.search(r'name="confirm"\s+value="([^"]+)"', html)
            if m:
                r2 = session.get(f'{base_url}&confirm={m.group(1)}', timeout=timeout, stream=True, allow_redirects=True)
                raw2 = _stream_bytes(r2)
                if detect_file_type(raw2) != 'html' and len(raw2) > 512: return raw2
            for extra in ['&confirm=t', '']:
                r = session.get(f'{base_url}{extra}', timeout=timeout, stream=True, allow_redirects=True)
                raw = _stream_bytes(r)
                if detect_file_type(raw) != 'html' and len(raw) > 512: return raw
        except: pass
        if attempt < retries - 1: time.sleep(min(2 ** attempt, 8))
    return None

def download_file(link: str) -> bytes | None:
    if not isinstance(link, str) or not link.strip(): return None
    fid = extract_fid(link)
    if fid: return download_gdrive(fid)
    try:
        r = requests.get(link.strip(), timeout=60, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        raw = _stream_bytes(r)
        if detect_file_type(raw) != 'html' and len(raw) > 512: return raw
    except: pass
    return None

def infer_extension(content: bytes | None, fallback: str = 'pdf') -> str:
    return {'pdf': 'pdf', 'jpg': 'jpg', 'png': 'png'}.get(
        detect_file_type(content) if content else 'x', fallback)

def make_safe_filename(nopol, kuantum, idx, ext, total=999, dup_label=''):
    safe = re.sub(r'[\\/:*?"<>|]', '_', str(nopol))
    pad = len(str(max(total, 1)))
    no = str(idx + 1).zfill(pad)
    return f'{no}_{safe}_{kuantum}{dup_label}.{ext}'


# ══════════════════════════════════════════════════════════════════════════════
# DISK-BASED ZIP & PDF BUILDERS
# ══════════════════════════════════════════════════════════════════════════════
def build_zip_to_disk(file_tasks: list[dict]) -> Path | None:
    td = _get_tmp_dir()
    zip_path = td / f"bundle_{int(time.time())}.zip"
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for task in file_tasks:
                data = cache_get(task['link'])
                if data:
                    zf.writestr(task['name'], data)
                    del data; gc.collect()
        return zip_path
    except:
        if zip_path.exists(): zip_path.unlink()
        return None

def img_bytes_to_pdf(img_bytes: bytes) -> bytes | None:
    tmp_path = None
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image as PILImage
        pil = PILImage.open(io.BytesIO(img_bytes))
        if pil.mode not in ('RGB', 'L'): pil = pil.convert('RGB')
        w_px, h_px = pil.size
        a4_w, a4_h = A4
        margin = 20
        scale = min((a4_w - 2 * margin) / w_px, (a4_h - 2 * margin) / h_px)
        draw_w, draw_h = w_px * scale, h_px * scale
        x = (a4_w - draw_w) / 2; y = (a4_h - draw_h) / 2
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name; pil.save(tmp_path, format='PNG')
        pdf_buf = io.BytesIO()
        c = rl_canvas.Canvas(pdf_buf, pagesize=(a4_w, a4_h))
        c.drawImage(tmp_path, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        c.save(); pdf_buf.seek(0); return pdf_buf.read()
    except: return None
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except: pass

def merge_pdfs_to_disk(links: list[str]) -> Path | None:
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try: from PyPDF2 import PdfWriter, PdfReader
        except ImportError: return None
    td = _get_tmp_dir()
    out_path = td / f"merged_{int(time.time())}.pdf"
    writer = PdfWriter(); page_count = 0
    for link in links:
        data = cache_get(link)
        if not data: continue
        ftype = detect_file_type(data)
        if ftype == 'pdf': pdf_data = data
        elif ftype in ('jpg', 'png'): pdf_data = img_bytes_to_pdf(data)
        else: pdf_data = None
        del data; gc.collect()
        if pdf_data:
            try:
                for page in PdfReader(io.BytesIO(pdf_data)).pages:
                    writer.add_page(page); page_count += 1
            except: continue
            del pdf_data; gc.collect()
    if page_count == 0: return None
    with open(out_path, 'wb') as f: writer.write(f)
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# PARALLEL DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
def _worker_to_disk(task: dict) -> dict:
    link = task['link']
    if cache_has(link): data = cache_get(link)
    else:
        data = download_file(link)
        if data: cache_put(link, data)
    return {**task, 'ok': data is not None, 'ext': infer_extension(data) if data else 'pdf'}

def run_bulk_download(rows: list[dict], label: str = '') -> tuple[list, list]:
    total = len(rows)
    prog_container = st.empty()
    with prog_container.container():
        prog_bar = st.progress(0)
        st.markdown(
            f'<div class="alert a-info"><span class="alert-ico">⏳</span>'
            f'<div><b>Mengunduh {label}…</b> {total} file · {DOWNLOAD_WORKERS} thread paralel</div></div>',
            unsafe_allow_html=True)
        status_txt = st.empty()
    ok_rows: list[dict] = []; fail_list: list[str] = []; done_n = 0
    for batch_start in range(0, total, DOWNLOAD_BATCH_SIZE):
        batch = rows[batch_start: batch_start + DOWNLOAD_BATCH_SIZE]
        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
            futs = {ex.submit(_worker_to_disk, t): t for t in batch}
            for fut in as_completed(futs):
                res = fut.result()
                if res['ok']: ok_rows.append(res)
                else: fail_list.append(f"{res['nopol']} ({res['kuantum']}){res.get('dup_label', '')}")
                done_n += 1
                prog_bar.progress(done_n / total)
                pct = int(done_n / total * 100)
                status_txt.markdown(
                    f"**{pct}%** — {done_n}/{total} &nbsp;|&nbsp; ✅ **{len(ok_rows)}** berhasil &nbsp;|&nbsp; ❌ **{len(fail_list)}** gagal")
        gc.collect()
    prog_container.empty()
    return ok_rows, fail_list


# ══════════════════════════════════════════════════════════════════════════════
# FILE READING
# ══════════════════════════════════════════════════════════════════════════════
def read_file(f):
    if f.name.lower().endswith('.csv'): return pd.read_csv(f)
    return pd.read_excel(f)

def read_xlsx_with_hyperlinks(f):
    try:
        from openpyxl import load_workbook
        f.seek(0); wb = load_workbook(f, data_only=True); ws = wb.active
        hyperlinks = {}
        for row in ws.iter_rows():
            for cell in row:
                if cell.hyperlink:
                    target = (cell.hyperlink if isinstance(cell.hyperlink, str) else cell.hyperlink.target)
                    if target: hyperlinks[(cell.row, cell.column)] = target
        if not hyperlinks: f.seek(0); return pd.read_excel(f)
        f.seek(0); df = pd.read_excel(f)
        for (row, col), target in hyperlinks.items():
            if row < 2: continue
            pr, pc = row - 2, col - 1
            if pr < len(df) and pc < len(df.columns):
                if not str(df.iloc[pr, pc]).strip().startswith('http'):
                    df.iloc[pr, pc] = target
        return df
    except:
        f.seek(0); return pd.read_excel(f)

def load_file1(df):
    nc = (find_col(df, ['nopol', 'nomor polisi', 'no pol', 'no.pol', 'nopolisi']) or find_col(df, ['pol']))
    kc = find_col(df, ['kuantum', 'quantum', 'tonase', 'tonage', 'qty', 'jumlah', 'volume', 'berat'])
    if not nc: st.error(f"❌ Kolom NOPOL tidak ditemukan. Kolom: `{'`, `'.join(df.columns)}`"); return pd.DataFrame()
    if not kc: st.error("❌ Kolom KUANTUM tidak ditemukan."); return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol'] = df[nc].apply(norm_nopol)
    out['kuantum'] = df[kc].apply(norm_kuantum)
    out = out[(out['nopol'] != '') & out['nopol'].notna()].dropna(subset=['kuantum'])
    return out[out['kuantum'] > 0].reset_index(drop=True)

def load_file2(raw_df):
    df = raw_df.copy()
    if df.empty: return pd.DataFrame()
    frow = df.iloc[0].tolist()
    if any(str(v).upper().strip() in ['NOPOL', 'KUANTUM', 'FOTO SURAT JALAN', 'SURAT JALAN'] for v in frow):
        df.columns = [str(c).strip() for c in df.iloc[0]]; df = df[1:].reset_index(drop=True)
    nc = (find_col(df, ['nopol', 'nomor polisi', 'no pol', 'no truk', 'no.pol', 'nopolisi']) or find_col(df, ['pol']))
    kc = find_col(df, ['kuantum', 'quantum', 'tonase', 'tonage', 'qty', 'jumlah', 'volume', 'berat'])
    lc = find_col(df, ['surat jalan', 'suratjalan', 'foto surat', 'foto', 'link', 'url', 'drive', 'gdrive'])
    if not nc: st.error("❌ Kolom NOPOL tidak ditemukan di File 2."); return pd.DataFrame()
    if not kc: st.error("❌ Kolom KUANTUM tidak ditemukan di File 2."); return pd.DataFrame()
    if not lc: st.error("❌ Kolom SURAT JALAN / LINK tidak ditemukan di File 2."); return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol'] = df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else '')
    out['kuantum'] = df[kc].apply(norm_kuantum)
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

def nopol_similarity(a, b): return SequenceMatcher(None, a, b).ratio()

def find_nopol_suggestions(nopol_f1, kuantum, df2, top_n=5, min_similarity=0.5):
    same_kuantum = df2[df2['kuantum'] == kuantum].copy()
    if same_kuantum.empty: return []
    results = []
    for _, row in same_kuantum.iterrows():
        sim = nopol_similarity(nopol_f1, row['nopol'])
        if sim >= min_similarity:
            results.append({'nopol_f2': row['nopol'], 'kuantum': int(row['kuantum']),
                            'surat_jalan': row['surat_jalan'], 'similarity': round(sim * 100, 1)})
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]

def build_missing_with_suggestions(missing_df, df1, df2):
    rows = []
    for _, row in missing_df.iterrows():
        nopol = row['nopol']; kuantum = int(row['kuantum'])
        f2_match = df2[df2['nopol'] == nopol]
        if len(f2_match) > 0:
            ks = sorted(f2_match['kuantum'].dropna().astype(int).unique().tolist())
            d = ', '.join(map(str, ks[:8])) + (f' (+{len(ks)-8})' if len(ks) > 8 else '')
            rows.append({'nopol': nopol, 'kuantum': kuantum, 'kategori': 'kuantum_beda', 'info': d, 'saran': []})
        else:
            saran = find_nopol_suggestions(nopol, kuantum, df2)
            rows.append({'nopol': nopol, 'kuantum': kuantum,
                         'kategori': 'nopol_mirip' if saran else 'tidak_ada', 'info': '', 'saran': saran})
    return rows

def detect_duplicates_f1(df1):
    key = ['nopol', 'kuantum']
    counts = df1.groupby(key).size().reset_index(name='jumlah_duplikat')
    dup_keys = counts[counts['jumlah_duplikat'] > 1][key]
    if dup_keys.empty: return pd.DataFrame()
    merged = df1.merge(dup_keys, on=key, how='inner').merge(counts, on=key, how='left')
    merged['baris_ke'] = merged.groupby(key).cumcount() + 1
    return merged.reset_index(drop=True)

def match_files(df1, df2):
    df2_valid = df2[df2['surat_jalan'].str.startswith('http', na=False)].copy()
    pos_in_group = df1.groupby(['nopol', 'kuantum']).cumcount()
    result_rows = []
    for idx, row1 in df1.iterrows():
        pos = int(pos_in_group[idx])
        matches = df2_valid[(df2_valid['nopol'] == row1['nopol']) & (df2_valid['kuantum'] == row1['kuantum'])].reset_index(drop=True)
        if len(matches) > 0:
            mrow = matches.iloc[min(pos, len(matches) - 1)]
            result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                 'surat_jalan': mrow['surat_jalan'], '_f1_idx': idx, '_link_no': pos + 1})
        else:
            result_rows.append({'nopol': row1['nopol'], 'kuantum': row1['kuantum'],
                                 'surat_jalan': None, '_f1_idx': idx, '_link_no': 0})
    return pd.DataFrame(result_rows)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for _k in ['result_df', 'missing_df', 'nopol_diff_df', 'nopol_miss_df',
           'active_preview', 'df2_debug', 'df1_debug', 'dup_df',
           'missing_detail', 'saran_preview', 'dup_prev_active', 'processed']:
    if _k not in st.session_state: st.session_state[_k] = None
if st.session_state.saran_preview is None: st.session_state.saran_preview = {}
if st.session_state.dup_prev_active is None: st.session_state.dup_prev_active = {}
if st.session_state.processed is None: st.session_state.processed = False
_get_tmp_dir()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('''
    <div style="text-align:center;padding:20px 0 14px">
      <div style="width:52px;height:52px;background:linear-gradient(135deg,#f76707,#fd9a3c);border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin:0 auto 12px;box-shadow:0 6px 20px rgba(247,103,7,.32)">🚚</div>
      <div style="font-family:'Sora',sans-serif;font-weight:800;font-size:1rem;color:#1a1d2e">SuratJalan</div>
      <div style="font-size:.62rem;color:#7b82b8;margin-top:3px;text-transform:uppercase;letter-spacing:1.5px;font-weight:700">Bulk Downloader · v3.0</div>
    </div>''', unsafe_allow_html=True)
    st.divider()
    with st.expander("📋 Cara Penggunaan", expanded=True):
        st.markdown("1. **Upload File 1** — Daftar target (NOPOL + Kuantum)\n2. **Upload File 2** — Database link Google Drive\n3. Klik **⚙️ Proses & Cocokkan**\n4. Download **ZIP** atau **PDF Gabungan**")
    with st.expander("📂 Format File"):
        st.markdown("**File 1:** `NOPOL` + `KUANTUM`\n\n**File 2:** `NOPOL` + `KUANTUM` + `Link GDrive`\n\n✅ Mendukung **hyperlink** Excel\n\nFormat: `.xlsx`, `.xls`, `.csv`")
    with st.expander("❓ FAQ"):
        st.markdown("**Hyperlink Excel?** Otomatis terdeteksi!\n\n**File gagal?** Mungkin private/expired.\n\n**Duplikat?** NOPOL+Kuantum muncul >1×.\n\n**Saran NOPOL?** Fuzzy matching otomatis.\n\n**Cache?** Tersimpan di disk temporer — RAM aman!")
    st.divider()
    if st.session_state.processed:
        n_c = cache_count(); sz = cache_size_bytes()
        tot_l = len(st.session_state.result_df) if st.session_state.result_df is not None else 0
        pct = int(n_c / max(tot_l, 1) * 100)
        st.markdown(f'<div style="font-size:.8rem;font-weight:700;color:#3b5bdb;margin-bottom:6px">💾 Cache Disk: {n_c} file · {sz/1024/1024:.1f} MB</div>', unsafe_allow_html=True)
        st.progress(min(pct / 100, 1.0))
        st.caption(f"{pct}% dari {tot_l} link ter-cache")
        if st.button("🗑️ Bersihkan Cache", use_container_width=True):
            cache_clear(); st.rerun()
    st.caption("Made with ❤️ · Streamlit · v3.0 disk-mode")


# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo">🚚</div>
    <div>
      <div class="topbar-name">SuratJalan Bulk Downloader</div>
      <div class="topbar-ver">v3.0 · Disk-mode · Large File Safe</div>
    </div>
  </div>
  <div class="topbar-chips">
    <span class="chip chip-orange">⚡ 6 Thread</span>
    <span class="chip chip-green">✅ Auto-Hyperlink</span>
    <span class="chip chip-blue">🔍 Fuzzy NOPOL</span>
    <span class="chip chip-violet">💾 Disk Cache</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">✦ Logistics · Automation · Documents ✦</div>
  <div class="hero-title">Download Surat Jalan<br><span>Ratusan File, Sekali Klik</span></div>
  <div class="hero-desc">Cocokkan NOPOL + Kuantum dari dua file, unduh ratusan dokumen besar sekaligus tanpa crash. Cache berbasis disk — tidak memborosi RAM. ZIP & PDF gabungan langsung ke disk.</div>
  <div class="hero-badges">
    <span class="hero-badge">📦 Bulk ZIP</span>
    <span class="hero-badge">📄 PDF Merge</span>
    <span class="hero-badge">🔍 Fuzzy Match</span>
    <span class="hero-badge">⚡ Paralel Download</span>
    <span class="hero-badge">💾 Disk Cache</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── STEP TRACKER ──────────────────────────────────────────────────────────────
def render_steps(active: int):
    items = [("1", "Upload File", "File 1 & 2"), ("2", "Proses", "Matching"), ("3", "Download", "ZIP / PDF")]
    parts = []
    for i, (n, lbl, sub) in enumerate(items):
        idx = i + 1
        if idx < active: s, icon = "done", "✓"
        elif idx == active: s, icon = "active", n
        else: s, icon = "idle", n
        parts.append(
            f'<div class="step-item {s}"><span class="step-num">{icon}</span>'
            f'<span>{lbl} <span style="opacity:.5;font-size:.68em">· {sub}</span></span></div>')
        if i < len(items) - 1: parts.append('<span class="step-sep">›</span>')
    st.markdown(f'<div class="steps-wrap">{"".join(parts)}</div>', unsafe_allow_html=True)

render_steps(3 if st.session_state.processed else 1)


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-hdr"><span class="sec-num">01</span><span class="sec-title">Upload File</span><span class="sec-line"></span></div>', unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2, gap="medium")
with col_f1:
    ready1 = "ready" if st.session_state.get("f1") else ""
    st.markdown(f'''<div class="ucard ucard-a {ready1}">
      <div class="ucard-head">
        <div class="ucard-icon ucard-icon-a">📋</div>
        <div>
          <div class="ucard-ttl">File 1 — Daftar Target</div>
          <div class="ucard-sub">Data yang ingin dicocokkan &amp; didownload</div>
        </div>
      </div>
      <div class="tag-row"><span class="tag-r">NOPOL *</span><span class="tag-r">KUANTUM *</span></div>
    </div>''', unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv', 'xlsx', 'xls'], key='f1', label_visibility='collapsed')
    if file1:
        st.markdown(f'<div class="file-pill">✅ &nbsp;<b>{file1.name}</b> — {file1.size/1024:.1f} KB</div>', unsafe_allow_html=True)

with col_f2:
    ready2 = "ready" if st.session_state.get("f2") else ""
    st.markdown(f'''<div class="ucard ucard-b {ready2}">
      <div class="ucard-head">
        <div class="ucard-icon ucard-icon-b">🗄️</div>
        <div>
          <div class="ucard-ttl">File 2 — Database Surat Jalan</div>
          <div class="ucard-sub">Berisi link Google Drive (URL atau hyperlink)</div>
        </div>
      </div>
      <div class="tag-row"><span class="tag-r">NOPOL *</span><span class="tag-r">KUANTUM *</span><span class="tag-r">Link GDrive *</span><span class="tag-o">hyperlink ✓</span></div>
    </div>''', unsafe_allow_html=True)
    file2 = st.file_uploader("File 2", type=['csv', 'xlsx', 'xls'], key='f2', label_visibility='collapsed')
    if file2:
        st.markdown(f'<div class="file-pill">✅ &nbsp;<b>{file2.name}</b> — {file2.size/1024:.1f} KB</div>', unsafe_allow_html=True)

st.markdown("")
both = file1 is not None and file2 is not None
bc1, bc2 = st.columns([2, 10])
with bc1:
    process = st.button('⚙️ Proses & Cocokkan', use_container_width=True, disabled=not both, type="primary")
with bc2:
    if not both:
        missing_f = [f for f in [("File 1" if not file1 else None), ("File 2" if not file2 else None)] if f]
        st.markdown(f'<div style="padding:11px 0;font-size:.8rem;color:#7b82b8">Upload <b style="color:#f76707">{" &amp; ".join(missing_f)}</b> untuk melanjutkan</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:11px 0;font-size:.8rem;color:#2f9e44;font-weight:700">✅ Kedua file siap — klik tombol untuk memproses!</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS
# ══════════════════════════════════════════════════════════════════════════════
if process:
    cache_clear()
    with st.spinner('🔄 Memproses dan mencocokkan data…'):
        raw_df2 = (read_xlsx_with_hyperlinks(file2)
                   if file2.name.lower().endswith(('.xlsx', '.xls')) else read_file(file2))
        df1 = load_file1(read_file(file1))
        df2 = load_file2(raw_df2)
        if df1.empty or df2.empty: st.stop()
        dup_df = detect_duplicates_f1(df1)
        st.session_state.dup_df = dup_df
        result_all = match_files(df1, df2)
        found = result_all[result_all['surat_jalan'].notna() &
                           result_all['surat_jalan'].str.startswith('http', na=False)].copy().reset_index(drop=True)
        matched_f1_idx = set(found['_f1_idx'].tolist())
        missing_rows = df1[~df1.index.isin(matched_f1_idx)].copy()
        missing = missing_rows.drop_duplicates(subset=['nopol', 'kuantum']).reset_index(drop=True)
        missing_detail = build_missing_with_suggestions(missing, df1, df2)
        st.session_state.missing_detail = missing_detail
        diff_rows, miss_rows = [], []
        for item in missing_detail:
            if item['kategori'] == 'kuantum_beda':
                diff_rows.append({'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                                   'Kuantum di File 2': item['info'], 'Status': '⚠️ Kuantum tidak cocok'})
            else:
                miss_rows.append({'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                                   'Status': '❌ NOPOL tidak ada di File 2',
                                   'Saran NOPOL (Kuantum Cocok)': (
                                       ', '.join([f"{s['nopol_f2']} ({s['similarity']}%)" for s in item['saran']])
                                       if item['saran'] else '-')})
        st.session_state.result_df     = found
        st.session_state.missing_df    = missing
        st.session_state.nopol_diff_df = pd.DataFrame(diff_rows)
        st.session_state.nopol_miss_df = pd.DataFrame(miss_rows)
        st.session_state.df2_debug     = df2
        st.session_state.df1_debug     = df1
        st.session_state.active_preview = None
        st.session_state.saran_preview  = {}
        st.session_state.dup_prev_active = {}
        st.session_state.processed      = True

    n_dup_groups = (len(dup_df[['nopol', 'kuantum']].drop_duplicates()) if not dup_df.empty else 0)
    n_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')
    st.balloons()
    st.success(f"✅ {len(found)} link ditemukan dari {len(df1)} data · {len(missing)} tidak match · {n_dup_groups} duplikat · {n_mirip} saran mirip")
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.result_df is not None:
    found      = st.session_state.result_df
    missing    = st.session_state.missing_df
    nopol_diff = st.session_state.nopol_diff_df
    nopol_miss = st.session_state.nopol_miss_df
    df2_all    = st.session_state.df2_debug
    df1_all    = st.session_state.df1_debug
    dup_df     = st.session_state.dup_df if st.session_state.dup_df is not None else pd.DataFrame()
    missing_detail = st.session_state.missing_detail or []

    n_match      = len(found)
    n_diff_k     = len(nopol_diff) if nopol_diff is not None else 0
    n_miss_nopol = len(nopol_miss) if nopol_miss is not None else 0
    n_all_miss   = len(missing)
    n_dup_groups = len(dup_df[['nopol', 'kuantum']].drop_duplicates()) if not dup_df.empty else 0
    n_dup_rows   = len(dup_df) if not dup_df.empty else 0
    n_nopol_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')
    match_rate   = int(n_match / max(len(df1_all), 1) * 100) if df1_all is not None else 0
    n_cached     = cache_count()
    cached_mb    = cache_size_bytes() / 1024 / 1024

    # ── STAT CARDS ──
    st.markdown('<div class="sec-hdr"><span class="sec-num">02</span><span class="sec-title">Ringkasan Hasil</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-top-bar" style="background:linear-gradient(90deg,#2f9e44,#51cf66)"></div>
        <div class="stat-bg-icon">✅</div>
        <div class="stat-lbl">Link Ditemukan</div>
        <div class="stat-val" style="color:#2f9e44">{n_match}</div>
        <div class="stat-sub" style="color:#2f9e44">{match_rate}% match rate</div>
      </div>
      <div class="stat-card">
        <div class="stat-top-bar" style="background:linear-gradient(90deg,#7048e8,#9775fa)"></div>
        <div class="stat-bg-icon">🔁</div>
        <div class="stat-lbl">Duplikat File 1</div>
        <div class="stat-val" style="color:#7048e8">{n_dup_groups}</div>
        <div class="stat-sub" style="color:#7048e8">{n_dup_rows} baris total</div>
      </div>
      <div class="stat-card">
        <div class="stat-top-bar" style="background:linear-gradient(90deg,#e67700,#fcc419)"></div>
        <div class="stat-bg-icon">⚠️</div>
        <div class="stat-lbl">Kuantum Beda</div>
        <div class="stat-val" style="color:#e67700">{n_diff_k}</div>
        <div class="stat-sub" style="color:#e67700">NOPOL ada, qty ≠</div>
      </div>
      <div class="stat-card">
        <div class="stat-top-bar" style="background:linear-gradient(90deg,#e03131,#ff6b6b)"></div>
        <div class="stat-bg-icon">❌</div>
        <div class="stat-lbl">NOPOL Tidak Ada</div>
        <div class="stat-val" style="color:#e03131">{n_miss_nopol}</div>
        <div class="stat-sub" style="color:#e03131">{n_nopol_mirip} ada saran</div>
      </div>
      <div class="stat-card">
        <div class="stat-top-bar" style="background:linear-gradient(90deg,#3b5bdb,#74c0fc)"></div>
        <div class="stat-bg-icon">💾</div>
        <div class="stat-lbl">Cache Disk</div>
        <div class="stat-val" style="color:#3b5bdb">{n_cached}</div>
        <div class="stat-sub" style="color:#3b5bdb">{cached_mb:.1f} MB di disk</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if n_dup_groups > 0:
        st.markdown(f'<div class="alert a-violet"><span class="alert-ico">🔁</span><div><b>{n_dup_groups} kombinasi duplikat</b> ({n_dup_rows} baris) di File 1. Nama file dibedakan <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.</div></div>', unsafe_allow_html=True)
    if n_nopol_mirip > 0:
        st.markdown(f'<div class="alert a-sky"><span class="alert-ico">🔍</span><div><b>{n_nopol_mirip} data</b> punya saran NOPOL mirip dengan kuantum cocok.</div></div>', unsafe_allow_html=True)
    if n_match == 0:
        st.markdown('<div class="alert a-error"><span class="alert-ico">⚠️</span><div><b>Tidak ada data yang match.</b> Pastikan format NOPOL &amp; KUANTUM konsisten di kedua file.</div></div>', unsafe_allow_html=True)

    # ── TABS ──
    st.markdown('<div class="sec-hdr"><span class="sec-num">03</span><span class="sec-title">Detail &amp; Download</span><span class="sec-line"></span></div>', unsafe_allow_html=True)

    tab1, tab_dup, tab2, tab3, tab4 = st.tabs([
        f"✅ Match ({n_match})",
        f"🔁 Duplikat ({n_dup_groups}g · {n_dup_rows}b)",
        f"⚠️ Kuantum Beda ({n_diff_k})",
        f"❌ NOPOL Tidak Ada ({n_miss_nopol})",
        f"🔴 Semua Tidak Match ({n_all_miss})",
    ])

    # ── TAB 1: MATCH ──────────────────────────────────────────────────────
    with tab1:
        if len(found) == 0:
            st.markdown('<div class="empty-state"><div class="ico">🔍</div><h3>Tidak Ada Data yang Match</h3><p>Tidak ada kombinasi NOPOL + Kuantum yang cocok antara File 1 dan File 2.</p></div>', unsafe_allow_html=True)
        else:
            sc1, sc2 = st.columns([3, 9])
            with sc1:
                search = st.text_input('Filter', placeholder='🔍  Ketik NOPOL…', label_visibility='collapsed', key='search_found')
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(re.escape(norm_nopol(search.strip())), na=False, case=False)].reset_index(drop=True)
            with sc2:
                st.markdown(f'<div style="padding:11px 4px;font-size:.79rem;color:#7b82b8">Menampilkan <b style="color:#1a1d2e">{len(disp)}</b> dari <b style="color:#1a1d2e">{len(found)}</b> surat jalan</div>', unsafe_allow_html=True)

            ac1, ac2, ac3, ac4 = st.columns([2, 2, 2, 6])
            with ac1: do_zip     = st.button('📦 Download ZIP', use_container_width=True, key='btn_zip')
            with ac2: do_merge   = st.button('📄 Gabung PDF',   use_container_width=True, key='btn_merge')
            with ac3: do_preload = st.button('⚡ Pre-load',     use_container_width=True, key='btn_preload')
            with ac4:
                n_c2 = sum(1 for _, r in disp.iterrows() if cache_has(r['surat_jalan']))
                pct_c = int(n_c2 / max(len(disp), 1) * 100)
                color = "#2f9e44" if pct_c == 100 else ("#e67700" if pct_c > 0 else "#7b82b8")
                sz_mb = cache_size_bytes() / 1024 / 1024
                st.markdown(f'<div class="cache-info">💾 Cache Disk: <b style="color:{color}">{n_c2}/{len(disp)}</b> ({pct_c}%) · {sz_mb:.1f} MB {"&nbsp;· ✅ Semua siap!" if pct_c==100 else "&nbsp;· Gunakan ⚡ Pre-load"}</div>', unsafe_allow_html=True)

            if do_preload and len(disp) > 0:
                needed = [r['surat_jalan'] for _, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                if not needed:
                    st.success('✅ Semua sudah di cache!')
                else:
                    tasks_pre = [{'idx': i, 'nopol': r['nopol'], 'kuantum': int(r['kuantum']),
                                  'link': r['surat_jalan'], 'dup_label': ''}
                                 for i, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                    pb = st.progress(0); stxt = st.empty(); ok_n = fail_n = done_n = 0
                    for batch_start in range(0, len(tasks_pre), DOWNLOAD_BATCH_SIZE):
                        batch = tasks_pre[batch_start: batch_start + DOWNLOAD_BATCH_SIZE]
                        with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
                            futs = {ex.submit(_worker_to_disk, t): t for t in batch}
                            for fut in as_completed(futs):
                                res = fut.result()
                                if res['ok']: ok_n += 1
                                else: fail_n += 1
                                done_n += 1
                                pb.progress(done_n / len(tasks_pre))
                                stxt.markdown(f"Pre-load **{done_n}/{len(tasks_pre)}** — ✅ {ok_n} · ❌ {fail_n}")
                        gc.collect()
                    stxt.success(f'✅ Selesai: {ok_n} berhasil, {fail_n} gagal · Cache: {cache_size_bytes()/1024/1024:.1f} MB')

            # ── ZIP ──
            if do_zip and len(disp) > 0:
                not_cached = [r['surat_jalan'] for _, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                if not_cached:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': int(r['kuantum']),
                                 'link': r['surat_jalan'], 'dup_label': ''}
                               for i, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                    ok_rows, fl = run_bulk_download(rows_dl, 'ZIP')
                    if fl:
                        with st.expander(f'⚠️ {len(fl)} gagal unduh'):
                            for f_name in fl: st.markdown(f'`{f_name}`')
                file_tasks = []
                for i, r in disp.iterrows():
                    if cache_has(r['surat_jalan']):
                        data_peek = cache_get(r['surat_jalan']); ext = infer_extension(data_peek); del data_peek
                        is_dup = (not dup_df.empty and ((dup_df['nopol'] == r['nopol']) & (dup_df['kuantum'] == r['kuantum'])).any())
                        dup_label = f'_DUPLIKAT{int(r["_link_no"])}' if is_dup and r["_link_no"] > 1 else ''
                        fname = make_safe_filename(r['nopol'], int(r['kuantum']), i, ext, total=len(disp), dup_label=dup_label)
                        file_tasks.append({'name': fname, 'link': r['surat_jalan']})
                if file_tasks:
                    with st.spinner(f'📦 Membuat ZIP {len(file_tasks)} file di disk…'):
                        zip_path = build_zip_to_disk(file_tasks)
                    if zip_path and zip_path.exists():
                        zip_size = zip_path.stat().st_size
                        st.markdown(f'<div class="alert a-success"><span class="alert-ico">📦</span><div><b>{len(file_tasks)} file siap</b> · ZIP {zip_size//1024:,} KB</div></div>', unsafe_allow_html=True)
                        with open(zip_path, 'rb') as zf:
                            st.download_button(f'💾 Simpan ZIP ({len(file_tasks)} file · {zip_size//1024:,} KB)', zf.read(), 'surat_jalan.zip', 'application/zip', key='dl_zip_r')
                        try: zip_path.unlink()
                        except: pass
                else:
                    st.warning('⚠️ Tidak ada file yang berhasil di-cache untuk di-ZIP.')

            # ── MERGE PDF ──
            if do_merge and len(disp) > 0:
                not_cached = [r['surat_jalan'] for _, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                if not_cached:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': int(r['kuantum']),
                                 'link': r['surat_jalan'], 'dup_label': ''}
                               for i, r in disp.iterrows() if not cache_has(r['surat_jalan'])]
                    ok_rows, fail_dl = run_bulk_download(rows_dl, 'PDF')
                    if fail_dl:
                        with st.expander(f'⚠️ {len(fail_dl)} tidak ikut'):
                            for f_name in fail_dl: st.markdown(f'`{f_name}`')
                links_ordered = [r['surat_jalan'] for _, r in disp.iterrows() if cache_has(r['surat_jalan'])]
                if links_ordered:
                    with st.spinner(f'📄 Menggabungkan {len(links_ordered)} file ke PDF…'):
                        merged_path = merge_pdfs_to_disk(links_ordered)
                    if merged_path and merged_path.exists():
                        merged_size = merged_path.stat().st_size
                        st.markdown(f'<div class="alert a-success"><span class="alert-ico">📄</span><div><b>{len(links_ordered)} file digabung</b> · PDF {merged_size//1024:,} KB</div></div>', unsafe_allow_html=True)
                        with open(merged_path, 'rb') as mf:
                            st.download_button(f'💾 Simpan PDF ({len(links_ordered)} hal · {merged_size//1024:,} KB)', mf.read(), 'surat_jalan_gabungan.pdf', 'application/pdf', key='dl_merged')
                        try: merged_path.unlink()
                        except: pass
                    else:
                        st.error('❌ Gagal membuat PDF. Pastikan `pypdf`, `reportlab`, `Pillow` terinstall.')

            # ── TABLE ──
            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            hcols = st.columns([0.5, 2.5, 1.3, 0.7, 1.8, 0.7, 2])
            for col, lbl in zip(hcols, ['#', 'NOPOL', 'Kuantum', 'Link #', 'Drive', '👁', '⬇️']):
                col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)
            st.markdown('<hr class="row-div">', unsafe_allow_html=True)

            for i, row in disp.iterrows():
                nopol = row['nopol']; kuantum = int(row['kuantum']); link = row['surat_jalan']
                link_no = int(row.get('_link_no', 1)); fid = extract_fid(link)
                is_dup = (not dup_df.empty and ((dup_df['nopol'] == nopol) & (dup_df['kuantum'] == kuantum)).any())
                cols = st.columns([0.5, 2.5, 1.3, 0.7, 1.8, 0.7, 2])
                cols[0].markdown(f'<span style="font-size:.73rem;color:#a8aed6">#{i+1}</span>', unsafe_allow_html=True)
                dup_badge = ' <span style="background:var(--violet-pale);color:#7048e8;font-size:.6rem;padding:1px 5px;border-radius:5px;font-weight:800">DUP</span>' if is_dup else ''
                cols[1].markdown(f'<span class="np {"np-dup" if is_dup else ""}">{nopol}</span>{dup_badge}', unsafe_allow_html=True)
                cols[2].markdown(f'<span style="font-family:var(--mono);font-size:.83rem;color:#3b5bdb;font-weight:600">{kuantum:,}</span>', unsafe_allow_html=True)
                cols[3].markdown(f'<span style="font-size:.7rem;color:#a8aed6">#{link_no}</span>', unsafe_allow_html=True)
                if fid: cols[4].markdown(f'[🔗 Buka](https://drive.google.com/file/d/{fid}/view)')
                else:   cols[4].markdown(f'[🔗 Buka]({link})')
                with cols[5]:
                    if st.button('👁️✕' if st.session_state.active_preview == i else '👁️', key=f'v_{i}'):
                        st.session_state.active_preview = (None if st.session_state.active_preview == i else i)
                        st.rerun()
                with cols[6]:
                    dup_label = f'_DUPLIKAT{link_no}' if link_no > 1 else ''
                    if cache_has(link):
                        cached = cache_get(link); ext = infer_extension(cached)
                        fname = make_safe_filename(nopol, kuantum, i, ext, total=len(disp), dup_label=dup_label)
                        st.download_button(f'⬇️ .{ext.upper()}', cached, fname,
                                           'application/pdf' if ext == 'pdf' else f'image/{ext}', key=f'd_{i}')
                        del cached
                    else:
                        if st.button('⬇️ Unduh', key=f'db_{i}'):
                            with st.spinner(f'Mengunduh {nopol}…'):
                                ct = download_file(link)
                            if ct:
                                cache_put(link, ct); ext = infer_extension(ct)
                                fname = make_safe_filename(nopol, kuantum, i, ext, total=len(disp), dup_label=dup_label)
                                st.download_button(f'💾 .{ext.upper()}', ct, fname,
                                                   'application/pdf' if ext == 'pdf' else f'image/{ext}', key=f'ds_{i}')
                                del ct
                            else:
                                st.error('❌ Gagal — file private/expired.')

                if st.session_state.active_preview == i:
                    purl = to_preview(link)
                    if purl:
                        import streamlit.components.v1 as components
                        st.markdown(f'<div class="alert a-sky" style="margin-top:8px"><span class="alert-ico">👁️</span><div>Preview — <b>{nopol}</b> · {kuantum:,} <a href="{purl}" target="_blank" style="margin-left:8px;font-size:.76rem;color:#3b5bdb;font-weight:700">↗ Tab baru</a></div></div>', unsafe_allow_html=True)
                        components.html(f'<iframe src="{purl}" width="100%" height="680" style="border:2px solid #a5d8ff;border-radius:14px;background:#fff" allow="autoplay"></iframe>', height=700)
                    else:
                        st.error('Link preview tidak valid.')
                if i < len(disp) - 1:
                    st.markdown('<hr class="row-div">', unsafe_allow_html=True)

    # ── TAB DUP ──────────────────────────────────────────────────────────
    with tab_dup:
        if dup_df.empty:
            st.markdown('<div class="empty-state"><div class="ico">🎉</div><h3>Tidak Ada Duplikat!</h3><p>Semua kombinasi NOPOL + Kuantum di File 1 adalah unik.</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert a-violet"><span class="alert-ico">🔁</span><div><b>{n_dup_groups} kombinasi duplikat</b> ({n_dup_rows} baris). Dibedakan dengan label <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.</div></div>', unsafe_allow_html=True)
            sd_dup = st.text_input('', placeholder='🔍  Filter NOPOL duplikat…', label_visibility='collapsed', key='sd_dup')
            dza, dzb, _ = st.columns([2, 2, 8])
            with dza: do_zip_dup   = st.button('📦 ZIP Duplikat', use_container_width=True, key='btn_zip_dup')
            with dzb: do_merge_dup = st.button('📄 PDF Duplikat', use_container_width=True, key='btn_merge_dup')

            all_dup_rows = []
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                lf = found[(found['nopol'] == nopol) & (found['kuantum'] == kuantum)]['surat_jalan'].tolist()
                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    bk = int(drow['baris_ke'])
                    lnk = None if not lf else (lf[i_row-1] if i_row <= len(lf) else lf[0])
                    all_dup_rows.append({'nopol': nopol, 'kuantum': int(kuantum), 'baris_ke': bk, 'dup_label': f'_DUPLIKAT{bk}', 'link': lnk})

            if do_zip_dup:
                vr = [r for r in all_dup_rows if r['link']]
                if not vr: st.warning('⚠️ Tidak ada link.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']} for i, r in enumerate(vr)]
                    ok_rows, fl = run_bulk_download(rows_dl, 'Duplikat ZIP')
                    file_tasks = [{'name': make_safe_filename(r['nopol'], r['kuantum'], i,
                                                               infer_extension(cache_get(r['link'])),
                                                               total=len(vr), dup_label=r['dup_label']),
                                   'link': r['link']} for i, r in enumerate(vr) if cache_has(r['link'])]
                    if file_tasks:
                        zip_path = build_zip_to_disk(file_tasks)
                        if zip_path:
                            with open(zip_path, 'rb') as zf:
                                st.download_button(f'💾 ZIP Duplikat ({len(file_tasks)} file)', zf.read(), 'duplikat.zip', 'application/zip', key='dl_zip_dup_r')
                            try: zip_path.unlink()
                            except: pass
                    if fl:
                        with st.expander(f'❌ {len(fl)} gagal'):
                            for f_name in fl: st.markdown(f'`{f_name}`')

            if do_merge_dup:
                vr = [r for r in all_dup_rows if r['link']]
                if not vr: st.warning('⚠️ Tidak ada link.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']} for i, r in enumerate(vr)]
                    ok_rows, fl = run_bulk_download(rows_dl, 'Duplikat PDF')
                    links_ord = [r['link'] for r in vr if cache_has(r['link'])]
                    if links_ord:
                        with st.spinner('Menggabungkan…'):
                            merged_path = merge_pdfs_to_disk(links_ord)
                        if merged_path:
                            with open(merged_path, 'rb') as mf:
                                st.download_button('💾 PDF Duplikat', mf.read(), 'duplikat.pdf', 'application/pdf', key='dl_merge_dup_r')
                            try: merged_path.unlink()
                            except: pass
                        else:
                            st.error('❌ Gagal PDF.')
                    if fl:
                        with st.expander(f'⚠️ {len(fl)} gagal'):
                            for f_name in fl: st.markdown(f'`{f_name}`')

            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            row_counter = 0
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                if sd_dup.strip() and norm_nopol(sd_dup.strip()) not in nopol: continue
                lf = found[(found['nopol'] == nopol) & (found['kuantum'] == kuantum)]['surat_jalan'].tolist()
                st.markdown(f'<div class="dup-group"><div class="dup-group-header"><span class="np np-dup">{nopol}</span><span style="color:#3d4066;font-size:.8rem;font-family:var(--mono);font-weight:600">{int(kuantum):,}</span><span style="background:#ffd8d8;color:#c62222;border-radius:7px;padding:2px 9px;font-size:.7rem;font-weight:800">Muncul {len(grp)}×</span><span style="background:var(--blue-pale);color:var(--blue);border-radius:7px;padding:2px 9px;font-size:.7rem;font-weight:800">{len(lf)} link di File 2</span></div>', unsafe_allow_html=True)
                dh = st.columns([0.6, 1.8, 2.2, 2, 0.8, 1.8])
                for col, lbl in zip(dh, ['Ke-', 'NOPOL', 'Label', 'Drive', '👁', '⬇️']):
                    col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)
                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    bk = int(drow['baris_ke']); dlbl = f'_DUPLIKAT{bk}'
                    lnk = None if not lf else (lf[i_row-1] if i_row <= len(lf) else lf[0])
                    fid = extract_fid(lnk) if lnk else None
                    uid = f'dup_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}_{bk}'
                    cols = st.columns([0.6, 1.8, 2.2, 2, 0.8, 1.8])
                    cols[0].markdown(f'<b style="color:#7048e8;font-family:var(--mono)">{bk}</b>', unsafe_allow_html=True)
                    cols[1].markdown(f'<span class="np np-dup">{nopol}</span>', unsafe_allow_html=True)
                    cols[2].markdown(f'<code style="background:var(--violet-lt);color:#7048e8;padding:2px 8px;border-radius:6px;font-size:.76rem;border:1px solid var(--violet-pale)">{dlbl}</code>', unsafe_allow_html=True)
                    if lnk and fid: cols[3].markdown(f'[🔗 Drive](https://drive.google.com/file/d/{fid}/view)')
                    elif lnk:       cols[3].markdown(f'[🔗 Buka]({lnk})')
                    else:           cols[3].markdown('<span style="color:#a8aed6">— Tidak ada</span>', unsafe_allow_html=True)
                    with cols[4]:
                        if lnk:
                            pgk = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                            isap = (st.session_state.dup_prev_active.get(pgk) == bk)
                            if st.button('👁️✕' if isap else '👁️', key=f'dprev_{uid}'):
                                st.session_state.dup_prev_active[pgk] = (None if isap else bk)
                                st.rerun()
                    with cols[5]:
                        if lnk:
                            if cache_has(lnk):
                                cached = cache_get(lnk); ext = infer_extension(cached)
                                fname = make_safe_filename(nopol, kuantum, row_counter, ext, total=n_dup_rows, dup_label=dlbl)
                                st.download_button(f'⬇️ .{ext.upper()}', cached, fname,
                                                   'application/pdf' if ext == 'pdf' else f'image/{ext}', key=f'ddl_{uid}')
                                del cached
                            else:
                                if st.button('⬇️ Unduh', key=f'ddlb_{uid}'):
                                    with st.spinner('Mengunduh…'):
                                        ct = download_file(lnk)
                                    if ct:
                                        cache_put(lnk, ct); ext = infer_extension(ct)
                                        fname = make_safe_filename(nopol, kuantum, row_counter, ext, total=n_dup_rows, dup_label=dlbl)
                                        st.download_button(f'💾 .{ext.upper()}', ct, fname,
                                                           'application/pdf' if ext == 'pdf' else f'image/{ext}', key=f'ddls_{uid}')
                                        del ct
                                    else:
                                        st.error('❌ Gagal.')
                        else:
                            st.markdown('`—`')
                    pgk = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                    if lnk and st.session_state.dup_prev_active.get(pgk) == bk:
                        purl = to_preview(lnk)
                        if purl:
                            import streamlit.components.v1 as components
                            st.markdown(f'<div class="alert a-sky" style="margin-top:8px"><span class="alert-ico">👁️</span><div>Preview — <b>{nopol}</b> · <code style="color:#7048e8">{dlbl}</code> · <a href="{purl}" target="_blank" style="font-size:.76rem;font-weight:700;color:#3b5bdb">↗ Tab baru</a></div></div>', unsafe_allow_html=True)
                            components.html(f'<iframe src="{purl}" width="100%" height="680" style="border:2px solid var(--violet-pale);border-radius:14px;background:#fff" allow="autoplay"></iframe>', height=700)
                        else:
                            st.error('Link preview tidak valid.')
                    row_counter += 1
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")

            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            exp_dup = dup_df[['nopol', 'kuantum', 'baris_ke', 'jumlah_duplikat']].copy()
            exp_dup.columns = ['NOPOL', 'Kuantum', 'Baris ke-', 'Total Duplikat']
            exp_dup['Label File'] = exp_dup['Baris ke-'].apply(lambda x: f'_DUPLIKAT{int(x)}')
            ec, _ = st.columns([2, 10])
            with ec:
                st.download_button('📥 Export CSV', exp_dup.to_csv(index=False).encode('utf-8'), 'duplikat.csv', 'text/csv', key='dl_dup')
            st.dataframe(exp_dup, use_container_width=True, hide_index=True)

    # ── TAB 2: KUANTUM BEDA ──────────────────────────────────────────────
    with tab2:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown('<div class="empty-state"><div class="ico">🎉</div><h3>Semua Kuantum Cocok!</h3><p>Tidak ada NOPOL dengan kuantum berbeda di File 2.</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert a-warn"><span class="alert-ico">⚠️</span><div><b>{len(nopol_diff)} data</b> — NOPOL ditemukan di File 2 tapi kuantumnya tidak cocok.</div></div>', unsafe_allow_html=True)
            sc, _ = st.columns([3, 9])
            with sc:
                sd = st.text_input('', placeholder='🔍 Filter NOPOL…', label_visibility='collapsed', key='sd')
            dd = nopol_diff.copy()
            if sd.strip():
                dd = dd[dd['NOPOL'].str.contains(re.escape(norm_nopol(sd)), na=False, case=False)].reset_index(drop=True)
            st.dataframe(dd, use_container_width=True, hide_index=True)
            ca, _ = st.columns([2, 10])
            with ca:
                st.download_button('📥 Export CSV', dd.to_csv(index=False).encode('utf-8'), 'kuantum_beda.csv', 'text/csv', key='dl_a')

    # ── TAB 3: NOPOL TIDAK ADA ───────────────────────────────────────────
    with tab3:
        miss_items = [x for x in missing_detail if x['kategori'] in ('nopol_mirip', 'tidak_ada')]
        if not miss_items:
            st.markdown('<div class="empty-state"><div class="ico">🎉</div><h3>Semua NOPOL Ditemukan!</h3></div>', unsafe_allow_html=True)
        else:
            n_mirip2    = sum(1 for x in miss_items if x['kategori'] == 'nopol_mirip')
            n_tdk_ada   = sum(1 for x in miss_items if x['kategori'] == 'tidak_ada')
            st.markdown(f'<div class="alert a-error"><span class="alert-ico">❌</span><div><b>{len(miss_items)} NOPOL tidak ada di File 2.</b> &nbsp;🔍 <b>{n_mirip2}</b> punya saran mirip · 🚫 <b>{n_tdk_ada}</b> tanpa saran</div></div>', unsafe_allow_html=True)
            fc1, fc2 = st.columns([3, 5])
            with fc1:
                sm = st.text_input('', placeholder='🔍 Filter NOPOL…', label_visibility='collapsed', key='sm')
            with fc2:
                min_sim = st.slider('Threshold Kemiripan (%)', 30, 90, 50, 5, key='sim_slider')

            for item_idx, item in enumerate(miss_items):
                nopol = item['nopol']; kuantum = item['kuantum']
                if sm.strip() and norm_nopol(sm.strip()) not in nopol: continue
                saran_f = [s for s in item['saran'] if s['similarity'] >= min_sim]
                has_s = bool(saran_f)
                bc = '#dce4ff' if has_s else '#ffe3e3'; bc2v = '#3b5bdb' if has_s else '#c62222'
                bl = '#4c6ef5' if has_s else '#e03131'
                st.markdown(f'<div style="background:#fff;border:2px solid {bc};border-left:4px solid {bl};border-radius:14px;padding:13px 18px;margin:12px 0;box-shadow:var(--shadow-sm)"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span class="np">{nopol}</span><span style="color:#3d4066;font-size:.79rem;font-family:var(--mono);font-weight:600">{kuantum:,}</span><span style="background:{bc};color:{bc2v};border-radius:7px;padding:2px 9px;font-size:.7rem;font-weight:800">{"🔍 " + str(len(saran_f)) + " saran" if has_s else "🚫 Tidak ada saran"}</span></div></div>', unsafe_allow_html=True)
                if saran_f:
                    sh = st.columns([0.4, 2.5, 1.5, 1.3, 2.5])
                    for col, lbl in zip(sh, ['#', 'NOPOL File 2', 'Kemiripan', 'Kuantum', 'Aksi']):
                        col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)
                    for s_idx, saran in enumerate(saran_f):
                        sk = f'saran_{item_idx}_{s_idx}'
                        sc0, sc1, sc2, sc3, sc4 = st.columns([0.4, 2.5, 1.5, 1.3, 2.5])
                        sim = saran['similarity']
                        sc0.markdown(f'`{s_idx+1}`')
                        sc1.markdown(f'<span class="np">{saran["nopol_f2"]}</span>', unsafe_allow_html=True)
                        sc2.markdown(f'<span class="sim {"sim-hi" if sim>=80 else "sim-md" if sim>=65 else "sim-lo"}">{sim}%</span>', unsafe_allow_html=True)
                        sc3.markdown(f'<span style="font-family:var(--mono);font-weight:600;color:#3b5bdb">{saran["kuantum"]:,}</span>', unsafe_allow_html=True)
                        with sc4:
                            cp, cd = st.columns(2)
                            with cp:
                                pa = st.session_state.saran_preview.get(f'item_{item_idx}') == s_idx
                                if st.button('👁️✕' if pa else '👁️', key=f'sprev_{sk}', use_container_width=True):
                                    st.session_state.saran_preview[f'item_{item_idx}'] = (None if pa else s_idx)
                                    st.rerun()
                            with cd:
                                ls = saran['surat_jalan']
                                if cache_has(ls):
                                    cs = cache_get(ls); ext_s = infer_extension(cs)
                                    fn_s = make_safe_filename(saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                    st.download_button(f'⬇️ .{ext_s.upper()}', cs, fn_s,
                                                       'application/pdf' if ext_s == 'pdf' else f'image/{ext_s}',
                                                       key=f'sdl_c_{sk}', use_container_width=True)
                                    del cs
                                else:
                                    if st.button('⬇️ Unduh', key=f'sdl_{sk}', use_container_width=True):
                                        with st.spinner('Mengunduh…'):
                                            ct_s = download_file(ls)
                                        if ct_s:
                                            cache_put(ls, ct_s); ext_s = infer_extension(ct_s)
                                            fn_s = make_safe_filename(saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                            st.download_button(f'💾 .{ext_s.upper()}', ct_s, fn_s,
                                                               'application/pdf' if ext_s == 'pdf' else f'image/{ext_s}',
                                                               key=f'sdl_s_{sk}', use_container_width=True)
                                            del ct_s
                                        else:
                                            st.error('❌ Gagal.')
                        if st.session_state.saran_preview.get(f'item_{item_idx}') == s_idx:
                            purl_s = to_preview(saran['surat_jalan'])
                            if purl_s:
                                import streamlit.components.v1 as components
                                sc_c = '#2f9e44' if sim >= 80 else '#e67700' if sim >= 65 else '#e03131'
                                st.markdown(f'<div class="alert a-sky" style="margin:8px 0"><span class="alert-ico">👁️</span><div>Preview — <b>{saran["nopol_f2"]}</b> · <b style="color:{sc_c}">{sim}%</b></div></div>', unsafe_allow_html=True)
                                components.html(f'<iframe src="{purl_s}" width="100%" height="680" style="border:2px solid #a5d8ff;border-radius:14px;background:#fff" allow="autoplay"></iframe>', height=700)

    # ── TAB 4: SEMUA TIDAK MATCH ─────────────────────────────────────────
    with tab4:
        if missing.empty:
            st.markdown('<div class="empty-state"><div class="ico">🏆</div><h3>Sempurna! Semua Data Match!</h3></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert a-error"><span class="alert-ico">🔴</span><div><b>{n_all_miss} kombinasi tidak match</b> total.</div></div>', unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Tidak Match", n_all_miss)
            m2.metric("⚠️ Kuantum Beda",   n_diff_k)
            m3.metric("❌ NOPOL Tidak Ada", n_miss_nopol)
            m4.metric("🔍 Ada Saran Mirip", n_nopol_mirip)
            all_m = missing.rename(columns={'nopol': 'NOPOL', 'kuantum': 'Kuantum File 1'}).copy()
            all_m['Kuantum File 1'] = all_m['Kuantum File 1'].astype(int)

            def get_ket(row):
                nopol = row['NOPOL']
                f2m = df2_all[df2_all['nopol'] == nopol]
                if len(f2m) > 0:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique().tolist())
                    d = ', '.join(map(str, ks[:5])) + (f' (+{len(ks)-5})' if len(ks) > 5 else '')
                    return f'⚠️ Kuantum beda (di File 2: {d})'
                saran = find_nopol_suggestions(nopol, int(row['Kuantum File 1']), df2_all, top_n=3)
                if saran:
                    top = saran[0]
                    return f'🔍 Saran: {top["nopol_f2"]} ({top["similarity"]}%)'
                return '❌ NOPOL tidak ada di File 2'

            with st.spinner('Menganalisis penyebab…'):
                all_m['Keterangan'] = all_m.apply(get_ket, axis=1)

            sa4c, _ = st.columns([3, 9])
            with sa4c:
                sa = st.text_input('', placeholder='🔍 Filter NOPOL…', label_visibility='collapsed', key='sa')
            if sa.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(re.escape(norm_nopol(sa)), na=False, case=False)].reset_index(drop=True)
            st.dataframe(all_m, use_container_width=True, hide_index=True)
            cde, _ = st.columns([2, 10])
            with cde:
                st.download_button('📥 Export CSV', all_m.to_csv(index=False).encode('utf-8'), 'semua_tidak_match.csv', 'text/csv', key='dl_c')

elif not st.session_state.processed:
    st.markdown('''
    <div class="empty-state" style="margin-top:28px">
      <div class="ico">📂</div>
      <h3>Upload File untuk Memulai</h3>
      <p>Upload <b>File 1</b> (daftar target) dan <b>File 2</b> (database surat jalan) di atas, lalu klik <b>⚙️ Proses &amp; Cocokkan Data</b>.</p>
    </div>
    ''', unsafe_allow_html=True)
