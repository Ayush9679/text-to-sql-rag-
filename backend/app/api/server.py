"""Minimal HTTP adapter for the completed Phase 7 query service."""

import json
import os
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text

from app.application import ApplicationQueryService, QueryRequest
from app.auth import AuthError, AuthService, AuthenticatedContext
from app.auth.service import auth_engine
from app.dataset import DatasetError, DatasetIngestionService
from app.dataset.service import tenant_schema_name
from app.schema_intelligence.service import SchemaIntelligenceService
from app.schema_retrieval.business_knowledge import BUSINESS_CONCEPTS
from app.schema_retrieval.documents import (
    SchemaDocumentBuilder,
    build_business_documents,
)
from app.schema_retrieval.serializer import SchemaSerializer
from app.sql_execution import SQLExecutionService


def _database_url() -> str:
    return (
        "postgresql+psycopg://"
        f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.environ['POSTGRES_DB']}"
    )


def build_application_service(tenant_id: str = "default") -> ApplicationQueryService:
    """Compose existing services from the established environment settings."""

    load_dotenv()
    base_schema_name = os.getenv("POSTGRES_SCHEMA", "analytics")
    engine = create_engine(_database_url(), pool_pre_ping=True)
    schema_name = tenant_schema_name(tenant_id)

    # Preserve the seeded demo schema for a fresh local installation, but
    # switch the default local tenant to its uploaded schema as soon as it has
    # a dataset.  Non-default tenants are always isolated schemas.
    if tenant_id == "default":
        uploaded_schema = SchemaIntelligenceService(engine).get_schema(schema_name)
        if not uploaded_schema.tables:
            schema_name = base_schema_name

    query_engine = create_engine(
        _database_url(),
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema_name},public"},
    )
    schema = SchemaIntelligenceService(query_engine).get_schema(schema_name)
    schema_documents = SchemaDocumentBuilder(SchemaSerializer()).build_documents(schema)
    documents = schema_documents + (build_business_documents(BUSINESS_CONCEPTS) if tenant_id == "default" else [])

    return ApplicationQueryService(
        schema=schema,
        documents=documents,
        execution_service=SQLExecutionService(engine=query_engine),
    )


