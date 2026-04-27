# CadArena Frontend

The frontend has two parts:

- a React app for the main website and `/community`
- the legacy Studio UI, embedded at `/studio`

## Routes

- `/` home page
- `/community` engineering Q&A
- `/generate`
- `/models`
- `/metrics`
- `/about`
- `/developers`
- `/studio`

## Directory Layout

```text
frontend/
├── public/
│   ├── assets/
│   └── studio-app/      generated copy of the legacy studio
├── scripts/
│   └── copy-studio.js   copies studio-source into public/studio-app
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── utils/
├── studio-source/       source of the legacy studio files
├── package.json
└── .env.example
```

## Local Development

Prerequisites:

- Node.js 16+
- backend running on `http://localhost:8000`

Install and start:

```bash
cd frontend
npm install
npm start
```

Open:

- `http://localhost:3000/`
- `http://localhost:3000/studio`
- `http://localhost:3000/community`

## Build

```bash
npm run build
```

The build process runs `prebuild`, which copies `studio-source/` into `public/studio-app/` before compiling the React app.

## Studio Workflow

- edit legacy studio files in `studio-source/`
- do not edit `public/studio-app/` directly
- `copy-studio.js` is the bridge between the source and the served copy

## Environment

Example values live in `frontend/.env.example`.

Common variables:

- `REACT_APP_API_URL`
- `REACT_APP_API_TIMEOUT`
- `REACT_APP_ENABLE_AUTH`
- `REACT_APP_ENV`
- `GENERATE_SOURCEMAP`

## Verification

```bash
npm run build
```

If the backend is already running, the React dev server proxies API requests to `http://localhost:8000`.
