# API Contract

**~88 routes across 8 modules.** This is what the frontend builds against — keep it
accurate. Screen numbers refer to the PDF spec.

---

## 1. Conventions

| | |
|---|---|
| User API base | `http://localhost:8000/api/v1` |
| Admin API base | `http://localhost:8000/api/v1/admin` |
| Auth header | `Authorization: Bearer <access_token>` |
| Live docs | `/api/docs/` (Swagger) · `/api/redoc/` · `/api/schema/` |
| Content type | `application/json`; uploads → `multipart/form-data` |
| Dates | `YYYY-MM-DD` · Datetimes `YYYY-MM-DDTHH:MM:SSZ` (UTC) · Times `HH:MM:SS` |
| Trailing slash | **required** on every route |

### Response envelope

Every response has the same outer shape. Built by `core/renderers.EnvelopeJSONRenderer`.

**Single object**
```json
{ "success": true, "message": null, "data": { "id": 12, "name": "Europe Summer" } }
```

**List — always paginated**
```json
{
  "success": true,
  "message": null,
  "data": {
    "results": [ { "id": 12 }, { "id": 13 } ],
    "pagination": {
      "count": 137, "page": 2, "pages": 7, "page_size": 20,
      "has_next": true, "has_previous": true,
      "next": "http://localhost:8000/api/v1/trips/?page=3",
      "previous": "http://localhost:8000/api/v1/trips/?page=1"
    }
  }
}
```

**Error**
```json
{
  "success": false,
  "message": "This field is required.",
  "errors": { "fields": { "start_date": ["This field is required."] } }
}
```

> **Frontend note:** list payloads are always at `data.results`, meta always at
> `data.pagination`. Build one fetch wrapper around that and you never think about
> it again.

### Pagination

`StandardPagination` is the DRF default → **every list endpoint is paginated** with
no per-view work.

| Param | Default | Max |
|---|---|---|
| `page` | 1 | — |
| `page_size` | 20 | 100 |

- City and activity pickers use `LargePagination`: default **50**, max 200.
- The community feed uses `FeedCursorPagination`: `?cursor=<opaque>&page_size=20`
  — cursor-based so posts arriving mid-scroll don't shift items across pages.
- Analytics endpoints are **not** paginated (bounded top-N / fixed windows).

### Shared list params

On every list endpoint unless noted: `?search=`, `?ordering=` (prefix `-` for
desc), `?page=`, `?page_size=`.

### Status codes

`200` OK · `201` Created · `204` No Content · `400` validation ·
`401` missing/expired token · `403` wrong owner or non-admin ·
`404` not found or soft-deleted · `409` conflict · `500` unhandled.

### Priority / ownership legend

**P0** must ship · **P1** if on schedule · **P2** cut first
**A** = Dev A · **B** = Dev B

---

