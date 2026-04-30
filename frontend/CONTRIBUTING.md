# Contributing to CadArena Frontend

Thank you for your interest in contributing to CadArena! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/CadArena.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `npm install`

## Development Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Build for production
npm run build
```

## Code Style

We use ESLint and Prettier for code formatting. Before committing:

```bash
# Format code
npm run format

# Lint code
npm run lint
```

### Style Guidelines

- Use functional components with hooks
- Use meaningful variable and function names
- Add comments for complex logic
- Keep components focused and single-responsibility
- Use TypeScript types where applicable

## Testing

All new features must include tests:

- Write tests for new components in `ComponentName.test.js`
- Write tests for utilities in `utils/utilityName.test.js`
- Aim for at least 70% code coverage
- Use React Testing Library for component tests
- Test behavior, not implementation

### Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test -- Button.test.js

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## Accessibility

All components must follow WCAG 2.1 AA standards:

- Include proper ARIA labels and roles
- Ensure keyboard navigation works
- Test with screen readers
- Respect `prefers-reduced-motion`
- Maintain sufficient color contrast

## Commit Messages

Use clear, descriptive commit messages:

```text
feat: Add new Button component with loading state
fix: Resolve accessibility issue in Modal component
docs: Update testing guide
refactor: Simplify validation logic
test: Add tests for Alert component
```

## Pull Request Process

1. Update the README.md with any new features or changes
2. Ensure all tests pass: `npm test`
3. Ensure code is formatted: `npm run format`
4. Ensure no linting errors: `npm run lint`
5. Create a pull request with a clear description
6. Link any related issues

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested the changes

## Checklist
- [ ] Tests pass
- [ ] Code is formatted
- [ ] No linting errors
- [ ] Accessibility standards met
- [ ] Documentation updated
```

## Component Guidelines

### Creating a New Component

1. Create component file: `src/components/ComponentName.js`
2. Create test file: `src/components/ComponentName.test.js`
3. Export from `src/components/index.js`
4. Add documentation in component file

### Component Template

```javascript
import React from 'react';
import PropTypes from 'prop-types';

/**
 * ComponentName - Brief description
 *
 * @param {Object} props - Component props
 * @param {string} props.title - Title text
 * @param {Function} props.onClick - Click handler
 * @returns {JSX.Element}
 */
function ComponentName({ title, onClick }) {
  return (
    <div role="region" aria-label={title}>
      <button onClick={onClick}>{title}</button>
    </div>
  );
}

ComponentName.propTypes = {
  title: PropTypes.string.isRequired,
  onClick: PropTypes.func,
};

ComponentName.defaultProps = {
  onClick: () => {},
};

export default ComponentName;
```

## Reporting Issues

When reporting bugs, include:

- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/videos if applicable
- Browser and OS information

## Questions?

Feel free to open an issue or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
