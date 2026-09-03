#!/usr/bin/env python3
"""
OrangeHRM Demo Connector Usage Guide
Shows how to use the HRIS integration manager with the demo connector
"""

import sys

sys.path.append("/Users/sheriftito/Downloads/psychsync")

import json

from app.integrations.hris.integration_manager import HRISIntegrationManager


def print_section(title: str):
    """Print formatted section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print("=" * 70)


def main():
    print_section("Mock HRIS Demo Connector - Usage Guide")

    # Initialize manager
    manager = HRISIntegrationManager()

    # 1. List available connectors
    print_section("1. Available HRIS Connectors")
    connectors = manager.list_available_connectors()
    for name, info in connectors.items():
        print(f"\n  📦 {name.upper()}")
        print(f"     Description: {info['description']}")
        print(f"     Required: {', '.join(info['required'])}")

    # 2. Create demo connector
    print_section("2. Creating Mock Demo Connector")

    config = {"demo_mode": True, "organization_id": "demo-org-123"}

    connector = manager.create_connector("mock-demo", config)

    if connector:
        print("✅ Demo connector created successfully!")
        print(f"   Type: {type(connector).__name__}")
    else:
        print("❌ Failed to create connector")
        return 1

    # 3. Test connection
    print_section("3. Testing Connection")
    try:
        is_connected = connector.test_connection()
        print(
            f"{'✅' if is_connected else '❌'} Connection status: {'Connected' if is_connected else 'Failed'}"
        )
    except Exception as e:
        print(f"❌ Connection test error: {e}")

    # 4. Get employees
    print_section("4. Fetching Employee Data")
    try:
        employees = connector.get_employees()
        print(f"✅ Found {len(employees)} employees\n")

        # Show first 3 employees
        for i, emp in enumerate(employees[:3], 1):
            print(f"  {i}. {emp.first_name} {emp.last_name}")
            print(f"     Department: {emp.department}")
            print(f"     Position: {emp.position}")
            print(f"     Status: {emp.employment_status}")
            print()

        if len(employees) > 3:
            print(f"  ... and {len(employees) - 3} more employees")
    except Exception as e:
        print(f"❌ Error fetching employees: {e}")

    # 5. Get departments
    print_section("5. Fetching Department Data")
    try:
        departments = connector.get_departments()
        print(f"✅ Found {len(departments)} departments\n")

        for dept in departments:
            print(f"  • {dept.get('name', dept.get('department', 'N/A'))}")
            print(f"    ID: {dept.get('id', 'N/A')}")
    except Exception as e:
        print(f"❌ Error fetching departments: {e}")

    # 6. Example: Filter employees
    print_section("6. Example: Filter Active Employees")
    try:
        all_employees = connector.get_employees()
        active_employees = [
            emp for emp in all_employees if emp.employment_status == "active"
        ]

        print(f"✅ Total employees: {len(all_employees)}")
        print(f"✅ Active employees: {len(active_employees)}")
        print(
            f"❌ Inactive/on-leave employees: {len(all_employees) - len(active_employees)}"
        )
    except Exception as e:
        print(f"❌ Error filtering employees: {e}")

    # 7. Usage summary
    print_section("7. Usage Summary")
    print(
        """
The Mock Demo Connector provides:

✅ No External Dependencies: Works entirely offline
✅ Sample Data: Pre-populated with realistic employee records
✅ Full API: All HRIS methods implemented
✅ Testing: Perfect for development and testing

Available Methods:
  • test_connection()       - Verify connector works
  • get_employees()         - Get all employee records
  • get_departments()       - Get department structure
  • get_attendance()        - Get attendance data
  • get_leave_records()     - Get leave/PTO records
  • get_performance_reviews() - Get performance reviews

Next Steps:
  • Test API endpoints: python3 test_hris_api.py
  • View in browser: http://localhost:5173/hris-connector
  • Check API docs: http://localhost:8000/docs
    """
    )

    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
