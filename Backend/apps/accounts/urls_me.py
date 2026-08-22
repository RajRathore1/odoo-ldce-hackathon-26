"""
Routes for `/users/me/**`. Separate from `urls.py` because `/auth/**`
and `/users/me/**` are different prefixes owned by the same app.

Empty until the endpoints land — the include in `config/` already
resolves, so adding a route here needs no change to `config/`.
"""

urlpatterns: list = []
