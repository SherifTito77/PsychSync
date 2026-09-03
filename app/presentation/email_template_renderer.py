"""
Email Template Renderer

This component is responsible for rendering email templates.
It is part of the PRESENTATION LAYER, not the business logic layer.

Responsibilities:
- Template loading and caching
- Context sanitization
- HTML rendering
- Template preview

NOT responsible for:
- Email delivery (that's EmailService's job)
- Business logic (belongs in domain layer)
- Data access (belongs in repository layer)
"""

import html
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import bleach
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTemplateRenderer:
    """
    Email template renderer with security controls

    This class handles presentation concerns only:
    - Loading templates from filesystem
    - Rendering templates with context
    - Sanitizing output

    Business logic about WHAT to send belongs in services.
    """

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize template renderer

        Args:
            template_dir: Directory containing email templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates" / "emails"

        self.template_dir = template_dir
        self.max_template_size = 100000  # 100KB
        self.allowed_template_extensions = {".html", ".htm", ".txt"}

        # Secure Jinja2 environment with autoescape
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            auto_reload=False,  # Security: disable auto-reload in production
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _validate_template_name(self, template_name: str) -> bool:
        """
        Validate template name to prevent path traversal

        Args:
            template_name: Name of template file

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check for path traversal attempts
            if ".." in template_name or "/" in template_name or "\\" in template_name:
                logger.warning(f"Path traversal attempt detected: {template_name}")
                return False

            # Check extension
            template_path = Path(template_name)
            if template_path.suffix.lower() not in self.allowed_template_extensions:
                logger.warning(f"Invalid template extension: {template_name}")
                return False

            # Check length
            if len(template_name) > 100:
                logger.warning(f"Template name too long: {template_name}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating template name {template_name}: {e}")
            return False

    def _sanitize_template_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize template context to prevent injection attacks

        Args:
            context: Template context dictionary

        Returns:
            Sanitized context dictionary
        """
        sanitized = {}

        for key, value in context.items():
            if isinstance(value, str):
                # Sanitize string values
                sanitized_value = bleach.clean(
                    value,
                    tags=["p", "br", "strong", "em", "u", "span", "div"],
                    attributes={"*": ["class", "id"]},
                    strip=True,
                )
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_template_context(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        bleach.clean(str(item), tags=[], strip=True)
                        if isinstance(item, str)
                        else item
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL to prevent malicious links

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL string
        """
        if not url:
            return ""

        try:
            # Parse URL
            parsed = urlparse(url)

            # Only allow specific schemes
            allowed_schemes = {"http", "https"}
            if parsed.scheme.lower() not in allowed_schemes:
                logger.warning(f"Blocked URL with unsafe scheme: {url}")
                return ""

            # Check for suspicious patterns
            if "javascript:" in url.lower() or "data:" in url.lower():
                logger.warning(f"Blocked suspicious URL: {url}")
                return ""

            # Ensure URL is properly encoded
            safe_url = html.escape(url)
            return safe_url

        except Exception as e:
            logger.error(f"Error sanitizing URL: {e}")
            return ""

    def _get_default_context(self) -> dict[str, Any]:
        """
        Get default template context with common variables

        Returns:
            Default context dictionary
        """
        return {
            "user_name": "User",
            "dashboard_url": self._sanitize_url(
                settings.FRONTEND_URL or "https://app.psychsync.com/dashboard"
            ),
            "help_url": self._sanitize_url(
                f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/help"
            ),
            "settings_url": self._sanitize_url(
                f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/settings"
            ),
            "unsubscribe_url": self._sanitize_url(
                f"{settings.FRONTEND_URL or 'https://app.psychsync.com'}/unsubscribe"
            ),
            "company_name": "PsychSync",
            "current_year": datetime.now().year,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render email template with context

        Args:
            template_name: Name of template file
            context: Template context data

        Returns:
            Rendered HTML string

        Raises:
            ValueError: If template name is invalid
            RuntimeError: If rendering fails
        """
        try:
            # Validate template name
            if not self._validate_template_name(template_name):
                raise ValueError(f"Invalid template name: {template_name}")

            # Get template
            template = self.env.get_template(template_name)

            # Sanitize context
            sanitized_context = self._sanitize_template_context(context)

            # Add secure default context
            default_context = self._get_default_context()
            merged_context = {**default_context, **sanitized_context}

            # Render template
            rendered_content = template.render(**merged_context)

            # Additional content sanitization
            rendered_content = bleach.clean(
                rendered_content,
                tags=[
                    "html",
                    "head",
                    "body",
                    "title",
                    "meta",
                    "link",
                    "style",
                    "div",
                    "span",
                    "p",
                    "br",
                    "strong",
                    "em",
                    "u",
                    "i",
                    "b",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "ul",
                    "ol",
                    "li",
                    "a",
                    "img",
                    "table",
                    "tr",
                    "td",
                    "th",
                    "header",
                    "footer",
                    "section",
                    "article",
                    "aside",
                    "nav",
                ],
                attributes={
                    "*": ["class", "id"],
                    "a": ["href", "title", "target"],
                    "img": ["src", "alt", "width", "height", "title"],
                    "meta": ["name", "content", "charset"],
                    "link": ["rel", "href", "type"],
                    "style": ["type"],
                    "table": ["border", "cellpadding", "cellspacing"],
                },
                strip=True,
            )

            # Check template size
            if len(rendered_content) > self.max_template_size:
                raise ValueError(
                    f"Template content too large: {len(rendered_content)} bytes"
                )

            logger.debug(f"Successfully rendered template: {template_name}")
            return rendered_content

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            # Return safe fallback
            return (
                f"<p>Email template could not be rendered. Please contact support.</p>"
            )

    def preview_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Preview email template without sending

        Args:
            template_name: Name of template file
            context: Template context data

        Returns:
            Rendered HTML string or error message
        """
        try:
            return self.render_template(template_name, context)

        except Exception as e:
            logger.error(f"Failed to preview template {template_name}: {e}")
            return f"Error rendering template: {e}"


# Singleton instance for use in application
email_template_renderer = EmailTemplateRenderer()
