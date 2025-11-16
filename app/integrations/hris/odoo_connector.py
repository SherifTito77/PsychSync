"""
Odoo HR Connector for PsychSync
Integrates with Odoo HR modules via XML-RPC API.

File: app/integrations/hris/odoo_connector.py

Odoo: Complete business suite with comprehensive HR modules
API Documentation: https://www.odoo.com/documentation/16.0/developer/reference/external_api.html
"""

from typing import Dict, List, Optional
from datetime import date, datetime
import xmlrpc.client
import logging

from .base_connector import (
    HRISConnector, Employee, AttendanceRecord,
    LeaveRecord, PerformanceReview
)

logger = logging.getLogger(__name__)


class OdooHRConnector(HRISConnector):
    """
    Connector for Odoo HR.
    Uses XML-RPC API for integration.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Odoo HR connector.
        
        Config should contain:
            - base_url: Odoo instance URL (e.g., https://your-instance.odoo.com)
            - database: Database name
            - username: User email/login
            - password: User password or API key
        """
        super().__init__(config)
        
        self.database = config.get('database', '')
        self.uid = None
        
        # Setup XML-RPC connections
        self.common = None
        self.models = None
        
        if self.base_url:
            try:
                self.common = xmlrpc.client.ServerProxy(f'{self.base_url}/xmlrpc/2/common')
                self.models = xmlrpc.client.ServerProxy(f'{self.base_url}/xmlrpc/2/object')
                
                # Authenticate
                self.uid = self.common.authenticate(
                    self.database,
                    self.username,
                    self.password,
                    {}
                )
                
                if self.uid:
                    logger.info(f"Authenticated with Odoo as UID: {self.uid}")
                else:
                    logger.error("Odoo authentication failed")
            
            except Exception as e:
                logger.error(f"Failed to connect to Odoo: {e}")
    
    def _execute(self, model: str, method: str, *args, **kwargs):
        """Execute Odoo model method."""
        if not self.uid or not self.models:
            raise Exception("Not authenticated with Odoo")
        
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
        """Test connection to Odoo."""
        try:
            if not self.uid:
                return False
            
            # Try to read employee count
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
        """Get employees from Odoo HR."""
        domain = []
        
        if status == "active":
            domain.append(('active', '=', True))
        elif status == "inactive":
            domain.append(('active', '=', False))
        
        if department:
            # Search for department ID first
            dept_ids = self._execute(
                'hr.department',
                'search',
                [[('name', '=', department)]]
            )
            if dept_ids:
                domain.append(('department_id', '=', dept_ids[0]))
        
        # Search employees
        employee_ids = self._execute('hr.employee', 'search', [domain])
        
        if not employee_ids:
            return []
        
        # Read employee details
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
            # Split name
            full_name = item.get('name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get contract for hire date
            hire_date = None
            try:
                contract_ids = self._execute(
                    'hr.contract',
                    'search',
                    [[('employee_id', '=', item['id'])], ('state', '=', 'open')],
                    {'limit': 1}
                )
                if contract_ids:
                    contracts = self._execute(
                        'hr.contract',
                        'read',
                        [contract_ids],
                        {'fields': ['date_start']}
                    )
                    if contracts and contracts[0].get('date_start'):
                        hire_date = datetime.strptime(
                            contracts[0]['date_start'],
                            '%Y-%m-%d'
                        ).date()
            except:
                pass
            
            emp = Employee(
                employee_id=str(item['id']),
                first_name=first_name,
                last_name=last_name,
                email=item.get('work_email', ''),
                phone=item.get('mobile_phone'),
                department=item['department_id'][1] if item.get('department_id') else None,
                position=item['job_id'][1] if item.get('job_id') else None,
                hire_date=hire_date,
                employment_status='active' if item.get('active') else 'inactive',
                manager_id=str(item['parent_id'][0]) if item.get('parent_id') else None,
                location=item['work_location_id'][1] if item.get('work_location_id') else None
            )
            employees.append(emp)
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get single employee by ID."""
        try:
            fields = [
                'id', 'name', 'work_email', 'mobile_phone', 'department_id',
                'job_id', 'parent_id', 'work_location_id', 'active'
            ]
            
            employees_data = self._execute(
                'hr.employee',
                'read',
                [[int(employee_id)]],
                {'fields': fields}
            )
            
            if not employees_data:
                return None
            
            item = employees_data[0]
            full_name = item.get('name', '')
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            return Employee(
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
        
        except Exception as e:
            logger.error(f"Error fetching employee {employee_id}: {e}")
            return None
    
    def get_attendance(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None
    ) -> List[AttendanceRecord]:
        """Get attendance records from Odoo."""
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
        """Get leave records from Odoo."""
        domain = [
            ('request_date_from', '>=', start_date.strftime('%Y-%m-%d')),
            ('request_date_from', '<=', end_date.strftime('%Y-%m-%d'))
        ]
        
        if employee_id:
            domain.append(('employee_id', '=', int(employee_id)))
        
        if status:
            # Map status to Odoo states
            status_map = {
                'pending': 'confirm',
                'approved': 'validate',
                'rejected': 'refuse',
                'cancelled': 'cancel'
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
            # Map Odoo state back
            state_map = {
                'confirm': 'pending',
                'validate': 'approved',
                'validate1': 'approved',
                'refuse': 'rejected',
                'cancel': 'cancelled'
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
        """Get performance appraisals from Odoo."""
        # Odoo doesn't have built-in performance reviews in community edition
        # This would require custom modules or enterprise edition
        logger.info("Performance reviews require Odoo Enterprise or custom modules")
        return []


# Example usage
if __name__ == "__main__":
    print("Odoo HR Connector Demo")
    print("=" * 60)
    
    config = {
        'base_url': 'https://your-instance.odoo.com',
        'database': 'your_database',
        'username': 'admin',
        'password': 'your_password'
    }
    
    connector = OdooHRConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful\n")
        
        employees = connector.get_employees(status="active")
        print(f"Active employees: {len(employees)}")
        
        if employees:
            print(f"\nFirst employee: {employees[0].first_name} {employees[0].last_name}")
        
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        attendance = connector.get_attendance(start_date, end_date)
        print(f"\nAttendance records: {len(attendance)}")
    else:
        print("✗ Connection failed")