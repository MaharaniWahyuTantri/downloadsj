import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import re
import time
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher

st.set_page_config(
    page_title="SuratJalan — Bulk Downloader",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Modern, Responsive, Gen Z / Millennial vibes
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap');

/* ── RESET & BASE ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: #0d0f14;
  color: #e8eaf0;
}

.stApp { background: #0d0f14; }
.main .block-container {
  padding: clamp(12px, 4vw, 32px) clamp(12px, 4vw, 48px) 48px !important;
  max-width: 1280px !important;
}

/* ── NOISE OVERLAY ── */
.stApp::before {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
  opacity: 0.4;
}

/* ── AMBIENT GLOW ── */
.ambient-bg {
  position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.ambient-bg::before {
  content: '';
  position: absolute; width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
  top: -200px; left: -100px; border-radius: 50%;
}
.ambient-bg::after {
  content: '';
  position: absolute; width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%);
  bottom: -150px; right: -100px; border-radius: 50%;
}

/* ── HEADER ── */
.app-header {
  position: relative; z-index: 2;
  background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(16,185,129,0.08) 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: clamp(20px, 4vw, 36px) clamp(20px, 4vw, 40px);
  margin-bottom: clamp(16px, 3vw, 28px);
  backdrop-filter: blur(20px);
  overflow: hidden;
}
.app-header::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.6), rgba(16,185,129,0.4), transparent);
}
.app-header::after {
  content: '🚛';
  position: absolute; right: -10px; bottom: -20px;
  font-size: clamp(80px, 15vw, 140px); opacity: 0.05;
  transform: rotate(-10deg); pointer-events: none;
}
.header-eyebrow {
  font-size: 0.68rem; font-weight: 700; letter-spacing: 2.5px;
  text-transform: uppercase; color: #6366f1; margin-bottom: 8px;
}
.header-title {
  font-size: clamp(1.4rem, 4vw, 2.2rem);
  font-weight: 800; color: #f0f2f8; line-height: 1.15;
  margin-bottom: 8px;
}
.header-title span { color: #6366f1; }
.header-sub {
  font-size: clamp(0.78rem, 2vw, 0.92rem);
  color: #7b8094; line-height: 1.65; max-width: 560px;
}
.header-chips {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px;
}
.chip {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 100px; padding: 4px 12px;
  font-size: 0.72rem; font-weight: 600; color: #9ca3af;
  letter-spacing: 0.3px;
}
.chip-green { border-color: rgba(16,185,129,0.3); color: #10b981; background: rgba(16,185,129,0.08); }
.chip-blue  { border-color: rgba(99,102,241,0.3);  color: #818cf8; background: rgba(99,102,241,0.08); }
.chip-amber { border-color: rgba(245,158,11,0.3);  color: #fbbf24; background: rgba(245,158,11,0.08); }

/* ── SECTION LABELS ── */
.sec-label {
  display: flex; align-items: center; gap: 10px;
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 2px; color: #4b5563;
  margin: clamp(20px, 4vw, 32px) 0 clamp(12px, 2vw, 18px);
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,0.06); }
.sec-num {
  width: 22px; height: 22px; border-radius: 6px;
  background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.3);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; color: #818cf8; flex-shrink: 0;
}

/* ── UPLOAD CARDS ── */
.upload-zone {
  background: rgba(255,255,255,0.03);
  border: 1.5px dashed rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: clamp(16px, 3vw, 24px);
  transition: border-color 0.2s, background 0.2s;
  position: relative; overflow: hidden;
  margin-bottom: 16px;
}
.upload-zone:hover {
  border-color: rgba(99,102,241,0.4);
  background: rgba(99,102,241,0.04);
}
.upload-zone.active {
  border-color: rgba(16,185,129,0.5);
  border-style: solid;
  background: rgba(16,185,129,0.04);
}
.upload-zone-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
}
.uz-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
  flex-shrink: 0;
}
.uz-icon-blue  { background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.2); }
.uz-icon-green { background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.2); }
.uz-title { font-size: 0.9rem; font-weight: 700; color: #e2e4ee; }
.uz-sub   { font-size: 0.72rem; color: #6b7280; margin-top: 2px; }
.tag-row  { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 8px; }
.col-tag  {
  font-size: 0.67rem; font-weight: 600; padding: 3px 8px; border-radius: 5px;
  font-family: 'DM Mono', monospace;
}
.tag-required { background: rgba(99,102,241,0.15); color: #818cf8; border: 1px solid rgba(99,102,241,0.25); }
.tag-optional { background: rgba(255,255,255,0.05); color: #6b7280; border: 1px solid rgba(255,255,255,0.08); }
.file-ok {
  display: flex; align-items: center; gap: 8px;
  background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.25);
  border-radius: 10px; padding: 8px 12px; margin-top: 8px;
  font-size: 0.8rem; color: #10b981; font-weight: 600;
}

/* ── PROCESS BUTTON ── */
.stButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important; font-size: 0.85rem !important;
  border-radius: 12px !important;
  padding: 10px 20px !important;
  transition: all 0.2s !important;
  cursor: pointer !important;
}

/* Primary (process) button override via parent */
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  color: #fff !important; border: none !important;
  box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  box-shadow: 0 6px 28px rgba(99,102,241,0.5) !important;
  transform: translateY(-1px) !important;
}

/* Default buttons */
.stButton > button {
  background: rgba(255,255,255,0.05) !important;
  color: #c4c8d6 !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  box-shadow: none !important;
}
.stButton > button:hover {
  background: rgba(99,102,241,0.12) !important;
  border-color: rgba(99,102,241,0.35) !important;
  color: #a5b4fc !important;
}
.stButton > button:disabled {
  background: rgba(255,255,255,0.03) !important;
  color: #374151 !important;
  border-color: rgba(255,255,255,0.05) !important;
  cursor: not-allowed !important;
}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"] > section {
  background: transparent !important;
  border: none !important;
}
div[data-testid="stFileUploaderDropzone"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1.5px dashed rgba(99,102,241,0.25) !important;
  border-radius: 12px !important;
  padding: 16px !important;
  transition: all 0.2s !important;
}
div[data-testid="stFileUploaderDropzone"]:hover {
  border-color: rgba(99,102,241,0.5) !important;
  background: rgba(99,102,241,0.05) !important;
}
div[data-testid="stFileUploaderDropzone"] p { color: #6b7280 !important; font-size: 0.82rem !important; }
button[data-testid="baseButton-secondary"] {
  background: rgba(99,102,241,0.15) !important;
  border: 1px solid rgba(99,102,241,0.3) !important;
  color: #818cf8 !important;
  border-radius: 8px !important;
}

/* ── STAT CARDS ── */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(160px, 100%), 1fr));
  gap: clamp(8px, 2vw, 14px);
  margin: clamp(14px, 3vw, 22px) 0;
}
.stat-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 14px; padding: clamp(14px, 2.5vw, 20px);
  position: relative; overflow: hidden;
  transition: transform 0.2s, border-color 0.2s;
  cursor: default;
}
.stat-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.12);
}
.stat-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.stat-card.green::before { background: linear-gradient(90deg, #10b981, #34d399); }
.stat-card.blue::before  { background: linear-gradient(90deg, #6366f1, #818cf8); }
.stat-card.amber::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.stat-card.red::before   { background: linear-gradient(90deg, #ef4444, #f87171); }
.stat-card.orange::before{ background: linear-gradient(90deg, #f97316, #fb923c); }
.stat-bg-icon {
  position: absolute; right: -8px; bottom: -8px;
  font-size: 3rem; opacity: 0.06; pointer-events: none;
}
.stat-val {
  font-family: 'DM Mono', monospace; font-size: clamp(1.8rem, 4vw, 2.4rem);
  font-weight: 500; line-height: 1; margin-bottom: 6px;
}
.stat-lbl {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1px; color: #4b5563; margin-bottom: 3px;
}
.stat-sub { font-size: 0.68rem; font-weight: 600; }
.c-green  { color: #10b981; }
.c-blue   { color: #818cf8; }
.c-amber  { color: #fbbf24; }
.c-red    { color: #f87171; }
.c-orange { color: #fb923c; }

/* ── ALERT BOXES ── */
.alert {
  border-radius: 12px; padding: clamp(10px, 2vw, 14px) clamp(12px, 2.5vw, 18px);
  margin: 10px 0; font-size: 0.84rem; line-height: 1.65;
  display: flex; gap: 10px; align-items: flex-start;
  position: relative; overflow: hidden;
}
.alert::before {
  content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 3px;
}
.alert-icon { font-size: 1rem; flex-shrink: 0; margin-top: 2px; }
.alert.success { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); color: #6ee7b7; }
.alert.success::before { background: #10b981; }
.alert.warn    { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); color: #fcd34d; }
.alert.warn::before    { background: #f59e0b; }
.alert.error   { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.2);  color: #fca5a5; }
.alert.error::before   { background: #ef4444; }
.alert.info    { background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2); color: #a5b4fc; }
.alert.info::before    { background: #6366f1; }
.alert.purple  { background: rgba(139,92,246,0.08); border: 1px solid rgba(139,92,246,0.2); color: #c4b5fd; }
.alert.purple::before  { background: #8b5cf6; }
.alert.sky     { background: rgba(14,165,233,0.08); border: 1px solid rgba(14,165,233,0.2); color: #7dd3fc; }
.alert.sky::before     { background: #0ea5e9; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 14px !important;
  padding: 5px !important;
  gap: 3px !important;
  overflow-x: auto !important;
  flex-wrap: nowrap !important;
  scrollbar-width: thin !important;
  scrollbar-color: rgba(99,102,241,0.3) transparent !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 10px !important;
  font-size: clamp(0.72rem, 1.8vw, 0.82rem) !important;
  font-weight: 600 !important;
  padding: clamp(6px,1.5vw,9px) clamp(8px,2vw,14px) !important;
  color: #6b7280 !important;
  border: none !important;
  background: transparent !important;
  white-space: nowrap !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  transition: all 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #c4c8d6 !important; }
.stTabs [aria-selected="true"] {
  background: rgba(99,102,241,0.18) !important;
  color: #a5b4fc !important;
  font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── PROGRESS BAR ── */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, #6366f1, #10b981) !important;
  border-radius: 100px !important;
}
.stProgress > div > div {
  background: rgba(255,255,255,0.06) !important;
  border-radius: 100px !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 10px !important;
  color: #e2e4ee !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 0.85rem !important;
  padding: 10px 14px !important;
  transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
  border-color: rgba(99,102,241,0.5) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #4b5563 !important; }

/* ── SLIDER ── */
.stSlider > div > div > div > div { background: #6366f1 !important; }
.stSlider > div > div > div { background: rgba(255,255,255,0.08) !important; }

/* ── DATAFRAME ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden; }
div[data-testid="stDataFrame"] > div {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 12px !important;
}

/* ── EXPANDER ── */
details { background: rgba(255,255,255,0.02) !important; border-radius: 10px !important; border: 1px solid rgba(255,255,255,0.07) !important; }
summary { font-size: 0.82rem !important; color: #9ca3af !important; padding: 10px 14px !important; }

/* ── METRICS ── */
div[data-testid="stMetric"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 12px !important;
  padding: 14px !important;
}
div[data-testid="stMetricLabel"] { color: #6b7280 !important; font-size: 0.75rem !important; }
div[data-testid="stMetricValue"] { color: #e2e4ee !important; font-family: 'DM Mono', monospace !important; }

/* ── DOWNLOAD BUTTONS ── */
.stDownloadButton > button {
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-weight: 700 !important; font-size: 0.82rem !important;
  background: rgba(16,185,129,0.12) !important;
  border: 1px solid rgba(16,185,129,0.3) !important;
  border-radius: 10px !important;
  color: #6ee7b7 !important;
  padding: 9px 16px !important;
  transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
  background: rgba(16,185,129,0.22) !important;
  border-color: rgba(16,185,129,0.5) !important;
  box-shadow: 0 4px 16px rgba(16,185,129,0.2) !important;
  transform: translateY(-1px) !important;
}

/* ── NOPOL PILLS ── */
.np {
  display: inline-block;
  background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.25);
  color: #a5b4fc; border-radius: 7px;
  padding: 3px 10px; font-family: 'DM Mono', monospace; font-size: 0.82rem;
  font-weight: 500;
}
.np-dup {
  background: rgba(139,92,246,0.12); border-color: rgba(139,92,246,0.3);
  color: #c4b5fd;
}

/* ── ROW DIVIDER ── */
.row-div { border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 10px 0; }

/* ── SIM BADGE ── */
.sim {
  display: inline-block; border-radius: 7px;
  padding: 2px 9px; font-size: 0.72rem; font-weight: 700;
}
.sim-hi  { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.sim-md  { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
.sim-lo  { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.2); }

/* ── DUP GROUP CARD ── */
.dup-group {
  background: rgba(139,92,246,0.05);
  border: 1px solid rgba(139,92,246,0.15);
  border-radius: 14px; padding: 14px 18px; margin: 14px 0 6px;
}
.dup-group-title {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px;
}

/* ── EMPTY STATE ── */
.empty-state {
  text-align: center; padding: clamp(32px, 6vw, 60px) 24px;
  color: #4b5563;
}
.empty-state .icon { font-size: clamp(2rem, 5vw, 3.5rem); margin-bottom: 14px; opacity: 0.6; }
.empty-state h3 { font-size: 1rem; font-weight: 700; color: #6b7280; margin-bottom: 8px; }
.empty-state p  { font-size: 0.82rem; line-height: 1.65; max-width: 320px; margin: 0 auto; }

/* ── TABLE COLUMNS ── */
.col-hdr {
  font-size: 0.67rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.2px; color: #4b5563;
}

/* ── STEP BAR ── */
.stepbar {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; padding: clamp(12px,2.5vw,16px) clamp(16px,3vw,24px);
  margin-bottom: clamp(16px,3vw,24px); gap: 0; overflow: hidden;
}
.step-item { display: flex; align-items: center; gap: 8px; flex: 1; }
.step-dot {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700; position: relative; z-index: 1;
}
.step-dot.done   { background: #10b981; color: #fff; }
.step-dot.active { background: #6366f1; color: #fff; box-shadow: 0 0 0 5px rgba(99,102,241,0.2); }
.step-dot.idle   { background: rgba(255,255,255,0.05); color: #374151; border: 1.5px solid rgba(255,255,255,0.08); }
.step-txt .lbl { font-size: 0.8rem; font-weight: 700; }
.step-txt .sub { font-size: 0.65rem; margin-top: 1px; }
.lbl-done   { color: #10b981; }
.lbl-active { color: #818cf8; }
.lbl-idle   { color: #374151; }
.sub-done   { color: #065f46; }
.sub-active { color: #4338ca; }
.sub-idle   { color: #1f2937; }
.conn { flex: 1; height: 1.5px; background: rgba(255,255,255,0.06); }
.conn.done { background: linear-gradient(90deg, #10b981, #6366f1); }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
  background: #0a0c10 !important;
  border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] * { color: #9ca3af !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }
section[data-testid="stSidebar"] h2 { color: #e2e4ee !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 100px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.5); }

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── SUCCESS / ERROR / WARNING ── */
div[data-testid="stAlert"] {
  background: rgba(255,255,255,0.03) !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── MAIN MENU & FOOTER HIDE ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── RESPONSIVE ── */
@media (max-width: 640px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .stepbar { padding: 10px 12px; }
  .step-txt .sub { display: none; }
  .app-header::after { display: none; }
}
@media (max-width: 400px) {
  .stat-grid { grid-template-columns: 1fr 1fr; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# UTILITIES (logic unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def norm_nopol(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ''
    s = str(v).strip().upper()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'([A-Z])(\d)', r'\1 \2', s)
    s = re.sub(r'(\d)([A-Z])', r'\1 \2', s)
    return re.sub(r'\s+', ' ', s).strip()

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
    if not isinstance(link, str) or not link.strip():
        return None
    for p in [r'/file/d/([a-zA-Z0-9_-]+)', r'id=([a-zA-Z0-9_-]+)',
              r'/d/([a-zA-Z0-9_-]+)', r'open\?id=([a-zA-Z0-9_-]+)']:
        m = re.search(p, link.strip())
        if m and len(m.group(1)) >= 15:
            return m.group(1)
    return None

def to_preview(link):
    fid = extract_fid(link)
    return f'https://drive.google.com/file/d/{fid}/preview' if fid else None

def detect_file_type(content):
    if not content or len(content) < 4:
        return 'unknown'
    sig = content[:8]
    if sig[:4] == b'%PDF':              return 'pdf'
    if sig[:3] == b'\xff\xd8\xff':      return 'jpg'
    if sig[:8] == b'\x89PNG\r\n\x1a\n': return 'png'
    try:
        snippet = content[:2000].decode('utf-8', errors='ignore').lower()
        if '<html' in snippet or '<!doctype' in snippet:
            return 'html'
    except Exception:
        pass
    return 'unknown'

def _get_bytes(resp):
    return b''.join(resp.iter_content(chunk_size=65536))

def download_gdrive(fid, retries=4, timeout=45):
    if not fid:
        return None
    session = requests.Session()
    session.headers.update({'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    base_url = f'https://drive.google.com/uc?export=download&id={fid}'
    for attempt in range(retries):
        try:
            r1   = session.get(base_url, timeout=timeout, stream=True, allow_redirects=True)
            raw1 = _get_bytes(r1)
            if 'text/html' not in r1.headers.get('Content-Type', ''):
                if detect_file_type(raw1) != 'html' and len(raw1) > 512:
                    return raw1
            html = raw1.decode('utf-8', errors='ignore')
            m = re.search(r'name="confirm"\s+value="([^"]+)"', html)
            if m:
                r2 = session.get(f'{base_url}&confirm={m.group(1)}',
                                 timeout=timeout, stream=True, allow_redirects=True)
                raw2 = _get_bytes(r2)
                if detect_file_type(raw2) != 'html' and len(raw2) > 512:
                    return raw2
            for extra in ['&confirm=t', '']:
                r   = session.get(f'{base_url}{extra}', timeout=timeout,
                                  stream=True, allow_redirects=True)
                raw = _get_bytes(r)
                if detect_file_type(raw) != 'html' and len(raw) > 512:
                    return raw
        except Exception:
            pass
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return None

def download_file(link):
    if not isinstance(link, str) or not link.strip():
        return None
    fid = extract_fid(link)
    if fid:
        return download_gdrive(fid)
    try:
        r   = requests.get(link.strip(), timeout=45, stream=True,
                           headers={'User-Agent': 'Mozilla/5.0'})
        raw = _get_bytes(r)
        if detect_file_type(raw) != 'html' and len(raw) > 512:
            return raw
    except Exception:
        pass
    return None

def infer_extension(content, fallback='pdf'):
    return {'pdf':'pdf','jpg':'jpg','png':'png'}.get(
        detect_file_type(content) if content else 'x', fallback)

def make_safe_filename(nopol, kuantum, idx, ext, total=999, dup_label=''):
    safe = re.sub(r'[\\/:*?"<>|]', '_', str(nopol))
    pad  = len(str(max(total, 1)))
    no   = str(idx + 1).zfill(pad)
    return f'{no}_{safe}_{kuantum}{dup_label}.{ext}'

def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()

def img_bytes_to_pdf(img_bytes):
    tmp_path = None
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image as PILImage
        pil = PILImage.open(io.BytesIO(img_bytes))
        if pil.mode not in ('RGB', 'L'):
            pil = pil.convert('RGB')
        w_px, h_px = pil.size
        a4_w, a4_h = A4
        margin = 20
        scale  = min((a4_w - 2 * margin) / w_px, (a4_h - 2 * margin) / h_px)
        draw_w, draw_h = w_px * scale, h_px * scale
        x = (a4_w - draw_w) / 2
        y = (a4_h - draw_h) / 2
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            pil.save(tmp_path, format='PNG')
        pdf_buf = io.BytesIO()
        c = rl_canvas.Canvas(pdf_buf, pagesize=(a4_w, a4_h))
        c.drawImage(tmp_path, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True)
        c.save()
        pdf_buf.seek(0)
        return pdf_buf.read()
    except Exception:
        return None
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except: pass

def merge_pdfs(content_list):
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfWriter, PdfReader
        except ImportError:
            return None
    writer = PdfWriter()
    for ct in content_list:
        if not ct:
            continue
        ftype    = detect_file_type(ct)
        pdf_data = ct if ftype == 'pdf' else (
            img_bytes_to_pdf(ct) if ftype in ('jpg', 'png') else None)
        if pdf_data:
            try:
                for page in PdfReader(io.BytesIO(pdf_data)).pages:
                    writer.add_page(page)
            except Exception:
                continue
    if len(writer.pages) == 0:
        return None
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()

def read_file(f):
    return pd.read_csv(f) if f.name.lower().endswith('.csv') else pd.read_excel(f)

def load_file1(df):
    nc = find_col(df, ['nopol','nomor polisi','no pol','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan. Kolom: `{'`, `'.join(df.columns)}`")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan. Kolom: `{'`, `'.join(df.columns)}`")
        return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol']   = df[nc].apply(norm_nopol)
    out['kuantum'] = df[kc].apply(norm_kuantum)
    out = out[(out['nopol'] != '') & out['nopol'].notna()].dropna(subset=['kuantum'])
    return out[out['kuantum'] > 0].reset_index(drop=True)

def load_file2(raw_df):
    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame()
    frow = df.iloc[0].tolist()
    if any(str(v).upper().strip() in ['NOPOL','KUANTUM','FOTO SURAT JALAN','SURAT JALAN'] for v in frow):
        df.columns = [str(c).strip() for c in df.iloc[0]]
        df = df[1:].reset_index(drop=True)
    nc = find_col(df, ['nopol','nomor polisi','no pol','no truk','no.pol','nopolisi']) or find_col(df, ['pol'])
    kc = find_col(df, ['kuantum','quantum','tonase','tonage','qty','jumlah','volume','berat'])
    lc = find_col(df, ['surat jalan','suratjalan','foto surat','foto','link','url','drive','gdrive'])
    if not nc:
        st.error(f"❌ Kolom NOPOL tidak ditemukan di File 2.")
        return pd.DataFrame()
    if not kc:
        st.error(f"❌ Kolom KUANTUM tidak ditemukan di File 2.")
        return pd.DataFrame()
    if not lc:
        st.error(f"❌ Kolom SURAT JALAN tidak ditemukan di File 2.")
        return pd.DataFrame()
    out = pd.DataFrame()
    out['nopol']       = df[nc].apply(lambda x: norm_nopol(str(x)) if pd.notna(x) else '')
    out['kuantum']     = df[kc].apply(norm_kuantum)
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

def nopol_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_nopol_suggestions(nopol_f1, kuantum, df2, top_n=5, min_similarity=0.5):
    same_kuantum = df2[df2['kuantum'] == kuantum].copy()
    if same_kuantum.empty:
        return []
    results = []
    for _, row in same_kuantum.iterrows():
        sim = nopol_similarity(nopol_f1, row['nopol'])
        if sim >= min_similarity:
            results.append({
                'nopol_f2':    row['nopol'],
                'kuantum':     int(row['kuantum']),
                'surat_jalan': row['surat_jalan'],
                'similarity':  round(sim * 100, 1),
            })
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]

def build_missing_with_suggestions(missing_df, df1, df2):
    rows = []
    for _, row in missing_df.iterrows():
        nopol   = row['nopol']
        kuantum = int(row['kuantum'])
        f2_match = df2[df2['nopol'] == nopol]
        if len(f2_match) > 0:
            ks = sorted(f2_match['kuantum'].dropna().astype(int).unique().tolist())
            d  = ', '.join(map(str, ks[:8])) + (f' (+{len(ks)-8})' if len(ks) > 8 else '')
            rows.append({'nopol': nopol, 'kuantum': kuantum,
                         'kategori': 'kuantum_beda', 'info': d, 'saran': []})
        else:
            saran    = find_nopol_suggestions(nopol, kuantum, df2)
            kategori = 'nopol_mirip' if saran else 'tidak_ada'
            rows.append({'nopol': nopol, 'kuantum': kuantum,
                         'kategori': kategori, 'info': '', 'saran': saran})
    return rows

def detect_duplicates_f1(df1):
    key    = ['nopol', 'kuantum']
    counts = df1.groupby(key).size().reset_index(name='jumlah_duplikat')
    dup_keys = counts[counts['jumlah_duplikat'] > 1][key]
    if dup_keys.empty:
        return pd.DataFrame()
    merged = df1.merge(dup_keys, on=key, how='inner')
    merged = merged.merge(counts, on=key, how='left')
    merged['baris_ke'] = merged.groupby(key).cumcount() + 1
    return merged.reset_index(drop=True)

def match_files(df1, df2):
    df2_valid = df2[df2['surat_jalan'].str.startswith('http', na=False)].copy()
    pos_in_group = df1.groupby(['nopol', 'kuantum']).cumcount()
    result_rows = []
    for idx, row1 in df1.iterrows():
        pos = int(pos_in_group[idx])
        matches = df2_valid[
            (df2_valid['nopol']   == row1['nopol']) &
            (df2_valid['kuantum'] == row1['kuantum'])
        ].reset_index(drop=True)
        if len(matches) > 0:
            link_idx = min(pos, len(matches) - 1)
            mrow     = matches.iloc[link_idx]
            result_rows.append({
                'nopol':       row1['nopol'],
                'kuantum':     row1['kuantum'],
                'surat_jalan': mrow['surat_jalan'],
                '_f1_idx':     idx,
                '_link_no':    pos + 1,
            })
        else:
            result_rows.append({
                'nopol':       row1['nopol'],
                'kuantum':     row1['kuantum'],
                'surat_jalan': None,
                '_f1_idx':     idx,
                '_link_no':    0,
            })
    return pd.DataFrame(result_rows)

def _worker(task, cache_snapshot):
    link = task['link']
    ct   = cache_snapshot.get(link)
    if ct is None:
        ct = download_file(link)
    return {**task, 'content': ct}

def run_bulk_download(rows, label=''):
    cache_snapshot = dict(st.session_state.dl_cache)
    tasks = [{'idx': r['idx'], 'nopol': r['nopol'], 'kuantum': r['kuantum'],
               'link': r['link'], 'dup_label': r.get('dup_label', '')}
             for r in rows]

    prog_container = st.empty()
    with prog_container.container():
        prog_bar = st.progress(0)
        st.markdown(f"""
        <div class="alert info">
          <span class="alert-icon">⏳</span>
          <div><b>Mengunduh {label}…</b> Proses paralel 8 thread, harap tunggu.</div>
        </div>""", unsafe_allow_html=True)
        status_txt = st.empty()

    ok_files  = {}
    new_cache = {}
    fail_list = []
    done_n    = 0
    total     = len(tasks)

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(_worker, t, cache_snapshot): t for t in tasks}
        for fut in as_completed(futs):
            res = fut.result()
            ct  = res['content']
            if ct:
                new_cache[res['link']] = ct
                ext  = infer_extension(ct)
                fn   = make_safe_filename(res['nopol'], res['kuantum'], res['idx'],
                                          ext, total=total, dup_label=res['dup_label'])
                base, c = fn, 1
                while fn in ok_files:
                    fn = base.rsplit('.', 1)[0] + f'_{c}.' + base.rsplit('.', 1)[-1]
                    c += 1
                ok_files[fn] = ct
            else:
                fail_list.append(f"{res['nopol']} ({res['kuantum']}){res['dup_label']}")
            done_n += 1
            prog_bar.progress(done_n / total)
            pct = int(done_n / total * 100)
            status_txt.markdown(
                f"**{pct}%** — {done_n}/{total} diproses &nbsp;|&nbsp; "
                f"✅ **{len(ok_files)}** berhasil &nbsp;|&nbsp; ❌ **{len(fail_list)}** gagal")

    prog_container.empty()
    return ok_files, fail_list, new_cache

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for _k in ['result_df','missing_df','nopol_diff_df','nopol_miss_df',
           'active_preview','df2_debug','df1_debug','dl_cache',
           'dup_df','missing_detail','saran_preview','dup_prev_active','processed']:
    if _k not in st.session_state:
        st.session_state[_k] = None
if st.session_state.dl_cache       is None: st.session_state.dl_cache       = {}
if st.session_state.saran_preview  is None: st.session_state.saran_preview  = {}
if st.session_state.dup_prev_active is None: st.session_state.dup_prev_active = {}
if st.session_state.processed      is None: st.session_state.processed      = False

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 12px">
      <div style="font-size:2.2rem;margin-bottom:8px">🚛</div>
      <div style="font-weight:800;font-size:1rem;color:#e2e4ee">SuratJalan</div>
      <div style="font-size:0.7rem;color:#4b5563;margin-top:4px;letter-spacing:1px;text-transform:uppercase">Bulk Downloader v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    with st.expander("📋 Cara Penggunaan", expanded=True):
        st.markdown("""
        1. **Upload File 1** — Daftar target (NOPOL + Kuantum)
        2. **Upload File 2** — Database dengan link Google Drive
        3. Klik **Proses Data**
        4. Download sebagai **ZIP** atau **PDF Gabungan**
        """)

    with st.expander("📂 Format File"):
        st.markdown("""
        **File 1 — Target:**
        - Kolom wajib: `NOPOL` dan `KUANTUM`
        - Format: `.xlsx`, `.xls`, `.csv`

        **File 2 — Database:**
        - Kolom wajib: `NOPOL`, `KUANTUM`, `Link GDrive`
        - Nama kolom fleksibel (auto-detect)
        """)

    with st.expander("❓ FAQ"):
        st.markdown("""
        **File gagal download?**
        File mungkin *private* atau link *expired*.

        **Apa itu Duplikat File 1?**
        NOPOL+Kuantum muncul >1x. Setiap baris tetap bisa didownload dengan label berbeda.

        **Saran NOPOL dari mana?**
        Fuzzy matching — algoritma perbandingan teks antar NOPOL.
        """)

    st.divider()
    if st.session_state.processed and st.session_state.result_df is not None:
        n_cached  = len(st.session_state.dl_cache)
        total_lnk = len(st.session_state.result_df)
        pct       = int(n_cached / max(total_lnk, 1) * 100)
        st.markdown(f"**Cache:** {n_cached}/{total_lnk} ({pct}%)")
        st.progress(min(pct / 100, 1.0))
        if n_cached > 0:
            sz = sum(len(v) for v in st.session_state.dl_cache.values())
            st.caption(f"Ukuran: {sz/1024/1024:.1f} MB")
        if st.button("🗑️ Bersihkan Cache", use_container_width=True):
            st.session_state.dl_cache = {}
            st.rerun()
    st.caption("Made with ❤️ · Streamlit")

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
  <div class="header-eyebrow">⚡ Logistics Tool</div>
  <div class="header-title">Download <span>Surat Jalan</span> in Bulk</div>
  <div class="header-sub">
    Cocokkan NOPOL + Kuantum secara otomatis dari dua file,
    unduh sebagai ZIP atau PDF gabungan. Dilengkapi deteksi duplikat &amp; saran NOPOL mirip.
  </div>
  <div class="header-chips">
    <span class="chip chip-green">✅ Auto-match NOPOL + Kuantum</span>
    <span class="chip chip-blue">⚡ 8 Thread Paralel</span>
    <span class="chip chip-amber">🔍 Fuzzy NOPOL Match</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP INDICATOR
# ══════════════════════════════════════════════════════════════════════════════
def render_steps(step):
    steps = [
        {"n": "1", "lbl": "Upload File", "sub": "File 1 & File 2"},
        {"n": "2", "lbl": "Proses",      "sub": "Matching otomatis"},
        {"n": "3", "lbl": "Download",    "sub": "ZIP atau PDF"},
    ]
    circles, labels = [], []
    for i, s in enumerate(steps):
        idx = i + 1
        if idx < step:   st = "done",   "✓"
        elif idx == step: st = "active", s["n"]
        else:             st = "idle",   s["n"]
        status, icon = st
        circles.append(f'<div class="step-dot {status}">{icon}</div>')
        labels.append(
            f'<div class="step-txt">'
            f'<div class="lbl lbl-{status}">{s["lbl"]}</div>'
            f'<div class="sub sub-{status}">{s["sub"]}</div></div>')
    c1 = "done" if step > 1 else ""
    c2 = "done" if step > 2 else ""
    st_obj = __import__('streamlit')
    st_obj.markdown(f"""
    <div class="stepbar">
      <div class="step-item">{circles[0]}{labels[0]}</div>
      <div class="conn {c1}"></div>
      <div class="step-item">{circles[1]}{labels[1]}</div>
      <div class="conn {c2}"></div>
      <div class="step-item">{circles[2]}{labels[2]}</div>
    </div>
    """, unsafe_allow_html=True)

current_step = 3 if st.session_state.processed else 1
render_steps(current_step)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="sec-label"><span class="sec-num">1</span> Upload File</div>', unsafe_allow_html=True)

col_f1, col_f2 = st.columns(2, gap="medium")

with col_f1:
    has = "active" if st.session_state.get('f1') else ""
    st.markdown(f"""
    <div class="upload-zone {has}">
      <div class="upload-zone-header">
        <div class="uz-icon uz-icon-blue">📋</div>
        <div>
          <div class="uz-title">File 1 — Daftar Target</div>
          <div class="uz-sub">Data yang ingin dicocokkan</div>
        </div>
      </div>
      <div class="tag-row">
        <span class="col-tag tag-required">NOPOL *</span>
        <span class="col-tag tag-required">KUANTUM *</span>
        <span class="col-tag tag-optional">nomor polisi</span>
        <span class="col-tag tag-optional">tonase</span>
        <span class="col-tag tag-optional">qty</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    file1 = st.file_uploader("File 1", type=['csv','xlsx','xls'], key='f1',
                              label_visibility='collapsed')
    if file1:
        st.markdown(f'<div class="file-ok">✅ <b>{file1.name}</b> — {file1.size/1024:.1f} KB</div>',
                    unsafe_allow_html=True)

with col_f2:
    has2 = "active" if st.session_state.get('f2') else ""
    st.markdown(f"""
    <div class="upload-zone {has2}">
      <div class="upload-zone-header">
        <div class="uz-icon uz-icon-green">🗄️</div>
        <div>
          <div class="uz-title">File 2 — Database Surat Jalan</div>
          <div class="uz-sub">Berisi link Google Drive</div>
        </div>
      </div>
      <div class="tag-row">
        <span class="col-tag tag-required">NOPOL *</span>
        <span class="col-tag tag-required">KUANTUM *</span>
        <span class="col-tag tag-required">Link GDrive *</span>
        <span class="col-tag tag-optional">surat jalan</span>
        <span class="col-tag tag-optional">foto</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    file2 = st.file_uploader("File 2", type=['csv','xlsx','xls'], key='f2',
                              label_visibility='collapsed')
    if file2:
        st.markdown(f'<div class="file-ok">✅ <b>{file2.name}</b> — {file2.size/1024:.1f} KB</div>',
                    unsafe_allow_html=True)

# ── Process Button ─────────────────────────────────────────────────────────
st.markdown("")
both = file1 is not None and file2 is not None
bc1, bc2 = st.columns([2, 8])
with bc1:
    process = st.button(
        '⚙️ Proses & Cocokkan Data',
        use_container_width=True,
        disabled=not both,
        type="primary",
    )
with bc2:
    if not both:
        missing_f = []
        if not file1: missing_f.append("File 1")
        if not file2: missing_f.append("File 2")
        st.markdown(f"""
        <div style="padding:10px 0;font-size:0.82rem;color:#4b5563">
        Belum ada: <b style="color:#6366f1">{' & '.join(missing_f)}</b>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:10px 0;font-size:0.82rem;color:#10b981">
        ✅ Kedua file siap — klik tombol untuk memproses
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PROSES DATA
# ══════════════════════════════════════════════════════════════════════════════
if process:
    with st.spinner('🔄 Memproses dan mencocokkan data…'):
        df1 = load_file1(read_file(file1))
        df2 = load_file2(read_file(file2))
        if df1.empty or df2.empty:
            st.stop()

        dup_df = detect_duplicates_f1(df1)
        st.session_state.dup_df = dup_df

        result_all = match_files(df1, df2)

        found = result_all[
            result_all['surat_jalan'].notna() &
            result_all['surat_jalan'].str.startswith('http', na=False)
        ].copy().reset_index(drop=True)

        matched_f1_idx = set(found['_f1_idx'].tolist())
        missing_rows   = df1[~df1.index.isin(matched_f1_idx)].copy()
        missing        = missing_rows.drop_duplicates(subset=['nopol','kuantum']).reset_index(drop=True)

        missing_detail = build_missing_with_suggestions(missing, df1, df2)
        st.session_state.missing_detail = missing_detail

        diff_rows, miss_rows = [], []
        for item in missing_detail:
            if item['kategori'] == 'kuantum_beda':
                diff_rows.append({
                    'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                    'Kuantum di File 2': item['info'], 'Status': '⚠️ Kuantum tidak cocok'
                })
            else:
                miss_rows.append({
                    'NOPOL': item['nopol'], 'Kuantum File 1': item['kuantum'],
                    'Status': '❌ NOPOL tidak ada di File 2',
                    'Saran NOPOL (Kuantum Cocok)': (
                        ', '.join([f"{s['nopol_f2']} ({s['similarity']}%)"
                                   for s in item['saran']]) if item['saran'] else '-')
                })

        st.session_state.result_df      = found
        st.session_state.missing_df     = missing
        st.session_state.nopol_diff_df  = pd.DataFrame(diff_rows)
        st.session_state.nopol_miss_df  = pd.DataFrame(miss_rows)
        st.session_state.df2_debug      = df2
        st.session_state.df1_debug      = df1
        st.session_state.active_preview  = None
        st.session_state.dl_cache        = {}
        st.session_state.saran_preview   = {}
        st.session_state.dup_prev_active = {}
        st.session_state.processed       = True

    n_dup_groups = (len(dup_df[['nopol','kuantum']].drop_duplicates()) if not dup_df.empty else 0)
    n_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')
    st.balloons()
    st.success(f"✅ {len(found)} link ditemukan dari {len(df1)} data · "
               f"{len(missing)} tidak match · {n_dup_groups} duplikat · {n_mirip} saran mirip")
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.result_df is not None:
    found          = st.session_state.result_df
    missing        = st.session_state.missing_df
    nopol_diff     = st.session_state.nopol_diff_df
    nopol_miss     = st.session_state.nopol_miss_df
    df2_all        = st.session_state.df2_debug
    df1_all        = st.session_state.df1_debug
    dup_df         = st.session_state.dup_df if st.session_state.dup_df is not None else pd.DataFrame()
    missing_detail = st.session_state.missing_detail or []

    n_match       = len(found)
    n_diff_k      = len(nopol_diff) if nopol_diff is not None else 0
    n_miss_nopol  = len(nopol_miss)  if nopol_miss  is not None else 0
    n_all_miss    = len(missing)
    n_dup_groups  = (len(dup_df[['nopol','kuantum']].drop_duplicates()) if not dup_df.empty else 0)
    n_dup_rows    = len(dup_df) if not dup_df.empty else 0
    n_nopol_mirip = sum(1 for x in missing_detail if x['kategori'] == 'nopol_mirip')
    match_rate    = int(n_match / max(len(df1_all), 1) * 100) if df1_all is not None else 0

    # ── STATS ─────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label"><span class="sec-num">2</span> Ringkasan Hasil</div>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-grid">
      <div class="stat-card green">
        <div class="stat-bg-icon">✅</div>
        <div class="stat-lbl">Link Ditemukan</div>
        <div class="stat-val c-green">{n_match}</div>
        <div class="stat-sub c-green">{match_rate}% match rate</div>
      </div>
      <div class="stat-card blue">
        <div class="stat-bg-icon">🔁</div>
        <div class="stat-lbl">Duplikat File 1</div>
        <div class="stat-val c-blue">{n_dup_groups}</div>
        <div class="stat-sub c-blue">{n_dup_rows} baris total</div>
      </div>
      <div class="stat-card amber">
        <div class="stat-bg-icon">⚠️</div>
        <div class="stat-lbl">Kuantum Beda</div>
        <div class="stat-val c-amber">{n_diff_k}</div>
        <div class="stat-sub c-amber">NOPOL ada, qty ≠</div>
      </div>
      <div class="stat-card red">
        <div class="stat-bg-icon">❌</div>
        <div class="stat-lbl">NOPOL Tidak Ada</div>
        <div class="stat-val c-red">{n_miss_nopol}</div>
        <div class="stat-sub c-red">{n_nopol_mirip} ada saran</div>
      </div>
      <div class="stat-card orange">
        <div class="stat-bg-icon">🔴</div>
        <div class="stat-lbl">Total Tidak Match</div>
        <div class="stat-val c-orange">{n_all_miss}</div>
        <div class="stat-sub c-orange">dari {len(df1_all)} data</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Smart alerts
    if n_dup_groups > 0:
        st.markdown(f"""
        <div class="alert purple">
          <span class="alert-icon">🔁</span>
          <div><b>{n_dup_groups} kombinasi duplikat</b> ({n_dup_rows} baris) di File 1.
          Setiap baris tetap bisa didownload — dibedakan dengan label
          <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.</div>
        </div>""", unsafe_allow_html=True)

    if n_nopol_mirip > 0:
        st.markdown(f"""
        <div class="alert sky">
          <span class="alert-icon">🔍</span>
          <div><b>{n_nopol_mirip} data</b> punya saran NOPOL mirip dengan kuantum cocok.
          Kemungkinan salah ketik 1–2 karakter. Cek tab ❌ NOPOL Tidak Ada.</div>
        </div>""", unsafe_allow_html=True)

    if n_match == 0:
        st.markdown("""
        <div class="alert error">
          <span class="alert-icon">⚠️</span>
          <div><b>Tidak ada data yang match.</b>
          Pastikan format NOPOL & KUANTUM konsisten di kedua file.
          Sistem auto-normalisasi spasi dan huruf kapital.</div>
        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="sec-label"><span class="sec-num">3</span> Detail & Download</div>',
                unsafe_allow_html=True)

    tab1, tab_dup, tab2, tab3, tab4 = st.tabs([
        f"✅ Match ({n_match})",
        f"🔁 Duplikat ({n_dup_groups}g · {n_dup_rows}b)",
        f"⚠️ Kuantum Beda ({n_diff_k})",
        f"❌ NOPOL Tidak Ada ({n_miss_nopol})",
        f"🔴 Semua Tidak Match ({n_all_miss})",
    ])

    # ────────────────────────────────────────────────────────────────────────
    # TAB 1 — MATCH
    # ────────────────────────────────────────────────────────────────────────
    with tab1:
        if len(found) == 0:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🔍</div>
              <h3>Tidak Ada Data yang Match</h3>
              <p>Tidak ada kombinasi NOPOL + Kuantum yang cocok antara File 1 dan File 2.</p>
            </div>""", unsafe_allow_html=True)
        else:
            sc1, sc2 = st.columns([3, 9])
            with sc1:
                search = st.text_input('Filter NOPOL', placeholder='🔍  Ketik NOPOL…',
                                       label_visibility='collapsed', key='search_found')
            disp = found.copy()
            if search.strip():
                disp = disp[disp['nopol'].str.contains(
                    re.escape(norm_nopol(search.strip())), na=False, case=False)
                ].reset_index(drop=True)
            with sc2:
                st.markdown(f"""
                <div style="padding:10px 4px;font-size:0.8rem;color:#6b7280">
                Menampilkan <b style="color:#e2e4ee">{len(disp)}</b> dari
                <b style="color:#e2e4ee">{len(found)}</b> surat jalan
                </div>""", unsafe_allow_html=True)

            # Action bar
            st.markdown("")
            ac1, ac2, ac3, ac4 = st.columns([2, 2, 2, 6])
            with ac1:
                do_zip = st.button('📦 Download ZIP', use_container_width=True, key='btn_zip',
                                   help=f"Download {len(disp)} surat jalan sebagai ZIP")
            with ac2:
                do_merge = st.button('📄 Gabung PDF', use_container_width=True, key='btn_merge',
                                     help=f"Gabungkan {len(disp)} file jadi 1 PDF")
            with ac3:
                do_preload = st.button('⚡ Pre-load', use_container_width=True, key='btn_preload',
                                       help="Download ke cache supaya lebih cepat nanti")
            with ac4:
                n_c = sum(1 for _, r in disp.iterrows() if r['surat_jalan'] in st.session_state.dl_cache)
                pct_c = int(n_c / max(len(disp), 1) * 100)
                color = "#10b981" if pct_c == 100 else ("#fbbf24" if pct_c > 0 else "#4b5563")
                st.markdown(f"""
                <div style="padding:9px 14px;background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.07);border-radius:10px;
                font-size:0.78rem;color:#6b7280">
                🗃️ Cache: <b style="color:{color}">{n_c}/{len(disp)}</b> ({pct_c}%)
                {'&nbsp;✅ siap' if pct_c == 100 else ''}
                </div>""", unsafe_allow_html=True)

            # Pre-load
            if do_preload and len(disp) > 0:
                needed = [row['surat_jalan'] for _, row in disp.iterrows()
                          if row['surat_jalan'] not in st.session_state.dl_cache]
                if not needed:
                    st.success('✅ Semua file sudah di cache!')
                else:
                    snap = dict(st.session_state.dl_cache)
                    tasks_pre = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                                   'link': row['surat_jalan'], 'dup_label': ''}
                                 for i, row in disp.iterrows() if row['surat_jalan'] not in snap]
                    pb = st.progress(0); stxt = st.empty()
                    ok_n = fail_n = done_n = 0; nc = {}
                    with ThreadPoolExecutor(max_workers=8) as ex:
                        futs = {ex.submit(_worker, t, snap): t for t in tasks_pre}
                        for fut in as_completed(futs):
                            res = fut.result()
                            if res['content']: nc[res['link']] = res['content']; ok_n += 1
                            else: fail_n += 1
                            done_n += 1
                            pb.progress(done_n / len(tasks_pre))
                            stxt.markdown(f"Pre-load **{done_n}/{len(tasks_pre)}** — ✅ {ok_n} · ❌ {fail_n}")
                    st.session_state.dl_cache.update(nc)
                    stxt.success(f'✅ Pre-load selesai: {ok_n} berhasil, {fail_n} gagal')

            # ZIP
            if do_zip and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_list, nc = run_bulk_download(rows_dl, 'ZIP')
                st.session_state.dl_cache.update(nc)
                if ok_files:
                    zd = make_zip(ok_files)
                    st.markdown(f"""<div class="alert success"><span class="alert-icon">📦</span>
                    <div><b>{len(ok_files)} file siap</b> · ZIP {len(zd)//1024:,} KB</div></div>""",
                                unsafe_allow_html=True)
                    st.download_button(f'💾 Simpan ZIP ({len(ok_files)} file · {len(zd)//1024:,} KB)',
                                       zd, 'surat_jalan.zip', 'application/zip', key='dl_zip_r')
                if fail_list:
                    with st.expander(f'⚠️ {len(fail_list)} gagal'):
                        for f in fail_list: st.markdown(f'`{f}`')

            # Merge PDF
            if do_merge and len(disp) > 0:
                rows_dl = [{'idx': i, 'nopol': row['nopol'], 'kuantum': int(row['kuantum']),
                             'link': row['surat_jalan'], 'dup_label': ''}
                            for i, row in disp.iterrows()]
                ok_files, fail_dl, nc = run_bulk_download(rows_dl, 'PDF')
                st.session_state.dl_cache.update(nc)
                if ok_files:
                    with st.spinner('📄 Menggabungkan…'):
                        ordered = [nc.get(r['surat_jalan']) or st.session_state.dl_cache.get(r['surat_jalan'])
                                   for _, r in disp.iterrows()]
                        ordered = [x for x in ordered if x]
                        merged  = merge_pdfs(ordered)
                    if merged:
                        st.markdown(f"""<div class="alert success"><span class="alert-icon">📄</span>
                        <div><b>{len(ordered)} file digabung</b> · PDF {len(merged)//1024:,} KB</div></div>""",
                                    unsafe_allow_html=True)
                        st.download_button(f'💾 Simpan PDF ({len(ordered)} hal · {len(merged)//1024:,} KB)',
                                           merged, 'surat_jalan_gabungan.pdf', 'application/pdf',
                                           key='dl_merged')
                        if fail_dl:
                            with st.expander(f'⚠️ {len(fail_dl)} tidak ikut'):
                                for f in fail_dl: st.markdown(f'`{f}`')
                    else:
                        st.error('❌ Gagal PDF. Pastikan `pypdf`, `reportlab`, `Pillow` terinstall.')

            # Table
            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            hcols = st.columns([0.5, 2.5, 1.3, 0.7, 1.8, 0.7, 2])
            for col, lbl in zip(hcols, ['#','NOPOL','Kuantum','Link #','Drive','👁','⬇️']):
                col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)
            st.markdown('<hr class="row-div">', unsafe_allow_html=True)

            for i, row in disp.iterrows():
                nopol   = row['nopol']
                kuantum = int(row['kuantum'])
                link    = row['surat_jalan']
                link_no = int(row.get('_link_no', 1))
                fid     = extract_fid(link)
                is_dup  = not dup_df.empty and (
                    ((dup_df['nopol'] == nopol) & (dup_df['kuantum'] == kuantum)).any())

                cols = st.columns([0.5, 2.5, 1.3, 0.7, 1.8, 0.7, 2])
                cols[0].markdown(f'<span style="font-size:0.78rem;color:#374151">#{i+1}</span>',
                                 unsafe_allow_html=True)
                dup_badge = ' <span style="background:rgba(139,92,246,0.2);color:#c4b5fd;font-size:0.62rem;padding:1px 6px;border-radius:4px">DUP</span>' if is_dup else ''
                cols[1].markdown(f'<span class="np {"np-dup" if is_dup else ""}">{nopol}</span>{dup_badge}',
                                 unsafe_allow_html=True)
                cols[2].markdown(f'<span style="font-family:\'DM Mono\',monospace;font-size:0.85rem;color:#e2e4ee">{kuantum:,}</span>',
                                 unsafe_allow_html=True)
                cols[3].markdown(f'<span style="font-size:0.75rem;color:#4b5563">#{link_no}</span>',
                                 unsafe_allow_html=True)
                if fid:
                    cols[4].markdown(f'[🔗 Buka](https://drive.google.com/file/d/{fid}/view)')
                else:
                    cols[4].markdown(f'[🔗 Buka]({link})')

                with cols[5]:
                    btn_lbl = '👁️✕' if st.session_state.active_preview == i else '👁️'
                    if st.button(btn_lbl, key=f'v_{i}'):
                        st.session_state.active_preview = (
                            None if st.session_state.active_preview == i else i)
                        st.rerun()

                with cols[6]:
                    dup_label = f'_DUPLIKAT{link_no}' if link_no > 1 else ''
                    cached = st.session_state.dl_cache.get(link)
                    if cached:
                        ext   = infer_extension(cached)
                        fname = make_safe_filename(nopol, kuantum, i, ext,
                                                   total=len(disp), dup_label=dup_label)
                        st.download_button(f'⬇️ .{ext.upper()}', cached, fname,
                                           'application/pdf' if ext == 'pdf' else f'image/{ext}',
                                           key=f'd_{i}')
                    else:
                        if st.button('⬇️ Unduh', key=f'db_{i}'):
                            with st.spinner(f'Mengunduh {nopol}…'):
                                ct = download_file(link)
                            if ct:
                                st.session_state.dl_cache[link] = ct
                                ext   = infer_extension(ct)
                                fname = make_safe_filename(nopol, kuantum, i, ext,
                                                           total=len(disp), dup_label=dup_label)
                                st.download_button(f'💾 .{ext.upper()}', ct, fname,
                                                   'application/pdf' if ext == 'pdf' else f'image/{ext}',
                                                   key=f'ds_{i}')
                            else:
                                st.error('❌ Gagal — file private/expired.')

                if st.session_state.active_preview == i:
                    purl = to_preview(link)
                    if purl:
                        import streamlit.components.v1 as components
                        st.markdown(f"""
                        <div class="alert sky" style="margin-top:8px">
                          <span class="alert-icon">👁️</span>
                          <div>Preview — <b>{nopol}</b> · {kuantum:,}
                          <a href="{purl}" target="_blank"
                          style="margin-left:8px;font-size:0.78rem;color:#7dd3fc">
                          ↗ Buka di tab baru</a></div>
                        </div>""", unsafe_allow_html=True)
                        components.html(
                            f'<iframe src="{purl}" width="100%" height="680" '
                            f'style="border:1px solid rgba(14,165,233,0.3);border-radius:12px;background:#fff"'
                            f' allow="autoplay"></iframe>', height=700)
                    else:
                        st.error('Link preview tidak valid.')

                if i < len(disp) - 1:
                    st.markdown('<hr class="row-div">', unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB DUP
    # ────────────────────────────────────────────────────────────────────────
    with tab_dup:
        if dup_df.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Tidak Ada Duplikat!</h3>
              <p>Semua kombinasi NOPOL + Kuantum di File 1 adalah unik.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert purple">
              <span class="alert-icon">🔁</span>
              <div><b>{n_dup_groups} kombinasi duplikat</b> ({n_dup_rows} baris).
              Setiap baris bisa didownload individual — nama file dibedakan
              <code>_DUPLIKAT1</code>, <code>_DUPLIKAT2</code>, dst.</div>
            </div>""", unsafe_allow_html=True)

            sd_dup = st.text_input('', placeholder='🔍  Filter NOPOL duplikat…',
                                   label_visibility='collapsed', key='sd_dup')
            dza, dzb, _ = st.columns([2, 2, 8])
            with dza:
                do_zip_dup = st.button('📦 ZIP Duplikat', use_container_width=True, key='btn_zip_dup')
            with dzb:
                do_merge_dup = st.button('📄 PDF Duplikat', use_container_width=True, key='btn_merge_dup')

            all_dup_rows = []
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)
                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    baris_ke  = int(drow['baris_ke'])
                    dup_label = f'_DUPLIKAT{baris_ke}'
                    link = (None if n_links == 0
                            else links_found[i_row - 1] if i_row <= n_links
                            else links_found[0])
                    all_dup_rows.append({'nopol': nopol, 'kuantum': int(kuantum),
                                         'baris_ke': baris_ke, 'dup_label': dup_label, 'link': link})

            if do_zip_dup:
                vr = [r for r in all_dup_rows if r['link']]
                if not vr: st.warning('⚠️ Tidak ada link.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']}
                                for i, r in enumerate(vr)]
                    ok_files, fl, nc = run_bulk_download(rows_dl, 'Duplikat ZIP')
                    st.session_state.dl_cache.update(nc)
                    if ok_files:
                        st.download_button(f'💾 ZIP Duplikat ({len(ok_files)} file)',
                                           make_zip(ok_files), 'duplikat.zip',
                                           'application/zip', key='dl_zip_dup_r')
                    if fl:
                        with st.expander(f'❌ {len(fl)} gagal'):
                            for f in fl: st.markdown(f'`{f}`')

            if do_merge_dup:
                vr = [r for r in all_dup_rows if r['link']]
                if not vr: st.warning('⚠️ Tidak ada link.')
                else:
                    rows_dl = [{'idx': i, 'nopol': r['nopol'], 'kuantum': r['kuantum'],
                                 'link': r['link'], 'dup_label': r['dup_label']}
                                for i, r in enumerate(vr)]
                    ok_files, fl, nc = run_bulk_download(rows_dl, 'Duplikat PDF')
                    st.session_state.dl_cache.update(nc)
                    if ok_files:
                        with st.spinner('Menggabungkan…'):
                            ordered = [nc.get(r['link']) or st.session_state.dl_cache.get(r['link']) for r in vr]
                            ordered = [x for x in ordered if x]
                            merged  = merge_pdfs(ordered)
                        if merged:
                            st.success(f'✅ {len(ordered)} file digabung · {len(merged)//1024:,} KB')
                            st.download_button('💾 PDF Duplikat', merged, 'duplikat.pdf',
                                               'application/pdf', key='dl_merge_dup_r')
                        else: st.error('❌ Gagal PDF.')
                    if fl:
                        with st.expander(f'⚠️ {len(fl)} gagal'): [st.markdown(f'`{f}`') for f in fl]

            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            row_counter = 0
            for (nopol, kuantum), grp in dup_df.groupby(['nopol', 'kuantum']):
                if sd_dup.strip() and norm_nopol(sd_dup.strip()) not in nopol:
                    continue
                links_found = found[
                    (found['nopol'] == nopol) & (found['kuantum'] == kuantum)
                ]['surat_jalan'].tolist()
                n_links = len(links_found)

                st.markdown(f"""
                <div class="dup-group">
                  <div class="dup-group-title">
                    <span class="np np-dup">{nopol}</span>
                    <span style="color:#6b7280;font-size:0.82rem">
                      <span style="font-family:'DM Mono',monospace">{int(kuantum):,}</span> kuantum
                    </span>
                    <span style="background:rgba(239,68,68,0.12);color:#f87171;
                    border-radius:6px;padding:2px 10px;font-size:0.73rem;font-weight:700">
                    Muncul {len(grp)}× di File 1</span>
                    <span style="background:rgba(99,102,241,0.12);color:#a5b4fc;
                    border-radius:6px;padding:2px 10px;font-size:0.73rem;font-weight:700">
                    {n_links} link di File 2</span>
                  </div>
                """, unsafe_allow_html=True)

                dh0,dh1,dh2,dh3,dh4,dh5 = st.columns([0.6, 1.8, 2.2, 2, 0.8, 1.8])
                for col, lbl in zip([dh0,dh1,dh2,dh3,dh4,dh5],
                                     ['Ke-','NOPOL','Label File','Drive','👁','⬇️']):
                    col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)

                for i_row, (_, drow) in enumerate(grp.iterrows(), start=1):
                    baris_ke  = int(drow['baris_ke'])
                    dup_label = f'_DUPLIKAT{baris_ke}'
                    link = (None if n_links == 0
                            else links_found[i_row - 1] if i_row <= n_links
                            else links_found[0])
                    fid = extract_fid(link) if link else None
                    uid = f'dup_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}_{baris_ke}'

                    cols = st.columns([0.6, 1.8, 2.2, 2, 0.8, 1.8])
                    cols[0].markdown(f'<b style="color:#818cf8">{baris_ke}</b>',
                                     unsafe_allow_html=True)
                    cols[1].markdown(f'<span class="np np-dup">{nopol}</span>',
                                     unsafe_allow_html=True)
                    cols[2].markdown(
                        f'<code style="background:rgba(139,92,246,0.12);color:#c4b5fd;'
                        f'padding:3px 8px;border-radius:6px;font-size:0.78rem">{dup_label}</code>',
                        unsafe_allow_html=True)
                    if link and fid:
                        cols[3].markdown(f'[🔗 Drive](https://drive.google.com/file/d/{fid}/view)')
                    elif link:
                        cols[3].markdown(f'[🔗 Buka]({link})')
                    else:
                        cols[3].markdown('<span style="color:#374151">— Tidak ada</span>', unsafe_allow_html=True)

                    with cols[4]:
                        if link:
                            pgk  = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                            isap = (st.session_state.dup_prev_active.get(pgk) == baris_ke)
                            if st.button('👁️✕' if isap else '👁️', key=f'dprev_{uid}'):
                                st.session_state.dup_prev_active[pgk] = (None if isap else baris_ke)
                                st.rerun()

                    with cols[5]:
                        if link:
                            cached = st.session_state.dl_cache.get(link)
                            if cached:
                                ext   = infer_extension(cached)
                                fname = make_safe_filename(nopol, kuantum, row_counter, ext,
                                                           total=n_dup_rows, dup_label=dup_label)
                                st.download_button(f'⬇️ .{ext.upper()}', cached, fname,
                                                   'application/pdf' if ext=='pdf' else f'image/{ext}',
                                                   key=f'ddl_{uid}')
                            else:
                                if st.button('⬇️ Unduh', key=f'ddlb_{uid}'):
                                    with st.spinner(f'Mengunduh…'):
                                        ct = download_file(link)
                                    if ct:
                                        st.session_state.dl_cache[link] = ct
                                        ext   = infer_extension(ct)
                                        fname = make_safe_filename(nopol, kuantum, row_counter, ext,
                                                                   total=n_dup_rows, dup_label=dup_label)
                                        st.download_button(f'💾 .{ext.upper()}', ct, fname,
                                                           'application/pdf' if ext=='pdf' else f'image/{ext}',
                                                           key=f'ddls_{uid}')
                                    else: st.error('❌ Gagal.')
                        else: st.markdown('`—`')

                    pgk = f'grp_{re.sub(r"[^a-zA-Z0-9]","_",nopol)}_{kuantum}'
                    if link and st.session_state.dup_prev_active.get(pgk) == baris_ke:
                        purl = to_preview(link)
                        if purl:
                            import streamlit.components.v1 as components
                            st.markdown(f"""
                            <div class="alert sky" style="margin-top:8px">
                              <span class="alert-icon">👁️</span>
                              <div>Preview — <b>{nopol}</b> ·
                              <code style="color:#c4b5fd">{dup_label}</code> ·
                              <a href="{purl}" target="_blank"
                              style="font-size:0.78rem;color:#7dd3fc">↗ tab baru</a></div>
                            </div>""", unsafe_allow_html=True)
                            components.html(
                                f'<iframe src="{purl}" width="100%" height="680" '
                                f'style="border:1px solid rgba(139,92,246,0.3);border-radius:12px;background:#fff"'
                                f' allow="autoplay"></iframe>', height=700)
                        else: st.error('Link preview tidak valid.')

                    row_counter += 1

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")

            # Export
            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            exp_dup = dup_df[['nopol','kuantum','baris_ke','jumlah_duplikat']].copy()
            exp_dup.columns = ['NOPOL','Kuantum','Baris ke-','Total Duplikat']
            exp_dup['Label File'] = exp_dup['Baris ke-'].apply(lambda x: f'_DUPLIKAT{int(x)}')
            ec1, _ = st.columns([2, 10])
            with ec1:
                st.download_button('📥 Export CSV', exp_dup.to_csv(index=False).encode('utf-8'),
                                   'duplikat.csv', 'text/csv', key='dl_dup')
            st.dataframe(exp_dup, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 2 — KUANTUM BEDA
    # ────────────────────────────────────────────────────────────────────────
    with tab2:
        if nopol_diff is None or nopol_diff.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Semua Kuantum Cocok!</h3>
              <p>Tidak ada NOPOL dengan kuantum berbeda antara File 1 dan File 2.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert warn">
              <span class="alert-icon">⚠️</span>
              <div><b>{len(nopol_diff)} data</b> — NOPOL ditemukan di File 2 tapi nilai
              kuantumnya tidak cocok. Kemungkinan perbedaan satuan atau input data.</div>
            </div>""", unsafe_allow_html=True)
            sc, _ = st.columns([3, 9])
            with sc:
                sd = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sd')
            dd = nopol_diff.copy()
            if sd.strip():
                dd = dd[dd['NOPOL'].str.contains(re.escape(norm_nopol(sd)), na=False,
                                                   case=False)].reset_index(drop=True)
            st.dataframe(dd, use_container_width=True, hide_index=True)
            ca, _ = st.columns([2, 10])
            with ca:
                st.download_button('📥 Export CSV', dd.to_csv(index=False).encode('utf-8'),
                                   'kuantum_beda.csv', 'text/csv', key='dl_a')

    # ────────────────────────────────────────────────────────────────────────
    # TAB 3 — NOPOL TIDAK ADA + SARAN
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        miss_items = [x for x in missing_detail if x['kategori'] in ('nopol_mirip', 'tidak_ada')]
        if not miss_items:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🎉</div>
              <h3>Semua NOPOL Ditemukan!</h3>
              <p>Tidak ada NOPOL dari File 1 yang hilang di File 2.</p>
            </div>""", unsafe_allow_html=True)
        else:
            n_mirip   = sum(1 for x in miss_items if x['kategori'] == 'nopol_mirip')
            n_tdk_ada = sum(1 for x in miss_items if x['kategori'] == 'tidak_ada')
            st.markdown(f"""
            <div class="alert error">
              <span class="alert-icon">❌</span>
              <div><b>{len(miss_items)} NOPOL tidak ada di File 2.</b>
              🔍 <b>{n_mirip}</b> punya saran mirip ·
              🚫 <b>{n_tdk_ada}</b> tanpa saran</div>
            </div>""", unsafe_allow_html=True)

            fc1, fc2 = st.columns([3, 5])
            with fc1:
                sm = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sm')
            with fc2:
                min_sim = st.slider('Threshold Kemiripan (%)', 30, 90, 50, 5, key='sim_slider')

            for item_idx, item in enumerate(miss_items):
                nopol   = item['nopol']
                kuantum = item['kuantum']
                if sm.strip() and norm_nopol(sm.strip()) not in nopol:
                    continue
                saran_f = [s for s in item['saran'] if s['similarity'] >= min_sim]
                has_s   = bool(saran_f)

                border_c = 'rgba(99,102,241,0.3)' if has_s else 'rgba(239,68,68,0.2)'
                bar_c    = '#6366f1' if has_s else '#ef4444'
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02);
                border:1px solid {border_c};border-left:3px solid {bar_c};
                border-radius:12px;padding:14px 18px;margin:10px 0">
                  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                    <span class="np">{nopol}</span>
                    <span style="color:#4b5563;font-size:0.8rem;font-family:'DM Mono',monospace">{kuantum:,}</span>
                    <span style="background:{'rgba(99,102,241,0.12)' if has_s else 'rgba(239,68,68,0.1)'};
                    color:{'#818cf8' if has_s else '#f87171'};border-radius:6px;
                    padding:2px 10px;font-size:0.72rem;font-weight:700">
                    {'🔍 ' + str(len(saran_f)) + ' saran' if has_s else '🚫 Tidak ada saran'}
                    </span>
                  </div>
                </div>""", unsafe_allow_html=True)

                if saran_f:
                    sh0,sh1,sh2,sh3,sh4 = st.columns([0.4, 2.5, 1.5, 1.3, 2.5])
                    for col, lbl in zip([sh0,sh1,sh2,sh3,sh4],
                                         ['#','NOPOL File 2','Kemiripan','Kuantum','Aksi']):
                        col.markdown(f'<span class="col-hdr">{lbl}</span>', unsafe_allow_html=True)

                    for s_idx, saran in enumerate(saran_f):
                        sk  = f'saran_{item_idx}_{s_idx}'
                        sc0,sc1,sc2,sc3,sc4 = st.columns([0.4, 2.5, 1.5, 1.3, 2.5])
                        sim = saran['similarity']
                        sc0.markdown(f'`{s_idx+1}`')
                        sc1.markdown(f'<span class="np">{saran["nopol_f2"]}</span>', unsafe_allow_html=True)
                        sc2.markdown(f'<span class="sim {"sim-hi" if sim>=80 else "sim-md" if sim>=65 else "sim-lo"}">{sim}%</span>',
                                     unsafe_allow_html=True)
                        sc3.markdown(f'<span style="font-family:\'DM Mono\',monospace">{saran["kuantum"]:,}</span>',
                                     unsafe_allow_html=True)

                        with sc4:
                            cp, cd = st.columns(2)
                            with cp:
                                pa = st.session_state.saran_preview.get(f'item_{item_idx}') == s_idx
                                if st.button('👁️✕' if pa else '👁️', key=f'sprev_{sk}',
                                             use_container_width=True):
                                    st.session_state.saran_preview[f'item_{item_idx}'] = (None if pa else s_idx)
                                    st.rerun()
                            with cd:
                                ls = saran['surat_jalan']
                                cs = st.session_state.dl_cache.get(ls)
                                if cs:
                                    ext_s = infer_extension(cs)
                                    fn_s  = make_safe_filename(saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                    st.download_button(f'⬇️ .{ext_s.upper()}', cs, fn_s,
                                                       'application/pdf' if ext_s=='pdf' else f'image/{ext_s}',
                                                       key=f'sdl_c_{sk}', use_container_width=True)
                                else:
                                    if st.button('⬇️ Unduh', key=f'sdl_{sk}', use_container_width=True):
                                        with st.spinner('Mengunduh…'): ct_s = download_file(ls)
                                        if ct_s:
                                            st.session_state.dl_cache[ls] = ct_s
                                            ext_s = infer_extension(ct_s)
                                            fn_s  = make_safe_filename(saran['nopol_f2'], saran['kuantum'], s_idx, ext_s)
                                            st.download_button(f'💾 .{ext_s.upper()}', ct_s, fn_s,
                                                               'application/pdf' if ext_s=='pdf' else f'image/{ext_s}',
                                                               key=f'sdl_s_{sk}', use_container_width=True)
                                        else: st.error('❌ Gagal.')

                        if st.session_state.saran_preview.get(f'item_{item_idx}') == s_idx:
                            purl_s = to_preview(saran['surat_jalan'])
                            if purl_s:
                                import streamlit.components.v1 as components
                                sc = '#10b981' if sim>=80 else '#f59e0b' if sim>=65 else '#ef4444'
                                st.markdown(f"""
                                <div class="alert sky" style="margin:8px 0">
                                  <span class="alert-icon">👁️</span>
                                  <div>Preview — <b>{saran['nopol_f2']}</b> ·
                                  <b style="color:{sc}">{sim}%</b> kemiripan ·
                                  <a href="{purl_s}" target="_blank" style="color:#7dd3fc;font-size:0.78rem">↗ tab baru</a>
                                  </div>
                                </div>""", unsafe_allow_html=True)
                                components.html(
                                    f'<iframe src="{purl_s}" width="100%" height="680" '
                                    f'style="border:1px solid rgba(14,165,233,0.3);border-radius:12px;background:#fff"'
                                    f' allow="autoplay"></iframe>', height=700)
                            else: st.error('Link tidak valid.')
                else:
                    st.caption(f'  {"🚫 Tidak ada saran." if item["kategori"]=="tidak_ada" else f"🔽 Kurangi threshold (saat ini {min_sim}%) untuk lebih banyak saran."}')

            st.markdown('<hr class="row-div">', unsafe_allow_html=True)
            if nopol_miss is not None and not nopol_miss.empty:
                cb, _ = st.columns([2, 10])
                with cb:
                    st.download_button('📥 Export CSV', nopol_miss.to_csv(index=False).encode('utf-8'),
                                       'nopol_tidak_ada.csv', 'text/csv', key='dl_b')
                st.dataframe(nopol_miss, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────────────────────
    # TAB 4 — SEMUA TIDAK MATCH
    # ────────────────────────────────────────────────────────────────────────
    with tab4:
        if missing.empty:
            st.markdown("""
            <div class="empty-state">
              <div class="icon">🏆</div>
              <h3>Sempurna! Semua Data Match!</h3>
              <p>Setiap baris di File 1 berhasil dicocokkan dengan File 2.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert error">
              <span class="alert-icon">🔴</span>
              <div><b>{n_all_miss} kombinasi tidak match</b> total.</div>
            </div>""", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Tidak Match", n_all_miss)
            m2.metric("⚠️ Kuantum Beda",   n_diff_k)
            m3.metric("❌ NOPOL Tidak Ada", n_miss_nopol)
            m4.metric("🔍 Ada Saran Mirip", n_nopol_mirip)

            all_m = missing.rename(columns={'nopol':'NOPOL','kuantum':'Kuantum File 1'}).copy()
            all_m['Kuantum File 1'] = all_m['Kuantum File 1'].astype(int)

            def get_ket(row):
                nopol = row['NOPOL']
                f2m   = df2_all[df2_all['nopol'] == nopol]
                if len(f2m) > 0:
                    ks = sorted(f2m['kuantum'].dropna().astype(int).unique().tolist())
                    d  = ', '.join(map(str, ks[:5])) + (f' (+{len(ks)-5})' if len(ks)>5 else '')
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
                sa = st.text_input('', placeholder='🔍 Filter NOPOL…',
                                   label_visibility='collapsed', key='sa')
            if sa.strip():
                all_m = all_m[all_m['NOPOL'].str.contains(
                    re.escape(norm_nopol(sa)), na=False, case=False)].reset_index(drop=True)

            st.dataframe(all_m, use_container_width=True, hide_index=True)
            cde, _ = st.columns([2, 10])
            with cde:
                st.download_button('📥 Export CSV', all_m.to_csv(index=False).encode('utf-8'),
                                   'semua_tidak_match.csv', 'text/csv', key='dl_c')

# ══════════════════════════════════════════════════════════════════════════════
# EMPTY STATE
# ══════════════════════════════════════════════════════════════════════════════
elif not st.session_state.processed:
    st.markdown("""
    <div class="empty-state" style="margin-top:24px">
      <div class="icon">📂</div>
      <h3>Upload File untuk Memulai</h3>
      <p>Upload <b>File 1</b> (daftar target) dan <b>File 2</b> (database surat jalan),
         lalu klik <b>⚙️ Proses & Cocokkan Data</b>.<br><br>
         Butuh bantuan? Lihat panduan di sidebar kiri ☰
      </p>
    </div>
    """, unsafe_allow_html=True)
