"""
Check actual database schema
File: check_schema.py (save in project root)
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, inspect, text
from app.db.database import engine

def check_database_schema():
    """Check what columns actually exist in the database"""
    
    inspector = inspect(engine)
    
    # Tables to check
    tables = ['users', 'organizations', 'teams', 'team_members']
    
    print("=" * 80)
    print("DATABASE SCHEMA CHECK")
    print("=" * 80)
    
    # First, list all tables that exist
    all_tables = inspector.get_table_names()
    print(f"\n📚 All tables in database: {', '.join(all_tables)}\n")
    
    for table_name in tables:
        if table_name in all_tables:
            print(f"\n📋 Table: {table_name}")
            print("-" * 80)
            
            columns = inspector.get_columns(table_name)
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                col_type = str(col['type'])
                default = f" DEFAULT {col['default']}" if col.get('default') else ""
                print(f"  {col['name']:<30} {col_type:<25} {nullable:<10}{default}")
            
            # Check foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"\n  Foreign Keys:")
                for fk in fks:
                    print(f"    {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        else:
            print(f"\n❌ Table '{table_name}' does not exist in database")
    
    print("\n" + "=" * 80)
    
    # Check if we can query organizations
    print("\nTesting organizations table query...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM organizations LIMIT 1"))
            row = result.fetchone()
            if row:
                print(f"✅ Found organization: {dict(row._mapping)}")
            else:
                print("⚠️  Organizations table is empty")
    except Exception as e:
        print(f"❌ Error querying organizations: {e}")

if __name__ == "__main__":
    try:
        check_database_schema()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
