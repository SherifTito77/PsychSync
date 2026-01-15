# Domain Services

## Overview

Stateless business logic that doesn't naturally fit in entities.

## Purpose

Contains business logic operations that span multiple entities or involve external services.

## Usage

```python
from app.domain.services.team_composition import TeamCompositionService

service = TeamCompositionService()
optimal = service.calculate_optimal_composition(team, candidates)
```


## Key Components

- Team Composition Services
- Assessment Services
- Analytics Services
- Validation Services

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
