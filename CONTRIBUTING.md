# Contributing to Shelter Discovery & Audit System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Shelter-updater.git
   cd Shelter-updater
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up your environment** following [docs/SETUP.md](docs/SETUP.md)

## Development Workflow

### 1. Create a Branch

Create a feature branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Your Changes

Follow the coding standards:

**Python Style**
- Follow PEP 8 style guide
- Use 4 spaces for indentation (configured in `.editorconfig`)
- Maximum line length: 120 characters
- Add type hints to function signatures
- Write descriptive docstrings for functions

**Example**:
```python
def fetch_shelter_data(shelter_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches shelter data from the database.

    Args:
        shelter_id: The unique building ID for the shelter

    Returns:
        Dictionary with shelter data, or None if not found
    """
    # Implementation...
```

### 3. Test Your Changes

Always test your changes before submitting:

**Run logic tests** (no API calls):
```bash
python tests/test_shelter_discovery.py
```

**Run environment tests** (uses real APIs - requires credentials):
```bash
python tests/test_local_env.py
```

**Syntax check**:
```bash
python -m py_compile new_shelters_global.py
python -m py_compile shelter_audit.py
python -m py_compile monitor_global_progress.py
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: descriptive summary of changes

- Detailed point 1
- Detailed point 2
- Explain why this change is needed"
```

**Good commit messages**:
- ✅ "Fix timeout handling in BBR API requests"
- ✅ "Add retry logic for connection errors"
- ✅ "Update documentation for new scheduling strategy"

**Bad commit messages**:
- ❌ "Fix bug"
- ❌ "Update code"
- ❌ "Changes"

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- **Title**: Clear, concise summary
- **Description**:
  - What changes were made
  - Why the changes were needed
  - Any breaking changes
  - Testing performed

## Contribution Areas

### Priority Areas

We welcome contributions in these areas:

1. **Bug Fixes**
   - API timeout handling improvements
   - Database connection error recovery
   - Edge case handling

2. **Testing**
   - Additional test coverage
   - Integration tests
   - Mock API tests

3. **Documentation**
   - Clarifying existing docs
   - Adding examples
   - Translating to other languages

4. **Performance**
   - Optimization of database queries
   - Reducing API call frequency
   - Memory usage improvements

5. **Features**
   - Additional data validation
   - Enhanced error reporting
   - Monitoring and alerting improvements

### What NOT to Change

Please avoid these changes without discussion:

- ❌ Changing core scheduling logic (3x daily runs)
- ❌ Modifying API endpoints or authentication
- ❌ Changing database schema
- ❌ Removing error handling or retries

If you want to make significant changes, **open an issue first** to discuss.

## Code Review Process

1. **Automated checks** must pass:
   - Syntax validation
   - All tests passing
   - No obvious security issues

2. **Manual review**:
   - Code follows style guidelines
   - Changes are well-documented
   - No breaking changes without discussion
   - Tests cover new functionality

3. **Feedback**: Address review comments and push updates

4. **Merge**: Once approved, maintainers will merge your PR

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Exact steps to trigger the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - Python version
   - OS (Windows, macOS, Linux)
   - Relevant logs/error messages
6. **Screenshots**: If applicable

### Feature Requests

When requesting features, include:

1. **Problem**: What problem does this solve?
2. **Proposed Solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Impact**: Who benefits from this feature?

## Questions?

- **Setup Issues**: Check [docs/SETUP.md](docs/SETUP.md) troubleshooting section
- **API Questions**: See [Datafordeler documentation](https://datafordeler.dk/vejledning)
- **Other Questions**: Open a GitHub issue with the `question` label

## Recognition

Contributors will be recognized in:
- Git commit history
- GitHub contributors page
- Release notes (for significant contributions)

Thank you for contributing! 🎉
