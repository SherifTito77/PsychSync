#!/usr/bin/env python3
"""
HRIS Development Server for Local Testing
Simulates various HRIS APIs for connector development.

Usage:
    python scripts/hris_dev_server.py --platform orangehrm --port 8080
    python scripts/hris_dev_server.py --platform custom --config config.json
"""

import argparse
import json
import logging
import random
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from flask import Flask, abort, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MockEmployee:
    """Mock employee for development server."""

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    department: str
    position: str
    hire_date: str
    employment_status: str
    manager_id: str
    location: str


@dataclass
class MockAttendance:
    """Mock attendance record."""

    id: str
    employee_id: str
    date: str
    clock_in: str
    clock_out: str
    hours_worked: float
    status: str


@dataclass
class MockLeave:
    """Mock leave record."""

    id: str
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    days_taken: float
    status: str
    reason: str


class HRISDevServer:
    """Development server for simulating HRIS APIs."""

    def __init__(self, platform: str = "orangehrm", port: int = 8080):
        self.platform = platform
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for development

        # Generate mock data
        self.employees = self._generate_mock_employees()
        self.attendance = self._generate_mock_attendance()
        self.leaves = self._generate_mock_leaves()

        # Setup API routes
        self._setup_routes()

    def _generate_mock_employees(self) -> List[MockEmployee]:
        """Generate mock employee data."""
        departments = [
            "Engineering",
            "HR",
            "Sales",
            "Marketing",
            "Finance",
            "Operations",
        ]
        positions = [
            "Software Engineer",
            "HR Manager",
            "Sales Representative",
            "Marketing Manager",
            "Financial Analyst",
            "Operations Manager",
            "Team Lead",
            "Director",
        ]
        locations = ["New York", "San Francisco", "London", "Singapore", "Remote"]

        employees = []
        for i in range(1, 21):  # 20 mock employees
            emp = MockEmployee(
                id=str(i),
                first_name=f"Employee{i}",
                last_name=f"Test{i}",
                email=f"employee{i}@testcompany.com",
                phone=f"+1-555-010-{i:04d}",
                department=secrets.choice(departments),
                position=secrets.choice(positions),
                hire_date=(
                    datetime.now() - timedelta(days=secrets.randbelow(970) + 30)
                ).strftime("%Y-%m-%d"),
                employment_status="active" if i % 10 != 0 else "inactive",
                manager_id=str(secrets.randbelow(4) + 1) if i > 5 else None,
                location=secrets.choice(locations),
            )
            employees.append(emp)

        return employees

    def _generate_mock_attendance(self) -> List[MockAttendance]:
        """Generate mock attendance data."""
        attendance = []
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        current_date = start_date
        record_id = 1

        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            for employee in self.employees[:15]:  # Only active employees
                if secrets.SystemRandom().random() > 0.2:  # 80% attendance rate
                    clock_in_hour = secrets.randbelow(2) + 8
                    clock_out_hour = secrets.randbelow(3) + 16
                    hours_worked = (
                        clock_out_hour - clock_in_hour - random.uniform(0.5, 1.5)
                    )  # Lunch break

                    att = MockAttendance(
                        id=str(record_id),
                        employee_id=employee.id,
                        date=current_date.strftime("%Y-%m-%d"),
                        clock_in=f"{current_date.strftime('%Y-%m-%d')}T{clock_in_hour:02d}:00:00",
                        clock_out=f"{current_date.strftime('%Y-%m-%d')}T{clock_out_hour:02d}:00:00",
                        hours_worked=round(hours_worked, 2),
                        status="present",
                    )
                    attendance.append(att)
                    record_id += 1

            current_date += timedelta(days=1)

        return attendance

    def _generate_mock_leaves(self) -> List[MockLeave]:
        """Generate mock leave records."""
        leave_types = ["vacation", "sick", "personal", "maternity", "paternity"]
        statuses = ["pending", "approved", "rejected"]

        leaves = []
        for i in range(1, 16):  # 15 mock leave requests
            start_date = date.today() + timedelta(days=random.randint(-30, 60))
            end_date = start_date + timedelta(days=secrets.randbelow(9) + 1)

            leave = MockLeave(
                id=str(i),
                employee_id=str(secrets.randbelow(14) + 1),
                leave_type=secrets.choice(leave_types),
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                days_taken=(end_date - start_date).days + 1,
                status=secrets.choice(statuses),
                reason=f"Mock leave reason {i}",
            )
            leaves.append(leave)

        return leaves

    def _setup_routes(self):
        """Setup API routes based on platform."""

        # Universal routes that work for all platforms
        @self.app.route("/api/health")
        def health_check():
            return jsonify(
                {
                    "status": "healthy",
                    "platform": self.platform,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route("/api/employees")
        def get_employees():
            department = request.args.get("department")
            status = request.args.get("status", "active")

            filtered_employees = self.employees

            if status:
                filtered_employees = [
                    emp for emp in filtered_employees if emp.employment_status == status
                ]

            if department:
                filtered_employees = [
                    emp for emp in filtered_employees if emp.department == department
                ]

            return jsonify(
                {
                    "status": "success",
                    "data": [asdict(emp) for emp in filtered_employees],
                    "count": len(filtered_employees),
                }
            )

        @self.app.route("/api/employees/<employee_id>")
        def get_employee(employee_id):
            employee = next(
                (emp for emp in self.employees if emp.id == employee_id), None
            )
            if not employee:
                abort(404, description="Employee not found")

            return jsonify({"status": "success", "data": asdict(employee)})

        @self.app.route("/api/attendance")
        def get_attendance():
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            employee_id = request.args.get("employee_id")

            filtered_attendance = self.attendance

            if start_date:
                filtered_attendance = [
                    att for att in filtered_attendance if att.date >= start_date
                ]
            if end_date:
                filtered_attendance = [
                    att for att in filtered_attendance if att.date <= end_date
                ]
            if employee_id:
                filtered_attendance = [
                    att for att in filtered_attendance if att.employee_id == employee_id
                ]

            return jsonify(
                {
                    "status": "success",
                    "data": [asdict(att) for att in filtered_attendance],
                    "count": len(filtered_attendance),
                }
            )

        @self.app.route("/api/leaves")
        def get_leaves():
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            employee_id = request.args.get("employee_id")
            status = request.args.get("status")

            filtered_leaves = self.leaves

            if start_date:
                filtered_leaves = [
                    leave for leave in filtered_leaves if leave.start_date >= start_date
                ]
            if end_date:
                filtered_leaves = [
                    leave for leave in filtered_leaves if leave.end_date <= end_date
                ]
            if employee_id:
                filtered_leaves = [
                    leave
                    for leave in filtered_leaves
                    if leave.employee_id == employee_id
                ]
            if status:
                filtered_leaves = [
                    leave for leave in filtered_leaves if leave.status == status
                ]

            return jsonify(
                {
                    "status": "success",
                    "data": [asdict(leave) for leave in filtered_leaves],
                    "count": len(filtered_leaves),
                }
            )

        # Platform-specific routes
        if self.platform == "orangehrm":
            self._setup_orangehrm_routes()
        elif self.platform == "quickbooks_workforce":
            self._setup_quickbooks_routes()
        else:
            self._setup_generic_routes()

    def _setup_orangehrm_routes(self):
        """Setup OrangeHRM-specific API routes."""

        @self.app.route("/api/v2/employees")
        def orangehrm_employees():
            # OrangeHRM v2 API format
            return jsonify(
                {
                    "data": [
                        asdict(emp)
                        for emp in self.employees
                        if emp.employment_status == "active"
                    ]
                }
            )

        @self.app.route("/api/v2/search/employees")
        def orangehrm_search():
            query = request.args.get("q", "").lower()
            matched = [
                emp
                for emp in self.employees
                if query in emp.first_name.lower() or query in emp.last_name.lower()
            ]
            return jsonify({"data": [asdict(emp) for emp in matched]})

    def _setup_quickbooks_routes(self):
        """Setup QuickBooks Workforce-specific API routes."""

        @self.app.route("/api/v1/users")
        def quickbooks_users():
            active = request.args.get("active", "true").lower() == "true"
            filtered = (
                [emp for emp in self.employees if emp.employment_status == "active"]
                if active
                else self.employees
            )

            return jsonify({"results": [asdict(emp) for emp in filtered]})

        @self.app.route("/api/v1/timesheets")
        def quickbooks_timesheets():
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            company_id = request.args.get("company_id", "12345")

            filtered_attendance = self.attendance

            if start_date:
                filtered_attendance = [
                    att for att in filtered_attendance if att.date >= start_date
                ]
            if end_date:
                filtered_attendance = [
                    att for att in filtered_attendance if att.date <= end_date
                ]

            return jsonify({"results": [asdict(att) for att in filtered_attendance]})

    def _setup_generic_routes(self):
        """Setup generic API routes for custom platforms."""

        @self.app.route("/api/v1/employees/search")
        def search_employees():
            term = request.args.get("term", "").lower()
            matched = [
                emp
                for emp in self.employees
                if term in emp.first_name.lower() or term in emp.last_name.lower()
            ]
            return jsonify({"employees": [asdict(emp) for emp in matched]})

        @self.app.route("/api/v1/reports/headcount")
        def headcount_report():
            department_counts = {}
            for emp in self.employees:
                dept = emp.department
                department_counts[dept] = department_counts.get(dept, 0) + 1

            return jsonify(
                {
                    "headcount": department_counts,
                    "total": len(self.employees),
                    "active": len(
                        [
                            emp
                            for emp in self.employees
                            if emp.employment_status == "active"
                        ]
                    ),
                }
            )

    def run(self):
        """Run the development server."""
        logger.info(
            f"Starting {self.platform} HRIS development server on port {self.port}"
        )
        logger.info(f"Available endpoints:")
        logger.info(f"  - http://localhost:{self.port}/api/health")
        logger.info(f"  - http://localhost:{self.port}/api/employees")
        logger.info(f"  - http://localhost:{self.port}/api/attendance")
        logger.info(f"  - http://localhost:{self.port}/api/leaves")

        self.app.run(host="0.0.0.0", port=self.port, debug=True)


def main():
    parser = argparse.ArgumentParser(description="HRIS Development Server")
    parser.add_argument(
        "--platform",
        choices=["orangehrm", "quickbooks_workforce", "generic"],
        default="orangehrm",
        help="HRIS platform to simulate",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to run server on")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    server = HRISDevServer(args.platform, args.port)
    server.run()


if __name__ == "__main__":
    main()
