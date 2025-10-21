# Contributing to WebSocket Notification Server

Thank you for your interest in contributing to the WebSocket Notification Server! This document provides guidelines and information for contributors.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd webSocket   ```

2. **Set up Python environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Install development tools**:
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Pytest**: Testing

Run all checks:
```bash
make lint
make format
make test
```

### Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a PR
- Aim for high test coverage (>90%)

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_connection_manager.py -v

# Run with coverage
pytest --cov=websocket_server --cov-report=html
```

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

Examples:
```
feat(websocket): add connection rate limiting
fix(shutdown): handle graceful shutdown timeout
docs(readme): update installation instructions
```

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   make test
   make lint
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): your change description"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements**:
   - Clear description of changes
   - All tests passing
   - Code review approval
   - Up-to-date with main branch

## Code Guidelines

### Python Style

- Follow PEP 8 (enforced by Black and Ruff)
- Use type hints for all functions and methods
- Write docstrings for public APIs
- Keep functions focused and small
- Use meaningful variable and function names

### Architecture

- Follow the existing project structure
- Use dependency injection where appropriate
- Implement proper error handling
- Add logging for important operations
- Write thread-safe code for concurrent operations

### Performance

- Consider performance implications of changes
- Use async/await for I/O operations
- Avoid blocking operations in async contexts
- Profile performance-critical code

## Reporting Issues

When reporting bugs or requesting features:

1. **Search existing issues** first
2. **Use issue templates** when available
3. **Provide clear reproduction steps** for bugs
4. **Include relevant logs and error messages**
5. **Specify your environment** (OS, Python version, etc.)

## Security

- Report security vulnerabilities privately
- Don't include sensitive data in issues or PRs
- Follow secure coding practices
- Validate all inputs

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new public APIs
- Update configuration documentation
- Include examples for new features

## Questions?

- Open a discussion for general questions
- Check existing documentation first
- Ask in issues for specific problems

Thank you for contributing!