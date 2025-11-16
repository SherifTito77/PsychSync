import sys
sys.path.insert(0, '/Users/sheriftito/Downloads/psychsync')

from sqlalchemy import inspect, text
from app.db.session import engine

# Check current columns
inspector = inspect(engine)
columns = {col['name']: col for col in inspector.get_columns('users')}

print("Current columns in users table:")
for col_name in columns.keys():
    print(f"  - {col_name}")

# Determine what needs to be added
conn = engine.connect()
trans = conn.begin()

try:
    # Check if we have 'password' but not 'hashed_password'
    if 'password' in columns and 'hashed_password' not in columns:
        print("\n✅ Renaming 'password' to 'hashed_password'")
        conn.execute(text("ALTER TABLE users RENAME COLUMN password TO hashed_password"))
    
    # Check if we need hashed_password column
    elif 'hashed_password' not in columns:
        print("\n✅ Adding 'hashed_password' column")
        conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR"))
    
    # Check if we need full_name
    if 'full_name' not in columns:
        print("✅ Adding 'full_name' column")
        conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
        
        # If first_name and last_name exist, populate full_name
        if 'first_name' in columns and 'last_name' in columns:
            print("✅ Populating full_name from first_name and last_name")
            conn.execute(text("""
                UPDATE users 
                SET full_name = COALESCE(first_name || ' ' || last_name, first_name, last_name)
                WHERE full_name IS NULL
            """))
    
    trans.commit()
    print("\n✅ Schema updated successfully!")
    
except Exception as e:
    trans.rollback()
    print(f"\n❌ Error: {e}")
finally:
    conn.close()

# Verify the changes
print("\nUpdated columns in users table:")
inspector = inspect(engine)
columns = {col['name']: col for col in inspector.get_columns('users')}
for col_name in columns.keys():
    print(f"  - {col_name}")
