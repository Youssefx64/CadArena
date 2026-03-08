# Frontend

The frontend is a lightweight static interface for CadArena.
It is intentionally kept framework-free: fast to load, simple to deploy, and easy to serve directly from FastAPI.

## Principles

- Direct page delivery with no build step
- Clear separation between pages, styles, scripts, and assets
- Stable file locations to match backend-served routes
- Low operational overhead for demos, iteration, and deployment

## Structure

```text
frontend/
├── index.html       # studio workspace
├── landing.html     # public landing page
├── blog.html        # blog page
├── contact.html     # contact page
├── profile.html     # user profile page
├── styles/          # page and shared stylesheets
├── scripts/         # page behavior and UI scripts
└── assets/          # logos and illustrations
```

## Route Mapping

These files are served by the backend without a frontend build pipeline:

- `/` -> `landing.html`
- `/blog` -> `blog.html`
- `/contact` -> `contact.html`
- `/app/` -> `index.html`

In addition, the backend mounts:

- `/app` as the frontend directory
- `/static` as a static asset path for the same directory

## Files

### HTML entry pages

- `landing.html`
- `index.html`
- `blog.html`
- `contact.html`
- `profile.html`

### Styles

- `styles/styles.css` for shared workspace styling
- Page-level styles such as `landing.css`, `blog.css`, `contact.css`, and `profile.css`

### Scripts

- `scripts/app.js` for the main studio behavior
- Page-specific scripts such as `landing.js`, `blog.js`, `contact.js`, and `profile.js`
- Shared helpers like `page-motion.js` and `back-nav.js`

## Working Model

This frontend is best treated as server-delivered UI rather than a separate SPA.
That choice keeps routing predictable and allows the FastAPI app to own both page delivery and API access.

## Why HTML Files Stay at Root

The backend references these files directly from [`backend/app/main.py`](/home/mango/Coding/Projects/CadArena/backend/app/main.py).
Keeping them at the frontend root avoids breaking route behavior and preserves simple file-based page serving.
