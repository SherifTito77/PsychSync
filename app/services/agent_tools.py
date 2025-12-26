"""
Agent Tool Implementations

This module contains the actual implementations of approved agent tools.
Each tool implementation must:
1. Validate inputs
2. Enforce constraints (row limits, file sizes, etc.)
3. Return results in a standard format
4. Handle errors gracefully
"""

from typing import Dict, Any, List
from datetime import datetime
import hashlib
import os


# ============================================================================
# Database Tools
# ============================================================================

async def db_read_query_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Execute read-only SQL query

    Parameters:
        query: SQL query (SELECT only)
        row_limit: Maximum rows to return (default: 1000)
    """

    from app.db.session import get_db
    from sqlalchemy import text

    query = parameters.get("query", "")
    row_limit = parameters.get("row_limit", 1000)

    # Validate query is read-only
    if not _validate_read_only_query(query):
        raise ValueError("Query must be SELECT only (no INSERT, UPDATE, DELETE, etc.)")

    # Apply row limit for clinicians
    if user_role == "clinician" and row_limit > 100:
        row_limit = 100

    # Add LIMIT clause
    if "LIMIT" not in query.upper():
        query += f" LIMIT {row_limit}"

    # Execute query
    db = get_db()
    result = db.execute(text(query))

    # Convert to list of dicts
    rows = []
    for row in result:
        rows.append(dict(row._mapping))

    return {
        "rows": rows,
        "row_count": len(rows),
        "query_executed": query
    }


async def db_anonymized_export_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Export anonymized data for research

    Parameters:
        query: SQL query
        anonymize_fields: List of fields to anonymize
    """

    from app.db.session import get_db
    from sqlalchemy import text

    query = parameters.get("query", "")
    anonymize_fields = parameters.get("anonymize_fields", [])

    # Validate query
    if not _validate_read_only_query(query):
        raise ValueError("Query must be SELECT only")

    # Execute query
    db = get_db()
    result = db.execute(text(query))

    # Anonymize results
    anonymized_rows = []
    for row in result:
        row_dict = dict(row._mapping)

        # Anonymize specified fields
        for field in anonymize_fields:
            if field in row_dict:
                # One-way hash
                value = str(row_dict[field])
                hashed = hashlib.sha256(value.encode()).hexdigest()[:16]
                row_dict[field] = f"anon_{hashed}"

        anonymized_rows.append(row_dict)

    return {
        "rows": anonymized_rows,
        "row_count": len(anonymized_rows),
        "anonymized_fields": anonymize_fields
    }


def _validate_read_only_query(query: str) -> bool:
    """Validate query is read-only SELECT"""

    dangerous_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'GRANT', 'REVOKE', 'TRUNCATE', 'EXEC'
    ]

    query_upper = query.upper()

    # Must start with SELECT
    if not query_upper.strip().startswith('SELECT'):
        return False

    # Must not contain dangerous keywords
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False

    # Check for comment injection
    if '--' in query or '/*' in query:
        return False

    return True


# ============================================================================
# Email Tools
# ============================================================================

async def email_draft_create_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Create email draft (does not send)

    Parameters:
        to: Recipient email
        subject: Email subject
        body: Email body
        template_id: Optional template ID
    """

    from app.services.email_service import EmailService

    to_email = parameters.get("to")
    subject = parameters.get("subject")
    body = parameters.get("body")
    template_id = parameters.get("template_id")

    # Create draft
    email_service = EmailService()
    draft_id = await email_service.create_draft(
        user_id=user_id,
        to=to_email,
        subject=subject,
        body=body,
        template_id=template_id
    )

    return {
        "draft_id": draft_id,
        "status": "draft_created",
        "message": "Email draft created. Manual send required."
    }


async def email_send_verified_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Send pre-verified email template

    Parameters:
        template_id: Template ID (must be approved)
        to: Recipient email
        template_data: Data for template
    """

    # Approved templates
    APPROVED_TEMPLATES = {
        'assessment_invitation': 'emails/assessment_invite.html',
        'reminder': 'emails/reminder.html',
        'results_available': 'emails/results_ready.html'
    }

    template_id = parameters.get("template_id")
    to_email = parameters.get("to")
    template_data = parameters.get("template_data", {})

    # Validate template is approved
    if template_id not in APPROVED_TEMPLATES:
        raise ValueError(f"Template '{template_id}' is not approved")

    # Check role permissions
    if user_role == "clinician":
        # Clinicians can only send certain templates
        if template_id not in ['assessment_invitation', 'reminder']:
            raise ValueError(f"Clinicians cannot send template '{template_id}'")

    # Send email
    from app.services.email_service import EmailService

    email_service = EmailService()
    result = await email_service.send_template_email(
        template_id=template_id,
        to=to_email,
        data=template_data
    )

    return {
        "email_id": result.get("email_id"),
        "status": "sent",
        "template_used": template_id
    }


