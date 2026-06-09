"""Auth helpers that return JSON (not redirects) for the SPA."""
from __future__ import annotations

import functools
import json
from typing import Any, Callable

from django.http import HttpRequest, JsonResponse


def json_login_required(view: Callable[..., JsonResponse]) -> Callable[..., JsonResponse]:
    """Return 401 JSON for anonymous users instead of redirecting to a login page."""

    @functools.wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        return view(request, *args, **kwargs)

    return wrapper


def parse_json_body(request: HttpRequest) -> dict:
    """Parse a JSON request body into a dict, tolerating empty bodies."""
    if not request.body:
        return {}
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
