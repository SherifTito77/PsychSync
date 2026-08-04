"""
QuickBooks Workforce Connector for PsychSync
Example of creating a new HRIS connector from scratch.

File: app/integrations/hris/quickbooks_workforce_connector.py

Usage:
    connector = QuickBooksWorkforceConnector(config)
    employees = connector.get_employees()
    attendance = connector.get_attendance(start_date, end_date)
"""

import logging
from datetime import date, datetime
from typing import Any

import requests

from .base_connector import (
    AttendanceRecord,
    Employee,
    HRISConnector,
    LeaveRecord,
    PerformanceReview,
)

logger = logging.getLogger(__name__)


class QuickBooksWorkforceConnector(HRISConnector):
    """
    QuickBooks Workforce Connector.

    QuickBooks Workforce (formerly TSheets) provides time tracking, scheduling,
    and HR management. This connector integrates with their REST API.

    API Documentation: https://developers.intuit.com/app/developer/timesheets/docs/api
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize QuickBooks Workforce connector.

        Required config:
            - client_id: OAuth2 client ID
            - client_secret: OAuth2 client secret
            - redirect_uri: OAuth2 redirect URI
            - access_token: OAuth2 access token (or use authentication flow)
            - refresh_token: OAuth2 refresh token
            - company_id: QuickBooks company ID
            - base_url: API base URL (default: https://rest.tsheets.com/api/v1)

        Optional config:
            - timeout: Request timeout in seconds
            - retry_attempts: Number of retry attempts
        """
        super().__init__(config)

        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.access_token = config["access_token"]
        self.refresh_token = config.get("refresh_token")
        self.company_id = config["company_id"]
        self.timeout = config.get("timeout", 30)
        self.retry_attempts = config.get("retry_attempts", 3)

        # Setup OAuth2 authentication
        self._setup_oauth()

    def _setup_oauth(self):
        """Setup OAuth2 authentication for QuickBooks API."""
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "User-Agent": "PsychSync-HRIS-Connector/1.0",
            }
        )

    def _refresh_access_token(self):
        """Refresh OAuth2 access token."""
        try:
            response = requests.post(
                "https://oauth.intuit.com/oauth2/v1/tokens/bearer",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {self._get_basic_auth()}",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                },
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]

            # Update session headers with new token
            self._setup_oauth()

            logger.info("Successfully refreshed access token")

        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise ConnectionError("Failed to refresh QuickBooks access token") from e

    def _get_basic_auth(self) -> str:
        """Get basic auth string for token refresh."""
        import base64

        auth_string = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(auth_string.encode()).decode()

    def _make_api_request(
        self, endpoint: str, method: str = "GET", **kwargs
    ) -> dict | None:
        """Make API request with retry logic and token refresh."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method, url=url, timeout=self.timeout, **kwargs
                )

                # Check for token expiry
                if response.status_code == 401 and attempt < self.retry_attempts - 1:
                    logger.info("Access token expired, refreshing...")
                    self._refresh_access_token()
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt == self.retry_attempts - 1:
                    raise
                continue

        return None

    def test_connection(self) -> bool:
        """Test connection to QuickBooks Workforce API."""
        try:
            # Try to get current user info
            response = self._make_api_request("current_user")
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_employees(
        self, department: str | None = None, status: str = "active"
    ) -> list[Employee]:
        """Get employees from QuickBooks Workforce."""
        try:
            # Get all users
            endpoint = f"users?active=true&per_page=500&company_id={self.company_id}"
            response = self._make_api_request(endpoint)

            if not response or "results" not in response:
                return []

            employees = []
            for user_data in response["results"]:
                # Filter by status
                if status == "active" and not user_data.get("active", False):
                    continue

                # Filter by department (custom field)
                if department:
                    user_departments = self._get_user_department(user_data["id"])
                    if department not in user_departments:
                        continue

                employee = Employee(
                    employee_id=str(user_data["id"]),
                    first_name=user_data.get("first_name", "").strip(),
                    last_name=user_data.get("last_name", "").strip(),
                    email=user_data.get("email", ""),
                    phone=user_data.get("mobile_number"),
                    department=(
                        self._get_user_department(user_data["id"])[0]
                        if self._get_user_department(user_data["id"])
                        else None
                    ),
                    position=user_data.get("job_title"),
                    hire_date=self._parse_date(user_data.get("hire_date")),
                    employment_status=(
                        "active" if user_data.get("active", False) else "inactive"
                    ),
                    manager_id=(
                        str(user_data.get("manager_id"))
                        if user_data.get("manager_id")
                        else None
                    ),
                    location=user_data.get("location_name"),
                )
                employees.append(employee)

            logger.info(
                f"Retrieved {len(employees)} employees from QuickBooks Workforce"
            )
            return employees

        except Exception as e:
            logger.error(f"Failed to get employees: {e}")
            return []

    def get_employee_by_id(self, employee_id: str) -> Employee | None:
        """Get single employee by ID."""
        try:
            endpoint = f"users/{employee_id}?company_id={self.company_id}"
            response = self._make_api_request(endpoint)

            if not response:
                return None

            user_data = response
            return Employee(
                employee_id=str(user_data["id"]),
                first_name=user_data.get("first_name", "").strip(),
                last_name=user_data.get("last_name", "").strip(),
                email=user_data.get("email", ""),
                phone=user_data.get("mobile_number"),
                department=(
                    self._get_user_department(user_data["id"])[0]
                    if self._get_user_department(user_data["id"])
                    else None
                ),
                position=user_data.get("job_title"),
                hire_date=self._parse_date(user_data.get("hire_date")),
                employment_status=(
                    "active" if user_data.get("active", False) else "inactive"
                ),
                manager_id=(
                    str(user_data.get("manager_id"))
                    if user_data.get("manager_id")
                    else None
                ),
                location=user_data.get("location_name"),
            )

        except Exception as e:
            logger.error(f"Failed to get employee {employee_id}: {e}")
            return None

    def get_attendance(
        self, start_date: date, end_date: date, employee_id: str | None = None
    ) -> list[AttendanceRecord]:
        """Get attendance records from QuickBooks Workforce."""
        try:
            attendance_records = []

            # Get timesheet data
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            endpoint = f"timesheets?start_date={start_str}&end_date={end_str}&company_id={self.company_id}"
            if employee_id:
                endpoint += f"&user_ids={employee_id}"

            response = self._make_api_request(endpoint)

            if not response or "results" not in response:
                return []

            for timesheet in response["results"]:
                # Get timesheet details with actual hours
                details_endpoint = (
                    f"timesheets/{timesheet['id']}/details?company_id={self.company_id}"
                )
                details_response = self._make_api_request(details_endpoint)

                if details_response and "results" in details_response:
                    for detail in details_response["results"]:
                        record = AttendanceRecord(
                            record_id=str(detail["id"]),
                            employee_id=str(timesheet["user_id"]),
                            date=self._parse_date(detail["date"]),
                            clock_in=self._parse_datetime(detail.get("clock_in")),
                            clock_out=self._parse_datetime(detail.get("clock_out")),
                            hours_worked=(
                                float(detail.get("duration", 0)) / 3600
                                if detail.get("duration")
                                else None
                            ),
                            status=(
                                "present" if detail.get("duration", 0) > 0 else "absent"
                            ),
                        )
                        attendance_records.append(record)

            logger.info(f"Retrieved {len(attendance_records)} attendance records")
            return attendance_records

        except Exception as e:
            logger.error(f"Failed to get attendance records: {e}")
            return []

    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: str | None = None,
        status: str | None = None,
    ) -> list[LeaveRecord]:
        """Get leave records from QuickBooks Workforce."""
        try:
            leave_records = []

            # Get time off requests
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            endpoint = f"time_off_requests?start_date={start_str}&end_date={end_str}&company_id={self.company_id}"
            if employee_id:
                endpoint += f"&user_ids={employee_id}"

            response = self._make_api_request(endpoint)

            if not response or "results" not in response:
                return []

            for time_off in response["results"]:
                # Filter by status if specified
                if status and time_off.get("status") != status:
                    continue

                record = LeaveRecord(
                    leave_id=str(time_off["id"]),
                    employee_id=str(time_off["user_id"]),
                    leave_type=time_off.get("time_off_type_id", "vacation"),
                    start_date=self._parse_date(time_off["start_date"]),
                    end_date=self._parse_date(time_off["end_date"]),
                    days_taken=time_off.get("amount", 0),
                    status=time_off.get("status", "pending"),
                    reason=time_off.get("notes"),
                )
                leave_records.append(record)

            logger.info(f"Retrieved {len(leave_records)} leave records")
            return leave_records

        except Exception as e:
            logger.error(f"Failed to get leave records: {e}")
            return []

    def get_performance_reviews(
        self,
        employee_id: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[PerformanceReview]:
        """Get performance reviews (limited in QuickBooks Workforce)."""
        try:
            # QuickBooks Workforce has limited performance review functionality
            # We'll create reviews based on performance metrics and feedback
            reviews = []

            # Get performance data if available
            endpoint = f"performance_data?company_id={self.company_id}"
            if employee_id:
                endpoint += f"&user_ids={employee_id}"

            response = self._make_api_request(endpoint)

            if not response or "results" not in response:
                return []

            for perf_data in response["results"]:
                # Convert performance data to review format
                review = PerformanceReview(
                    review_id=str(perf_data["id"]),
                    employee_id=str(perf_data["user_id"]),
                    reviewer_id=str(perf_data.get("manager_id", "system")),
                    review_date=self._parse_date(perf_data.get("review_date")),
                    rating=float(perf_data.get("performance_score", 0)),
                    comments=perf_data.get("feedback"),
                    goals=[perf_data.get("goal", "")] if perf_data.get("goal") else [],
                )
                reviews.append(review)

            return reviews

        except Exception as e:
            logger.error(f"Failed to get performance reviews: {e}")
            return []

    def _get_user_department(self, user_id: str) -> list[str]:
        """Get department(s) for a user from custom fields."""
        try:
            endpoint = f"users/{user_id}/customfields?company_id={self.company_id}"
            response = self._make_api_request(endpoint)

            if not response or "results" not in response:
                return []

            departments = []
            for custom_field in response["results"]:
                # Look for department custom field
                if "department" in custom_field.get("name", "").lower():
                    departments.append(custom_field.get("value", ""))

            return departments

        except Exception:
            return []

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object."""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, datetime_str: str | None) -> datetime | None:
        """Parse datetime string to datetime object."""
        if not datetime_str:
            return None

        try:
            return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        except (ValueError, TypeError):
            try:
                return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return None


