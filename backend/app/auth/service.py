"""Server-managed identity, business ownership, and OIDC support."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt
from sqlalchemy import Column, DateTime, ForeignKey, MetaData, String, Table, create_engine, select, update
from sqlalchemy.engine import Engine


metadata = MetaData()
users = Table("app_users", metadata, Column("id", String(36), primary_key=True), Column("email", String(320), nullable=False, unique=True), Column("name", String(200), nullable=False), Column("provider", String(40), nullable=False), Column("provider_user_id", String(255), nullable=False, unique=True), Column("created_at", DateTime(timezone=True), nullable=False))
businesses = Table("businesses", metadata, Column("id", String(36), primary_key=True), Column("name", String(200), nullable=False), Column("owner_user_id", String(36), ForeignKey("app_users.id"), nullable=False), Column("created_at", DateTime(timezone=True), nullable=False))
sessions = Table("auth_sessions", metadata, Column("id", String(64), primary_key=True), Column("user_id", String(36), ForeignKey("app_users.id"), nullable=False), Column("csrf_token", String(64), nullable=False), Column("expires_at", DateTime(timezone=True), nullable=False), Column("created_at", DateTime(timezone=True), nullable=False))


class AuthError(ValueError):
    pass


@dataclass(frozen=True)
class AuthenticatedContext:
    user_id: str
    email: str
    name: str
    business_id: str
    business_name: str
    tenant_id: str
    csrf_token: str


class AuthService:
    SESSION_COOKIE = "textsql_session"
    CSRF_COOKIE = "textsql_csrf"
    OAUTH_STATE_COOKIE = "textsql_oauth_state"
    SESSION_HOURS = 8

    def __init__(self, engine: Engine):
        self.engine = engine
        self._oauth_states: dict[str, tuple[str, str, datetime]] = {}

    def initialize(self) -> None:
        metadata.create_all(self.engine, checkfirst=True)

    def get_or_create_user_business(self, *, email: str, name: str, provider: str, provider_user_id: str) -> AuthenticatedContext:
        now = datetime.now(UTC)
        with self.engine.begin() as conn:
            user = conn.execute(select(users).where(users.c.provider == provider, users.c.provider_user_id == provider_user_id)).mappings().first()
            if user is None:
                user_id = secrets.token_hex(16)
                conn.execute(users.insert().values(id=user_id, email=email, name=name[:200] or email, provider=provider, provider_user_id=provider_user_id, created_at=now))
            else:
                user_id = user["id"]
                conn.execute(update(users).where(users.c.id == user_id).values(email=email, name=name[:200] or email))
            business = conn.execute(select(businesses).where(businesses.c.owner_user_id == user_id).order_by(businesses.c.created_at)).mappings().first()
            if business is None:
                business_id = secrets.token_hex(16)
                business_name = f"{(name or email).split('@')[0]}'s business"[:200]
                conn.execute(businesses.insert().values(id=business_id, name=business_name, owner_user_id=user_id, created_at=now))
            else:
                business_id, business_name = business["id"], business["name"]
        return AuthenticatedContext(user_id=user_id, email=email, name=name or email, business_id=business_id, business_name=business_name, tenant_id=business_id, csrf_token="")

    def create_session(self, context: AuthenticatedContext) -> tuple[str, str]:
        session_id, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        with self.engine.begin() as conn:
            conn.execute(sessions.insert().values(id=session_id, user_id=context.user_id, csrf_token=csrf, created_at=now, expires_at=now + timedelta(hours=self.SESSION_HOURS)))
        return session_id, csrf

    def sign_session_cookie(self, session_id: str) -> str:
        secret = self._session_secret()
        signature = hmac.new(secret.encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{session_id}.{signature}"

    def session_id_from_cookie(self, cookie_value: str | None) -> str | None:
        if not cookie_value or "." not in cookie_value:
            return None
        session_id, signature = cookie_value.rsplit(".", 1)
        if not session_id or not signature:
            return None
        expected = hmac.new(self._session_secret().encode("utf-8"), session_id.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        return session_id

    def resolve_session(self, session_id: str | None) -> AuthenticatedContext | None:
        if not session_id:
            return None
        now = datetime.now(UTC)
        with self.engine.begin() as conn:
            row = conn.execute(select(sessions.c.csrf_token, users.c.id, users.c.email, users.c.name, businesses.c.id.label("business_id"), businesses.c.name.label("business_name")).select_from(sessions.join(users, sessions.c.user_id == users.c.id).join(businesses, businesses.c.owner_user_id == users.c.id)).where(sessions.c.id == session_id, sessions.c.expires_at > now).order_by(businesses.c.created_at)).mappings().first()
        if row is None:
            return None
        return AuthenticatedContext(user_id=row["id"], email=row["email"], name=row["name"], business_id=row["business_id"], business_name=row["business_name"], tenant_id=row["business_id"], csrf_token=row["csrf_token"])

    def logout(self, session_id: str | None) -> None:
        if session_id:
            with self.engine.begin() as conn:
                conn.execute(sessions.delete().where(sessions.c.id == session_id))

    def require_csrf(self, context: AuthenticatedContext, supplied: str | None) -> None:
        if not supplied or not hmac.compare_digest(context.csrf_token, supplied):
            raise AuthError("CSRF validation failed.")

    def start_google_login(self) -> str:
        if os.getenv("AUTH_MODE", "oauth").lower() != "oauth":
            raise AuthError("Google OAuth is disabled in this environment.")
        client_id, redirect_uri = os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_REDIRECT_URI")
        if not client_id or not redirect_uri:
            raise AuthError("Google OAuth is not configured.")
        state, verifier, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(64), secrets.token_urlsafe(32)
        self._oauth_states[state] = (verifier, nonce, datetime.now(UTC) + timedelta(minutes=10))
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({"client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": "openid email profile", "state": state, "nonce": nonce, "code_challenge": challenge, "code_challenge_method": "S256"})

    def complete_google_login(self, query: dict[str, list[str]], *, expected_state: str | None = None) -> AuthenticatedContext:
        state, code = (query.get("state") or [""])[0], (query.get("code") or [""])[0]
        if expected_state is not None and not hmac.compare_digest(state, expected_state):
            raise AuthError("Invalid or expired OAuth callback.")
        saved = self._oauth_states.pop(state, None)
        if not state or not code or saved is None or saved[2] < datetime.now(UTC):
            raise AuthError("Invalid or expired OAuth callback.")
        verifier, nonce, _ = saved
        token = self.exchange_google_code(code=code, verifier=verifier)
        claims = self.verify_google_id_token(token.get("id_token"))
        if claims.get("nonce") != nonce or not claims.get("email_verified") or not claims.get("sub") or not claims.get("email"):
            raise AuthError("Google identity verification failed.")
        return self.get_or_create_user_business(email=claims["email"], name=claims.get("name", claims["email"]), provider="google", provider_user_id=claims["sub"])

    def exchange_google_code(self, *, code: str, verifier: str) -> dict:
        token_url = "https://oauth2.googleapis.com/token"
        body = urlencode({"code": code, "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"], "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"], "grant_type": "authorization_code", "code_verifier": verifier}).encode()
        try:
            with urlopen(Request(token_url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=10) as response:
                return json.loads(response.read())
        except Exception as exc:
            raise AuthError("Google token exchange failed.") from exc

    def verify_google_id_token(self, id_token: str | None) -> dict:
        if not id_token:
            raise AuthError("Google identity verification failed.")
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise AuthError("Google OAuth is not configured.")
        try:
            key = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs").get_signing_key_from_jwt(id_token).key
            claims = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=client_id,
                issuer=["https://accounts.google.com", "accounts.google.com"],
                options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            )
        except Exception as exc:
            raise AuthError("Google identity verification failed.") from exc
        return claims

    def development_login(self) -> AuthenticatedContext:
        if os.getenv("AUTH_MODE", "oauth").lower() != "development":
            raise AuthError("Development authentication is disabled.")
        email = os.getenv("DEV_USER_EMAIL")
        if not email:
            raise AuthError("DEV_USER_EMAIL is required for development authentication.")
        return self.get_or_create_user_business(email=email, name=os.getenv("DEV_USER_NAME", "Development User"), provider="development", provider_user_id=email)

    @staticmethod
    def _session_secret() -> str:
        secret = os.getenv("SESSION_SECRET")
        if not secret or len(secret) < 32:
            raise AuthError("SESSION_SECRET must be configured with at least 32 characters.")
        return secret


def auth_engine() -> Engine:
    return create_engine("postgresql+psycopg://" + f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}", pool_pre_ping=True)
