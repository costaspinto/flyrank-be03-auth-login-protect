import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import supabase_auth

@pytest.fixture
def client():
    return TestClient(app)

def fake_user():
    return {
        "id": "user-123",
        "email": "intern@example.com",
        "created_at": "2026-01-01T00:00:00Z",
        "last_sign_in_at": "2026-01-02T00:00:00Z",
        "user_metadata": {},
    }

def test_root_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "healthy"

def test_public_info_needs_no_token(client):
    response = client.get("/public/info")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome stranger! This info is public."

def test_protected_profile_rejects_missing_token(client):
    response = client.get("/protected/profile")
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Access token required"

def test_protected_profile_rejects_invalid_token(client, monkeypatch):
    def invalid(_token):
        raise supabase_auth.AuthProviderError("Invalid or expired token")
    monkeypatch.setattr(supabase_auth, "verify_access_token", invalid)
    response = client.get("/protected/profile", headers={"Authorization": "Bearer bad-token"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Invalid or expired token"

def test_protected_profile_accepts_valid_token(client, monkeypatch):
    monkeypatch.setattr(supabase_auth, "verify_access_token", lambda _token: fake_user())
    response = client.get("/protected/profile", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200
    assert response.json()["id"] == "user-123"
    assert response.json()["email"] == "intern@example.com"

def test_dashboard_is_protected(client, monkeypatch):
    monkeypatch.setattr(supabase_auth, "verify_access_token", lambda _token: fake_user())
    response = client.get("/protected/dashboard", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-123"

def test_signup_validation_returns_422_for_bad_email(client):
    response = client.post("/auth/signup", json={"email": "not-an-email", "password": "example-password"})
    assert response.status_code == 422

def test_signup_success_returns_201(client, monkeypatch):
    monkeypatch.setattr(supabase_auth, "signup", lambda email, password: {"user": fake_user()})
    response = client.post("/auth/signup", json={"email": "intern@example.com", "password": "example-password"})
    assert response.status_code == 201
    assert response.json()["user"]["id"] == "user-123"

def test_login_success_returns_tokens(client, monkeypatch):
    monkeypatch.setattr(supabase_auth, "login", lambda email, password: {
        "user": fake_user(), "access_token": "test-access-token",
        "refresh_token": "test-refresh-token", "token_type": "bearer"
    })
    response = client.post("/auth/login", json={"email": "intern@example.com", "password": "example-password"})
    assert response.status_code == 200
    assert response.json()["access_token"] == "test-access-token"
    assert response.json()["refresh_token"] == "test-refresh-token"

def test_login_failure_returns_401(client, monkeypatch):
    def fail(_email, _password):
        raise supabase_auth.AuthProviderError("Invalid login credentials")
    monkeypatch.setattr(supabase_auth, "login", fail)
    response = client.post("/auth/login", json={"email": "intern@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Invalid login credentials"

def test_logout_requires_token(client):
    assert client.post("/auth/logout").status_code == 401

def test_logout_success_returns_204(client, monkeypatch):
    monkeypatch.setattr(supabase_auth, "verify_access_token", lambda _token: fake_user())
    monkeypatch.setattr(supabase_auth, "logout", lambda _token: None)
    response = client.post("/auth/logout", headers={"Authorization": "Bearer valid-token"})
    assert response.status_code == 204


def test_signup_missing_fields_returns_400(client):
    response = client.post("/auth/signup", json={"email": "intern@example.com"})
    assert response.status_code == 400

def test_login_missing_fields_returns_400(client):
    response = client.post("/auth/login", json={"email": "intern@example.com"})
    assert response.status_code == 400
