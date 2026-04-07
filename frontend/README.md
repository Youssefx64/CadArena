# CadArena Frontend

React frontend for CadArena, a conversational CAD studio focused on architectural layouts, DXF exports, and AI-assisted design workflows.

## Highlights

- Single frontend workspace rooted at `frontend/`
- Dedicated `/studio` route for the embedded CadArena chat studio
- React marketing and project pages alongside the full studio experience
- Tailwind CSS, Framer Motion, React Router, and React Hot Toast

## Run Locally

### Prerequisites

- Node.js 16+
- CadArena backend running from `../backend`

### Install

```bash
npm install
```

### Start

```bash
npm start
```

Open `http://localhost:3000`, then visit `http://localhost:3000/studio` for the chat studio.

### Build

```bash
npm run build
```

## Studio Integration

The embedded studio is copied into `public/studio-app` automatically through:

- `npm start` -> `prestart`
- `npm run build` -> `prebuild`

The copy script lives in `scripts/copy-studio.js` and reads its source files from `studio-source/`.

## Environment

Create `.env` in `frontend` if needed:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
```

The studio itself uses relative `/api/v1/*` requests and is proxied to the FastAPI backend at `http://localhost:8000` during local development.

## Ownership

- Project: `CadArena`
- Maintainer: `Youssef Taha Badawi`
- LinkedIn: `https://www.linkedin.com/in/yousseftahaai/`
- GitHub: `https://github.com/Youssefx64/`
- Repository: `https://github.com/Youssefx64/CadArena`
- Project Email: `cadarena.ai@gmail.com`
