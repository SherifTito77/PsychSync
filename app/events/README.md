# Event System

## Overview

Event bus and event handling infrastructure.

## Purpose

Implements publish-subscribe pattern for domain events.

## Usage

```python
from app.events import publish, subscribe

@subscribe(UserRegisteredEvent)
async def handle_user_registered(event):
    send_welcome_email(event.email)

await publish(UserRegisteredEvent(user_id=123))
```


## Key Components

- Event Bus
- Event Handlers
- Event Store
- Replay Mechanisms

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
