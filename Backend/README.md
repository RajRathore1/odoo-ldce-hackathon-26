# GlobeTrotter — Backend

Django + DRF JSON API for the GlobeTrotter travel planner. SQLite is the
project database. No templates — `Frontend/` and `Admin_Panel/` are separate
clients.

## Setup

```bash
py -3 -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
cp .env.example .env        # then set SECRET_KEY
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py runserver
```

Generate a secret key with:
`python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`

## API docs

- Swagger UI — http://127.0.0.1:8000/api/schema/swagger-ui/
- OpenAPI schema — http://127.0.0.1:8000/api/schema/

## Layout

| Path | Purpose |
|---|---|
| `config/` | settings, root URLs, WSGI/ASGI |
| `common/` | shared pagination + `IsOwner` permission |
| `accounts/` | custom email-login user, profile, saved destinations |
| `geo/` | Country/Region/SubRegion/City (django-cities-light) + Activity catalogue |
| `trips/` | Trip, TripStop, StopActivity, budget |
| `community/` | public community feed |
| `analytics/` | admin-only aggregate stats (no models) |

## Migrations — read before running `migrate`

`AUTH_USER_MODEL` and `CITIES_LIGHT_APP_NAME` are both set in Step 2 and are
effectively one-way once the first migration is applied. Do not run `migrate`
until the `accounts.User` and `geo` models are in place; the two spots to
change are marked `STEP 2` in `config/settings.py`.
