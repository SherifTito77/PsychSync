# Domain Events

## Overview

Domain event definitions and handlers.

## Purpose

Implements domain events pattern for decoupling and eventual consistency.

## Usage

```python
from app.domain.events import UserRegisteredEvent

event = UserRegisteredEvent(user_id=123, email="user@example.com")
await publish(event)
```


## Key Components

- Event Definitions
- Event Handlers
- Event Publishing

## Related Documentation

- [Main README](../../../README.md)
- [API Documentation](../api/README.md)
- [Services Documentation](../services/README.md)
- [Database Documentation](../db/README.md)
- [Core Documentation](../core/README.md)

## Contributing

When adding new files to this directory, please:
1. Follow existing code patterns
2. Add comprehensive docstrings
3. Update this README with key changes
4. Ensure proper error handling
5. Add tests for new functionality

## Testing

Test files in this directory using:
```bash
pytest tests/path/to/this/directory/ -v
```
