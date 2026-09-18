import streamlit as st

SPORTS = {
    "pickleball": {"label": "Pickleball", "icon": "🏓", "description": "Fast-paced paddle sport", "color": "#34C759"},
    "padel": {"label": "Padel", "icon": "🎾", "description": "Enclosed-court racket sport", "color": "#007AFF"},
    "tennis": {"label": "Tennis", "icon": "🎾", "description": "Classic racket sport", "color": "#FFCC00"},
    "badminton": {"label": "Badminton", "icon": "🏸", "description": "Fast net-divided racket sport", "color": "#FF3B30"},
}


def set_ios_design():
    st.markdown(
        """
        <style>
        :root {
            --nm-green: #34C759;
            --nm-blue: #007AFF;
            --nm-orange: #FF9500;
            --nm-red: #FF3B30;
            --nm-yellow: #FFCC00;
            --nm-bg: #F5F5F7;
            --nm-card: #FFFFFF;
            --nm-text: #1C1C1E;
            --nm-secondary: #8E8E93;
            --nm-separator: #E5E5EA;
            --nm-sidebar: #FFFFFF;
        }

        html, body, [class*="css"], .stApp {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif !important;
            color: var(--nm-text) !important;
        }

        html, body, .stApp { background: var(--nm-bg) !important; }
        #MainMenu, footer { visibility: hidden !important; }
        .stDeployButton { display: none !important; }

        [data-testid="stHeader"] { background: transparent !important; }

        [data-testid="stSidebar"] {
            background: var(--nm-sidebar) !important;
            border-right: 1px solid var(--nm-separator) !important;
            width: 252px !important;
            min-width: 252px !important;
        }

        [data-testid="stSidebarContent"] { padding: 22px 16px 20px !important; }

        [data-testid="stMainBlockContainer"] {
            max-width: 1320px !important;
            padding-top: 2rem !important;
            padding-left: 2.5rem !important;
            padding-right: 2.5rem !important;
            padding-bottom: 3rem !important;
        }

        .nm-sidebar-brand { display:flex; align-items:center; gap:11px; padding:4px 6px 22px; }
        .nm-sidebar-logo {
            width:38px; height:38px; border-radius:11px; background:rgba(52,199,89,.13);
            display:flex; align-items:center; justify-content:center; font-size:21px;
        }
        .nm-sidebar-title { font-size:19px; font-weight:750; letter-spacing:-.02em; }
        .nm-sidebar-subtitle { font-size:11px; color:var(--nm-secondary); margin-top:1px; }
        .nm-sidebar-section {
            font-size:11px; font-weight:650; color:var(--nm-secondary); text-transform:uppercase;
            letter-spacing:.07em; padding:5px 8px 8px;
        }
        .nm-sidebar-account {
            margin-top:16px; padding:14px 10px 4px; border-top:1px solid var(--nm-separator);
            font-size:12px; color:var(--nm-secondary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
        }

        [data-testid="stSidebar"] [role="radiogroup"] {
            display:flex !important; flex-direction:column !important; gap:5px !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            min-height:42px !important; padding:9px 11px !important; border-radius:10px !important;
            margin:0 !important; transition:background .15s ease;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#F2F2F7 !important; }
        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none !important; }
        [data-testid="stSidebar"] [role="radiogroup"] label p {
            font-size:14px !important; font-weight:570 !important; color:#3C3C43 !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked),
        [data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {
            background:rgba(52,199,89,.12) !important;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p,
        [data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p {
            color:#248A3D !important; font-weight:650 !important;
        }

        h1 {
            font-size:34px !important; line-height:1.08 !important; letter-spacing:-0.025em !important;
            font-weight:720 !important; color:var(--nm-text) !important; margin-bottom:18px !important;
        }
        h2 {
            font-size:18px !important; font-weight:650 !important; color:var(--nm-text) !important;
            margin-top:22px !important; margin-bottom:9px !important;
        }
        .page-subtitle { margin:-12px 0 22px; color:var(--nm-secondary); font-size:14px; }
        .muted { color:var(--nm-secondary); }

        .nm-card, .game-card {
            background:var(--nm-card); border-radius:14px; padding:16px; margin-bottom:12px;
            border:1px solid rgba(229,229,234,.75); box-shadow:0 1px 2px rgba(0,0,0,.025);
        }
        .nm-card-green {
            background:rgba(52,199,89,.08); border:1px solid rgba(52,199,89,.16);
            border-radius:14px; padding:16px; margin-bottom:12px;
        }
        .nm-card-orange {
            background:rgba(255,149,0,.08); border:1px solid rgba(255,149,0,.16);
            border-radius:14px; padding:16px; margin-bottom:12px;
        }
        .nm-profile-card { min-height:245px; display:flex; flex-direction:column; justify-content:center; }
        .nm-compact-card { padding:13px 15px; }

        .game-card-header { display:flex; gap:12px; align-items:flex-start; justify-content:space-between; }
        .game-card-title { font-size:16px; font-weight:650; color:var(--nm-text); }
        .game-card-date { font-size:12px; color:var(--nm-secondary); }

        div[class*="st-key-match_row_"] {
            background:#fff; border:1px solid var(--nm-separator); border-radius:14px;
            padding:13px 15px 10px; margin-bottom:9px; box-shadow:0 1px 2px rgba(0,0,0,.025);
        }

        .desktop-list-head {
            display:grid; grid-template-columns:minmax(260px,4fr) 1fr 1fr 1.1fr; gap:16px;
            padding:0 16px 8px; color:var(--nm-secondary); font-size:11px; font-weight:650;
            text-transform:uppercase; letter-spacing:.05em;
        }

        .sport-badge {
            display:inline-flex; align-items:center; gap:6px; padding:4px 9px; border-radius:8px;
            font-size:12px; font-weight:550; background:#F2F2F7; color:#3C3C43;
        }
        .status-badge {
            display:inline-flex; align-items:center; gap:4px; border-radius:999px; padding:4px 9px;
            font-size:11px; font-weight:650; white-space:nowrap;
        }
        .status-ready { background:rgba(52,199,89,.14); color:#248A3D; }
        .status-pending { background:rgba(255,149,0,.15); color:#C65D00; }
        .status-processing { background:rgba(0,122,255,.13); color:#0066CC; }
        .status-failed { background:rgba(255,59,48,.13); color:#D70015; }

        .stButton > button, .stFormSubmitButton > button {
            border-radius:10px !important; min-height:40px; border:0 !important;
            font-weight:600 !important; font-size:14px !important; box-shadow:none !important;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background:var(--nm-green) !important; color:#fff !important;
        }
        .stButton > button[kind="secondary"] {
            background:#FFFFFF !important; color:var(--nm-text) !important; border:1px solid var(--nm-separator) !important;
        }
        .stButton > button:hover { transform:none !important; }

        .st-key-settings_actions button, .st-key-settings_panel button {
            min-height:36px !important; padding:6px 10px !important; font-size:13px !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stFileUploader"] section,
        [data-baseweb="select"] > div { border-radius:10px !important; }

        [data-testid="stFileUploaderDropzone"] {
            min-height:172px; border-radius:14px !important; border:1.5px dashed #C7C7CC !important;
            background:#FBFBFC !important;
        }

        [data-testid="stTabs"] [role="tablist"] { gap:20px !important; border-bottom:1px solid var(--nm-separator); }
        [data-testid="stTabs"] [role="tab"] { font-size:14px !important; padding-left:2px !important; padding-right:2px !important; }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color:var(--nm-green) !important; border-bottom-color:var(--nm-green) !important;
        }

        [data-testid="stMetric"] {
            background:#fff; border-radius:12px; padding:11px 13px !important;
            border:1px solid rgba(229,229,234,.8); box-shadow:none;
        }
        [data-testid="stMetricValue"] { font-size:23px !important; font-weight:700 !important; }
        [data-testid="stMetricLabel"] { color:var(--nm-secondary) !important; font-size:11px !important; }

        .skill-bar-wrap { margin-bottom:13px; }
        .skill-bar-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; }
        .skill-bar-label { font-size:14px; font-weight:550; }
        .skill-bar-score { font-size:13px; font-weight:650; }
        .skill-bar-bg { height:7px; background:#E5E5EA; border-radius:999px; overflow:hidden; }
        .skill-bar-fill { height:100%; border-radius:999px; }

        .kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:9px; margin:12px 0; }
        .kpi-card { background:#fff; border:1px solid var(--nm-separator); border-radius:12px; padding:12px; text-align:center; }
        .kpi-icon { font-size:18px; }
        .kpi-value { font-size:21px; font-weight:700; margin-top:2px; }
        .kpi-label { font-size:11px; color:var(--nm-secondary); margin-top:2px; }

        .settings-row {
            display:flex; align-items:center; gap:10px; background:#fff; border:1px solid var(--nm-separator);
            border-radius:10px; padding:10px 12px; margin-bottom:7px; font-size:13px;
        }
        .settings-row .chevron { margin-left:auto; color:#C7C7CC; }
        .coach-summary { position:sticky; top:1.5rem; }

        hr { border:0 !important; border-top:1px solid var(--nm-separator) !important; margin:16px 0 !important; }

        @media (max-width:900px) {
            [data-testid="stMainBlockContainer"] { padding-left:1.25rem !important; padding-right:1.25rem !important; }
            .kpi-grid { grid-template-columns:repeat(2,1fr); }
            .desktop-list-head { display:none; }
        }

        @media (max-width:640px) {
            [data-testid="stSidebar"] { width:230px !important; min-width:230px !important; }
            [data-testid="stMainBlockContainer"] {
                padding-left:14px !important; padding-right:14px !important; padding-top:1rem !important;
            }
            h1 { font-size:30px !important; }
            .nm-profile-card { min-height:unset; }
            [data-testid="stFileUploaderDropzone"] { min-height:130px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"<h1>{title}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def section_title(title: str):
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)


def sport_label(sport: str) -> str:
    info = SPORTS.get(sport, SPORTS["pickleball"])
    return f"{info['icon']} {info['label']}"


def skill_bar(label, icon, score, max_score=5.0, color="green"):
    score = float(score or 0)
    pct = max(0, min(100, int((score / max_score) * 100)))
    fills = {"green": "#34C759", "blue": "#007AFF", "orange": "#FF9500", "red": "#FF3B30", "yellow": "#FFCC00"}
    fill = fills.get(color, "#34C759")
    st.markdown(
        f"""
        <div class="skill-bar-wrap">
          <div class="skill-bar-header">
            <span class="skill-bar-label">{icon} {label}</span>
            <span class="skill-bar-score" style="color:{fill};">{score:.1f}</span>
          </div>
          <div class="skill-bar-bg"><div class="skill-bar-fill" style="width:{pct}%;background:{fill};"></div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def performance_ring(score, max_score=5.0, label="Overall Performance"):
    score = float(score or 0)
    pct = max(0.0, min(1.0, score / max_score))
    r, circ = 60, 376.99
    dash = pct * circ
    gap = circ - dash
    color = "#34C759" if score >= 4.0 else ("#FF9500" if score >= 3.0 else "#FF3B30")
    st.markdown(
        f"""
        <div class="nm-card" style="text-align:center;padding:18px 16px 14px;">
          <div style="font-size:15px;font-weight:650;margin-bottom:8px;">{label}</div>
          <svg width="132" height="132" viewBox="0 0 160 160" aria-label="{score} out of {max_score}">
            <circle cx="80" cy="80" r="{r}" fill="none" stroke="#E5E5EA" stroke-width="12"/>
            <circle cx="80" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="12"
              stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round" transform="rotate(-90 80 80)"/>
            <text x="80" y="74" text-anchor="middle" font-size="32" font-weight="700" fill="#1C1C1E">{score:.1f}</text>
            <text x="80" y="96" text-anchor="middle" font-size="14" fill="#8E8E93">/ {max_score:.1f}</text>
          </svg>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_grid(items):
    html = '<div class="kpi-grid">'
    for icon, value, label, color in items:
        html += (
            '<div class="kpi-card">'
            f'<div class="kpi-icon">{icon}</div>'
            f'<div class="kpi-value" style="color:{color};">{value}</div>'
            f'<div class="kpi-label">{label}</div>'
            '</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def strengths_focus(strengths, focus_areas):
    col1, col2 = st.columns(2)
    with col1:
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px;"><span>{n}</span><b>{s:.1f}</b></div>'
            for n, s in strengths
        )
        st.markdown(f'<div class="nm-card-green"><b>⭐ Strengths</b><div style="height:7px"></div>{rows}</div>', unsafe_allow_html=True)
    with col2:
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px;"><span>{n}</span><b>{s:.1f}</b></div>'
            for n, s in focus_areas
        )
        st.markdown(f'<div class="nm-card-orange"><b>🎯 Focus Areas</b><div style="height:7px"></div>{rows}</div>', unsafe_allow_html=True)
