"""Auth happy-path + guard tests via the Django test client."""
from __future__ import annotations

import json

import pytest
from django.test import Client


@pytest.mark.django_db
def test_signup_login_me_logout_flow():
    client = Client()

    # Anonymous -> 401
    assert client.get("/api/auth/me/").status_code == 401

    # Signup auto-logs-in
    resp = client.post(
        "/api/auth/signup/",
        data=json.dumps({"username": "alice", "email": "a@x.com", "password": "Sup3rStr0ng!pw"}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "alice"

    # me works while authenticated
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    # logout, then me -> 401
    assert client.post("/api/auth/logout/").status_code == 200
    assert client.get("/api/auth/me/").status_code == 401

    # login again
    login = client.post(
        "/api/auth/login/",
        data=json.dumps({"username": "alice", "password": "Sup3rStr0ng!pw"}),
        content_type="application/json",
    )
    assert login.status_code == 200


@pytest.mark.django_db
def test_signup_rejects_weak_password():
    client = Client()
    resp = client.post(
        "/api/auth/signup/",
        data=json.dumps({"username": "bob", "email": "b@x.com", "password": "123"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "password" in resp.json()["errors"]


@pytest.mark.django_db
def test_login_with_bad_credentials_returns_401():
    client = Client()
    resp = client.post(
        "/api/auth/login/",
        data=json.dumps({"username": "ghost", "password": "whatever"}),
        content_type="application/json",
    )
    assert resp.status_code == 401
