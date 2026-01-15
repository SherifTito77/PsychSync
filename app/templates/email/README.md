# Email Templates

## Overview

HTML and text email templates.

## Purpose

Email templates for notifications, onboarding, and communications.

## Usage

```python
from app.templates.email.welcome import render_welcome_email

html = render_welcome_email(user_name="John")
```


## Key Components

- Welcome Emails
- Notification Emails
- Onboarding Emails
- Transactional Emails

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