## 2. Auth — `/auth/` · Screen 1 · **Dev A · P0**

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register/` | — | create account |
| POST | `/auth/login/` | — | access + refresh |
| POST | `/auth/token/refresh/` | — | rotate access token |
| POST | `/auth/logout/` | ✅ | blacklist refresh token |
| POST | `/auth/password/forgot/` | — | issue reset token |
| POST | `/auth/password/reset/` | — | consume token, set password |
| POST | `/auth/password/change/` | ✅ | change while logged in |

**POST `/auth/register/`**

Params: `email`*, `password`*, `confirm_password`*, `first_name`*, `last_name`,
`phone_number`, `city` (id), `country` (id), `additional_info`

```json
{
  "success": true,
  "message": "Account created successfully.",
  "data": {
    "user": {
      "id": 7, "email": "riya@example.com", "first_name": "Riya",
      "last_name": "Sharma", "avatar": null, "role": "USER",
      "city": { "id": 42, "name": "Ahmedabad" },
      "country": { "id": 3, "name": "India", "iso2": "IN" }
    },
    "tokens": {
      "access": "eyJhbGciOiJIUzI1NiIs...",
      "refresh": "eyJhbGciOiJIUzI1NiIs..."
    }
  }
}
```

**POST `/auth/login/`** — `email`*, `password`*. Same `data` shape as register.
`401` on bad credentials, `403` when `is_active=False`.

> Implementation note: `django.contrib.auth.authenticate()` returns `None` for
> *both* cases, because `ModelBackend` rejects `is_active=False` before the view
> sees it. `LoginSerializer` re-checks explicitly to tell them apart. The 403 is
> only returned to a caller who already supplied the correct password, so it is
> not an account-enumeration oracle.
>
> Email is matched case-insensitively and stored lower-cased.

**POST `/auth/password/forgot/`** — `email`*. Always `200` with a generic message,
so the endpoint never leaks whether an address exists. In dev the token prints to
the console.

```json
{ "success": true, "message": "If that email exists, a reset link has been sent.", "data": null }
```

**POST `/auth/password/reset/`** — `token`*, `password`*, `confirm_password`*.
`400` if the token is expired, already used, or unknown.

---

## 3. Profile — `/users/me/` · Screen 12 · **Dev A · P0**

> Saved destinations (last 3 rows) are served by **Dev B** from `apps/geo/` — see
> `MODELS.md` §4 for why. Same URL prefix, different app.
>
> Note on ownership throughout this document: **Dev A owns every model**
> (except `community` / `analytics`); the owner tag on each section is the owner of
> the **endpoints**. See `TODO.md` §1.

| Method | Path | Purpose |
|---|---|---|
| GET | `/users/me/` | current profile |
| PATCH | `/users/me/` | update name, phone, language, currency, city, country, additional_info |
| POST | `/users/me/avatar/` | upload photo (`multipart`, field `avatar`) |
| DELETE | `/users/me/` | delete account — soft delete + blacklist tokens |
| GET | `/users/me/stats/` | counts for the profile header |
| GET | `/users/me/saved-destinations/` | paginated |
| POST | `/users/me/saved-destinations/` | `city`* (id), `note` |
| DELETE | `/users/me/saved-destinations/{id}/` | remove |

**GET `/users/me/`**
```json
{
  "success": true, "message": null,
  "data": {
    "id": 7, "email": "riya@example.com",
    "first_name": "Riya", "last_name": "Sharma", "full_name": "Riya Sharma",
    "phone_number": "+91 98250 11111",
    "avatar": "http://localhost:8000/media/users/avatars/7.jpg",
    "city": { "id": 42, "name": "Ahmedabad" },
    "country": { "id": 3, "name": "India", "iso2": "IN" },
    "additional_info": "", "language": "en", "currency": "INR",
    "role": "USER", "is_email_verified": false,
    "created_at": "2026-08-01T09:12:00Z"
  }
}
```

**GET `/users/me/stats/`**

> ⚠️ **Returns zeros until task A3.** Every figure aggregates over `trips`,
> which does not exist yet. The shape below is final, so the profile header can
> be built against it now.

```json
{
  "success": true, "message": null,
  "data": {
    "total_trips": 9, "ongoing": 1, "upcoming": 3, "completed": 5,
    "cities_visited": 21, "countries_visited": 7,
    "total_planned_spend": "412300.00", "currency": "INR"
  }
}
```

---

## 4. Geo — `/cities/`, `/countries/` · Screen 7 · **Dev B · P0**

| Method | Path | Purpose |
|---|---|---|
| GET | `/countries/` | dropdown source. `?search=`, `?region=` |
| GET | `/cities/` | **City Search** |
| GET | `/cities/{id}/` | detail + top 10 activities |
| GET | `/cities/popular/` | dashboard recommendations. `?limit=10` |

**GET `/cities/`**

| Param | Type | Notes |
|---|---|---|
| `search` | string | city name, state, country name |
| `country` | int | country id |
| `region` | string | `Asia`, `Europe`, … |
| `min_cost_index` / `max_cost_index` | decimal | |
| `ordering` | enum | `-popularity_score` (default), `name`, `cost_index`, `-cost_index` |
| `page` / `page_size` | int | `page_size` default **50** |

```json
{
  "success": true, "message": null,
  "data": {
    "results": [
      {
        "id": 88, "name": "Paris", "state": "Île-de-France",
        "country": { "id": 11, "name": "France", "iso2": "FR", "flag_emoji": "🇫🇷" },
        "region": "Europe",
        "cost_index": "142.50", "avg_daily_cost": "9800.00", "currency": "EUR",
        "popularity_score": 1284,
        "image_url": "https://cdn.globetrotter.dev/cities/paris.jpg",
        "activities_count": 37,
        "is_saved": true
      }
    ],
    "pagination": { "count": 150, "page": 1, "pages": 3, "page_size": 50,
                    "has_next": true, "has_previous": false,
                    "next": "http://localhost:8000/api/v1/cities/?page=2",
                    "previous": null }
  }
}
```

`is_saved` is annotated against the requesting user so the frontend renders the
bookmark state without a second call. `activities_count` is a `Count` annotation.

---

## 5. Activities catalog — `/activities/` · Screen 8 · **Dev B · P0**

| Method | Path | Purpose |
|---|---|---|
| GET | `/activity-categories/` | filter chips (unpaginated, small fixed set) |
| GET | `/activities/` | **Activity Search** |
| GET | `/activities/{id}/` | detail |
| GET | `/activities/popular/` | suggestions. `?city=&limit=` |

**GET `/activities/`**

| Param | Type | Notes |
|---|---|---|
| `search` | string | name + description |
| `city` | int | |
| `country` | int | via `city__country` |
| `category` | int | |
| `activity_type` | enum | `SIGHTSEEING`, `FOOD`, `ADVENTURE`, `CULTURE`, `NIGHTLIFE`, `SHOPPING`, `NATURE`, `RELAX`, `TRANSPORT`, `OTHER` |
| `min_cost` / `max_cost` | decimal | |
| `min_duration` / `max_duration` | int | minutes |
| `ordering` | enum | `-popularity_score` (default), `cost`, `-cost`, `duration_minutes`, `-rating` |

```json
{
  "success": true, "message": null,
  "data": {
    "results": [
      {
        "id": 512, "name": "Paragliding at Bir Billing",
        "description": "20-minute tandem flight with a certified pilot.",
        "activity_type": "ADVENTURE",
        "category": { "id": 4, "name": "Adventure", "slug": "adventure", "icon": "mountain" },
        "city": { "id": 61, "name": "Bir", "country_name": "India" },
        "cost": "2500.00", "currency": "INR",
        "duration_minutes": 90, "rating": "4.6", "popularity_score": 340,
        "image_url": "https://cdn.globetrotter.dev/activities/512.jpg"
      }
    ],
    "pagination": { "count": 412, "page": 1, "pages": 9, "page_size": 50,
                    "has_next": true, "has_previous": false,
                    "next": "http://localhost:8000/api/v1/activities/?page=2",
                    "previous": null }
  }
}
```

---

## 6. Dashboard — `/dashboard/` · Screen 2 · **Dev B · P0**

**GET `/dashboard/`** — one call, so the home screen isn't a five-request waterfall.
Lives in its own `apps/dashboard/` (views only, no models) and composes
`geo.selectors.popular_cities()` + `budget.services.bulk_trip_cost_summary()`.

```json
{
  "success": true, "message": null,
  "data": {
    "user": { "first_name": "Riya", "avatar": "http://.../7.jpg" },
    "counts": { "total_trips": 9, "ongoing": 1, "upcoming": 3, "completed": 5 },
    "ongoing_trip": {
      "id": 31, "name": "Himachal Winter",
      "start_date": "2026-08-18", "end_date": "2026-08-27",
      "stops_count": 3, "days_remaining": 5,
      "cover_photo": "http://.../covers/31.jpg"
    },
    "recent_trips": [
      { "id": 31, "name": "Himachal Winter", "status": "ONGOING",
        "start_date": "2026-08-18", "end_date": "2026-08-27",
        "stops_count": 3, "estimated_cost": "48200.00", "currency": "INR",
        "cover_photo": "http://.../covers/31.jpg" }
    ],
    "popular_cities": [
      { "id": 88, "name": "Paris", "country_name": "France",
        "popularity_score": 1284, "image_url": "https://.../paris.jpg" }
    ],
    "budget_highlights": {
      "currency": "INR",
      "total_planned": "412300.00",
      "upcoming_trips_budget": "96500.00",
      "avg_cost_per_trip": "45811.11",
      "over_budget_trips": 1
    }
  }
}
```

`ongoing_trip` is `null` when the user has none.

---

## 7. Trips — `/trips/` · Screens 3, 4, 6, 10, 11 · **Dev A**

### 7.1 Trip CRUD · P0

| Method | Path | Purpose |
|---|---|---|
| GET | `/trips/` | **My Trips** |
| POST | `/trips/` | **Create Trip** |
| GET | `/trips/{id}/` | detail with nested stops + activities |
| PATCH | `/trips/{id}/` | edit |
| DELETE | `/trips/{id}/` | soft delete |
| POST | `/trips/{id}/cover-photo/` | upload (`multipart`, field `cover_photo`) |
| POST | `/trips/{id}/duplicate/` | clone your own trip |

**GET `/trips/`**

| Param | Type | Notes |
|---|---|---|
| `status` | enum | `DRAFT`, `PLANNED`, `ONGOING`, `COMPLETED`, `CANCELLED` — Screen 6 tabs |
| `search` | string | name + description |
| `city` / `country` | int | trips containing this city/country |
| `start_date_after` / `start_date_before` | date | |
| `is_public` | bool | |
| `group_by` | enum | `status`, `month`, `country` — mockup's "Group by" control |
| `ordering` | enum | `-created_at` (default), `start_date`, `-start_date`, `name` |

```json
{
  "success": true, "message": null,
  "data": {
    "results": [
      {
        "id": 31, "name": "Himachal Winter", "description": "Bir + Manali + Kasol",
        "start_date": "2026-08-18", "end_date": "2026-08-27",
        "duration_days": 10, "status": "ONGOING",
        "cover_photo": "http://localhost:8000/media/trips/covers/31.jpg",
        "stops_count": 3, "activities_count": 14,
        "cities": ["Bir", "Manali", "Kasol"],
        "total_budget": "50000.00", "estimated_cost": "48200.00",
        "currency": "INR", "is_over_budget": false,
        "is_public": true,
        "share_url": "http://localhost:3000/trips/shared/9f1c8ab2-...",
        "created_at": "2026-07-02T11:40:00Z"
      }
    ],
    "pagination": { "count": 9, "page": 1, "pages": 1, "page_size": 20,
                    "has_next": false, "has_previous": false,
                    "next": null, "previous": null }
  }
}
```

With `?group_by=`, `data` gains a sibling key (`results` stays flat):
```json
"groups": [ { "key": "ONGOING",   "label": "Ongoing",  "count": 1 },
            { "key": "PLANNED",   "label": "Upcoming", "count": 3 },
            { "key": "COMPLETED", "label": "Completed","count": 5 } ]
