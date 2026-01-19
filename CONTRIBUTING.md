# Contributing Guidelines

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ai-underwriting.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Process

1. Make your changes
2. Run tests: `pytest` / `npm test`
3. Run linters: `ruff check .` / `npm run lint`
4. Commit changes using conventional commits
5. Push to your fork
6. Create a Pull Request

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Use Ruff for formatting and linting

### TypeScript/JavaScript
- Follow ESLint rules
- Use Prettier for formatting
- Write typed code (TypeScript)
- Document components

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(auth): add password reset functionality

- Added password reset endpoint
- Added email notification
- Added token validation

Closes #123
```

## Pull Request Process

1. Ensure all tests pass
2. Ensure linters pass
3. Update documentation if needed
4. Request review from maintainers
5. Address feedback
6. Merge when approved

## Testing

### Backend Tests
```bash
pytest tests/ -v --cov=backend
```

### Frontend Tests
```bash
cd frontend
npm run test:ui
```

## Code Review Criteria

- Code is well-documented
- Tests are added/updated
- No linting errors
- Type safety maintained
- Security considerations addressed
- Performance impact evaluated
