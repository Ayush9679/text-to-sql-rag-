import json
import threading
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from app.api import server as api_server
from app.auth.service import AuthenticatedContext, AuthService


class _FakeAuth:
    def __init__(self):
        self.logged_out = []
        self.contexts = {
            "session-a": AuthenticatedContext(
                user_id="user-a",
                email="a@example.com",
                name="A",
                business_id="business-a",
                business_name="A Business",
                tenant_id="business-a",
                csrf_token="csrf-a",
            ),
            "session-b": AuthenticatedContext(
                user_id="user-b",
                email="b@example.com",
                name="B",
                business_id="business-b",
                business_name="B Business",
                tenant_id="business-b",
                csrf_token="csrf-b",
            ),
        }

    def initialize(self):
        return None

    def session_id_from_cookie(self, cookie_value):
        return cookie_value

    def resolve_session(self, session_id):
        return self.contexts.get(session_id)

    def require_csrf(self, context, supplied):
        if supplied != context.csrf_token:
            raise api_server.AuthError("CSRF validation failed.")

    def logout(self, session_id):
        self.logged_out.append(session_id)
        self.contexts.pop(session_id, None)


@pytest.fixture
def http_api(monkeypatch):
    fake_auth = _FakeAuth()
    handler = api_server.QueryRequestHandler
    handler.auth_service = fake_auth
    handler.application_services = {}
    handler.allowed_origin = "http://localhost:3000"
    monkeypatch.setenv("SESSION_SECRET", "x" * 40)
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", fake_auth
    finally:
        httpd.shutdown()
        thread.join(timeout=5)


def _request(url, *, method="GET", body=None, session=None, csrf=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if session:
        headers["Cookie"] = f"{AuthService.SESSION_COOKIE}={session}"
    if csrf:
        headers["X-CSRF-Token"] = csrf
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            payload = response.read()
            return response.status, dict(response.headers), json.loads(payload or b"{}")
    except HTTPError as error:
        return error.code, dict(error.headers), json.loads(error.read() or b"{}")


def test_unauthenticated_query_is_401(http_api):
    base_url, _auth = http_api

    status, _headers, body = _request(f"{base_url}/query", method="POST", body={"query": "show customers"})

    assert status == HTTPStatus.UNAUTHORIZED
    assert "Authentication is required" in body["error"]


def test_unauthenticated_upload_is_401(http_api):
    base_url, _auth = http_api

    status, _headers, body = _request(
        f"{base_url}/datasets/upload",
        method="POST",
        body={"filename": "customers.csv", "csv_text": "id\n1\n"},
    )

    assert status == HTTPStatus.UNAUTHORIZED
    assert "Authentication is required" in body["error"]


def test_auth_me_returns_safe_identity(http_api):
    base_url, _auth = http_api

    status, _headers, body = _request(f"{base_url}/auth/me", session="session-a")

    assert status == HTTPStatus.OK
    assert body == {
        "authenticated": True,
        "user": {"id": "user-a", "email": "a@example.com", "name": "A"},
        "business": {"id": "business-a", "name": "A Business"},
        "csrf_token": "csrf-a",
    }


def test_invalid_session_auth_me_is_unauthenticated(http_api):
    base_url, _auth = http_api

    status, _headers, body = _request(f"{base_url}/auth/me", session="missing")

    assert status == HTTPStatus.OK
    assert body == {"authenticated": False}


def test_logout_invalidates_session_and_requires_csrf(http_api):
    base_url, auth = http_api

    status, _headers, body = _request(f"{base_url}/auth/logout", method="POST", session="session-a")
    assert status == HTTPStatus.FORBIDDEN
    assert "CSRF" in body["error"]

    status, _headers, _body = _request(f"{base_url}/auth/logout", method="POST", session="session-a", csrf="csrf-a")
    assert status == HTTPStatus.NO_CONTENT
    assert auth.logged_out == ["session-a"]

    status, _headers, body = _request(f"{base_url}/auth/me", session="session-a")
    assert status == HTTPStatus.OK
    assert body == {"authenticated": False}


def test_query_uses_session_tenant_not_browser_tenant(http_api, monkeypatch):
    base_url, _auth = http_api
    tenants = []

    class _Response:
        def model_dump(self, mode="json"):
            return {"status": "success", "columns": [], "rows": [], "row_count": 0, "metadata": {"mode": mode}}

    class _App:
        def handle(self, request):
            return _Response()

    def build(tenant_id):
        tenants.append(tenant_id)
        return _App()

    monkeypatch.setattr(api_server, "build_application_service", build)

    status, _headers, body = _request(
        f"{base_url}/query",
        method="POST",
        session="session-a",
        csrf="csrf-a",
        body={"query": "show customers", "tenant_id": "business-b"},
    )

    assert status == HTTPStatus.OK
    assert body["status"] == "success"
    assert tenants == ["business-a"]


def test_upload_uses_session_tenant_not_browser_tenant(http_api, monkeypatch):
    base_url, _auth = http_api
    tenants = []

    class _Result:
        def model_dump(self, mode="json"):
            return {"tenant_id": tenants[-1], "schema_name": "tenant_business_a", "table_name": "customers", "row_count": 1, "columns": []}

    class _Ingestion:
        def __init__(self, _engine):
            return None

        def ingest_csv(self, *, tenant_id, filename, content):
            tenants.append(tenant_id)
            return _Result()

    monkeypatch.setattr(api_server, "create_engine", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(api_server, "DatasetIngestionService", _Ingestion)

    status, _headers, body = _request(
        f"{base_url}/datasets/upload",
        method="POST",
        session="session-a",
        csrf="csrf-a",
        body={"filename": "customers.csv", "csv_text": "id\n1\n", "tenant_id": "business-b"},
    )

    assert status == HTTPStatus.CREATED
    assert body["tenant_id"] == "business-a"
    assert tenants == ["business-a"]


def test_dataset_listing_uses_only_session_tenant_schema(http_api, monkeypatch):
    base_url, _auth = http_api
    schemas_seen = []

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _statement):
            return type("Result", (), {"scalar_one": lambda self: 2})()

    class _Engine:
        def begin(self):
            return _Connection()

    class _Inspector:
        def get_table_names(self, *, schema):
            schemas_seen.append(schema)
            return ["customers"]

        def get_columns(self, table_name, *, schema):
            schemas_seen.append(schema)
            assert table_name == "customers"
            return [{"name": "id", "type": "INTEGER"}]

    monkeypatch.setattr(api_server, "create_engine", lambda *_args, **_kwargs: _Engine())
    monkeypatch.setattr(api_server, "inspect", lambda _engine: _Inspector())

    status, _headers, body = _request(f"{base_url}/datasets", session="session-a")

    assert status == HTTPStatus.OK
    assert body["datasets"] == [{"table_name": "customers", "row_count": 2, "columns": [{"name": "id", "type": "INTEGER"}]}]
    assert schemas_seen == ["tenant_business_a", "tenant_business_a"]
