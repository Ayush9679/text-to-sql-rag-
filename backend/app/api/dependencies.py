"""FastAPI request dependencies: database, authentication, tenant isolation, and CSRF."""

import os
from typing import Annotated
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthError, AuthService, AuthenticatedContext
from app.auth.service import auth_engine
from app.config import get_settings
from app.database.session import get_db

settings = get_settings()

_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(auth_engine())
        _auth_service.initialize()
    return _auth_service


def get_current_context(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session_cookie: Annotated[str | None, Cookie(alias=AuthService.SESSION_COOKIE)] = None,
) -> AuthenticatedContext | None:
    session_id = auth_service.session_id_from_cookie(session_cookie)
    context = auth_service.resolve_session(session_id)
    if context is not None:
        return context

    # Development mode fallback context
    auth_mode = os.getenv("AUTH_MODE", settings.AUTH_MODE).lower()
    if auth_mode == "development":
        dev_email = os.getenv("DEV_USER_EMAIL", settings.DEV_USER_EMAIL) or "dev@example.com"
        dev_name = os.getenv("DEV_USER_NAME", settings.DEV_USER_NAME) or "Development User"
        try:
            return auth_service.get_or_create_user_business(
                email=dev_email,
                name=dev_name,
                provider="development",
                provider_user_id=dev_email,
            )
        except Exception:
            return None
    return None


def require_authenticated(
    context: Annotated[AuthenticatedContext | None, Depends(get_current_context)],
) -> AuthenticatedContext:
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return context


def require_csrf(
    context: Annotated[AuthenticatedContext, Depends(require_authenticated)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> None:
    auth_mode = os.getenv("AUTH_MODE", settings.AUTH_MODE).lower()
    if auth_mode == "development" and not x_csrf_token:
        return
    try:
        auth_service.require_csrf(context, x_csrf_token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
