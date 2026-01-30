# Contributing to Telegram Multi-Account Message Sender

Thank you for your interest in contributing to the Telegram Multi-Account Message Sender! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:
1. Check if the issue already exists
2. Search through closed issues
3. Verify you're using the latest version

When creating an issue, please include:
- **Clear title**: Brief description of the issue
- **Description**: Detailed explanation of the problem
- **Steps to reproduce**: How to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, app version
- **Screenshots**: If applicable
- **Logs**: Relevant error messages or logs

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature already exists
2. Search through existing feature requests
3. Provide a clear description
4. Explain the use case and benefits
5. Consider implementation complexity

### Code Contributions

#### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   # Always start from the latest main branch
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   # Or for bug fixes: git checkout -b fix/issue-description
   # Or for docs: git checkout -b docs/update-readme
   # Or for chores: git checkout -b chore/cleanup-code
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**:
   ```bash
   pytest
   pytest --cov=app tests/  # With coverage
   ```

4. **Check code style**:
   ```bash
   black app/
   isort app/
   flake8 app/
   mypy app/
   ```

5. **Commit your changes** (using Conventional Commits):
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   # Or: fix: resolve bug description
   # Or: docs: update documentation
   # Or: chore: maintenance task
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** (see PR Flow section below)

#### Pull Request Guidelines

- **Clear title**: Describe what the PR does
- **Detailed description**: Explain the changes and why
- **Reference issues**: Link to related issues
- **Screenshots**: For UI changes
- **Tests**: Ensure all tests pass
- **Documentation**: Update docs if needed
- **Breaking changes**: Clearly mark any breaking changes

## 🌿 Branching Strategy

### Branch Naming Convention

We use a clear branching strategy to organize development:

- **`feature/`** - New features and enhancements
  - Example: `feature/add-campaign-scheduling`
  - Example: `feature/improve-ui-design`

- **`fix/`** - Bug fixes
  - Example: `fix/account-authorization-error`
  - Example: `fix/memory-leak-in-campaigns`

- **`docs/`** - Documentation updates
  - Example: `docs/update-api-documentation`
  - Example: `docs/add-installation-guide`

- **`chore/`** - Maintenance tasks, refactoring, dependencies
  - Example: `chore/update-dependencies`
  - Example: `chore/refactor-settings-service`

- **`test/`** - Adding or updating tests
  - Example: `test/add-campaign-tests`
  - Example: `test/increase-coverage`

### Branch Workflow

1. **Always start from `main`**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create your branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Work on your changes** and commit frequently with clear messages

4. **Keep your branch updated**:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-feature-name
   git merge main  # or git rebase main
   ```

5. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

## 🔄 Pull Request (PR) Flow

### Before Creating a PR

1. **Ensure your branch is up to date**:
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/your-feature-name
   git merge main
   ```

2. **Run all checks**:
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black app/ --check
   isort app/ --check
   flake8 app/
   mypy app/
   ```

3. **Update documentation** if your changes affect:
   - User-facing features
   - API changes
   - Configuration options
   - Installation process

### Creating a Pull Request

1. **Go to GitHub** and click "New Pull Request"

2. **Select your branch** to merge into `main`

3. **Fill out the PR template** with:
   - Clear title (use Conventional Commits format)
   - Description of changes
   - Related issues (use `Closes #123` or `Fixes #456`)
   - Screenshots (for UI changes)
   - Testing notes

4. **Mark as Draft** if work is in progress, or **Ready for Review** when complete

### PR Review Process

1. **Automated Checks**: CI/CD will run tests and linting
   - All checks must pass before merge
   - Fix any failing checks

2. **Code Review**: At least one maintainer must approve
   - Address review comments
   - Make requested changes
   - Re-request review when ready

3. **Merge Requirements**:
   - All CI checks passing
   - At least one approval
   - No merge conflicts
   - Up to date with `main` branch

4. **Merge Options**:
   - **Squash and merge** (preferred for feature branches)
   - **Merge commit** (for complex features)
   - **Rebase and merge** (for clean history)

### PR Best Practices

- **Keep PRs focused**: One feature or fix per PR
- **Keep PRs small**: Easier to review and merge
- **Write clear descriptions**: Explain what and why
- **Link related issues**: Use GitHub issue linking
- **Update CHANGELOG.md**: Add entry for user-facing changes
- **Respond to feedback**: Engage with reviewers

## 📋 Development Guidelines

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

#### Running Code Quality Checks

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint code
flake8 app/

# Type checking
mypy app/

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

### Project Structure

```
app/
├── core/           # Core functionality
├── gui/            # GUI components
├── models/         # Database models
├── services/       # Business logic
├── utils/          # Utility functions
└── translations/   # Translation files
```

### Architecture Principles

- **MVC Pattern**: Model-View-Controller architecture
- **Service Layer**: Business logic in services
- **Dependency Injection**: Loose coupling between components
- **Error Handling**: Comprehensive error handling
- **Logging**: Detailed logging for debugging
- **Testing**: Unit and integration tests

### Database Changes

When modifying database models:
1. Update the model in `app/models/`
2. Create a migration script
3. Test the migration
4. Update documentation

### Translation Updates

When adding new text:
1. Add the key to `app/translations/en.json`
2. Add translations to all language files
3. Use the `_()` function in code
4. Test with different languages

### UI Guidelines

