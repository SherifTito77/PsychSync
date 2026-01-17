"""
Email Template Renderer for Clinical Notifications

Renders HTML email templates with clinical data.
Supports multiple email clients with table-based responsive design.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailTemplateRenderer:
    """
    DESIGN DECISIONS:
    - Table-based HTML: Maximum email client compatibility
    - Inline CSS: Gmail and some clients strip <style> tags
    - Responsive: Mobile-first with max-width containers
    - Accessibility: Alt text, semantic HTML, high contrast
    - Fallbacks: MSO conditionals for Outlook support
    """

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize template renderer with template directory"""
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "emails" / "clinical"

        self.template_dir = Path(template_dir)
        logger.info(f"Email template directory: {self.template_dir}")

    def render_crisis_alert(
        self,
        recipient_name: str,
        alert_type: str,
        severity: str,
        alert_message: str,
        screening_type: str,
        screening_date: str,
        action_url: str,
        organization_name: str = "PsychSync"
    ) -> str:
        """
        Render crisis alert email template

        DESIGN DECISION:
        - Red gradient header for urgency
        - Severity badge with color coding
        - Emergency resources always visible
        - Clear CTA button above the fold
        """

        # Format alert type for display
        alert_type_formatted = alert_type.replace('_', ' ').title()

        # Determine severity color
        severity_colors = {
            'critical': '#dc2626',  # Red
            'high': '#ea580c',  # Orange
            'moderate': '#ca8a04',  # Yellow
            'low': '#16a34a'  # Green
        }
        severity_color = severity_colors.get(severity.lower(), '#6b7280')

        # Load template
        template_path = self.template_dir / "crisis_alert.html"

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

        except FileNotFoundError:
            logger.error(f"Template not found: {template_path}")
            return self._fallback_crisis_alert(
                recipient_name=recipient_name,
                alert_type=alert_type,
                severity=severity,
                alert_message=alert_message,
                action_url=action_url
            )

        # Render template with variables
        rendered = template_content.replace('{{ recipient_name }}', recipient_name)
        rendered = rendered.replace('{{ alert_type }}', alert_type)
        rendered = rendered.replace('{{ alert_type_formatted }}', alert_type_formatted)
        rendered = rendered.replace('{{ severity }}', severity)
        rendered = rendered.replace('{{ severity_color }}', severity_color)
        rendered = rendered.replace('{{ alert_message }}', alert_message)
        rendered = rendered.replace('{{ screening_type }}', screening_type)
        rendered = rendered.replace('{{ screening_date }}', screening_date)
        rendered = rendered.replace('{{ action_url }}', action_url)
        rendered = rendered.replace('{{ organization_name }}', organization_name)
        rendered = rendered.replace('{{ notification_date }}', datetime.now().strftime('%Y-%m-%d %H:%M'))
        rendered = rendered.replace('{{ unsubscribe_url }}', f'{action_url}/notifications')

        return rendered

    def _fallback_crisis_alert(
        self,
        recipient_name: str,
        alert_type: str,
        severity: str,
        alert_message: str,
        action_url: str
    ) -> str:
        """Fallback plain-text crisis alert if template fails to load"""
        return f"""
CRISIS ALERT - {severity.upper()}

Dear {recipient_name},

A {alert_type.replace('_', ' ').title()} alert has been triggered requiring immediate attention.

Details:
{alert_message}

Severity: {severity.upper()}

Please log in to review this screening immediately:
{action_url}

If this is a life-threatening emergency, contact emergency services.

---
PsychSync Clinical Platform
HIPAA-compliant • Secure • Encrypted
        """.strip()

    def render_pending_review(
        self,
        recipient_name: str,
        total_pending: int,
        pending_breakdown: Dict[str, int],
        hours_threshold: int,
        action_url: str,
        organization_name: str = "PsychSync"
    ) -> str:
        """
        Render pending review notification email

        DESIGN DECISION:
        - Table format for breakdown
        - Blue accent color (informational)
        - Grouped by screening type
        - Clear CTA to review queue

        TODO(human): Implement pending review email template
        - Create pending_review.html in templates/emails/clinical/
        - Use table layout for screening type breakdown
        - Include progress bar for completion rate
        - Add sorting options (by date, by severity)
        """

        # TODO(human): Implement HTML template rendering
        # For now, return plain text
        breakdown_text = "\n".join([
            f"- {screening_type}: {count} pending"
            for screening_type, count in pending_breakdown.items()
        ])

        return f"""
Pending Review Notification

Dear {recipient_name},

You have {total_pending} screening(s) that have been pending review for more than {hours_threshold} hours:

{breakdown_text}

Please log in to review these screenings at your earliest convenience:
{action_url}

---
PsychSync Clinical Platform
HIPAA-compliant • Secure • Encrypted
        """.strip()

    def render_weekly_summary(
        self,
        recipient_name: str,
        week_start: str,
        week_end: str,
        total_screenings: int,
        completion_rate: float,
        crisis_count: int,
        avg_response_time: float,
        top_concerns: list,
        action_url: str,
        organization_name: str = "PsychSync"
    ) -> str:
        """
        Render weekly summary email for clinicians

        DESIGN DECISION:
        - Professional dashboard-style layout
        - Charts rendered as HTML tables or embedded images
        - Green/blue color scheme (informational)
        - Printable format
        - Export to PDF option

        TODO(human): Implement weekly summary email template
        - Create weekly_summary.html in templates/emails/clinical/
        - Include visual charts (use HTML/CSS bar charts)
        - Show trends vs previous week (arrows up/down)
        - Add "Download PDF Report" link
        - Include team comparison if applicable
        """

        # TODO(human): Implement HTML template rendering
        # For now, return plain text
        concerns_text = "\n".join([
            f"- {concern}: {count}"
            for concern, count in top_concerns[:5]
        ])

        return f"""
Weekly Clinical Summary - {week_start} to {week_end}

Dear {recipient_name},

Here's your weekly clinical analytics summary:

📊 Screening Activity
- Total Screenings: {total_screenings}
- Completion Rate: {completion_rate:.1f}%
- Crisis Alerts: {crisis_count}
- Avg Response Time: {avg_response_time:.1f} minutes

🔍 Top Concerns This Week:
{concerns_text}

View full analytics dashboard:
{action_url}

---
PsychSync Clinical Platform
HIPAA-compliant • Secure • Encrypted
        """.strip()


# Singleton instance for easy importing
_email_renderer: Optional[EmailTemplateRenderer] = None


def get_email_renderer() -> EmailTemplateRenderer:
    """Get or create singleton email renderer instance"""
    global _email_renderer
    if _email_renderer is None:
        _email_renderer = EmailTemplateRenderer()
    return _email_renderer
