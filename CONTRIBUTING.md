# Contributing to Telegram Multi-Account Message Sender

Thank you for your interest in contributing to the Telegram Multi-Account Message Sender project! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)
- [Documentation](#documentation)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Guidelines](#commit-guidelines)
- [Release Process](#release-process)
- [Community Guidelines](#community-guidelines)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming and inclusive environment for all contributors. By participating, you agree to uphold this code.

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, education, socio-economic status, nationality
- Personal appearance, race, religion, or sexual identity and orientation

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

Examples of unacceptable behavior include:

- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers are responsible for clarifying and enforcing our standards of acceptable behavior and will take appropriate and fair corrective action in response to any behavior they deem inappropriate.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.10 or higher
- Git
- A GitHub account
- Basic knowledge of Python and PyQt5
- Understanding of the project's purpose and goals

### Fork the Repository

1. Go to the [project repository](https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender)
2. Click the "Fork" button in the top-right corner
3. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

### Set Up Upstream Remote

```bash
git remote add upstream https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
```

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 4. Configure Environment

```bash
cp example_files/env_template.txt .env
# Edit .env with your configuration
```

### 5. Run Tests

```bash
pytest
```

### 6. Start Development

```bash
python main.py
```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix existing issues
- **Feature Additions**: Add new functionality
- **Documentation**: Improve or add documentation
- **Testing**: Add or improve tests
- **Performance**: Optimize existing code
- **UI/UX**: Improve user interface and experience
- **Translations**: Add or improve translations
- **Examples**: Add code examples or tutorials

### Before Contributing

1. **Check Existing Issues**: Look for existing issues or discussions
2. **Discuss Major Changes**: Open an issue for significant changes
3. **Follow the Style Guide**: Adhere to our code style guidelines
4. **Write Tests**: Include tests for new functionality
5. **Update Documentation**: Update relevant documentation

### Contribution Process

1. **Create a Branch**: Create a feature branch from `main`
2. **Make Changes**: Implement your changes
3. **Write Tests**: Add tests for your changes
4. **Update Documentation**: Update relevant documentation
5. **Run Tests**: Ensure all tests pass
6. **Format Code**: Run code formatting tools
7. **Commit Changes**: Commit with descriptive messages
8. **Push Changes**: Push to your fork
9. **Create Pull Request**: Open a pull request

## Pull Request Process

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code has been performed
- [ ] Code has been commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation have been made
- [ ] Changes generate no new warnings
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published

### Pull Request Template

When creating a pull request, use the provided template:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Related Issues
Fixes #(issue number)

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing performed

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Checklist
- [ ] Code follows the project's style guidelines
- [ ] Self-review of code has been performed
- [ ] Code has been commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation have been made
- [ ] Changes generate no new warnings
- [ ] New and existing unit tests pass locally
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automated Checks**: CI/CD runs automatically
2. **Code Review**: At least one reviewer required
3. **Testing**: All tests must pass
4. **Documentation**: Documentation must be updated
5. **Approval**: At least one approval required
6. **Merge**: Maintainer merges the PR

## Issue Reporting

### Before Creating an Issue

1. **Search Existing Issues**: Check if the issue already exists
2. **Check Documentation**: Look for solutions in the documentation
3. **Try Troubleshooting**: Follow the troubleshooting guide
4. **Gather Information**: Collect relevant information

### Issue Templates

We provide templates for different types of issues:

- **Bug Report**: For reporting bugs
- **Feature Request**: For requesting new features
- **Documentation**: For documentation issues
- **Question**: For asking questions

### Bug Report Template

```markdown
## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Environment
- OS: [e.g. Windows 10, macOS 12, Ubuntu 20.04]
- Python Version: [e.g. 3.10.0]
- Application Version: [e.g. 1.0.0]
- Browser: [e.g. Chrome 91, Firefox 89]

## Screenshots
If applicable, add screenshots to help explain your problem.

## Additional Context
Add any other context about the problem here.
```

### Feature Request Template

```markdown
## Feature Description
A clear and concise description of the feature you'd like to see.

## Problem Statement
Is your feature request related to a problem? Please describe.
A clear and concise description of what the problem is.

## Proposed Solution
Describe the solution you'd like to see implemented.

## Alternatives Considered
Describe any alternative solutions or features you've considered.

## Additional Context
Add any other context or screenshots about the feature request here.
```

## Feature Requests

### Guidelines for Feature Requests

1. **Check Existing Issues**: Look for similar feature requests
2. **Provide Context**: Explain why the feature is needed
3. **Be Specific**: Provide detailed descriptions
4. **Consider Implementation**: Think about how it might be implemented
5. **Provide Examples**: Give examples of how the feature would work

### Feature Request Process

1. **Create Issue**: Use the feature request template
2. **Discussion**: Engage in discussion with maintainers
3. **Approval**: Wait for maintainer approval
4. **Implementation**: Implement the feature
5. **Testing**: Test the feature thoroughly
6. **Documentation**: Update documentation
7. **Pull Request**: Submit a pull request

## Bug Reports

### Guidelines for Bug Reports

1. **Reproducible**: Provide steps to reproduce the bug
2. **Specific**: Be specific about the problem
3. **Environment**: Include environment details
4. **Screenshots**: Add screenshots if applicable
5. **Logs**: Include relevant log entries

### Bug Report Process

1. **Create Issue**: Use the bug report template
2. **Investigation**: Maintainers investigate the issue
3. **Reproduction**: Verify the bug can be reproduced
4. **Fix**: Implement a fix
5. **Testing**: Test the fix thoroughly
6. **Release**: Include fix in next release

## Documentation

### Documentation Guidelines

1. **Clear and Concise**: Write clear, concise documentation
2. **Up-to-date**: Keep documentation current
3. **Comprehensive**: Cover all aspects of the feature
4. **Examples**: Provide code examples
5. **Formatting**: Use proper markdown formatting

### Documentation Types

- **API Documentation**: Document all APIs
- **User Guide**: User-facing documentation
- **Developer Guide**: Developer documentation
- **README**: Project overview and setup
- **Changelog**: Record of changes
- **FAQ**: Frequently asked questions

### Documentation Process

1. **Identify Need**: Identify documentation needs
2. **Write Content**: Write the documentation
3. **Review**: Have others review the content
4. **Update**: Update existing documentation
5. **Maintain**: Keep documentation current

## Testing

### Testing Guidelines

1. **Write Tests**: Write tests for all new functionality
2. **Test Coverage**: Aim for high test coverage
3. **Test Types**: Include unit, integration, and UI tests
4. **Test Data**: Use appropriate test data
5. **Test Environment**: Test in different environments

### Test Types

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **UI Tests**: Test user interface components
- **Performance Tests**: Test performance and load
- **Security Tests**: Test security aspects

### Testing Process

1. **Write Tests**: Write tests for new functionality
2. **Run Tests**: Run tests locally
3. **Fix Issues**: Fix any test failures
4. **CI/CD**: Ensure tests pass in CI/CD
5. **Review**: Have tests reviewed

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: 100 characters (instead of 79)
- **Import Sorting**: Use isort with black compatibility
- **Type Hints**: Use type hints for all functions and methods
- **Docstrings**: Use Google-style docstrings

### Code Formatting

```bash
# Format code with Black
black app/

# Sort imports with isort
isort app/

# Check code style with flake8
flake8 app/

# Type checking with mypy
mypy app/
```

### Example Code Style

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum

class AccountStatus(str, Enum):
    """Account status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class Account(SQLModel, table=True):
    """Account model for storing Telegram account information."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(unique=True, index=True)
    username: Optional[str] = None
    status: AccountStatus = AccountStatus.OFFLINE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def is_online(self) -> bool:
        """Check if account is online."""
        return self.status == AccountStatus.ONLINE
    
    def get_display_name(self) -> str:
        """Get display name for UI."""
        if self.username:
            return f"@{self.username}"
        return self.phone_number
```

## Commit Guidelines

### Commit Message Format

We use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools

### Examples

```bash
feat(accounts): add account authorization functionality
fix(campaigns): resolve campaign start time issue
docs(api): update API documentation
style(ui): improve button styling
refactor(database): optimize database queries
perf(messages): improve message sending performance
test(campaigns): add campaign creation tests
chore(deps): update dependencies
```

### Commit Process

1. **Stage Changes**: `git add .`
2. **Commit**: `git commit -m "feat(accounts): add account authorization"`
3. **Push**: `git push origin feature-branch`
4. **Create PR**: Open a pull request

## Release Process

### Release Types

- **Major**: Significant new features or breaking changes
- **Minor**: New features or significant improvements
- **Patch**: Bug fixes and minor improvements
- **Pre-release**: Alpha, beta, or release candidate versions

### Release Schedule

- **Major releases**: Every 6 months
- **Minor releases**: Every 2-3 months
- **Patch releases**: As needed for bug fixes
- **Pre-releases**: Before major releases

### Release Process

1. **Version Bump**: Update version numbers
2. **Changelog**: Update changelog
3. **Testing**: Run full test suite
4. **Documentation**: Update documentation
5. **Release**: Create release
6. **Announcement**: Announce the release

## Community Guidelines

### Communication

- **Be Respectful**: Treat everyone with respect
- **Be Constructive**: Provide constructive feedback
- **Be Patient**: Be patient with others
- **Be Helpful**: Help others when possible
- **Be Professional**: Maintain professional communication

### Getting Help

- **Documentation**: Check the documentation first
- **Issues**: Search existing issues
- **Discussions**: Use GitHub discussions
- **Community**: Engage with the community
- **Maintainers**: Contact maintainers if needed

### Recognition

- **Contributors**: All contributors are recognized
- **Maintainers**: Maintainers are acknowledged
- **Community**: Community members are valued
- **Feedback**: Feedback is appreciated
- **Suggestions**: Suggestions are welcome

## Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Development branch
- **feature/**: Feature branches
- **bugfix/**: Bug fix branches
- **hotfix/**: Hotfix branches

### Branch Naming

- **feature/**: `feature/account-authorization`
- **bugfix/**: `bugfix/campaign-start-issue`
- **hotfix/**: `hotfix/security-patch`
- **docs/**: `docs/api-documentation`
- **test/**: `test/campaign-tests`

### Merge Strategy

- **Squash and Merge**: For feature branches
- **Rebase and Merge**: For bug fix branches
- **Merge Commit**: For hotfix branches

## Code Review Process

### Review Guidelines

1. **Be Constructive**: Provide constructive feedback
2. **Be Specific**: Be specific about issues
3. **Be Respectful**: Be respectful in comments
4. **Be Thorough**: Review thoroughly
5. **Be Timely**: Respond in a timely manner

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes
- [ ] Performance is acceptable
- [ ] Security is considered
- [ ] Error handling is appropriate
- [ ] Logging is adequate

## Continuous Integration

### CI/CD Pipeline

1. **Code Quality**: Run code quality checks
2. **Testing**: Run automated tests
3. **Building**: Build packages and installers
4. **Deployment**: Deploy to staging/production
5. **Monitoring**: Monitor deployment

### Automated Checks

- **Code Formatting**: Black and isort
- **Linting**: flake8 and mypy
- **Testing**: pytest with coverage
- **Security**: Security scanning
- **Performance**: Performance testing

## Security

### Security Guidelines

1. **Input Validation**: Validate all input
2. **Output Encoding**: Encode output properly
3. **Authentication**: Implement proper authentication
4. **Authorization**: Implement proper authorization
5. **Data Protection**: Protect sensitive data

### Security Process

1. **Security Review**: Review code for security issues
2. **Vulnerability Scanning**: Scan for vulnerabilities
3. **Penetration Testing**: Perform penetration testing
4. **Security Updates**: Apply security updates
5. **Incident Response**: Respond to security incidents

## Performance

### Performance Guidelines

1. **Optimize Queries**: Optimize database queries
2. **Use Caching**: Implement caching where appropriate
3. **Minimize I/O**: Minimize input/output operations
4. **Use Async**: Use async operations where possible
5. **Monitor Performance**: Monitor performance metrics

### Performance Process

1. **Performance Testing**: Test performance regularly
2. **Profiling**: Profile code for bottlenecks
3. **Optimization**: Optimize identified bottlenecks
4. **Monitoring**: Monitor performance in production
5. **Scaling**: Scale as needed

## Conclusion

Thank you for contributing to the Telegram Multi-Account Message Sender project! Your contributions help make this project better for everyone.

If you have any questions or need help, please don't hesitate to reach out to the maintainers or the community.

Remember: This project is for educational and legitimate business purposes only. Always comply with Telegram's Terms of Service and applicable laws.

Happy contributing! 🚀