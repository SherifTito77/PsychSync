# Error Page Templates

## Overview

Error page templates for web interface.

## Purpose

Templates for displaying user-friendly error pages.

## Usage

```python
from app.templates.errors import render_error_page

html = render_error_page(error_code=404)
```


## Key Components

- 404 Not Found
- 500 Server Error
- 403 Forbidden
- Custom Error Pages

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
