"""
Sentrifugo Connector for PsychSync
Integrates with Sentrifugo HRIS via database access.

File: app/integrations/hris/sentrifugo_connector.py

Sentrifugo: Enterprise-grade HRIS with performance appraisals and time management
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


class SentrifugoConnector(HRISConnector):
    """
    Connector for Sentrifugo HRIS.
    Uses direct database access (MySQL).
    """
    
    def __init__(self, config: Dict):
        """
        Initialize Sentrifugo connector.
        
        Config should contain:
            - db_host: Database host
            - db_name: Database name (default: sentrifugo)
            - db_user: Database username
            - db_password: Database password
            - db_port: Database port (default: 3306)
        """
        super().__init__(config)
        
        self.db_config = {
            'host': config.get('db_host', 'localhost'),
            'database': config.get('db_name', 'sentrifugo'),
            'user': config.get('db_user', ''),
            'password': config.get('db_password', ''),
            'port': config.get('db_port', 3306),
            'charset': 'utf8mb4'
        }
    
    def _get_db_connection(self):
        """Get database connection."""
        return pymysql.connect(**self.db_config)
    
    def test_connection(self) -> bool:
        """Test connection to Sentrifugo database."""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
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
        """Get employees from Sentrifugo."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                e.user_id as employee_id,
                e.userfullname as full_name,
                e.emailid as email,
                e.mobilephone as phone,
                bu.bu_name as department,
                p.positionname as position,
                e.joiningdate as hire_date,
                e.empstatus as employment_status,
                e.reporting_manager as manager_id,
                l.location as location
            FROM main_users e
            LEFT JOIN main_businessunits bu ON e.businessunit_id = bu.id
            LEFT JOIN main_positions p ON e.position_id = p.id
            LEFT JOIN main_locations l ON e.location_id = l.id
            WHERE e.isactive = 1
        """
        
        params = []
        
        if status == "active":
            query += " AND e.empstatus IN ('Active', 'Current')"
        elif status == "inactive":
            query += " AND e.empstatus IN ('Inactive', 'Terminated')"
        
        if department:
            query += " AND bu.bu_name = %s"
            params.append(department)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        employees = []
        for row in rows:
            # Split full name
            full_name = row['full_name'] or ''
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            emp = Employee(
                employee_id=str(row['employee_id']),
                first_name=first_name,
                last_name=last_name,
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
        """Get attendance records from Sentrifugo."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                a.id as record_id,
                a.user_id as employee_id,
                a.attendance_date as date,
                a.checkin_time as clock_in,
                a.checkout_time as clock_out,
                a.totalhours as hours_worked,
                a.attendance_status as status
            FROM main_employeeattendance a
            WHERE a.attendance_date BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND a.user_id = %s"
            params.append(employee_id)
        
        query += " ORDER BY a.attendance_date, a.checkin_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Parse times
            clock_in = None
            clock_out = None
            
            if row['clock_in']:
                if isinstance(row['clock_in'], str):
                    clock_in = datetime.strptime(
                        f"{row['date']} {row['clock_in']}", 
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    clock_in = datetime.combine(row['date'], row['clock_in'])
            
            if row['clock_out']:
                if isinstance(row['clock_out'], str):
                    clock_out = datetime.strptime(
                        f"{row['date']} {row['clock_out']}", 
                        "%Y-%m-%d %H:%M:%S"
                    )
                else:
                    clock_out = datetime.combine(row['date'], row['clock_out'])
            
            record = AttendanceRecord(
                record_id=str(row['record_id']),
                employee_id=str(row['employee_id']),
                date=row['date'],
                clock_in=clock_in,
                clock_out=clock_out,
                hours_worked=float(row['hours_worked']) if row['hours_worked'] else None,
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
        """Get leave records from Sentrifugo."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                l.id as leave_id,
                l.user_id as employee_id,
                lt.leavename as leave_type,
                l.from_date as start_date,
                l.to_date as end_date,
                l.no_of_days as days_taken,
                l.leave_status_id as status,
                l.reason
            FROM main_employeeleaves l
            LEFT JOIN main_leavetypes lt ON l.leavetype_id = lt.id
            WHERE l.from_date BETWEEN %s AND %s
        """
        
        params = [start_date, end_date]
        
        if employee_id:
            query += " AND l.user_id = %s"
            params.append(employee_id)
        
        if status:
            # Map status to Sentrifugo status IDs
            status_map = {'pending': '1', 'approved': '2', 'rejected': '3'}
            if status in status_map:
                query += " AND l.leave_status_id = %s"
                params.append(status_map[status])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        records = []
        for row in rows:
            # Map status ID to text
            status_map = {'1': 'pending', '2': 'approved', '3': 'rejected'}
            status_text = status_map.get(str(row['status']), 'pending')
            
            record = LeaveRecord(
                leave_id=str(row['leave_id']),
                employee_id=str(row['employee_id']),
                leave_type=row['leave_type'] or 'vacation',
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(row['days_taken'] or 0),
                status=status_text,
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
        """Get performance appraisals from Sentrifugo."""
        conn = self._get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        query = """
            SELECT 
                pa.id as review_id,
                pa.user_id as employee_id,
                pa.appraiser_id as reviewer_id,
                pa.appraisal_date as review_date,
                pa.rating_scale as rating,
                pa.comments
            FROM main_pa_employee_appraisals pa
            WHERE 1=1
        """
        
        params = []
        
        if employee_id:
            query += " AND pa.user_id = %s"
            params.append(employee_id)
        
        if start_date:
            query += " AND pa.appraisal_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND pa.appraisal_date <= %s"
            params.append(end_date)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        reviews = []
        for row in rows:
            review = PerformanceReview(
                review_id=str(row['review_id']),
                employee_id=str(row['employee_id']),
                reviewer_id=str(row['reviewer_id']),
                review_date=row['review_date'] or date.today(),
                rating=float(row['rating']) if row['rating'] else None,
                comments=row['comments']
            )
            reviews.append(review)
        
        cursor.close()
        conn.close()
        
        return reviews


# Example usage
if __name__ == "__main__":
    print("Sentrifugo Connector Demo")
    print("=" * 60)
    
    config = {
        'db_host': 'localhost',
        'db_name': 'sentrifugo',
        'db_user': 'root',
        'db_password': 'password',
        'db_port': 3306
    }
    
    connector = SentrifugoConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful\n")
        
        employees = connector.get_employees(status="active")
        print(f"Active employees: {len(employees)}")
        
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        attendance = connector.get_attendance(start_date, end_date)
        print(f"Attendance records: {len(attendance)}")
        
        leaves = connector.get_leave_records(start_date, end_date)
        print(f"Leave records: {len(leaves)}")
    else:
        print("✗ Connection failed")