# ============================================================================
# File System Tools
# ============================================================================

ALLOWED_READ_DIRS = [
    '/app/public/',
    '/app/templates/',
    '/app/docs/',
    '/var/assessment-exports/'
]

ALLOWED_WRITE_DIRS = [
    '/var/assessment-exports/',
    '/var/tmp/',
    '/var/user-uploads/'
]


async def file_read_allowed_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Read file from allowed directory

    Parameters:
        file_path: Path to file
    """

    file_path = parameters.get("file_path")

    # Validate path
    if not _validate_file_path(file_path, ALLOWED_READ_DIRS):
        raise ValueError(f"File path '{file_path}' is not in allowed directories")

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file size (max 10MB)
    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:
        raise ValueError(f"File too large: {file_size} bytes (max 10MB)")

    # Read file
    with open(file_path, 'r') as f:
        content = f.read()

    return {
        "file_path": file_path,
        "content": content,
        "size_bytes": file_size
    }


async def file_write_allowed_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Write file to allowed directory

    Parameters:
        file_path: Path to file
        content: File content
    """

    file_path = parameters.get("file_path")
    content = parameters.get("content", "")

    # Validate path
    if not _validate_file_path(file_path, ALLOWED_WRITE_DIRS):
        raise ValueError(f"File path '{file_path}' is not in allowed directories")

    # Check if file exists (prevent overwrites)
    if os.path.exists(file_path):
        raise FileExistsError(f"File already exists: {file_path}")

    # Check content size (max 50MB)
    content_size = len(content.encode())
    if content_size > 50 * 1024 * 1024:
        raise ValueError(f"Content too large: {content_size} bytes (max 50MB)")

    # Write file
    with open(file_path, 'w') as f:
        f.write(content)

    return {
        "file_path": file_path,
        "size_bytes": content_size,
        "status": "written"
    }


def _validate_file_path(file_path: str, allowed_dirs: List[str]) -> bool:
    """Validate file path is in allowed directories"""

    # Normalize path
    normalized = os.path.normpath(file_path)

    # Check for directory traversal
    if '..' in normalized:
        return False

    # Check against allowed directories
    for allowed_dir in allowed_dirs:
        if normalized.startswith(allowed_dir):
            return True

    return False


# ============================================================================
# API Tools
# ============================================================================

ALLOWED_API_DOMAINS = {
    'api.openai.com': {
        'rate_limit': '100/minute',
        'data_types': ['text']
    },
    'api.anthropic.com': {
        'rate_limit': '100/minute',
        'data_types': ['text']
    },
    'api.sendgrid.com': {
        'rate_limit': '10/second',
        'data_types': ['email_metadata']
    }
}


async def api_external_call_impl(
    parameters: Dict[str, Any],
    user_id: str,
    user_role: str
) -> Dict[str, Any]:
    """
    Call approved external API

    Parameters:
        url: API URL (must be allowed domain)
        method: HTTP method
        headers: Request headers
        body: Request body (optional)
    """

    import aiohttp

    url = parameters.get("url")
    method = parameters.get("method", "GET")
    headers = parameters.get("headers", {})
    body = parameters.get("body")

    # Validate domain
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if domain not in ALLOWED_API_DOMAINS:
        raise ValueError(f"Domain '{domain}' is not in allowed list")

    # Check request body size
    if body:
        body_size = len(body.encode())
        if body_size > 1 * 1024 * 1024:  # 1MB
            raise ValueError(f"Request body too large: {body_size} bytes (max 1MB)")

    # Make request
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=method,
            url=url,
            headers=headers,
            json=body if body else None,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response_data = await response.text()
            response_status = response.status

    return {
        "url": url,
        "status_code": response_status,
        "response": response_data,
        "domain": domain
    }
