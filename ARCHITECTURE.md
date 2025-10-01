# PrunArr Architecture

## Overview

PrunArr follows a layered architecture pattern with clear separation of concerns between API clients, business logic, and presentation layers.

## Architecture Layers

### 1. API Client Layer (`prunarr/*.py`)
**Purpose**: Direct communication with external APIs (Radarr, Sonarr, Tautulli)

- `radarr.py` - RadarrAPI wrapper for movie management
- `sonarr.py` - SonarrAPI wrapper for TV series management
- `tautulli.py` - TautulliAPI client for watch history

**Responsibilities**:
- HTTP communication with external services
- Raw API response handling
- Basic error handling
- No business logic

### 2. Domain Models Layer (`prunarr/models/`)
**Purpose**: Type-safe representations of core business entities

- `movie.py` - Movie domain model with watch status
- `series.py` - TV series domain model
- `episode.py` - Episode and Season domain models
- `watch_history.py` - Watch history records and status enums

**Benefits**:
- Strong typing throughout the codebase
- Centralized validation logic
- Easy to test in isolation
- Clear data contracts between layers

### 3. Service Layer (`prunarr/services/`)
**Purpose**: Business logic coordination between APIs and domain models

- `user_service.py` - User tag parsing and validation
- `media_matcher.py` - Correlates watch history with media libraries
- `watch_calculator.py` - Watch status, progress, and completion calculations

**Responsibilities**:
- Complex business logic
- Multi-API coordination
- Data transformation
- Calculation and analysis
- No direct API calls (delegates to API clients)
- No presentation logic (delegates to commands)

### 4. Orchestration Layer (`prunarr/prunarr.py`)
**Purpose**: High-level coordination of services and API clients

The `PrunArr` class serves as a facade that:
- Initializes API clients and services
- Provides backward-compatible methods for existing commands
- Delegates complex operations to service layer
- Maintains configuration state

**Current Status**: Refactored to use service layer internally while maintaining existing public API.

### 5. Utility Layer (`prunarr/utils/`)
**Purpose**: Reusable helper functions organized by responsibility

- `formatters.py` - Human-readable formatting (file sizes, dates, status)
- `parsers.py` - Data parsing (episode keys, etc.)
- `filters.py` - Common filtering operations
- `validators.py` - Input validation and data integrity

**Benefits**:
- No more monolithic utils.py
- Easy to find and test specific functionality
- Clear single responsibility for each module

### 6. Command Layer (`prunarr/commands/`)
**Purpose**: CLI interface and user interaction

- `movies.py` - Movie management commands
- `series.py` - TV series management commands
- `history.py` - Watch history commands

**Responsibilities**:
- Parse CLI arguments
- Call orchestrator methods
- Format output with Rich tables
- Handle user confirmations
- Display progress indicators

### 7. Configuration & Logging
- `config.py` - Pydantic settings with YAML/env support
- `logger.py` - Rich-styled logging system
- `cli.py` - Main CLI entry point with Typer

## Data Flow

```
User Input (CLI)
    ↓
Commands (presentation layer)
    ↓
PrunArr Orchestrator (coordination)
    ↓
Services (business logic)
    ↓
API Clients (external communication)
    ↓
Domain Models (type-safe data)
```

## Key Design Patterns

### 1. Facade Pattern
`PrunArr` class acts as a simplified interface to complex subsystems.

### 2. Service Layer Pattern
Business logic extracted into dedicated service classes.

### 3. Repository Pattern (Implicit)
API clients act as repositories for external data sources.

### 4. Domain Model Pattern
Rich domain objects with behavior, not just data.

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Changes are localized to specific layers
3. **Reusability**: Services and utilities can be used by multiple commands
4. **Type Safety**: Domain models provide strong typing
5. **Clarity**: Clear responsibility for each component
6. **Scalability**: Easy to add new features without disrupting existing code

## Migration Path

The refactoring maintains backward compatibility:
- Existing commands continue to work without changes
- `PrunArr` orchestrator delegates to services internally
- Utils maintain backward-compatible imports
- Domain models are available but optional for gradual adoption

## Testing Strategy

```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_utils.py
│   └── test_prunarr_helpers.py
├── integration/       # API integration tests
│   ├── test_radarr.py
│   ├── test_sonarr.py
│   └── test_tautulli.py
└── fixtures/          # Shared test data
```

## Future Improvements

1. **Command Layer**: Refactor commands to use domain models directly
2. **Repository Pattern**: Formalize API clients as repositories
3. **Dependency Injection**: Use DI container for service instantiation
4. **Event System**: Add events for cross-cutting concerns (logging, metrics)
5. **Async Support**: Add async/await for concurrent API calls
6. **Caching Layer**: Add intelligent caching for frequently accessed data