```

> **Perf:** `estimated_cost` / `is_over_budget` come from
> `bulk_trip_cost_summary(trip_ids)` — one query for the whole page. Do **not**
> call `trip_cost_summary()` per row.

**POST `/trips/`** — `name`*, `start_date`*, `end_date`*, `description`,
`total_budget`, `currency`, `cover_photo` (file)

Validation: `end_date >= start_date`. Past `start_date` is allowed — users log
completed trips.

```json
{ "success": true, "message": "Trip created successfully.",
  "data": { "id": 44, "name": "Europe Summer",
            "start_date": "2026-11-02", "end_date": "2026-11-16",
            "duration_days": 15, "status": "PLANNED", "stops_count": 0,
            "currency": "INR", "total_budget": null,
            "share_token": "3b7f21ca-...", "is_public": false } }
```

### 7.2 Stops (sections) · Screen 5 · P0

| Method | Path | Purpose |
|---|---|---|
| GET | `/trips/{trip_id}/stops/` | list, ordered by `order` |
| POST | `/trips/{trip_id}/stops/` | **Add Stop** |
| GET | `/trips/{trip_id}/stops/{id}/` | detail |
| PATCH | `/trips/{trip_id}/stops/{id}/` | edit city / dates / budget |
| DELETE | `/trips/{trip_id}/stops/{id}/` | remove (cascades to its activities) |
| POST | `/trips/{trip_id}/stops/reorder/` | drag-to-reorder |

**POST `/trips/{trip_id}/stops/`** — `city`* (id), `start_date`*, `end_date`*,
`title`, `budget`, `notes`

`order` is assigned server-side (`max(order) + 1`). Validation: the stop range must
sit inside the trip range → `400` otherwise.

```json
{ "success": true, "message": "Stop added.",
  "data": { "id": 89, "title": "Bir",
            "city": { "id": 61, "name": "Bir", "country_name": "India",
                      "image_url": "https://.../bir.jpg" },
            "start_date": "2026-08-18", "end_date": "2026-08-21",
            "nights": 3, "order": 1, "budget": "18000.00",
            "activities_count": 0, "notes": "" } }
