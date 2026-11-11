---
name: react
description: Frontend conventions for this project (React 19 + TypeScript + Vite + Tailwind CSS v4, modular feature-based components). Use whenever creating or editing anything under frontend/.
---

# React frontend

Stack: React 19, TypeScript (strict), Vite, Tailwind CSS v4, @tanstack/react-query for server
data, react-router for pages, react-leaflet + Leaflet for the map (OpenStreetMap tiles, no API
key). Import alias `@/` → `frontend/src/`. JavaScript files are not allowed; use `.ts`/`.tsx`.

## Folder structure

```
frontend/src/
  main.tsx               # entry; renders <App/>
  app/                   # App, providers (QueryClient), router
  components/
    ui/                  # generic presentational pieces: Button, Card, Select, Badge, Spinner
    layout/              # header, footer, page shell
  features/<name>/       # one folder per feature (map, tracts, rankings, sources, ...)
    api/                 # calls to the backend for this feature
    hooks/               # react-query hooks and feature state
    components/          # components used only by this feature
    types.ts             # mirrors backend schemas
    index.ts             # public API: the ONLY file other modules import from
  pages/                 # route screens; compose features, no business logic
  services/httpClient.ts # shared fetch wrapper with typed errors
  hooks/  utils/  types/  config/  styles/
```

## Rules
- Import a feature only via its `index.ts` (`@/features/map`), never its internals.
- Features don't import other features' internals; move shared code to components/, hooks/,
  services/ or utils/.
- One component per file, PascalCase file name; named exports only. Hooks are `useX.ts`.
- Components stay small (aim < 150 lines). Split by responsibility: container (data) vs view.
- All server data through react-query hooks in the feature's hooks/; no fetch in components.
- `import type` for type-only imports; no TS `enum` (use string-literal unions).
- Every async view handles loading, error and empty states with a clear message.
- Accessibility: semantic elements, labels on inputs, keyboard focus visible, alt text.
- Style only with Tailwind classes (see the `tailwind` skill).
- `npm run build` and `npm run lint` must pass before merging.
