"""Écran d'authentification Streamlit aligné sur LoginView.swift."""

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
    st.session_state.setdefault("auth_mode", "login")
    is_registering = st.session_state["auth_mode"] == "register"

    st.markdown(
        f"""
        <div style="max-width:460px;margin:9vh auto 0;text-align:center;">
          <div style="font-size:52px;line-height:1;margin-bottom:10px;">🎾</div>
          <div style="font-size:34px;font-weight:750;letter-spacing:-0.03em;color:#1C1C1E;">NextMove</div>
          <div style="font-size:17px;font-weight:600;color:#8E8E93;margin-top:5px;">
            {"Créer un compte" if is_registering else "Connexion"}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="max-width:460px;margin:24px auto 0;">', unsafe_allow_html=True)
    _render_auth_form(is_registering)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_auth_form(is_registering: bool) -> None:
    form_key = "register_form" if is_registering else "login_form"

    with st.form(form_key):
        email = st.text_input(
            "Email",
            placeholder="Email",
            key=f"{form_key}_email",
        )
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Mot de passe",
            key=f"{form_key}_password",
        )
        submitted = st.form_submit_button(
            "S'inscrire" if is_registering else "Se connecter",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not email or len(password) < 6:
            st.error("Le mot de passe doit contenir au moins 6 caractères.")
            return

        if is_registering:
            _register(email, password)
        else:
            _login(email, password)

    toggle_label = "J'ai déjà un compte" if is_registering else "Créer un compte"
    if st.button(toggle_label, use_container_width=True, key="toggle_auth_mode"):
        st.session_state["auth_mode"] = "login" if is_registering else "register"
        st.rerun()


def _login(email: str, password: str) -> None:
    with get_db_session() as db:
        try:
            user = authenticate_user(db, email, password)
            db.expunge(user)
        except InvalidCredentialsError:
            st.error("Email ou mot de passe incorrect.")
            return

    start_session(user)
    st.rerun()


def _register(email: str, password: str) -> None:
    with get_db_session() as db:
        try:
            # Comme LoginView.swift, l'inscription ne demande pas le sport.
            # Le choix de sport reste une étape séparée de l'expérience.
            user = register_user(db, email, password)
            db.expunge(user)
        except EmailAlreadyExistsError:
            st.error("Un compte existe déjà avec cet email.")
            return

    start_session(user)
    st.rerun()
