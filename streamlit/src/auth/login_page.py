"""
Page de connexion / inscription — affichée quand aucun utilisateur n'est
connecté (voir la vérification en haut de app.py).
"""

import streamlit as st

from src.db.session import get_db_session
from src.auth.service import (
    register_user,
    authenticate_user,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from src.auth.session_manager import login as start_session


def render_login_page() -> None:
    st.markdown("""
    <div style="text-align:center; padding: 32px 0 8px;">
      <div style="font-size:40px;">🏓</div>
      <div style="font-size:28px;font-weight:700;color:#1C1C1E;">NextMove</div>
      <div style="font-size:15px;color:#8E8E93;">Smart Coach AI</div>
    </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["Connexion", "Créer un compte"])

            with tab_login:
                _render_login_form()

            with tab_register:
                _render_register_form()


def _render_login_form() -> None:
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="toi@exemple.fr")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button(
            "Se connecter", type="primary", use_container_width=True
        )

    if submitted:
        if not email or not password:
            st.error("Merci de remplir tous les champs.")
            return

        with get_db_session() as db:
            try:
                user = authenticate_user(db, email, password)
                db.expunge(user)
            except InvalidCredentialsError:
                st.error("Email ou mot de passe incorrect.")
                return

        start_session(user)
        st.rerun()


def _render_register_form() -> None:
    with st.form("register_form"):
        email = st.text_input("Email", placeholder="toi@exemple.fr", key="register_email")
        password = st.text_input("Mot de passe", type="password", key="register_password")
        password_confirm = st.text_input(
            "Confirme le mot de passe", type="password", key="register_password_confirm"
        )
        sport = st.selectbox(
            "Sport préféré",
            options=["pickleball", "football", "padel"],
            format_func=lambda s: {"pickleball": "🏓 Pickleball", "football": "⚽ Football", "padel": "🎾 Padel"}[s],
        )
        submitted = st.form_submit_button(
            "Créer mon compte", type="primary", use_container_width=True
        )

    if submitted:
        if not email or not password:
            st.error("Merci de remplir tous les champs.")
            return
        if len(password) < 8:
            st.error("Le mot de passe doit faire au moins 8 caractères.")
            return
        if password != password_confirm:
            st.error("Les mots de passe ne correspondent pas.")
            return

        with get_db_session() as db:
            try:
                user = register_user(db, email, password, preferred_sport=sport)
                db.expunge(user)
            except EmailAlreadyExistsError:
                st.error("Un compte existe déjà avec cet email.")
                return

        start_session(user)
        st.rerun()