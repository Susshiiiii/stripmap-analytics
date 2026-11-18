import re
from datetime import date, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from PIL import Image

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

st.set_page_config(page_title="IFX | Semiconductor Defect Analytics", page_icon="🏭", layout="wide")

# ==========================================
# THEME: Apple-style glass UI, light / dark (dark by default)
# ==========================================
FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif'

THEMES = {
    "dark": {
        "scheme": "dark", "bg": "#000000", "elevated": "#2C2C2E",
        "glow1": "rgba(41,151,255,0.24)", "glow2": "rgba(94,92,230,0.22)", "glow3": "rgba(48,209,88,0.10)",
        "glass": "rgba(28,28,30,0.58)", "glass_strong": "rgba(28,28,30,0.82)",
        "input": "rgba(255,255,255,0.07)", "border": "rgba(255,255,255,0.10)", "border_strong": "rgba(255,255,255,0.18)",
        "highlight": "rgba(255,255,255,0.07)",
        "text": "#F5F5F7", "text2": "#A1A1A6", "accent": "#2997FF", "accent_soft": "rgba(41,151,255,0.18)",
        "success": "#30D158",
        "shadow": "0 8px 30px rgba(0,0,0,0.45)", "shadow_sm": "0 1px 3px rgba(0,0,0,0.30)",
        "grid": "rgba(255,255,255,0.08)", "tile_border": "rgba(255,255,255,0.18)", "mark_border": "#FFFFFF",
    },
    "light": {
        "scheme": "light", "bg": "#F5F5F7", "elevated": "#FFFFFF",
        "glow1": "rgba(0,113,227,0.16)", "glow2": "rgba(175,82,222,0.14)", "glow3": "rgba(52,199,89,0.12)",
        "glass": "rgba(255,255,255,0.62)", "glass_strong": "rgba(255,255,255,0.86)",
        "input": "rgba(0,0,0,0.04)", "border": "rgba(0,0,0,0.08)", "border_strong": "rgba(0,0,0,0.14)",
        "highlight": "rgba(255,255,255,0.75)",
        "text": "#1D1D1F", "text2": "#6E6E73", "accent": "#0071E3", "accent_soft": "rgba(0,113,227,0.10)",
        "success": "#248A3D",
        "shadow": "0 8px 30px rgba(0,0,0,0.08)", "shadow_sm": "0 1px 3px rgba(0,0,0,0.06)",
        "grid": "rgba(0,0,0,0.08)", "tile_border": "rgba(0,0,0,0.14)", "mark_border": "#1D1D1F",
    },
}

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
IS_DARK = bool(st.session_state.dark_mode)
T = THEMES["dark" if IS_DARK else "light"]


def apply_theme(T, is_dark):
    glass = (
        "background: var(--glass); backdrop-filter: saturate(180%) blur(24px); "
        "-webkit-backdrop-filter: saturate(180%) blur(24px); border: 1px solid var(--border); "
        "box-shadow: var(--shadow), inset 0 1px 0 var(--highlight);"
    )
    # Streamlit's data grids are canvas-drawn in the base (dark) theme; invert them in light mode.
    grid_fix = "" if is_dark else '[data-testid="stDataFrame"] > div { filter: invert(1) hue-rotate(180deg); }'
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {{
  color-scheme: {T['scheme']};
  --bg: {T['bg']}; --elevated: {T['elevated']}; --glass: {T['glass']}; --glass-strong: {T['glass_strong']};
  --input: {T['input']}; --border: {T['border']}; --border-strong: {T['border_strong']}; --highlight: {T['highlight']};
  --text: {T['text']}; --text2: {T['text2']}; --accent: {T['accent']}; --accent-soft: {T['accent_soft']};
  --success: {T['success']}; --shadow: {T['shadow']}; --shadow-sm: {T['shadow_sm']};
  --font: {FONT_STACK}; --ease: cubic-bezier(0.25, 0.1, 0.25, 1);
}}
.stApp {{
  background-color: var(--bg);
  background-image:
    radial-gradient(900px 620px at 6% -8%, {T['glow1']}, transparent 62%),
    radial-gradient(820px 620px at 96% 6%, {T['glow2']}, transparent 62%),
    radial-gradient(1000px 720px at 50% 112%, {T['glow3']}, transparent 62%);
  background-attachment: fixed;
  color: var(--text); font-family: var(--font);
}}
.stApp, [data-testid="stSidebar"] > div:first-child, div[data-testid="stMetric"], .glass, .result-card, .legend-pill,
.stButton > button, .stDownloadButton > button, [data-baseweb="select"] > div, [data-baseweb="input"] {{
  transition: background-color .4s ease, color .3s ease, border-color .4s ease, box-shadow .4s ease, transform .2s var(--ease);
}}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2.4rem; max-width: 1800px; padding-bottom: 4rem; }}
h1, h2, h3, h4, h5, h6 {{ color: var(--text) !important; font-family: var(--font); letter-spacing: -0.015em; font-weight: 600 !important; }}
.stMarkdown p, .stMarkdown li, label {{ color: var(--text); }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: var(--text2) !important; }}
[data-testid="stWidgetLabel"] p {{ color: var(--text2) !important; font-weight: 500; font-size: 14px; }}
hr {{ border: none !important; border-top: 1px solid var(--border) !important; margin: 2rem 0 !important; }}
code {{ color: var(--accent) !important; background: var(--accent-soft) !important; border-radius: 6px; padding: 1px 6px; }}

/* ---- glass surfaces ---- */
[data-testid="stSidebar"] {{ background: transparent; }}
[data-testid="stSidebar"] > div:first-child {{ background: var(--glass-strong); backdrop-filter: saturate(180%) blur(28px);
  -webkit-backdrop-filter: saturate(180%) blur(28px); border-right: 1px solid var(--border); }}
[data-testid="stSidebar"][aria-expanded="true"] {{ min-width: 440px !important; max-width: 440px !important; }}
[data-testid="stSidebar"][aria-expanded="false"] {{ min-width: 0 !important; max-width: 0 !important; width: 0 !important;
  overflow: hidden !important; border: none !important; }}
.st-key-gen_date [data-testid="stDateInputField"] {{ font-size: 13px; padding-left: 2px; padding-right: 2px; }}
[data-testid="stSidebar"] h2 {{ font-size: 20px !important; }}
/* sidebar layout: content column fills the height so the account block sits at the bottom */
[data-testid="stSidebarUserContent"] {{ padding-top: 0 !important; }}
[data-testid="stSidebarUserContent"] > div > [data-testid="stVerticalBlock"] {{ min-height: calc(100vh - 5.5rem); }}
.st-key-sb_footer {{ padding-top: 12px; border-top: 1px solid var(--border); }}
[data-testid="stLayoutWrapper"]:has(> .st-key-sb_footer), .st-key-sb_footer {{ margin-top: auto; }}
.st-key-sb_nav, .st-key-sb_footer {{ gap: 4px !important; }}
.brand {{ display: flex; align-items: center; gap: 12px; padding: 0 4px 14px; border-bottom: 1px solid var(--border); margin: -6px 0 2px; }}
.brand-mark {{ display: flex; filter: drop-shadow(0 4px 10px var(--accent-soft)); }}
.brand-name {{ font-size: 18px; font-weight: 700; letter-spacing: -0.01em; color: var(--text); line-height: 1.15; }}
.brand-sub {{ font-size: 12px; color: var(--text2); }}
.nav-label {{ font-size: 12.5px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--text); opacity: .6; margin: 18px 4px 6px; }}
.brand + .nav-label {{ margin-top: 8px; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: 13.5px !important; }}
[class*="st-key-nav_"] .stButton > button {{ justify-content: flex-start; gap: 10px; min-height: 40px; height: 40px; padding: 0 12px !important;
  border-radius: 10px !important; border: none !important; background: transparent !important; color: var(--text2) !important; transform: none !important; }}
