# GlobeTrotter — Odoo LDCE Hackathon '26

Personalized multi-city travel planning platform. Users build multi-stop
itineraries, attach activities to each stop, track budgets, and share trips
publicly.

## Structure

| Folder | What | Stack |
|---|---|---|
| `Backend/` | REST API — `/api/v1/**` and `/api/v1/admin/**` | Django 5 + DRF, SQLite, JWT |
| `Frontend/` | user-facing client | TBD |
| `Admin_Panel/` | admin dashboard | TBD |

## Getting started

### Backend

```bash
cd Backend
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash
# source .venv/bin/activate        # macOS / Linux

pip install -r requirements/dev.txt
cp .env.example .env

python manage.py migrate
python manage.py seed_all
python manage.py runserver
```

| URL | What |
|---|---|
| <http://localhost:8000/api/docs/> | **Swagger UI — the API reference** |
| <http://localhost:8000/api/redoc/> | ReDoc |
| <http://localhost:8000/api/schema/> | raw OpenAPI schema |
| <http://localhost:8000/django-admin/> | Django admin |

Demo login: `demo@globetrotter.dev` / `Demo@1234`

Reset the database at any time:

```bash
rm db.sqlite3 && python manage.py migrate && python manage.py seed_all
```

### Frontend / Admin Panel

Setup instructions to be added by their owners. Both consume the backend API —
use the Swagger UI above as the contract, plus the Postman collection at
`Backend/postman/`.

## API conventions

Two things worth knowing before writing a single client call:

**1. Every response uses the same envelope.**

```json
{ "success": true, "message": null, "data": { } }
{ "success": false, "message": "...", "errors": { } }
```

**2. Every list endpoint is paginated** — results at `data.results`, meta at
`data.pagination`.

```json
{
  "success": true,
  "data": {
    "results": [],
    "pagination": { "count": 137, "page": 2, "pages": 7, "page_size": 20,
                    "has_next": true, "has_previous": true,
                    "next": "...", "previous": "..." }
  }
}
```

Query params: `?page=`, `?page_size=` (max 100), plus `?search=` and `?ordering=`
on every list. Auth header: `Authorization: Bearer <access_token>`.
