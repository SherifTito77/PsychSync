# app/backup.py
import os
import subprocess
from datetime import datetime


def backup_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"

    # TODO(human): Validate and sanitize db_url before use
    # For security, we should validate that db_url contains only expected characters
    # and doesn't contain command injection attempts like semicolons, pipes, etc.
    # Consider using a dedicated backup library like psycopg2's copy_expert()
    # or environment-based authentication instead of passing db_url directly.

    # Use shell=False to prevent command injection
    subprocess.run(["pg_dump", db_url, "-f", backup_file], check=False)
    subprocess.run(["gzip", backup_file], check=False)
    print(f"Backup created: {backup_file}.gz")


if __name__ == "__main__":
    backup_database()
