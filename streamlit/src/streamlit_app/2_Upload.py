import streamlit as st
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))
from src.design import set_ios_design, page_header, section_title
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.video_storage import upload_video, VideoTooLargeError, MAX_UPLOAD_SIZE_MB
from src.services.match_service import create_pending_match, mark_match_ready, CVPipelineError

set_ios_design()

current_user = get_current_user()

st.session_state.setdefault("upload_widget_version", 0)
st.session_state.setdefault("current_upload_match_id", None)
st.session_state.setdefault("upload_stage", None)  # None | "pending" | "ready"

page_header("Upload", "Import your match footage")

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
      <div style="font-size:15px;color:#1C1C1E;padding-top:4px;">Prefer a short sequence (a few points) over a full match</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sport selection for THIS upload (confirmed, not silently inherited) ─
section_title("Which sport is this video?")
_sport_options = ["pickleball", "tennis", "padel"]
_sport_labels = {"pickleball": "🏓 Pickleball", "tennis": "🎾 Tennis", "padel": "🥎 Padel"}
default_index = _sport_options.index(current_user.preferred_sport) if current_user.preferred_sport in _sport_options else 0
selected_sport = st.radio(
    "Sport for this upload",
    _sport_options,
    index=default_index,
    format_func=lambda s: _sport_labels[s],
    horizontal=True,
    label_visibility="collapsed",
    key="upload_sport_choice"
)

# ── File upload ─────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
uploader_key = f"video_uploader_{st.session_state['upload_widget_version']}"
uploaded = st.file_uploader(
    "⬆️ Import Video",
    type=["mp4", "mov", "m4v"],
    label_visibility="collapsed",
    help=f"MP4 or MOV, up to {MAX_UPLOAD_SIZE_MB}MB (free plan limit)",
    key=uploader_key,
)

st.markdown(f"""
<div style="text-align:center;padding:8px 0 16px;">
  <div style="font-size:15px;font-weight:500;color:#007AFF;">⬆️ Import Video</div>
  <div style="font-size:13px;color:#8E8E93;margin-top:4px;">MP4, MOV up to {MAX_UPLOAD_SIZE_MB}MB — a short sequence works best</div>
</div>
""", unsafe_allow_html=True)

if uploaded is not None and st.session_state["upload_stage"] is None:
    video_bytes = uploaded.getbuffer().tobytes()

    with st.spinner("Uploading video..."):
        try:
            storage_path = upload_video(current_user.id, uploaded.name, video_bytes)
        except VideoTooLargeError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Échec de l'upload : {e}")
            st.stop()

    with get_db_session() as db:
        match = create_pending_match(
            db=db,
            user_id=current_user.id,
            title=uploaded.name.rsplit(".", 1)[0],
            sport=selected_sport,
            video_storage_path=storage_path,
        )
        st.session_state["current_upload_match_id"] = match.id

    st.session_state["upload_stage"] = "pending"
    st.rerun()

# ── Post-upload card — état piloté par upload_stage, jamais par un pop() isolé ──
if st.session_state["upload_stage"] in ("pending", "ready"):
    if st.session_state["upload_stage"] == "ready":
        st.markdown("""
        <div class="nm-card" style="text-align:center;border:2px solid #34C759;padding:24px;">
          <div style="font-size:32px;margin-bottom:8px;">✅</div>
          <div style="font-size:17px;font-weight:600;color:#1C1C1E;">Analysis complete!</div>
          <div style="font-size:14px;color:#8E8E93;margin-top:4px;">Your game is ready in the Library.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="nm-card" style="text-align:center;border:2px solid #34C759;padding:24px;">
          <div style="font-size:32px;margin-bottom:8px;">✅</div>
          <div style="font-size:17px;font-weight:600;color:#1C1C1E;">Video Imported!</div>
          <div style="font-size:14px;color:#8E8E93;margin-top:4px;">
            Your video has been saved. Go to the Library tab to view and analyze it.
          </div>
        </div>
        """, unsafe_allow_html=True)

    if uploaded is not None:
        st.video(uploaded)

    def _reset_upload_state():
        st.session_state["current_upload_match_id"] = None
        st.session_state["upload_stage"] = None
        st.session_state["upload_widget_version"] += 1

    if st.session_state["upload_stage"] == "pending":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📚 Go to Library", use_container_width=True, type="primary", key="go_to_library_pending"):
                _reset_upload_state()
                st.session_state["nav_target"] = "📚  Library"
                st.rerun()
        with col2:
            if st.button("🔍 Analyze Now", use_container_width=True, key="analyze_now"):
                with st.status("Analyzing your game...", expanded=True) as status:
                    st.write("🎯 Detecting players and ball (Computer Vision)...")
                    try:
                        with get_db_session() as db:
                            mark_match_ready(db, st.session_state["current_upload_match_id"])
                    except CVPipelineError as e:
                        status.update(label="Analysis failed", state="error", expanded=True)
                        st.error(f"⚠️ {e}")
                        st.stop()
                    st.write("📊 Calculating performance metrics...")
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                st.session_state["upload_stage"] = "ready"
                st.rerun()
    else:  # "ready"
        if st.button("📚 Go to Library", use_container_width=True, type="primary", key="go_to_library_ready"):
            _reset_upload_state()
            st.session_state["nav_target"] = "📚  Library"
            st.rerun()

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
      <span style="color:#34C759;">●</span> Short sequences upload faster and analyze better
    </div>
  </div>
</div>
""", unsafe_allow_html=True)