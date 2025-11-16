"""
IceHRM Connector for PsychSync
Integrates with IceHRM via REST API and database.

File: app/integrations/hris/icehrm_connector.py

IceHRM: Lightweight HRIS for startups & SMBs
API Documentation: https://icehrm.com/explore/documentation/
"""

from typing import Dict, List, Optional
from datetime import date, datetime
import pymysql
import logging

from .base_connector import (
    HRISConnector, Employee, AttendanceRecord,
    LeaveRecord, PerformanceReview
)

logger = logging.getLogger(__name__)


class IceHRMConnector(HRISConnector):
    """
    Connector for IceHRM.
    Supports both REST API and direct database access.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize IceHRM connector.
        
        Config should contain:
            - base_url: IceHRM installation URL
            - api_key: API key from Settings > API
            - db_host: Database host (optional)
            - db_name: Database name
            - db_user: Database username
            - db_password: Database password
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'icehrm'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
        
        # Setup API authentication
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to IceHRM."""
        # Try API first
        if self.api_key:
            try:
                response = self._make_request('GET', '/api/employees')
                if response:
                    return True
            except:
                pass
        
        # Try database
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
        """Get employees from IceHRM."""
        if self.api_key:
            return self._get_employees_api(department, status)
        return self._get_employees_db(department, status)
    
    def _get_employees_api(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees via API."""
        params = {'status': 'Active' if status == 'active' else 'Terminated'}
        response = self._make_request('GET', '/api/employees', params=params)
        
        if not response or 'data' not in response:
            return []
        
        employees = []
        for item in response['data']:
            emp = Employee(
                employee_id=str(item.get('id', '')),
                first_name=item.get('first_name', ''),
                last_name=item.get('last_name', ''),
                email=item.get('work_email', ''),
                phone=item.get('mobile_phone'),
                department=item.get('department'),
                position=item.get('job_title'),
                hire_date=datetime.strptime(item['joined_date'], '%Y-%m-%d').date() if item.get('joined_date') else None,
                employment_status=item.get('employment_status', 'active'),
                manager_id=str(item.get('supervisor')) if item.get('supervisor') else None,
                location=item.get('work_location')
            )
            
            if department and emp.department != department:
                continue
            
            employees.append(emp)
        
        return employees
    
    def _get_employees_db(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees via database."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                e.id as employee_id,
                e.first_name,
                e.last_name,
                e.work_email as email,
                e.mobile_phone as phone,
                d.name as department,
                j.name as position,
                e.joined_date as hire_date,
                e.employment_status,
                e.supervisor as manager_id,
                e.work_station as location
            FROM Employees e
            LEFT JOIN CompanyStructures d ON e.department = d.id
            LEFT JOIN JobTitles j ON e.job_title = j.id
            WHERE 1=1
        """
        
        params = []
        
        if status == "active":
            query += " AND e.employment_status = %s"
            params.append('Active')
        
        if department:
            query += " AND d.name = %s"
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
        if self.api_key:
            response = self._make_request('GET', f'/api/employees/{employee_id}')
            if response and 'data' in response:
                item = response['data']
                return Employee(
                    employee_id=str(item.get('id', '')),
                    first_name=item.get('first_name', ''),
                    last_name=item.get('last_name', ''),
                    email=item.get('work_email', ''),
                    phone=item.get('mobile_phone'),
                    department=item.get('department'),
                    position=item.get('job_title'),
                    hire_date=datetime.strptime(item['joined_date'], '%Y-%m-%d').date() if item.get('joined_date') else None,
                    employment_status=item.get('employment_status', 'active'),
                    manager_id=str(item.get('supervisor')) if item.get('supervisor') else None,
                    location=item.get('work_location')
                )
        
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
                a.id as record_id,
                a.employee as employee_id,
                a.in_time as clock_in,
                a.out_time as clock_out,
                a.note
            FROM Attendance a
            WHERE DATE(a.in_time) BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND a.employee = %s"
            params.append(employee_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
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
                status='present'
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
                l.employee as employee_id,
                lt.name as leave_type,
                l.date_start as start_date,
                l.date_end as end_date,
                l.details as reason,
                l.status
            FROM EmployeeLeaves l
            LEFT JOIN LeaveTypes lt ON l.leave_type = lt.id
            WHERE l.date_start BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND l.employee = %s"
            params.append(employee_id)
        
        if status:
            query += " AND l.status = %s"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Calculate days
            days_taken = (row['end_date'] - row['start_date']).days + 1
            
            record = LeaveRecord(
                leave_id=str(row['leave_id']),
                employee_id=str(row['employee_id']),
                leave_type=row['leave_type'] or 'vacation',
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(days_taken),
                status=row['status'] or 'pending',
                reason=row['reason']
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
        """Get performance reviews."""
        # IceHRM has limited performance review features
        return []


# Example usage
if __name__ == "__main__":
    print("IceHRM Connector Demo")
    print("=" * 60)
    
    config = {
        'base_url': 'https://your-icehrm.com',
        'api_key': 'your_api_key',
        'db_host': 'localhost',
        'db_name': 'icehrm',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    connector = IceHRMConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful\n")
        
        employees = connector.get_employees()
        print(f"Employees: {len(employees)}")
    else:
        print("✗ Connection failed")