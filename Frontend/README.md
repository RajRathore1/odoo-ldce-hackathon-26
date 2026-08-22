# GlobeTrotter — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4.

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
```

## How data is fetched

Every call is made from the browser, straight to the backend, so you can watch
each one in the Network tab. There is no Next.js API route in between.

- `lib/api/client.ts` builds the URL from `NEXT_PUBLIC_API_BASE_URL`, attaches
  the bearer token, unwraps the `{success, message, data}` envelope, and on a
  401 refreshes once and retries. Refresh tokens rotate and the spent one is
  blacklisted immediately, so concurrent calls share a single refresh.
- `lib/api/use-api.ts` is the GET hook pages use.
- `components/auth-provider.tsx` owns the session and guards `(main)` routes.
- Tokens live in `localStorage`, which means JavaScript can read them.

`NEXT_PUBLIC_API_BASE_URL` is inlined at build time, so restart the dev server
after changing it. The backend allows CORS from `http://localhost:3000`.

## Layout

```
src/
  app/
    (auth)/          login + registration, split-panel shell, no navbar
    (main)/          everything after login, wrapped by GlobalTrotterNavbar
    globals.css      design tokens (@theme) + base styles
  lib/api/           client, hooks, and one type module per backend app
  components/
    ui/              Button, Input/Textarea/Select, Badge, Avatar
    navbar.tsx       GlobalTrotterNavbar
    search-filter-bar.tsx
    trip-card.tsx
  lib/               types, formatters, mock data
```

## Design system

Colours and fonts live as Tailwind theme tokens in `src/app/globals.css`, so
they are available both as CSS variables (`var(--color-primary)`) and as
utilities (`bg-primary`, `text-text-muted`, `font-heading`). Nothing should
hardcode a hex value.

| Token             | Use                                  |
| ----------------- | ------------------------------------ |
| `primary`         | navy — header/nav, primary buttons   |
| `accent`          | amber — "Plan a trip" style CTAs     |
| `success`         | Completed trip badge                 |
| `warning`         | Ongoing trip badge                   |
| `info`            | Up-coming trip badge                 |
| `bg` / `surface`  | page background / cards              |
| `text` / `text-muted` | body copy / secondary copy       |

Fonts: Poppins for headings (`font-heading`), Inter for body (default).

## Progress

- [x] Design system + shared components
- [x] Hour 1 — Login & Registration
- [x] Hour 2 — Main landing page
- [ ] Hour 3 — Create a new trip
- [ ] Hour 4 — Build itinerary
- [ ] Hour 5 — User trip listing
- [ ] Hour 6 — Activity / city search
- [ ] Hour 7 — Itinerary view with budget
- [ ] Hour 8 — Profile + calendar