class QueryRequestHandler(BaseHTTPRequestHandler):
    """Serve the Phase 7 QueryRequest/QueryResponse contract at POST /query."""

    application_services: dict[str, ApplicationQueryService] = {}
    auth_service: AuthService | None = None
    allowed_origin = os.getenv("FRONTEND_URL", os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"))

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        """Expose discoverable API metadata without requiring a web framework."""

        path = urlparse(self.path).path
        if path in {"/", "/health"}:
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "text-to-sql-api",
                    "query_endpoint": "/query",
                    "documentation": "/docs",
                },
            )
            return
        if path == "/auth/login":
            self._auth_login()
            return
        if path == "/auth/callback":
            self._auth_callback()
            return
        if path == "/auth/me":
            self._auth_me()
            return
        if path == "/datasets":
            context = self._require_authenticated()
            if context is not None:
                self._list_datasets(context.tenant_id)
            return
        if path == "/openapi.json":
            self._send_json(HTTPStatus.OK, self._openapi_schema())
            return
        if path == "/docs":
            self._send_html(HTTPStatus.OK, self._documentation_page())
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if urlparse(self.path).path not in {"/query", "/datasets", "/datasets/upload", "/auth/logout", "/auth/me"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-CSRF-Token")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path
        if path == "/auth/logout":
            context = self._require_authenticated()
            if context is None:
                return
            if not self._require_csrf(context):
                return
            self._auth().logout(self._session_id())
            self.send_response(HTTPStatus.NO_CONTENT)
            self._cors_headers()
            self._clear_auth_cookies()
            self.end_headers()
            return
        if path not in {"/query", "/datasets/upload"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})
            return
        context = self._require_authenticated()
        if context is None:
            return
        if not self._require_csrf(context):
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
        except (ValueError, ValidationError, json.JSONDecodeError):
            self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "Invalid query request."})
            return

        tenant_id = context.tenant_id

        if path == "/datasets/upload":
            self._upload_dataset(tenant_id, payload)
            return

        try:
            # Tenant selection is server-controlled; never accept a tenant
            # identifier from query JSON.
            payload.pop("tenant_id", None)
            request = QueryRequest.model_validate(payload)
        except (ValueError, ValidationError):
            self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "Invalid query request."})
            return

        try:
            if tenant_id not in self.application_services:
                self.application_services[tenant_id] = build_application_service(tenant_id)
            response = self.application_services[tenant_id].handle(request)
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Query service is unavailable."})
            return

        self._send_json(HTTPStatus.OK, response.model_dump(mode="json"))

    def _auth_login(self) -> None:
        try:
            if os.getenv("AUTH_MODE", "oauth").lower() == "development":
                context = self._auth().development_login()
                session_id, csrf = self._auth().create_session(context)
                self._redirect_frontend(session_id=session_id, csrf=csrf)
                return
            auth_url = self._auth().start_google_login()
            state = (parse_qs(urlparse(auth_url).query).get("state") or [""])[0]
            self._redirect(auth_url, oauth_state=state)
        except AuthError as exc:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})

    def _auth_callback(self) -> None:
        try:
            context = self._auth().complete_google_login(parse_qs(urlparse(self.path).query), expected_state=self._oauth_state())
            session_id, csrf = self._auth().create_session(context)
            self._redirect_frontend(session_id=session_id, csrf=csrf)
        except AuthError:
            self._redirect(f"{self._frontend_url()}/login?auth=failed", clear_oauth_state=True)

    def _auth_me(self) -> None:
        context = self._current_context()
        if context is None:
            self._send_json(HTTPStatus.OK, {"authenticated": False})
            return
        self._send_json(
            HTTPStatus.OK,
            {
                "authenticated": True,
                "user": {"id": context.user_id, "email": context.email, "name": context.name},
                "business": {"id": context.business_id, "name": context.business_name},
                "csrf_token": context.csrf_token,
            },
        )

    def _list_datasets(self, tenant_id: str) -> None:
        schema_name = tenant_schema_name(tenant_id)
        try:
            engine = create_engine(_database_url(), pool_pre_ping=True)
            inspector = inspect(engine)
            datasets = []
            with engine.begin() as connection:
                for table_name in inspector.get_table_names(schema=schema_name):
                    row_count = connection.execute(text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')).scalar_one()
                    columns = inspector.get_columns(table_name, schema=schema_name)
                    datasets.append(
                        {
                            "table_name": table_name,
                            "row_count": row_count,
                            "columns": [{"name": column["name"], "type": str(column["type"])} for column in columns],
                        }
                    )
            self._send_json(HTTPStatus.OK, {"datasets": datasets})
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Datasets are unavailable."})

    def _upload_dataset(self, tenant_id: str, payload: dict) -> None:
        filename = payload.get("filename")
        csv_text = payload.get("csv_text")
        if not isinstance(filename, str) or not isinstance(csv_text, str):
            self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "filename and csv_text are required."})
            return
        try:
            engine = create_engine(_database_url(), pool_pre_ping=True)
            result = DatasetIngestionService(engine).ingest_csv(
                tenant_id=tenant_id,
                filename=filename,
                content=csv_text.encode("utf-8"),
            )
            self.application_services.pop(tenant_id, None)
        except DatasetError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Dataset upload is unavailable."})
            return
        self._send_json(HTTPStatus.CREATED, result.model_dump(mode="json"))

    def _tenant_id(self) -> str:
        context = self._current_context()
        if context is not None:
            tenant_id = context.tenant_id
        elif os.getenv("AUTH_MODE", "oauth").lower() == "development" and os.getenv("LOCAL_TENANT_ID"):
            tenant_id = os.environ["LOCAL_TENANT_ID"]
        else:
            raise DatasetError("Authentication is required.")
        if not tenant_id.strip():
            raise DatasetError("A tenant identifier is required.")
        tenant_schema_name(tenant_id)
        return tenant_id

    def _auth(self) -> AuthService:
        if self.auth_service is None:
            self.__class__.auth_service = AuthService(auth_engine())
            self.__class__.auth_service.initialize()
        return self.auth_service

    def _current_context(self) -> AuthenticatedContext | None:
        return self._auth().resolve_session(self._session_id())

    def _require_authenticated(self) -> AuthenticatedContext | None:
        context = self._current_context()
        if context is None:
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Authentication is required."})
            return None
        return context

    def _require_csrf(self, context: AuthenticatedContext) -> bool:
        try:
            self._auth().require_csrf(context, self.headers.get("X-CSRF-Token"))
            return True
        except AuthError as exc:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": str(exc)})
            return False

    def _session_id(self) -> str | None:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        morsel = cookie.get(AuthService.SESSION_COOKIE)
        return self._auth().session_id_from_cookie(morsel.value if morsel else None)

    def _oauth_state(self) -> str | None:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        morsel = cookie.get(AuthService.OAUTH_STATE_COOKIE)
        return morsel.value if morsel else None

    def _frontend_url(self) -> str:
        return os.getenv("FRONTEND_URL", os.getenv("FRONTEND_ORIGIN", self.allowed_origin)).rstrip("/")

    def _cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        allowed_origin = os.getenv("FRONTEND_URL", os.getenv("FRONTEND_ORIGIN", self.allowed_origin)).rstrip("/")
        if origin == allowed_origin:
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Credentials", "true")

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: HTTPStatus, page: str) -> None:
        body = page.encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect_frontend(self, *, session_id: str, csrf: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self._set_auth_cookies(session_id, csrf)
        self._clear_oauth_state_cookie()
        self.send_header("Location", self._frontend_url())
        self.end_headers()

    def _redirect(self, location: str, *, oauth_state: str | None = None, clear_oauth_state: bool = False) -> None:
        self.send_response(HTTPStatus.FOUND)
        if oauth_state:
            self._set_oauth_state_cookie(oauth_state)
        if clear_oauth_state:
            self._clear_oauth_state_cookie()
        self.send_header("Location", location)
        self.end_headers()

    def _set_auth_cookies(self, session_id: str, csrf: str) -> None:
        secure = os.getenv("COOKIE_SECURE", "true").lower() != "false"
        same_site = os.getenv("COOKIE_SAMESITE", "Lax")
        max_age = AuthService.SESSION_HOURS * 60 * 60
        suffix = f"Max-Age={max_age}; Path=/; SameSite={same_site}"
        if secure:
            suffix += "; Secure"
        self.send_header("Set-Cookie", f"{AuthService.SESSION_COOKIE}={self._auth().sign_session_cookie(session_id)}; HttpOnly; {suffix}")
        self.send_header("Set-Cookie", f"{AuthService.CSRF_COOKIE}={csrf}; {suffix}")

    def _clear_auth_cookies(self) -> None:
        suffix = "Max-Age=0; Path=/; SameSite=Lax"
        self.send_header("Set-Cookie", f"{AuthService.SESSION_COOKIE}=; HttpOnly; {suffix}")
        self.send_header("Set-Cookie", f"{AuthService.CSRF_COOKIE}=; {suffix}")

    def _set_oauth_state_cookie(self, state: str) -> None:
        secure = os.getenv("COOKIE_SECURE", "true").lower() != "false"
        suffix = "Max-Age=600; Path=/auth/callback; SameSite=Lax; HttpOnly"
        if secure:
            suffix += "; Secure"
        self.send_header("Set-Cookie", f"{AuthService.OAUTH_STATE_COOKIE}={state}; {suffix}")

    def _clear_oauth_state_cookie(self) -> None:
        self.send_header("Set-Cookie", f"{AuthService.OAUTH_STATE_COOKIE}=; Max-Age=0; Path=/auth/callback; SameSite=Lax; HttpOnly")

    @staticmethod
    def _openapi_schema() -> dict:
        return {
            "openapi": "3.0.3",
            "info": {"title": "Text-to-SQL API", "version": "1.0.0"},
            "paths": {
                "/auth/login": {"get": {"summary": "Start Google OAuth login", "responses": {"302": {"description": "Redirect to Google"}}}},
                "/auth/callback": {"get": {"summary": "Complete Google OAuth login", "responses": {"303": {"description": "Redirect to frontend"}}}},
                "/auth/me": {"get": {"summary": "Return authenticated user and business", "responses": {"200": {"description": "Authentication state"}}}},
                "/auth/logout": {"post": {"summary": "Invalidate the current session", "responses": {"204": {"description": "Logged out"}}}},
                "/query": {
                    "post": {
                        "summary": "Run a natural-language analytical query",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["query"],
                                        "properties": {
                                            "query": {"type": "string"},
                                            "clarification_state": {"type": "object"},
                                            "clarification_answer": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {"description": "QueryResponse"},
                            "401": {"description": "Authentication required"},
                            "403": {"description": "CSRF validation failed"},
                            "422": {"description": "Invalid request"},
                            "500": {"description": "Query service unavailable"},
                        },
                    }
                }
                ,
                "/datasets/upload": {
                    "post": {
                        "summary": "Create a tenant-isolated table from a CSV file",
                        "parameters": [{"name": "X-CSRF-Token", "in": "header", "required": True, "schema": {"type": "string"}}],
                        "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "required": ["filename", "csv_text"]}}}},
                        "responses": {"201": {"description": "Dataset uploaded"}, "400": {"description": "CSV validation failure"}, "401": {"description": "Authentication required"}, "403": {"description": "CSRF validation failed"}},
                    }
                },
                "/datasets": {
                    "get": {
                        "summary": "List datasets in the authenticated tenant",
                        "responses": {"200": {"description": "Tenant datasets"}, "401": {"description": "Authentication required"}},
                    }
                }
            },
        }

    @staticmethod
    def _documentation_page() -> str:
        return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Text-to-SQL API</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:48px auto;padding:0 24px;color:#172033}code,pre{background:#f2f4f8;border-radius:6px;padding:3px 6px}pre{padding:16px;overflow:auto}h1{margin-bottom:8px}</style>
</head><body><h1>Text-to-SQL API</h1><p>The API is running. Send natural-language requests to <code>POST /query</code>.</p>
<h2>Request</h2><pre>{"query":"Return 10 customers."}</pre>
<h2>Routes</h2><ul><li><code>GET /health</code> — service status</li><li><code>GET /openapi.json</code> — API schema</li><li><code>POST /query</code> — query pipeline</li></ul>
</body></html>"""

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        """Avoid logging request bodies or sensitive configuration."""


def main() -> None:
    load_dotenv()
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    QueryRequestHandler.allowed_origin = os.getenv("FRONTEND_URL", os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")).rstrip("/")
    QueryRequestHandler.auth_service = AuthService(auth_engine())
    QueryRequestHandler.auth_service.initialize()
    server = ThreadingHTTPServer((host, port), QueryRequestHandler)
    print(f"Query API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
