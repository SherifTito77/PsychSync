# Utility Functions

## Overview

General utility functions and helpers.

## Purpose

Contains reusable utility functions used across the application.

## Usage

```python
from app.utils.date import utcnow
from app.utils.string import generate_random_string

now = utcnow()
token = generate_random_string(32)
```


## Key Components

- Date Utilities
- String Utilities
- Validation Helpers
- Conversion Utilities

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
