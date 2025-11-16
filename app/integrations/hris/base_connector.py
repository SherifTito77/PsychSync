"""
Base HRIS Connector for PsychSync
Provides abstract base class for all HRIS integrations.

File: app/integrations/hris/base_connector.py

Requirements:
    pip install requests pandas sqlalchemy psycopg2-binary pymysql python-dateutil
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, date
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Employee:
    """Standardized employee data structure."""
    employee_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    employment_status: str = "active"
    manager_id: Optional[str] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Convert date objects to strings
        if self.hire_date:
            data['hire_date'] = self.hire_date.isoformat()
        return data


@dataclass
class AttendanceRecord:
    """Standardized attendance record."""
    record_id: str
    employee_id: str
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    hours_worked: Optional[float] = None
    status: str = "present"  # present, absent, leave, remote
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.date:
            data['date'] = self.date.isoformat()
        if self.clock_in:
            data['clock_in'] = self.clock_in.isoformat()
        if self.clock_out:
            data['clock_out'] = self.clock_out.isoformat()
        return data


@dataclass
class LeaveRecord:
    """Standardized leave record."""
    leave_id: str
    employee_id: str
    leave_type: str  # vacation, sick, personal, etc.
    start_date: date
    end_date: date
    days_taken: float
    status: str  # pending, approved, rejected, cancelled
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.start_date:
            data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        return data


@dataclass
class PerformanceReview:
    """Standardized performance review."""
    review_id: str
    employee_id: str
    reviewer_id: str
    review_date: date
    rating: Optional[float] = None
    comments: Optional[str] = None
    goals: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.review_date:
            data['review_date'] = self.review_date.isoformat()
        return data


class HRISConnector(ABC):
    """
    Abstract base class for HRIS connectors.
    All HRIS integrations should inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize HRIS connector.
        
        Args:
            config: Configuration dictionary containing:
                - base_url: HRIS API base URL
                - api_key: API authentication key
                - username: Username (if applicable)
                - password: Password (if applicable)
                - database_config: Database connection details (if applicable)
        """
        self.config = config
        self.base_url = config.get('base_url', '')
        self.api_key = config.get('api_key')
        self.username = config.get('username')
        self.password = config.get('password')
        self.session = requests.Session()
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication for API requests."""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
        elif self.username and self.password:
            self.session.auth = HTTPBasicAuth(self.username, self.password)
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to HRIS.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_employees(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """
        Retrieve employee list.
        
        Args:
            department: Filter by department
            status: Filter by employment status
            
        Returns:
            List of Employee objects
        """
        pass
    
    @abstractmethod
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """
        Get single employee by ID.
        
        Args:
            employee_id: Employee identifier
            
        Returns:
            Employee object or None
        """
        pass
    
    @abstractmethod
    def get_attendance(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None
    ) -> List[AttendanceRecord]:
        """
        Retrieve attendance records.
        
        Args:
            start_date: Start date for records
            end_date: End date for records
            employee_id: Optional filter for specific employee
            
        Returns:
            List of AttendanceRecord objects
        """
        pass
    
    @abstractmethod
    def get_leave_records(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[LeaveRecord]:
        """
        Retrieve leave records.
        
        Args:
            start_date: Start date for records
            end_date: End date for records
            employee_id: Optional filter for specific employee
            status: Optional filter by status
            
        Returns:
            List of LeaveRecord objects
        """
        pass
    
    @abstractmethod
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """
        Retrieve performance review records.
        
        Args:
            employee_id: Optional filter for specific employee
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            List of PerformanceReview objects
        """
        pass
    
    def export_to_csv(
        self,
        data: List[Any],
        filename: str,
        output_dir: str = "./exports"
    ) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of data objects (Employee, AttendanceRecord, etc.)
            filename: Output filename
            output_dir: Output directory
            
        Returns:
            Path to exported file
        """
        import os
        
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to DataFrame
        if not data:
            logger.warning("No data to export")
            return ""
        
        df = pd.DataFrame([item.to_dict() for item in data])
        
        # Generate full path
        filepath = os.path.join(output_dir, filename)
        
        # Export to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(data)} records to {filepath}")
        
        return filepath
    
    def export_to_dataframe(self, data: List[Any]) -> pd.DataFrame:
        """
        Convert data to pandas DataFrame.
        
        Args:
            data: List of data objects
            
        Returns:
            DataFrame
        """
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame([item.to_dict() for item in data])
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make HTTP request to HRIS API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response JSON or None
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def sync_employees_to_database(
        self,
        employees: List[Employee],
        db_connection: Any
    ):
        """
        Sync employee data to database.
        
        Args:
            employees: List of Employee objects
            db_connection: Database connection object
        """
        # Convert to DataFrame
        df = self.export_to_dataframe(employees)
        
        # Write to database
        df.to_sql(
            'hris_employees',
            con=db_connection,
            if_exists='replace',
            index=False
        )
        
        logger.info(f"Synced {len(employees)} employees to database")
    
    def get_sync_statistics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get synchronization statistics.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with sync stats
        """
        try:
            employees = self.get_employees()
            attendance = self.get_attendance(start_date, end_date)
            leaves = self.get_leave_records(start_date, end_date)
            
            return {
                'sync_date': datetime.utcnow().isoformat(),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'employee_count': len(employees),
                'attendance_records': len(attendance),
                'leave_records': len(leaves),
                'active_employees': len([e for e in employees if e.employment_status == 'active'])
            }
        
        except Exception as e:
            logger.error(f"Error getting sync statistics: {e}")
            return {}


class CSVConnector(HRISConnector):
    """
    CSV file-based connector for manual exports.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CSV connector.
        
        Config should contain:
            - employees_csv: Path to employees CSV
            - attendance_csv: Path to attendance CSV
            - leave_csv: Path to leave CSV
        """
        super().__init__(config)
        self.employees_csv = config.get('employees_csv')
        self.attendance_csv = config.get('attendance_csv')
        self.leave_csv = config.get('leave_csv')
    
    def test_connection(self) -> bool:
        """Test if CSV files are accessible."""
        import os
        return all(
            os.path.exists(path) for path in 
            [self.employees_csv, self.attendance_csv, self.leave_csv]
            if path
        )
    
    def get_employees(
        self,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Employee]:
        """Load employees from CSV."""
        if not self.employees_csv:
            return []
        
        df = pd.read_csv(self.employees_csv)
        
        # Filter by status
        if 'employment_status' in df.columns:
            df = df[df['employment_status'] == status]
        
        # Filter by department
        if department and 'department' in df.columns:
            df = df[df['department'] == department]
        
        # Convert to Employee objects
        employees = []
        for _, row in df.iterrows():
            emp = Employee(
                employee_id=str(row.get('employee_id', '')),
                first_name=row.get('first_name', ''),
                last_name=row.get('last_name', ''),
                email=row.get('email', ''),
                phone=row.get('phone'),
                department=row.get('department'),
                position=row.get('position'),
                hire_date=pd.to_datetime(row.get('hire_date')).date() if pd.notna(row.get('hire_date')) else None,
                employment_status=row.get('employment_status', 'active'),
                manager_id=row.get('manager_id'),
                location=row.get('location')
            )
            employees.append(emp)
        
        return employees
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by ID from CSV."""
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
        """Load attendance from CSV."""
        if not self.attendance_csv:
            return []
        
        df = pd.read_csv(self.attendance_csv)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Filter by employee
        if employee_id:
            df = df[df['employee_id'] == employee_id]
        
        # Convert to AttendanceRecord objects
        records = []
        for _, row in df.iterrows():
            record = AttendanceRecord(
                record_id=str(row.get('record_id', '')),
                employee_id=str(row.get('employee_id', '')),
                date=row['date'],
                clock_in=pd.to_datetime(row.get('clock_in')) if pd.notna(row.get('clock_in')) else None,
                clock_out=pd.to_datetime(row.get('clock_out')) if pd.notna(row.get('clock_out')) else None,
                hours_worked=float(row.get('hours_worked', 0)) if pd.notna(row.get('hours_worked')) else None,
                status=row.get('status', 'present')
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
        """Load leave records from CSV."""
        if not self.leave_csv:
            return []
        
        df = pd.read_csv(self.leave_csv)
        df['start_date'] = pd.to_datetime(df['start_date']).dt.date
        df['end_date'] = pd.to_datetime(df['end_date']).dt.date
        
        # Filter by date range
        df = df[(df['start_date'] >= start_date) & (df['start_date'] <= end_date)]
        
        # Filter by employee
        if employee_id:
            df = df[df['employee_id'] == employee_id]
        
        # Filter by status
        if status:
            df = df[df['status'] == status]
        
        # Convert to LeaveRecord objects
        records = []
        for _, row in df.iterrows():
            record = LeaveRecord(
                leave_id=str(row.get('leave_id', '')),
                employee_id=str(row.get('employee_id', '')),
                leave_type=row.get('leave_type', 'vacation'),
                start_date=row['start_date'],
                end_date=row['end_date'],
                days_taken=float(row.get('days_taken', 0)),
                status=row.get('status', 'pending'),
                reason=row.get('reason')
            )
            records.append(record)
        
        return records
    
    def get_performance_reviews(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PerformanceReview]:
        """Performance reviews not supported in CSV connector."""
        return []


# Example usage
if __name__ == "__main__":
    print("HRIS Base Connector Demo")
    print("=" * 60)
    
    # Example with CSV connector
    config = {
        'employees_csv': 'data/employees.csv',
        'attendance_csv': 'data/attendance.csv',
        'leave_csv': 'data/leave.csv'
    }
    
    connector = CSVConnector(config)
    
    if connector.test_connection():
        print("✓ Connection successful")
        
        # Get employees
        employees = connector.get_employees(status="active")
        print(f"\nFound {len(employees)} active employees")
        
        if employees:
            print(f"\nFirst employee: {employees[0].first_name} {employees[0].last_name}")
        
        # Get attendance for last 30 days
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        attendance = connector.get_attendance(start_date, end_date)
        print(f"\nFound {len(attendance)} attendance records in last 30 days")
        
        # Export to CSV
        if employees:
            filepath = connector.export_to_csv(employees, 'exported_employees.csv')
            print(f"\nExported to: {filepath}")
    
    else:
        print("✗ Connection failed - CSV files not found")