- **Consistent styling**: Follow existing UI patterns
- **Responsive design**: Ensure UI works on different screen sizes
- **Accessibility**: Consider accessibility requirements
- **User experience**: Prioritize user experience
- **Error handling**: Provide clear error messages

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── ui/            # UI tests
└── fixtures/      # Test fixtures
```

### Writing Tests

- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **UI tests**: Test user interface functionality
- **Coverage**: Aim for high test coverage

### Test Examples

```python
def test_campaign_creation():
    """Test campaign creation functionality."""
    campaign = Campaign(
        name="Test Campaign",
        message_text="Test message"
    )
    assert campaign.name == "Test Campaign"
    assert campaign.message_text == "Test message"

def test_translation_system():
    """Test translation system."""
    translation_manager = TranslationManager()
    translation_manager.set_language("en")
    text = translation_manager.get_text("common.save")
    assert text == "Save"
```

## 📚 Documentation

### Documentation Standards

- **Clear and concise**: Write clear, easy-to-understand documentation
- **Examples**: Include code examples
- **Up-to-date**: Keep documentation current
- **Comprehensive**: Cover all aspects of the project

### Types of Documentation

- **API Documentation**: Function and class documentation
- **User Guide**: End-user documentation
- **Developer Guide**: Developer documentation
- **README**: Project overview and quick start
- **Changelog**: Version history and changes

### Writing Documentation

```python
def create_campaign(name: str, message_text: str) -> Campaign:
    """
    Create a new campaign.
    
    Args:
        name: Campaign name
        message_text: Message content
        
    Returns:
        Created campaign instance
        
    Raises:
        ValueError: If name is empty
        ValidationError: If message_text is invalid
    """
    if not name:
        raise ValueError("Campaign name cannot be empty")
    
    campaign = Campaign(name=name, message_text=message_text)
    return campaign
```

## 🐛 Bug Reports

### Before Reporting

1. **Check existing issues**: Search for similar issues
2. **Update to latest version**: Ensure you're using the latest version
3. **Check documentation**: Review relevant documentation
4. **Test in clean environment**: Test in a fresh installation

### Bug Report Template

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 10, macOS 12, Ubuntu 20.04]
- Python Version: [e.g. 3.10.0]
- App Version: [e.g. 1.2.0]

**Additional Context**
Add any other context about the problem here.
```

## ✨ Feature Requests

### Before Requesting

1. **Check existing features**: Ensure the feature doesn't already exist
2. **Search requests**: Look for similar feature requests
3. **Consider alternatives**: Think about workarounds
4. **Assess complexity**: Consider implementation complexity

### Feature Request Template

```markdown
**Feature Description**
A clear and concise description of the feature you'd like to see.

**Use Case**
Describe the use case and how this feature would be beneficial.

**Proposed Solution**
A clear and concise description of what you want to happen.

**Alternatives**
Describe any alternative solutions or features you've considered.

**Additional Context**
Add any other context or screenshots about the feature request here.
```

## 🔒 Security

### Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public issue
2. Email us at security@voxhash.dev
3. Include detailed information about the vulnerability
4. Allow time for us to address the issue before disclosure

### Security Guidelines

- **Input validation**: Always validate user input
- **Authentication**: Implement proper authentication
- **Authorization**: Check permissions before actions
- **Data protection**: Protect sensitive data
- **Error handling**: Don't expose sensitive information in errors

## 📝 Commit Messages

### Commit Message Format (Conventional Commits)

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): brief description

Detailed description of changes (optional)

BREAKING CHANGE: description (if applicable)

Closes #123
```

### Commit Types

- **`feat`**: New feature (triggers minor version bump)
- **`fix`**: Bug fix (triggers patch version bump)
- **`docs`**: Documentation changes only
- **`style`**: Code style changes (formatting, missing semicolons, etc.)
- **`refactor`**: Code refactoring (no feature change or bug fix)
- **`perf`**: Performance improvements
- **`test`**: Adding or updating tests
- **`chore`**: Maintenance tasks (dependencies, build config, etc.)
- **`ci`**: CI/CD configuration changes
- **`build`**: Build system or dependency changes

### Scope (Optional)

Scope indicates the area of the codebase:
- `accounts` - Account management
- `campaigns` - Campaign functionality
- `templates` - Template system
- `ui` - User interface
- `api` - API changes
- `docs` - Documentation
- `config` - Configuration

### Examples

```
feat(campaigns): add scheduling functionality

Add ability to schedule campaigns for specific times with timezone support.
Includes UI updates and backend logic for scheduling.

Closes #45
```

```
fix(accounts): resolve authorization timeout issue

Fix issue where account authorization would timeout after 30 seconds.
Increased timeout to 60 seconds and added retry logic.

Fixes #67
```

```
docs: update installation guide

Add Windows-specific installation instructions and troubleshooting section.
```

### Examples

```
feat(campaigns): add campaign scheduling functionality

Add ability to schedule campaigns for specific times with timezone support.
Includes UI updates and backend logic for scheduling.

Closes #45
```

```
fix(accounts): resolve account authorization issue

Fix issue where accounts would fail to authorize due to session handling.
Updated session management logic and error handling.

Fixes #67
```

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version numbers updated
- [ ] Release notes prepared
- [ ] Builds tested
- [ ] Release created

## 🤔 Questions?

If you have questions about contributing:

- **GitHub Discussions**: Use GitHub Discussions for general questions
- **Issues**: Create an issue for specific problems
- **Email**: Contact us at contact@voxhash.dev

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the BSD 3-Clause License.

## 🙏 Recognition

Contributors will be recognized in:
- **README**: Listed in the contributors section
- **Release Notes**: Mentioned in relevant releases
- **Changelog**: Credited for their contributions

Thank you for contributing to the Telegram Multi-Account Message Sender! 🎉