"""Régressions entre les nouveautés web et les clients de l'API commune."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import uuid

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from alembic import command
from alembic.config import Config

from backend.api.main import app
from backend.api.deps import get_db
from backend.api.routes_export import _render_html
from backend.auth.tokens import create_session_token
from backend.db.models import Base, User, Match, ChatMessage


@pytest.fixture
def database(client):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(email="player@example.com", password_hash="unused", preferred_sport="padel")
        other = User(email="other@example.com", password_hash="unused", preferred_sport="tennis")
        db.add_all([user, other])
        db.commit()
        match = Match(user_id=user.id, title="Match test", sport="padel", status="ready", rating=3,
                      rallies=12, winners=2, errors=0, coverage=50, patterns_summary={})
        db.add(match)
        db.commit()
        app.dependency_overrides[get_db] = lambda: db
        yield db, user, other, match
    engine.dispose()


def test_cookie_login_and_logout_keep_bearer_compatible(client, database):
    db, user, _, _ = database
    with patch("backend.api.routes_auth.authenticate_user", return_value=user):
        response = client.post("/auth/login", json={"email": user.email, "password": "password"})
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert client.get("/auth/me").json()["id"] == user.id
    token = response.json()["access_token"]
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401
    # Le JWT retourné en JSON continue de fonctionner pour iOS.
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_cookie_writes_reject_foreign_origin_but_native_bearer_works(client, database):
    _, user, _, _ = database
    token = create_session_token(user.id)
    client.cookies.set("access_token", token)
    assert client.patch("/auth/me", json={"preferred_sport": "tennis"},
                        headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert client.patch("/auth/me", json={"preferred_sport": "tennis"}).status_code == 200
    client.cookies.clear()
    client.headers.pop("origin", None)
    assert client.patch("/auth/me", json={"preferred_sport": "padel"},
                        headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_ios_sync_is_still_persisted_and_visible(client, database):
    db, user, _, _ = database
    client.headers.pop("origin", None)
    client.headers["Authorization"] = f"Bearer {create_session_token(user.id)}"
    payload = {"title": "iOS", "sport": "padel", "rating": 8.0,
               "skills": [{"label": "Serve", "score": "80", "color": "green"}],
               "rallies": 18}
    response = client.post("/matches/sync", json=payload)
    assert response.status_code == 201
    saved = db.get(Match, response.json()["id"])
    assert saved.user_id == user.id
    assert saved.skills == payload["skills"]
    assert saved.video_storage_path is None
    assert saved.id in [m["id"] for m in client.get("/matches").json()]


def test_chat_persists_both_turns_and_enforces_ownership(client, database):
    db, user, other, match = database
    client.headers["Authorization"] = f"Bearer {create_session_token(user.id)}"
    with patch("backend.api.routes_chat.Moderator") as moderator, \
         patch("backend.api.routes_chat.get_knowledge_base") as kb, \
         patch("backend.api.routes_chat.Agent") as agent:
        moderator.return_value.moderate.return_value.is_prompt_injection = False
        kb.return_value.retrieve.return_value = []
        agent.return_value.call_and_validate.return_value = SimpleNamespace(reply="Travaille le service.")
        response = client.post(f"/matches/{match.id}/chat", json={"message": "Que travailler ?"})
    assert response.status_code == 200
    history = client.get(f"/matches/{match.id}/chat").json()
    assert [m["role"] for m in history] == ["user", "coach"]
    assert history[-1]["text"] == "Travaille le service."
    assert db.query(ChatMessage).count() == 2
    client.headers["Authorization"] = f"Bearer {create_session_token(other.id)}"
    assert client.get(f"/matches/{match.id}/chat").status_code == 404
    assert client.get(f"/matches/{match.id}/export-pdf").status_code == 404
    client.headers["Authorization"] = f"Bearer {create_session_token(user.id)}"
    with patch("backend.api.routes_matches.delete_video"):
        assert client.delete(f"/matches/{match.id}").status_code == 204
    assert db.query(ChatMessage).count() == 0


def test_export_handles_mobile_scores_escapes_html_and_preserves_zero(database):
    _, _, _, match = database
    match.title = '<img src="http://internal/secret">'
    match.skills = [{"label": "<script>bad()</script>", "score": "80"}, {"label": "Web", "score": 3}]
    html = _render_html(match)
    assert '<img src=' not in html
    assert '<script>' not in html
    assert '&lt;script&gt;' in html
    assert 'width:80%' in html
    assert 'width:60%' in html
    assert '>0</div><div class="kpi-label">ERREURS' in html


def test_export_returns_pdf_and_encoded_filename(client, database):
    _, user, _, match = database
    match.title = 'Match été "finale"'
    client.headers["Authorization"] = f"Bearer {create_session_token(user.id)}"
    with patch("backend.api.routes_export.sync_playwright") as playwright:
        browser = playwright.return_value.__enter__.return_value.chromium.launch.return_value
        browser.new_page.return_value.pdf.return_value = b"%PDF-1.4\nfixture"
        response = client.get(f"/matches/{match.id}/export-pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "filename*=UTF-8''Match%20%C3%A9t%C3%A9" in response.headers["content-disposition"]
    browser.close.assert_called_once()


def test_migrations_upgrade_existing_schema_without_losing_matches(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config("backend/alembic.ini")
    command.upgrade(config, "56822ee323a9")
    engine = create_engine(database_url)
    uid, mid = str(uuid.uuid4()), str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(User.__table__.insert().values(id=uid, email="migration@example.com", password_hash="unused"))
        conn.execute(Match.__table__.insert().values(id=mid, user_id=uid, title="Keep me", sport="padel"))
    command.upgrade(config, "head")
    assert "chat_messages" in inspect(engine).get_table_names()
    with Session(engine) as db:
        assert db.get(Match, mid).title == "Keep me"
        db.add(ChatMessage(match_id=mid, role="user", text="Saved"))
        db.commit()
    command.upgrade(config, "head")  # un deuxième lancement ne rejoue rien
    command.downgrade(config, "56822ee323a9")
    assert "chat_messages" not in inspect(engine).get_table_names()
    with Session(engine) as db:
        assert db.get(Match, mid).title == "Keep me"
    engine.dispose()


def test_streamlit_style_delete_cascades_chat_without_new_orm_relationship(database):
    db, _, _, match = database
    mid = match.id
    db.add(ChatMessage(match_id=mid, role="user", text="Conversation"))
    db.commit()
    db.execute(Match.__table__.delete().where(Match.id == mid))
    db.commit()
    assert db.query(ChatMessage).count() == 0


def test_native_client_can_login_again_without_origin_header(client, database):
    _, user, _, _ = database
    client.headers.pop("origin", None)
    with patch("backend.api.routes_auth.authenticate_user", return_value=user):
        for _ in range(2):
            response = client.post("/auth/login", json={"email": user.email, "password": "password"})
            assert response.status_code == 200
