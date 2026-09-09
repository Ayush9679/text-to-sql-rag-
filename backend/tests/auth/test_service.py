from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import create_engine, select, update

from app.auth.service import AuthError, AuthService, sessions


@pytest.fixture
def auth(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    service = AuthService(engine)
    service.initialize()
    return service


def test_user_and_business_are_created(auth):
    context = auth.get_or_create_user_business(
        email="ayush@example.com",
        name="Ayush",
        provider="google",
        provider_user_id="google-1",
    )

    assert context.email == "ayush@example.com"
    assert context.business_name == "Ayush's business"
    assert context.tenant_id == context.business_id


def test_existing_user_login_reuses_business(auth):
    first = auth.get_or_create_user_business(email="a@example.com", name="A", provider="google", provider_user_id="sub")
    second = auth.get_or_create_user_business(email="a@example.com", name="A Updated", provider="google", provider_user_id="sub")

    assert second.user_id == first.user_id
    assert second.business_id == first.business_id
    assert second.tenant_id == first.tenant_id


def test_session_resolves_and_rejects_tampered_cookie(auth):
    context = auth.get_or_create_user_business(email="a@example.com", name="A", provider="google", provider_user_id="sub")
    session_id, csrf = auth.create_session(context)

    signed = auth.sign_session_cookie(session_id)
    assert auth.session_id_from_cookie(signed) == session_id
    assert auth.session_id_from_cookie(f"{session_id}.bad") is None
    resolved = auth.resolve_session(session_id)
    assert resolved is not None
    assert resolved.csrf_token == csrf
    assert resolved.tenant_id == context.tenant_id


def test_expired_session_is_invalid(auth):
    context = auth.get_or_create_user_business(email="a@example.com", name="A", provider="google", provider_user_id="sub")
    session_id, _ = auth.create_session(context)

    with auth.engine.begin() as connection:
        connection.execute(update(sessions).where(sessions.c.id == session_id).values(expires_at=datetime.now(UTC) - timedelta(seconds=1)))

    assert auth.resolve_session(session_id) is None


def test_csrf_validation(auth):
    context = auth.get_or_create_user_business(email="a@example.com", name="A", provider="google", provider_user_id="sub")
    session_id, csrf = auth.create_session(context)
    resolved = auth.resolve_session(session_id)

    auth.require_csrf(resolved, csrf)
    with pytest.raises(AuthError):
        auth.require_csrf(resolved, "wrong")


def test_oauth_state_validation_rejects_unknown_state(auth):
    with pytest.raises(AuthError, match="Invalid or expired"):
        auth.complete_google_login({"state": ["missing"], "code": ["code"]})


def test_oauth_state_validation_rejects_cookie_mismatch(auth, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oauth")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    login_url = auth.start_google_login()
    state = login_url.split("state=", 1)[1].split("&", 1)[0]

    with pytest.raises(AuthError, match="Invalid or expired"):
        auth.complete_google_login({"state": [state], "code": ["code"]}, expected_state="different")


def test_complete_google_login_uses_verified_claims(auth, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oauth")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    login_url = auth.start_google_login()
    state = login_url.split("state=", 1)[1].split("&", 1)[0]
    nonce = auth._oauth_states[state][1]
    monkeypatch.setattr(auth, "exchange_google_code", lambda **_kwargs: {"id_token": "verified"})
    monkeypatch.setattr(
        auth,
        "verify_google_id_token",
        lambda token: {"sub": "sub", "email": "a@example.com", "email_verified": True, "name": "A", "nonce": nonce},
    )

    context = auth.complete_google_login({"state": [state], "code": ["code"]})

    assert context.email == "a@example.com"


def test_invalid_id_token_is_rejected(auth, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    with pytest.raises(AuthError):
        auth.verify_google_id_token(None)


@pytest.mark.parametrize(
    "error",
    [
        jwt.InvalidAudienceError("bad audience"),
        jwt.InvalidIssuerError("bad issuer"),
        jwt.ExpiredSignatureError("expired"),
    ],
)
def test_google_token_validation_errors_are_rejected(auth, monkeypatch, error):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")

    class _Jwks:
        def get_signing_key_from_jwt(self, _token):
            return type("Key", (), {"key": "key"})()

    monkeypatch.setattr(jwt, "PyJWKClient", lambda _url: _Jwks())

    def decode(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(jwt, "decode", decode)

    with pytest.raises(AuthError):
        auth.verify_google_id_token("token")


def test_verified_google_token_returns_claims(auth, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")

    class _Jwks:
        def get_signing_key_from_jwt(self, _token):
            return type("Key", (), {"key": "key"})()

    expected = {"sub": "sub", "aud": "client", "iss": "https://accounts.google.com", "exp": 1, "iat": 1}
    monkeypatch.setattr(jwt, "PyJWKClient", lambda _url: _Jwks())
    monkeypatch.setattr(jwt, "decode", lambda *_args, **_kwargs: expected)

    assert auth.verify_google_id_token("token") == expected
