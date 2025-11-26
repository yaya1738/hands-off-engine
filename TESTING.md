# Testing Guide

## Overview

The Hands-Off Engine includes comprehensive automated testing to ensure system reliability and correctness. Tests are organized into unit tests and integration tests, with continuous integration via GitHub Actions.

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_decider.py

# Specific test class
pytest tests/unit/test_decider.py::TestPlanActions

# Specific test method
pytest tests/unit/test_decider.py::TestPlanActions::test_plan_actions_kelly_sizing
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest tests/ -v --tb=short
```

## Test Structure

### Unit Tests (`tests/unit/`)

Unit tests validate individual components in isolation:

- **`test_audit_logger.py`** - Tests audit logging functionality (history_log module)
- **`test_decider.py`** - Tests decision logic and Kelly sizing
- **`test_executor.py`** - Tests execution validation and safety checks
- **`test_ai_nexus.py`** - Tests AI orchestration and budget tracking
- **`test_history_log.py`** - Tests Spark Plug history logging system
- **`test_tri_agent_cpu_v02.py`** - Tests Spark Plug v0.2 CPU functionality

### Integration Tests (`tests/integration/`)

Integration tests validate end-to-end workflows:

- **`test_alpha_to_execution.py`** - Full pipeline test (alpha → decider → executor)
- **`test_ai_intake.py`** - Tests /plan command handling
- **`test_coordination.py`** - Tests multi-agent coordination files

### Test Fixtures (`tests/fixtures/`)

Reusable test data and mock responses:

- `sample_polymarket_model.json` - Sample market data
- `mock_api_response.json` - Mock API responses
- `test_config.json` - Test configuration

## Test Coverage

Current test coverage targets:

- **Unit Tests**: 60%+ coverage
- **Core Modules**: 80%+ coverage (decider, executor)
- **Safety-Critical Code**: 100% coverage

View current coverage:

```bash
pytest tests/unit/ --cov=. --cov-report=term-missing
```

## Continuous Integration

Tests run automatically on:

- **Pull Requests**: All tests must pass before merge
- **Push to main/develop**: Full test suite + coverage report

See `.github/workflows/tests.yml` for CI configuration.

## Writing Tests

### Unit Test Template

```python
import pytest
from module import Function

class TestFunction:
    """Tests for Function"""
    
    def test_basic_functionality(self):
        """Test basic case"""
        result = Function(input_data)
        assert result == expected_output
    
    def test_edge_case(self):
        """Test edge case"""
        result = Function(edge_input)
        assert result is not None
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data["key"] == "value"
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

@patch('module.external_api_call')
def test_with_mock(mock_api):
    """Test with mocked external call"""
    mock_api.return_value = {"status": "success"}
    result = my_function()
    assert result["status"] == "success"
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_case():
    """Unit test"""
    pass

@pytest.mark.integration
def test_integration_case():
    """Integration test"""
    pass

@pytest.mark.slow
def test_slow_case():
    """Slow running test"""
    pass

@pytest.mark.requires_api
def test_with_api():
    """Requires external API"""
    pass
```

Run specific markers:

```bash
pytest -m unit        # Run only unit tests
pytest -m integration # Run only integration tests
pytest -m "not slow"  # Skip slow tests
```

## Best Practices

### Do's

✅ **Write tests first** for new functionality (TDD)  
✅ **Test edge cases** (null, empty, boundary values)  
✅ **Mock external dependencies** (APIs, databases)  
✅ **Keep tests isolated** (no shared state)  
✅ **Use descriptive test names** that explain what's tested  
✅ **Test both success and failure paths**

### Don'ts

❌ **Don't rely on test execution order**  
❌ **Don't test implementation details** (test behavior)  
❌ **Don't use real API credentials** in tests  
❌ **Don't skip broken tests** (fix or remove them)  
❌ **Don't make tests too complex** (keep them simple)

## Safety-Critical Tests

Tests for safety-critical components (executor validation, risk limits) must:

1. **Cover all safety checks** (confidence threshold, position size limits)
2. **Verify rejection of invalid actions** (low confidence, oversized positions)
3. **Test boundary conditions** (exactly at threshold values)
4. **Ensure DRYRUN is enforced** by default

See `tests/unit/test_executor.py` for examples.

## Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
pip install -r requirements-test.txt
```

### Coverage Data Not Generated

```bash
# Clean old coverage data
rm -rf .coverage htmlcov/

# Run tests with coverage
pytest tests/ --cov=.
```

### Tests Pass Locally But Fail in CI

- Check Python version (CI uses 3.11 and 3.12)
- Verify all dependencies in requirements-test.txt
- Check for hardcoded paths or environment-specific code

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
