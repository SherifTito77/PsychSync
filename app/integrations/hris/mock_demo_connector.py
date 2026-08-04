"""
Mock Demo HRIS Connector
Local mock connector for testing without external dependencies
"""

import logging
from datetime import date, datetime, timedelta
from typing import List

from .base_connector import (
    AttendanceRecord,
    Employee,
    HRISConnector,
    LeaveRecord,
    PerformanceReview,
)

logger = logging.getLogger(__name__)


class MockDemoConnector(HRISConnector):
    """
    Mock HRIS connector for development and testing.
    Returns realistic sample data without external dependencies.
    """

    def __init__(self, config: dict):
        """Initialize mock connector."""
        super().__init__(config)
        self.demo_mode = config.get("demo_mode", True)
        logger.info("✅ Mock Demo Connector initialized")

    def test_connection(self) -> bool:
        """Test connection (always successful for mock)."""
        logger.info("✅ Mock connection test successful")
        return True

    def get_employee_by_id(self, employee_id: str) -> Employee:
        """Get a specific employee by ID."""
        employees = self.get_employees()
        for emp in employees:
            if emp.employee_id == employee_id:
                logger.info(f"✅ Found employee {employee_id}")
                return emp

        raise ValueError(f"Employee {employee_id} not found")

    def get_employees(self) -> List[Employee]:
        """Get mock employee data."""
        logger.info("Fetching mock employees...")

        employees = [
            Employee(
                employee_id="EMP001",
                first_name="John",
                last_name="Smith",
                email="john.smith@company.com",
                department="Engineering",
                position="Senior Software Engineer",
                employment_status="active",
                hire_date=date(2020, 3, 15),
            ),
            Employee(
                employee_id="EMP002",
                first_name="Sarah",
                last_name="Johnson",
                email="sarah.j@company.com",
                department="Engineering",
                position="DevOps Engineer",
                employment_status="active",
                hire_date=date(2021, 6, 1),
            ),
            Employee(
                employee_id="EMP003",
                first_name="Michael",
                last_name="Chen",
                email="michael.chen@company.com",
                department="Product",
                position="Product Manager",
                employment_status="active",
                hire_date=date(2019, 11, 10),
            ),
            Employee(
                employee_id="EMP004",
                first_name="Emily",
                last_name="Davis",
                email="emily.davis@company.com",
                department="HR",
                position="HR Manager",
                employment_status="active",
                hire_date=date(2018, 2, 20),
            ),
            Employee(
                employee_id="EMP005",
                first_name="David",
                last_name="Wilson",
                email="david.wilson@company.com",
                department="Sales",
                position="Sales Representative",
                employment_status="active",
                hire_date=date(2022, 1, 5),
            ),
            Employee(
                employee_id="EMP006",
                first_name="Lisa",
                last_name="Anderson",
                email="lisa.anderson@company.com",
                department="Marketing",
                position="Marketing Specialist",
                employment_status="leave",
                hire_date=date(2021, 9, 15),
            ),
        ]

        logger.info(f"✅ Returning {len(employees)} mock employees")
        return employees

    def get_departments(self) -> List[dict]:
        """Get mock department data."""
        logger.info("Fetching mock departments...")

        departments = [
            {"id": "DEPT001", "name": "Engineering", "headcount": 45},
            {"id": "DEPT002", "name": "Product", "headcount": 12},
            {"id": "DEPT003", "name": "HR", "headcount": 8},
            {"id": "DEPT004", "name": "Sales", "headcount": 25},
            {"id": "DEPT005", "name": "Marketing", "headcount": 15},
            {"id": "DEPT006", "name": "Finance", "headcount": 10},
        ]

        logger.info(f"✅ Returning {len(departments)} mock departments")
        return departments

    def get_attendance(
        self, start_date: date, end_date: date
    ) -> List[AttendanceRecord]:
        """Get mock attendance records."""
        logger.info(f"Fetching mock attendance from {start_date} to {end_date}...")

        records = []
        current_date = start_date

        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                for emp_id in ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"]:
                    records.append(
                        AttendanceRecord(
                            record_id=f"ATT-{current_date.strftime('%Y%m%d')}-{emp_id}",
                            employee_id=emp_id,
                            date=current_date,
                            clock_in=datetime.combine(
                                current_date, datetime.min.time()
                            ).replace(hour=9, minute=0),
                            clock_out=datetime.combine(
                                current_date, datetime.min.time()
                            ).replace(hour=17, minute=30),
                            hours_worked=8.5,
                            status="present",
                        )
                    )

            current_date += timedelta(days=1)

        logger.info(f"✅ Returning {len(records)} mock attendance records")
        return records

    def get_leave_records(self, start_date: date, end_date: date) -> List[LeaveRecord]:
        """Get mock leave records."""
        logger.info(f"Fetching mock leave records from {start_date} to {end_date}...")

        records = [
            LeaveRecord(
                leave_id="LV-001",
                employee_id="EMP001",
                leave_type="Vacation",
                start_date=date(2024, 1, 15),
                end_date=date(2024, 1, 19),
                days_taken=5.0,
                status="approved",
                reason="Family vacation",
            ),
            LeaveRecord(
                leave_id="LV-002",
                employee_id="EMP003",
                leave_type="Sick",
                start_date=date(2024, 1, 8),
                end_date=date(2024, 1, 9),
                days_taken=2.0,
                status="approved",
                reason="Medical appointment",
            ),
            LeaveRecord(
                leave_id="LV-003",
                employee_id="EMP006",
                leave_type="Parental",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                days_taken=90.0,
                status="approved",
                reason="Parental leave",
            ),
        ]

        logger.info(f"✅ Returning {len(records)} mock leave records")
        return records

    def get_performance_reviews(
        self, employee_id: str = None
    ) -> List[PerformanceReview]:
        """Get mock performance reviews."""
        logger.info("Fetching mock performance reviews...")

        reviews = [
            PerformanceReview(
                review_id="PR-001",
                employee_id="EMP001",
                reviewer_id="EMP004",
                review_date=date(2023, 12, 15),
                rating=4.5,
                comments="Excellent performance on key projects",
            ),
            PerformanceReview(
                review_id="PR-002",
                employee_id="EMP002",
                reviewer_id="EMP003",
                review_date=date(2023, 12, 16),
                rating=4.2,
                comments="Strong technical skills, good collaboration",
            ),
            PerformanceReview(
                review_id="PR-003",
                employee_id="EMP003",
                reviewer_id="EMP004",
                review_date=date(2023, 12, 17),
                rating=4.7,
                comments="Outstanding product leadership",
            ),
        ]

        if employee_id:
            reviews = [r for r in reviews if r.employee_id == employee_id]

        logger.info(f"✅ Returning {len(reviews)} mock performance reviews")
        return reviews
