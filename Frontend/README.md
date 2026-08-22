# GlobeTrotter — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4.

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
```

## Layout

```
src/
  app/
    (auth)/          login + registration, split-panel shell, no navbar
    (main)/          everything after login, wrapped by GlobalTrotterNavbar
    globals.css      design tokens (@theme) + base styles
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
