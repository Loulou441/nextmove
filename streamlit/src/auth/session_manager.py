"""
Gestion de la session utilisateur côté Streamlit via un cookie navigateur.

st.session_state seul ne suffit pas : il est réinitialisé à chaque nouveau
chargement de page/onglet. Le cookie, lui, persiste — c'est ce qui permet
à un utilisateur de rester connecté après un refresh.
"""

import streamlit as st
import extra_streamlit_components as stx

from src.auth.tokens import create_session_token, decode_session_token
from src.db.session import get_db_session
from src.db.models import User

COOKIE_NAME = "nextmove_session"


def get_cookie_manager() -> stx.CookieManager:
    """
    Retourne une instance unique de CookieManager pour toute la durée de vie
    de l'app (évite de recréer le composant à chaque rerun, ce qui provoquerait
    des erreurs de clé dupliquée dans Streamlit).
    """
    if "cookie_manager" not in st.session_state:
        st.session_state["cookie_manager"] = stx.CookieManager(key="nextmove_cookie_manager")
    return st.session_state["cookie_manager"]


def login(user: User) -> None:
    """Crée un token de session et le stocke dans un cookie navigateur."""
    token = create_session_token(user.id)
    cookie_manager = get_cookie_manager()
    cookie_manager.set(COOKIE_NAME, token, key="set_session_cookie")
    st.session_state["current_user_id"] = user.id


def logout() -> None:
    """Supprime le cookie de session et vide l'état local."""
    cookie_manager = get_cookie_manager()
    cookie_manager.delete(COOKIE_NAME, key="delete_session_cookie")
    st.session_state.pop("current_user_id", None)


def get_current_user() -> User | None:
    """
    Retourne l'utilisateur actuellement connecté (via le cookie), ou None
    si personne n'est connecté / le token est invalide ou expiré.
    """
    cookie_manager = get_cookie_manager()
    token = cookie_manager.get(COOKIE_NAME)

    if not token:
        return None

    user_id = decode_session_token(token)
    if not user_id:
        return None

    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is not None:
            # Détache l'objet de la session pour pouvoir l'utiliser après
            # la fermeture du "with" (sinon SQLAlchemy lève une erreur
            # si on accède à ses attributs plus tard).
            db.expunge(user)
        return user