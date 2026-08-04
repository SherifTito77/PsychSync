#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI application.
Usage: python generate_openapi_spec.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.main import app

    # Generate OpenAPI spec
    openapi_schema = app.openapi()

    # Save to file
    output_path = Path(__file__).parent / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✅ OpenAPI spec generated successfully: {output_path}")
    print(f"   Endpoints documented: {len(openapi_schema.get('paths', {}))}")
    print(f"\nNow you can run:")
    print(
        f"   python agents/api_contract_agent.py --api-path app/api/v1/api.py --spec-path openapi.json"
    )

except ImportError as e:
    print(f"❌ Error importing app: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure you're in the virtual environment: source .venv/bin/activate")
    print("2. Install dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error generating spec: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
