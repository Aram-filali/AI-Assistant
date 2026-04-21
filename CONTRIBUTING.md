# Contributing to AI Sales Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Make your changes
5. Write or update tests
6. Commit with clear messages: `git commit -m 'Add amazing feature'`
7. Push to your fork
8. Create a Pull Request

## Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend
cd ../frontend
npm install
```

## Code Quality Standards

### Python (Backend)

- **Style**: Follow PEP 8 ([autopep8](https://pypi.org/project/autopep8/) or [black](https://github.com/psf/black))
- **Type Hints**: All public functions must have type hints
- **Docstrings**: Use Google-style docstrings
- **Testing**: Write tests for all new features
- **Coverage**: Maintain >80% code coverage

```bash
# Format code
black backend/app/

# Run linter
pylint backend/app/

# Run tests
pytest backend/tests/ --cov=app/
```

### TypeScript (Frontend)

- **Style**: Follow ESLint config (auto-fixable)
- **Type Safety**: Use proper TypeScript types, avoid `any`
- **Components**: Write functional components with hooks
- **Testing**: Write tests for complex components

```bash
# Format code
npm run format

# Run linter
npm run lint

# Run tests
npm test
```

## Testing Requirements

### Backend
- All new endpoints must have integration tests
- All business logic must have unit tests
- Run full test suite before submitting PR: `pytest tests/ -v`
- Minimum 80% code coverage for new code

### Frontend
- Component tests for UI changes
- Integration tests for user flows
- Run: `npm test`

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: Add user authentication
fix: Resolve CORS headers issue
docs: Update README deployment section
refactor: Simplify RAG pipeline
test: Add integration tests for chat endpoint
chore: Update dependencies
```

## Pull Request Process

1. **Title**: Descriptive title (e.g., "feat: Add knowledge base document versioning")
2. **Description**: Explain what, why, and how
3. **Tests**: Include test results or link to test coverage
4. **Documentation**: Update README/docs if needed
5. **No Breaking Changes**: Avoid API changes without discussion

### PR Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Code coverage maintained (>80%)
- [ ] Comments explain non-obvious logic
- [ ] Documentation updated
- [ ] No secrets/credentials in code

## Reporting Issues

### Bug Reports
Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python/Node version)
- Error logs if available

### Feature Requests
Include:
- Clear use case
- Proposed solution
- Why it's valuable
- Any concerns/tradeoffs

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Configuration & utilities
│   ├── models/           # Database models
│   ├── schemas/          # Request/response schemas
│   ├── services/         # Business logic
│   └── utils/            # Helper functions
└── tests/                # Test suite

frontend/
├── app/
│   ├── (auth)/           # Authentication pages
│   ├── dashboard/        # Main UI
│   └── components/       # Reusable components
├── lib/                  # Utilities & hooks
└── __tests__/            # Tests
```

## Architecture Decisions

Key architectural patterns:

1. **Service Layer Pattern**: Business logic in services, not directly in endpoints
2. **Factory Pattern**: Test data generation via factories (not fixtures)
3. **RAG Pipeline**: Modular components (loader → splitter → embedder → retriever → generator)
4. **Async-First**: All I/O operations are async
5. **Multi-Tenant Isolation**: User data always filtered by user_id

## Performance Guidelines

- API responses: < 200ms for simple operations
- Document processing: Target 100 docs/minute
- Concurrent users: Test with 100+ simultaneous connections
- Database queries: Use indexes, avoid N+1 queries

## Security Best Practices

- Never commit secrets (use .env.example)
- Validate all user inputs
- Use parameterized queries (SQLAlchemy ORM)
- Hash passwords (PBKDF2-SHA256)
- Implement rate limiting
- Add CORS properly configured
- Keep dependencies updated: `pip-audit`, `npm audit`

## Documentation Guidelines

- Code comments explain **why**, not **what**
- Docstrings for all public APIs
- Keep README updated with changes
- Document complex algorithms
- Update API docs (/docs endpoint)

## Questions?

- Create a GitHub Discussion
- Open an Issue for clarification
- Email: contact@yourdomain.com

## License

By contributing, you agree your code will be licensed under MIT License.

---

Thank you for contributing to AI Sales Assistant! 🚀
