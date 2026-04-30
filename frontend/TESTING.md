# CadArena Frontend

AI-Powered Architectural CAD Studio Frontend

## 🚀 Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm start
```

Runs the app in development mode. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Build

```bash
npm run build
```

Builds the app for production to the `build` folder.

## 🧪 Testing

### Run Tests

```bash
npm test
```

Runs the test suite in interactive watch mode.

### Run Tests with Coverage

```bash
npm test -- --coverage
```

Generates a coverage report for all test files.

### Run Specific Test File

```bash
npm test -- Button.test.js
```

## 📋 Project Structure

```text
src/
├── components/
│   ├── ui/              # Reusable UI components
│   ├── pages/           # Page components
│   └── layout/          # Layout components
├── hooks/               # Custom React hooks
├── utils/               # Utility functions
├── constants/           # Constants and configuration
├── styles/              # Global styles
└── App.js              # Main app component
```

## 🎨 Components

### UI Components

- **Button** - Customizable button with variants and sizes
- **Alert** - Alert component with different types (success, error, warning, info)
- **Input** - Text input with validation
- **Select** - Dropdown select component
- **Textarea** - Multi-line text input
- **Modal** - Modal dialog component
- **Card** - Card container component
- **LoadingSkeleton** - Loading placeholder component

## ♿ Accessibility

All components follow WCAG 2.1 AA standards:

- Keyboard navigation support
- ARIA labels and roles
- Color contrast compliance
- Motion preferences support (`prefers-reduced-motion`)
- Screen reader friendly

## 🧩 Hooks

### useReducedMotion

Detects if user prefers reduced motion:

```javascript
import { useReducedMotion } from './hooks';

function MyComponent() {
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      animate={{ opacity: 1 }}
      transition={{ duration: prefersReduced ? 0 : 0.3 }}
    >
      Content
    </motion.div>
  );
}
```

## 🔍 Validation

Comprehensive validation utilities:

```javascript
import { validateEmail, validatePassword, validateForm } from './utils/validation';

// Single field validation
validateEmail('test@example.com'); // true

// Password strength check
const result = validatePassword('SecurePass123!');
console.log(result.strength); // 5

// Form validation
const errors = validateForm(formData, rules);
```

## 🛠️ Configuration Files

- `.babelrc` - Babel configuration for JSX and ES6+
- `.eslintrc.json` - ESLint rules
- `.prettierrc` - Code formatting rules
- `jest.config.js` - Jest testing configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.js` - PostCSS configuration

## 📦 Dependencies

### Main

- React 18.2.0
- React Router DOM 6.3.0
- Axios 1.4.0
- Framer Motion 10.12.16
- Tailwind CSS 3.3.2
- Lucide React 0.263.1
- Recharts 2.7.2
- React Hot Toast 2.4.1

### Dev

- Jest 29.5.0
- React Testing Library 13.3.0
- Babel Jest 29.5.0
- ESLint
- Prettier

## 🚀 Performance

- Code splitting with React.lazy
- Image optimization
- Bundle analysis
- Lazy loading components

## 📝 Code Style

Code is formatted with Prettier and linted with ESLint. Run before committing:

```bash
npm run lint
npm run format
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT
