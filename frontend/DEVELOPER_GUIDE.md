# CadArena Frontend - Developer Guide

## Project Structure

```
frontend/
├── public/
│   ├── index.html          # Main React app entry
│   ├── studio-app/         # Studio UI (vanilla JS)
│   │   ├── index.html
│   │   └── profile.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   └── layout/         # Layout components (Navbar, Footer)
│   ├── pages/              # Page components
│   │   ├── HomePage.js     # Landing page
│   │   ├── StudioPage.js   # Main editor
│   │   ├── ModelsPage.js   # Model info
│   │   ├── MetricsPage.js  # Metrics display
│   │   ├── AboutPage.js    # About/documentation
│   │   └── DevelopersPage.js
│   ├── services/           # API services
│   │   └── api.js          # Axios-based API client
│   ├── App.js              # Root component
│   └── index.js            # React entry point
├── studio-source/          # Studio UI source (copied to public/studio-app)
│   ├── index.html
│   ├── scripts/
│   │   ├── app.js          # Main application logic
│   │   ├── back-nav.js     # Navigation handler
│   │   └── profile.js      # Profile management
│   └── styles/
│       ├── styles.css      # Main styles
│       ├── back-nav.css    # Navigation styles
│       └── profile.css     # Profile styles
├── package.json            # Dependencies
└── tailwind.config.js      # Tailwind configuration
```

## Setup

### Prerequisites
- Node.js 16+ and npm 8+
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local if needed
nano .env.local

# Start development server
npm start
```

The app will open at `http://localhost:3000`

### Build for Production

```bash
# Create optimized production build
npm run build

# Serve locally to test
npx serve -s build -l 3000
```

## Available Scripts

- `npm start` - Start development server with hot reload
- `npm build` - Create production build
- `npm test` - Run test suite (when available)
- `npm eject` - Eject from create-react-app (one-way operation)

## Key Features

### 1. Studio Application
- **Location**: `/studio` route (or `/app/` for vanilla JS version)
- **Features**: 
  - Conversational floor plan generation
  - Project management
  - DXF preview and download
  - Model selection
  - Chat-based iteration

### 2. Landing Pages
- **Home**: Showcase features and metrics
- **Models**: Model comparison and details
- **Metrics**: Performance benchmarks
- **About**: Documentation and guides
- **Developers**: API documentation

### 3. API Integration
- **Base URL**: Configurable via `REACT_APP_API_URL`
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /workspace/generate-dxf` - Generate DXF from prompt
  - `POST /workspace/iterate` - Iterate on existing design
  - `GET /workspace/projects` - List projects
  - etc.

## Development Guidelines

### Code Style
- Use ES6+ syntax
- Functional components with React hooks
- Meaningful variable and function names
- Comments for complex logic
- Accessibility-first: ARIA labels, semantic HTML

### Component Guidelines
- Keep components focused (single responsibility)
- Use props for configuration
- Lift state when needed
- Memoize expensive computations with `useMemo`

### Performance Best Practices
- Lazy load pages with `React.lazy()`
- Code-split large bundles
- Optimize images (use WebP when possible)
- Minimize re-renders with `React.memo()`
- Use production builds for testing

### Error Handling
- Wrap API calls in try/catch
- Show user-friendly error messages
- Log errors to console in development
- Handle network timeouts gracefully

## Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Testing (TODO)
Testing infrastructure needs to be set up. Recommended stack:
- Jest for unit tests
- React Testing Library for component tests
- Cypress for E2E tests

## Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] API URL points to production backend
- [ ] Analytics enabled (if applicable)
- [ ] Error logging configured
- [ ] Security headers set
- [ ] HTTPS enabled
- [ ] CSP policy configured
- [ ] All tests passing
- [ ] Performance optimized (Lighthouse score >90)
- [ ] Accessibility checked (WCAG AA)

### Deployment Commands
```bash
# Build for production
npm run build

# Test production build locally
npx serve -s build

# Deploy (example with Vercel)
vercel deploy --prod
```

## Common Issues & Solutions

### Backend Connection Fails
- Ensure backend is running: `uvicorn app.main:app --reload`
- Check API_URL in `.env.local`
- Verify CORS headers in backend

### Styles Not Loading
- Clear browser cache (Ctrl+Shift+Delete)
- Check Tailwind build: `npm run build`
- Verify CSS files in public folder

### Studio Page Blank
- Check browser console for errors
- Verify studio-source files are copied to public/
- Clear localStorage: see browser DevTools

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `REACT_APP_API_URL` | `http://localhost:8000` | Backend API endpoint |
| `REACT_APP_API_TIMEOUT` | `180000` | Request timeout (ms) |
| `REACT_APP_ENABLE_AUTH` | `false` | Enable authentication UI |
| `REACT_APP_ENV` | `development` | Runtime environment |
| `GENERATE_SOURCEMAP` | `false` | Include sourcemaps in build |

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/description

# Make changes and commit
git add .
git commit -m "brief description"

# Push and create PR
git push origin feature/description
```

## Resources

- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Framer Motion](https://www.framer.com/motion/)
- [Lucide Icons](https://lucide.dev)
- [Axios Documentation](https://axios-http.com)

## Support

For issues or questions:
1. Check existing GitHub issues
2. Create a new issue with minimal reproducible example
3. Contact the development team

---

Last updated: 2026-04-26
