import streamlit as st

from src.design import SPORTS, page_header, section_title, set_ios_design
from src.auth.session_manager import get_current_user
from src.db.session import get_db_session
from src.services.video_storage import MAX_UPLOAD_SIZE_MB, VideoTooLargeError, upload_video
from src.services.match_service import create_pending_match

set_ios_design()
page_header("Upload")

current_user = get_current_user()
if current_user is None:
    st.stop()

sport = st.session_state.get("sport", "pickleball")
info = SPORTS.get(sport, SPORTS["pickleball"])
st.session_state.setdefault("upload_widget_version", 0)

# Current sport indicator — same role as UploadView.sportIndicator.
st.markdown(
    f"""
    <div class="nm-card" style="display:flex;align-items:center;justify-content:center;gap:10px;padding:14px;">
      <span style="font-size:25px;">{info['icon']}</span>
      <span style="font-size:16px;font-weight:600;color:#8E8E93;">Recording {info['label']}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("How to Record")
steps = [
    "Position your camera to capture the full court",
    "Mount camera 4+ feet high for best results",
    "Tap the button below to start recording",
]
steps_html = "".join(
    f"""
    <div style="display:flex;align-items:flex-start;gap:12px;">
      <div style="width:28px;height:28px;background:#34C759;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;flex:0 0 28px;">{idx}</div>
      <div style="font-size:15px;padding-top:4px;">{text}</div>
    </div>
    """
    for idx, text in enumerate(steps, 1)
)
st.markdown(
    f'<div class="nm-card"><div style="display:flex;flex-direction:column;gap:14px;">{steps_html}</div></div>',
    unsafe_allow_html=True,
)

# Streamlit ne fournit pas de capture vidéo native équivalente à AVFoundation.
# Le bouton reste présent pour conserver le parcours visuel Swift, sans simuler
# un enregistrement qui n'existe pas réellement côté navigateur.
if st.button("🎥  Record Video", type="primary", use_container_width=True, key="record_video"):
    st.info("Browser video recording is not available yet. Use Import Video below.")

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

with st.form(f"import_video_form_{st.session_state['upload_widget_version']}", clear_on_submit=False):
    title = st.text_input(
        "Game Title",
        value=f"Imported {info['label']}",
        placeholder="Game Title",
    )
    uploaded = st.file_uploader(
        "Import Video",
        type=["mp4", "mov", "m4v"],
        help=f"MP4, MOV or M4V — up to {MAX_UPLOAD_SIZE_MB} MB",
    )
    import_submitted = st.form_submit_button("⬇️  Import Video", use_container_width=True)

if import_submitted:
    if uploaded is None:
        st.error("Choose a video first.")
    elif not title.strip():
        st.error("Enter a game title.")
    else:
        video_bytes = uploaded.getbuffer().tobytes()
        try:
            with st.spinner("Importing video..."):
                storage_path = upload_video(current_user.id, uploaded.name, video_bytes)
                with get_db_session() as db:
                    create_pending_match(
                        db=db,
                        user_id=current_user.id,
                        title=title.strip(),
                        sport=sport,
                        video_storage_path=storage_path,
                    )
            st.toast("Video imported successfully!", icon="✅")
            st.session_state["upload_widget_version"] += 1
            st.session_state["last_import_success"] = True
            st.rerun()
        except VideoTooLargeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Import failed: {exc}")

if st.session_state.pop("last_import_success", False):
    st.markdown(
        """
        <div class="nm-card" style="display:flex;align-items:center;gap:10px;border:1px solid rgba(52,199,89,.20);">
          <span style="font-size:24px;">✅</span>
          <span style="font-size:14px;font-weight:600;">Video imported successfully!</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

section_title("Pro Tips")
for tip in ["Record in landscape mode", "Ensure good lighting", "Keep camera stable"]:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin:8px 2px;color:#8E8E93;font-size:13px;"><span style="color:#34C759;">●</span>{tip}</div>',
        unsafe_allow_html=True,
    )
