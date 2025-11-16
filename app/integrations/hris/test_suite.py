"""
Comprehensive Testing Suite for HRIS Connectors
Tests all connectors with sample data and validates functionality.

File: app/integrations/hris/test_suite.py

Usage:
    python test_suite.py
    python test_suite.py --hris orangehrm
    python test_suite.py --quick
"""

import sys
import argparse
from datetime import date, timedelta, datetime
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HRISTestSuite:
    """Comprehensive test suite for HRIS connectors."""
    
    def __init__(self):
        """Initialize test suite."""
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'tests': []
        }
    
    def run_test(self, test_name: str, test_func, *args, **kwargs):
        """
        Run a single test and record results.
        
        Args:
            test_name: Name of the test
            test_func: Function to execute
            *args, **kwargs: Arguments for test function
        """
        self.results['total_tests'] += 1
        
        try:
            test_func(*args, **kwargs)
            self.results['passed'] += 1
            status = '✓ PASS'
            logger.info(f"{status}: {test_name}")
            
            self.results['tests'].append({
                'name': test_name,
                'status': 'PASS',
                'error': None
            })
        
        except AssertionError as e:
            self.results['failed'] += 1
            status = '✗ FAIL'
            logger.error(f"{status}: {test_name} - {str(e)}")
            
            self.results['tests'].append({
                'name': test_name,
                'status': 'FAIL',
                'error': str(e)
            })
        
        except Exception as e:
            self.results['failed'] += 1
            status = '✗ ERROR'
            logger.error(f"{status}: {test_name} - {str(e)}")
            
            self.results['tests'].append({
                'name': test_name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✓ Passed: {self.results['passed']}")
        print(f"✗ Failed: {self.results['failed']}")
        print(f"⊘ Skipped: {self.results['skipped']}")
        
        if self.results['failed'] > 0:
            print("\nFailed Tests:")
            for test in self.results['tests']:
                if test['status'] in ['FAIL', 'ERROR']:
                    print(f"  - {test['name']}: {test['error']}")
        
        success_rate = (self.results['passed'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print("=" * 70 + "\n")


def test_base_connector():
    """Test base connector functionality."""
    from .base_connector import Employee, AttendanceRecord, LeaveRecord
    
    suite = HRISTestSuite()
    
    # Test Employee dataclass
    def test_employee_creation():
        emp = Employee(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john.doe@company.com',
            department='Engineering'
        )
        assert emp.employee_id == 'EMP001'
        assert emp.first_name == 'John'
        assert emp.email == 'john.doe@company.com'
    
    suite.run_test("Employee Creation", test_employee_creation)
    
    # Test Employee to_dict
    def test_employee_to_dict():
        emp = Employee(
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            email='john@company.com',
            hire_date=date(2023, 1, 15)
        )
        data = emp.to_dict()
        assert data['employee_id'] == 'EMP001'
        assert data['hire_date'] == '2023-01-15'
    
    suite.run_test("Employee to_dict", test_employee_to_dict)
    
    # Test AttendanceRecord
    def test_attendance_record():
        record = AttendanceRecord(
            record_id='ATT001',
            employee_id='EMP001',
            date=date.today(),
            hours_worked=8.0,
            status='present'
        )
        assert record.hours_worked == 8.0
        assert record.status == 'present'
    
    suite.run_test("AttendanceRecord Creation", test_attendance_record)
    
    # Test LeaveRecord
    def test_leave_record():
        record = LeaveRecord(
            leave_id='LV001',
            employee_id='EMP001',
            leave_type='vacation',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            days_taken=5.0,
            status='approved'
        )
        assert record.days_taken == 5.0
        assert record.status == 'approved'
    
    suite.run_test("LeaveRecord Creation", test_leave_record)
    
    suite.print_summary()
    return suite.results


def test_csv_connector():
    """Test CSV connector with sample data."""
    import tempfile
    import os
    import pandas as pd
    from .base_connector import CSVConnector
    
    suite = HRISTestSuite()
    
    # Create temporary CSV files
    temp_dir = tempfile.mkdtemp()
    
    # Sample employee data
    employees_data = {
        'employee_id': ['EMP001', 'EMP002', 'EMP003'],
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john@company.com', 'jane@company.com', 'bob@company.com'],
        'department': ['Engineering', 'Sales', 'Engineering'],
        'position': ['Developer', 'Manager', 'Developer'],
        'hire_date': ['2023-01-15', '2022-06-01', '2023-03-20'],
        'employment_status': ['active', 'active', 'active']
    }
    
    employees_csv = os.path.join(temp_dir, 'employees.csv')
    pd.DataFrame(employees_data).to_csv(employees_csv, index=False)
    
    # Sample attendance data
    attendance_data = {
        'record_id': ['ATT001', 'ATT002', 'ATT003'],
        'employee_id': ['EMP001', 'EMP001', 'EMP002'],
        'date': ['2025-01-01', '2025-01-02', '2025-01-01'],
        'clock_in': ['2025-01-01 09:00:00', '2025-01-02 09:00:00', '2025-01-01 08:30:00'],
        'clock_out': ['2025-01-01 17:00:00', '2025-01-02 17:00:00', '2025-01-01 16:30:00'],
        'hours_worked': [8.0, 8.0, 8.0],
        'status': ['present', 'present', 'present']
    }
    
    attendance_csv = os.path.join(temp_dir, 'attendance.csv')
    pd.DataFrame(attendance_data).to_csv(attendance_csv, index=False)
    
    # Sample leave data
    leave_data = {
        'leave_id': ['LV001', 'LV002'],
        'employee_id': ['EMP001', 'EMP002'],
        'leave_type': ['vacation', 'sick'],
        'start_date': ['2025-02-01', '2025-01-15'],
        'end_date': ['2025-02-05', '2025-01-16'],
        'days_taken': [5.0, 2.0],
        'status': ['approved', 'approved'],
        'reason': ['Family vacation', 'Flu']
    }
    
    leave_csv = os.path.join(temp_dir, 'leave.csv')
    pd.DataFrame(leave_data).to_csv(leave_csv, index=False)
    
    # Create connector
    config = {
        'employees_csv': employees_csv,
        'attendance_csv': attendance_csv,
        'leave_csv': leave_csv
    }
    
    connector = CSVConnector(config)
    
    # Test connection
    def test_connection():
        assert connector.test_connection() == True
    
    suite.run_test("CSV Connection Test", test_connection)
    
    # Test get employees
    def test_get_employees():
        employees = connector.get_employees()
        assert len(employees) == 3
        assert employees[0].first_name == 'John'
    
    suite.run_test("CSV Get Employees", test_get_employees)
    
    # Test department filter
    def test_department_filter():
        employees = connector.get_employees(department='Engineering')
        assert len(employees) == 2
    
    suite.run_test("CSV Department Filter", test_department_filter)
    
    # Test get employee by ID
    def test_get_employee_by_id():
        employee = connector.get_employee_by_id('EMP001')
        assert employee is not None
        assert employee.first_name == 'John'
    
    suite.run_test("CSV Get Employee by ID", test_get_employee_by_id)
    
    # Test get attendance
    def test_get_attendance():
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        attendance = connector.get_attendance(start_date, end_date)
        assert len(attendance) == 3
    
    suite.run_test("CSV Get Attendance", test_get_attendance)
    
    # Test get leave records
    def test_get_leave_records():
        start_date = date(2025, 1, 1)
        end_date = date(2025, 3, 31)
        leaves = connector.get_leave_records(start_date, end_date)
        assert len(leaves) == 2
    
    suite.run_test("CSV Get Leave Records", test_get_leave_records)
    
    # Test export to CSV
    def test_export_to_csv():
        employees = connector.get_employees()
        output_dir = tempfile.mkdtemp()
        filepath = connector.export_to_csv(employees, 'test_export.csv', output_dir)
        assert os.path.exists(filepath)
    
    suite.run_test("CSV Export", test_export_to_csv)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    suite.print_summary()
    return suite.results


def test_integration_manager():
    """Test integration manager functionality."""
    from .integration_manager import HRISIntegrationManager
    
    suite = HRISTestSuite()
    
    manager = HRISIntegrationManager()
    
    # Test list connectors
    def test_list_connectors():
        connectors = manager.list_available_connectors()
        assert len(connectors) > 0
        assert 'orangehrm' in connectors
        assert 'csv' in connectors
    
    suite.run_test("List Available Connectors", test_list_connectors)
    
    # Test config validation
    def test_config_validation():
        # Valid config
        valid_config = {
            'employees_csv': 'test.csv',
            'attendance_csv': 'test2.csv',
            'leave_csv': 'test3.csv'
        }
        assert manager._validate_config('csv', valid_config) == True
        
        # Invalid config (missing required fields)
        invalid_config = {'optional_field': 'value'}
        assert manager._validate_config('csv', invalid_config) == False
    
    suite.run_test("Config Validation", test_config_validation)
    
    suite.print_summary()
    return suite.results


def test_data_models():
    """Test all data model conversions."""
    from .base_connector import Employee, AttendanceRecord, LeaveRecord, PerformanceReview
    
    suite = HRISTestSuite()
    
    # Test date conversions
    def test_date_conversions():
        emp = Employee(
            employee_id='EMP001',
            first_name='Test',
            last_name='User',
            email='test@test.com',
            hire_date=date(2023, 1, 15)
        )
        
        data = emp.to_dict()
        assert data['hire_date'] == '2023-01-15'
    
    suite.run_test("Date Conversions", test_date_conversions)
    
    # Test datetime conversions
    def test_datetime_conversions():
        record = AttendanceRecord(
            record_id='ATT001',
            employee_id='EMP001',
            date=date.today(),
            clock_in=datetime(2025, 1, 1, 9, 0, 0),
            clock_out=datetime(2025, 1, 1, 17, 0, 0),
            hours_worked=8.0
        )
        
        data = record.to_dict()
        assert 'clock_in' in data
        assert isinstance(data['clock_in'], str)
    
    suite.run_test("DateTime Conversions", test_datetime_conversions)
    
    suite.print_summary()
    return suite.results


def run_all_tests(quick=False):
    """Run all test suites."""
    print("\n" + "=" * 70)
    print("HRIS CONNECTOR TEST SUITE")
    print("=" * 70 + "\n")
    
    all_results = []
    
    # Test base connector
    print("\n📦 Testing Base Connector...")
    all_results.append(test_base_connector())
    
    # Test CSV connector
    print("\n📄 Testing CSV Connector...")
    all_results.append(test_csv_connector())
    
    # Test integration manager
    print("\n🔧 Testing Integration Manager...")
    all_results.append(test_integration_manager())
    
    # Test data models
    print("\n📊 Testing Data Models...")
    all_results.append(test_data_models())
    
    # Overall summary
    total_tests = sum(r['total_tests'] for r in all_results)
    total_passed = sum(r['passed'] for r in all_results)
    total_failed = sum(r['failed'] for r in all_results)
    
    print("\n" + "=" * 70)
    print("OVERALL TEST RESULTS")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"✓ Passed: {total_passed}")
    print(f"✗ Failed: {total_failed}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\nOverall Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_failed} test(s) failed. Please review errors above.")
    
    print("=" * 70 + "\n")
    
    return total_failed == 0


def test_specific_hris(hris_type: str, config: Dict):
    """
    Test a specific HRIS connector.
    
    Args:
        hris_type: Type of HRIS to test
        config: Configuration dictionary
    """
    from .integration_manager import HRISIntegrationManager
    
    print(f"\n{'=' * 70}")
    print(f"Testing {hris_type.upper()} Connector")
    print('=' * 70)
    
    manager = HRISIntegrationManager()
    suite = HRISTestSuite()
    
    # Test connection
    def test_connection():
        connector = manager.create_connector(hris_type, config)
        assert connector is not None, f"Failed to create {hris_type} connector"
        assert connector.test_connection(), f"{hris_type} connection test failed"
    
    suite.run_test(f"{hris_type} Connection", test_connection)
    
    # If connection works, test data retrieval
    connector = manager.create_connector(hris_type, config)
    if connector:
        def test_get_employees():
            employees = connector.get_employees()
            assert employees is not None
            print(f"  Found {len(employees)} employees")
        
        suite.run_test(f"{hris_type} Get Employees", test_get_employees)
        
        def test_get_attendance():
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            attendance = connector.get_attendance(start_date, end_date)
            assert attendance is not None
            print(f"  Found {len(attendance)} attendance records")
        
        suite.run_test(f"{hris_type} Get Attendance", test_get_attendance)
    
    suite.print_summary()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test HRIS Connectors')
    parser.add_argument('--hris', type=str, help='Test specific HRIS (orangehrm, csv, etc.)')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    
    args = parser.parse_args()
    
    if args.hris:
        print(f"Testing specific HRIS: {args.hris}")
        print("Please provide configuration in config.json or modify this script")
        # Add your config here
        config = {}
        test_specific_hris(args.hris, config)
    else:
        success = run_all_tests(quick=args.quick)
        sys.exit(0 if success else 1)