
### Local Testing

```bash
# Set environment variables
$env:SECRET_KEY="test-secret-key-for-testing-1234567890abcdef"
$env:FLASK_CONFIG="testing"

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_routes.py -v

# Run with coverage report
pytest tests/ -v --cov=app --cov-report=html
```

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch
