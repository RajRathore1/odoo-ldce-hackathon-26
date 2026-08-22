# API Reference — implemented surface

Generated from the code, not from the plan. Every endpoint below is a live route
in the resolver as of branch `abhishekRajput_backend`; every field list is read
off the serializer that actually shapes the response.

Sections follow the folder layout under [apps/](../apps/), so the doc and the
codebase are navigated the same way. For the *planned* surface (including
endpoints not written yet) see [docs/API.md](API.md).

| Doc | Scope |
|---|---|
| `API.md` | the contract — everything the frontend was promised |
| **`API_REFERENCE.md`** | ← you are here. Only what exists and runs. |

---

## Contents

1. [Conventions](#1-conventions)
2. [Route index](#2-route-index)
3. [`apps/accounts`](#3-appsaccounts) — auth + own profile
4. [`apps/geo`](#4-appsgeo) — countries, cities, saved destinations
5. [`apps/activities`](#5-appsactivities) — activity catalog
6. [`apps/trips`](#6-appstrips) — trips, stops, trip activities, itinerary
7. [`apps/budget`](#7-appsbudget) — expenses, cost breakdown
8. [Not implemented yet](#8-not-implemented-yet)

---

## 1. Conventions

### Base URL

```
http://localhost:8000/api/v1/
```

Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`, raw schema at `/api/schema/`.

### Authentication

JWT bearer, from [`config/settings/base.py`](../config/settings/base.py):

```http
Authorization: Bearer <access>
```

- access token life **60 min**, refresh **7 days** (`.env` overridable)
- `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` are on — a refresh call
  returns a **new refresh token and kills the old one**. The client must store it.
- DRF's global default is `IsAuthenticated`
  ([`config/settings/base.py`](../config/settings/base.py)), so **every endpoint
  needs a token unless the table says `AllowAny`**. That includes `/cities/` and
  `/activities/` — they are not public in the current code.

### Response envelope

Applied by [`core/renderers.py`](../core/renderers.py) to every response. Views
never build it by hand.

```json
{ "success": true, "message": null, "data": { } }
```

```json
{ "success": false, "message": "End date must be on or after the start date.",
  "errors": { "fields": { "end_date": ["End date must be on or after the start date."] } } }
```

- field errors are nested under `errors.fields` so the client can bind them to inputs
- single-message errors (401/403/404/throttle) come back as `errors.detail`
- `204 No Content` returns an **empty body** — the renderer short-circuits on `None`

### Pagination

Every list is paginated ([`core/pagination.py`](../core/pagination.py)); rows at
`data.results`, meta at `data.pagination`.

```json
{ "success": true, "message": null, "data": {
    "results": [],
    "pagination": { "count": 137, "page": 2, "pages": 7, "page_size": 20,
                    "has_next": true, "has_previous": true,
                    "next": "http://localhost:8000/api/v1/cities/?page=3",
                    "previous": "http://localhost:8000/api/v1/cities/?page=1" } } }
```

| Class | Default | `?page_size=` max | Used by |
|---|---|---|---|
| `StandardPagination` | 20 | 100 | trips, expenses, stops, saved destinations, trip activities |
| `LargePagination` | 50 | 200 | `/countries/`, `/cities/`, `/activities/` |

Opted out (`pagination_class = None`, bounded aggregates): `/cities/popular/`,
`/activities/popular/`, `/activity-categories/`, `/trips/{id}/itinerary/`,
`/trips/{id}/budget/`.

### Shared query params

| Param | Applies to | Notes |
|---|---|---|
| `page`, `page_size` | every paginated list | |
| `search` | lists with `search_fields` | DRF `SearchFilter`, icontains-OR across the fields |
| `ordering` | lists with `ordering_fields` | `-` prefixes descending |

Comma-separated multi-value filters (`?status=DRAFT,PLANNED`) come from
[`core/filters.py`](../core/filters.py) `CharInFilter` / `NumberInFilter`.

### Types

| | |
|---|---|
| Money | JSON **string** — `"48200.00"`. `COERCE_DECIMAL_TO_STRING` is left on deliberately. |
| Date | `"2026-03-14"` |
| Time | `"09:30:00"` |
| Datetime | `"2026-08-22T11:04:03Z"` |
| Currency | 3-char ISO, uppercased on write |
| Images | URL relative to the host in dev — `"/media/users/avatars/x.jpg"`, `null` when unset |

No FX conversion anywhere: a trip has one currency and its children inherit it.

### Status codes

| Code | When |
|---|---|
| 200 | read, update, action |
| 201 | create |
| 204 | delete (soft) — empty body |
| 400 | validation, business rule |
| 401 | missing/expired/bad token, wrong login credentials |
| 403 | authenticated but not allowed (deactivated account, non-owner detail route) |
| 404 | not found **or** not yours — owner-scoped querysets 404 rather than 403 |
| 409 | state conflict (`ConflictError`) — e.g. re-saving a destination |

---

## 2. Route index

33 live routes. `/api/v1/admin/**` resolves but is **empty** — every
`urls_admin.py` is still `urlpatterns: list = []`.

### [`apps/accounts`](../apps/accounts/) — 10

| Method | Path | Auth |
|---|---|---|
| POST | `/auth/register/` | AllowAny |
| POST | `/auth/login/` | AllowAny |
| POST | `/auth/token/refresh/` | AllowAny |
| POST | `/auth/logout/` | Bearer |
| POST | `/auth/password/forgot/` | AllowAny |
| POST | `/auth/password/reset/` | AllowAny |
| POST | `/auth/password/change/` | Bearer |
| GET · PATCH · DELETE | `/users/me/` | Bearer |
| POST | `/users/me/avatar/` | Bearer |
| GET | `/users/me/stats/` | Bearer |

### [`apps/geo`](../apps/geo/) — 6

| Method | Path |
|---|---|
| GET | `/countries/` |
| GET | `/cities/` |
| GET | `/cities/popular/` |
| GET | `/cities/{id}/` |
| GET · POST | `/users/me/saved-destinations/` |
| DELETE | `/users/me/saved-destinations/{id}/` |

### [`apps/activities`](../apps/activities/) — 4

| Method | Path |
|---|---|
| GET | `/activity-categories/` |
| GET | `/activities/` |
| GET | `/activities/popular/` |
| GET | `/activities/{id}/` |

### [`apps/trips`](../apps/trips/) — 10

| Method | Path |
|---|---|
| GET · POST | `/trips/` |
| GET · PUT · PATCH · DELETE | `/trips/{id}/` |
| POST | `/trips/{id}/cover-photo/` |
| GET · POST | `/trips/{trip_id}/stops/` |
| POST | `/trips/{trip_id}/stops/reorder/` |
| GET · PUT · PATCH · DELETE | `/trips/{trip_id}/stops/{id}/` |
| GET · POST | `/trips/{trip_id}/stops/{stop_id}/activities/` |
| POST | `/trips/{trip_id}/activities/reorder/` |
| GET | `/trips/{trip_id}/itinerary/` |
| GET · PUT · PATCH · DELETE | `/trip-activities/{id}/` |

### [`apps/budget`](../apps/budget/) — 3

| Method | Path |
|---|---|
| GET · POST | `/trips/{trip_id}/expenses/` |
| GET · PUT · PATCH · DELETE | `/trips/{trip_id}/expenses/{id}/` |
| GET | `/trips/{trip_id}/budget/` |

---

## 3. `apps/accounts`

Code: [views.py](../apps/accounts/views.py) ·
[serializers.py](../apps/accounts/serializers.py) ·
[services.py](../apps/accounts/services.py) ·
[selectors.py](../apps/accounts/selectors.py) ·
[urls.py](../apps/accounts/urls.py) ·
[urls_me.py](../apps/accounts/urls_me.py)

### Shared read shape — `User`

`UserSerializer`. Returned by every auth endpoint (under `data.user`), by
`GET|PATCH /users/me/` and by the avatar upload.

```json
{
  "id": 4,
  "email": "riya@example.com",
  "first_name": "Riya",
  "last_name": "Sharma",
  "full_name": "Riya Sharma",
  "phone_number": "+91 98765 43210",
  "avatar": "/media/users/avatars/riya.jpg",
  "city": { "id": 12, "name": "Ahmedabad", "state": "Gujarat" },
  "country": { "id": 1, "name": "India", "iso2": "IN" },
  "additional_info": "Prefers mountains.",
  "language": "en",
  "currency": "INR",
  "role": "USER",
  "is_email_verified": false,
  "created_at": "2026-08-01T09:12:44Z"
}
```

Read-only: `id`, `email`, `role`, `is_email_verified`, `created_at`.
`city` / `country` are `null` when unset. `role` is one of `USER`, `ADMIN`.

---

### POST `/auth/register/` · `RegisterView` · AllowAny

**Payload**

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `email` | string | yes | lowercased; uniqueness checked case-insensitively against `all_objects`, so a soft-deleted account still owns its address |
| `password` | string | yes | run through Django's `AUTH_PASSWORD_VALIDATORS` |
| `confirm_password` | string | yes | must equal `password` |
| `first_name` | string | yes | non-blank |
| `last_name` | string | no | |
| `phone_number` | string | no | |
| `city` | int (City id) | no | |
| `country` | int (Country id) | no | |
| `additional_info` | string | no | |

```json
{
  "email": "riya@example.com",
  "password": "Str0ng!pass",
  "confirm_password": "Str0ng!pass",
  "first_name": "Riya",
  "last_name": "Sharma",
  "phone_number": "+91 98765 43210",
  "city": 12,
  "country": 1,
  "additional_info": ""
}
```

**201**

```json
{ "success": true, "message": "Account created successfully.",
  "data": { "user": { "...": "User shape above" },
            "tokens": { "access": "eyJ...", "refresh": "eyJ..." } } }
```

**400** — duplicate email, mismatched confirmation, weak password:

```json
{ "success": false, "message": "An account with this email already exists.",
  "errors": { "fields": { "email": ["An account with this email already exists."] } } }
```

---

### POST `/auth/login/` · `LoginView` · AllowAny

**Payload** — `{"email": "riya@example.com", "password": "Str0ng!pass"}`

**200** — identical `data` shape to register, so the client has one "you are
signed in" code path.

```json
{ "success": true, "message": "Signed in successfully.",
  "data": { "user": { "...": "User" },
            "tokens": { "access": "eyJ...", "refresh": "eyJ..." } } }
```

| Failure | Code | Message |
|---|---|---|
| unknown email **or** wrong password | 401 | `Incorrect email or password.` — one message on purpose, so this is not an account-enumeration oracle |
| correct password, `is_active=False` | 403 | `This account has been deactivated. Contact an administrator.` |

---

### POST `/auth/token/refresh/` · `TokenRefreshView` · AllowAny

SimpleJWT's view, re-exported. **Payload** `{"refresh": "eyJ..."}`.

**200** — both tokens, because rotation is on and the old refresh is now
blacklisted. Store the new refresh or the next call fails.

```json
{ "success": true, "message": null,
  "data": { "access": "eyJ...", "refresh": "eyJ...NEW" } }
```

**401** `Token is invalid or expired.`

---

### POST `/auth/logout/` · `LogoutView` · Bearer

**Payload** `{"refresh": "eyJ..."}`. Blacklists it. **Idempotent** — an
already-spent token is still a 200.

**200** `{"success": true, "message": "Signed out successfully.", "data": null}`

---

### POST `/auth/password/forgot/` · `PasswordForgotView` · AllowAny

**Payload** `{"email": "riya@example.com"}`

**200, always** — whether or not the address exists. A 404 here would leak which
emails have accounts. In dev the token is printed to the console.

```json
{ "success": true, "message": "If that email exists, a reset link has been sent.", "data": null }
```

---

### POST `/auth/password/reset/` · `PasswordResetView` · AllowAny

**Payload**

| Field | Type | Req |
|---|---|:--:|
| `token` | string | yes |
| `password` | string | yes |
| `confirm_password` | string | yes |

Token validity (unknown / expired / already spent) is checked in `services`, not
the serializer — whether a token is spent is state, and the service is what marks
it used inside the transaction. Every outstanding refresh token for the user dies.

**200** `Password reset. You can now sign in.`
**400** on a bad, expired or reused token.

---

### POST `/auth/password/change/` · `PasswordChangeView` · Bearer

**Payload**

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `current_password` | string | yes | verified against the caller |
| `password` | string | yes | must differ from `current_password` |
| `confirm_password` | string | yes | |

**200** `Password changed. Please sign in again.` — **every session dies,
including the caller's own**. The client must sign in again.

---

### `/users/me/` · `MeView` · Bearer

#### GET

**200** — the `User` shape. `city` / `country` joined in a single query by
`selectors.user_with_relations`.

#### PATCH — partial update

| Field | Type |
|---|---|
| `first_name` | string |
| `last_name` | string |
| `phone_number` | string |
| `city` | int (City id) |
| `country` | int (Country id) |
| `additional_info` | string |
| `language` | string |
| `currency` | 3-char ISO, uppercased on save |

Absent on purpose: `email`, `role`, `is_active` (must not be self-service) and
`avatar` (has its own multipart endpoint).

**200** `{"success": true, "message": "Profile updated.", "data": { "...": "User" } }`

#### DELETE

**204**, empty body. Soft delete, and every session is killed.

---

### POST `/users/me/avatar/` · `AvatarView` · Bearer

`multipart/form-data`, single required field `avatar` (image).

```http
POST /api/v1/users/me/avatar/
Content-Type: multipart/form-data

avatar=@riya.jpg
```

**200** `{"success": true, "message": "Avatar updated.", "data": { "...": "User" } }`

---

### GET `/users/me/stats/` · `MeStatsView` · Bearer

Profile-header counters (Screen 12).

```json
{ "success": true, "message": null, "data": {
    "total_trips": 0, "ongoing": 0, "upcoming": 0, "completed": 0,
    "cities_visited": 0, "countries_visited": 0,
    "total_planned_spend": "0.00", "currency": "INR" } }
```

> **Known stub.** [`selectors.user_stats()`](../apps/accounts/selectors.py)
> returns literal zeros — the aggregation over `trips` was never wired up after
> the Trip model landed. The shape is final; only the numbers are fake.

---

## 4. `apps/geo`

Code: [views.py](../apps/geo/views.py) ·
[serializers.py](../apps/geo/serializers.py) ·
[filters.py](../apps/geo/filters.py) ·
[selectors.py](../apps/geo/selectors.py) ·
[services.py](../apps/geo/services.py) ·
[urls.py](../apps/geo/urls.py)

Read-only except saved destinations. Every route needs a Bearer token (no view
here opts out of the global default).

### GET `/countries/` · `CountryListView`

`LargePagination` — roughly 30 rows, so a dropdown fills in one request.

| Query | Type | Notes |
|---|---|---|
| `region` | string | case-insensitive exact |
| `is_active` | bool | |
| `search` | string | `name`, `iso2`, `iso3` |
| `ordering` | `name` / `region` | default `name` |

**200**

```json
{ "success": true, "message": null, "data": {
  "results": [
    { "id": 1, "name": "India", "iso2": "IN", "iso3": "IND",
      "region": "Asia", "currency_code": "INR", "flag_emoji": "🇮🇳" }
  ],
  "pagination": { "count": 30, "page": 1, "pages": 1, "page_size": 50,
                  "has_next": false, "has_previous": false,
                  "next": null, "previous": null } } }
```

---

### GET `/cities/` · `CityListView`

City Search (Screen 7). `LargePagination`.

| Query | Type | Notes |
|---|---|---|
| `country` | int | |
| `region` | string | lives on the country — one join, one filter |
| `min_cost_index` / `max_cost_index` | number | |
| `is_active` | bool | |
| `search` | string | `name`, `state`, `country__name` |
| `ordering` | `popularity_score` / `name` / `cost_index` / `avg_daily_cost` | default `-popularity_score,name` |

**200** — one `results` row:

```json
{
  "id": 12,
  "name": "Manali",
  "state": "Himachal Pradesh",
  "country": { "id": 1, "name": "India", "iso2": "IN", "flag_emoji": "🇮🇳" },
  "region": "Asia",
  "cost_index": "62.50",
  "avg_daily_cost": "2400.00",
  "currency": "INR",
  "popularity_score": 880,
  "image_url": "https://cdn.example.com/manali.jpg",
  "activities_count": 24,
  "is_saved": true
}
```

`activities_count` and `is_saved` are **queryset annotations** from
`selectors.city_list(user)`, never per-row queries. `is_saved` is scoped to the
caller, so the frontend draws the bookmark without a second call.

---

### GET `/cities/popular/` · `PopularCityListView`

Bounded top-N. **Not paginated** — `data` is a bare array of the row shape above.

| Query | Type | Default | Max |
|---|---|---|---|
| `limit` | int | 10 | 50 — silently clamped; a non-numeric value falls back to the default |

```json
{ "success": true, "message": null,
  "data": [ { "id": 12, "name": "Manali", "...": "same fields as /cities/" } ] }
```

Ordering is fixed at `-popularity_score, name` over `is_active=True`. No
`search`, `ordering` or filters — the filter backends are switched off on this view.

---

### GET `/cities/{id}/` · `CityDetailView`

The list row **plus** the map fields and the top 10 activities.

```json
{ "success": true, "message": null, "data": {
  "id": 12, "name": "Manali", "state": "Himachal Pradesh",
  "country": { "id": 1, "name": "India", "iso2": "IN", "flag_emoji": "🇮🇳" },
  "region": "Asia", "cost_index": "62.50", "avg_daily_cost": "2400.00",
  "currency": "INR", "popularity_score": 880,
  "image_url": "https://cdn.example.com/manali.jpg",
  "activities_count": 24, "is_saved": true,
  "description": "Hill station on the Beas.",
  "latitude": "32.239600", "longitude": "77.188700", "timezone": "Asia/Kolkata",
  "top_activities": [
    { "id": 501, "name": "Solang Valley paragliding", "activity_type": "ADVENTURE",
      "cost": "2500.00", "currency": "INR", "duration_minutes": 90,
      "rating": "4.6", "image_url": "https://cdn.example.com/solang.jpg" }
  ] } }
```

`top_activities` is capped at 10 by `selectors.city_top_activities`.
**404** for an id that does not exist.

---

### `/users/me/saved-destinations/` · `SavedDestinationListCreateView`

Owned by `geo` rather than `accounts`, because City Search annotates `is_saved`
off this model and `geo` may not import `accounts`. `StandardPagination`.

#### GET

**200**

```json
{ "success": true, "message": null, "data": {
  "results": [
    { "id": 7,
      "city": { "id": 12, "name": "Manali", "state": "Himachal Pradesh",
                "country_name": "India",
                "image_url": "https://cdn.example.com/manali.jpg" },
      "note": "Go in October.",
      "created_at": "2026-08-10T06:31:02Z" }
  ],
  "pagination": { "count": 1, "page": 1, "pages": 1, "page_size": 20,
                  "has_next": false, "has_previous": false,
                  "next": null, "previous": null } } }
```

#### POST

| Field | Type | Req |
|---|---|:--:|
| `city` | int (City id) | yes |
| `note` | string, max 255 | no |

```json
{ "city": 12, "note": "Go in October." }
```

**201** `{"success": true, "message": "Destination saved.", "data": { "...": "row above" } }`

**409** — the same city twice:

```json
{ "success": false, "message": "You have already saved this destination.",
  "errors": { "detail": "You have already saved this destination." } }
```

---

### DELETE `/users/me/saved-destinations/{id}/` · `SavedDestinationDestroyView`

Owner-scoped queryset, so somebody else's id is a **404**, not a 403.

**204**, empty body.

---

## 5. `apps/activities`

Code: [views.py](../apps/activities/views.py) ·
[serializers.py](../apps/activities/serializers.py) ·
[filters.py](../apps/activities/filters.py) ·
[selectors.py](../apps/activities/selectors.py) ·
[urls.py](../apps/activities/urls.py)

Read-only catalog. Bearer token required on all four routes.

### `activity_type` values

From [constants.py](../apps/activities/constants.py):

`SIGHTSEEING` · `FOOD` · `ADVENTURE` · `CULTURE` · `NIGHTLIFE` · `SHOPPING` ·
`NATURE` · `RELAX` · `TRANSPORT` · `OTHER`

---

### GET `/activity-categories/` · `ActivityCategoryListView`

Screen 8's filter chips. **Not paginated**, no filters — a small fixed set
rendered all at once.

```json
{ "success": true, "message": null, "data": [
  { "id": 3, "name": "Adventure", "slug": "adventure",
    "icon": "mountain", "description": "Trekking, rafting, paragliding." } ] }
```

---

### GET `/activities/` · `ActivityListView`

Activity Search (Screen 8). `LargePagination`.

| Query | Type | Notes |
|---|---|---|
| `city` | int | |
| `country` | int list | comma-separated — `?country=1,2` |
| `category` | int list | comma-separated |
| `activity_type` | string list | comma-separated, e.g. `?activity_type=FOOD,ADVENTURE` |
| `min_cost` / `max_cost` | number | |
| `min_duration` / `max_duration` | number | minutes |
| `is_active` | bool | |
| `search` | string | `name`, `description` |
| `ordering` | `popularity_score` / `cost` / `duration_minutes` / `rating` / `name` | default `-popularity_score,name` |

**200** — one `results` row (also the body of `/activities/{id}/`):

```json
{
  "id": 501,
  "name": "Solang Valley paragliding",
  "description": "Tandem flight with a certified pilot.",
  "activity_type": "ADVENTURE",
  "category": { "id": 3, "name": "Adventure", "slug": "adventure", "icon": "mountain" },
  "city": { "id": 12, "name": "Manali", "state": "Himachal Pradesh",
            "country_name": "India", "image_url": "https://cdn.example.com/manali.jpg" },
  "cost": "2500.00",
  "currency": "INR",
  "duration_minutes": 90,
  "rating": "4.6",
  "popularity_score": 640,
  "image_url": "https://cdn.example.com/solang.jpg"
}
```

---

### GET `/activities/popular/` · `PopularActivityListView`

Bounded top-N. **Not paginated** — `data` is a bare array of the row shape above.

| Query | Type | Default | Max |
|---|---|---|---|
| `city` | int | — | restrict to one city |
| `limit` | int | 10 | 50, clamped |

---

### GET `/activities/{id}/` · `ActivityDetailView`

**200** — the row shape above, unwrapped: `data` is the object itself.
**404** for an unknown id.

---

## 6. `apps/trips`

Code: [views.py](../apps/trips/views.py) ·
[serializers.py](../apps/trips/serializers.py) ·
[filters.py](../apps/trips/filters.py) ·
[selectors.py](../apps/trips/selectors.py) ·
[services.py](../apps/trips/services.py) ·
[urls.py](../apps/trips/urls.py)

Everything here is **owner-scoped at the queryset**, not by permission class:
another user's trip id is a **404**, never a 403. `IsTripOwner` stays on detail
routes as a second line of defence. Nested routes resolve `trip_id` (and
`stop_id`) through `TripScopedMixin` / `StopScopedMixin`, so ownership is
checked once.

### `status` values

From [constants.py](../apps/trips/constants.py):

| Value | UI label | Set by |
|---|---|---|
| `DRAFT` | Draft | the user, explicitly |
| `PLANNED` | Upcoming | derived from dates in `Trip.save()` |
| `ONGOING` | Ongoing | derived |
| `COMPLETED` | Completed | derived |
| `CANCELLED` | Cancelled | the user, explicitly |

Only `DRAFT` and `CANCELLED` are honoured on write. The other three are
recomputed from the dates on every save, so sending them is **silently ignored
rather than rejected**.

---

### Shared read shapes

#### `TripActivity` — `TripActivitySerializer`

```json
{
  "id": 3312,
  "trip_stop": 91,
  "title": "Solang Valley paragliding",
  "activity_id": 501,
  "activity_type": "ADVENTURE",
  "day_date": "2026-03-16",
  "start_time": "09:30:00",
  "end_time": "11:00:00",
  "duration_minutes": 90,
  "cost": "2500.00",
  "currency": "INR",
  "order": 1,
  "notes": "Carry a windbreaker."
}
```

`title` / `activity_type` come off model properties: the catalog row when
`activity_id` is set, the user's own wording for a custom entry. For a custom
entry `activity_id` is `null` and `activity_type` is `null`.

`cost` is a **snapshot** taken when the activity was added — editing the catalog
later never rewrites a saved budget.

#### `TripStop` — `TripStopSerializer`

```json
{
  "id": 91,
  "title": "Manali",
  "city": { "id": 12, "name": "Manali", "state": "Himachal Pradesh",
            "country_name": "India", "image_url": "https://cdn.example.com/manali.jpg" },
  "start_date": "2026-03-15",
  "end_date": "2026-03-18",
  "nights": 3,
  "order": 1,
  "budget": "18000.00",
  "activities_count": 4,
  "notes": ""
}
```

`title` falls back to the city name when the stop has no explicit title.
Nested inside `GET /trips/{id}/` this shape gains an `activities` array.

---

### GET `/trips/` · `TripViewSet.list`

My Trips (Screen 6). `StandardPagination`.

| Query | Type | Notes |
|---|---|---|
| `status` | string list | comma-separated — `?status=PLANNED,DRAFT` |
| `is_public` | bool | |
| `start_date_after` / `start_date_before` | date | |
| `city` | int list | trips containing this city; excludes soft-deleted stops |
| `country` | int list | same, via the city's country |
| `search` | string | `name`, `description` |
| `ordering` | `created_at` / `start_date` / `name` | default `-created_at` |

**200** — one `results` row (`TripListSerializer`):

```json
{
  "id": 55,
  "name": "Himachal in spring",
  "description": "Bir, Manali, Kasol.",
  "start_date": "2026-03-14",
  "end_date": "2026-03-24",
  "duration_days": 11,
  "status": "PLANNED",
  "cover_photo": "/media/trips/covers/himachal.jpg",
  "stops_count": 3,
  "activities_count": 9,
  "cities": ["Bir", "Manali", "Kasol"],
  "total_budget": "60000.00",
  "estimated_cost": "48200.00",
  "currency": "INR",
  "is_over_budget": false,
  "is_public": false,
  "share_url": "http://localhost:5173/trips/shared/8f2c9d64-1a3e-4b77-9c50-2f6b1d0e77aa",
  "created_at": "2026-08-02T10:22:31Z"
}
```

`share_token` is deliberately **not** on the list shape — a page of tokens is a
page of live share links, and nothing on Screen 6 needs them. `estimated_cost`
and `is_over_budget` come from one bulk cost lookup for the whole page, passed
into the serializer as context.

`share_url` points at the **frontend** (`FRONTEND_BASE_URL` + `/trips/shared/{token}`),
not at this API, and is populated whether or not the trip is public. `cities` is
the city names in stop order — the "Bir · Manali · Kasol" line on a card.
`duration_days` counts both ends: the 14th to the 24th is 11 days. Stop `nights`
is the one range in the project **not** counted inclusively — the 15th to the
18th is 3 nights, because that is what a hotel booking means.

---

### POST `/trips/` · `TripViewSet.create`

**Payload** — `TripWriteSerializer`

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `name` | string, max 150 | yes | |
| `description` | string | no | |
| `start_date` | date | yes | a past date is allowed — users log trips they already took |
| `end_date` | date | yes | must be on or after `start_date` |
| `status` | `DRAFT` / `CANCELLED` | no | anything else is overwritten from the dates |
| `total_budget` | decimal | no | nullable |
| `currency` | 3-char ISO | no | uppercased; default `INR` |
| `cover_photo` | image | no | prefer the dedicated multipart endpoint |

Not writable here: `is_public` (sharing has its own endpoints — not implemented
yet), `share_token`, `views_count`, `copied_from`.

```json
{
  "name": "Himachal in spring",
  "description": "Bir, Manali, Kasol.",
  "start_date": "2026-03-14",
  "end_date": "2026-03-24",
  "status": "DRAFT",
  "total_budget": "60000.00",
  "currency": "INR"
}
```

**201** — the **detail** shape, message `Trip created successfully.`

---

### GET `/trips/{id}/` · `TripViewSet.retrieve`

`TripDetailSerializer` — every list field **plus**:

```json
{ "success": true, "message": null, "data": {
  "id": 55, "name": "Himachal in spring", "...": "all TripListSerializer fields",
  "share_token": "8f2c9d64-1a3e-4b77-9c50-2f6b1d0e77aa",
  "views_count": 0,
  "copied_from": null,
  "updated_at": "2026-08-20T14:03:19Z",
  "stops": [
    { "id": 91, "title": "Manali",
      "city": { "id": 12, "name": "Manali", "state": "Himachal Pradesh",
                "country_name": "India", "image_url": "https://cdn.example.com/manali.jpg" },
      "start_date": "2026-03-15", "end_date": "2026-03-18",
      "nights": 3, "order": 1, "budget": "18000.00",
      "activities_count": 1, "notes": "",
      "activities": [ { "id": 3312, "trip_stop": 91,
                        "title": "Solang Valley paragliding", "activity_id": 501,
                        "activity_type": "ADVENTURE", "day_date": "2026-03-16",
                        "start_time": "09:30:00", "end_time": "11:00:00",
                        "duration_minutes": 90, "cost": "2500.00",
                        "currency": "INR", "order": 1, "notes": "" } ] }
  ] } }
```

---

### PUT · PATCH `/trips/{id}/` · `TripViewSet.update`

Same payload as create; `PATCH` is partial. Both validate against the merged
instance, so moving only one of the two dates is still checked.

**Extra rule** — a date change that would strand a stop outside its own trip is
rejected, because the itinerary only emits dates inside the trip range and those
days would silently vanish from the screen:

```json
{ "success": false,
  "message": "These stops would fall outside the new dates: Manali, Kasol. Move or remove them first.",
  "errors": { "fields": { "start_date": ["These stops would fall outside the new dates: Manali, Kasol. Move or remove them first."] } } }
```

**200** — the detail shape, message `Trip updated.`

---

### DELETE `/trips/{id}/` · `TripViewSet.destroy`

Soft delete. **204**, empty body.

---

### POST `/trips/{id}/cover-photo/` · `TripViewSet.cover_photo`

`multipart/form-data`, single required field `cover_photo` (image).

**200** — the full detail shape, message `Cover photo updated.`

---

### `/trips/{trip_id}/stops/` · `TripStopListCreateView`

#### GET

**200** — paginated `TripStopSerializer` rows, ordered by `order`, with the city
and its country joined.

#### POST — `TripStopWriteSerializer`

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `city` | int (City id) | no | nullable — a stop can be a place with no catalog city |
| `title` | string, max 120 | no | falls back to the city name on read |
| `start_date` | date | yes | must sit inside the trip's range |
| `end_date` | date | yes | on or after `start_date`, inside the trip's range |
| `budget` | decimal | no | nullable |
| `notes` | string | no | |

`order` is **not accepted** — it is assigned server-side on create and changed
only through the reorder endpoint, which is the one place that can keep the whole
sequence consistent in a single statement.

```json
{ "city": 12, "title": "", "start_date": "2026-03-15",
  "end_date": "2026-03-18", "budget": "18000.00", "notes": "" }
```

**201** `{"success": true, "message": "Stop added.", "data": { "...": "TripStop" } }`

**400** — outside the trip:

```json
{ "success": false,
  "message": "A stop must sit inside the trip's dates (2026-03-14 to 2026-03-24).",
  "errors": { "fields": { "start_date": ["A stop must sit inside the trip's dates (2026-03-14 to 2026-03-24)."] } } }
```

---

### GET · PUT · PATCH · DELETE `/trips/{trip_id}/stops/{id}/` · `TripStopDetailView`

Same write payload as POST, same date rules. `PATCH` is partial.

- **200** on update, message `Stop updated.`
- **204** on delete (soft), empty body

---

### POST `/trips/{trip_id}/stops/reorder/` · `TripStopReorderView`

Drag-to-reorder. One `bulk_update` inside a transaction — there is deliberately
no `UniqueConstraint(trip, order)`, because SQLite has no deferred constraints
and a reorder would violate it mid-update.

**Payload**

```json
{ "items": [ { "id": 91, "order": 1 },
             { "id": 92, "order": 2 },
             { "id": 93, "order": 3 } ] }
```

| Field | Type | Notes |
|---|---|---|
| `items` | array | non-empty |
| `items[].id` | int | must belong to this trip |
| `items[].order` | int | minimum 1 |

**200** — the **whole reordered list**, re-read through the selector so the city
rows are joined rather than lazy-loaded:

```json
{ "success": true, "message": "Stops reordered.",
  "data": [ { "id": 91, "order": 1, "...": "TripStop" } ] }
```

**400** — foreign ids:

```json
{ "success": false, "message": "These stops do not belong to this trip: [404].",
  "errors": { "fields": { "items": ["These stops do not belong to this trip: [404]."] } } }
```

---

### `/trips/{trip_id}/stops/{stop_id}/activities/` · `TripActivityListCreateView`

#### GET

**200** — paginated `TripActivity` rows for that stop.

#### POST — `TripActivityCreateSerializer`

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `activity` | int (catalog Activity id) | XOR | exactly one of `activity` / `custom_title` |
| `custom_title` | string, max 150 | XOR | free text for something not in the catalog |
| `day_date` | date | yes | must sit inside the **stop's** range |
| `start_time` | time | no | |
| `end_time` | time | no | must be after `start_time` when both are given |
| `cost` | decimal | no | omitted + `activity` given → snapshotted from the catalog row |
| `duration_minutes` | int | no | |
| `notes` | string | no | |

`currency` is **not accepted**: a trip has one currency and its children inherit
it. Taking the catalog row's currency would let one trip hold two, and the budget
sums children without converting.

```json
{ "activity": 501, "day_date": "2026-03-16",
  "start_time": "09:30:00", "end_time": "11:00:00", "notes": "" }
```

```json
{ "custom_title": "Coffee at Johnson's", "day_date": "2026-03-17",
  "cost": "450.00", "duration_minutes": 60 }
```

**201** `{"success": true, "message": "Activity added.", "data": { "...": "TripActivity" } }`

**400** — both or neither:

```json
{ "success": false,
  "message": "Provide either `activity` (a catalog id) or `custom_title`, not both and not neither.",
  "errors": { "fields": { "custom_title": ["Provide either `activity` (a catalog id) or `custom_title`, not both and not neither."] } } }
```

**400** — day outside the stop:

```json
{ "success": false,
  "message": "This day is outside the stop's dates (2026-03-15 to 2026-03-18).",
  "errors": { "fields": { "day_date": ["This day is outside the stop's dates (2026-03-15 to 2026-03-18)."] } } }
```

---

### GET · PUT · PATCH · DELETE `/trip-activities/{id}/` · `TripActivityDetailView`

**Flat on purpose**: calendar drag-and-drop moves an item between days *and*
stops, so a nested URL would encode a parent that is about to change. Ownership
resolves through `trip_stop__trip__user`.

#### PATCH — `TripActivityUpdateSerializer`

| Field | Type | Notes |
|---|---|---|
| `day_date` | date | must stay inside the current stop's range |
| `start_time` | time | |
| `end_time` | time | after `start_time` |
| `cost` | decimal | |
| `duration_minutes` | int | |
| `order` | int | |
| `notes` | string | |

`activity` and `custom_title` are deliberately absent — swapping one for the
other is a different activity, and allowing it here is how a row ends up with
both or neither and trips the database constraint. To move an activity to a
**different stop**, use the reorder endpoint.

**200** `{"success": true, "message": "Activity updated.", "data": { "...": "TripActivity" } }`
**204** on delete (soft), empty body.

---

### POST `/trips/{trip_id}/activities/reorder/` · `TripActivityReorderView`

Reorders **and** moves activities between days or stops, in one `bulk_update`.

**Payload**

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `items[].id` | int | yes | must belong to this trip |
| `items[].order` | int | yes | minimum 1 |
| `items[].day_date` | date | no | send only when the day changed |
| `items[].trip_stop` | int | no | send only when the stop changed; must belong to this trip |

Dragging inside one day sends neither optional field.

```json
{ "items": [
    { "id": 3312, "order": 2 },
    { "id": 3313, "order": 1, "day_date": "2026-03-17" },
    { "id": 3314, "order": 3, "day_date": "2026-03-20", "trip_stop": 92 } ] }
```

**200**

```json
{ "success": true, "message": "Activities reordered.",
  "data": [ { "id": 3313, "order": 1, "...": "TripActivity" } ] }
```

**400** cases, all under `errors.fields.items`:

- `These activities do not belong to this trip: [999].`
- `Stop 404 does not belong to this trip.`
- `Activity 3314 would land on 2026-03-30, outside stop 92 (2026-03-19 to 2026-03-22).`

---

### GET `/trips/{trip_id}/itinerary/` · `TripItineraryView`

Screen 10. **Not paginated** — a trip is a bounded object and the screen renders
all of it at once.

| Query | Values | Default |
|---|---|---|
| `view` | `day` / `stop` | `day` |

**Every date in the trip range is returned, including empty ones** — the
frontend renders placeholders and does not compute gaps. `stop` is `null` on a
day no stop covers. Where two stops overlap a date the **lower `order`** wins;
overlap is legal, since a travel day can belong to the stop you are leaving.

`days` is present for `?view=day` and `stops` for `?view=stop` — the other key is
**absent**, not null, so the client branches on the parameter it sent.

#### `?view=day` (default) — **200**

```json
{ "success": true, "message": null, "data": {
  "trip": { "id": 55, "name": "Himachal in spring",
            "start_date": "2026-03-14", "end_date": "2026-03-24",
            "duration_days": 11, "currency": "INR" },
  "days": [
    { "date": "2026-03-14", "day_number": 1, "stop": null,
      "activities": [], "day_total_cost": "0.00" },
    { "date": "2026-03-16", "day_number": 3,
      "stop": { "id": 91, "title": "Manali",
                "city": { "id": 12, "name": "Manali", "state": "Himachal Pradesh",
                          "country_name": "India",
                          "image_url": "https://cdn.example.com/manali.jpg" },
                "order": 1 },
      "activities": [ { "id": 3312, "trip_stop": 91,
                        "title": "Solang Valley paragliding", "activity_id": 501,
                        "activity_type": "ADVENTURE", "day_date": "2026-03-16",
                        "start_time": "09:30:00", "end_time": "11:00:00",
                        "duration_minutes": 90, "cost": "2500.00",
                        "currency": "INR", "order": 1, "notes": "" } ],
      "day_total_cost": "2500.00" }
  ],
  "totals": { "activities_cost": "31200.00",
              "expenses_cost": "17000.00",
              "grand_total": "48200.00" } } }
```

#### `?view=stop` — **200**

Same `trip` and `totals`; `days` is replaced by `stops`. Days no stop covers land
in a trailing group with `stop: null`, so no day is ever dropped.

```json
{ "success": true, "message": null, "data": {
  "trip": { "...": "as above" },
  "stops": [
    { "stop": { "id": 91, "title": "Manali", "city": { "...": "CityMini" }, "order": 1 },
      "days": [ { "date": "2026-03-15", "day_number": 2, "stop": { "...": "same stop" },
                  "activities": [], "day_total_cost": "0.00" } ],
      "stop_total_cost": "12400.00" },
    { "stop": null,
      "days": [ { "date": "2026-03-14", "day_number": 1, "stop": null,
                  "activities": [], "day_total_cost": "0.00" } ],
      "stop_total_cost": "0.00" }
  ],
  "totals": { "...": "as above" } } }
```

---

## 7. `apps/budget`

Code: [views.py](../apps/budget/views.py) ·
[serializers.py](../apps/budget/serializers.py) ·
[filters.py](../apps/budget/filters.py) ·
[selectors.py](../apps/budget/selectors.py) ·
[services.py](../apps/budget/services.py) ·
[urls.py](../apps/budget/urls.py)

Both prefixes hang off a trip: `trip_id` is a **parent**, not a filter, and it
resolves through the same `TripScopedMixin` as trips — a trip that is not yours
is a 404.

### `category` values

From [constants.py](../apps/budget/constants.py):

`TRANSPORT` · `STAY` · `ACTIVITY` · `MEALS` · `SHOPPING` · `OTHER`

> **`ACTIVITY` has two sources.** The bucket is `SUM(TripActivity.cost)` **plus**
> `Expense` rows filed under `ACTIVITY`. The sum is written in exactly one place,
> `services.trip_budget_breakdown`. Do not re-derive it.

---

### `/trips/{trip_id}/expenses/` · `ExpenseListCreateView`

#### GET

| Query | Type | Notes |
|---|---|---|
| `category` | string list | comma-separated |
| `trip_stop` | int | |
| `is_estimated` | bool | |
| `search` | string | `title`, `notes` |
| `ordering` | `incurred_on` / `amount` / `created_at` | default `-incurred_on,-created_at` |

**200** — paginated `ExpenseSerializer` rows:

```json
{ "success": true, "message": null, "data": {
  "results": [
    { "id": 771,
      "category": "STAY",
      "category_label": "Stay",
      "title": "Hostel, 3 nights",
      "amount": "5400.00",
      "currency": "INR",
      "trip_stop": 91,
      "incurred_on": "2026-03-15",
      "is_estimated": true,
      "notes": "",
      "created_at": "2026-08-20T12:00:00Z" }
  ],
  "pagination": { "count": 1, "page": 1, "pages": 1, "page_size": 20,
                  "has_next": false, "has_previous": false,
                  "next": null, "previous": null } } }
```

#### POST — `ExpenseWriteSerializer`

| Field | Type | Req | Notes |
|---|---|:--:|---|
| `category` | choice | yes | see the list above |
| `title` | string, max 150 | yes | |
| `amount` | decimal | yes | |
| `trip_stop` | int | no | nullable; must belong to **this** trip |
| `incurred_on` | date | no | nullable; must sit inside the trip's dates |
| `is_estimated` | bool | no | default `true` |
| `notes` | string | no | |

`currency` is absent on purpose — inherited from the trip, because the budget
adds these amounts up without converting.

```json
{ "category": "STAY", "title": "Hostel, 3 nights", "amount": "5400.00",
  "trip_stop": 91, "incurred_on": "2026-03-15", "is_estimated": true, "notes": "" }
```

**201** `{"success": true, "message": "Expense added.", "data": { "...": "Expense" } }`

**400** cases:

```json
{ "success": false, "message": "That stop does not belong to this trip.",
  "errors": { "fields": { "trip_stop": ["That stop does not belong to this trip."] } } }
```

```json
{ "success": false,
  "message": "This day is outside the trip's dates (2026-03-14 to 2026-03-24).",
  "errors": { "fields": { "incurred_on": ["This day is outside the trip's dates (2026-03-14 to 2026-03-24)."] } } }
```

A day outside the trip would never appear in the budget's `by_day` series, so the
money would be in the total but on no chart — hence the check.

---

### GET · PUT · PATCH · DELETE `/trips/{trip_id}/expenses/{id}/` · `ExpenseDetailView`

Same write payload; `PATCH` is partial.

- **200** on update, message `Expense updated.`
- **204** on delete (soft), empty body

---

### GET `/trips/{trip_id}/budget/` · `TripBudgetView`

Screen 9, whole. **Not paginated** — every part of the response is bounded by the
trip: one bucket per category, one row per stop, one row per day.

Labels and percentages are **precomputed** — the frontend should not divide to
draw a pie. Only non-zero buckets are returned, sorted by amount descending, so
the chart has no empty slices to filter out. `by_day` covers **every date in the
trip range**, including zero-spend days.

**200**

```json
{ "success": true, "message": null, "data": {
  "currency": "INR",
  "total_budget": "60000.00",
  "grand_total": "48200.00",
  "remaining": "11800.00",
  "is_over_budget": false,
  "avg_cost_per_day": "4381.82",
  "breakdown": [
    { "category": "ACTIVITY", "label": "Activities", "amount": "31200.00", "percentage": 64.7 },
    { "category": "STAY",     "label": "Stay",       "amount": "12000.00", "percentage": 24.9 },
    { "category": "MEALS",    "label": "Meals",      "amount": "5000.00",  "percentage": 10.4 }
  ],
  "by_stop": [
    { "stop_id": 91, "title": "Manali", "budget": "18000.00",
      "spent": "16400.00", "is_over_budget": false },
    { "stop_id": 92, "title": "Kasol", "budget": null,
      "spent": "9200.00", "is_over_budget": false }
  ],
  "by_day": [
    { "date": "2026-03-14", "amount": "0.00",    "is_over_budget": false },
    { "date": "2026-03-15", "amount": "7100.00", "is_over_budget": true }
  ],
  "alerts": [
    { "type": "OVERBUDGET_DAY", "date": "2026-03-15",
      "message": "2026-03-15 exceeds the average daily budget by 30%." }
  ] } }
```

**Field notes**

| Field | Type | Notes |
|---|---|---|
| `total_budget` | string / `null` | straight off the trip |
| `grand_total` | string | activities + expenses, from the one formula |
| `remaining` | string / `null` | `null` when the trip has no `total_budget` |
| `avg_cost_per_day` | string | `grand_total / duration_days` |
| `breakdown[].percentage` | **float** | already a percentage, 1 decimal |
| `by_stop[].budget` | string / `null` | the stop's own budget |
| `by_day[].is_over_budget` | bool | against the daily allowance, `total_budget / duration_days` |
| `alerts[].type` | `OVERBUDGET_TRIP` / `OVERBUDGET_DAY` | both need a `total_budget`; the trip-wide alert has `date: null` and sorts first |

A day alert only fires past a 10% tolerance over the daily allowance
(`DAY_ALERT_TOLERANCE`), so a rounding-level overshoot does not spam the screen.
With no `total_budget` set, `remaining` is `null`, `is_over_budget` is `false`
everywhere and `alerts` is empty.

---

## 8. Not implemented yet

These resolve as URL includes but have empty `urlpatterns`, so nothing under
them is routable. `config/api_urls.py` and `config/admin_urls.py` wired every
include up front on purpose — adding an endpoint means editing only the app's
own `urls.py`.

| Folder | Planned surface | Status |
|---|---|---|
| [apps/dashboard/](../apps/dashboard/) | `GET /dashboard/` — one aggregated home-screen call | empty |
| [apps/community/](../apps/community/) | `/community/**` — posts, comments, likes | empty (P2, first on the cut list) |
| [apps/analytics/](../apps/analytics/) | `/admin/analytics/**` + the `ActivityLog` middleware | empty |
| every `urls_admin.py` | the whole `/api/v1/admin/**` tree — users, trip moderation, master-data CRUD, analytics | **all empty** |

Also absent from the trips app, though `docs/API.md` specifies them:

- `POST` / `DELETE /trips/{id}/share/` — `is_public` is not writable anywhere in the current code
- `GET /public/trips/{share_token}/` — the public share page
- `POST /trips/{id}/copy/` — copy-with-date-rebase (`copied_from` exists on the model but is never set)
- `GET /trips/{id}/calendar/` — the calendar view

`Trip.share_token` and `Trip.share_url` are populated and readable on the trip
detail shape, but no endpoint consumes them yet.

When adding admin views, inherit
[`core.mixins.AdminOnlyMixin`](../core/mixins.py) on **every one**. DRF resolves
permission classes per view and middleware cannot see a JWT user, so a view that
forgets it falls back to the global `IsAuthenticated` — meaning any logged-in
user reaches an admin endpoint.
