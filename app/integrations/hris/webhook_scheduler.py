"""
Webhook Integration & Scheduled Sync System for PsychSync
Real-time event processing and automated synchronization.

File: app/integrations/hris/webhook_scheduler.py
"""

import hashlib
import hmac
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
import schedule
from flask import Flask, request, jsonify
import requests

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Types of webhook events."""
    EMPLOYEE_CREATED = "employee.created"
    EMPLOYEE_UPDATED = "employee.updated"
    EMPLOYEE_DELETED = "employee.deleted"
    ATTENDANCE_RECORDED = "attendance.recorded"
    LEAVE_REQUESTED = "leave.requested"
    LEAVE_APPROVED = "leave.approved"
    LEAVE_REJECTED = "leave.rejected"
    PERFORMANCE_REVIEW_COMPLETED = "review.completed"
    DEPARTMENT_CHANGED = "employee.department_changed"
    TERMINATION = "employee.terminated"


@dataclass
class WebhookEvent:
    """Webhook event data structure."""
    event_id: str
    event_type: str
    timestamp: datetime
    source: str  # HRIS system name
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class WebhookReceiver:
    """
    Webhook receiver for HRIS events.
    Processes incoming webhooks from various HRIS systems.
    """
    
    def __init__(self, secret_key: str, port: int = 5000):
        """
        Initialize webhook receiver.
        
        Args:
            secret_key: Secret key for webhook signature verification
            port: Port to listen on
        """
        self.secret_key = secret_key
        self.port = port
        self.app = Flask(__name__)
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_log: List[WebhookEvent] = []
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for webhooks."""
        
        @self.app.route('/webhook/hris', methods=['POST'])
        def receive_webhook():
            """Main webhook endpoint."""
            try:
                # Verify signature
                signature = request.headers.get('X-Webhook-Signature')
                if not self._verify_signature(request.data, signature):
                    logger.warning("Invalid webhook signature")
                    return jsonify({'error': 'Invalid signature'}), 401
                
                # Parse payload
                payload = request.json
                
                # Create event
                event = WebhookEvent(
                    event_id=payload.get('event_id', str(datetime.now().timestamp())),
                    event_type=payload.get('event_type'),
                    timestamp=datetime.fromisoformat(payload.get('timestamp', datetime.now().isoformat())),
                    source=payload.get('source', 'unknown'),
                    data=payload.get('data', {}),
                    metadata=payload.get('metadata')
                )
                
                # Log event
                self.event_log.append(event)
                logger.info(f"Received webhook: {event.event_type} from {event.source}")
                
                # Process event
                self._process_event(event)
                
                return jsonify({
                    'status': 'success',
                    'event_id': event.event_id,
                    'processed_at': datetime.now().isoformat()
                }), 200
            
            except Exception as e:
                logger.error(f"Webhook processing error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/webhook/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'events_processed': len(self.event_log),
                'handlers_registered': sum(len(v) for v in self.handlers.values())
            })
    
    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Request payload
            signature: Provided signature
            
        Returns:
            True if signature is valid
        """
        if not signature:
            return False
        
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callable that accepts WebhookEvent
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type}")
    
    def _process_event(self, event: WebhookEvent):
        """
        Process webhook event.
        
        Args:
            event: Webhook event to process
        """
        handlers = self.handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.event_type}: {e}")
    
    def run(self, debug: bool = False):
        """
        Start webhook receiver.
        
        Args:
            debug: Run in debug mode
        """
        logger.info(f"Starting webhook receiver on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[WebhookEvent]:
        """
        Get filtered event log.
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            since: Filter by timestamp
            
        Returns:
            List of webhook events
        """
        events = self.event_log
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if source:
            events = [e for e in events if e.source == source]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events


class WebhookSender:
    """
    Send webhooks to external systems.
    Notify other services of HRIS changes.
    """
    
    def __init__(self, webhook_urls: List[str], secret_key: str):
        """
        Initialize webhook sender.
        
        Args:
            webhook_urls: List of webhook URLs to send to
            secret_key: Secret key for signing webhooks
        """
        self.webhook_urls = webhook_urls
        self.secret_key = secret_key
        self.session = requests.Session()
    
    def send_webhook(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "psychsync"
    ) -> Dict[str, bool]:
        """
        Send webhook to all configured URLs.
        
        Args:
            event_type: Type of event
            data: Event data
            source: Source system name
            
        Returns:
            Dictionary mapping URLs to success status
        """
        event = WebhookEvent(
            event_id=str(datetime.now().timestamp()),
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            data=data
        )
        
        payload = json.dumps(event.to_dict())
        signature = self._generate_signature(payload.encode())
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature
        }
        
        results = {}
        
        for url in self.webhook_urls:
            try:
                response = self.session.post(
                    url,
                    data=payload,
                    headers=headers,
                    timeout=10
                )
                
                results[url] = response.status_code == 200
                
                if response.status_code == 200:
                    logger.info(f"Webhook sent successfully to {url}")
                else:
                    logger.warning(f"Webhook failed for {url}: {response.status_code}")
            
            except Exception as e:
                logger.error(f"Failed to send webhook to {url}: {e}")
                results[url] = False
        
        return results
    
    def _generate_signature(self, payload: bytes) -> str:
        """Generate HMAC signature for payload."""
        return hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()


@dataclass
class SyncJob:
    """Scheduled sync job configuration."""
    job_id: str
    hris_type: str
    schedule_expression: str  # e.g., "every day at 02:00"
    sync_types: List[str]  # employees, attendance, leaves, reviews
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_status: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        if self.last_run:
            result['last_run'] = self.last_run.isoformat()
        if self.next_run:
            result['next_run'] = self.next_run.isoformat()
        return result


class SyncScheduler:
    """
    Scheduled synchronization manager.
    Automates periodic HRIS data synchronization.
    """
    
    def __init__(self):
        """Initialize sync scheduler."""
        self.jobs: Dict[str, SyncJob] = {}
        self.running = False
        self.thread = None
        self.sync_callbacks: Dict[str, Callable] = {}
    
    def add_job(
        self,
        job_id: str,
        hris_type: str,
        schedule_expression: str,
        sync_types: List[str],
        callback: Callable
    ):
        """
        Add a scheduled sync job.
        
        Args:
            job_id: Unique job identifier
            hris_type: HRIS system type
            schedule_expression: Schedule expression (e.g., "every day at 02:00")
            sync_types: Types of data to sync
            callback: Function to call for sync
        """
        job = SyncJob(
            job_id=job_id,
            hris_type=hris_type,
            schedule_expression=schedule_expression,
            sync_types=sync_types,
            enabled=True
        )
        
        self.jobs[job_id] = job
        self.sync_callbacks[job_id] = callback
        
        # Parse and schedule
        self._schedule_job(job)
        
        logger.info(f"Added sync job: {job_id} - {schedule_expression}")
    
    def _schedule_job(self, job: SyncJob):
        """Schedule a job using the schedule library."""
        def job_wrapper():
            """Wrapper to execute job and update status."""
            if not job.enabled:
                return
            
            logger.info(f"Running sync job: {job.job_id}")
            job.last_run = datetime.now()
            
            try:
                callback = self.sync_callbacks[job.job_id]
                callback(job)
                job.last_status = "success"
                logger.info(f"Sync job completed: {job.job_id}")
            
            except Exception as e:
                job.last_status = "failed"
                logger.error(f"Sync job failed: {job.job_id} - {e}")
        
        # Parse schedule expression and create schedule
        parts = job.schedule_expression.lower().split()
        
        if "every" in parts:
            if "day" in parts:
                if "at" in parts:
                    time_idx = parts.index("at") + 1
                    if time_idx < len(parts):
                        schedule.every().day.at(parts[time_idx]).do(job_wrapper)
                else:
                    schedule.every().day.do(job_wrapper)
            
            elif "hour" in parts:
                schedule.every().hour.do(job_wrapper)
            
            elif "minute" in parts or "minutes" in parts:
                # Extract number
                for part in parts:
                    if part.isdigit():
                        schedule.every(int(part)).minutes.do(job_wrapper)
                        break
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            if job_id in self.sync_callbacks:
                del self.sync_callbacks[job_id]
            logger.info(f"Removed sync job: {job_id}")
    
    def enable_job(self, job_id: str):
        """Enable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            logger.info(f"Enabled sync job: {job_id}")
    
    def disable_job(self, job_id: str):
        """Disable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            logger.info(f"Disabled sync job: {job_id}")
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        
        def run_scheduler():
            logger.info("Sync scheduler started")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Sync scheduler stopped")
    
    def get_jobs(self) -> List[SyncJob]:
        """Get all scheduled jobs."""
        return list(self.jobs.values())
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if job:
            return job.to_dict()
        return None


# Example usage
if __name__ == "__main__":
    print("Webhook & Scheduler Demo")
    print("=" * 70)
    
    # Example 1: Webhook Receiver
    print("\n1. Setting up Webhook Receiver...")
    
    receiver = WebhookReceiver(secret_key='my-secret-key', port=5001)
    
    # Register handlers
    def handle_employee_created(event: WebhookEvent):
        print(f"  New employee: {event.data.get('employee_id')}")
    
    def handle_leave_requested(event: WebhookEvent):
        print(f"  Leave requested: {event.data.get('leave_id')}")
    
    receiver.register_handler('employee.created', handle_employee_created)
    receiver.register_handler('leave.requested', handle_leave_requested)
    
    print("  Registered event handlers")
    
    # Example 2: Webhook Sender
    print("\n2. Setting up Webhook Sender...")
    
    sender = WebhookSender(
        webhook_urls=['https://api.yourapp.com/webhook'],
        secret_key='my-secret-key'
    )
    
    # Send test webhook
    results = sender.send_webhook(
        event_type='employee.updated',
        data={'employee_id': 'EMP001', 'changes': {'department': 'Engineering'}},
        source='orangehrm'
    )
    
    print(f"  Webhook sent: {results}")
    
    # Example 3: Sync Scheduler
    print("\n3. Setting up Sync Scheduler...")
    
    scheduler = SyncScheduler()
    
    def sync_employees(job: SyncJob):
        print(f"  Syncing employees from {job.hris_type}")
        # Actual sync logic here
    
    # Schedule daily sync at 2 AM
    scheduler.add_job(
        job_id='daily_employee_sync',
        hris_type='orangehrm',
        schedule_expression='every day at 02:00',
        sync_types=['employees'],
        callback=sync_employees
    )
    
    # Schedule hourly attendance sync
    scheduler.add_job(
        job_id='hourly_attendance_sync',
        hris_type='orangehrm',
        schedule_expression='every hour',
        sync_types=['attendance'],
        callback=sync_employees
    )
    
    print("  Scheduled jobs:")
    for job in scheduler.get_jobs():
        print(f"    - {job.job_id}: {job.schedule_expression}")
    
    print("\n✓ System ready for webhook processing and scheduled syncs")