```

**POST `/trips/{trip_id}/stops/reorder/`**
```json
{ "items": [ { "id": 91, "order": 1 }, { "id": 89, "order": 2 }, { "id": 90, "order": 3 } ] }
```
One `bulk_update` in one transaction. Returns the reordered list. `400` if any id
does not belong to the trip.

### 7.3 Trip activities · Screen 5 · P0

| Method | Path | Purpose |
|---|---|---|
| GET | `/trips/{trip_id}/stops/{stop_id}/activities/` | list for a stop |
| POST | `/trips/{trip_id}/stops/{stop_id}/activities/` | attach catalog activity or custom entry |
| PATCH | `/trip-activities/{id}/` | edit time / cost / day / order |
| DELETE | `/trip-activities/{id}/` | remove |
| POST | `/trips/{trip_id}/activities/reorder/` | reorder / move across days |

Detail routes are **flat** (`/trip-activities/{id}/`) on purpose: calendar
drag-and-drop moves an item between days *and* stops, and a nested URL would encode
a parent that is about to change.

**POST `.../activities/`** — `activity` (id) **or** `custom_title`, plus `day_date`*,
`start_time`, `end_time`, `cost`, `duration_minutes`, `notes`

- Exactly one of `activity` / `custom_title` is required → `400` otherwise.
- If `activity` is given and `cost` is omitted, `cost` is **snapshotted** from the
  catalog.
- `day_date` must fall inside the parent stop's range.

**POST `/trips/{trip_id}/activities/reorder/`** — also handles moving between days:
```json
{ "items": [ { "id": 771, "order": 1, "day_date": "2026-08-19", "trip_stop": 89 } ] }
```

### 7.4 Itinerary view · Screen 6 · P0

**GET `/trips/{trip_id}/itinerary/`** — `?view=day` (default) or `?view=stop`.
Not paginated; a trip is a bounded object.

```json
{
  "success": true, "message": null,
  "data": {
    "trip": { "id": 31, "name": "Himachal Winter",
              "start_date": "2026-08-18", "end_date": "2026-08-27",
              "duration_days": 10, "currency": "INR" },
    "days": [
      {
        "date": "2026-08-18", "day_number": 1,
        "stop": { "id": 89, "title": "Bir",
                  "city": { "id": 61, "name": "Bir" }, "order": 1 },
        "activities": [
          { "id": 771, "title": "Paragliding at Bir Billing", "activity_id": 512,
            "activity_type": "ADVENTURE",
            "start_time": "09:30:00", "end_time": "11:00:00",
            "duration_minutes": 90, "cost": "2500.00", "currency": "INR",
            "order": 1, "notes": "" }
        ],
        "day_total_cost": "2500.00"
      },
      { "date": "2026-08-19", "day_number": 2,
        "stop": { "id": 89, "title": "Bir",
                  "city": { "id": 61, "name": "Bir" }, "order": 1 },
        "activities": [], "day_total_cost": "0.00" }
    ],
    "totals": { "activities_cost": "31400.00", "expenses_cost": "16800.00",
                "grand_total": "48200.00" }
  }
}
```

**Every date in the trip range appears, including empty days.** The frontend renders
a placeholder rather than computing gaps. `stop` is `null` on days not covered by
any stop.

### 7.5 Calendar · Screen 10 · P0

**GET `/trips/{trip_id}/calendar/`** — `?month=YYYY-MM` (optional; omit for the
whole trip)

Same data as the itinerary, shaped for a calendar grid. When `month` is given, the
range is padded to whole weeks so the grid is complete.

```json
{
  "success": true, "message": null,
  "data": {
    "range": { "start": "2026-08-01", "end": "2026-08-31" },
    "cells": [
      { "date": "2026-08-18", "in_trip": true, "stop_id": 89, "city_name": "Bir",
        "activity_count": 1, "day_total_cost": "2500.00", "is_over_budget": false,
        "items": [ { "id": 771, "title": "Paragliding at Bir Billing",
                     "start_time": "09:30:00", "activity_type": "ADVENTURE" } ] },
      { "date": "2026-08-01", "in_trip": false, "stop_id": null, "city_name": null,
        "activity_count": 0, "day_total_cost": "0.00", "is_over_budget": false,
        "items": [] }
    ]
  }
}
```

### 7.6 Budget · Screen 9 · **Dev A** · P0

**GET `/trips/{trip_id}/budget/`** — chart-ready. Labels and percentages are
precomputed; the frontend should not be dividing to draw a pie.

```json
{
  "success": true, "message": null,
  "data": {
    "currency": "INR",
    "total_budget": "50000.00",
    "grand_total": "48200.00",
    "remaining": "1800.00",
    "is_over_budget": false,
    "avg_cost_per_day": "4820.00",
    "breakdown": [
      { "category": "TRANSPORT", "label": "Transport",  "amount": "12000.00", "percentage": 24.9 },
      { "category": "STAY",      "label": "Stay",       "amount": "14000.00", "percentage": 29.0 },
      { "category": "ACTIVITY",  "label": "Activities", "amount": "17400.00", "percentage": 36.1 },
      { "category": "MEALS",     "label": "Meals",      "amount": "4800.00",  "percentage": 10.0 }
    ],
    "by_stop": [
      { "stop_id": 89, "title": "Bir", "budget": "18000.00",
        "spent": "17600.00", "is_over_budget": false }
    ],
    "by_day": [
      { "date": "2026-08-18", "amount": "6200.00", "is_over_budget": true }
    ],
    "alerts": [
      { "type": "OVERBUDGET_DAY", "date": "2026-08-18",
        "message": "2026-08-18 exceeds the average daily budget by 28%." }
    ]
  }
}
```

`total_budget`, `remaining` and `is_over_budget` are `null`/`false` when the user
never set a budget.

### 7.7 Expenses · **Dev A** · P0

| Method | Path | Purpose |
|---|---|---|
| GET | `/trips/{trip_id}/expenses/` | paginated. `?category=`, `?trip_stop=`, `?is_estimated=`, `?ordering=` |
| POST | `/trips/{trip_id}/expenses/` | `category`*, `title`*, `amount`*, `trip_stop`, `incurred_on`, `is_estimated`, `notes` |
| GET | `/trips/{trip_id}/expenses/{id}/` | detail |
| PATCH | `/trips/{trip_id}/expenses/{id}/` | edit |
| DELETE | `/trips/{trip_id}/expenses/{id}/` | remove |

### 7.8 Sharing · Screen 11 · **Dev A** · P0

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/trips/{id}/share/` | ✅ | set `is_public=True`, return share URL |
| DELETE | `/trips/{id}/share/` | ✅ | revoke |
| POST | `/trips/{id}/share/regenerate/` | ✅ | new `share_token`, kills old links |
| GET | `/public/trips/{share_token}/` | — | read-only public itinerary |
| POST | `/public/trips/{share_token}/copy/` | ✅ | **Copy Trip** into my account |

