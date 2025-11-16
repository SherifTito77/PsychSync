"""
Additional HRIS Connectors for PsychSync
Includes: Dolibarr, OpenCATS (ATS), and Jorani

File: app/integrations/hris/additional_connectors.py
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


class DolibarrConnector(HRISConnector):
    """
    Connector for Dolibarr ERP/CRM/HR.
    Lightweight modular system with HR capabilities.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Dolibarr connector.
        
        Config should contain:
            - base_url: Dolibarr API URL
            - api_key: DOLAPIKEY from user settings
            - db_host: Database host (optional)
            - db_name: Database name
            - db_user: Database user
            - db_password: Database password
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'dolibarr'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
        
        # Dolibarr uses DOLAPIKEY header
        if self.api_key:
            self.session.headers.update({
                'DOLAPIKEY': self.api_key,
                'Accept': 'application/json'
            })
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to Dolibarr."""
        # Try API
        if self.api_key:
            try:
                response = self._make_request('GET', '/users')
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
        """Get employees from Dolibarr."""
        # Dolibarr stores employees in llx_user table
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                u.rowid as employee_id,
                u.firstname as first_name,
                u.lastname as last_name,
                u.email,
                u.user_mobile as phone,
                u.job,
                u.fk_user as manager_id,
                u.statut as status
            FROM llx_user u
            WHERE u.employee = 1
        """
        
        params = []
        
        if status == "active":
            query += " AND u.statut = 1"
        elif status == "inactive":
            query += " AND u.statut = 0"
        
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
                department=None,  # Dolibarr doesn't have built-in departments
                position=row['job'],
                hire_date=None,
                employment_status='active' if row['status'] == 1 else 'inactive',
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
        """Get attendance records."""
        # Dolibarr attendance in llx_holiday table (time off)
        return []
    
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """Get leave records from Dolibarr."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                h.rowid as leave_id,
                h.fk_user as employee_id,
                ht.label as leave_type,
                h.date_debut as start_date,
                h.date_fin as end_date,
                h.halfday,
                h.statut as status,
                h.description as reason
            FROM llx_holiday h
            LEFT JOIN llx_c_holiday_types ht ON h.fk_type = ht.rowid
            WHERE DATE(h.date_debut) BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND h.fk_user = %s"
            params.append(employee_id)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Calculate days
            days = (row['end_date'] - row['start_date']).days + 1
            if row['halfday']:
                days = days - 0.5
            
            # Map status
            status_map = {1: 'pending', 2: 'approved', 3: 'rejected'}
            
            record = LeaveRecord(
                leave_id=str(row['leave_id']),
                employee_id=str(row['employee_id']),
                leave_type=row['leave_type'] or 'vacation',
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(days),
                status=status_map.get(row['status'], 'pending'),
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
        """Performance reviews not available in Dolibarr."""
        return []


class OpenCATSConnector(HRISConnector):
    """
    Connector for OpenCATS Applicant Tracking System.
    Focused on recruitment rather than full HRIS.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize OpenCATS connector.
        
        Config should contain:
            - db_host: Database host
            - db_name: Database name (default: opencats)
            - db_user: Database user
            - db_password: Database password
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'opencats'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to OpenCATS."""
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
        """
        Get employees (hired candidates) from OpenCATS.
        Note: OpenCATS is primarily for recruitment, not employee management.
        """
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                c.candidate_id as employee_id,
                c.first_name,
                c.last_name,
                c.email1 as email,
                c.phone_home as phone,
                j.title as position
            FROM candidate c
            LEFT JOIN candidate_joborder cj ON c.candidate_id = cj.candidate_id
            LEFT JOIN joborder j ON cj.joborder_id = j.joborder_id
            WHERE cj.status = 'Hired'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            emp = Employee(
                employee_id=str(row['employee_id']),
                first_name=row['first_name'] or '',
                last_name=row['last_name'] or '',
                email=row['email'] or '',
                phone=row['phone'],
                department=None,
                position=row['position'],
                hire_date=None,
                employment_status='active',
                manager_id=None,
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
        """Attendance not tracked in OpenCATS."""
        return []
    
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """Leave records not tracked in OpenCATS."""
        return []
    
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """Performance reviews not available in OpenCATS."""
        return []


class JoraniConnector(HRISConnector):
    """
    Connector for Jorani Leave Management System.
    Focused specifically on leave/time-off management.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Jorani connector.
        
        Config should contain:
            - db_host: Database host
            - db_name: Database name (default: jorani)
            - db_user: Database user
            - db_password: Database password
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'jorani'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'charset': 'utf8mb4'
        }
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to Jorani."""
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
        """Get employees from Jorani."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                u.id as employee_id,
                u.firstname as first_name,
                u.lastname as last_name,
                u.email,
                o.name as department,
                p.name as position,
                u.datehired as hire_date,
                u.active as status,
                u.manager as manager_id
            FROM users u
            LEFT JOIN organization o ON u.organization = o.id
            LEFT JOIN positions p ON u.position = p.id
            WHERE 1=1
        """
        
        params = []
        
        if status == "active":
            query += " AND u.active = 1"
        elif status == "inactive":
            query += " AND u.active = 0"
        
        if department:
            query += " AND o.name = %s"
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
                phone=None,
                department=row['department'],
                position=row['position'],
                hire_date=row['hire_date'],
                employment_status='active' if row['status'] == 1 else 'inactive',
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
        """Attendance not primary feature in Jorani."""
        return []
    
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """Get leave records from Jorani."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                l.id as leave_id,
                l.employee as employee_id,
                lt.name as leave_type,
                l.startdate as start_date,
                l.enddate as end_date,
                l.duration as days_taken,
                l.status,
                l.cause as reason
            FROM leaves l
            LEFT JOIN types lt ON l.type = lt.id
            WHERE l.startdate BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND l.employee = %s"
            params.append(employee_id)
        
        if status:
            # Jorani status: 1=requested, 2=accepted, 3=rejected
            status_map = {'pending': 1, 'approved': 2, 'rejected': 3}
            if status in status_map:
                query += " AND l.status = %s"
                params.append(status_map[status])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Map status back
            status_map = {1: 'pending', 2: 'approved', 3: 'rejected'}
            
            record = LeaveRecord(
                leave_id=str(row['leave_id']),
                employee_id=str(row['employee_id']),
                leave_type=row['leave_type'] or 'vacation',
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(row['days_taken'] or 0),
                status=status_map.get(row['status'], 'pending'),
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
        """Performance reviews not available in Jorani."""
        return []


# Example usage
if __name__ == "__main__":
    print("Additional HRIS Connectors Demo")
    print("=" * 70)
    
    # Dolibarr example
    print("\n1. Dolibarr ERP/CRM/HR")
    dolibarr_config = {
        'base_url': 'https://your-dolibarr.com/api/index.php',
        'api_key': 'your_api_key',
        'db_host': 'localhost',
        'db_name': 'dolibarr',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    # OpenCATS example
    print("\n2. OpenCATS Applicant Tracking")
    opencats_config = {
        'db_host': 'localhost',
        'db_name': 'opencats',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    # Jorani example
    print("\n3. Jorani Leave Management")
    jorani_config = {
        'db_host': 'localhost',
        'db_name': 'jorani',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    print("\nNote: Update configurations with real credentials to test")
    