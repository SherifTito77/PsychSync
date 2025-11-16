"""
OrangeHRM Connector for PsychSync
Integrates with OrangeHRM API and database.

File: app/integrations/hris/orangehrm_connector.py

OrangeHRM API Documentation: https://orangehrm.github.io/orangehrm-api-doc/
"""

from typing import Dict, List, Optional
from datetime import date, datetime
from dateutil import parser
import pymysql
import logging

from .base_connector import (
    HRISConnector, Employee, AttendanceRecord,
    LeaveRecord, PerformanceReview
)

logger = logging.getLogger(__name__)


class OrangeHRMConnector(HRISConnector):
    """
    Connector for OrangeHRM (open-source HRIS).
    Supports both API and direct database access.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize OrangeHRM connector.
        
        Config should contain:
            - base_url: OrangeHRM API URL (e.g., https://your-domain.com/api/v2)
            - api_key: OAuth 2.0 client credentials
            - client_id: OAuth client ID
            - client_secret: OAuth client secret
            - db_host: Database host (optional, for direct DB access)
            - db_name: Database name
            - db_user: Database username
            - db_password: Database password
        """
        super().__init__(config)
        
        # Database configuration
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'orangehrm'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
        
        # OAuth configuration
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = None
        
        # Get access token
        if self.client_id and self.client_secret:
            self._get_access_token()
    
    def _get_access_token(self):
        """Get OAuth 2.0 access token."""
        token_url = f"{self.base_url}/oauth/issueToken"
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        try:
            response = self.session.post(token_url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            # Update session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            logger.info("OAuth token obtained successfully")
        
        except Exception as e:
            logger.error(f"Failed to get OAuth token: {e}")
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to OrangeHRM."""
        # Try API first
        try:
            response = self._make_request('GET', '/employees')
            if response:
                return True
        except:
            pass
        
        # Try database connection
        try:
            conn = self._get_db_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_employees(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees from OrangeHRM."""
        # Try API first
        if self.access_token:
            return self._get_employees_api(department, status)
        
        # Fall back to database
        return self._get_employees_db(department, status)
    
    def _get_employees_api(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees via API."""
        params = {
            'limit': 1000,
            'offset': 0
        }
        
        if status == "active":
            params['empStatus'] = 'Active'
        
        response = self._make_request('GET', '/employees', params=params)
        
        if not response or 'data' not in response:
            return []
        
        employees = []
        for item in response['data']:
            emp = Employee(
                employee_id=str(item.get('empNumber', '')),
                first_name=item.get('firstName', ''),
                last_name=item.get('lastName', ''),
                email=item.get('workEmail', ''),
                phone=item.get('workTelephone'),
                department=item.get('subunit', {}).get('name') if isinstance(item.get('subunit'), dict) else None,
                position=item.get('jobTitle', {}).get('title') if isinstance(item.get('jobTitle'), dict) else None,
                hire_date=parser.parse(item['joinedDate']).date() if item.get('joinedDate') else None,
                employment_status=item.get('empStatus', {}).get('name', 'active') if isinstance(item.get('empStatus'), dict) else 'active',
                manager_id=str(item.get('supervisor', {}).get('empNumber')) if isinstance(item.get('supervisor'), dict) else None,
                location=item.get('location', {}).get('name') if isinstance(item.get('location'), dict) else None
            )
            
            # Filter by department if specified
            if department and emp.department != department:
                continue
            
            employees.append(emp)
        
        return employees
    
    def _get_employees_db(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees via direct database access."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                e.emp_number as employee_id,
                e.emp_firstname as first_name,
                e.emp_lastname as last_name,
                e.emp_work_email as email,
                e.emp_mobile as phone,
                su.name as department,
                jt.job_title_name as position,
                e.joined_date as hire_date,
                es.name as employment_status,
                sup.emp_number as manager_id,
                l.name as location
            FROM hs_hr_employee e
            LEFT JOIN ohrm_subunit su ON e.work_station = su.id
            LEFT JOIN ohrm_job_title jt ON e.job_title_code = jt.id
            LEFT JOIN ohrm_employment_status es ON e.emp_status = es.id
            LEFT JOIN hs_hr_employee sup ON e.supervisor_id = sup.emp_number
            LEFT JOIN ohrm_location l ON e.location_id = l.id
            WHERE 1=1
        """
        
        params = []
        
        if status == "active":
            query += " AND es.name = %s"
            params.append('Active')
        
        if department:
            query += " AND su.name = %s"
            params.append(department)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            emp = Employee(
                employee_id=str(row['employee_id']),
                first_name=row['first_name'] or '',
                last_name=row['last_name'] or '',
                email=row['email'] or '',
                phone=row['phone'],
                department=row['department'],
                position=row['position'],
                hire_date=row['hire_date'],
                employment_status=row['employment_status'] or 'active',
                manager_id=str(row['manager_id']) if row['manager_id'] else None,
                location=row['location']
            )
            employees.append(emp)
        
        cursor.close()
        conn.close()
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get single employee by ID."""
        # Try API
        if self.access_token:
            response = self._make_request('GET', f'/employees/{employee_id}')
            if response and 'data' in response:
                item = response['data']
                return Employee(
                    employee_id=str(item.get('empNumber', '')),
                    first_name=item.get('firstName', ''),
                    last_name=item.get('lastName', ''),
                    email=item.get('workEmail', ''),
                    phone=item.get('workTelephone'),
                    department=item.get('subunit', {}).get('name'),
                    position=item.get('jobTitle', {}).get('title'),
                    hire_date=parser.parse(item['joinedDate']).date() if item.get('joinedDate') else None,
                    employment_status=item.get('empStatus', {}).get('name', 'active'),
                    manager_id=str(item.get('supervisor', {}).get('empNumber')),
                    location=item.get('location', {}).get('name')
                )
        
        # Fall back to database
        employees = self._get_employees_db()
        for emp in employees:
            if emp.employee_id == employee_id:
                return emp
        
        return None
    
    def get_attendance(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None
    ) -> List[AttendanceRecord]:
        """Get attendance records."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                ar.id as record_id,
                ar.employee_id,
                ar.punch_in_utc_time as clock_in,
                ar.punch_out_utc_time as clock_out,
                ar.punch_in_note,
                ar.state as status
            FROM ohrm_attendance_record ar
            WHERE DATE(ar.punch_in_utc_time) BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND ar.employee_id = %s"
            params.append(employee_id)
        
        query += " ORDER BY ar.punch_in_utc_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Calculate hours worked
            hours_worked = None
            if row['clock_in'] and row['clock_out']:
                delta = row['clock_out'] - row['clock_in']
                hours_worked = delta.total_seconds() / 3600
            
            record = AttendanceRecord(
                record_id=str(row['record_id']),
                employee_id=str(row['employee_id']),
                date=row['clock_in'].date() if row['clock_in'] else start_date,
                clock_in=row['clock_in'],
                clock_out=row['clock_out'],
                hours_worked=hours_worked,
                status=row['status'] or 'present'
            )
            records.append(record)
        
        cursor.close()
        conn.close()
        
        return records
    
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """Get leave records."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                l.id as leave_id,
                l.emp_number as employee_id,
                lt.name as leave_type,
                l.date as leave_date,
                l.length_hours,
                l.length_days as days_taken,
                l.status,
                l.comments as reason
            FROM ohrm_leave l
            LEFT JOIN ohrm_leave_type lt ON l.leave_type_id = lt.id
            WHERE l.date BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND l.emp_number = %s"
            params.append(employee_id)
        
        if status:
            query += " AND l.status = %s"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Group by leave_id to get date ranges
        leaves_dict = {}
        for row in rows:
            leave_id = str(row['leave_id'])
            if leave_id not in leaves_dict:
                leaves_dict[leave_id] = {
                    'leave_id': leave_id,
                    'employee_id': str(row['employee_id']),
                    'leave_type': row['leave_type'] or 'vacation',
                    'dates': [row['leave_date']],
                    'days_taken': float(row['days_taken'] or 0),
                    'status': row['status'] or 'pending',
                    'reason': row['reason']
                }
            else:
                leaves_dict[leave_id]['dates'].append(row['leave_date'])
                leaves_dict[leave_id]['days_taken'] += float(row['days_taken'] or 0)
        
        # Convert to LeaveRecord objects
        records = []
        for leave_data in leaves_dict.values():
            dates = sorted(leave_data['dates'])
            record = LeaveRecord(
                leave_id=leave_data['leave_id'],
                employee_id=leave_data['employee_id'],
                leave_type=leave_data['leave_type'],
                start_date=dates[0],
                end_date=dates[-1],
                days_taken=leave_data['days_taken'],
                status=leave_data['status'],
                reason=leave_data['reason']
            )
            records.append(record)
        
        cursor.close()
        conn.close()
        
        return records
    
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """Get performance review records."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                pr.id as review_id,
                pr.employee_number as employee_id,
                pr.reviewer_id,
                pr.review_period_start,
                pr.review_period_end,
                pr.rating,
                pr.comments
            FROM ohrm_performance_review pr
            WHERE 1=1
        """
        
        params = []
        
        if employee_id:
            query += " AND pr.employee_number = %s"
            params.append(employee_id)
        
        if start_date:
            query += " AND pr.review_period_start >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND pr.review_period_end <= %s"
            params.append(end_date)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        reviews = []
        for row in rows:
            review = PerformanceReview(
                review_id=str(row['review_id']),
                employee_id=str(row['employee_id']),
                reviewer_id=str(row['reviewer_id']),
                review_date=row['review_period_end'] or date.today(),
                rating=float(row['rating']) if row['rating'] else None,
                comments=row['comments']
            )
            reviews.append(review)
        
        cursor.close()
        conn.close()
        
        return reviews


# Example usage
if __name__ == "__main__":
    print("OrangeHRM Connector Demo")
    print("=" * 60)
    
    # Configuration
    config = {
        'base_url': 'https://your-orangehrm.com/symfony/web/index.php/api/v2',
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'db_host': 'localhost',
        'db_name': 'orangehrm',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    connector = OrangeHRMConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful\n")
        
        # Get employees
        employees = connector.get_employees(status="active")
        print(f"Active employees: {len(employees)}")
        
        if employees:
            print(f"First employee: {employees[0].first_name} {employees[0].last_name}")
            print(f"Department: {employees[0].department}")
            print(f"Position: {employees[0].position}")
        
        # Get attendance for last 30 days
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        attendance = connector.get_attendance(start_date, end_date)
        print(f"\nAttendance records (last 30 days): {len(attendance)}")
        
        # Get leave records
        leaves = connector.get_leave_records(start_date, end_date)
        print(f"Leave records (last 30 days): {len(leaves)}")
        
        # Export to CSV
        if employees:
            filepath = connector.export_to_csv(
                employees,
                f'orangehrm_employees_{date.today()}.csv'
            )
            print(f"\nExported employees to: {filepath}")
    
    else:
        print("✗ Connection failed")