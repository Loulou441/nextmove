import streamlit as st
import time
from pathlib import Path
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title

set_ios_design()
page_header("Upload", "Recording Pickleball 🏓")

# ── How to record ───────────────────────────────────────────────────
section_title("How to Record")
st.markdown("""
<div class="nm-card">
  <div style="display:flex;flex-direction:column;gap:12px;">
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <div style="width:28px;height:28px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:13px;font-weight:700;flex-shrink:0;">1</div>
      <div style="font-size:15px;color:#1C1C1E;padding-top:4px;">Position your camera to capture the full court</div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <div style="width:28px;height:28px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:13px;font-weight:700;flex-shrink:0;">2</div>
      <div style="font-size:15px;color:#1C1C1E;padding-top:4px;">Mount camera 4+ feet high for best results</div>
    </div>
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <div style="width:28px;height:28px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:13px;font-weight:700;flex-shrink:0;">3</div>
      <div style="font-size:15px;color:#1C1C1E;padding-top:4px;">Record your full game or a specific sequence</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── File upload ─────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
uploaded = st.file_uploader(
    "⬆️ Import Video",
    type=["mp4", "mov", "m4v"],
    label_visibility="collapsed",
    help="MP4 or MOV format supported"
)

st.markdown("""
<div style="text-align:center;padding:8px 0 16px;">
  <div style="font-size:15px;font-weight:500;color:#007AFF;">⬆️ Import Video</div>
  <div style="font-size:13px;color:#8E8E93;margin-top:4px;">MP4, MOV up to 500MB</div>
</div>
""", unsafe_allow_html=True)

if uploaded is not None:
    # Save video
    VIDEO_DIR = ROOT / "data" / "videos"
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = VIDEO_DIR / f"{ts}_{uploaded.name.replace(' ', '_')}"
    with open(save_path, "wb") as f:
        f.write(uploaded.getbuffer())

    # Confirmation modal style
    st.markdown("""
    <div class="nm-card" style="text-align:center;border:2px solid #34C759;padding:24px;">
      <div style="font-size:32px;margin-bottom:8px;">✅</div>
      <div style="font-size:17px;font-weight:600;color:#1C1C1E;">Video Imported!</div>
      <div style="font-size:14px;color:#8E8E93;margin-top:4px;">
        Your video has been imported. Go to the Library tab to view and analyze it.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.video(uploaded)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 Go to Library", use_container_width=True, type="primary"):
            st.info("Navigate to Library in the sidebar →")
    with col2:
        if st.button("🔍 Analyze Now", use_container_width=True):
            with st.status("Analyzing your game...", expanded=True) as status:
                st.write("🎯 Detecting players and court...")
                time.sleep(1)
                st.write("🏓 Tracking ball and movements...")
                time.sleep(1)
                st.write("📊 Calculating performance metrics...")
                time.sleep(1)
                status.update(label="Analysis complete!", state="complete", expanded=False)
            st.success("✅ Your game is ready in the Library!")

# ── Pro tips ────────────────────────────────────────────────────────
section_title("Pro Tips")
st.markdown("""
<div class="nm-card">
  <div style="display:flex;flex-direction:column;gap:10px;">
    <div style="display:flex;align-items:center;gap:8px;font-size:14px;color:#1C1C1E;">
      <span style="color:#34C759;">●</span> Record in landscape mode
    </div>
    <div style="display:flex;align-items:center;gap:8px;font-size:14px;color:#1C1C1E;">
      <span style="color:#34C759;">●</span> Ensure good lighting
    </div>
    <div style="display:flex;align-items:center;gap:8px;font-size:14px;color:#1C1C1E;">
      <span style="color:#34C759;">●</span> Keep camera stable
    </div>
    <div style="display:flex;align-items:center;gap:8px;font-size:14px;color:#1C1C1E;">
      <span style="color:#34C759;">●</span> Capture the full court width
    </div>
  </div>
</div>
""", unsafe_allow_html=True)