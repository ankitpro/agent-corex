# Contributing to Agent-Core

Thank you for your interest in contributing to Agent-Core! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip or conda

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/agent-corex.git
cd agent-corex

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest pytest-cov black flake8
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Write your code and ensure it follows the project's style guide.

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_retrieval.py -v

# Run with coverage
pytest tests/ --cov=packages
```

### 4. Code Style

```bash
# Format code with black
black packages/ apps/ tests/

# Check linting
flake8 packages/ apps/ tests/
```

### 5. Commit Changes

```bash
git add .
git commit -m "Add feature: descriptive commit message"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Contribution Guidelines

### Code Style

- **Language**: Python 3.8+
- **Formatter**: Black
- **Linter**: Flake8
- **Docstrings**: Google-style docstrings

### Commit Messages

Use clear, descriptive commit messages:

```
Add hybrid ranking method

- Combines keyword and embedding scoring
- Includes fallback to keyword-only if model unavailable
- Adds comprehensive tests

Fixes #123
```

### Pull Request Guidelines

1. **Title**: Clear, descriptive title
2. **Description**: Explain what and why
3. **Tests**: Include tests for new functionality
4. **Documentation**: Update README if needed
5. **No Breaking Changes**: Maintain backward compatibility

### Testing Requirements

- All new features must have tests
- Minimum 80% code coverage
- Tests should cover edge cases
- Use descriptive test names

Example test:

```python
def test_hybrid_ranking_finds_semantic_matches(self):
    """Verify that hybrid ranking catches semantically related tools."""
    results = rank_tools("modify file", tools, method="hybrid")
    assert len(results) > 0
    # Should find edit_file even though "modify" != "edit"
```

## Areas for Contribution

### High Priority

- [ ] Fine-tuned embedding models for specific domains
- [ ] Performance optimizations
- [ ] Documentation improvements
- [ ] Bug fixes

### Medium Priority

- [ ] Cross-lingual semantic search
- [ ] Tool usage frequency weighting
- [ ] Caching layer
- [ ] Tool discovery UI

### Lower Priority

- [ ] Custom model selection
- [ ] Advanced filtering
- [ ] Analytics dashboard
- [ ] Integration examples

## Reporting Issues

### Bug Reports

Include:
- Python version
- Environment (OS, hardware)
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

### Feature Requests

Include:
- Use case/motivation
- Proposed solution
- Alternatives considered
- Potential impact

## Code Review Process

1. **Automated Checks**: Tests and linting must pass
2. **Code Review**: At least one maintainer review
3. **Feedback**: Address review comments
4. **Merge**: Squash and merge to main

## Development Tips

### Debugging

```python
# Add debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use print statements
print(f"Debug: {variable}")
```

### Performance Testing

```python
import time

start = time.time()
# code to test
end = time.time()
print(f"Time: {end - start:.4f}s")
```

### Memory Profiling

```bash
pip install memory-profiler
python -m memory_profiler script.py
```

## Common Tasks

### Adding a New Ranking Method

1. Create method in `ranker.py`
2. Add tests in `test_retrieval.py`
3. Document in README
4. Update API if needed

### Adding a New Tool Type

1. Extend `ToolRegistry` or create new class
2. Add corresponding tests
3. Update documentation
4. Add integration tests

### Updating Dependencies

```bash
# Check outdated packages
pip list --outdated

# Update requirements.txt
pip freeze > requirements.txt

# Test with new versions
pytest tests/
```

## Release Process

Releases are managed by maintainers:

1. Update version in `setup.py`
2. Update CHANGELOG
3. Create release commit
4. Tag with version
5. Push to GitHub
6. Create GitHub release

## Getting Help

- **Issues**: Ask questions in issue tracker
- **Discussions**: Use GitHub discussions
- **Email**: Contact maintainers directly

## Code of Conduct

- Be respectful and inclusive
- No harassment or discrimination
- Constructive feedback only
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub acknowledgments

Thank you for contributing to Agent-Core!
