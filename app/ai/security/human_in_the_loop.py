"""
Human-in-the-Loop Workflows for AI Security

Provides approval workflows for sensitive AI operations, ensuring human oversight
for critical decisions and actions.

Key Features:
- Approval request generation
- Multi-stage approval workflows
- Timeout handling
- Approval audit trail
- Integration with tool scoping
- Risk-based approval requirements

Resources:
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- OECD AI Principles: https://www.oecd.org/ai/
"""

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ApprovalStatus(Enum):
    """Status of approval request"""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RiskLevel(Enum):
    """Risk level of operation"""

    LOW = "low"  # Routine operations
    MEDIUM = "medium"  # Requires review
    HIGH = "high"  # Requires explicit approval
    CRITICAL = "critical"  # Requires multiple approvals


@dataclass
class ApprovalRequest:
    """Approval request for sensitive AI operation"""

    request_id: str
    operation_type: str
    risk_level: RiskLevel
    requester_id: str
    requested_at: datetime
    timeout_minutes: int
    status: ApprovalStatus = ApprovalStatus.PENDING
    approvers: List[str] = field(default_factory=list)
    approvals_received: Dict[str, bool] = field(default_factory=dict)
    denials: List[str] = field(default_factory=list)
    operation_details: Dict[str, Any] = field(default_factory=dict)
    justification: Optional[str] = None
    responded_at: Optional[datetime] = None

    def is_approved(self) -> bool:
        """Check if request is approved"""
        if self.status != ApprovalStatus.APPROVED:
            return False

        # Check if all required approvers approved
        return len(self.approvals_received) >= len(self.approvers)

    def is_expired(self) -> bool:
        """Check if request has timed out"""
        if self.status != ApprovalStatus.PENDING:
            return False

        expiry = self.requested_at + timedelta(minutes=self.timeout_minutes)
        return datetime.now(timezone.utc) > expiry


