import streamlit as st

def set_ios_design():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', -apple-system, sans-serif !important; background-color: #F2F2F7 !important; color: #1C1C1E !important; }
    .stApp { background-color: #F2F2F7 !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E5EA !important; min-width: 260px !important; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 2px !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label { padding: 10px 14px !important; border-radius: 12px !important; transition: background 0.15s ease; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #F2F2F7 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #EAFBF0 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) div p { color: #1A7F3C !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none !important; }
    h1 { font-size: 34px !important; font-weight: 700 !important; color: #1C1C1E !important; }
    h2 { font-size: 22px !important; font-weight: 600 !important; color: #1C1C1E !important; margin-top: 24px !important; margin-bottom: 8px !important; }
    .nm-card { background: #FFFFFF; border-radius: 16px; padding: 20px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .nm-card-green { background: #F0FBF4; border-radius: 16px; padding: 20px; margin-bottom: 12px; border: 1px solid #D1F0DC; }
    .nm-card-orange { background: #FFF8F0; border-radius: 16px; padding: 20px; margin-bottom: 12px; border: 1px solid #FFE4CC; }
    [data-testid="stMetric"] { background: #FFFFFF; border-radius: 16px; padding: 16px 20px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 700 !important; color: #1C1C1E !important; }
    [data-testid="stMetricLabel"] { font-size: 13px !important; color: #8E8E93 !important; }
    .stButton > button { border-radius: 14px !important; font-weight: 600 !important; font-size: 15px !important; padding: 12px 24px !important; border: none !important; }
    .stButton > button[kind="primary"] { background: #34C759 !important; color: white !important; }
    .stButton > button[kind="primary"]:hover { background: #2DB54E !important; transform: translateY(-1px) !important; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #34C759 !important; border-bottom: 2px solid #34C759 !important; }
    hr { border: none !important; border-top: 1px solid #E5E5EA !important; margin: 20px 0 !important; }
    .page-subtitle { font-size: 15px; color: #8E8E93; margin-top: -8px; margin-bottom: 20px; }
    .sport-badge { display: inline-flex; align-items: center; gap: 6px; background: #F2F2F7; border-radius: 20px; padding: 5px 12px; font-size: 14px; font-weight: 500; color: #3C3C43; }
    .nm-card { background: #FFFFFF; border-radius: 16px; padding: 20px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .game-card { background: #FFFFFF; border-radius: 16px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .game-card-title { font-size: 16px; font-weight: 600; color: #1C1C1E; }
    .game-card-date { font-size: 13px; color: #8E8E93; margin-top: 2px; }
    .status-badge { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
    .status-ready { background: #D1F0DC; color: #1A7F3C; }
    .status-pending { background: #FFE4CC; color: #B35500; }
    .skill-bar-wrap { margin-bottom: 14px; }
    .skill-bar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .skill-bar-label { font-size: 15px; font-weight: 500; color: #1C1C1E; }
    .skill-bar-score.green { color: #34C759; font-weight: 600; }
    .skill-bar-score.blue  { color: #007AFF; font-weight: 600; }
    .skill-bar-score.orange{ color: #FF9500; font-weight: 600; }
    .skill-bar-bg { height: 8px; background: #E5E5EA; border-radius: 4px; overflow: hidden; }
    .skill-bar-fill { height: 100%; border-radius: 4px; }
    .kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }
    .kpi-card { background: #F2F2F7; border-radius: 14px; padding: 16px; text-align: center; }
    .kpi-card .kpi-icon { font-size: 22px; margin-bottom: 4px; }
    .kpi-card .kpi-value { font-size: 24px; font-weight: 700; color: #1C1C1E; }
    .kpi-card .kpi-label { font-size: 12px; color: #8E8E93; font-weight: 500; margin-top: 2px; }
    .highlight-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #F2F2F7; }
    .highlight-row:last-child { border-bottom: none; }
    .highlight-title { font-size: 15px; font-weight: 500; color: #1C1C1E; }
    .highlight-time { font-size: 13px; color: #8E8E93; margin-top: 2px; }
    .highlight-tag { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 20px; }
    .tag-winner  { background: #D1F0DC; color: #1A7F3C; }
    .tag-rally   { background: #D6E9FF; color: #0055B3; }
    .tag-attack  { background: #FFE4CC; color: #B35500; }
    .tag-defense { background: #E8E0FF; color: #5500B3; }
    .insight-item { display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-size: 15px; color: #1C1C1E; }
    .insight-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

def skill_bar(label, icon, score, max_score=5.0, color="green"):
    pct = int((score / max_score) * 100)
    fills = {"green": "#34C759", "blue": "#007AFF", "orange": "#FF9500", "red": "#FF3B30"}
    fill = fills.get(color, "#34C759")
    st.markdown(f"""
    <div class="skill-bar-wrap">
      <div class="skill-bar-header">
        <span class="skill-bar-label">{icon} {label}</span>
        <span class="skill-bar-score {color}">{score}</span>
      </div>
      <div class="skill-bar-bg">
        <div class="skill-bar-fill" style="width:{pct}%;background:{fill}"></div>
      </div>
    </div>""", unsafe_allow_html=True)

def performance_ring(score, max_score=5.0, label="Overall Performance"):
    pct = score / max_score
    r, circ = 60, 376.99
    dash = pct * circ
    gap  = circ - dash
    color = "#34C759" if score >= 4.0 else ("#FF9500" if score >= 3.0 else "#FF3B30")
    st.markdown(f"""
    <div class="nm-card" style="text-align:center;padding:28px 20px 20px;">
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;margin-bottom:16px;">{label}</div>
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="#E5E5EA" stroke-width="12"/>
        <circle cx="80" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="12"
          stroke-dasharray="{dash:.1f} {gap:.1f}" stroke-linecap="round" transform="rotate(-90 80 80)"/>
        <text x="80" y="74" text-anchor="middle" font-size="32" font-weight="700" fill="#1C1C1E">{score}</text>
        <text x="80" y="96" text-anchor="middle" font-size="14" fill="#8E8E93">/ {max_score}</text>
      </svg>
    </div>""", unsafe_allow_html=True)

def kpi_grid(items):
    html = '<div class="kpi-grid">'
    for icon, value, label, color in items:
        html += f'<div class="kpi-card"><div class="kpi-icon">{icon}</div><div class="kpi-value" style="color:{color}">{value}</div><div class="kpi-label">{label}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def strengths_focus(strengths, focus_areas):
    col1, col2 = st.columns(2)
    with col1:
        rows = "".join([f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:14px;"><span>{n}</span><span style="font-weight:600;color:#34C759">{s}</span></div>' for n,s in strengths])
        st.markdown(f'<div class="nm-card-green"><div style="font-size:16px;font-weight:600;color:#1A7F3C;margin-bottom:12px;">⭐ Strengths</div>{rows}</div>', unsafe_allow_html=True)
    with col2:
        rows = "".join([f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:14px;"><span>{n}</span><span style="font-weight:600;color:#FF9500">{s}</span></div>' for n,s in focus_areas])
        st.markdown(f'<div class="nm-card-orange"><div style="font-size:16px;font-weight:600;color:#B35500;margin-bottom:12px;">🎯 Focus Areas</div>{rows}</div>', unsafe_allow_html=True)

def section_title(title):
    st.markdown(f'<h2>{title}</h2>', unsafe_allow_html=True)

def page_header(title, subtitle=""):
    st.markdown(f'<h1>{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)
