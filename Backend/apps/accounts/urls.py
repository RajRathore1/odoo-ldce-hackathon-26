"""
User-facing routes for accounts. Mounted by `config/api_urls.py` at `/auth/`.

`/users/me/**` lives in `urls_me.py` — different prefix, same app.
"""

from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path(
        "password/forgot/",
        views.PasswordForgotView.as_view(),
        name="auth-password-forgot",
    ),
    path(
        "password/reset/", views.PasswordResetView.as_view(), name="auth-password-reset"
    ),
    path(
        "password/change/",
        views.PasswordChangeView.as_view(),
        name="auth-password-change",
    ),
]
