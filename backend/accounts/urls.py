"""URL configuration for the accounts (auth) app."""
from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf_view, name="auth-csrf"),
    path("signup/", views.signup_view, name="auth-signup"),
    path("login/", views.login_view, name="auth-login"),
    path("logout/", views.logout_view, name="auth-logout"),
    path("me/", views.me_view, name="auth-me"),
]
