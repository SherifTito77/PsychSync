"""
Frappe HR / ERPNext Connector for PsychSync
Works with both Frappe HR and ERPNext HR modules.

File: app/integrations/hris/frappe_connector.py

Frappe HR: Python-based, highly customizable HR system
ERPNext: Full ERP with comprehensive HR modules
API Documentation: https://frappeframework.com/docs/user/en/api
"""

from typing import Dict, List, Optional
from datetime import date, datetime
import logging

from .base_connector import (
    HRISConnector, Employee, AttendanceRecord,
    LeaveRecord, PerformanceReview
)

logger = logging.getLogger(__name__)


class FrappeHRConnector(HRISConnector):
    """
    Connector for Frappe HR and ERPNext.
    Uses Frappe REST API with token authentication.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Frappe HR connector.
        
        Config should contain:
            - base_url: Frappe instance URL (e.g., https://your-site.erpnext.com)
            - api_key: API key from user settings
            - api_secret: API secret from user settings
        """
        super().__init__(config)
        
        self.api_secret = config.get('api_secret')
        
        # Setup authentication headers
        if self.api_key and self.api_secret:
            self.session.headers.update({
                'Authorization': f'token {self.api_key}:{self.api_secret}',
                'Content-Type': 'application/json'
            })
    
    def test_connection(self) -> bool:
        """Test connection to Frappe."""
        try:
            response = self._make_request('GET', '/api/resource/Employee?limit_page_length=1')
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_employees(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees from Frappe HR."""
        params = {
            'fields': '["name","employee_name","prefered_email","cell_number",' +
                     '"department","designation","date_of_joining","status",' +
                     '"reports_to","location"]',
            'limit_page_length': 10000
        }
        
        filters = []
        
        if status == "active":
            filters.append(['status', '=', 'Active'])
        elif status == "inactive":
            filters.append(['status', 'in', ['Left', 'Suspended']])
        
        if department:
            filters.append(['department', '=', department])
        
        if filters:
            import json
            params['filters'] = json.dumps(filters)
        
        response = self._make_request('GET', '/api/resource/Employee', params=params)
        
        if not response or 'data' not in response:
            return []
        
        employees = []
        for item in response['data']:
            # Split employee name
            full_name = item.get('employee_name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            emp = Employee(
                employee_id=item.get('name', ''),
                first_name=first_name,
                last_name=last_name,
                email=item.get('prefered_email', ''),
                phone=item.get('cell_number'),
                department=item.get('department'),
                position=item.get('designation'),
                hire_date=datetime.strptime(item['date_of_joining'], '%Y-%m-%d').date() if item.get('date_of_joining') else None,
                employment_status=item.get('status', 'Active').lower(),
                manager_id=item.get('reports_to'),
                location=item.get('location')
            )
            employees.append(emp)
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get single employee by ID."""
        try:
            response = self._make_request('GET', f'/api/resource/Employee/{employee_id}')
            
            if not response or 'data' not in response:
                return None
            
            item = response['data']
            full_name = item.get('employee_name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            return Employee(
                employee_id=item.get('name', ''),
                first_name=first_name,
                last_name=last_name,
                email=item.get('prefered_email', ''),
                phone=item.get('cell_number'),
                department=item.get('department'),
                position=item.get('designation'),
                hire_date=datetime.strptime(item['date_of_joining'], '%Y-%m-%d').date() if item.get('date_of_joining') else None,
                employment_status=item.get('status', 'Active').lower(),
                manager_id=item.get('reports_to'),
                location=item.get('location')
            )
        except Exception as e:
            logger.error(f"Error fetching employee {employee_id}: {e}")
            return None
    
    def get_attendance(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None
    ) -> List[AttendanceRecord]:
        """Get attendance records from Frappe HR."""
        import json
        
        filters = [
            ['attendance_date', 'between', [start_date.isoformat(), end_date.isoformat()]]
        ]
        
        if employee_id:
            filters.append(['employee', '=', employee_id])
        
        params = {
            'fields': '["name","employee","attendance_date","status","working_hours"]',
            'filters': json.dumps(filters),
            'limit_page_length': 10000
        }
        
        response = self._make_request('GET', '/api/resource/Attendance', params=params)
        
        if not response or 'data' not in response:
            return []
        
        records = []
        for item in response['data']:
            record = AttendanceRecord(
                record_id=item.get('name', ''),
                employee_id=item.get('employee', ''),
                date=datetime.strptime(item['attendance_date'], '%Y-%m-%d').date(),
                clock_in=None,  # Frappe doesn't track exact times by default
                clock_out=None,
                hours_worked=float(item['working_hours']) if item.get('working_hours') else None,
                status=item.get('status', 'Present').lower()
            )
            records.append(record)
        
        return records
    
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """Get leave records from Frappe HR."""
        import json
        
        filters = [
            ['from_date', '>=', start_date.isoformat()],
            ['from_date', '<=', end_date.isoformat()]
        ]
        
        if employee_id:
            filters.append(['employee', '=', employee_id])
        
        if status:
            # Map status to Frappe status
            status_map = {
                'pending': 'Open',
                'approved': 'Approved',
                'rejected': 'Rejected',
                'cancelled': 'Cancelled'
            }
            frappe_status = status_map.get(status.lower(), 'Open')
            filters.append(['status', '=', frappe_status])
        
        params = {
            'fields': '["name","employee","leave_type","from_date","to_date",' +
                     '"total_leave_days","status","description"]',
            'filters': json.dumps(filters),
            'limit_page_length': 10000
        }
        
        response = self._make_request('GET', '/api/resource/Leave Application', params=params)
        
        if not response or 'data' not in response:
            return []
        
        records = []
        for item in response['data']:
            # Map Frappe status back
            status_map = {
                'Open': 'pending',
                'Approved': 'approved',
                'Rejected': 'rejected',
                'Cancelled': 'cancelled'
            }
            
            record = LeaveRecord(
                leave_id=item.get('name', ''),
                employee_id=item.get('employee', ''),
                leave_type=item.get('leave_type', 'vacation'),
                start_date=datetime.strptime(item['from_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(item['to_date'], '%Y-%m-%d').date(),
                days_taken=float(item.get('total_leave_days', 0)),
                status=status_map.get(item.get('status', 'Open'), 'pending'),
                reason=item.get('description')
            )
            records.append(record)
        
        return records
    
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """Get performance appraisals from Frappe HR."""
        import json
        
        filters = []
        
        if employee_id:
            filters.append(['employee', '=', employee_id])
        
        if start_date:
            filters.append(['start_date', '>=', start_date.isoformat()])
        
        if end_date:
            filters.append(['end_date', '<=', end_date.isoformat()])
        
        params = {
            'fields': '["name","employee","start_date","end_date","total_score","remarks"]',
            'limit_page_length': 10000
        }
        
        if filters:
            params['filters'] = json.dumps(filters)
        
        response = self._make_request('GET', '/api/resource/Appraisal', params=params)
        
        if not response or 'data' not in response:
            return []
        
        reviews = []
        for item in response['data']:
            review = PerformanceReview(
                review_id=item.get('name', ''),
                employee_id=item.get('employee', ''),
                reviewer_id='',  # Not available in basic appraisal doctype
                review_date=datetime.strptime(item['end_date'], '%Y-%m-%d').date() if item.get('end_date') else date.today(),
                rating=float(item['total_score']) if item.get('total_score') else None,
                comments=item.get('remarks')
            )
            reviews.append(review)
        
        return reviews


class ERPNextConnector(FrappeHRConnector):
    """
    Connector for ERPNext HR module.
    Inherits from FrappeHRConnector since ERPNext is built on Frappe.
    """
    
    def __init__(self, config: Dict):
        """Initialize ERPNext connector (same as Frappe HR)."""
        super().__init__(config)
        logger.info("ERPNext connector initialized (using Frappe HR API)")


# Example usage
if __name__ == "__main__":
    print("Frappe HR / ERPNext Connector Demo")
    print("=" * 60)
    
    config = {
        'base_url': 'https://your-site.erpnext.com',
        'api_key': 'your_api_key',
        'api_secret': 'your_api_secret'
    }
    
    # Works for both Frappe HR and ERPNext
    connector = FrappeHRConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful\n")
        
        employees = connector.get_employees(status="active")
        print(f"Active employees: {len(employees)}")
        
        if employees:
            print(f"\nFirst employee: {employees[0].first_name} {employees[0].last_name}")
            print(f"Department: {employees[0].department}")
        
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        attendance = connector.get_attendance(start_date, end_date)
        print(f"\nAttendance records: {len(attendance)}")
        
        leaves = connector.get_leave_records(start_date, end_date)
        print(f"Leave records: {len(leaves)}")
    else:
        print("✗ Connection failed")