**POST `/trips/{id}/share/`**
```json
{ "success": true, "message": "Trip is now public.",
  "data": { "is_public": true,
            "share_token": "9f1c8ab2-4d21-4a77-9f3e-2b7c5d1a9e4f",
            "share_url": "http://localhost:3000/trips/shared/9f1c8ab2-4d21-4a77-9f3e-2b7c5d1a9e4f",
            "views_count": 0 } }
```

**GET `/public/trips/{share_token}/`** — `AllowAny`. `404` when the trip is not
public or is soft-deleted. Increments `views_count`.

Payload is the itinerary shape with two differences: `owner` is reduced to
`{first_name, avatar}`, and `total_budget` / `remaining` are **omitted entirely**.
No PII, no financial targets.

**POST `/public/trips/{share_token}/copy/`** — `start_date` (optional, rebase),
`name` (optional override)

Deep-copies trip → stops → trip activities → expenses into the caller's account.
Sets `copied_from`, resets `is_public=False` and `status=DRAFT`, generates a fresh
`share_token`, and shifts every date so day 1 lands on `start_date` when supplied
(decision D9).

---

## 8. Community — `/community/` · mockup Screen 10 · **Dev B · P2**

| Method | Path | Purpose |
|---|---|---|
| GET | `/community/posts/` | cursor-paginated feed. `?search=`, `?city=`, `?activity_type=`, `?user=`, `?trip=`, `?ordering=-created_at\|-likes_count` |
| POST | `/community/posts/` | `title`*, `body`*, `trip`, `city`, `activity`, `cover_image` |
| GET | `/community/posts/{id}/` | detail |
| PATCH | `/community/posts/{id}/` | author only |
| DELETE | `/community/posts/{id}/` | author only |
| POST | `/community/posts/{id}/like/` | like |
| DELETE | `/community/posts/{id}/like/` | unlike |
| GET | `/community/posts/{id}/comments/` | paginated, nested replies |
| POST | `/community/posts/{id}/comments/` | `body`*, `parent` |
| DELETE | `/community/comments/{id}/` | author only |

