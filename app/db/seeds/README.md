# Database Seed Data

## Overview

Seed data for database initialization.

## Purpose

Contains initial data for database seeding and testing.

## Usage

```python
from app.db.seeds.seed_assessments import seed_assessments

await seed_assessments(db)
```


## Key Components

- Assessment Seeds
- Framework Seeds
- Demo Data
- Reference Data

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
