# GEMINI.md - Script & Utility Management

This directory contains utility scripts, migrations, security scans, and maintenance tools.

## 📝 Usage Guidelines
- **Categorization:** Use the subdirectories (`security/`, `pipeline_components/`) whenever possible.
- **Naming:** Use descriptive names (e.g., `fix_bug_123.py` instead of `fix.py`).
- **Shebang:** Ensure all `.sh` and `.py` scripts have the appropriate shebang (`#!/bin/bash` or `#!/usr/bin/env python3`).
- **Execution:** Prefer running scripts via `python -m scripts.your_script` if they require application imports.

## 🛠 Script Standards
- **Logging:** Use the `logging` module instead of `print()`.
- **Arguments:** Use `argparse` for scripts that require parameters.
- **Safety:** Always implement a `--dry-run` flag for scripts that modify database records or files.
- **Cleanup:** Scripts should clean up their own temporary files and locks.

## 📂 Maintenance
- **Archival:** Periodically move stale or one-off scripts to an `archived/` subdirectory (create it if needed).
- **Documentation:** Add a docstring at the top of every script explaining its purpose and any risks.
- **Dependencies:** If a script requires a new dependency, it MUST be added to `requirements-dev.txt` or `requirements.txt`.

## 🔒 Security
- **Credentials:** NEVER hardcode secrets. Use environment variables or `app.core.config.settings`.
- **Permissions:** Ensure scripts do not have broad `777` permissions. Use `755` for executables.
