# Admin Templates

## Overview

Administrative interface templates.

## Purpose

Templates for admin panels and dashboards.

## Usage

```python
from app.templates.admin import render_admin_dashboard

html = render_admin_dashboard(data=metrics)
```


## Key Components

- Dashboard Templates
- Admin Forms
- Admin Reports

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
