# Test Suite Documentation

## Structure

```
backend/tests/
├── __init__.py               # Package marker
├── conftest.py               # Pytest configuration
├── test_auth.py              # Authentication tests
├── test_errors.py            # Error handling tests
├── test_security.py          # Security tests
├── test_endpoints.py         # Endpoint tests
├── test_integration.py       # Integration tests
└── README_TESTS.md          # This file
```

## Quick Start

### Install dependencies
```bash
pip install pytest pytest-asyncio httpx
```

### Run all tests
```bash
cd backend
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_auth.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Categories

### 1. Authentication (`test_auth.py`)
- ✅ Valid login credentials
- ✅ Get current user
- ❌ Invalid email
- ❌ Wrong password  
- ❌ No token
- ❌ Invalid token
- Security: SQL injection, token format

### 2. Error Handling (`test_errors.py`)
- 404 Not Found
- 400 Bad Request
- 401 Unauthorized
- 422 Validation Errors
- Consistent error format

### 3. Security (`test_security.py`)
- Access control verification
- Input validation
- SQL injection prevention
- XSS prevention
- Sensitive data protection

### 4. Endpoints (`test_endpoints.py`)
- Leads endpoints (GET, pagination, search, filter)
- Analytics endpoints
- Activity logs
- Chat conversations
- Knowledge bases
- Export endpoints

### 5. Integration (`test_integration.py`)
- Complete auth workflow
- Leads workflow
- Chat workflow
- Knowledge workflow

## Running Tests

### All tests
```bash
pytest tests/
```

### Verbose output
```bash
pytest tests/ -v
```

### Stop on first failure
```bash
pytest tests/ -x
```

### Show print statements
```bash
pytest tests/ -s
```

### Coverage report
```bash
pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html to see report
```

### Specific marker
```bash
pytest tests/ -m integration
```

## Test Data

Tests use:
- Admin: `admin@gmail.com` / `admin123`
- Backend: `http://localhost:8000`

### Prerequisites

Backend must be running:
```bash
docker-compose up -d backend
```

Database must have test data populated.

## Important Notes

1. **Async tests**: Use `@pytest.mark.asyncio` decorator
2. **Fixtures**: Reusable test components (client, auth_client)
3. **Parametrize**: Test multiple values with `@pytest.mark.parametrize`
4. **Markers**: Organize tests with `@pytest.mark.integration`, etc.

## Expected Coverage

| Category | Current | Target |
|----------|---------|--------|
| Auth | 80% | 95% |
| Errors | 40% | 80% |
| Security | 30% | 80% |
| Endpoints | 70% | 90% |
| Integration | 50% | 85% |

## CI/CD Integration

Add to GitHub Actions (`.github/workflows/test.yml`):

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: password
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
```

## Common Issues

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Then restart backend
docker-compose up -d backend
```

### Import errors
```bash
# Install dependencies
pip install -r requirements.txt
```

### Async test errors
```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

## Next Steps

1. ✅ Run tests locally
2. ✅ Add to CI/CD pipeline
3. ✅ Increase coverage to 85%+
4. ✅ Add frontend tests (Jest)
5. ✅ Add load testing (k6)