class ApprovalWorkflow:
    """
    Human-in-the-loop approval workflow manager

    Manages approval requests for sensitive AI operations with:
    - Risk-based approval requirements
    - Multi-approvers for critical operations
    - Timeout handling
    - Audit trail
    """

    def __init__(self):
        """Initialize approval workflow manager"""
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: List[ApprovalRequest] = []
        self.approvers: Dict[str, List[str]] = {}  # user_id -> [approver_ids]
        self.risk_rules: Dict[str, RiskLevel] = {}
        self.lock = threading.Lock()

        # Initialize default risk rules
        self._initialize_risk_rules()

    def _initialize_risk_rules(self) -> None:
        """Initialize default risk rules for operation types"""
        self.risk_rules = {
            # Low risk operations
            "sentiment_analysis": RiskLevel.LOW,
            "personality_assessment": RiskLevel.LOW,
            "basic_analytics": RiskLevel.LOW,
            # Medium risk operations
            "clinical_assessment": RiskLevel.MEDIUM,
            "behavioral_analysis": RiskLevel.MEDIUM,
            "data_export": RiskLevel.MEDIUM,
            # High risk operations
            "file_write": RiskLevel.HIGH,
            "database_write": RiskLevel.HIGH,
            "api_integration": RiskLevel.HIGH,
            "bulk_operations": RiskLevel.HIGH,
            # Critical risk operations
            "system_command": RiskLevel.CRITICAL,
            "delete_data": RiskLevel.CRITICAL,
            "user_management": RiskLevel.CRITICAL,
            "security_config": RiskLevel.CRITICAL,
        }

    def add_risk_rule(self, operation_type: str, risk_level: RiskLevel) -> None:
        """
        Add or update risk rule for operation type

        Args:
            operation_type: Type of operation
            risk_level: Risk level for this operation
        """
        self.risk_rules[operation_type] = risk_level

    def set_approvers(self, user_id: str, approver_ids: List[str]) -> None:
        """
        Set approvers for a user

        Args:
            user_id: User requiring approval
            approver_ids: List of approver user IDs
        """
        self.approvers[user_id] = approver_ids

    def get_required_approvers(self, operation_type: str, risk_level: RiskLevel) -> int:
        """
        Get number of approvers required based on risk level

        Args:
            operation_type: Type of operation
            risk_level: Risk level

        Returns:
            Number of required approvers
        """
        if risk_level == RiskLevel.CRITICAL:
            return 2  # Require 2 approvers for critical operations
        elif risk_level == RiskLevel.HIGH:
            return 1  # Require 1 approver for high risk
        elif risk_level == RiskLevel.MEDIUM:
            return 1  # Require 1 approver for medium risk
        else:
            return 0  # No approval needed for low risk

    def create_approval_request(
        self,
        operation_type: str,
        requester_id: str,
        operation_details: Dict[str, Any],
        justification: Optional[str] = None,
        timeout_minutes: int = 60,
    ) -> ApprovalRequest:
        """
        Create approval request for operation

        Args:
            operation_type: Type of operation
            requester_id: User requesting operation
            operation_details: Details of the operation
            justification: Justification for the operation
            timeout_minutes: Minutes until request times out

        Returns:
            Approval request
        """
        # Determine risk level
        risk_level = self.risk_rules.get(operation_type, RiskLevel.MEDIUM)

        # Get required approvers
        approvers = self.approvers.get(requester_id, [])

        # Create request
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            operation_type=operation_type,
            risk_level=risk_level,
            requester_id=requester_id,
            requested_at=datetime.now(timezone.utc),
            timeout_minutes=timeout_minutes,
            approvers=approvers,
            operation_details=operation_details,
            justification=justification,
        )

        # Store request
        with self.lock:
            self.pending_requests[request.request_id] = request

        return request

    def approve_request(
        self, request_id: str, approver_id: str, comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a request

        Args:
            request_id: Request ID
            approver_id: Approver user ID
            comments: Optional approval comments

        Returns:
            Result dictionary
        """
        with self.lock:
            request = self.pending_requests.get(request_id)

            if not request:
                return {
                    "success": False,
                    "error": "Request not found or already processed",
                }

            # Check if expired
            if request.is_expired():
                request.status = ApprovalStatus.TIMEOUT
                self.completed_requests.append(request)
                del self.pending_requests[request_id]
                return {"success": False, "error": "Request has expired"}

            # Check if approver is authorized
            if approver_id not in request.approvers:
                return {
                    "success": False,
                    "error": "Approver not authorized for this request",
                }

            # Check if already approved/denied
            if approver_id in request.approvals_received:
                return {"success": False, "error": "Already approved by this approver"}

            # Record approval
            request.approvals_received[approver_id] = True

            # Check if all approvals received
            required = self.get_required_approvers(
                request.operation_type, request.risk_level
            )

            if len(request.approvals_received) >= required:
                request.status = ApprovalStatus.APPROVED
                request.responded_at = datetime.now(timezone.utc)
                self.completed_requests.append(request)
                del self.pending_requests[request_id]

                return {
                    "success": True,
                    "status": "approved",
                    "message": "Request approved",
                }
            else:
                return {
                    "success": True,
                    "status": "pending",
                    "message": f"Approval recorded. {required - len(request.approvals_received)} more approval(s) needed.",
                }

    def deny_request(
        self, request_id: str, approver_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deny a request

        Args:
            request_id: Request ID
            approver_id: Approver user ID
            reason: Optional denial reason

        Returns:
            Result dictionary
        """
        with self.lock:
            request = self.pending_requests.get(request_id)

            if not request:
                return {
                    "success": False,
                    "error": "Request not found or already processed",
                }

            # Check if approver is authorized
            if approver_id not in request.approvers:
                return {
                    "success": False,
                    "error": "Approver not authorized for this request",
                }

            # Record denial
            request.denials.append(approver_id)
            request.status = ApprovalStatus.DENIED
            request.responded_at = datetime.now(timezone.utc)

            # Move to completed
            self.completed_requests.append(request)
            del self.pending_requests[request_id]

            return {"success": True, "status": "denied", "message": "Request denied"}

    def check_approval_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check status of approval request

        Args:
            request_id: Request ID

        Returns:
            Status dictionary
        """
        with self.lock:
            request = self.pending_requests.get(request_id)

            if not request:
                # Check completed requests
                for completed in self.completed_requests:
                    if completed.request_id == request_id:
                        return {
                            "status": completed.status.value,
                            "approvals_received": len(completed.approvals_received),
                            "denials": len(completed.denials),
                            "responded_at": (
                                completed.responded_at.isoformat()
                                if completed.responded_at
                                else None
                            ),
                        }

                return {"error": "Request not found"}

            # Check if expired
            if request.is_expired():
                request.status = ApprovalStatus.TIMEOUT
                self.completed_requests.append(request)
                del self.pending_requests[request_id]

                return {
                    "status": ApprovalStatus.TIMEOUT.value,
                    "message": "Request has expired",
                }

            return {
                "status": request.status.value,
                "risk_level": request.risk_level.value,
                "requester": request.requester_id,
                "approvers_required": len(request.approvers),
                "approvals_received": len(request.approvals_received),
                "denials": len(request.denials),
                "requested_at": request.requested_at.isoformat(),
                "expires_at": (
                    request.requested_at + timedelta(minutes=request.timeout_minutes)
                ).isoformat(),
            }

    def cancel_request(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """
        Cancel a pending request

        Args:
            request_id: Request ID
            user_id: User cancelling (must be requester)

        Returns:
            Result dictionary
        """
        with self.lock:
            request = self.pending_requests.get(request_id)

            if not request:
                return {
                    "success": False,
                    "error": "Request not found or already processed",
                }

            # Check if user is requester
            if request.requester_id != user_id:
                return {"success": False, "error": "Only requester can cancel"}

            # Cancel request
            request.status = ApprovalStatus.CANCELLED
            self.completed_requests.append(request)
            del self.pending_requests[request_id]

            return {
                "success": True,
                "status": "cancelled",
                "message": "Request cancelled",
            }

    def get_pending_requests(
        self, user_id: Optional[str] = None
    ) -> List[ApprovalRequest]:
        """
        Get pending approval requests

        Args:
            user_id: Optional filter by user

        Returns:
            List of pending requests
        """
        with self.lock:
            requests = list(self.pending_requests.values())

            # Clean expired requests
            for request in requests:
                if request.is_expired():
                    request.status = ApprovalStatus.TIMEOUT
                    self.completed_requests.append(request)
                    self.pending_requests.pop(request.request_id, None)

            # Filter by user if specified
            if user_id:
                requests = [
                    r
                    for r in self.pending_requests.values()
                    if r.requester_id == user_id or user_id in r.approvers
                ]

            return list(self.pending_requests.values())

    def get_approval_history(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get approval history

        Args:
            user_id: Optional filter by user
            limit: Max results

        Returns:
            Approval history
        """
        with self.lock:
            history = self.completed_requests

            if user_id:
                history = [
                    r
                    for r in history
                    if r.requester_id == user_id or user_id in r.approvers
                ]

            # Return most recent first
            history = sorted(history, key=lambda x: x.requested_at, reverse=True)

            return [
                {
                    "request_id": r.request_id,
                    "operation_type": r.operation_type,
                    "risk_level": r.risk_level.value,
                    "requester": r.requester_id,
                    "status": r.status.value,
                    "requested_at": r.requested_at.isoformat(),
                    "responded_at": (
                        r.responded_at.isoformat() if r.responded_at else None
                    ),
                }
                for r in history[:limit]
            ]


# Singleton instance
_approval_workflow = None


def get_approval_workflow() -> ApprovalWorkflow:
    """Get global approval workflow instance"""
    global _approval_workflow
    if _approval_workflow is None:
        _approval_workflow = ApprovalWorkflow()
    return _approval_workflow


# Example usage
if __name__ == "__main__":
    print("Human-in-the-Loop Workflow Demo")
    print("=" * 60)

    # Initialize workflow
    workflow = ApprovalWorkflow()

    # Set up approvers
    print("\n1. Setting Up Approvers")
    print("-" * 60)

    workflow.set_approvers("user_123", ["manager_456", "admin_789"])
    print("✓ Set approvers for user_123")

    # Create approval request
    print("\n2. Creating Approval Request")
    print("-" * 60)

    request = workflow.create_approval_request(
        operation_type="file_write",
        requester_id="user_123",
        operation_details={
            "filepath": "results/export.json",
            "operation": "write",
            "data_size": "1.2MB",
        },
        justification="Need to export assessment results for compliance",
        timeout_minutes=60,
    )

    print(f"Request ID: {request.request_id}")
    print(f"Operation: {request.operation_type}")
    print(f"Risk Level: {request.risk_level.value}")
    print(f"Approvers Required: {len(request.approvers)}")
    print(f"Status: {request.status.value}")

    # Check status
    print("\n3. Checking Status")
    print("-" * 60)

    status = workflow.check_approval_status(request.request_id)
    print(f"Current Status: {status['status']}")
    print(
        f"Approvals Received: {status['approvals_received']}/{status['approvers_required']}"
    )

    # Approve request
    print("\n4. Approving Request")
    print("-" * 60)

    result = workflow.approve_request(
        request_id=request.request_id,
        approver_id="manager_456",
        comments="Approved for compliance export",
    )

    print(f"Approval Result: {result['success']}")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Message: {result.get('message', '')}")

    # Deny request example
    print("\n5. Denying Request (Example)")
    print("-" * 60)

    deny_request = workflow.create_approval_request(
        operation_type="system_command",
        requester_id="user_123",
        operation_details={"command": "rm -rf /data", "reason": "Testing"},
    )

    result = workflow.deny_request(
        request_id=deny_request.request_id,
        approver_id="admin_789",
        reason="Unsafe operation - not approved",
    )

    print(f"Deny Result: {result['success']}")
    print(f"Status: {result.get('status')}")

    # Get history
    print("\n6. Approval History")
    print("-" * 60)

    history = workflow.get_approval_history(limit=5)
    print(f"Total Requests: {len(history)}")
    for entry in history:
        print(
            f"  {entry['operation_type']} - {entry['status']} ({entry['risk_level']})"
        )

    print("\n" + "=" * 60)
    print("Demo complete!")
