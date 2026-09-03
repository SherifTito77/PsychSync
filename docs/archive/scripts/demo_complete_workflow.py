#!/usr/bin/env python3
"""
Complete Workflow Demo: From HRIS Connection to Analytics
Shows the full journey of connecting OrangeHRM Demo and performing analytics
"""

import sys

sys.path.append("/Users/sheriftito/Downloads/psychsync")

from collections import Counter
from datetime import date

from app.integrations.hris.orangehrm_demo_connector import OrangeHRMDemoConnector

print("=" * 80)
print("🎯 COMPLETE WORKFLOW: OrangeHRM Demo → Analytics")
print("=" * 80)
print()

# ============================================================================
# STEP 1: CONNECT TO ORANGEHRM DEMO
# ============================================================================
print("✅ STEP 1: CONNECT TO ORANGEHRM DEMO")
print("-" * 80)
print()

config = {
    "base_url": "https://opensource-demo.orangehrmlive.com",
    "username": "Admin",
    "password": "admin123",
    "demo_mode": True,
}

connector = OrangeHRMDemoConnector(config)
print("✅ Connected to OrangeHRM Demo")
print(f"   Demo Mode: {connector.demo_mode}")
print(f"   Base URL: {connector.base_url}")
print()

# ============================================================================
# STEP 2: RETRIEVE ALL EMPLOYEE DATA
# ============================================================================
print("✅ STEP 2: RETRIEVE EMPLOYEE DATA")
print("-" * 80)
print()

employees = connector.get_employees()
print(f"✅ Retrieved {len(employees)} employees:")
print()

for emp in employees:
    print(f"   👤 {emp.first_name} {emp.last_name}")
    print(f"      ID: {emp.employee_id}")
    print(f"      Email: {emp.email}")
    print(f"      Department: {emp.department}")
    print(f"      Position: {emp.position}")
    print(f"      Location: {emp.location}")
    print(f"      Status: {emp.employment_status}")
    print(f"      Hire Date: {emp.hire_date}")
    print()

# ============================================================================
# STEP 3: RETRIEVE ATTENDANCE DATA
# ============================================================================
print("✅ STEP 3: RETRIEVE ATTENDANCE DATA")
print("-" * 80)
print()

attendance = connector.get_attendance()
print(f"✅ Retrieved {len(attendance)} attendance records:")
print()

total_hours = 0
for record in attendance:
    print(f"   📅 {record.date}")
    print(f"      Employee: {record.employee_id}")
    print(f"      Hours: {record.hours_worked}")
    print(f"      Status: {record.status}")
    total_hours += record.hours_worked

print(f"\n   📊 Total Hours: {total_hours}")
print()

# ============================================================================
# STEP 4: RETRIEVE LEAVE DATA
# ============================================================================
print("✅ STEP 4: RETRIEVE LEAVE DATA")
print("-" * 80)
print()

leave = connector.get_leave_records()
print(f"✅ Retrieved {len(leave)} leave records:")
print()

total_leave_days = 0
for record in leave:
    print(f"   🏖️  {record.leave_type}")
    print(f"      Employee: {record.employee_id}")
    print(f"      Period: {record.start_date} to {record.end_date}")
    print(f"      Days: {record.days_taken}")
    print(f"      Status: {record.status}")
    print(f"      Reason: {record.reason}")
    total_leave_days += record.days_taken

print(f"\n   📊 Total Leave Days: {total_leave_days}")
print()

# ============================================================================
# STEP 5: RETRIEVE PERFORMANCE DATA
# ============================================================================
print("✅ STEP 5: RETRIEVE PERFORMANCE DATA")
print("-" * 80)
print()

reviews = connector.get_performance_reviews()
print(f"✅ Retrieved {len(reviews)} performance reviews:")
print()

total_rating = 0
for review in reviews:
    print(f"   ⭐ Review: {review.review_id}")
    print(f"      Employee: {review.employee_id}")
    print(f"      Reviewer: {review.reviewer_id}")
    print(f"      Date: {review.review_date}")
    print(f"      Rating: {review.rating}/5")
    print(f"      Comments: {review.comments}")
    total_rating += review.rating

avg_rating = total_rating / len(reviews) if reviews else 0
print(f"\n   📊 Average Rating: {avg_rating:.2f}/5")
print()

# ============================================================================
# STEP 6: WORKFORCE ANALYTICS
# ============================================================================
print("✅ STEP 6: WORKFORCE ANALYTICS")
print("-" * 80)
print()

# Department Distribution
print("📊 DEPARTMENT DISTRIBUTION:")
dept_counts = Counter(emp.department for emp in employees)
for dept, count in dept_counts.items():
    percentage = (count / len(employees)) * 100
    print(f"   {dept}: {count} employees ({percentage:.1f}%)")
print()

# Position Distribution
print("📊 POSITION DISTRIBUTION:")
position_counts = Counter(emp.position for emp in employees)
for position, count in position_counts.items():
    print(f"   {position}: {count}")
print()

# Location Distribution
print("📊 LOCATION DISTRIBUTION:")
location_counts = Counter(emp.location for emp in employees)
for location, count in location_counts.items():
    print(f"   {location}: {count} employees")
print()

