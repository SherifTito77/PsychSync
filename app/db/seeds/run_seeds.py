"""
Simple script to run seeds from command line

File path: app/db/seeds/run_seeds.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import after adding to path
from app.db.seeds.seed_organizations import run_seed

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PsychSync - Database Seeding")
    print("=" * 60 + "\n")
    
    try:
        run_seed()
        print("\n✅ All seeds completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Seed failed: {e}\n")
        sys.exit(1)