# CadArena

AI-powered architectural design platform that transforms natural language prompts into professional CAD floor plans.

## Architecture

- **Frontend**: React 18 app (Create React App / react-scripts) running on port 5000
- **Backend**: FastAPI (Python 3.12) running on port 8000 (dev) / port 5000 (production)
- **Database**: SQLite (stored in `backend/data/`)
- **AI**: HuggingFace transformers, Ollama LLM integration, LangChain

## Project Structure

```
frontend/          React frontend app
  src/             Application source
  public/          Static assets
  studio-source/   Studio app source (copied to public/studio-app on start)
  scripts/         Build helper scripts (copy-studio.js)

backend/           FastAPI backend
  app/
    api/           API v1 routes (DXF endpoints)
    core/          Settings, logging, env loading
    models/        Pydantic models
    routers/       Route handlers (auth, community, workspace, etc.)
    services/      Business logic (design parser, DXF, auth, community)
    domain/        Domain logic
  data/            SQLite database files (runtime, gitignored)
  .env             Runtime environment variables (not in git)
  .env.example     Template for env vars
```

## Key Features

- AI-powered floor plan generation from natural language
- DXF export (AutoCAD/Revit compatible)
- EBC 2023 compliance checking
- Community Q&A hub (coming soon)
- Multi-language (Arabic & English)
- JWT authentication with optional Google OAuth
- Workspace with project management

## Workflows

- **Start application** — Frontend dev server: `cd frontend && HOST=0.0.0.0 PORT=5000 DANGEROUSLY_DISABLE_HOST_CHECK=true REACT_APP_API_URL='' npm start`
- **Backend API** — Backend server: `cd backend && python -m uvicorn app.main:app --host localhost --port 8000`

## Deployment

- Build: `cd frontend && npm run build` (React build served by FastAPI)
- Run: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 5000`
- Target: autoscale

## Environment Variables

Stored in `backend/.env` (see `backend/.env.example` for template). Key vars:
- `CADARENA_JWT_SECRET` — JWT signing secret
- `PROVIDER_KEY_SECRET` — Fernet key for encrypting provider API keys
- `HF_TOKEN` — HuggingFace token (optional, enables higher rate limits)
- `CADARENA_WORKSPACE_DB_PATH` — SQLite DB path (default: `./data/workspace.db`)

## Dependencies

- Python: FastAPI, uvicorn, ezdxf, matplotlib, torch (CPU), transformers, accelerate, langchain, langchain-ollama, bcrypt, cryptography
- Node: React, react-router-dom, axios, framer-motion, tailwindcss, recharts, lucide-react

## Authentication System

**Backend** (already complete): JWT HTTP-only cookies (`cadarena_auth`, 7-day TTL, SameSite=lax), bcrypt password hashing, profile + avatar endpoints, optional Google OAuth.

**Frontend** (`frontend/src/`):
- `services/authApi.js` — Dedicated axios instance with `withCredentials: true` and `baseURL: ''` (relative, uses CRA proxy in dev / same-origin in prod). Exports: `register`, `login`, `logout`, `getCurrentUser`, `getProfile`, `updateProfile`, `uploadAvatar`, `deleteAvatar`.
- `contexts/AuthContext.js` — React context providing `user`, `profile`, `isLoading`, `isAuthenticated`, `avatarTs`, and `login/register/logout/refreshProfile/bumpAvatarTs`. Silently restores session on app mount via `GET /api/v1/auth/me`.
- `components/auth/ProtectedRoute.js` — Redirects to `/login` (with `state.from`) if not authenticated. Shows spinner while auth state is resolving.
- `pages/LoginPage.js` — Email + password with show/hide toggle, real-time validation, animated error banner, redirects to originally-intended page on success.
- `pages/SignUpPage.js` — Name + email + password + confirm fields, 4-level password strength meter, real-time validation.
- `pages/ProfilePage.js` — Protected. Displays avatar, display name, headline, join date, company, website. Edit button opens EditProfilePage.
- `pages/EditProfilePage.js` — Protected. Avatar upload/delete with live preview (5 MB max). Form fields: display_name, headline, company, website, timezone. Saves via PATCH + refreshes context.

**Routes**: `/login`, `/signup`, `/profile` (protected), `/profile/edit` (protected).

**Navbar auth state**: Unauthenticated → "Sign In" ghost button + "Sign Up" primary button. Authenticated → "Studio" button + avatar/name button with animated dropdown (My Profile, Edit Profile, Sign Out). Mobile menu shows user card + profile/sign-out actions.

**Avatar cache-busting**: `avatarTs` state (timestamp) in AuthContext, bumped after avatar upload/delete. Used as `?t=${avatarTs}` on all `<img src="/api/v1/profile/me/avatar">` elements.

## UI/UX Notes

- **Code splitting**: All 8 pages are lazy-loaded via `React.lazy` + `Suspense` with a skeleton fallback (`PageLoader`) for smooth transitions
- **Navbar**: Animated mobile menu (Framer Motion slide-in with staggered items), Escape key closes menu, body scroll locked when open, "Launch Studio" CTA button on desktop/mobile, ARIA `aria-expanded` and `aria-current` attributes on all nav items
- **Footer**: All internal links use React Router `<Link>` to avoid full-page reloads
- **CommunityPage**: No external CDN image dependencies — all icons use lucide-react; includes email notification sign-up with `aria-live` feedback
- **GeneratorPage**: Status indicator shown inline without toast on page load; blueprint placeholder shown in preview pane before generation; metrics card rendered post-generation. Accepts `location.state.prefillPrompt` from navigation to pre-fill the prompt textarea.
- **HomePage**: Full redesigned landing page with 7 sections:
  1. **Hero** — Animated gradient background, gradient headline, `HeroPromptBar` (pill-shaped input with Framer Motion cycling placeholder, navigates to `/generate` with prefilled prompt), quick-try example chips, ghost CTAs, `BlueprintPreview` card
  2. **Trust Strip** — 5 key metrics (84.5% accuracy, 2.3s generation, +13.2% over baseline, EBC 2023, DXF-ready) in a glass-morphism horizontal band
  3. **How It Works** — 3-step section (Describe → Generate → Export) with numbered `landing-step-index` badges, icon badges, and a desktop connector line
  4. **Features** — 4 cards: AI Generation, Constraint-Aware Design, Measurable Quality, DXF Export
  5. **Live Demo** — 2-column layout: interactive prompt selector (4 examples) + `BlueprintPreview` with animated output metric chips (FID, CLIP, Adjacency, EBC)
  6. **Performance** — Improvements list + animated progress bar for 84.5% accuracy
  7. **CTA** — `app-cta-panel` gradient with `HeroPromptBar` (dark variant) + Studio link
- **CSS additions** (`index.css`): `.hero-prompt-bar`, `.hero-prompt-bar-dark`, `.hero-prompt-input`, `.landing-trust-strip`, `.landing-step-index`
- **CSS**: Design system uses CSS custom properties + `@layer components` in `index.css`; no CSS modules
- **Accessibility**: ARIA labels on all interactive elements, `role="status"` with `aria-live` on dynamic status regions, `sr-only` labels on icon-only buttons, focus management on mobile menu
