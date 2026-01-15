# HRIS System Integration

## Overview

Human Resource Information System integrations.

## Purpose

Provides adapters for connecting to various HRIS platforms like BambooHR, Workday, etc.

## Usage

```python
from app.integrations.hris.bamboohr import BambooHRClient

client = BambooHRClient(api_key="...")
employees = await client.get_employees()
```


## Key Components

- BambooHR Adapter
- Workday Adapter
- Unified HRIS Interface
- Sync Operations

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
