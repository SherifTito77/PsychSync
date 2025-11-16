# app/backup.py
import os, subprocess
from datetime import datetime

def backup_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backup_{timestamp}.sql"
    subprocess.run(f"pg_dump {db_url} > {backup_file}", shell=True, check=True)
    subprocess.run(f"gzip {backup_file}", shell=True, check=True)
    print(f"Backup created: {backup_file}.gz")

if __name__ == "__main__":
    backup_database()

