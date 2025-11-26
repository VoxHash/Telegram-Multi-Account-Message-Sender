# Architecture

System architecture and design documentation for Telegram Multi-Account Message Sender.

## Overview

Telegram Multi-Account Message Sender is built with a modular architecture using Python and PyQt5.

## Architecture Layers

### Presentation Layer

- **GUI**: PyQt5-based graphical interface
- **Widgets**: Reusable UI components
- **Themes**: Theme system for UI customization

### Business Logic Layer

- **Engine**: Core message sending engine
- **Campaign Manager**: Campaign management logic
- **Throttler**: Rate limiting and throttling
- **Compliance**: Compliance and safety controls

### Data Layer

- **Models**: SQLModel-based data models
- **Database**: SQLite database
- **Services**: Database and service layer

## Key Components

### Core Components

- `app/core/engine.py`: Message sending engine
- `app/core/throttler.py`: Rate limiting
- `app/core/compliance.py`: Compliance controls
- `app/core/spintax.py`: Spintax processing

### Services

- `app/services/db.py`: Database service
- `app/services/campaign_manager.py`: Campaign management
- `app/services/logger.py`: Logging service
- `app/services/settings.py`: Settings management

### Models

- `app/models/account.py`: Account model
- `app/models/campaign.py`: Campaign model
- `app/models/recipient.py`: Recipient model
- `app/models/template.py`: Template model

## Data Flow

1. User interacts with GUI
2. GUI calls service layer
3. Service layer processes business logic
4. Data layer persists changes
5. Updates reflected in GUI

## Design Patterns

- **MVC**: Model-View-Controller pattern
- **Service Layer**: Business logic separation
- **Repository Pattern**: Data access abstraction

## Dependencies

- **PyQt5**: GUI framework
- **Telethon**: Telegram client library
- **SQLModel**: Database ORM
- **asyncio**: Asynchronous operations

## See Also

- [API Documentation](api.md) for API details
- [Development Guide](../CONTRIBUTING.md) for development setup

