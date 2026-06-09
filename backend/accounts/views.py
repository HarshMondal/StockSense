"""Session-based auth endpoints for the React SPA."""
from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .decorators import json_login_required, parse_json_body


def _user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username, "email": user.email}


@ensure_csrf_cookie
@require_GET
def csrf_view(request: HttpRequest) -> JsonResponse:
    """Seed the csrftoken cookie so the SPA can send X-CSRFToken on mutations."""
    return JsonResponse({"detail": "CSRF cookie set."})


@require_POST
def signup_view(request: HttpRequest) -> JsonResponse:
    data = parse_json_body(request)
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    errors: dict = {}
    if not username:
        errors["username"] = "Username is required."
    elif User.objects.filter(username__iexact=username).exists():
        errors["username"] = "That username is already taken."
    if email and User.objects.filter(email__iexact=email).exists():
        errors["email"] = "An account with that email already exists."
    if not password:
        errors["password"] = "Password is required."
    else:
        try:
            validate_password(password)
        except ValidationError as exc:
            errors["password"] = list(exc.messages)
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return JsonResponse(_user_payload(user), status=201)


@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    data = parse_json_body(request)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=401)
    login(request, user)
    return JsonResponse(_user_payload(user))


@require_POST
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"detail": "Logged out."})


@json_login_required
@require_GET
def me_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(_user_payload(request.user))