```json
{
  "success": true, "message": null,
  "data": {
    "results": [
      { "id": 220, "title": "Bir Billing was unreal",
        "body": "Flew at sunrise, cheapest adventure of the trip...",
        "cover_image": "http://.../posts/220.jpg",
        "author": { "id": 7, "first_name": "Riya", "avatar": "http://.../7.jpg" },
        "city": { "id": 61, "name": "Bir", "country_name": "India" },
        "trip": { "id": 31, "name": "Himachal Winter", "share_url": "http://..." },
        "likes_count": 34, "comments_count": 6, "is_liked_by_me": false,
        "created_at": "2026-08-20T06:15:00Z" }
    ],
    "pagination": { "page_size": 20,
                    "next": "http://localhost:8000/api/v1/community/posts/?cursor=cD0yMDI2LTA4",
                    "previous": null }
  }
}
```

---

## 9. Admin API — `/api/v1/admin/` · Screen 13 · P1

Every route is gated by `core.permissions.IsAdminRole` (`is_staff` **or**
`role == "ADMIN"`). Separate `urls_admin.py` + separate serializers per app, so a
user endpoint can never inherit admin field exposure. Non-admin → `403`.

### 9.1 User management · **Dev B**

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/users/` | `?search=`, `?is_active=`, `?role=`, `?country=`, `?created_after=`, `?ordering=` |
| GET | `/admin/users/{id}/` | detail + counts |
| PATCH | `/admin/users/{id}/` | `is_active`, `role`, `is_staff` |
| DELETE | `/admin/users/{id}/` | soft delete |
| POST | `/admin/users/{id}/restore/` | undo |
| GET | `/admin/users/{id}/trips/` | that user's trips |

```json
{
  "success": true, "message": null,
  "data": {
    "results": [
      { "id": 7, "email": "riya@example.com", "full_name": "Riya Sharma",
        "role": "USER", "is_active": true, "is_email_verified": false,
        "city_name": "Ahmedabad", "country_name": "India",
        "trips_count": 9, "posts_count": 3,
        "last_login": "2026-08-21T18:02:00Z",
        "created_at": "2026-08-01T09:12:00Z" }
    ],
    "pagination": { "count": 1240, "page": 1, "pages": 62, "page_size": 20,
                    "has_next": true, "has_previous": false,
                    "next": "http://localhost:8000/api/v1/admin/users/?page=2",
                    "previous": null }
  }
}
```

### 9.2 Trip moderation · **Dev B**

| Path | Methods |
|---|---|
| `/admin/trips/` | GET — `?user=`, `?status=`, `?is_public=`, `?created_after=` |
| `/admin/trips/{id}/` | GET, DELETE |

### 9.3 Master-data CRUD · **Dev B**

Reads already exist on the user API; the admin tree adds writes.

| Path | Methods |
|---|---|
| `/admin/countries/`, `/admin/countries/{id}/` | GET POST PATCH DELETE |
| `/admin/cities/`, `/admin/cities/{id}/` | GET POST PATCH DELETE |
| `/admin/activity-categories/`, `/{id}/` | GET POST PATCH DELETE |
| `/admin/activities/`, `/admin/activities/{id}/` | GET POST PATCH DELETE |
| `/admin/posts/`, `/admin/posts/{id}/` | GET, PATCH (`is_flagged`, `is_published`), DELETE |

### 9.4 Analytics · **Dev B**

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/analytics/overview/` | KPI tiles |
| GET | `/admin/analytics/popular-cities/` | `?limit=10&period=30d` |
| GET | `/admin/analytics/popular-activities/` | `?limit=10&period=30d` |
| GET | `/admin/analytics/user-growth/` | `?period=30d&interval=day` |
| GET | `/admin/analytics/trip-trends/` | trips created over time + avg budget |
| GET | `/admin/analytics/engagement/` | from `ActivityLog` |

