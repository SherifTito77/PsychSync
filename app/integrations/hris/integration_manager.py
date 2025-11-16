"""
HRIS Integration Manager for PsychSync
Central manager for all HRIS connectors with factory pattern.

File: app/integrations/hris/integration_manager.py

Usage:
    manager = HRISIntegrationManager()
    connector = manager.create_connector('orangehrm', config)
    employees = connector.get_employees()
"""

from typing import Dict, Optional, Type
from datetime import date, timedelta
import logging

from .base_connector import HRISConnector, CSVConnector
from .orangehrm_connector import OrangeHRMConnector
from .sentrifugo_connector import SentrifugoConnector
from .icehrm_connector import IceHRMConnector
from .frappe_connector import FrappeHRConnector, ERPNextConnector
from .odoo_connector import OdooHRConnector

logger = logging.getLogger(__name__)


class HRISIntegrationManager:
    """
    Factory and manager for HRIS connectors.
    Provides centralized access to all HRIS integrations.
    """
    
    # Registry of available connectors
    CONNECTORS = {
        'csv': CSVConnector,
        'orangehrm': OrangeHRMConnector,
        'sentrifugo': SentrifugoConnector,
        'icehrm': IceHRMConnector,
        'frappe': FrappeHRConnector,
        'erpnext': ERPNextConnector,
        'odoo': OdooHRConnector,
    }
    
    # Configuration templates for each HRIS
    CONFIG_TEMPLATES = {
        'csv': {
            'required': ['employees_csv'],
            'optional': ['attendance_csv', 'leave_csv'],
            'description': 'CSV file-based connector for manual exports'
        },
        'orangehrm': {
            'required': ['db_host', 'db_name', 'db_user', 'db_password'],
            'optional': ['base_url', 'client_id', 'client_secret'],
            'description': 'OrangeHRM open-source HRIS'
        },
        'sentrifugo': {
            'required': ['db_host', 'db_name', 'db_user', 'db_password'],
            'optional': ['db_port'],
            'description': 'Sentrifugo enterprise-grade HRIS'
        },
        'icehrm': {
            'required': ['base_url'],
            'optional': ['api_key', 'db_host', 'db_name', 'db_user', 'db_password'],
            'description': 'IceHRM lightweight HRIS'
        },
        'frappe': {
            'required': ['base_url', 'api_key', 'api_secret'],
            'optional': [],
            'description': 'Frappe HR with custom workflows'
        },
        'erpnext': {
            'required': ['base_url', 'api_key', 'api_secret'],
            'optional': [],
            'description': 'ERPNext integrated business suite'
        },
        'odoo': {
            'required': ['base_url', 'database', 'username', 'password'],
            'optional': [],
            'description': 'Odoo all-in-one business suite'
        }
    }
    
    def __init__(self):
        """Initialize integration manager."""
        self.active_connectors: Dict[str, HRISConnector] = {}
    
    def list_available_connectors(self) -> Dict[str, Dict]:
        """
        List all available HRIS connectors with their requirements.
        
        Returns:
            Dictionary of connector info
        """
        return self.CONFIG_TEMPLATES
    
    def create_connector(
        self,
        hris_type: str,
        config: Dict
    ) -> Optional[HRISConnector]:
        """
        Create and initialize HRIS connector.
        
        Args:
            hris_type: Type of HRIS (orangehrm, sentrifugo, etc.)
            config: Configuration dictionary
            
        Returns:
            Initialized connector or None if failed
        """
        hris_type = hris_type.lower()
        
        if hris_type not in self.CONNECTORS:
            logger.error(f"Unknown HRIS type: {hris_type}")
            logger.info(f"Available types: {', '.join(self.CONNECTORS.keys())}")
            return None
        
        # Validate configuration
        if not self._validate_config(hris_type, config):
            return None
        
        try:
            connector_class = self.CONNECTORS[hris_type]
            connector = connector_class(config)
            
            # Test connection
            if not connector.test_connection():
                logger.error(f"Connection test failed for {hris_type}")
                return None
            
            # Store active connector
            self.active_connectors[hris_type] = connector
            
            logger.info(f"✓ Successfully connected to {hris_type}")
            return connector
        
        except Exception as e:
            logger.error(f"Failed to create {hris_type} connector: {e}")
            return None
    
    def _validate_config(self, hris_type: str, config: Dict) -> bool:
        """Validate configuration has required fields."""
        template = self.CONFIG_TEMPLATES.get(hris_type, {})
        required = template.get('required', [])
        
        missing = [key for key in required if key not in config or not config[key]]
        
        if missing:
            logger.error(f"Missing required config fields for {hris_type}: {', '.join(missing)}")
            return False
        
        return True
    
    def get_connector(self, hris_type: str) -> Optional[HRISConnector]:
        """Get existing active connector."""
        return self.active_connectors.get(hris_type.lower())
    
    def sync_all_data(
        self,
        connector: HRISConnector,
        days_back: int = 30
    ) -> Dict:
        """
        Synchronize all data from HRIS.
        
        Args:
            connector: HRIS connector instance
            days_back: Number of days to look back for attendance/leaves
            
        Returns:
            Dictionary with sync results
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        results = {
            'success': False,
            'timestamp': date.today().isoformat(),
            'data': {}
        }
        
        try:
            # Get employees
            logger.info("Syncing employees...")
            employees = connector.get_employees(status="active")
            results['data']['employees'] = len(employees)
            logger.info(f"✓ Synced {len(employees)} employees")
            
            # Get attendance
            logger.info(f"Syncing attendance ({days_back} days)...")
            attendance = connector.get_attendance(start_date, end_date)
            results['data']['attendance'] = len(attendance)
            logger.info(f"✓ Synced {len(attendance)} attendance records")
            
            # Get leave records
            logger.info(f"Syncing leave records ({days_back} days)...")
            leaves = connector.get_leave_records(start_date, end_date)
            results['data']['leaves'] = len(leaves)
            logger.info(f"✓ Synced {len(leaves)} leave records")
            
            # Get performance reviews
            logger.info("Syncing performance reviews...")
            reviews = connector.get_performance_reviews(
                start_date=start_date,
                end_date=end_date
            )
            results['data']['reviews'] = len(reviews)
            logger.info(f"✓ Synced {len(reviews)} performance reviews")
            
            results['success'] = True
            results['message'] = "Sync completed successfully"
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def export_all_data(
        self,
        connector: HRISConnector,
        output_dir: str = "./exports",
        days_back: int = 30
    ) -> Dict[str, str]:
        """
        Export all HRIS data to CSV files.
        
        Args:
            connector: HRIS connector instance
            output_dir: Directory for exports
            days_back: Number of days for attendance/leaves
            
        Returns:
            Dictionary mapping data type to file path
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        exports = {}
        
        try:
            # Export employees
            employees = connector.get_employees()
            if employees:
                path = connector.export_to_csv(
                    employees,
                    f'employees_{date.today()}.csv',
                    output_dir
                )
                exports['employees'] = path
            
            # Export attendance
            attendance = connector.get_attendance(start_date, end_date)
            if attendance:
                path = connector.export_to_csv(
                    attendance,
                    f'attendance_{start_date}_to_{end_date}.csv',
                    output_dir
                )
                exports['attendance'] = path
            
            # Export leaves
            leaves = connector.get_leave_records(start_date, end_date)
            if leaves:
                path = connector.export_to_csv(
                    leaves,
                    f'leaves_{start_date}_to_{end_date}.csv',
                    output_dir
                )
                exports['leaves'] = path
            
            # Export reviews
            reviews = connector.get_performance_reviews(
                start_date=start_date,
                end_date=end_date
            )
            if reviews:
                path = connector.export_to_csv(
                    reviews,
                    f'reviews_{start_date}_to_{end_date}.csv',
                    output_dir
                )
                exports['reviews'] = path
            
            logger.info(f"✓ Exported {len(exports)} files")
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
        
        return exports
    
    def get_integration_status(self) -> Dict:
        """Get status of all active integrations."""
        status = {
            'total_connectors': len(self.active_connectors),
            'connectors': {}
        }
        
        for hris_type, connector in self.active_connectors.items():
            try:
                is_connected = connector.test_connection()
                status['connectors'][hris_type] = {
                    'connected': is_connected,
                    'type': connector.__class__.__name__
                }
            except:
                status['connectors'][hris_type] = {
                    'connected': False,
                    'type': connector.__class__.__name__
                }
        
        return status


