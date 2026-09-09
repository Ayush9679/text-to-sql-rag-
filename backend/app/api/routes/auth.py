"""Authentication endpoints: Google OAuth, session check, development login, and logout."""

import os
from urllib.parse import parse_qs, urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.auth import AuthError, AuthService, AuthenticatedContext
from app.api.dependencies import get_auth_service, get_current_context, require_authenticated, require_csrf
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.get("/me")
def get_auth_status(
    context: AuthenticatedContext | None = Depends(get_current_context),
) -> dict:
    if context is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": {"id": context.user_id, "email": context.email, "name": context.name},
        "business": {"id": context.business_id, "name": context.business_name},
        "csrf_token": context.csrf_token,
    }


@router.get("/login")
def login(
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    if settings.AUTH_MODE == "development":
        context = auth_service.development_login()
        session_id, csrf = auth_service.create_session(context)
        resp = RedirectResponse(url=settings.FRONTEND_URL, status_code=status.HTTP_303_SEE_OTHER)
        _set_cookies(resp, session_id, csrf, auth_service)
        return resp

    auth_url = auth_service.start_google_login()
    state = (parse_qs(urlparse(auth_url).query).get("state") or [""])[0]
    resp = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    if state:
        resp.set_cookie(
            key=AuthService.OAUTH_STATE_COOKIE,
            value=state,
            max_age=600,
            path="/auth/callback",
            httponly=True,
            samesite="lax",
            secure=settings.COOKIE_SECURE,
        )
    return resp


@router.get("/callback")
def oauth_callback(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    query_params = {k: [v] for k, v in request.query_params.items()}
    expected_state = request.cookies.get(AuthService.OAUTH_STATE_COOKIE)

    try:
        context = auth_service.complete_google_login(query_params, expected_state=expected_state)
        session_id, csrf = auth_service.create_session(context)
        resp = RedirectResponse(url=settings.FRONTEND_URL, status_code=status.HTTP_303_SEE_OTHER)
        _set_cookies(resp, session_id, csrf, auth_service)
        resp.delete_cookie(AuthService.OAUTH_STATE_COOKIE, path="/auth/callback")
        return resp
    except AuthError:
        resp = RedirectResponse(url=f"{settings.FRONTEND_URL}/login?auth=failed", status_code=status.HTTP_302_FOUND)
        resp.delete_cookie(AuthService.OAUTH_STATE_COOKIE, path="/auth/callback")
        return resp


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    context: AuthenticatedContext = Depends(require_authenticated),
    _csrf: None = Depends(require_csrf),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    session_cookie = request.cookies.get(AuthService.SESSION_COOKIE)
    session_id = auth_service.session_id_from_cookie(session_cookie)
    if session_id:
        auth_service.logout(session_id)
    response.delete_cookie(AuthService.SESSION_COOKIE, path="/")
    response.delete_cookie(AuthService.CSRF_COOKIE, path="/")


def _set_cookies(response: Response, session_id: str, csrf: str, auth_service: AuthService) -> None:
    max_age = AuthService.SESSION_HOURS * 3600
    signed_session = auth_service.sign_session_cookie(session_id)
    response.set_cookie(
        key=AuthService.SESSION_COOKIE,
        value=signed_session,
        max_age=max_age,
        path="/",
        httponly=True,
        samesite=settings.COOKIE_SAMESITE.lower(),
        secure=settings.COOKIE_SECURE,
    )
    response.set_cookie(
        key=AuthService.CSRF_COOKIE,
        value=csrf,
        max_age=max_age,
        path="/",
        httponly=False,
        samesite=settings.COOKIE_SAMESITE.lower(),
        secure=settings.COOKIE_SECURE,
    )