`period` ∈ `7d`, `30d`, `90d`, `all`. **Not paginated** — bounded top-N / fixed windows.

**GET `/admin/analytics/overview/`**
```json
{
  "success": true, "message": null,
  "data": {
    "users":  { "total": 1240, "active": 1198, "new_this_period": 86, "growth_pct": 7.4 },
    "trips":  { "total": 3410, "created_this_period": 214, "public": 512,
                "avg_stops_per_trip": 3.2 },
    "budget": { "avg_trip_budget": "51200.00", "currency": "INR",
                "total_planned_value": "174592000.00" },
    "content":{ "posts": 640, "comments": 2180 },
    "period": "30d"
  }
}
```

**GET `/admin/analytics/popular-cities/`**
```json
{
  "success": true, "message": null,
  "data": {
    "period": "30d",
    "results": [
      { "city_id": 88, "city_name": "Paris", "country_name": "France",
        "trip_count": 214, "unique_users": 189, "avg_stay_days": 4.1,
        "share_pct": 12.4 }
    ]
  }
}
```

**GET `/admin/analytics/user-growth/`** — zero-filled for gap days so the chart has
no holes.
```json
{
  "success": true, "message": null,
  "data": {
    "period": "30d", "interval": "day",
    "series": [
      { "date": "2026-07-24", "new_users": 3, "cumulative": 1154 },
      { "date": "2026-07-25", "new_users": 0, "cumulative": 1154 }
    ],
    "totals": { "new_users": 86, "growth_pct": 7.4 }
  }
}
```

