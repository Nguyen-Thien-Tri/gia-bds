<!--
Project-specific Copilot instructions for quick agent productivity.
Keep this file concise (20–50 lines). Update when repo structure or conventions change.
-->

# Quick Project Guide for AI Coding Agents

- **Stack & Tooling:** Vite + React + TypeScript, TailwindCSS (v4 plugin), ESLint. See `package.json` scripts: `dev`, `build`, `preview`, `lint`.
- **Entry / Routing:** Routing is defined in `src/main.tsx`. Pages live under `src/pages/*` and are wired to routes (e.g. `/bieu-do-gia-ban` -> `src/pages/BieuDoGiaBan/BieuDoGiaBan.tsx`).
- **Feature layout:** Each page folder groups related components under `components/`. Example: `src/pages/BieuDoGiaBan/components/` contains `FilterSection.tsx`, `ChartsSection.tsx`, `RealEstateAnalytics.tsx`.
- **Styling:** Tailwind via `index.css` and `tailwindcss` plugin in `vite.config.js`. Follow the existing utility class usage—do not introduce global CSS unless necessary.
- **Data & Backend:** Firebase (modular v9) is used in examples. See `src/pages/FirestoreQueryTester.tsx` for the canonical Firestore usage and the `price_data` collection queries. Replace the firebaseConfig in that file or centralize env-based config when making changes.
- **Geo data & assets:** Static geographic data (provinces/districts) live in `src/assets/geo.ts`. Filter logic in `FilterSection.tsx` derives districts from that file—preserve that pattern if modifying filters.
- **Charts & visualization:** Charts use `recharts` and `chart.js`. See `src/pages/TrangChu/components/*` and `src/pages/*/components/ChartsSection.tsx` for examples of how data is transformed into chart props.
- **Component patterns:** Components are TypeScript `tsx` default exports, often with small exported helpers (e.g., `MultiSelectFilter`, `FiltersContainer` in `FilterSection.tsx`). Prefer named prop interfaces and avoid changing public prop shapes without updates across callers.
- **Conventions & UX details:**
  - UI strings and routes use Vietnamese (e.g., `Xem`, `Chọn tất cả`); preserve locale when editing text.
  - Some components enforce selection rules (e.g., districts enabled only when exactly one city selected in `FiltersContainer`). Keep these rules intact when refactoring.
- **Linting & quality:** Run `npm run lint` for ESLint checks. Project uses `eslint.config.js` and TypeScript-aware rules.
- **No test harness detected:** There are no unit tests in the repo; add tests in `src/__tests__` only after agreeing on test framework and config.
- **Important files to inspect when making changes:**
  - `src/main.tsx` (routing)
  - `src/pages/*/components/*` (UI patterns)
  - `src/assets/geo.ts` (geo data)
  - `src/pages/FirestoreQueryTester.tsx` (Firebase patterns)
  - `vite.config.js` and `package.json` (build/dev scripts)

Examples for common tasks:

- Add a route: update `src/main.tsx` and create a page under `src/pages/<Feature>/` with a `components` subfolder.
- Fetch Firestore data: follow the pattern in `src/pages/FirestoreQueryTester.tsx` (use modular SDK: `getFirestore`, `collection`, `query`, `getDocs`).

If anything here seems incomplete or you want the agent to standardize config (e.g., centralize Firebase config into an env-based module), say which area to prioritize and I will update the repo and tests accordingly.
