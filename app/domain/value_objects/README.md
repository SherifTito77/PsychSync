# Value Objects

## Overview

Immutable value objects with no identity.

## Purpose

Defines concepts identified by their attributes rather than identity.

## Usage

```python
from app.domain.value_objects import Email, TeamId

email = Email("user@example.com")
team_id = TeamId("team-123")
```


## Key Components

- Email Value Object
- Team Identifiers
- Assessment Scores
- Validation Value Objects

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