[class*="st-key-nav_"] .stButton > button p {{ font-size: 14.5px; font-weight: 500; color: inherit !important; }}
[class*="st-key-nav_"] .stButton > button > div, .st-key-logout_btn .stButton > button > div {{ justify-content: flex-start !important; width: 100%; gap: 10px; }}
[class*="st-key-nav_"] .stButton > button:hover {{ background: var(--input) !important; color: var(--text) !important; }}
[class*="st-key-nav_"][class*="_on"] .stButton > button {{ background: var(--accent-soft) !important; color: var(--accent) !important; box-shadow: none; }}
[class*="st-key-nav_"][class*="_on"] .stButton > button p {{ font-weight: 600; }}
.st-key-logout_btn .stButton > button {{ justify-content: flex-start; gap: 10px; min-height: 40px; border: none !important;
  background: transparent !important; color: #FF453A !important; padding: 0 12px !important; }}
.st-key-logout_btn .stButton > button p {{ color: #FF453A !important; font-weight: 500; }}
.st-key-logout_btn .stButton > button:hover {{ background: rgba(255,69,58,0.12) !important; }}
.filter-label {{ display: flex; align-items: center; gap: 8px; margin: 0 4px; }}
.filter-label .filter-count {{ opacity: 1; }}
.filter-count {{ font-size: 11px; font-weight: 700; letter-spacing: 0; padding: 1px 7px; border-radius: 980px;
  background: var(--accent); color: #FFFFFF; }}
.st-key-filter_head {{ margin-top: 12px; }}
.st-key-btn_reset_filters button {{ border: none !important; background: transparent !important; min-height: 28px; padding: 0 !important; }}
.st-key-btn_reset_filters {{ padding-top: 10px; }}
.st-key-filter_head [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
.st-key-btn_reset_filters button p {{ color: var(--accent) !important; font-size: 13px; font-weight: 600; }}
.st-key-btn_reset_filters button:disabled p {{ color: var(--text2) !important; opacity: .5; }}
.st-key-sb_filters [data-testid="stExpander"] details {{ border-radius: 14px !important; box-shadow: none !important; background: var(--input) !important; }}
.st-key-sb_filters [data-testid="stExpander"] summary {{ padding: 10px 12px !important; }}
.st-key-sb_filters [data-testid="stExpander"] summary p {{ font-size: 14px !important; font-weight: 500 !important; }}
[class*="st-key-gen_lots_"] button, [class*="st-key-gen_ucode_"] button {{ border: none !important; background: transparent !important; min-height: 30px; }}
[class*="st-key-gen_lots_"] button p, [class*="st-key-gen_ucode_"] button p {{ color: var(--accent) !important; font-size: 13px; font-weight: 600; }}
.st-key-sb_filters .stMultiSelect .react-aria-ComboBox > div {{ max-height: 220px; overflow-y: auto; }}
/* ---- collapsed sidebar: mini rail ---- */
.st-key-mini_rail {{ display: none !important; }}
body:has([data-testid="stSidebar"][aria-expanded="false"]) .st-key-mini_rail {{
  display: flex !important; flex-direction: column; align-items: center; gap: 6px !important;
  position: fixed; left: 14px; top: 14px; bottom: 14px; width: 68px; z-index: 999990; padding: 14px 0;
  background: var(--glass-strong); backdrop-filter: saturate(180%) blur(28px); -webkit-backdrop-filter: saturate(180%) blur(28px);
  border: 1px solid var(--border); border-radius: 22px; box-shadow: var(--shadow), inset 0 1px 0 var(--highlight); }}
body:has([data-testid="stSidebar"][aria-expanded="false"]) .block-container {{ padding-left: 120px !important; }}
.st-key-mini_rail [data-testid="stElementContainer"] {{ width: auto !important; }}
.rail-brand {{ display: flex; justify-content: center; padding: 2px 0 10px; margin-bottom: 4px; border-bottom: 1px solid var(--border); width: 44px; }}
[class*="st-key-rail_"] .stButton button {{ width: 44px; height: 44px; min-height: 44px; padding: 0 !important; border-radius: 12px !important;
  border: none !important; background: transparent !important; color: var(--text2) !important; position: relative; transform: none !important; }}
[class*="st-key-rail_"] .stButton button {{ font-size: 0 !important; overflow: hidden; }}
[class*="st-key-rail_"] .stButton button [data-testid="stMarkdownContainer"], [class*="st-key-rail_"] .stButton button p {{ display: none !important; }}
[class*="st-key-rail_"] .stButton button > div {{ width: auto !important; gap: 0 !important; }}
[class*="st-key-rail_"] .stButton button > div {{ justify-content: center !important; }}
[class*="st-key-rail_"] .stButton button span[data-testid="stIconMaterial"] {{ font-size: 22px !important; }}
[class*="st-key-rail_"] .stButton button:hover {{ background: var(--input) !important; color: var(--text) !important; }}
[class*="st-key-rail_"][class*="_on"] .stButton > button {{ background: var(--accent-soft) !important; color: var(--accent) !important; }}
[data-testid="stExpandSidebarButton"] {{ position: fixed !important; left: 68px; top: 32px; z-index: 999999; width: 28px !important; height: 28px !important;
  border-radius: 50% !important; background: var(--elevated) !important; border: 1px solid var(--border-strong) !important;
  box-shadow: var(--shadow-sm); color: var(--text) !important; }}
[data-testid="stExpandSidebarButton"]:hover {{ background: var(--accent) !important; color: #FFFFFF !important; border-color: transparent !important; }}
.data-status {{ display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text2); margin: 2px 4px 6px; }}
.data-status .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.data-status .dot.on {{ background: var(--success); box-shadow: 0 0 0 3px rgba(48,209,88,0.18); }}
.data-status .dot.off {{ background: var(--text2); opacity: .5; }}
.empty-state {{ max-width: 640px; margin: 8vh auto 0; padding: 40px 32px; }}
.st-key-btn_latest_date button, .st-key-btn_latest_week button {{ padding: .5rem .3rem !important; min-height: 40px; }}
.st-key-btn_latest_date button p, .st-key-btn_latest_week button p {{ font-size: 12px !important; white-space: nowrap; }}
[data-testid="stPopover"] button {{ border-radius: 980px !important; border: 1px solid var(--border-strong) !important;
  background: var(--input) !important; color: #FF453A !important; }}
[data-testid="stPopover"] button p {{ color: #FF453A !important; }}
[data-testid="stPopoverBody"] {{ background: var(--glass-strong) !important; backdrop-filter: saturate(180%) blur(28px);
  -webkit-backdrop-filter: saturate(180%) blur(28px); border: 1px solid var(--border) !important; border-radius: 16px !important; }}
.st-key-confirm_delete_all button[kind="primary"], .st-key-confirm_delete_all [data-testid="stBaseButton-primary"] {{ background: #FF3B30 !important; border-color: transparent !important; }}
[data-testid="stSidebar"] h3 {{ font-size: 13px !important; color: var(--text2) !important; text-transform: uppercase; letter-spacing: .08em; margin-top: .6rem; }}
div[data-testid="stMetric"] {{ {glass} border-radius: 18px; padding: 20px 22px; }}
div[data-testid="stMetric"]:hover {{ transform: translateY(-2px); }}
/* equal-height cards: metric fills its (already stretched) column */
[data-testid="stElementContainer"]:has(> [data-testid="stMetric"]) {{ flex: 1 1 auto; display: flex; }}
[data-testid="stElementContainer"] > [data-testid="stMetric"] {{ flex: 1 1 auto; height: 100%; box-sizing: border-box; }}
[data-testid="stMetricLabel"] p {{ color: var(--text2) !important; font-size: 14px !important; font-weight: 500; }}
[data-testid="stMetricValue"] {{ color: var(--text) !important; font-weight: 700; letter-spacing: -0.02em; }}
[data-testid="stForm"], [data-testid="stExpander"] details, .glass, .st-key-glass-box,
[class*="st-key-glass"] {{ {glass} border-radius: 22px !important; }}
[data-testid="stForm"] {{ padding: 28px 28px 22px !important; }}
[data-testid="stExpander"] summary p {{ color: var(--text) !important; font-weight: 600; }}
[data-testid="stFileUploaderDropzone"] {{ background: var(--input) !important; border: 1.5px dashed var(--border-strong) !important; border-radius: 16px !important; }}
[data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small {{ color: var(--text2) !important; }}
[data-testid="stAlert"] > div {{ border-radius: 14px !important; backdrop-filter: blur(20px); }}
[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; border: 1px solid var(--border); box-shadow: var(--shadow-sm); }}
{grid_fix}
iframe {{ border-radius: 12px; color-scheme: {T['scheme']}; }}

/* ---- segmented tabs ---- */
.stTabs [role="tablist"] {{ gap: 4px; padding: 5px; width: fit-content; border-radius: 980px; border-bottom: none;
  background: var(--glass); backdrop-filter: saturate(180%) blur(24px); -webkit-backdrop-filter: saturate(180%) blur(24px);
  border: 1px solid var(--border); box-shadow: var(--shadow-sm); margin-bottom: 1.4rem; }}
.stTabs [data-testid="stTab"] {{ height: auto; padding: 9px 20px; border-radius: 980px; background: transparent; cursor: pointer; }}
.stTabs [data-testid="stTab"] p {{ font-size: 15px; font-weight: 500; color: var(--text2) !important; }}
.stTabs [data-testid="stTab"][aria-selected="true"] {{ background: var(--elevated); box-shadow: var(--shadow-sm); }}
.stTabs [data-testid="stTab"][aria-selected="true"] p {{ color: var(--text) !important; font-weight: 600; }}
.stTabs .react-aria-SelectionIndicator, .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

/* ---- buttons ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius: 980px !important; border: 1px solid var(--border-strong) !important; background: var(--input) !important;
  color: var(--text) !important; font-weight: 500; padding: .5rem 1.15rem; }}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{ transform: translateY(-1px); border-color: var(--accent) !important; }}
button[kind="primary"], button[kind="primaryFormSubmit"], [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {{
  background: var(--accent) !important; border-color: transparent !important; color: #FFFFFF !important; }}
button[kind="primary"] p, button[kind="primaryFormSubmit"] p {{ color: #FFFFFF !important; }}

/* ---- inputs (Streamlit 1.65 react-aria widgets) ---- */
.stSelectbox .react-aria-ComboBox > div, .stMultiSelect .react-aria-ComboBox > div,
[data-testid="stNumberInputContainer"], [data-testid="stDateInputField"], [data-testid="stTextInputRootElement"],
.stTextInput .react-aria-TextField > div, .stTextArea textarea, [data-testid="stFileChip"] {{
  background: var(--input) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; }}
.stSelectbox .react-aria-ComboBox > div:focus-within, .stMultiSelect .react-aria-ComboBox > div:focus-within,
[data-testid="stNumberInputContainer"]:focus-within, [data-testid="stDateInputField"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within, .stTextInput .react-aria-TextField > div:focus-within {{
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }}
.stSelectbox input, .stMultiSelect input, .stNumberInput input, .stTextInput input, .stTextArea textarea,
[data-testid="stDateInputField"] span, [data-testid="stFileChipName"], [data-testid="stFileChip"] span, [data-testid="stFileChip"] small {{
  color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }}
.stSelectbox svg, .stMultiSelect svg, .stNumberInput button svg, [data-testid="stFileChip"] svg {{ fill: var(--text2); color: var(--text2); }}
.stNumberInput button {{ background: transparent !important; border: none !important; color: var(--text2) !important; }}
[data-testid="stMultiSelectTagsContainer"] > span > span:first-child, [data-baseweb="tag"] {{ border-radius: 980px !important; }}
.stCheckbox label:has(input:not(:checked)) > div:first-of-type {{ background-color: var(--input) !important; border: 1px solid var(--border-strong) !important; }}
.st-key-dark_mode label:has(input:not(:checked)) > div:first-of-type {{ background-color: {"rgba(255,255,255,0.22)" if is_dark else "rgba(0,0,0,0.16)"} !important; border: none !important; }}
.st-key-dark_mode label > div:first-of-type > div {{ background-color: #FFFFFF !important; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
.react-aria-Popover, [data-baseweb="popover"] > div, [role="listbox"], [data-baseweb="calendar"], .react-aria-Calendar {{
  background: var(--glass-strong) !important; backdrop-filter: saturate(180%) blur(28px); -webkit-backdrop-filter: saturate(180%) blur(28px);
  border-radius: 14px !important; border: 1px solid var(--border) !important; box-shadow: var(--shadow) !important; color: var(--text) !important; }}
[role="option"] {{ color: var(--text) !important; background-color: transparent; border-radius: 8px; }}
[role="option"]:hover, [role="option"][data-focused], [role="option"][aria-selected="true"] {{ background: var(--accent-soft) !important; }}

/* ---- custom pieces ---- */
.hero {{ padding: 4px 0 22px; }}
.eyebrow {{ font-size: 13px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }}
.hero-title {{ font-size: clamp(32px, 3.6vw, 54px); font-weight: 700; line-height: 1.07; letter-spacing: -0.025em; margin: 10px 0 12px; color: var(--text); }}
.hero-sub {{ font-size: 19px; line-height: 1.45; color: var(--text2); margin: 0; }}
.pill-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }}
.pill {{ {glass} border-radius: 980px; padding: 6px 14px; font-size: 13px; font-weight: 600; color: var(--text); box-shadow: var(--shadow-sm); }}
.pill b {{ color: var(--text2); font-weight: 500; margin-left: 6px; }}
.login-hero {{ text-align: center; margin: 7vh 0 26px; }}
.login-icon {{ {glass} width: 76px; height: 76px; border-radius: 22px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 34px; }}
.login-title {{ font-size: 40px; font-weight: 700; letter-spacing: -0.02em; color: var(--text); margin: 0; }}
.login-sub {{ font-size: 17px; color: var(--text2); margin: 10px 0 0; }}
.user-chip {{ {glass} display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 16px; margin: 6px 0 12px; box-shadow: var(--shadow-sm); }}
.avatar {{ width: 38px; height: 38px; border-radius: 50%; background: var(--accent); color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; }}
.user-chip .who {{ font-weight: 600; color: var(--text); font-size: 15px; line-height: 1.2; }}
.user-chip .role {{ color: var(--text2); font-size: 12px; }}
.legend-pill {{ {glass} display: flex; align-items: center; gap: 10px; border-radius: 980px; padding: 9px 16px; margin-top: 10px; font-size: 14px; font-weight: 500; color: var(--text); box-shadow: var(--shadow-sm); }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 4px; display: inline-block; }}
.result-card {{ {glass} border-radius: 24px; padding: 30px 24px; text-align: center; margin-top: 16px; }}
.result-label {{ color: var(--text2); font-size: 13px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 8px; }}
.result-value {{ font-size: 3rem; font-weight: 700; letter-spacing: -0.03em; line-height: 1.1; }}
.result-meta {{ color: var(--text2); font-size: 14px; margin-top: 10px; }}
.footer-signature {{ position: fixed; bottom: 10px; right: 18px; color: var(--text2); opacity: .45; font-size: .75rem; font-weight: 500;
  letter-spacing: .5px; z-index: 999; user-select: none; pointer-events: none; }}
</style>
<div class="footer-signature">Designed by Danial Hensemmm</div>
""", unsafe_allow_html=True)


def style_fig(fig):
    """Apply the active theme to a Plotly figure (transparent, glass-friendly background)."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T["text"], family=FONT_STACK, size=13),
        legend=dict(font=dict(color=T["text"])),
        hoverlabel=dict(bgcolor=T["elevated"], bordercolor=T["border_strong"], font=dict(color=T["text"], family=FONT_STACK)),
    )
    axis = dict(gridcolor=T["grid"], zerolinecolor=T["grid"], linecolor=T["grid"],
                tickfont=dict(color=T["text2"]), title_font=dict(color=T["text2"]))
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    for tr in fig.data:
        if tr.type == "scatter":
            tr.update(line=dict(color=T["accent"], width=3, shape="spline"),
                      marker=dict(color=T["accent"], size=8, line=dict(color=T["bg"], width=2)),
                      textfont=dict(color=T["text2"]))
        elif tr.type == "pie":
            tr.update(marker=dict(line=dict(color=T["bg"], width=2)))
    return fig


apply_theme(T, IS_DARK)


# --- USER AUTHENTICATION DICTIONARY ---
USERS = {
    "admin_danial": "password123",
    "operator1": "vegasparrow2026",
    "inspector_A": "defect2026",
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

if not st.session_state.authenticated:
    _, toggle_col = st.columns([5, 1])
    toggle_col.toggle("Dark mode", key="dark_mode")
    _, login_col, _ = st.columns([1, 1.1, 1])
    with login_col:
        st.markdown(
            '<div class="login-hero"><div class="login-icon">🔒</div>'
            '<div class="login-title">Restricted Access</div>'
            '<div class="login-sub">IC Package Defect Analytics. Log in with your authorized ID and password.</div></div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Log In", type="primary", width="stretch")

            if submit_button:
                if username_input in USERS and USERS[username_input] == password_input:
                    st.session_state.authenticated = True
                    st.session_state.username = username_input
                    st.success("Login successful! Loading application...")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

    st.stop()

# ==========================================
# SIDEBAR: brand -> main navigation -> data -> dashboard filters -> account
# ==========================================
PAGES = [
    ("dashboard", "Dashboard & Stations", ":material/space_dashboard:"),
    ("painter", "Mapping Painter", ":material/brush:"),
    ("finder", "Unit Finder", ":material/travel_explore:"),
]
if st.session_state.get("page") not in {p[0] for p in PAGES}:
    st.session_state.page = "dashboard"
PAGE = st.session_state.page


def go_to(page):
    st.session_state.page = page


def log_out():
    st.session_state.authenticated = False
    st.session_state.username = ""


# Containers fix the visual order; each one is filled further down the script.
sb_nav = st.sidebar.container(key="sb_nav")
sb_data = st.sidebar.container(key="sb_data")
sb_filters = st.sidebar.container(key="sb_filters")
sb_footer = st.sidebar.container(key="sb_footer")

BRAND_SVG = (
    '<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">'
    '<rect width="34" height="34" rx="9" fill="var(--accent)"/>'
    + "".join(
        f'<rect x="{6 + c * 8}" y="{6 + r * 8}" width="6" height="6" rx="1.6" fill="{col}"/>'
        for r, row in enumerate([["#FFFFFF", "#FFFFFF", "#FFC0CB"], ["#FFFFFF", "#FF4500", "#FFFFFF"], ["#FFA500", "#FFFFFF", "#FFFFFF"]])
        for c, col in enumerate(row)
    )
    + "</svg>"
)

with sb_nav:
    st.markdown(
        f'<div class="brand"><div class="brand-mark">{BRAND_SVG}</div>'
        '<div><div class="brand-name">Stripmap</div><div class="brand-sub">Defect Analytics</div></div></div>'
        '<div class="nav-label">Main</div>',
        unsafe_allow_html=True,
    )
    for page_id, page_label, page_icon in PAGES:
        st.button(page_label, icon=page_icon, width="stretch", on_click=go_to, args=(page_id,),
                  key=f"nav_{page_id}_{'on' if page_id == PAGE else 'off'}")

with sb_footer:
    st.markdown('<div class="nav-label">Account</div>', unsafe_allow_html=True)
    st.toggle("Dark mode", key="dark_mode")
    st.markdown(
        f'<div class="user-chip"><div class="avatar">{st.session_state.username[:1].upper()}</div>'
        f'<div><div class="who">{st.session_state.username}</div><div class="role">Signed in</div></div></div>',
        unsafe_allow_html=True,
    )
    st.button("Log out", icon=":material/logout:", key="logout_btn", width="stretch", on_click=log_out)

# Collapsed state: a slim glass rail with the logo and icon-only navigation (tooltips on hover).
# CSS shows it only while the Streamlit sidebar is collapsed; Streamlit's own expand button sits on its edge.
with st.container(key="mini_rail"):
    st.markdown(f'<div class="rail-brand">{BRAND_SVG}</div>', unsafe_allow_html=True)
    for page_id, page_label, page_icon in PAGES:
        st.button(page_label, icon=page_icon, help=page_label, on_click=go_to, args=(page_id,),
                  key=f"rail_{page_id}_{'on' if page_id == PAGE else 'off'}")

# Status indicator on the nav item + hide dashboard-only filters on other pages
_marked = len(st.session_state.get("selected_painter_units", set()))
_page_css = ""
if _marked:
    _page_css += '[class*="st-key-rail_painter_"] button::after { content: ""; position: absolute; top: 7px; right: 7px; width: 7px; height: 7px; border-radius: 50%; background: var(--accent); }'
    _page_css += (f'[class*="st-key-nav_painter_"] button::after {{ content: "{_marked}"; margin-left: auto; font-size: 11px; '
                  'font-weight: 600; padding: 1px 8px; border-radius: 980px; background: var(--accent-soft); color: var(--accent); }')
if PAGE != "dashboard":
    _page_css += ".st-key-sb_filters { display: none !important; }"
if _page_css:
    st.markdown(f"<style>{_page_css}</style>", unsafe_allow_html=True)

if PAGE == "dashboard":
    st.markdown(
        '<div class="hero"><div class="eyebrow">Stripmap Analytics</div>'
        '<div class="hero-title">Semiconductor Production Line<br>&amp; Stripmap Analytics</div>'
        '<div class="hero-sub">Monitoring for VEGA, SPARROW, SQUID &amp; SOLARIS. One integrated workspace, every unit on every strip.</div>'
        '<div class="pill-row"><span class="pill">VEGA<b>960 units</b></span><span class="pill">SPARROW<b>1,920 units</b></span>'
        '<span class="pill">SQUID<b>1,224 units</b></span><span class="pill">SOLARIS<b>1,292 units</b></span></div></div>',
        unsafe_allow_html=True,
    )

DEVICE_SPECS = {
    "VEGA": {"max_x": 64, "max_y": 15, "total_units": 960, "cols_per_panel": 16},
    "SPARROW": {"max_x": 96, "max_y": 20, "total_units": 1920, "cols_per_panel": 24},
    "SQUID": {"max_x": 72, "max_y": 17, "total_units": 1224, "cols_per_panel": 18},
    "SOLARIS": {"max_x": 76, "max_y": 17, "total_units": 1292, "cols_per_panel": 19},
}

ALIASES = {
    "lot": "MESLotID", "lotid": "MESLotID", "meslotid": "MESLotID", "lot_id": "MESLotID",
    "ttime": "Timestamp", "timestamp": "Timestamp", "datetime": "Timestamp", "date": "Timestamp",
    "proddate": "Timestamp", "reportdate": "Timestamp",
    "x": "X", "xcoord": "X", "x_coordinate": "X", "xposition": "X", "stripx": "X", "strip_x": "X",
    "y": "Y", "ycoord": "Y", "y_coordinate": "Y", "yposition": "Y", "stripy": "Y", "strip_y": "Y",
    "device": "Device", "devicecategory": "Device", "product": "Device", "model": "Device",
    "usmdevice": "Device", "usm_device": "Device",
    "code": "RejectCode", "rejectcode": "RejectCode", "defectcode": "RejectCode",
    "operin": "WB_In", "qty": "Qty",
    "userrejectcode": "UserRejectCode", "user_reject_code": "UserRejectCode",
    "ifxlotno": "IFXLotNo", "stripid": "StripID",
    "ta_yield_loss_%": "TA_Yield_Loss_Pct"
}

REJECT_CODE_MAPPING = {
    207: "207 - ABF (ASIC BOND FAIL)",
    316: "316 - NO MEMS",
    317: "317 - MBF (MEMS BOND FAIL)",
    315: "315 - Unprocessed",
    314: "314 - NSOL (non stick on l)",
    215: "215 - NSOP (non stick on pad)",
    230: "230 - Others",
    202: "202 - TA : PARTICLES (environment)",
    233: "233 - CS : CORNER SHOWN (solder dispense)",
    210: "210 - EC : EPOXY COVERAGE (coating)",
    216: "216 - MB : MISSING BOND (wire bond)",
    302: "302 - ISS : INSUFFICIENT SOLDERPASTE",
    206: "206 - ND : NO DIE (die attach)",
    269: "269 - MSO : MISSING SOLDER",
    236: "236 - NL : NO LID (lid attach)",
    238: "238 - LP : LID PLACEMENT",
    239: "239 - LD : LID DEFORMED",
    240: "240 - LR : LID ROTATION",
    241: "241 - LCK : LCP LID CRACK",
    245: "245 - CML : CONTAMINATED ON LCP LID SURFACE",
    276: "276 - WLO : WRONG LID ORIENTATION",
    277: "277 - EOL : EPOXY ON LID",
    278: "278 - LT : LID TILT",
    306: "306 - LSC : SCRATCHES ON METAL LID",
    "EXS": "EXS - Extra / Excess",
    "MBP": "MBP - Missing Wire / MBP",
    "SB": "SB - Solder Ball",
    "BDT": "BDT - Bond Tail",
    "NBS": "NBS - No Ball Size",
    "NC": "NC - No Coating",
}

STATION_CODES = {
    "Die Attach": [
        207, 316, 317, 315,
        "207 - ABF (ASIC BOND FAIL)", "316 - NO MEMS", "317 - MBF (MEMS BOND FAIL)", "315 - Unprocessed",
        "ABF", "NO_MEMS", "MBF", "UNPROCESSED"
    ],
    "Wire Bond": [
        314, 215, 230, 315, "MBP", "BDT", "NBS",
        "314 - NSOL (non stick on l)", "215 - NSOP (non stick on pad)", "230 - Others", "315 - Unprocessed",
        "NSOL", "NSOP", "OTHERS", "UNPROCESSED", "MBP - Missing Wire / MBP", "BDT - Bond Tail", "NBS - No Ball Size"
    ],
    "Strip AOI": [
        202, 233, 210, 216, 302, 206, 269, "EXS", "SB", "NC",
        "202 - TA : PARTICLES (environment)", "233 - CS : CORNER SHOWN (solder dispense)", 
        "210 - EC : EPOXY COVERAGE (coating)", "216 - MB : MISSING BOND (wire bond)", 
        "302 - ISS : INSUFFICIENT SOLDERPASTE", "206 - ND : NO DIE (die attach)", "269 - MSO : MISSING SOLDER",
        "TA", "CS", "EC", "MB", "ISS", "ND", "MSO", "EXS - Extra / Excess", "SB - Solder Ball", "NC - No Coating"
    ],
    "Lid AOI": [
        236, 238, 239, 240, 241, 245, 276, 277, 278, 306,
        "236 - NL : NO LID (lid attach)", "238 - LP : LID PLACEMENT", "239 - LD : LID DEFORMED", 
        "240 - LR : LID ROTATION", "241 - LCK : LCP LID CRACK", "245 - CML : CONTAMINATED ON LCP LID SURFACE", 
        "276 - WLO : WRONG LID ORIENTATION", "277 - EOL : EPOXY ON LID", "278 - LT : LID TILT", "306 - LSC : SCRATCHES ON METAL LID",
        "NL", "LP", "LD", "LR", "LCK", "CML", "WLO", "EOL", "LT", "LSC"
    ],
}

def clean_columns(df):
    df = df.copy()
    renamed = {}
    for c in df.columns:
        key = re.sub(r"[^a-z0-9_]", "", str(c).strip().lower().replace(" ", "_"))
        renamed[c] = ALIASES.get(key, str(c).strip())
    df = df.rename(columns=renamed)
    return df.loc[:, ~df.columns.duplicated()]

def normalize_device(value):
    s = str(value).strip().upper()
    if "SPARROW" in s or "U9927" in s:
        return "SPARROW"
    if "VEGA" in s or "U9921B" in s:
        return "VEGA"
    if "SOLARIS" in s:
        return "SOLARIS"
    if "SQUID" in s:
        return "SQUID"
    return "VEGA"

def unit_number(x, y, device_name="VEGA"):
    spec = DEVICE_SPECS.get(device_name, DEVICE_SPECS["VEGA"])
    max_x, max_y = spec["max_x"], spec["max_y"]
    x, y = int(x), int(y)
    
    if x < 1 or x > max_x or y < 1 or y > max_y:
        return 0
        
    x_offset = max_x - x
    pair_index = x_offset // 2
    is_ascending = (x_offset % 2) == 1
    total = max_x * max_y
    top_unit = total - (pair_index * 2 * max_y) - ((2 * max_y - 1) if is_ascending else 0)
    return top_unit + ((y - 1) if is_ascending else -(y - 1))

def parse_production_dates(values):
    parsed = pd.to_datetime(values, errors="coerce")
    numeric = pd.to_numeric(values, errors="coerce")
    serial_mask = numeric.between(20000, 80000)
    if serial_mask.any():
        parsed = pd.Series(parsed, index=values.index)
        parsed.loc[serial_mask] = pd.to_datetime(
            numeric.loc[serial_mask], unit="D", origin="1899-12-30", errors="coerce"
        )
    return pd.to_datetime(parsed, errors="coerce")

def get_severity(c):
    if c == 0: return "Zero"
    elif 1 <= c <= 10: return "Clean"
    elif 11 <= c <= 20: return "Moderate"
    elif 21 <= c <= 30: return "High"
    else: return "Critical"

def severity_counts(coord_rejects, max_x, max_y, n_lots):
    """Count units per severity class over the full X*Y grid.
    Every active lot shares the same aggregated grid, so the single-grid
    count is multiplied by n_lots (same result as building one grid per lot)."""
    grid_counts = [int(coord_rejects.get((x, y), 0)) for x in range(1, max_x + 1) for y in range(1, max_y + 1)]
    sev = pd.Series([get_severity(c) for c in grid_counts]).value_counts() * n_lots
    out = sev.reset_index()
    out.columns = ["Severity", "Total"]
    return out

def load_single_excel_file(upload_file):
    xls = pd.ExcelFile(upload_file)
    main_sheet_name = "UGP_IFX_VISCO_Rejects_Overall" if "UGP_IFX_VISCO_Rejects_Overall" in xls.sheet_names else xls.sheet_names[0]
    df_raw = pd.read_excel(upload_file, sheet_name=main_sheet_name)
    df_raw = clean_columns(df_raw)

    avg_map = pd.DataFrame()
    if "Average" in xls.sheet_names:
        df_avg = pd.read_excel(upload_file, sheet_name="Average")
        df_avg = clean_columns(df_avg)
        req_cols = [c for c in ["MESLotID", "WB_In", "TA_Yield_Loss_Pct"] if c in df_avg.columns]
        if "MESLotID" in req_cols:
            avg_map = df_avg.groupby("MESLotID", as_index=False).agg({
                col: "max" for col in req_cols if col != "MESLotID"
            })

    return prepare_data(df_raw, avg_map)

def prepare_data(df, avg_map=None):
    df = clean_columns(df)
    
    if "Device" in df.columns and "DeviceID" not in df.columns:
        df["DeviceID"] = df["Device"].astype(str)
    if "X" in df.columns and "SourceX" not in df.columns:
        df["SourceX"] = df["X"]
    if "Y" in df.columns and "SourceY" not in df.columns:
        df["SourceY"] = df["Y"]
        
    required_defaults = [
        ("MESLotID", "UNASSIGNED"),
        ("X", np.nan),
        ("Y", np.nan),
        ("Device", "VEGA"),
        ("DeviceID", "VEGA"),
        ("Timestamp", pd.NaT),
        ("WB_In", 0),
        ("Qty", 1),
        ("UserRejectCode", "Unspecified"),
        ("TA_Yield_Loss_Pct", np.nan)
    ]
    for col, default in required_defaults:
        if col not in df.columns:
            df[col] = default

    def parse_user_code(val):
        sval = str(val).strip()
        if sval in REJECT_CODE_MAPPING:
            return REJECT_CODE_MAPPING[sval]
        if sval.upper() in REJECT_CODE_MAPPING:
            return REJECT_CODE_MAPPING[sval.upper()]
        try:
            ival = int(float(sval))
            if ival in REJECT_CODE_MAPPING:
                return REJECT_CODE_MAPPING[ival]
        except:
            pass
        for k, v in REJECT_CODE_MAPPING.items():
            if str(k).upper() == sval.upper() or sval.upper() in v.upper():
                return v
        return sval

    df["UserRejectCode_Str"] = df["UserRejectCode"].apply(parse_user_code)
    df["RejectCode_Str"] = df["UserRejectCode_Str"]

    df["Device_Category"] = df["DeviceID"].map(normalize_device)
    df["Device"] = df["Device_Category"]
    df["X"] = pd.to_numeric(df["X"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df["Y"] = pd.to_numeric(df["Y"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    df["MESLotID"] = df["MESLotID"].fillna("UNASSIGNED").astype(str).str.strip()
    df["Timestamp"] = parse_production_dates(df["Timestamp"])
    
    if avg_map is not None and not avg_map.empty:
        df = df.merge(avg_map, on="MESLotID", how="left", suffixes=("", "_lookup"))
        if "WB_In_lookup" in df.columns:
            df["WB_In"] = df["WB_In_lookup"].fillna(df["WB_In"])
            df = df.drop(columns=["WB_In_lookup"])
        if "TA_Yield_Loss_Pct_lookup" in df.columns:
            df["TA_Yield_Loss_Pct"] = df["TA_Yield_Loss_Pct_lookup"].fillna(df["TA_Yield_Loss_Pct"])
            df = df.drop(columns=["TA_Yield_Loss_Pct_lookup"])

    df["WB_In"] = pd.to_numeric(df["WB_In"], errors="coerce").fillna(0)
    df["TA_Yield_Loss_Pct"] = pd.to_numeric(df["TA_Yield_Loss_Pct"], errors="coerce")
    
    if "Qty" not in df.columns:
        df["Qty"] = 1
    else:
        df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(1)
    
    return df

def sidebar_multiselect_all(label, options, key, icon=None):
    """Collapsible multiselect group with Select all / Clear.
    The header shows a summary, e.g. "Production lots · 214 of 1,347".
    Empty selection is treated downstream as 'no filter' (= everything)."""
    options = sorted(set(options))
    prev = st.session_state.get(key)
    if prev is None:
        st.session_state[key] = options[:]
    else:
        kept = [o for o in prev if o in options]
        st.session_state[key] = kept if (kept or not prev) else options[:]
    n_sel, n_all = len(st.session_state[key]), len(options)
    summary = f"All {n_all:,}" if n_sel in (0, n_all) else f"{n_sel:,} of {n_all:,}"
    with st.expander(f"{label} · {summary}", key=f"exp_{key}", icon=icon):
        c1, c2 = st.columns(2)
        c1.button("Select all", key=f"{key}_all", width="stretch", type="tertiary",
                  on_click=lambda: st.session_state.__setitem__(key, options[:]))
        c2.button("Clear", key=f"{key}_clr", width="stretch", type="tertiary",
                  on_click=lambda: st.session_state.__setitem__(key, []))
        return st.multiselect(label, options=options, key=key, label_visibility="collapsed",
                              placeholder=f"All {label.lower()}")


with sb_data:
    st.markdown('<div class="nav-label">Data</div>', unsafe_allow_html=True)
    uploaded_master = st.file_uploader("Master file (Rejects + Average sheets)", type=["xlsx"],
                                       key=f"master_excel_uploader_{st.session_state.get('uploader_nonce', 0)}")
    
    if uploaded_master is not None:
        upload_key = f"{uploaded_master.name}:{uploaded_master.size}"
        if st.session_state.get("loaded_upload_key") != upload_key:
            try:
                with st.spinner("Processing master file & matching Average sheet lookup..."):
                    df_loaded = load_single_excel_file(uploaded_master)
                    st.session_state.raw_data = df_loaded
                    st.session_state.loaded_upload_key = upload_key
                    st.session_state.pop("defect_editor", None)
                    st.success(f"Loaded {len(df_loaded):,} rows successfully.")
            except Exception as exc:
                st.error(f"Could not read master file: {exc}")

    _rows = len(st.session_state.raw_data) if "raw_data" in st.session_state else 0
    st.markdown(
        f'<div class="data-status"><span class="dot {"on" if _rows else "off"}"></span>'
        f'{f"{_rows:,} rows loaded" if _rows else "No data loaded"}</div>',
        unsafe_allow_html=True,
    )
    enable_auto_refresh = st.toggle("Auto-refresh every 30s", value=False, key="auto_refresh")
    if enable_auto_refresh and st_autorefresh:
        st_autorefresh(interval=30000, key="datarefresh")

# ------------------------------------------
# PAGE: MAPPING PAINTER (no data needed)
# ------------------------------------------
if PAGE == "painter":
    st.subheader("🎨 Mapping Painter & Reference Viewer")
    painter_device = st.selectbox("Select Device Category for Painting", ["VEGA", "SPARROW", "SQUID", "SOLARIS"], index=0, key="painter_device_select")
    
    p_spec = DEVICE_SPECS[painter_device]
    p_max_x, p_max_y = p_spec["max_x"], p_spec["max_y"]
    p_cols_per_panel = p_spec["cols_per_panel"]

    st.caption(f"Device: {painter_device} ({p_spec['total_units']} Units). Click on any unit tile to toggle red (Reject).")

    if "selected_painter_units" not in st.session_state:
        st.session_state.selected_painter_units = set()

    query_params = st.query_params
    if "paint_unit" in query_params:
        try:
            u_clicked = int(query_params["paint_unit"])
            if u_clicked in st.session_state.selected_painter_units:
                st.session_state.selected_painter_units.remove(u_clicked)
            else:
                st.session_state.selected_painter_units.add(u_clicked)
        except ValueError:
            pass
        st.query_params.clear()
        st.rerun()

    if st.button("🗑️ Reset All Marked Units"):
        st.session_state.selected_painter_units = set()
        st.rerun()

    with st.container(border=True, key="glass_painter_map"):
        p_panel_definitions = [
            ("Panel 4", list(range(p_max_x, p_max_x - p_cols_per_panel, -1))),
            ("Panel 3", list(range(p_max_x - p_cols_per_panel, p_max_x - 2*p_cols_per_panel, -1))),
            ("Panel 2", list(range(p_max_x - 2*p_cols_per_panel, p_max_x - 3*p_cols_per_panel, -1))),
            ("Panel 1", list(range(p_max_x - 3*p_cols_per_panel, 0, -1))),
        ]

        painter_html_panels = []
        for panel_name, x_values in p_panel_definitions:
            tile_html = []
            x_header_html = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_values])
        
            for y in range(1, p_max_y + 1):
                for x in x_values:
                    u_id = unit_number(x, y, painter_device)
                    is_marked = u_id in st.session_state.selected_painter_units
                    bg_color = "#FF0000" if is_marked else "#008000"
                    border_style = f"2px solid {T['mark_border']}" if is_marked else f"1px solid {T['tile_border']}"
                
                    tooltip = f"Unit: {u_id} (X: {x}, Y: {y}) - Click to toggle"
                    tile_html.append(
                        f'<div class="unit" style="background:{bg_color}; border:{border_style};" '
                        f'title="{tooltip}" onclick="try {{ window.parent.history.pushState({{}}, \'\', \'?paint_unit={u_id}\'); window.parent.dispatchEvent(new Event(\'popstate\')); }} catch(e) {{ window.parent.location.href = window.parent.location.pathname + \'?paint_unit={u_id}\'; }}">{u_id}</div>'
                    )
        
            x_footer_html = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_values])
        
            painter_html_panels.append(
                f'<section class="panel"><div class="panel-title">{panel_name}</div>'
                f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_values)}, 22px);">{x_header_html}</div>'
                f'<div class="panel-grid" style="grid-template-columns: repeat({len(x_values)}, 22px);">{"".join(tile_html)}</div>'
                f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_values)}, 22px);">{x_footer_html}</div></section>'
            )

        painter_y_axis_labels_html = "".join([f'<div class="axis-y-label">{y}</div>' for y in range(1, p_max_y + 1)])
        painter_y_axis_html = f'<section class="y-panel"><div class="panel-title">Y</div><div class="axis-x-row"></div><div class="y-axis-grid">{painter_y_axis_labels_html}</div><div class="axis-x-row"></div></section>'

        painter_map_html = f'''<!DOCTYPE html>
        <html><head><meta charset="utf-8">
        <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; background: transparent; color: {T["text"]}; font-family: {FONT_STACK}; color-scheme: {T["scheme"]}; }}
        .matrix-scroll {{ width: 100%; overflow-x: auto; overflow-y: hidden; padding: 6px 4px 18px 4px; }}
        .panels {{ display: flex; align-items: flex-start; gap: 10px; width: max-content; padding-right: 15px; }}
        .panel {{ flex: 0 0 auto; }}
        .y-panel {{ flex: 0 0 auto; margin-left: 2px; }}
        .panel-title {{ text-align: center; color: {T["text"]}; font-size: 12px; font-weight: 600; padding: 0 0 5px 0; }}
        .axis-x-row {{ display: grid; gap: 2px; margin: 4px 0; height: 10px; }}
        .axis-x-label {{ width: 22px; text-align: center; color: {T["text2"]}; font-size: 8px; font-weight: 600; line-height: 10px; }}
        .panel-grid {{ display: grid; grid-auto-rows: 22px; gap: 2px; }}
        .y-axis-grid {{ display: grid; grid-template-columns: 20px; grid-auto-rows: 22px; gap: 2px; }}
        .axis-y-label {{ height: 22px; display: flex; align-items: center; justify-content: center; color: {T["text2"]}; font-size: 9px; font-weight: 600; }}
        .unit {{ width: 22px; height: 22px; border-radius: 2px; display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-size: 7px; line-height: 1; font-weight: 600; cursor: pointer; user-select: none; }}
        .unit:hover {{ outline: 2px solid {T["mark_border"]}; outline-offset: 1px; transform: scale(1.10); position: relative; z-index: 5; }}
        </style></head>
        <body><div class="matrix-scroll"><div class="panels">{''.join(painter_html_panels)}{painter_y_axis_html}</div></div>
        </body></html>'''
    
        st.iframe(painter_map_html, height=540)

    st.markdown("---")
    st.subheader("📋 StripMap Reference Image Viewer")
    st.caption("Upload your reference stripmap image here for direct visual comparison.")
    
    ref_upload = st.file_uploader("Upload Reference StripMap Image", type=["png", "jpg", "jpeg"], key="ref_uploader")
    if ref_upload is not None:
        ref_image = Image.open(ref_upload)
        st.image(ref_image, caption="Reference StripMap Screenshot", width="stretch")

    st.markdown("---")
    selected_count = len(st.session_state.selected_painter_units)
    st.markdown(f"### 🎯 Marked Reject Units: `{selected_count}` / {p_spec['total_units']}")

    if selected_count > 0:
        rows = []
        for u in sorted(st.session_state.selected_painter_units):
            found_x, found_y = None, None
            for x in range(1, p_max_x + 1):
                for y in range(1, p_max_y + 1):
                    if unit_number(x, y, painter_device) == u:
                        found_x, found_y = x, y
                        break
                if found_x:
                    break
            rows.append({
                "Device": painter_device,
                "Unit No.": u,
                "X": found_x,
                "Y": found_y,
                "Status": "REJECT (User Marked)"
            })
        
        marked_df = pd.DataFrame(rows)
        st.dataframe(marked_df, width="stretch", hide_index=True)
        
        st.download_button(
            "📥 Download Marked Units Table (CSV)",
            marked_df.to_csv(index=False).encode("utf-8"),
            f"marked_{painter_device}_rejects.csv",
            "text/csv",
            type="primary"
        )
    else:
        st.info("Click on any unit tile on the grid map above to mark it as reject (turns red).")

# ------------------------------------------
# PAGE: UNIT FINDER (no data needed)
# ------------------------------------------
if PAGE == "finder":
    st.subheader("🔍 Unit Finder & Coordinate Lookup")
    st.caption("Look up unit numbers from X & Y coordinates, or find X & Y coordinates from a unit number for specific device specifications.")

    finder_device = st.selectbox(
        "Select Device Category for Lookup",
        ["VEGA", "SPARROW", "SQUID", "SOLARIS"],
        index=0,
        key="finder_device_filter"
    )

    f_spec = DEVICE_SPECS[finder_device]
    f_max_x, f_max_y, f_total = f_spec["max_x"], f_spec["max_y"], f_spec["total_units"]

    st.markdown(f"**Selected Device**: `{finder_device}` — Total Units: `{f_total}` | Max X: `{f_max_x}` | Max Y: `{f_max_y}`")
    st.markdown("---")

    f_col1, f_col2 = st.columns(2, gap="large")

    with f_col1:
        st.markdown("### 📍 Lookup by X & Y Coordinates")
        st.markdown(f"Enter coordinates $(1 \\le X \\le {f_max_x}, 1 \\le Y \\le {f_max_y})$ to get the corresponding Unit Number.")
        
        fx_in, fy_in = st.columns(2)
        with fx_in:
            search_x = st.number_input("X Coordinate", min_value=1, max_value=f_max_x, value=1, step=1, key="search_x_input")
        with fy_in:
            search_y = st.number_input("Y Coordinate", min_value=1, max_value=f_max_y, value=1, step=1, key="search_y_input")
        
        calculated_unit = unit_number(search_x, search_y, finder_device)
        
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">Resulting Unit Number</div>
                <div class="result-value" style="color:var(--success)">{calculated_unit}</div>
                <div class="result-meta">Device: <b>{finder_device}</b> · X: {search_x} · Y: {search_y}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f_col2:
        st.markdown("### 🔢 Lookup by Unit Number")
        st.markdown(f"Enter a Unit Number $(1 \\le \\text{{Unit}} \\le {f_total})$ to find its X & Y coordinates.")
        
        search_unit = st.number_input("Unit Number", min_value=1, max_value=f_total, value=1, step=1, key="search_unit_input")
        
        found_xy = None
        for x in range(1, f_max_x + 1):
            for y in range(1, f_max_y + 1):
                if unit_number(x, y, finder_device) == search_unit:
                    found_xy = (x, y)
                    break
            if found_xy:
                break
        
        if found_xy:
            rx, ry = found_xy
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="result-label">Resulting Coordinates</div>
                    <div class="result-value" style="color:var(--accent)">X {rx} &nbsp;·&nbsp; Y {ry}</div>
                    <div class="result-meta">Device: <b>{finder_device}</b> · Unit ID: {search_unit}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("Unit number not found in grid layout.")

# Painter / Finder are done above. The dashboard filters below are still built (hidden on
# those pages) so their selections are kept when the user comes back to the dashboard.
EMPTY_STATE = (
    '<div class="result-card empty-state"><div class="login-icon">📂</div>'
    '<div class="login-title" style="font-size:28px">No data loaded yet</div>'
    '<div class="login-sub">Upload <code>UGP_IFX_VISCO_Rejects_Overall.xlsx</code> in the sidebar under <b>Data</b> to start.<br>'
    'Mapping Painter and Unit Finder work without data.</div></div>'
)
if "raw_data" not in st.session_state:
    if PAGE == "dashboard":
        st.markdown(EMPTY_STATE, unsafe_allow_html=True)
    st.stop()

raw = st.session_state.raw_data.copy()

if PAGE == "dashboard":
    with st.expander("Open data editor", expanded=False):
        edited = st.data_editor(
            raw, num_rows="dynamic", width="stretch", height=300,
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm"),
                "X": st.column_config.NumberColumn("X coordinate", min_value=1, step=1),
                "Y": st.column_config.NumberColumn("Y coordinate", min_value=1, step=1),
            },
            key="defect_editor"
        )
        c1, c2, c3, _ = st.columns([1, 1.7, 1.4, 3], vertical_alignment="center")
        if c1.button("Apply edits", type="primary"):
            st.session_state.raw_data = prepare_data(edited)
            st.success("Edits applied successfully.")
            st.rerun()
        c2.download_button("Download current data as CSV", raw.to_csv(index=False).encode("utf-8"), "defect_logs.csv", "text/csv")
        with c3.popover("🗑️ Delete all data"):
            st.markdown(f"**Delete all {len(raw):,} rows?**")
            st.caption("This empties the data loaded in the app. Your Excel file on disk is not changed. "
                       "Download the CSV first if you want a copy.")
            if st.button("Yes, delete all data", type="primary", key="confirm_delete_all", width="stretch"):
                st.session_state.raw_data = raw.iloc[0:0].copy()
                for k in ("defect_editor", "loaded_upload_key", "gen_lots", "gen_ucode", "gen_date", "gen_date_span"):
                    st.session_state.pop(k, None)
                st.session_state.uploader_nonce = st.session_state.get("uploader_nonce", 0) + 1
                st.rerun()

if raw.empty:
    if PAGE == "dashboard":
        st.markdown(EMPTY_STATE, unsafe_allow_html=True)
    st.stop()

# ==========================================
# SHARED TOP FILTERS FOR 2D DASHBOARD
# ==========================================
with sb_filters:
    filter_head = st.container(key="filter_head")  # filled after the filters (needs the active count)
    category_options = ["VEGA", "SPARROW", "SQUID", "SOLARIS"]
    dev_c1, dev_c2 = st.columns(2, gap="small")
    selected_category = dev_c1.selectbox("Device", category_options, index=0, key="gen_cat")

    spec = DEVICE_SPECS[selected_category]
    max_x, max_y = spec["max_x"], spec["max_y"]

    raw_device_options = ["ALL"] + sorted(raw[raw["Device_Category"] == selected_category]["DeviceID"].dropna().unique().tolist())
    selected_device_model = dev_c2.selectbox("Model / Variant", raw_device_options, index=0, key="gen_dev")

    cat_base_raw = raw[raw["Device_Category"] == selected_category]
    if selected_device_model != "ALL":
        cat_base_raw = cat_base_raw[cat_base_raw["DeviceID"] == selected_device_model]

    lot_options = sorted(cat_base_raw["MESLotID"].dropna().unique().tolist())


    master_all_station_codes = sorted(list(set(
        [str(x) for x in STATION_CODES["Die Attach"] + STATION_CODES["Wire Bond"] + STATION_CODES["Strip AOI"] + STATION_CODES["Lid AOI"]]
    )))

    general_base_raw = cat_base_raw[cat_base_raw["UserRejectCode_Str"].isin(master_all_station_codes)]
    available_general_codes = sorted(list(set(str(x) for x in general_base_raw["UserRejectCode_Str"].dropna().unique().tolist())))
    if not available_general_codes:
        available_general_codes = sorted(list(set(str(x) for x in cat_base_raw["UserRejectCode_Str"].dropna().unique().tolist())))


    valid_dates = raw["Timestamp"].dropna()
    if len(valid_dates):
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
    else:
        min_date, max_date = date.today(), date.today()
    # Reset the range to the full span whenever newly loaded data has a different date span.
    if st.session_state.get("gen_date_span") != (min_date, max_date) or "gen_date" not in st.session_state:
        st.session_state["gen_date"] = (min_date, max_date)
        st.session_state["gen_date_span"] = (min_date, max_date)


    def apply_quick_range(days, base_df, latest):
        """Set the date filter to the last `days` days ending at the latest production date,
        and select only the lots produced inside that window."""
        start = latest - timedelta(days=days - 1)
        st.session_state["gen_date"] = (start, latest)
        in_window = base_df[base_df["Timestamp"].dt.date.between(start, latest)]
        st.session_state["gen_lots"] = sorted(in_window["MESLotID"].dropna().unique().tolist())


    date_col, latest_col, week_col = st.columns([2.25, 1, 1], vertical_alignment="bottom", gap="small")
    date_range = date_col.date_input("Production date", key="gen_date")
    latest_col.button("Latest Date", key="btn_latest_date", width="stretch", help=f"Only {max_date:%Y-%m-%d}",
                      on_click=apply_quick_range, args=(1, cat_base_raw, max_date))
    week_col.button("Latest Week", key="btn_latest_week", width="stretch",
                    help=f"{max_date - timedelta(days=6):%Y-%m-%d} to {max_date:%Y-%m-%d}",
                    on_click=apply_quick_range, args=(7, cat_base_raw, max_date))

    selected_lots = sidebar_multiselect_all("Production lots", lot_options, "gen_lots", icon=":material/inventory_2:")
    selected_user_codes = sidebar_multiselect_all("Reject codes", available_general_codes, "gen_ucode", icon=":material/report:")

    def reset_filters():
        for k in ("gen_lots", "gen_ucode"):
            st.session_state.pop(k, None)
        st.session_state["gen_dev"] = "ALL"
        st.session_state["gen_date"] = st.session_state.get("gen_date_span", (min_date, max_date))

    full_span = st.session_state.get("gen_date_span")
    active_filters = sum([
        selected_device_model != "ALL",
        0 < len(selected_lots) < len(lot_options),
        0 < len(selected_user_codes) < len(available_general_codes),
        isinstance(date_range, (tuple, list)) and tuple(date_range) != tuple(full_span or ()),
    ])
    with filter_head:
        h1, h2 = st.columns([3, 1], vertical_alignment="center")
        badge = f'<span class="filter-count">{active_filters}</span>' if active_filters else ""
        h1.markdown(f'<div class="nav-label filter-label">Dashboard filters{badge}</div>', unsafe_allow_html=True)
        h2.button("Reset", key="btn_reset_filters", type="tertiary", width="stretch", on_click=reset_filters,
                  disabled=not active_filters, help="Reset device model, dates, lots and codes")

# Apply Filter
filtered = general_base_raw.copy()
if selected_lots:
    filtered = filtered[filtered["MESLotID"].isin(selected_lots)]
if selected_user_codes:
    filtered = filtered[filtered["UserRejectCode_Str"].isin(selected_user_codes)]

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    if filtered["Timestamp"].notna().any():
        filtered = filtered[
            filtered["Timestamp"].isna() |
            ((filtered["Timestamp"].dt.date >= start_date) & (filtered["Timestamp"].dt.date <= end_date))
        ]

filtered["X_internal"] = filtered["X"].abs()
filtered["Y_internal"] = filtered["Y"]
valid = filtered[
    filtered["X_internal"].between(1, max_x) &
    filtered["Y_internal"].between(1, max_y)
].copy()

capacity = max_x * max_y
unique_affected = valid[["DeviceID", "MESLotID", "X_internal", "Y_internal"]].drop_duplicates().shape[0] if not valid.empty else 0
lot_device_count = filtered[["DeviceID", "MESLotID"]].drop_duplicates().shape[0]
total_max_units = max(1, lot_device_count * capacity)
yield_pct = max(0.0, 100.0 - (unique_affected / total_max_units * 100.0))
reject_count = int(filtered["Qty"].sum())
lots_evaluated = filtered["MESLotID"].nunique()
ratio_pct = (unique_affected / total_max_units * 100.0) if total_max_units else 0

coordinate_rejects = valid.groupby(["X_internal", "Y_internal"])["Qty"].sum().to_dict() if not valid.empty else {}

stations_list = ["Die Attach", "Wire Bond", "Strip AOI", "Lid AOI"]

# ------------------------------------------
# PAGE: 2D DASHBOARD & STATIONS
# ------------------------------------------
if PAGE == "dashboard":
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Rejects (Qty)", f"{reject_count:,}")
    k2.metric("Lots Evaluated", f"{lots_evaluated:,}")
    k3.metric("Affected Unit Coordinates", f"{unique_affected:,}", f"{ratio_pct:.2f}% of lot capacity")
    k4.metric("Estimated Yield", f"{yield_pct:.2f}%")

    st.subheader(f"Defect Severity & Daily Average TA Yield Loss Analytics ({selected_category})")

    if not filtered.empty:
        col_pie, col_trend = st.columns(2, border=True)
        with col_pie:
            st.markdown("#### Defect Proportion by Category")
            if not valid.empty:
                n_active_lots = valid[["DeviceID", "MESLotID"]].drop_duplicates().shape[0]
                sev_counts = severity_counts(coordinate_rejects, max_x, max_y, n_active_lots)
                fig_pie = px.pie(
                    sev_counts, names="Severity", values="Total", hole=0.4,
                    color="Severity", 
                    color_discrete_map={
                        "Zero": "#008000", "Clean": "#FFC0CB", "Moderate": "#FFA500", "High": "#FF4500", "Critical": "#FF0000"
                    }
                )
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(style_fig(fig_pie), theme=None, width="stretch")
            else:
                st.info("No coordinate data available for Pie Chart.")

        with col_trend:
            st.markdown("#### Daily Average TA Yield Loss (%) Over Time")
            if filtered["Timestamp"].notna().any():
                trend_df = filtered.dropna(subset=["Timestamp"]).copy()
                trend_df["Date"] = trend_df["Timestamp"].dt.date
                
                if "TA_Yield_Loss_Pct" in trend_df.columns and trend_df["TA_Yield_Loss_Pct"].notna().any():
                    trend_df["TA_Loss_Scaled"] = np.where(
                        trend_df["TA_Yield_Loss_Pct"] <= 1.0,
                        trend_df["TA_Yield_Loss_Pct"] * 100.0,
                        trend_df["TA_Yield_Loss_Pct"]
                    )
                    daily_trend = trend_df.groupby("Date").agg(
                        Avg_TA_Loss=("TA_Loss_Scaled", "mean"),
                        Total_Rejects=("Qty", "sum"),
                        Total_WB_In=("WB_In", "max"),
                        Total_Lots=("MESLotID", "nunique")
                    ).reset_index()
                else:
                    lot_summary = trend_df.groupby(["Date", "MESLotID"]).agg(
                        Lot_Rejects=("Qty", "sum"),
                        WB_In=("WB_In", "max")
                    ).reset_index()
                    lot_summary["Lot_Reject_Pct"] = np.where(
                        lot_summary["WB_In"] > 0,
                        (lot_summary["Lot_Rejects"] / lot_summary["WB_In"]) * 100.0,
                        0.0
                    )
                    daily_trend = lot_summary.groupby("Date").agg(
                        Avg_TA_Loss=("Lot_Reject_Pct", "mean"),
                        Total_Rejects=("Lot_Rejects", "sum"),
                        Total_WB_In=("WB_In", "sum"),
                        Total_Lots=("MESLotID", "nunique")
                    ).reset_index()

                fig_trend = px.line(
                    daily_trend, 
                    x="Date", 
                    y="Avg_TA_Loss", 
                    markers=True, 
                    labels={"Avg_TA_Loss": "Average TA Yield Loss (%)"}
                )
                
                fig_trend.update_traces(
                    customdata=daily_trend[["Total_Rejects", "Total_WB_In", "Total_Lots"]],
                    hovertemplate=(
                        "<b>Date</b>: %{x}<br>"
                        "<b>Average TA Yield Loss</b>: %{y:.2f}%<br>"
                        "<b>Total Lots</b>: %{customdata[2]:,}<br>"
                        "<b>Total Rejects (Qty)</b>: %{customdata[0]:,}<br>"
                        "<b>Total Input (WB In)</b>: %{customdata[1]:,}<br>"
                        "<extra></extra>"
                    ),
                    text=daily_trend["Avg_TA_Loss"].round(2).astype(str) + "%",
                    textposition="top center",
                    mode="lines+markers+text"
                )
                
                fig_trend.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)", 
                    
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(style_fig(fig_trend), theme=None, width="stretch")
            else:
                st.info("Timestamp data not available for trend chart.")

    # General 2D Grid Map Generator
    st.markdown("---")
    with st.container(border=True, key="glass_unit_map"):
        st.subheader(f"2D General Individual Unit Map ({selected_category}: {spec['total_units']} Units)")
        st.caption(f"Each square represents one physical unit. X axis: 1 to {max_x} (right to left), Y axis: 1 to {max_y} (top to bottom).")

        cols_per_p = spec["cols_per_panel"]
        panel_definitions = [
            ("Panel 4", list(range(max_x, max_x - cols_per_p, -1))),
            ("Panel 3", list(range(max_x - cols_per_p, max_x - 2*cols_per_p, -1))),
            ("Panel 2", list(range(max_x - 2*cols_per_p, max_x - 3*cols_per_p, -1))),
            ("Panel 1", list(range(max_x - 3*cols_per_p, 0, -1))),
        ]

        def get_tile_color(count):
            if count == 0:
                return "#008000"
            elif 1 <= count <= 10:
                return "#FFC0CB"
            elif 11 <= count <= 20:
                return "#FFA500"
            elif 21 <= count <= 30:
                return "#FF4500"
            else:
                return "#FF0000"

        panel_html_parts = []
        for panel_name, x_values in panel_definitions:
            tile_html = []
            x_header_html = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_values])
        
            for y in range(1, max_y + 1):
                for x in x_values:
                    unit_id = unit_number(x, y, selected_category)
                    rej_cnt = int(coordinate_rejects.get((x, y), 0))
                    tile_color = get_tile_color(rej_cnt)
                    tooltip = f"X: {x}&#10;Y: {y}&#10;Unit: {unit_id}&#10;Rejects: {rej_cnt}"
                    tile_html.append(
                        f'<div class="unit" style="background:{tile_color}" '
                        f'title="{tooltip}" aria-label="X {x}, Y {y}, Unit {unit_id}, Rejects {rej_cnt}">'
                        f'{unit_id}</div>'
                    )
        
            x_footer_html = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_values])
        
            panel_html_parts.append(
                f'<section class="panel"><div class="panel-title">{panel_name}</div>'
                f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_values)}, 22px);">{x_header_html}</div>'
                f'<div class="panel-grid" style="grid-template-columns: repeat({len(x_values)}, 22px);">{"".join(tile_html)}</div>'
                f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_values)}, 22px);">{x_footer_html}</div></section>'
            )

        y_axis_labels_html = "".join([f'<div class="axis-y-label">{y}</div>' for y in range(1, max_y + 1)])
        y_axis_column_html = f'<section class="y-panel"><div class="panel-title">Y</div><div class="axis-x-row"></div><div class="y-axis-grid">{y_axis_labels_html}</div><div class="axis-x-row"></div></section>'

        unit_map_html = f'''<!DOCTYPE html>
        <html><head><meta charset="utf-8">
        <style>
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; background: transparent; color: {T["text"]}; font-family: {FONT_STACK}; color-scheme: {T["scheme"]}; }}
        .matrix-scroll {{ width: 100%; overflow-x: auto; overflow-y: hidden; padding: 6px 4px 18px 4px; }}
        .panels {{ display: flex; align-items: flex-start; gap: 10px; width: max-content; padding-right: 15px; }}
        .panel {{ flex: 0 0 auto; }}
        .y-panel {{ flex: 0 0 auto; margin-left: 2px; }}
        .panel-title {{ text-align: center; color: {T["text"]}; font-size: 12px; font-weight: 600; padding: 0 0 5px 0; }}
        .axis-x-row {{ display: grid; gap: 2px; margin: 4px 0; height: 10px; }}
        .axis-x-label {{ width: 22px; text-align: center; color: {T["text2"]}; font-size: 8px; font-weight: 600; line-height: 10px; }}
        .panel-grid {{ display: grid; grid-auto-rows: 22px; gap: 2px; }}
        .y-axis-grid {{ display: grid; grid-template-columns: 20px; grid-auto-rows: 22px; gap: 2px; }}
        .axis-y-label {{ height: 22px; display: flex; align-items: center; justify-content: center; color: {T["text2"]}; font-size: 9px; font-weight: 600; }}
        .unit {{ width: 22px; height: 22px; border: 1px solid {T["tile_border"]}; border-radius: 2px; display: flex; align-items: center; justify-content: center; color: #101318; font-size: 7px; line-height: 1; font-weight: 600; cursor: help; user-select: none; }}
        .unit:hover {{ outline: 2px solid {T["mark_border"]}; outline-offset: 1px; transform: scale(1.10); position: relative; z-index: 5; }}
        .legend-note {{ color: {T["text2"]}; font-size: 11px; margin: 8px 3px 0 3px; }}
        </style></head>
        <body><div class="matrix-scroll"><div class="panels">{''.join(panel_html_parts)}{y_axis_column_html}</div></div>
        <div class="legend-note">Hover over a unit to view X, Y, unit number, and reject count.</div>
        </body></html>'''
        st.iframe(unit_map_html, height=540)

        legend_cols = st.columns(5)
        legends_data = [
            ("0 · Zero", "#008000"),
            ("1–10 · Clean", "#FFC0CB"),
            ("11–20 · Moderate", "#FFA500"),
            ("21–30 · High", "#FF4500"),
            (">30 · Critical", "#FF0000")
        ]
        for col, (label, color) in zip(legend_cols, legends_data):
            col.markdown(f'<div class="legend-pill"><span class="legend-dot" style="background:{color}"></span>{label}</div>', unsafe_allow_html=True)

    st.markdown("---")
    left, right = st.columns([1, 1.35], border=True)
    with left:
        st.subheader("Top 10 Critical Hotspots")
        if valid.empty:
            st.info("No valid X/Y coordinates in current selection.")
        else:
            hotspots = valid.groupby(["X_internal", "Y_internal"])["Qty"].sum().reset_index(name="Reject count")
            hotspots["X"] = hotspots["X_internal"].astype(int)
            hotspots["Y"] = hotspots["Y_internal"].astype(int)
            hotspots["Unit No."] = hotspots.apply(lambda r: unit_number(r["X"], r["Y"], selected_category), axis=1)
            hotspots = hotspots.sort_values(["Reject count", "X", "Y"], ascending=[False, False, True]).head(10)
            hotspots.insert(0, "Rank", range(1, len(hotspots)+1))
            st.dataframe(hotspots[["Rank", "Unit No.", "X", "Y", "Reject count"]], hide_index=True, width="stretch")
    with right:
        st.subheader("Recent Raw Data Stream")
        recent = filtered.sort_values("Timestamp", ascending=False, na_position="last").head(25).copy()
        recent["UnitNo"] = recent.apply(
            lambda r: unit_number(int(r["X"]), int(r["Y"]), selected_category)
            if pd.notna(r["X"]) and pd.notna(r["Y"]) and 1 <= r["X"] <= max_x and 1 <= r["Y"] <= max_y else np.nan,
            axis=1,
        )
        preferred = ["Timestamp", "Device", "DeviceID", "MESLotID", "IFXLotNo", "StripID", "WB_In", "TA_Yield_Loss_Pct", "Qty", "SourceX", "SourceY", "X", "Y", "UnitNo", "UserRejectCode_Str"]
        display_recent = recent[[c for c in preferred if c in recent.columns]].rename(columns={
            "SourceX": "Raw X", "SourceY": "Raw Y", "X": "Normalized X", "Y": "Normalized Y", "UnitNo": "Unit No.", "WB_In": "Wirebond In", "TA_Yield_Loss_Pct": "TA Yield Loss %", "Qty": "Reject Qty",
            "UserRejectCode_Str": "Reject Code"
        })
        st.dataframe(display_recent, hide_index=True, width="stretch", height=360)
        st.download_button("Export filtered records (CSV)", filtered.to_csv(index=False).encode("utf-8"), f"filtered_{selected_category}_records.csv", "text/csv")

    # ==========================================
    # 4 DETAILED STATION HEATMAPS & ANALYTICS
    # ==========================================
    st.markdown("---")
    st.markdown("## 🏭 Detailed Station Analytics & Heatmaps")
    st.caption("Detailed breakdown for Die Attach, Wire Bond, Strip AOI, and Lid AOI with official reject codes.")

    for idx, stn_label in enumerate(stations_list):
        with st.container(border=True, key=f"glass_station_{idx}"):
            st.markdown(f"### 📍 Station: {stn_label}")

            t_codes = STATION_CODES.get(stn_label, [])
            stn_raw_base = raw[raw["UserRejectCode_Str"].isin(t_codes)]

            stn_avail_codes = sorted(list(set(str(x) for x in stn_raw_base["UserRejectCode_Str"].dropna().unique().tolist())))

            sf1, sf2, sf3 = st.columns(3)
            stn_cat = sf1.selectbox("Device Category", category_options, index=0, key=f"stn_cat_{idx}")
        
            stn_spec = DEVICE_SPECS[stn_cat]
            stn_mx, stn_my = stn_spec["max_x"], stn_spec["max_y"]

            stn_dev_options = ["ALL"] + sorted(raw[raw["Device_Category"] == stn_cat]["DeviceID"].dropna().unique().tolist())
            stn_dev_sel = sf2.selectbox("Device Model / Variant", stn_dev_options, index=0, key=f"stn_dev_{idx}")

            selected_stn_codes = sf3.multiselect(
                "Reject Codes Filter", 
                options=stn_avail_codes, 
                default=stn_avail_codes, 
                key=f"stn_codes_{idx}"
            )

            stn_df = stn_raw_base[stn_raw_base["Device_Category"] == stn_cat].copy()
            if stn_dev_sel != "ALL":
                stn_df = stn_df[stn_df["DeviceID"] == stn_dev_sel]

            if selected_stn_codes:
                stn_df = stn_df[stn_df["UserRejectCode_Str"].isin(selected_stn_codes)]

            stn_df["X_internal"] = stn_df["X"].abs()
            stn_df["Y_internal"] = stn_df["Y"]
            stn_valid = stn_df[
                stn_df["X_internal"].between(1, stn_mx) &
                stn_df["Y_internal"].between(1, stn_my)
            ].copy()

            stn_cap = stn_mx * stn_my
            stn_unique_affected = stn_valid[["DeviceID", "MESLotID", "X_internal", "Y_internal"]].drop_duplicates().shape[0] if not stn_valid.empty else 0
            stn_lot_count = stn_df[["DeviceID", "MESLotID"]].drop_duplicates().shape[0]
            stn_total_max = max(1, stn_lot_count * stn_cap)
            stn_yield = max(0.0, 100.0 - (stn_unique_affected / stn_total_max * 100.0))
            stn_ratio_pct = (stn_unique_affected / stn_total_max * 100.0) if stn_total_max else 0

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric("Station Rejects (Qty)", f"{int(stn_df['Qty'].sum()):,}")
            sm2.metric("Lots Evaluated", f"{stn_df['MESLotID'].nunique():,}")
            sm3.metric("Affected Coordinates", f"{stn_unique_affected:,}", f"{stn_ratio_pct:.2f}% capacity")
            sm4.metric("Estimated Yield", f"{stn_yield:.2f}%")

            if not stn_df.empty:
                sc_pie, sc_trend = st.columns(2, border=True)
                with sc_pie:
                    st.markdown("###### Defect Proportion by Category")
                    if not stn_valid.empty:
                        s_coord_rej = stn_valid.groupby(["X_internal", "Y_internal"])["Qty"].sum().to_dict()
                        s_n_lots = stn_valid[["DeviceID", "MESLotID"]].drop_duplicates().shape[0]
                        s_sev_counts = severity_counts(s_coord_rej, stn_mx, stn_my, s_n_lots)
                        fig_s_pie = px.pie(
                            s_sev_counts, names="Severity", values="Total", hole=0.4,
                            color="Severity", 
                            color_discrete_map={
                                "Zero": "#008000", "Clean": "#FFC0CB", "Moderate": "#FFA500", "High": "#FF4500", "Critical": "#FF0000"
                            }
                        )
                        fig_s_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=5, b=5, l=5, r=5))
                        st.plotly_chart(style_fig(fig_s_pie), theme=None, width="stretch", key=f"pie_{idx}")
                    else:
                        st.info("No coordinate data available for Pie Chart.")

                with sc_trend:
                    st.markdown("###### Daily Average Reject Loss (%) Over Time")
                    if stn_df["Timestamp"].notna().any():
                        s_trend_df = stn_df.dropna(subset=["Timestamp"]).copy()
                        s_trend_df["Date"] = s_trend_df["Timestamp"].dt.date
                    
                        s_lot_summary = s_trend_df.groupby(["Date", "MESLotID"]).agg(
                            Lot_Rejects=("Qty", "sum"),
                            WB_In=("WB_In", "max")
                        ).reset_index()
                    
                        s_lot_summary["Lot_Reject_Pct"] = np.where(
                            s_lot_summary["WB_In"] > 0,
                            (s_lot_summary["Lot_Rejects"] / s_lot_summary["WB_In"]) * 100.0,
                            0.0
                        )
                    
                        s_daily_trend = s_lot_summary.groupby("Date").agg(
                            Avg_Reject_Percentage=("Lot_Reject_Pct", "mean"),
                            Total_Rejects=("Lot_Rejects", "sum"),
                            Total_WB_In=("WB_In", "sum"),
                            Total_Lots=("MESLotID", "nunique")
                        ).reset_index()
                    
                        fig_s_trend = px.line(s_daily_trend, x="Date", y="Avg_Reject_Percentage", markers=True)
                        fig_s_trend.update_traces(
                            customdata=s_daily_trend[["Total_Rejects", "Total_WB_In", "Total_Lots"]],
                            hovertemplate=(
                                "<b>Date</b>: %{x}<br>"
                                "<b>Average Reject Loss</b>: %{y:.2f}%<br>"
                                "<b>Total Lots</b>: %{customdata[2]:,}<br>"
                                "<b>Total Rejects (Qty)</b>: %{customdata[0]:,}<br>"
                                "<b>Total Input (WB In)</b>: %{customdata[1]:,}<br>"
                                "<extra></extra>"
                            ),
                            text=s_daily_trend["Avg_Reject_Percentage"].round(2).astype(str) + "%",
                            textposition="top center",
                            mode="lines+markers+text"
                        )
                        fig_s_trend.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=5, b=5, l=5, r=5))
                        st.plotly_chart(style_fig(fig_s_trend), theme=None, width="stretch", key=f"trend_{idx}")
                    else:
                        st.info("Timestamp data not available for trend chart.")
            else:
                s_coord_rej = {}

            # Station Heatmap Map
            st.markdown(f"###### Individual Unit Map ({stn_cat}: {stn_spec['total_units']} Units)")
            s_panel_defs = [
                ("Panel 4", list(range(stn_mx, stn_mx - stn_spec["cols_per_panel"], -1))),
                ("Panel 3", list(range(stn_mx - stn_spec["cols_per_panel"], stn_mx - 2*stn_spec["cols_per_panel"], -1))),
                ("Panel 2", list(range(stn_mx - 2*stn_spec["cols_per_panel"], stn_mx - 3*stn_spec["cols_per_panel"], -1))),
                ("Panel 1", list(range(stn_mx - 3*stn_spec["cols_per_panel"], 0, -1))),
            ]

            s_html_parts = []
            for p_name, x_vals in s_panel_defs:
                t_html = []
                x_hdr = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_vals])
                for y in range(1, stn_my + 1):
                    for x in x_vals:
                        u_id = unit_number(x, y, stn_cat)
                        cnt = int(s_coord_rej.get((x, y), 0))
                        t_col = get_tile_color(cnt)
                        t_tooltip = f"Station: {stn_label}&#10;X: {x}&#10;Y: {y}&#10;Unit: {u_id}&#10;Rejects: {cnt}"
                        t_html.append(f'<div class="unit" style="background:{t_col}" title="{t_tooltip}">{u_id}</div>')
                x_ftr = "".join([f'<div class="axis-x-label">{x}</div>' for x in x_vals])
                s_html_parts.append(
                    f'<section class="panel"><div class="panel-title">{p_name}</div>'
                    f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_vals)}, 22px);">{x_hdr}</div>'
                    f'<div class="panel-grid" style="grid-template-columns: repeat({len(x_vals)}, 22px);">{"".join(t_html)}</div>'
                    f'<div class="axis-x-row" style="grid-template-columns: repeat({len(x_vals)}, 22px);">{x_ftr}</div></section>'
                )

            s_y_lbls = "".join([f'<div class="axis-y-label">{y}</div>' for y in range(1, stn_my + 1)])
            s_y_col = f'<section class="y-panel"><div class="panel-title">Y</div><div class="axis-x-row"></div><div class="y-axis-grid">{s_y_lbls}</div><div class="axis-x-row"></div></section>'

            stn_map_html = f'''<!DOCTYPE html>
            <html><head><meta charset="utf-8">
            <style>
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; padding: 0; background: transparent; color: {T["text"]}; font-family: {FONT_STACK}; color-scheme: {T["scheme"]}; }}
            .matrix-scroll {{ width: 100%; overflow-x: auto; overflow-y: hidden; padding: 4px 2px 12px 2px; }}
            .panels {{ display: flex; align-items: flex-start; gap: 10px; width: max-content; }}
            .panel {{ flex: 0 0 auto; }}
            .y-panel {{ flex: 0 0 auto; margin-left: 2px; }}
            .panel-title {{ text-align: center; color: {T["text"]}; font-size: 11px; font-weight: 600; padding-bottom: 3px; }}
            .axis-x-row {{ display: grid; gap: 2px; margin: 3px 0; height: 10px; }}
            .axis-x-label {{ width: 22px; text-align: center; color: {T["text2"]}; font-size: 8px; font-weight: 600; line-height: 10px; }}
            .panel-grid {{ display: grid; grid-auto-rows: 22px; gap: 2px; }}
            .y-axis-grid {{ display: grid; grid-template-columns: 20px; grid-auto-rows: 22px; gap: 2px; }}
            .axis-y-label {{ height: 22px; display: flex; align-items: center; justify-content: center; color: {T["text2"]}; font-size: 9px; font-weight: 600; }}
            .unit {{ width: 22px; height: 22px; border: 1px solid {T["tile_border"]}; border-radius: 2px; display: flex; align-items: center; justify-content: center; color: #101318; font-size: 7px; font-weight: 600; cursor: help; }}
            </style></head>
            <body><div class="matrix-scroll"><div class="panels">{''.join(s_html_parts)}{s_y_col}</div></div></body></html>'''
            st.iframe(stn_map_html, height=480)
