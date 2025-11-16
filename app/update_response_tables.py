# app/update_response_tables.py
"""
Update response tables with new columns
Run this once: python update_response_tables.py
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE assessment_responses 
                ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'in_progress';
            """))
            conn.commit()
            print("✓ Added status column")
        except Exception as e:
            print(f"status column might already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE assessment_responses 
                ADD COLUMN IF NOT EXISTS current_section INTEGER DEFAULT 0;
            """))
            conn.commit()
            print("✓ Added current_section column")
        except Exception as e:
            print(f"current_section column might already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE assessment_responses 
                ADD COLUMN IF NOT EXISTS progress_percentage FLOAT DEFAULT 0.0;
            """))
            conn.commit()
            print("✓ Added progress_percentage column")
        except Exception as e:
            print(f"progress_percentage column might already exist: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE assessment_responses 
                ADD COLUMN IF NOT EXISTS last_saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
            """))
            conn.commit()
            print("✓ Added last_saved_at column")
        except Exception as e:
            print(f"last_saved_at column might already exist: {e}")
        
        # Create response_scores table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS response_scores (
                    id SERIAL PRIMARY KEY,
                    response_id INTEGER REFERENCES assessment_responses(id) ON DELETE CASCADE,
                    total_score FLOAT,
                    max_possible_score FLOAT,
                    percentage_score FLOAT,
                    subscale_scores JSON,
                    interpretation TEXT,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            print("✓ Created response_scores table")
        except Exception as e:
            print(f"response_scores table might already exist: {e}")

if __name__ == "__main__":
    print("Running response tables migration...")
    run_migration()
    print("Migration complete!")
    