import os
import sys

# This mimics what alembic/env.py does
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use the correct path: app.db.models
from app.db.models import Base
from app.db.models import * # Import all models

print("Alembic can see the following tables:")
for table_name in Base.metadata.tables.keys():
    print(f"- {table_name}")

if not Base.metadata.tables:
    print("\nERROR: No tables were found! The models are not being imported correctly.")