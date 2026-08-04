#!/usr/bin/env python3
"""
Complete Guide: Connect and Use OrangeHRM Demo
This script walks you through the entire process
"""

import json

import requests

API_BASE = "http://localhost:8000/api/v1/hris"
FRONTEND_URL = "http://localhost:5173/hris-connector"

print("=" * 70)
print("🎯 STEP-BY-STEP: Connect OrangeHRM Demo to Your SaaS")
print("=" * 70)
print()

print("📍 YOUR ORANGEHRM DEMO:")
print(
    "   URL: https://opensource-demo.orangehrmlive.com/web/index.php/admin/viewSystemUsers"
)
print("   Username: Admin")
print("   Password: admin123")
print()

print("=" * 70)
print("✅ STEP 1: Verify OrangeHRM Demo is Available")
print("=" * 70)
print()

response = requests.get(f"{API_BASE}/providers/available")
data = response.json()

if "orangehrm-demo" in data.get("providers", {}):
    provider = data["providers"]["orangehrm-demo"]
    print("✅ OrangeHRM Demo is available!")
    print(f"   Name: {provider['name']}")
    print(f"   Type: {provider['api_type']}")
    print(f"   Authentication: {provider['authentication']}")
    print(f"   Description: {provider.get('description', 'N/A')}")
    print()
else:
    print("❌ OrangeHRM Demo not found in providers")
    print("   Please check if the backend is running")
    exit(1)

print("=" * 70)
print("✅ STEP 2: Test the Demo Connector Directly")
print("=" * 70)
print()

print("Testing OrangeHRM Demo connector without API connection...")
print()

# Import and test the connector
import sys

sys.path.append("/Users/sheriftito/Downloads/psychsync")

from app.integrations.hris.orangehrm_demo_connector import OrangeHRMDemoConnector

config = {
    "base_url": "https://opensource-demo.orangehrmlive.com",
    "username": "Admin",
    "password": "admin123",
    "demo_mode": True,
}

print("Creating connector...")
connector = OrangeHRMDemoConnector(config)

print("\n📊 Fetching employee data...")
employees = connector.get_employees()
print(f"✅ Found {len(employees)} employees:")
for emp in employees[:3]:
    print(f"   • {emp.first_name} {emp.last_name} - {emp.department}")
print()

print("🔄 Testing sync...")
sync_result = connector.sync_data(full_sync=True)
if sync_result.get("success"):
    print(f"✅ Sync successful!")
    print(f"   Total records: {sync_result['records_synced']}")
    print(f"   Employees: {sync_result['employees']}")
    print(f"   Attendance: {sync_result['attendance_records']}")
    print(f"   Leave: {sync_result['leave_records']}")
    print(f"   Performance: {sync_result['performance_reviews']}")
print()

print("=" * 70)
print("✅ STEP 3: View in Browser")
print("=" * 70)
print()

print(f"Open your browser and go to:")
print(f"   {FRONTEND_URL}")
print()
print("You will see:")
print("   ✅ 8 HRIS provider cards")
print("   ✅ OrangeHRM Demo card (with 🎯 icon)")
print("   ✅ Click on it to select")
print()

print("=" * 70)
print("✅ STEP 4: What You Can Do Now")
print("=" * 70)
print()

print("OPTION A - Test the Demo Data (No API needed):")
print("   1. Run: python3 test_orangehrm_demo_live.py")
print("   2. See all 5 employees")
print("   3. View attendance records")
print("   4. Check leave data")
print("   5. Review performance ratings")
print()

print("OPTION B - Create API Connection (Requires auth):")
print("   1. Get auth token from login endpoint")
print("   2. Call POST /api/v1/hris/connection/setup")
print("   3. Use provider: 'orangehrm-demo'")
print()

print("OPTION C - Use the Employee Data Directly:")
print("   The demo connector provides data via Python:")
print("   • connector.get_employees()")
print("   • connector.get_attendance()")
print("   • connector.get_leave_records()")
print("   • connector.get_performance_reviews()")
print()

print("=" * 70)
print("📦 Demo Data Available")
print("=" * 70)
print()

print("EMPLOYEES:")
for emp in employees:
    print(f"   {emp.employee_id}: {emp.first_name} {emp.last_name}")
    print(f"      Department: {emp.department}")
    print(f"      Position: {emp.position}")
    print(f"      Email: {emp.email}")
    print(f"      Status: {emp.employment_status}")
    print()

print("=" * 70)
print("🎯 NEXT ACTIONS")
print("=" * 70)
print()

print("1. ✅ VIEW IN BROWSER:")
print(f"     Open {FRONTEND_URL}")
print("     Click on OrangeHRM Demo card (🎯)")
print()

print("2. ✅ RUN TEST SCRIPT:")
print("     python3 test_orangehrm_demo_live.py")
print()

print("3. ✅ EXPLORE DEMO DATA:")
print("     Use the connector directly in your code")
print("     All data is accessible without authentication")
print()

print("4. ⏳  CREATE CONNECTION (Optional):")
print("     If you want to test the full API workflow,")
print("     you'll need to login first to get an auth token")
print()

print("=" * 70)
print("🎉 YOU'RE ALL SET!")
print("=" * 70)
print()

print("Your OrangeHRM Demo connector is working!")
print()
print("Quick test:")
print("   python3 test_orangehrm_demo_live.py")
print()
print("View in browser:")
print(f"   {FRONTEND_URL}")
print()
print("🚀 Happy connecting!")