# Example usage and demo
if __name__ == "__main__":
    print("=" * 70)
    print("HRIS Integration Manager Demo")
    print("=" * 70)
    
    manager = HRISIntegrationManager()
    
    # List available connectors
    print("\n📋 Available HRIS Connectors:")
    print("-" * 70)
    for hris_type, info in manager.list_available_connectors().items():
        print(f"\n{hris_type.upper()}")
        print(f"  Description: {info['description']}")
        print(f"  Required: {', '.join(info['required'])}")
        if info['optional']:
            print(f"  Optional: {', '.join(info['optional'])}")
    
    # Example: Create OrangeHRM connector
    print("\n" + "=" * 70)
    print("Creating OrangeHRM Connector")
    print("=" * 70)
    
    orangehrm_config = {
        'base_url': 'https://demo.orangehrmlive.com/symfony/web/index.php/api/v2',
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret',
        'db_host': 'localhost',
        'db_name': 'orangehrm',
        'db_user': 'root',
        'db_password': 'password'
    }
    
    # Note: This will fail without real credentials
    print("\nAttempting to connect to OrangeHRM...")
    connector = manager.create_connector('orangehrm', orangehrm_config)
    
    if connector:
        print("✓ Connection successful!")
        
        # Sync data
        print("\nSyncing data...")
        results = manager.sync_all_data(connector, days_back=30)
        
        if results['success']:
            print("\n✓ Sync completed:")
            for key, value in results['data'].items():
                print(f"  - {key}: {value} records")
        
        # Export data
        print("\nExporting data...")
        exports = manager.export_all_data(connector)
        
        if exports:
            print("\n✓ Exported files:")
            for data_type, filepath in exports.items():
                print(f"  - {data_type}: {filepath}")
    
    else:
        print("✗ Connection failed (expected with demo credentials)")
    
    # Show integration status
    print("\n" + "=" * 70)
    print("Integration Status")
    print("=" * 70)
    status = manager.get_integration_status()
    print(f"\nActive connectors: {status['total_connectors']}")
    
    for hris_type, info in status['connectors'].items():
        status_icon = "✓" if info['connected'] else "✗"
        print(f"  {status_icon} {hris_type}: {info['type']}")