---

## 10. Route count

| Module | Routes | Owner | Priority |
|---|---|---|---|
| Auth | 7 | **A** | P0 |
| Profile | 8 | **A** | P0 |
| Trips — CRUD, stops, trip activities, itinerary, calendar, share/copy | 22 | **A** | P0 |
| Budget + expenses | 6 | **A** | P0 |
| Geo | 4 + 3 | **B** | P0 |
| Activities catalog | 4 | **B** | P0 |
| Dashboard | 1 | **B** | P0 |
| Community | 10 | **B** | P2 |
| Admin — users + trips | 8 | **B** | P1 |
| Admin — master data | 15 | **B** | P1 |
| Admin — analytics | 6 | **B** | P1 |
| **Total** | **~94** | | |

**Dev A ships ~43 routes** (all P0 — Screens 1, 3, 4, 5, 6, 9, 10, 11, 12).
**Dev B ships ~51** (Screens 2, 7, 8, 13, Community; 29 of them admin-only P1).
P0 across both is ~52 routes.

---

## 11. Frontend integration notes

1. **Every list is paginated.** `data.results` + `data.pagination`. Always.
2. **Enums are uppercase strings.** `"ONGOING"`, `"ADVENTURE"`, `"TRANSPORT"`.
   Render your own labels; don't string-match on display text.
3. **Money is a decimal string**, not a number — `"48200.00"`. Parse deliberately;
   don't let JS float arithmetic near it.
4. **Dates are naive `YYYY-MM-DD`.** No timezone on trip/stop/activity dates. Only
   `created_at`/`updated_at` carry `Z`.
5. **`401` → refresh once, then log out.** `POST /auth/token/refresh/` with the
   refresh token. Tokens rotate: store the new refresh token from the response.
6. **Empty days are returned, not omitted**, in both itinerary and calendar.
7. **Chart endpoints are pre-aggregated.** `percentage` and `share_pct` are already
   computed; series are zero-filled.
