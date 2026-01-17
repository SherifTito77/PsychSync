#!/usr/bin/env python3
"""
Minimal test to verify server can start with core endpoints only
"""

import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

print("Testing imports...")

try:
    print("1. Testing core imports...")
    from app.core.config import settings
    print("   ✓ Config imported")

    from app.core.database import get_db
    print("   ✓ Database imported")

    from app.main import app
    print("   ✓ Main app imported")

    print("2. Testing API router...")
    from app.api.v1.api import api_router
    print("   ✓ API router imported")

    print("3. Checking routes...")
    routes = [route.path for route in app.routes]
    print(f"   ✓ Total routes: {len(routes)}")

    core_routes = [r for r in routes if r.endswith(('/health', '/auth', '/users'))]
    print(f"   ✓ Core routes found: {len(core_routes)}")

    print("\n✅ All imports successful! The app should be able to start.")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
