"""
Complete PsychSync HRIS Integration System
Combines all features: connectors, webhooks, scheduling, multi-format exports.

File: app/integrations/hris/psychsync_integration.py
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field

from .integration_manager import HRISIntegrationManager
from .export_manager import ExportManager
from .webhook_scheduler import WebhookReceiver, WebhookSender, SyncScheduler, WebhookEvent
from .extended_models import EmployeeExtended, AttendanceRecordExtended, LeaveRecordExtended

logger = logging.getLogger(__name__)


@dataclass
class IntegrationConfig:
    """Complete integration configuration."""
    # HRIS Settings
    hris_type: str
    hris_config: Dict[str, Any]
    
    # Export Settings
    export_dir: str = "./exports"
    export_formats: List[str] = field(default_factory=lambda: ['csv', 'json', 'excel'])
    enable_cloud_export: bool = False
    s3_bucket: Optional[str] = None
    
    # Webhook Settings
    enable_webhooks: bool = False
    webhook_secret: str = ""
    webhook_port: int = 5000
    outbound_webhooks: List[str] = field(default_factory=list)
    
    # Scheduling Settings
    enable_scheduling: bool = True
    sync_schedule: str = "every day at 02:00"
    sync_types: List[str] = field(default_factory=lambda: ['employees', 'attendance', 'leaves'])
    
    # Database Settings
    enable_database_sync: bool = False
    database_url: Optional[str] = None
    
    # Analytics Settings
    calculate_risk_scores: bool = True
    calculate_engagement: bool = True
    generate_reports: bool = True


class PsychSyncIntegration:
    """
    Complete HRIS integration system for PsychSync.
    Combines all features into a single, easy-to-use interface.
    """
    
    def __init__(self, config: IntegrationConfig):
        """
        Initialize PsychSync Integration.
        
        Args:
            config: Integration configuration
        """
        self.config = config
        
        # Initialize components
        self.hris_manager = HRISIntegrationManager()
        self.export_manager = ExportManager(output_dir=config.export_dir)
        
        # HRIS Connector
        self.connector = None
        
        # Webhook components
        self.webhook_receiver = None
        self.webhook_sender = None
        
        # Scheduler
        self.scheduler = None
        
        # Statistics
        self.stats = {
            'last_sync': None,
            'total_employees': 0,
            'total_syncs': 0,
            'failed_syncs': 0,
            'webhooks_received': 0,
            'webhooks_sent': 0
        }
        
        # Initialize
        self._initialize()
    
    def _initialize(self):
        """Initialize all components."""
        logger.info("Initializing PsychSync HRIS Integration...")
        
        # Connect to HRIS
        self.connector = self.hris_manager.create_connector(
            self.config.hris_type,
            self.config.hris_config
        )
        
        if not self.connector:
            raise Exception(f"Failed to connect to {self.config.hris_type}")
        
        logger.info(f"✓ Connected to {self.config.hris_type}")
        
        # Setup webhooks
        if self.config.enable_webhooks:
            self._setup_webhooks()
        
        # Setup scheduler
        if self.config.enable_scheduling:
            self._setup_scheduler()
        
        logger.info("✓ PsychSync Integration initialized successfully")
    
    def _setup_webhooks(self):
        """Setup webhook receiver and sender."""
        # Receiver
        self.webhook_receiver = WebhookReceiver(
            secret_key=self.config.webhook_secret,
            port=self.config.webhook_port
        )
        
        # Register default handlers
        self.webhook_receiver.register_handler(
            'employee.created',
            self._handle_employee_created
        )
        self.webhook_receiver.register_handler(
            'employee.updated',
            self._handle_employee_updated
        )
        self.webhook_receiver.register_handler(
            'leave.requested',
            self._handle_leave_requested
        )
        
        logger.info("✓ Webhook receiver configured")
        
        # Sender
        if self.config.outbound_webhooks:
            self.webhook_sender = WebhookSender(
                webhook_urls=self.config.outbound_webhooks,
                secret_key=self.config.webhook_secret
            )
            logger.info("✓ Webhook sender configured")
    
    def _setup_scheduler(self):
        """Setup sync scheduler."""
        self.scheduler = SyncScheduler()
        
        # Add main sync job
        self.scheduler.add_job(
            job_id=f'{self.config.hris_type}_sync',
            hris_type=self.config.hris_type,
            schedule_expression=self.config.sync_schedule,
            sync_types=self.config.sync_types,
            callback=self._scheduled_sync
        )
        
        # Start scheduler
        self.scheduler.start()
        
        logger.info(f"✓ Scheduler configured: {self.config.sync_schedule}")
    
    def _scheduled_sync(self, job):
        """Execute scheduled sync."""
        logger.info(f"Starting scheduled sync: {job.job_id}")
        
        try:
            result = self.sync_all_data()
            
            if result['success']:
                self.stats['total_syncs'] += 1
                logger.info("✓ Scheduled sync completed successfully")
            else:
                self.stats['failed_syncs'] += 1
                logger.error(f"✗ Scheduled sync failed: {result.get('error')}")
        
        except Exception as e:
            self.stats['failed_syncs'] += 1
            logger.error(f"Scheduled sync error: {e}")
    
    def _handle_employee_created(self, event: WebhookEvent):
        """Handle employee created webhook."""
        logger.info(f"Employee created: {event.data.get('employee_id')}")
        self.stats['webhooks_received'] += 1
        
        # Sync the new employee
        employee_id = event.data.get('employee_id')
        if employee_id:
            employee = self.connector.get_employee_by_id(employee_id)
            if employee:
                # Send notification to outbound webhooks
                if self.webhook_sender:
                    self.webhook_sender.send_webhook(
                        event_type='employee.created',
                        data=employee.to_dict(),
                        source='psychsync'
                    )
                    self.stats['webhooks_sent'] += 1
    
    def _handle_employee_updated(self, event: WebhookEvent):
        """Handle employee updated webhook."""
        logger.info(f"Employee updated: {event.data.get('employee_id')}")
        self.stats['webhooks_received'] += 1
    
    def _handle_leave_requested(self, event: WebhookEvent):
        """Handle leave requested webhook."""
        logger.info(f"Leave requested: {event.data.get('leave_id')}")
        self.stats['webhooks_received'] += 1
        
        # Send notification
        if self.webhook_sender:
            self.webhook_sender.send_webhook(
                event_type='leave.requested',
                data=event.data,
                source='psychsync'
            )
            self.stats['webhooks_sent'] += 1
    
    def sync_all_data(
        self,
        days_back: int = 30,
        export: bool = True
    ) -> Dict[str, Any]:
        """
        Sync all HRIS data.
        
        Args:
            days_back: Number of days to sync for attendance/leaves
            export: Whether to export data after sync
            
        Returns:
            Sync results dictionary
        """
        logger.info("Starting full data sync...")
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'data': {},
            'exports': {}
        }
        
        try:
            # Sync employees
            if 'employees' in self.config.sync_types:
                logger.info("Syncing employees...")
                employees = self.connector.get_employees(status='active')
                result['data']['employees'] = employees
                result['data']['employee_count'] = len(employees)
                self.stats['total_employees'] = len(employees)
                logger.info(f"✓ Synced {len(employees)} employees")
            
            # Sync attendance
            if 'attendance' in self.config.sync_types:
                logger.info(f"Syncing attendance ({days_back} days)...")
                attendance = self.connector.get_attendance(start_date, end_date)
                result['data']['attendance'] = attendance
                result['data']['attendance_count'] = len(attendance)
                logger.info(f"✓ Synced {len(attendance)} attendance records")
            
            # Sync leaves
            if 'leaves' in self.config.sync_types:
                logger.info(f"Syncing leaves ({days_back} days)...")
                leaves = self.connector.get_leave_records(start_date, end_date)
                result['data']['leaves'] = leaves
                result['data']['leave_count'] = len(leaves)
                logger.info(f"✓ Synced {len(leaves)} leave records")
            
            # Sync reviews
            if 'reviews' in self.config.sync_types:
                logger.info("Syncing performance reviews...")
                reviews = self.connector.get_performance_reviews(
                    start_date=start_date,
                    end_date=end_date
                )
                result['data']['reviews'] = reviews
                result['data']['review_count'] = len(reviews)
                logger.info(f"✓ Synced {len(reviews)} performance reviews")
            
            # Export data
            if export:
                result['exports'] = self._export_data(result['data'])
            
            # Sync to database
            if self.config.enable_database_sync and self.config.database_url:
                self._sync_to_database(result['data'])
            
            result['success'] = True
            self.stats['last_sync'] = datetime.now()
            
            logger.info("✓ Full sync completed successfully")
        
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _export_data(self, data: Dict[str, List]) -> Dict[str, Any]:
        """
        Export synced data in multiple formats.
        
        Args:
            data: Dictionary of synced data
            
        Returns:
            Export paths
        """
        logger.info("Exporting data...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exports = {}
        
        # Create export package
        package_name = f"{self.config.hris_type}_sync_{timestamp}"
        
        exports = self.export_manager.create_export_package(
            data,
            package_name,
            formats=self.config.export_formats
        )
        
        # Cloud export
        if self.config.enable_cloud_export and self.config.s3_bucket:
            logger.info("Uploading to S3...")
            for data_type, data_list in data.items():
                if data_list:
                    s3_key = f"hris_data/{package_name}/{data_type}.parquet"
                    success = self.export_manager.export_to_s3(
                        data_list,
                        self.config.s3_bucket,
                        s3_key,
                        format='parquet'
                    )
                    if success:
                        exports[f'{data_type}_s3'] = f"s3://{self.config.s3_bucket}/{s3_key}"
        
        logger.info(f"✓ Exported to {len(exports)} locations")
        
        return exports
    
    def _sync_to_database(self, data: Dict[str, List]):
        """
        Sync data to database.
        
        Args:
            data: Dictionary of synced data
        """
        logger.info("Syncing to database...")
        
        from sqlalchemy import create_engine
        
        try:
            engine = create_engine(self.config.database_url)
            
            for data_type, data_list in data.items():
                if data_list:
                    table_name = f"hris_{data_type}"
                    success = self.export_manager.export_to_sql(
                        data_list,
                        table_name,
                        self.config.database_url,
                        if_exists='replace'
                    )
                    if success:
                        logger.info(f"✓ Synced {data_type} to database")
        
        except Exception as e:
            logger.error(f"Database sync failed: {e}")
    
    def get_employee(self, employee_id: str) -> Optional[EmployeeExtended]:
        """Get single employee with extended data."""
        employee = self.connector.get_employee_by_id(employee_id)
        
        if not employee:
            return None
        
        # Convert to extended model with analytics
        # (In production, you would calculate these from actual data)
        extended_emp = EmployeeExtended(
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            phone=employee.phone,
            department=employee.department,
            position=employee.position,
            hire_date=employee.hire_date,
            employment_status=employee.employment_status,
            manager_id=employee.manager_id,
            location=employee.location,
            data_sync_date=datetime.now(),
            data_source=self.config.hris_type
        )
        
        return extended_emp
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            **self.stats,
            'hris_type': self.config.hris_type,
            'connector_status': 'connected' if self.connector else 'disconnected',
            'webhook_enabled': self.config.enable_webhooks,
            'scheduling_enabled': self.config.enable_scheduling,
            'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0
        }
    
    def start_webhook_receiver(self):
        """Start webhook receiver (blocking)."""
        if self.webhook_receiver:
            logger.info("Starting webhook receiver...")
            self.webhook_receiver.run()
        else:
            logger.warning("Webhooks not enabled")
    
    def stop(self):
        """Stop all services."""
        logger.info("Stopping PsychSync Integration...")
        
        if self.scheduler:
            self.scheduler.stop()
        
        logger.info("✓ PsychSync Integration stopped")


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("PsychSync Complete HRIS Integration System")
    print("=" * 70)
    
    # Configuration
    config = IntegrationConfig(
        hris_type='orangehrm',
        hris_config={
            'base_url': 'https://demo.orangehrmlive.com/api/v2',
            'client_id': 'your_client_id',
            'client_secret': 'your_client_secret',
            'db_host': 'localhost',
            'db_name': 'orangehrm',
            'db_user': 'root',
            'db_password': 'password'
        },
        export_dir='./psychsync_exports',
        export_formats=['csv', 'json', 'excel', 'parquet'],
        enable_webhooks=True,
        webhook_secret='super-secret-key',
        webhook_port=5000,
        outbound_webhooks=['https://api.yourapp.com/webhook'],
        enable_scheduling=True,
        sync_schedule='every day at 02:00',
        sync_types=['employees', 'attendance', 'leaves', 'reviews'],
        enable_database_sync=False,
        database_url=None,
        calculate_risk_scores=True,
        calculate_engagement=True,
        generate_reports=True
    )
    
    # Initialize integration
    try:
        integration = PsychSyncIntegration(config)
        
        print("\n✓ Integration initialized successfully!")
        print("\n📊 System Status:")
        stats = integration.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Perform initial sync
        print("\n🔄 Starting initial sync...")
        result = integration.sync_all_data(days_back=30)
        
        if result['success']:
            print("\n✓ Sync completed!")
            print(f"\n📈 Sync Results:")
            for key, value in result['data'].items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} records")
                else:
                    print(f"  {key}: {value}")
            
            if result.get('exports'):
                print(f"\n💾 Exported to {len(result['exports'])} locations")
        else:
            print(f"\n✗ Sync failed: {result.get('error')}")
        
        # Keep running (for webhooks and scheduled syncs)
        print("\n🚀 System running. Press Ctrl+C to stop.")
        print("   Scheduled syncs: Enabled")
        print("   Webhook receiver: Enabled on port 5000")
        
        # In production, this would keep running
        # integration.start_webhook_receiver()
    
    except Exception as e:
        print(f"\n✗ Failed to initialize: {e}")