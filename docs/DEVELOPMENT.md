# Development Guide

This guide provides information for developers who want to contribute to or extend the Telegram Multi-Account Message Sender application.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Building](#building)
- [Contributing](#contributing)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Security Considerations](#security-considerations)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment (recommended)
- Code editor (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git
   cd Telegram-Multi-Account-Message-Sender
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set Up Pre-commit Hooks**:
   ```bash
   pre-commit install
   ```

5. **Configure Environment**:
   ```bash
   cp example_files/env_template.txt .env
   # Edit .env with your configuration
   ```

### Development Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **pre-commit**: Git hooks

## Project Structure

```
telegram-multi-account-sender/
├── app/                          # Main application code
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── spintax.py           # Spintax processing
│   │   └── telegram_client.py   # Telegram client management
│   ├── gui/                      # GUI components
│   │   ├── __init__.py
│   │   ├── main.py              # Main window
│   │   ├── theme.py             # Theme management
│   │   └── widgets/             # GUI widgets
│   │       ├── __init__.py
│   │       ├── account_widget.py
│   │       ├── campaign_widget.py
│   │       ├── log_widget.py
│   │       ├── recipient_widget.py
│   │       ├── settings_widget.py
│   │       └── template_widget.py
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── account.py
│   │   ├── campaign.py
│   │   ├── recipient.py
│   │   ├── template.py
│   │   └── send_log.py
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── campaign_manager.py
│   │   ├── database.py
│   │   ├── logger.py
│   │   ├── message_engine.py
│   │   ├── settings.py
│   │   └── translation.py
│   └── translations/             # Translation files
│       ├── en.json
│       ├── fr.json
│       ├── es.json
│       └── ...
├── docs/                         # Documentation
│   ├── README.md
│   ├── API.md
│   ├── USER_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── DEVELOPMENT.md
├── example_files/                # Example files
│   ├── env_template.txt
│   ├── recipients_example.csv
│   ├── templates_example.csv
│   └── ...
├── tests/                        # Test files
│   ├── __init__.py
│   ├── test_accounts.py
│   ├── test_campaigns.py
│   └── ...
├── .github/                      # GitHub configuration
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── release.yml
│   └── ISSUE_TEMPLATE/
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── MANIFEST.in
├── main.py
└── build_installers.py
```

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

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_campaigns.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_campaigns.py::test_create_campaign
```

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from app.models import Campaign, CampaignStatus
from app.services import CampaignManager

class TestCampaignManager:
    """Test cases for CampaignManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.campaign_manager = CampaignManager()
        self.test_campaign = Campaign(
            name="Test Campaign",
            status=CampaignStatus.DRAFT
        )
    
    def test_create_campaign(self):
        """Test campaign creation."""
        # Arrange
        campaign_data = {
            "name": "Test Campaign",
            "status": CampaignStatus.DRAFT
        }
        
        # Act
        result = self.campaign_manager.create_campaign(campaign_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Campaign"
        assert result.status == CampaignStatus.DRAFT
    
    def test_start_campaign(self):
        """Test campaign starting."""
        # Arrange
        campaign_id = 1
        
        # Act
        result = self.campaign_manager.start_campaign(campaign_id)
        
        # Assert
        assert result is True
    
    @patch('app.services.campaign_manager.get_session')
    def test_start_campaign_with_mock(self, mock_get_session):
        """Test campaign starting with mocked session."""
        # Arrange
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        campaign_id = 1
        
        # Act
        result = self.campaign_manager.start_campaign(campaign_id)
        
        # Assert
        assert result is True
        mock_session.get.assert_called_once()
```

### Test Coverage

We aim for high test coverage:

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **UI Tests**: Test GUI components (using pytest-qt)
- **End-to-End Tests**: Test complete workflows

### Mocking

Use mocking for external dependencies:

```python
from unittest.mock import Mock, patch, MagicMock

# Mock external API calls
@patch('app.services.telegram_client.TelegramClient')
def test_send_message(self, mock_client):
    # Mock the client
    mock_client_instance = Mock()
    mock_client.return_value = mock_client_instance
    
    # Test the function
    result = send_message("+1234567890", "Hello World")
    
    # Assert the mock was called
    mock_client_instance.send_message.assert_called_once()
```

## Building

### Building the Package

```bash
# Build source and wheel distributions
python -m build

# Build only wheel
python -m build --wheel

# Build only source distribution
python -m build --sdist
```

### Building Installers

```bash
# Build all installers
python build_installers.py

# Build specific platform installer
python build_installers.py --platform windows
python build_installers.py --platform macos
python build_installers.py --platform linux
```

### Building Documentation

```bash
# Build Sphinx documentation (if using Sphinx)
sphinx-build -b html docs/ docs/_build/html

# Build API documentation
pydoc -w app.models
pydoc -w app.services
```

## Contributing

### Contribution Workflow

1. **Fork the Repository**: Create your own fork
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Implement your changes
4. **Write Tests**: Add tests for your changes
5. **Run Tests**: Ensure all tests pass
6. **Format Code**: Run Black and isort
7. **Commit Changes**: `git commit -m 'Add amazing feature'`
8. **Push to Branch**: `git push origin feature/amazing-feature`
9. **Create Pull Request**: Open a PR on GitHub

### Pull Request Guidelines

- **Clear Description**: Describe what the PR does
- **Related Issues**: Link to related issues
- **Tests**: Include tests for new functionality
- **Documentation**: Update documentation if needed
- **Breaking Changes**: Clearly mark breaking changes

### Code Review Process

1. **Automated Checks**: CI/CD runs automatically
2. **Manual Review**: At least one reviewer required
3. **Testing**: All tests must pass
4. **Documentation**: Documentation must be updated
5. **Approval**: At least one approval required

## Architecture

### Design Patterns

- **MVC Pattern**: Model-View-Controller separation
- **Service Layer**: Business logic in services
- **Repository Pattern**: Data access abstraction
- **Observer Pattern**: Event handling with Qt signals
- **Factory Pattern**: Object creation

### Component Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GUI Layer     │    │  Service Layer  │    │   Data Layer    │
│                 │    │                 │    │                 │
│  MainWindow     │◄──►│ CampaignManager │◄──►│   Database      │
│  Widgets        │    │ MessageEngine   │    │   Models        │
│  Dialogs        │    │ TelegramClient  │    │   Migrations    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **User Input**: User interacts with GUI
2. **Event Handling**: Qt signals handle events
3. **Service Layer**: Business logic processes requests
4. **Data Layer**: Database operations
5. **Response**: Results returned to GUI
6. **UI Update**: GUI updates with results

## Database Schema

### Entity Relationships

```
Account (1) ──── (N) SendLog
Campaign (1) ──── (N) SendLog
Recipient (1) ──── (N) SendLog
RecipientList (1) ──── (N) Recipient
MessageTemplate (1) ──── (N) Campaign
```

### Migration Strategy

1. **Version Control**: Track schema versions
2. **Backward Compatibility**: Maintain compatibility
3. **Data Migration**: Migrate existing data
4. **Rollback Support**: Support rollbacks

### Database Operations

```python
from sqlmodel import Session, select
from app.services.database import get_session
from app.models import Campaign

def get_campaigns(session: Session) -> List[Campaign]:
    """Get all campaigns."""
    statement = select(Campaign)
    return session.exec(statement).all()

def create_campaign(session: Session, campaign_data: dict) -> Campaign:
    """Create a new campaign."""
    campaign = Campaign(**campaign_data)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign
```

## API Design

### RESTful Principles

- **Resource-Based URLs**: Use nouns for resources
- **HTTP Methods**: Use appropriate HTTP methods
- **Status Codes**: Return appropriate status codes
- **Error Handling**: Consistent error responses

### API Endpoints

```python
# Campaign endpoints
GET    /api/campaigns          # List campaigns
POST   /api/campaigns          # Create campaign
GET    /api/campaigns/{id}     # Get campaign
PUT    /api/campaigns/{id}     # Update campaign
DELETE /api/campaigns/{id}     # Delete campaign

# Account endpoints
GET    /api/accounts           # List accounts
POST   /api/accounts           # Add account
GET    /api/accounts/{id}      # Get account
PUT    /api/accounts/{id}      # Update account
DELETE /api/accounts/{id}      # Delete account
```

### Error Handling

```python
from fastapi import HTTPException
from typing import Dict, Any

def handle_error(error: Exception) -> HTTPException:
    """Handle errors and return appropriate HTTP response."""
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    elif isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail="Permission denied")
    else:
        return HTTPException(status_code=500, detail="Internal server error")
```

## Security Considerations

### Input Validation

- **Sanitize Input**: Sanitize all user input
- **Validate Data**: Validate data types and ranges
- **SQL Injection**: Use parameterized queries
- **XSS Prevention**: Escape HTML output

### Authentication & Authorization

- **API Keys**: Use secure API keys
- **Session Management**: Secure session handling
- **Access Control**: Implement proper access control
- **Audit Logging**: Log security events

### Data Protection

- **Encryption**: Encrypt sensitive data
- **Secure Storage**: Use secure storage methods
- **Data Backup**: Regular secure backups
- **Data Retention**: Implement data retention policies

### Security Best Practices

1. **Keep Dependencies Updated**: Regularly update dependencies
2. **Use HTTPS**: Always use HTTPS in production
3. **Validate Input**: Validate all input data
4. **Error Handling**: Don't expose sensitive information in errors
5. **Logging**: Log security events appropriately

## Performance Optimization

### Database Optimization

- **Indexing**: Add appropriate indexes
- **Query Optimization**: Optimize database queries
- **Connection Pooling**: Use connection pooling
- **Caching**: Implement caching where appropriate

### Memory Management

- **Object Lifecycle**: Manage object lifecycles properly
- **Memory Leaks**: Avoid memory leaks
- **Garbage Collection**: Understand garbage collection
- **Resource Cleanup**: Clean up resources properly

### Async Programming

- **Async/Await**: Use async/await for I/O operations
- **Threading**: Use threading for CPU-bound tasks
- **Event Loops**: Manage event loops properly
- **Concurrency**: Handle concurrency safely

## Deployment

### Production Deployment

1. **Environment Setup**: Set up production environment
2. **Configuration**: Configure production settings
3. **Database Setup**: Set up production database
4. **Monitoring**: Set up monitoring and logging
5. **Security**: Implement security measures

### Containerization

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

### CI/CD Pipeline

1. **Code Quality**: Run code quality checks
2. **Testing**: Run automated tests
3. **Building**: Build packages and installers
4. **Deployment**: Deploy to production
5. **Monitoring**: Monitor deployment

## Monitoring and Logging

### Logging Strategy

- **Structured Logging**: Use structured logging
- **Log Levels**: Use appropriate log levels
- **Log Aggregation**: Aggregate logs centrally
- **Log Analysis**: Analyze logs for insights

### Monitoring

- **Application Metrics**: Monitor application metrics
- **System Metrics**: Monitor system resources
- **Error Tracking**: Track and analyze errors
- **Performance Monitoring**: Monitor performance

### Alerting

- **Error Alerts**: Alert on errors
- **Performance Alerts**: Alert on performance issues
- **Resource Alerts**: Alert on resource usage
- **Security Alerts**: Alert on security events

## Documentation

### Code Documentation

- **Docstrings**: Document all functions and classes
- **Type Hints**: Use type hints for clarity
- **Comments**: Add comments for complex logic
- **README**: Maintain up-to-date README

### API Documentation

- **OpenAPI**: Use OpenAPI for API documentation
- **Examples**: Provide usage examples
- **Error Codes**: Document error codes
- **Versioning**: Document API versioning

### User Documentation

- **User Guide**: Comprehensive user guide
- **Troubleshooting**: Troubleshooting guide
- **FAQ**: Frequently asked questions
- **Video Tutorials**: Video tutorials for complex features

## Conclusion

This development guide provides a comprehensive overview of the development process for the Telegram Multi-Account Message Sender application. Follow these guidelines to ensure code quality, maintainability, and successful contributions to the project.

For more specific information, refer to the individual documentation files in the `docs/` directory or the inline code documentation.
