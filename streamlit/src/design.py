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
            --nm-bg: #F2F2F7;
            --nm-card: #FFFFFF;
            --nm-text: #1C1C1E;
            --nm-secondary: #8E8E93;
            --nm-separator: #E5E5EA;
        }

        html, body, [class*="css"], .stApp {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif !important;
            color: var(--nm-text) !important;
        }

        html, body, .stApp { background: var(--nm-bg) !important; }
        #MainMenu, footer, header, [data-testid="stSidebar"] { display: none !important; }
        .stDeployButton { display: none !important; }

        [data-testid="stMainBlockContainer"] {
            max-width: 760px !important;
            padding-top: 1.25rem !important;
            padding-left: 18px !important;
            padding-right: 18px !important;
            padding-bottom: calc(112px + env(safe-area-inset-bottom)) !important;
        }

        h1 {
            font-size: 34px !important;
            line-height: 1.08 !important;
            letter-spacing: -0.025em !important;
            font-weight: 700 !important;
            color: var(--nm-text) !important;
            margin-bottom: 18px !important;
        }
        h2 {
            font-size: 20px !important;
            font-weight: 650 !important;
            color: var(--nm-text) !important;
            margin-top: 22px !important;
            margin-bottom: 10px !important;
        }
        .page-subtitle {
            margin: -12px 0 18px;
            color: var(--nm-secondary);
            font-size: 14px;
        }

        .nm-card, .game-card {
            background: var(--nm-card);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 5px 18px rgba(0,0,0,.045);
        }
        .nm-card-green {
            background: rgba(52,199,89,.10);
            border: 1px solid rgba(52,199,89,.17);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
        }
        .nm-card-orange {
            background: rgba(255,149,0,.10);
            border: 1px solid rgba(255,149,0,.17);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
        }
        .game-card-header { display:flex; gap:12px; align-items:flex-start; justify-content:space-between; }
        .game-card-title { font-size:17px; font-weight:650; color:var(--nm-text); }
        .game-card-date { font-size:12px; color:var(--nm-secondary); }

        .sport-badge {
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:5px 10px;
            border-radius:9px;
            font-size:13px;
            font-weight:550;
            background:#F2F2F7;
            color:#3C3C43;
        }
        .status-badge {
            display:inline-flex;
            align-items:center;
            gap:4px;
            border-radius:999px;
            padding:4px 9px;
            font-size:12px;
            font-weight:600;
            white-space:nowrap;
        }
        .status-ready { background:rgba(52,199,89,.14); color:#248A3D; }
        .status-pending { background:rgba(255,149,0,.15); color:#C65D00; }
        .status-processing { background:rgba(0,122,255,.13); color:#0066CC; }
        .status-failed { background:rgba(255,59,48,.13); color:#D70015; }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 12px !important;
            min-height: 44px;
            border: 0 !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background: var(--nm-green) !important;
            color: #fff !important;
        }
        .stButton > button[kind="secondary"] {
            background: #FFFFFF !important;
            color: var(--nm-text) !important;
            border: 1px solid var(--nm-separator) !important;
        }
        .stButton > button:hover { transform:none !important; }

        [data-testid="stTextInput"] input,
        [data-testid="stFileUploader"] section,
        [data-baseweb="select"] > div {
            border-radius: 10px !important;
        }

        /* Bottom TabView: 3 tabs, same order as Swift. */
        .st-key-bottom_nav {
            position: fixed !important;
            left: 50% !important;
            bottom: 0 !important;
            transform: translateX(-50%);
            z-index: 1000;
            width: min(760px, 100vw) !important;
            box-sizing: border-box;
            padding: 7px 12px calc(7px + env(safe-area-inset-bottom)) !important;
            background: rgba(249,249,249,.96);
            border-top: 1px solid rgba(60,60,67,.18);
            backdrop-filter: blur(22px);
            -webkit-backdrop-filter: blur(22px);
        }
        .st-key-bottom_nav [role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 0 !important;
            width: 100% !important;
        }
        .st-key-bottom_nav [role="radiogroup"] label {
            margin: 0 !important;
            padding: 7px 2px !important;
            justify-content: center !important;
            text-align: center !important;
            border-radius: 0 !important;
            background: transparent !important;
        }
        .st-key-bottom_nav [role="radiogroup"] label > div:first-child { display:none !important; }
        .st-key-bottom_nav [role="radiogroup"] label p {
            margin:0 !important;
            text-align:center !important;
            white-space:nowrap !important;
            font-size:12px !important;
            font-weight:550 !important;
            color:#8E8E93 !important;
        }
        .st-key-bottom_nav [role="radiogroup"] label:has(input:checked) p,
        .st-key-bottom_nav [role="radiogroup"] label[data-selected="true"] p {
            color: var(--nm-green) !important;
        }

        [data-testid="stTabs"] [role="tablist"] { gap: 14px !important; }
        [data-testid="stTabs"] [role="tab"] { font-size:14px !important; }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color: var(--nm-green) !important;
            border-bottom-color: var(--nm-green) !important;
        }

        [data-testid="stMetric"] {
            background:#fff;
            border-radius:14px;
            padding:14px 16px !important;
            box-shadow:0 1px 2px rgba(0,0,0,.04);
        }
        [data-testid="stMetricValue"] { font-size:26px !important; font-weight:700 !important; }
        [data-testid="stMetricLabel"] { color:var(--nm-secondary) !important; font-size:12px !important; }

        .skill-bar-wrap { margin-bottom: 14px; }
        .skill-bar-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:5px; }
        .skill-bar-label { font-size:15px; font-weight:550; }
        .skill-bar-score { font-size:14px; font-weight:650; }
        .skill-bar-bg { height:8px; background:#E5E5EA; border-radius:999px; overflow:hidden; }
        .skill-bar-fill { height:100%; border-radius:999px; }

        .kpi-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin:14px 0; }
        .kpi-card { background:#F2F2F7; border-radius:13px; padding:14px; text-align:center; }
        .kpi-icon { font-size:20px; }
        .kpi-value { font-size:23px; font-weight:700; margin-top:2px; }
        .kpi-label { font-size:12px; color:var(--nm-secondary); margin-top:2px; }

        .settings-row {
            display:flex; align-items:center; gap:12px;
            background:#fff; border-radius:12px; padding:14px 16px;
            margin-bottom:8px;
        }
        .settings-row .chevron { margin-left:auto; color:#C7C7CC; }
        .muted { color:var(--nm-secondary); }
        hr { border:0 !important; border-top:1px solid var(--nm-separator) !important; margin:18px 0 !important; }

        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] { padding-left:14px !important; padding-right:14px !important; }
            h1 { font-size:32px !important; }
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
        <div class="nm-card" style="text-align:center;padding:24px 20px 18px;">
          <div style="font-size:17px;font-weight:650;margin-bottom:12px;">{label}</div>
          <svg width="154" height="154" viewBox="0 0 160 160" aria-label="{score} out of {max_score}">
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
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:14px;"><span>{n}</span><b>{s:.1f}</b></div>'
            for n, s in strengths
        )
        st.markdown(f'<div class="nm-card-green"><b>⭐ Strengths</b><div style="height:8px"></div>{rows}</div>', unsafe_allow_html=True)
    with col2:
        rows = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:14px;"><span>{n}</span><b>{s:.1f}</b></div>'
            for n, s in focus_areas
        )
        st.markdown(f'<div class="nm-card-orange"><b>🎯 Focus Areas</b><div style="height:8px"></div>{rows}</div>', unsafe_allow_html=True)
