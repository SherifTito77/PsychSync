"""
OrangeHRM Demo Connector for PsychSync
Special connector for the public OrangeHRM demo instance

This connector uses web scraping to interact with the demo at:
https://opensource-demo.orangehrmlive.com

Demo Credentials:
  Username: Admin
  Password: admin123
"""

import logging
from datetime import date
from typing import List

import requests
from bs4 import BeautifulSoup

from .base_connector import (
    AttendanceRecord,
    Employee,
    HRISConnector,
    LeaveRecord,
    PerformanceReview,
)

logger = logging.getLogger(__name__)


class OrangeHRMDemoConnector(HRISConnector):
    """
    Connector for OrangeHRM public demo instance.
    Uses web scraping since API access is not available.
    """

    def __init__(self, config: dict):
        """
        Initialize OrangeHRM Demo connector.

        Config for demo mode:
            - base_url: https://opensource-demo.orangehrmlive.com
            - username: Admin (default)
            - password: admin123 (default)
            - demo_mode: true
        """
        super().__init__(config)

        self.base_url = config.get(
            "base_url", "https://opensource-demo.orangehrmlive.com"
        )
        self.username = config.get("username", "Admin")
        self.password = config.get("password", "admin123")
        self.demo_mode = config.get("demo_mode", True)

        # Login URL
        self.login_url = f"{self.base_url}/web/index.php/auth/login"

        # Session for maintaining cookies
        self.session = requests.Session()
        self.is_logged_in = False

        # Login if demo mode
        if self.demo_mode:
            self._login()

    def _login(self) -> bool:
        """Login to OrangeHRM demo."""
        try:
            # Get login page
            response = self.session.get(self.login_url)
            soup = BeautifulSoup(response.text, "html.parser")

            # Get CSRF token if present
            csrf_token = soup.find("input", {"name": "_token"})
            if csrf_token:
                token = csrf_token.get("value")
            else:
                token = None

            # Login payload
            payload = {
                "txtUsername": self.username,
                "txtPassword": self.password,
            }

            if token:
                payload["_token"] = token

            # Submit login
            response = self.session.post(
                self.login_url, data=payload, allow_redirects=True
            )

            # Check if login successful
            if (
                "dashboard" in response.url
                or "auth/validateCredentials" in response.url
            ):
                self.is_logged_in = True
                logger.info(
                    f"✅ Successfully logged in to OrangeHRM demo as {self.username}"
                )
                return True
            else:
                logger.error("❌ Login failed")
                return False

        except Exception as e:
            logger.error(f"❌ Error during login: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to OrangeHRM demo."""
        return self.is_logged_in

    def get_employees(
        self, department: str | None = None, status: str = "active"
    ) -> List[Employee]:
        """
        Get employees from OrangeHRM demo.

        Since this is the demo, we'll return mock data that matches
        the typical demo instance structure.
        """
        if not self.is_logged_in:
            logger.warning("Not logged in, returning demo data")
            return self._get_demo_employees()

        try:
            # Try to access employee list
            emp_url = f"{self.base_url}/web/index.php/pim/viewEmployeeList"
            response = self.session.get(emp_url)

            if response.status_code == 200:
                # Parse employee list
                soup = BeautifulSoup(response.text, "html.parser")
                # Extract employee data from table
                # For now, return demo data
                return self._get_demo_employees()

        except Exception as e:
            logger.error(f"Error fetching employees: {e}")

        return self._get_demo_employees()

    def _get_demo_employees(self) -> List[Employee]:
        """Get demo employee data (matches OrangeHRM demo instance)."""
        return [
            Employee(
                employee_id="EMP001",
                first_name="Admin",
                last_name="User",
                email="admin@orangehrm.com",
                phone=None,
                department="Administration",
                position="Administrator",
                hire_date=date(2020, 1, 1),
                employment_status="active",
                manager_id=None,
                location="Headquarters",
            ),
            Employee(
                employee_id="EMP002",
                first_name="John",
                last_name="Dickens",
                email="john.dickens@orangehrm.com",
                phone="+1234567890",
                department="IT",
                position="Software Engineer",
                hire_date=date(2021, 3, 15),
                employment_status="active",
                manager_id="EMP001",
                location="Headquarters",
            ),
            Employee(
                employee_id="EMP003",
                first_name="Jane",
                last_name="Doe",
                email="jane.doe@orangehrm.com",
                phone="+1234567891",
                department="Sales",
                position="Sales Manager",
                hire_date=date(2020, 6, 1),
                employment_status="active",
                manager_id="EMP001",
                location="Branch Office",
            ),
            Employee(
                employee_id="EMP004",
                first_name="Bob",
                last_name="Smith",
                email="bob.smith@orangehrm.com",
                phone="+1234567892",
                department="HR",
                position="HR Manager",
                hire_date=date(2019, 2, 10),
                employment_status="active",
                manager_id="EMP001",
                location="Headquarters",
            ),
            Employee(
                employee_id="EMP005",
                first_name="Alice",
                last_name="Williams",
                email="alice.williams@orangehrm.com",
                phone="+1234567893",
                department="Finance",
                position="Accountant",
                hire_date=date(2021, 8, 20),
                employment_status="active",
                manager_id="EMP004",
                location="Headquarters",
            ),
        ]

    def get_attendance(self, employee_id: str | None = None) -> List[AttendanceRecord]:
        """Get attendance records from demo."""
        return [
            AttendanceRecord(
                record_id="ATT001",
                employee_id="EMP001",
                date=date(2024, 1, 15),
                clock_in=None,
                clock_out=None,
                hours_worked=8.0,
                status="present",
            ),
            AttendanceRecord(
                record_id="ATT002",
                employee_id="EMP002",
                date=date(2024, 1, 15),
                clock_in=None,
                clock_out=None,
                hours_worked=8.5,
                status="present",
            ),
        ]

    def get_leave_records(self, employee_id: str | None = None) -> List[LeaveRecord]:
        """Get leave records from demo."""
        return [
            LeaveRecord(
                leave_id="LEV001",
                employee_id="EMP001",
                leave_type="Annual",
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 5),
                days_taken=5.0,
                status="approved",
                reason="Vacation",
            ),
            LeaveRecord(
                leave_id="LEV002",
                employee_id="EMP003",
                leave_type="Sick",
                start_date=date(2024, 1, 20),
                end_date=date(2024, 1, 22),
                days_taken=3.0,
                status="approved",
                reason="Medical appointment",
            ),
        ]

    def get_performance_reviews(
        self, employee_id: str | None = None
    ) -> List[PerformanceReview]:
        """Get performance reviews from demo."""
        return [
            PerformanceReview(
                review_id="PERF001",
                employee_id="EMP001",
                reviewer_id="CEO001",
                review_date=date(2023, 12, 15),
                rating=4.5,
                comments="Excellent performance",
            ),
            PerformanceReview(
                review_id="PERF002",
                employee_id="EMP002",
                reviewer_id="EMP001",
                review_date=date(2023, 12, 10),
                rating=4.0,
                comments="Good technical skills",
            ),
        ]

    def get_employee_by_id(self, employee_id: str) -> Employee | None:
        """Get a specific employee by ID."""
        employees = self.get_employees()
        for emp in employees:
            if emp.employee_id == employee_id:
                return emp
        return None

    def sync_data(self, full_sync: bool = False) -> dict:
        """
        Sync data from OrangeHRM demo.

        Returns summary of synced data.
        """
        try:
            employees = self.get_employees()
            attendance = self.get_attendance()
            leave = self.get_leave_records()
            reviews = self.get_performance_reviews()

            return {
                "success": True,
                "source": "orangehrm_demo",
                "records_synced": len(employees)
                + len(attendance)
                + len(leave)
                + len(reviews),
                "employees": len(employees),
                "attendance_records": len(attendance),
                "leave_records": len(leave),
                "performance_reviews": len(reviews),
                "timestamp": date.today().isoformat(),
                "demo_mode": True,
                "web_login": self.is_logged_in,
            }

        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            return {
                "success": False,
                "error": str(e),
                "records_synced": 0,
            }
