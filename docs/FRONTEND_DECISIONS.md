# AERIS Frontend Redesign Decisions

## 1. CSS and Theming Strategy
- Decided to strip out inline/Tailwind hardcoded colors and replace them with a unified **Design Token System** (`styles/tokens.css`).
- Created a dense, military-grade presentation with sober styling: high-contrast panels, single-pixel borders, no "glassmorphism", and restricted animation.
- Implemented robust Night (dark) and Day (light) mode toggles via CSS variables on the `:root` and `html[data-theme="day"]`.

## 2. Dependency Fixes
- The previous implementation used `@fontsource` packages which caused a peer-dependency crash with `vite@8.3.2`. 
- **Decision:** Removed all `@fontsource` NPM packages. Fonts (Inter) are now fetched via `index.html` Google Fonts standard `link` elements. 

## 3. Component Rewrites (Presentation Layer Only)
- **App Shell & Header:** Converted to a Command Bar style with a non-operational "PROTOTYPE" classification banner. Preserved RBAC routing and exact component paths.
- **Login Modal:** Switched to a secure, military-terminal visual style while preserving all existing login state machinery and demo fallback credentials.
- **Fleet Overview:** Reorganized into a high-density, priority-sorted data table with prominent Key Performance Indicator (KPI) metrics on top. Preserved CSV export and precise search/filtering logic.
- **Recommendations View (Decision Queue):** Re-structured to emphasize the "Human-in-the-loop" concept. Clearly segregated AI reasoning (SHAP evidence passports) from human decision buttons (Accept/Defer/Reject). 
- **Spares & Facilities:** Adopted logistics-terminal visuals.
- **Audit & Security:** Visualized the cryptographic hash chain and egress isolation in a unified security posture command dashboard.
- **Aircraft Details (Digital Twin):** Displayed as a modal slide-over that cleanly isolates model inferences, telemetry sparklines (Recharts), and What-If simulators.
- **Model Cards:** Provided static, structured model specification panels mirroring the strict ML governance logic of the backend.

## 4. Preservation of Core Logic
- **Hard Rule Maintained:** No backend endpoints, RBAC mechanics, database queries, API client files (`client.ts`), or ML data structures were modified.
- **React State:** All existing `useState` and `useEffect` blocks in `App.tsx` and child components were replicated byte-for-byte to prevent regression of logic.
