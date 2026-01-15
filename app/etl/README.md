# ETL Pipelines

## Overview

Extract, Transform, Load pipelines for data processing.

## Purpose

Contains data processing pipelines for imports, exports, and data migrations.

## Usage

```python
from app.etl.pipelines.import_users import UserImportPipeline

pipeline = UserImportPipeline(csv_file)
await pipeline.run()
```


## Key Components

- Import Pipelines
- Export Pipelines
- Data Transformations
- Validation Steps

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
