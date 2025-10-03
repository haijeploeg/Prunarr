# PrunArr Architecture

## Overview

PrunArr follows a layered architecture pattern with clear separation of concerns between API clients, business logic, and presentation layers.

## Architecture Layers

### 1. API Client Layer (`prunarr/*.py`)
**Purpose**: Direct communication with external APIs (Radarr, Sonarr, Tautulli) with caching integration

- `radarr.py` - RadarrAPI wrapper for movie management with cache support
- `sonarr.py` - SonarrAPI wrapper for TV series management with cache support
- `tautulli.py` - TautulliAPI client for watch history with cache support

**Responsibilities**:
- HTTP communication with external services
- Raw API response handling
- Cache integration for improved performance
- Basic error handling
- Debug logging of API calls
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

- `movies.py` - Movie management commands with JSON/table output
- `series.py` - TV series management commands with JSON/table output
- `history.py` - Watch history commands with JSON/table output
- `cache.py` - Cache management commands with JSON/table output

**Responsibilities**:
- Parse CLI arguments
- Call orchestrator methods
- Format output with Rich tables or JSON
- Handle user confirmations
- Display progress indicators
- Support dual output modes (table/json)

### 7. Cache Layer (`prunarr/cache/`)
**Purpose**: Performance optimization through intelligent caching

- `cache_manager.py` - Cache manager with TTL support and size limits
- `cache_store.py` - Disk-based JSON cache storage

**Responsibilities**:
- Minimize API calls through caching
- TTL-based expiration (configurable per data type)
- Size limit enforcement with automatic cleanup
- Cache statistics tracking (hits, misses, last accessed)
- Debug logging of cache operations

**Cached Data Types**:
- Movies (Radarr) - 1 hour default TTL
- Series (Sonarr) - 1 hour default TTL
- Watch History (Tautulli) - 5 minutes default TTL
- Tags - 24 hours default TTL
- Metadata - 24 hours default TTL

### 8. Configuration & Logging
- `config.py` - Pydantic settings with YAML/env support, cache & log level configuration
- `logger.py` - Rich-styled logging system with priority-based filtering
- `cli.py` - Main CLI entry point with Typer
- `utils.py` - Formatting helpers (durations, file sizes, dates, status)

## Data Flow

```
User Input (CLI)
    ↓
Commands (presentation layer - table/JSON output)
    ↓
PrunArr Orchestrator (coordination)
    ↓
Services (business logic)
    ↓
API Clients (external communication) ←→ Cache Layer (performance)
    ↓
Domain Models (type-safe data)
```

### Data Flow with Caching

```
Command Request
    ↓
API Client checks Cache Manager
    ├─ Cache Hit → Return cached data (fast path)
    │
    └─ Cache Miss → Fetch from API
                    ↓
                Store in Cache with TTL
                    ↓
                Return fresh data
```

### Logging Flow

```
Component Operation
    ↓
Logger with configured level (ERROR/WARNING/INFO/DEBUG)
    ↓
Priority Check (is message priority >= configured level?)
    ├─ Yes → Format with Rich styling + timestamp → Output to stderr
    │
    └─ No → Discard message

Special Case: --debug flag always overrides to DEBUG level
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

### 5. Caching Pattern
Transparent caching layer with TTL-based expiration.

### 6. Strategy Pattern (Output Formatting)
Commands support multiple output strategies (table vs JSON).

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Changes are localized to specific layers
3. **Reusability**: Services and utilities can be used by multiple commands
4. **Type Safety**: Domain models provide strong typing
5. **Clarity**: Clear responsibility for each component
6. **Scalability**: Easy to add new features without disrupting existing code
7. **Performance**: Caching layer dramatically reduces API calls
8. **Flexibility**: Dual output modes (table/JSON) support both human and machine interaction
9. **Observability**: Configurable logging provides visibility at multiple levels

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

## Recent Improvements

1. ✅ **Caching Layer**: Implemented intelligent caching with TTL support
2. ✅ **Logging System**: Added priority-based log levels with --debug override
3. ✅ **JSON Output**: All list/get/status commands support JSON output
4. ✅ **Performance**: Cache dramatically improves response times for repeated queries
5. ✅ **Observability**: Debug logging throughout API clients and cache operations

## Future Improvements

1. **Command Layer**: Refactor commands to use domain models directly
2. **Repository Pattern**: Formalize API clients as repositories
3. **Dependency Injection**: Use DI container for service instantiation
4. **Event System**: Add events for cross-cutting concerns (logging, metrics)
5. **Async Support**: Add async/await for concurrent API calls
6. **Cache Warmup**: Automatic background cache refresh before expiration
7. **Cache Compression**: Add optional compression for large cached datasets
8. **Distributed Caching**: Support for Redis or other distributed cache backends
