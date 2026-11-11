---
name: tailwind
description: Tailwind CSS v4 setup and usage for this project's React frontend. Use when styling components, adding theme tokens, or touching frontend/src/styles or vite.config.ts.
---

# Tailwind CSS v4

## Setup
- Install: `npm install -D tailwindcss @tailwindcss/vite`.
- Register `tailwindcss()` from `@tailwindcss/vite` in `vite.config.ts` plugins.
- `src/styles/index.css` starts with `@import "tailwindcss";` and is imported in `main.tsx`.
- v4 is CSS-first: there is **no tailwind.config.js and no postcss.config.js**. Don't create them.

## Theme tokens
Define the palette and fonts once with `@theme` in index.css; they become utilities:

```css
@import "tailwindcss";
@theme {
  --color-need-low: #e8f1e4;
  --color-need-high: #9b2c2c;
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
}
/* -> bg-need-low, text-need-high, font-sans */
```
Custom utilities use `@utility name { ... }`, not `@layer utilities`.

## Rules
- Style with utility classes in `className`. No CSS modules, no inline style objects
  (except values computed at runtime, e.g. map colours from data).
- Repeated class combinations → a component in components/ui/, not `@apply`.
- Use theme tokens instead of arbitrary values (`bg-[#123456]`) for anything reused.
- Mobile-first: base classes for phones, then `sm: md: lg:` overrides.
- Choropleth colours must be colour-blind safe and come with a legend.
- v4 renames: `shadow-sm`→`shadow-xs`, `shadow`→`shadow-sm`, `rounded`→`rounded-sm`,
  `outline-none`→`outline-hidden`, `ring`→`ring-3`.
