# 🤝 Contributing to Telegram Multi-Account Message Sender

Thank you for your interest in contributing to this project! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic knowledge of Python, PyQt5, and Telegram API
- Understanding of async/await patterns

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

## 🛠️ Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **ruff** for linting
- **mypy** for type checking
- **pytest** for testing

Run all checks before committing:
```bash
black app/ tests/
isort app/ tests/
ruff check app/ tests/
mypy app/
pytest
```

### Testing

Write tests for new features and bug fixes:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_spintax.py

# Run integration tests
pytest tests/integration/
```

### Git Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

Examples:
```
feat(accounts): add proxy support for accounts
fix(campaigns): resolve scheduling timezone issue
docs: update installation instructions
```

## 📁 Project Structure

```
app/
├── core/           # Core business logic
│   ├── engine.py   # Main orchestration
│   ├── telethon_client.py  # Telegram client management
│   ├── throttler.py        # Rate limiting
│   ├── spintax.py          # Message personalization
│   ├── compliance.py       # Safety checks
│   └── analytics.py        # Performance tracking
├── gui/            # User interface
│   ├── main.py     # Main window
│   ├── theme.py    # Theme management
│   └── widgets/    # UI components
├── models/         # Database models
├── services/       # Core services
└── utils/          # Utility functions

tests/
├── unit/           # Unit tests
└── integration/    # Integration tests

scripts/            # Build and utility scripts
assets/             # Static assets
docs/               # Documentation
```

## 🎯 Areas for Contribution

### High Priority
- [ ] Account management UI improvements
- [ ] Campaign builder enhancements
- [ ] Recipient management features
- [ ] Log viewer improvements
- [ ] Settings panel enhancements

### Medium Priority
- [ ] Template management system
- [ ] Analytics dashboard
- [ ] Export/import functionality
- [ ] Plugin system
- [ ] API documentation

### Low Priority
- [ ] Mobile app
- [ ] Web interface
- [ ] Advanced analytics
- [ ] Multi-language support

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to reproduce the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: OS, Python version, app version
6. **Logs**: Relevant log output
7. **Screenshots**: If applicable

## 💡 Feature Requests

When requesting features, please include:

1. **Description**: Clear description of the feature
2. **Use case**: Why this feature is needed
3. **Proposed solution**: How you think it should work
4. **Alternatives**: Other solutions you've considered
5. **Additional context**: Any other relevant information

## 🔒 Security

If you discover a security vulnerability, please:

1. **DO NOT** create a public issue
2. Email us at security@voxhash.dev
3. Include detailed information about the vulnerability
4. We will respond within 48 hours

## 📝 Documentation

We welcome contributions to documentation:

- README improvements
- Code comments
- API documentation
- User guides
- Video tutorials

## 🏷️ Labels

We use labels to categorize issues and pull requests:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority: high`: High priority
- `priority: medium`: Medium priority
- `priority: low`: Low priority

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior

- Be respectful and inclusive
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory language
- Personal attacks or political discussions
- Public or private harassment
- Publishing private information without permission
- Other unprofessional conduct

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: contact@voxhash.dev
- **Discord**: [Join our Discord server](https://discord.gg/voxhash)

## 🎉 Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Social media (with permission)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🧪 Testing Guidelines

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### GUI Tests
```bash
# Test the main application
python main.py

# Test specific components
python -m pytest tests/unit/test_gui.py
```

### Database Tests
```bash
# Test database operations
python -m pytest tests/unit/test_models.py
```

## 🔧 Development Tools

### Code Quality
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📋 Checklist for Contributors

Before submitting a PR, make sure:

- [ ] Code follows the style guidelines
- [ ] Tests pass locally
- [ ] Documentation is updated
- [ ] Changes are tested with different scenarios
- [ ] Cross-platform compatibility is maintained
- [ ] Commit messages follow the convention
- [ ] PR description is clear and detailed
- [ ] Related issues are linked
- [ ] Security considerations are addressed

## 🎯 Quick Start for New Contributors

1. **Read the documentation**
2. **Set up the development environment**
3. **Look for "good first issue" labels**
4. **Start with small contributions**
5. **Ask questions if you need help**
6. **Have fun contributing!**

## 🎬 Project Philosophy

Telegram Multi-Account Message Sender is designed with these core principles:

- **Professional**: High-quality implementation and user experience
- **Safe**: Built-in safety features and compliance controls
- **Efficient**: Fast, responsive, and resource-efficient
- **User-Friendly**: Intuitive and easy to use
- **Reliable**: Stable, consistent, and dependable
- **Secure**: Privacy-first design with encrypted storage

When contributing, please keep these principles in mind and help us maintain the project's high standards!

---

## 🤖 A Message from the Team

"Hey there, future contributor! We're super excited that you want to help make Telegram Multi-Account Message Sender even better! Whether you're fixing bugs, adding features, or improving the user experience, every contribution helps us create the best automation tool possible.

Don't be afraid to ask questions - we're here to help! And remember, coding is like magic... but with more debugging!

Let's build something amazing together! ✨"

---

**Made with ❤️ by VoxHash and the amazing community**

*Telegram Multi-Account Message Sender is ready to work with you!* 🚀