# Register the connector
def register_connector():
    """Register this connector with the integration manager."""
    from .integration_manager import HRISIntegrationManager

    HRISIntegrationManager.CONNECTORS["quickbooks_workforce"] = (
        QuickBooksWorkforceConnector
    )

    # Add configuration template
    HRISIntegrationManager.CONFIG_TEMPLATES["quickbooks_workforce"] = {
        "required": ["client_id", "client_secret", "access_token", "company_id"],
        "optional": [
            "refresh_token",
            "redirect_uri",
            "base_url",
            "timeout",
            "retry_attempts",
        ],
        "description": "QuickBooks Workforce (formerly TSheets) time tracking and HR management",
    }


# Example usage
if __name__ == "__main__":
    print("QuickBooks Workforce Connector Demo")
    print("=" * 60)

    # Configuration example
    config = {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "access_token": "your_access_token",
        "refresh_token": "your_refresh_token",
        "company_id": "12345",
        "base_url": "https://rest.tsheets.com/api/v1",
        "timeout": 30,
        "retry_attempts": 3,
    }

    connector = QuickBooksWorkforceConnector(config)

    if connector.test_connection():
        print("✓ Connection successful")

        # Test getting employees
        employees = connector.get_employees(status="active")
        print(f"\nFound {len(employees)} active employees")

        # Test getting attendance for last 7 days
        from datetime import timedelta

        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        attendance = connector.get_attendance(start_date, end_date)
        print(f"Found {len(attendance)} attendance records in last 7 days")

    else:
        print("✗ Connection failed")