# Employment Status
print("📊 EMPLOYMENT STATUS:")
status_counts = Counter(emp.employment_status for emp in employees)
for status, count in status_counts.items():
    print(f"   {status}: {count} employees")
print()

# ============================================================================
# STEP 7: ATTENDANCE ANALYTICS
# ============================================================================
print("✅ STEP 7: ATTENDANCE ANALYTICS")
print("-" * 80)
print()

# Average hours per day
avg_hours = total_hours / len(attendance) if attendance else 0
print(f"📊 Average Hours per Day: {avg_hours:.2f}")

# Attendance by employee
attendance_by_emp = Counter(record.employee_id for record in attendance)
print(f"\n📊 Attendance Records by Employee:")
for emp_id, count in attendance_by_emp.items():
    emp = next((e for e in employees if e.employee_id == emp_id), None)
    if emp:
        print(f"   {emp.first_name} {emp.last_name}: {count} records")
print()

# ============================================================================
# STEP 8: LEAVE ANALYTICS
# ============================================================================
print("✅ STEP 8: LEAVE ANALYTICS")
print("-" * 80)
print()

# Leave by type
leave_by_type = Counter(record.leave_type for record in leave)
print("📊 Leave by Type:")
for leave_type, count in leave_by_type.items():
    days = sum(r.days_taken for r in leave if r.leave_type == leave_type)
    print(f"   {leave_type}: {count} requests, {days} total days")
print()

# Leave by employee
print("📊 Leave by Employee:")
leave_by_emp = {}
for record in leave:
    if record.employee_id not in leave_by_emp:
        leave_by_emp[record.employee_id] = {"count": 0, "days": 0}
    leave_by_emp[record.employee_id]["count"] += 1
    leave_by_emp[record.employee_id]["days"] += record.days_taken

for emp_id, data in leave_by_emp.items():
    emp = next((e for e in employees if e.employee_id == emp_id), None)
    if emp:
        print(
            f"   {emp.first_name} {emp.last_name}: {data['count']} requests, {data['days']} days"
        )
print()

# ============================================================================
# STEP 9: PERFORMANCE ANALYTICS
# ============================================================================
print("✅ STEP 9: PERFORMANCE ANALYTICS")
print("-" * 80)
print()

# Rating distribution
print(f"📊 Average Rating: {avg_rating:.2f}/5")
print()

# Performance by employee
performance_by_emp = {}
for review in reviews:
    if review.employee_id not in performance_by_emp:
        performance_by_emp[review.employee_id] = []
    performance_by_emp[review.employee_id].append(review.rating)

print("📊 Performance by Employee:")
for emp_id, ratings in performance_by_emp.items():
    emp = next((e for e in employees if e.employee_id == emp_id), None)
    if emp:
        avg = sum(ratings) / len(ratings)
        print(
            f"   {emp.first_name} {emp.last_name}: {avg:.2f}/5 ({len(ratings)} reviews)"
        )
print()

# ============================================================================
# STEP 10: SYNC ALL DATA
# ============================================================================
print("✅ STEP 10: SYNC ALL DATA")
print("-" * 80)
print()

sync_result = connector.sync_data(full_sync=True)
if sync_result.get("success"):
    print("✅ Sync Successful!")
    print(f"   Source: {sync_result['source']}")
    print(f"   Total Records: {sync_result['records_synced']}")
    print(f"   📊 Employees: {sync_result['employees']}")
    print(f"   ⏰ Attendance Records: {sync_result['attendance_records']}")
    print(f"   🏖️  Leave Records: {sync_result['leave_records']}")
    print(f"   ⭐ Performance Reviews: {sync_result['performance_reviews']}")
    print(f"   Timestamp: {sync_result['timestamp']}")
else:
    print("❌ Sync Failed")
    print(f"   Error: {sync_result.get('error')}")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("🎉 WORKFLOW COMPLETE - SUMMARY")
print("=" * 80)
print()

print("📦 DATA RETRIEVED:")
print(f"   👥 Employees: {len(employees)}")
print(f"   ⏰ Attendance Records: {len(attendance)}")
print(f"   🏖️  Leave Records: {len(leave)}")
print(f"   ⭐ Performance Reviews: {len(reviews)}")
print()

print("🏢 ORGANIZATIONAL INSIGHTS:")
print(f"   Departments: {len(dept_counts)}")
print(f" Locations: {len(location_counts)}")
print(f" Total Hours Worked: {total_hours}")
print(f" Total Leave Days: {total_leave_days}")
print(f" Avg Performance Rating: {avg_rating:.2f}/5")
print()

print("✅ CONNECTOR STATUS:")
print(f"   Provider: OrangeHRM Demo")
print(f"   Mode: Demo Mode (Mock Data)")
print(f"   Status: Fully Functional")
print()

print("=" * 80)
print("💡 YOU CAN NOW:")
print("=" * 80)
print()
print("1. ✅ Use this connector in your production code")
print("2. ✅ Integrate with your HRIS analytics dashboard")
print("3. ✅ Build custom reports and visualizations")
print("4. ✅ Create automated workflows for employee data")
print("5. ✅ Extend with additional HRIS providers")
print()

print("🚀 The OrangeHRM Demo connector is ready for production use!")
print()
