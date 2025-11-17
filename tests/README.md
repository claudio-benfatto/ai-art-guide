# Tests for Barcelona AI Art Guide

This directory contains comprehensive tests for the data models and validation logic.

## Test Coverage

**95 tests with 92% code coverage**

### Test Files

- `test_event_model.py` - Event model validation (69 tests)
  - ID format validation
  - String length validation (title, description)
  - Tags validation (controlled vocabulary, count)
  - Category, domain, cost bucket validation
  - Date range validation (including "unknown")
  - Outdoor field validation (bool or "unknown")
  - Coordinates validation (Barcelona bounds)
  - Source type validation

- `test_other_models.py` - Venue, UserProfile, EmbeddingDoc models (21 tests)
  - Venue validation (ID, type, name, coordinates)
  - UserProfile validation (tags, weights, language)
  - EmbeddingDoc validation (vector dimensionality)

- `test_data_container.py` - DataContainer integration tests (22 tests)
  - Referential integrity (venue_id references)
  - Uniqueness validation (duplicate IDs)
  - Query methods (by ID, venue, tag)
  - Tag coverage analysis
  - YAML loading/saving
  - Roundtrip serialization

## Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run with coverage report
```bash
poetry run pytest --cov=src/adk/models --cov-report=term-missing
```

### Run specific test file
```bash
poetry run pytest tests/test_event_model.py
```

### Run specific test class
```bash
poetry run pytest tests/test_event_model.py::TestEventDateValidation
```

### Run specific test
```bash
poetry run pytest tests/test_event_model.py::TestEventDateValidation::test_end_before_start
```

### Run tests matching a pattern
```bash
poetry run pytest -k "validation"
```

### Run with verbose output
```bash
poetry run pytest -v
```

### Alternative: Using Poetry shell
```bash
# Activate Poetry's virtual environment
poetry shell

# Then run commands without "poetry run" prefix
pytest
pytest --cov=src/adk/models
```

## Test Fixtures

Common test data is defined in `conftest.py`:

- `valid_event_data` - Minimal valid event
- `valid_venue_data` - Minimal valid venue
- `valid_user_profile_data` - Valid user profile
- `valid_embedding_doc_data` - Valid embedding document
- `valid_data_container_dict` - Complete data with events and venues
- `test_data_dir` - Temporary directory for file tests

## Coverage Report

After running tests with coverage, open `htmlcov/index.html` in a browser for detailed coverage visualization.

## Writing New Tests

When adding new validation rules:

1. Add test in appropriate test file
2. Use pytest fixtures for common data
3. Use `pytest.raises(ValidationError)` for error cases
4. Use `pytest.mark.parametrize` for testing multiple values
5. Run tests to verify coverage stays high

## CI Integration

These tests are designed to run in CI/CD pipelines with:
```bash
pytest --cov=src --cov-report=xml --cov-report=term
```
