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

## Database

```bash
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py createsuperuser   # prompts for email, not username
```

`AUTH_USER_MODEL = accounts.User` (email login, no username) and
`CITIES_LIGHT_APP_NAME = "geo"` are both set. `MIGRATION_MODULES` disables
cities-light's own migrations so Country/Region/SubRegion/City are created in
`geo` with the extra `cost_index` / `popularity` / `blurb` / `image` fields.
There must be no `cities_light_*` tables; if you see any, the DB predates
these settings — delete `db.sqlite3` and re-migrate.

The city and activity tables are empty until the Step 4 import/seed.

## Endpoints

### Auth (`/api/auth/`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `register/` | public | returns user + token pair |
| POST | `login/` | public | email + password |
| POST | `refresh/` | public | rotates the refresh token |
| POST | `logout/` | bearer | blacklists the refresh token |
| POST | `password-reset/` | public | always 200; never reveals if the email exists |
| POST | `password-reset/confirm/` | public | takes `uid`, `token`, `new_password` |
| GET PATCH DELETE | `me/` | bearer | PATCH accepts multipart for `photo`; DELETE is permanent |
| GET POST | `me/saved-destinations/` | bearer | |
| DELETE | `me/saved-destinations/{id}/` | bearer | |

Access tokens last 60 minutes, refresh tokens 7 days with rotation and
blacklist-after-rotation. Send `Authorization: Bearer <access>`.

Reset mail prints to the console in development. The link points at
`FRONTEND_PASSWORD_RESET_URL` with `?uid=&token=` appended; the frontend
reads those off the query string and posts them to the confirm endpoint.

### Catalogue (public)

| Method | Path |
|---|---|
| GET | `/api/cities/` |
| GET | `/api/cities/{id}/` |
| GET | `/api/activities/` |
| GET | `/api/activities/{id}/` |

`/api/cities/` supports `?search=` (transliterated — `zurich`, `Zürich` and
`zurich switzerland` all match), `?country=`, `?country_code=`, `?continent=`,
`?region=`, `?cost_index_min=`, `?cost_index_max=`, and
`?ordering=popularity|population|name|cost_index`.

`/api/activities/` supports `?search=`, `?city=`, `?category=`, `?cost_min=`,
`?cost_max=`, `?duration_max=`, and
`?ordering=cost|popularity|duration_minutes|name`.

## Tests

```bash
./venv/Scripts/python.exe manage.py test
```
