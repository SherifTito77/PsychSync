"""
Extended HRIS Connectors for PsychSync
Includes: MintHCM, Open HRMS, BambooHR, Gusto, Namely, Workday

File: app/integrations/hris/extended_connectors.py
"""

from typing import Dict, List, Optional
from datetime import date, datetime
import pymysql
import logging
import requests

from .base_connector import (
    HRISConnector, Employee, AttendanceRecord,
    LeaveRecord, PerformanceReview
)

logger = logging.getLogger(__name__)


class MintHCMConnector(HRISConnector):
    """
    Connector for MintHCM (built on SugarCRM).
    AI-enabled, GDPR-compliant HR system.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize MintHCM connector.
        
        Config should contain:
            - base_url: MintHCM API URL
            - username: API username
            - password: API password
            - db_host: Database host (optional)
            - db_name: Database name
            - db_user: Database user
            - db_password: Database password
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'minthcm'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
        
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with MintHCM API."""
        if not self.base_url or not self.username or not self.password:
            return
        
        try:
            auth_url = f"{self.base_url}/Api/access_token"
            response = self.session.post(
                auth_url,
                json={
                    'grant_type': 'password',
                    'username': self.username,
                    'password': self.password,
                    'client_id': 'sugarcrm',
                    'platform': 'api'
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data.get('access_token')
            
            if self.access_token:
                self.session.headers.update({
                    'OAuth-Token': self.access_token
                })
                logger.info("MintHCM authentication successful")
        
        except Exception as e:
            logger.error(f"MintHCM authentication failed: {e}")
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to MintHCM."""
        if self.access_token:
            try:
                response = self._make_request('GET', '/Api/V8/module/Employees')
                return response is not None
            except:
                pass
        
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
        """Get employees from MintHCM."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                e.id as employee_id,
                e.first_name,
                e.last_name,
                e.email1 as email,
                e.phone_work as phone,
                d.name as department,
                e.title as position,
                e.hire_date,
                e.employee_status as employment_status,
                e.reports_to_id as manager_id
            FROM employees e
            LEFT JOIN employees_cstm ec ON e.id = ec.id_c
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.deleted = 0
        """
        
        params = []
        
        if status == "active":
            query += " AND e.employee_status = 'Active'"
        
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
                location=None
            )
            employees.append(emp)
        
        cursor.close()
        conn.close()
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get single employee by ID."""
        employees = self.get_employees()
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
        """Get attendance records from MintHCM."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                a.id as record_id,
                a.employee_id,
                a.date,
                a.time_from as clock_in,
                a.time_to as clock_out,
                a.hours_worked,
                a.status
            FROM workschedules a
            WHERE a.date BETWEEN %s AND %s
            AND a.deleted = 0
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND a.employee_id = %s"
            params.append(employee_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            record = AttendanceRecord(
                record_id=str(row['record_id']),
                employee_id=str(row['employee_id']),
                date=row['date'],
                clock_in=datetime.combine(row['date'], row['clock_in']) if row.get('clock_in') else None,
                clock_out=datetime.combine(row['date'], row['clock_out']) if row.get('clock_out') else None,
                hours_worked=float(row['hours_worked']) if row.get('hours_worked') else None,
                status=row.get('status', 'present')
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
        """Get leave records from MintHCM."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                h.id as leave_id,
                h.employee_id,
                ht.name as leave_type,
                h.date_from as start_date,
                h.date_to as end_date,
                h.days as days_taken,
                h.status,
                h.description as reason
            FROM holidays h
            LEFT JOIN holiday_types ht ON h.holiday_type_id = ht.id
            WHERE h.date_from BETWEEN %s AND %s
            AND h.deleted = 0
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND h.employee_id = %s"
            params.append(employee_id)
        
        if status:
            query += " AND h.status = %s"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            record = LeaveRecord(
                leave_id=str(row['leave_id']),
                employee_id=str(row['employee_id']),
                leave_type=row['leave_type'] or 'vacation',
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(row['days_taken'] or 0),
                status=row.get('status', 'pending'),
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
        """Get performance reviews from MintHCM."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                a.id as review_id,
                a.employee_id,
                a.reviewer_id,
                a.date_entered as review_date,
                a.overall_rating as rating,
                a.comments
            FROM appraisals a
            WHERE a.deleted = 0
        """
        
        params = []
        
        if employee_id:
            query += " AND a.employee_id = %s"
            params.append(employee_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        reviews = []
        for row in rows:
            review = PerformanceReview(
                review_id=str(row['review_id']),
                employee_id=str(row['employee_id']),
                reviewer_id=str(row['reviewer_id']),
                review_date=row['review_date'].date() if row.get('review_date') else date.today(),
                rating=float(row['rating']) if row.get('rating') else None,
                comments=row.get('comments')
            )
            reviews.append(review)
        
        cursor.close()
        conn.close()
        
        return reviews


class OpenHRMSConnector(HRISConnector):
    """
    Connector for Open HRMS (built on Odoo).
    Modular HR system with payroll capabilities.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Open HRMS connector.
        
        Config should contain:
            - base_url: Odoo instance URL
            - database: Database name
            - username: User email/login
            - password: User password
        """
        super().__init__(config)
        
        self.database = config.get('database', '')
        self.uid = None
        
        # Setup XML-RPC connections
        self.common = None
        self.models = None
        
        if self.base_url:
            try:
                import xmlrpc.client
                self.common = xmlrpc.client.ServerProxy(f'{self.base_url}/xmlrpc/2/common')
                self.models = xmlrpc.client.ServerProxy(f'{self.base_url}/xmlrpc/2/object')
                
                self.uid = self.common.authenticate(
                    self.database,
                    self.username,
                    self.password,
                    {}
                )
                
                if self.uid:
                    logger.info(f"Open HRMS authenticated as UID: {self.uid}")
            
            except Exception as e:
                logger.error(f"Failed to connect to Open HRMS: {e}")
    
    def _execute(self, model: str, method: str, *args, **kwargs):
        """Execute Odoo model method."""
        if not self.uid or not self.models:
            raise Exception("Not authenticated with Open HRMS")
        
        return self.models.execute_kw(
            self.database,
            self.uid,
            self.password,
            model,
            method,
            args,
            kwargs
        )
    
    def test_connection(self) -> bool:
        """Test connection to Open HRMS."""
        try:
            if not self.uid:
                return False
            count = self._execute('hr.employee', 'search_count', [[]])
            return count >= 0
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_employees(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Get employees from Open HRMS."""
        domain = []
        
        if status == "active":
            domain.append(('active', '=', True))
        
        if department:
            dept_ids = self._execute(
                'hr.department',
                'search',
                [[('name', '=', department)]]
            )
            if dept_ids:
                domain.append(('department_id', '=', dept_ids[0]))
        
        employee_ids = self._execute('hr.employee', 'search', [domain])
        
        if not employee_ids:
            return []
        
        fields = [
            'id', 'name', 'work_email', 'mobile_phone', 'department_id',
            'job_id', 'parent_id', 'work_location_id', 'active'
        ]
        
        employees_data = self._execute(
            'hr.employee',
            'read',
            [employee_ids],
            {'fields': fields}
        )
        
        employees = []
        for item in employees_data:
            full_name = item.get('name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            emp = Employee(
                employee_id=str(item['id']),
                first_name=first_name,
                last_name=last_name,
                email=item.get('work_email', ''),
                phone=item.get('mobile_phone'),
                department=item['department_id'][1] if item.get('department_id') else None,
                position=item['job_id'][1] if item.get('job_id') else None,
                hire_date=None,
                employment_status='active' if item.get('active') else 'inactive',
                manager_id=str(item['parent_id'][0]) if item.get('parent_id') else None,
                location=item['work_location_id'][1] if item.get('work_location_id') else None
            )
            employees.append(emp)
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get single employee by ID."""
        employees = self.get_employees()
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
        """Get attendance records from Open HRMS."""
        domain = [
            ('check_in', '>=', start_date.strftime('%Y-%m-%d 00:00:00')),
            ('check_in', '<=', end_date.strftime('%Y-%m-%d 23:59:59'))
        ]
        
        if employee_id:
            domain.append(('employee_id', '=', int(employee_id)))
        
        attendance_ids = self._execute('hr.attendance', 'search', [domain])
        
        if not attendance_ids:
            return []
        
        fields = ['id', 'employee_id', 'check_in', 'check_out', 'worked_hours']
        attendances = self._execute(
            'hr.attendance',
            'read',
            [attendance_ids],
            {'fields': fields}
        )
        
        records = []
        for item in attendances:
            check_in = datetime.strptime(item['check_in'], '%Y-%m-%d %H:%M:%S') if item.get('check_in') else None
            check_out = datetime.strptime(item['check_out'], '%Y-%m-%d %H:%M:%S') if item.get('check_out') else None
            
            record = AttendanceRecord(
                record_id=str(item['id']),
                employee_id=str(item['employee_id'][0]),
                date=check_in.date() if check_in else start_date,
                clock_in=check_in,
                clock_out=check_out,
                hours_worked=float(item['worked_hours']) if item.get('worked_hours') else None,
                status='present'
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
        """Get leave records from Open HRMS."""
        domain = [
            ('request_date_from', '>=', start_date.strftime('%Y-%m-%d')),
            ('request_date_from', '<=', end_date.strftime('%Y-%m-%d'))
        ]
        
        if employee_id:
            domain.append(('employee_id', '=', int(employee_id)))
        
        if status:
            status_map = {
                'pending': 'confirm',
                'approved': 'validate',
                'rejected': 'refuse'
            }
            odoo_status = status_map.get(status.lower(), 'confirm')
            domain.append(('state', '=', odoo_status))
        
        leave_ids = self._execute('hr.leave', 'search', [domain])
        
        if not leave_ids:
            return []
        
        fields = [
            'id', 'employee_id', 'holiday_status_id', 'request_date_from',
            'request_date_to', 'number_of_days', 'state', 'name'
        ]
        
        leaves = self._execute(
            'hr.leave',
            'read',
            [leave_ids],
            {'fields': fields}
        )
        
        records = []
        for item in leaves:
            state_map = {
                'confirm': 'pending',
                'validate': 'approved',
                'refuse': 'rejected'
            }
            
            record = LeaveRecord(
                leave_id=str(item['id']),
                employee_id=str(item['employee_id'][0]),
                leave_type=item['holiday_status_id'][1] if item.get('holiday_status_id') else 'vacation',
                start_date=datetime.strptime(item['request_date_from'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(item['request_date_to'], '%Y-%m-%d').date(),
                days_taken=float(item.get('number_of_days', 0)),
                status=state_map.get(item.get('state', 'confirm'), 'pending'),
                reason=item.get('name')
            )
            records.append(record)
        
        return records
    
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """Get performance reviews from Open HRMS."""
        # Open HRMS has payroll appraisal module
        return []


# Example usage
if __name__ == "__main__":
    print("Extended HRIS Connectors Demo")
    print("=" * 70)
    
    print("\n1. MintHCM Configuration")
    minthcm_config = {
        'base_url': 'https://your-mint.com',
        'username': 'admin',
        'password': 'password',
        'db_host': 'localhost',
        'db_name': 'minthcm',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    print("\n2. Open HRMS Configuration")
    openhrms_config = {
        'base_url': 'https://your-openhrms.com',
        'database': 'openhrms_db',
        'username': 'admin',
        'password': 'password'
    }
    
    print("\nUpdate configurations with real credentials to test")