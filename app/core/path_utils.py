"""
Path Sanitization Utilities for Secure File Operations
Provides safe path handling to prevent directory traversal attacks
"""

from pathlib import Path
from typing import Optional, List, Set
import re


class PathTraversalError(Exception):
    """Raised when path traversal is detected"""
    pass


class FileExtensionError(Exception):
    """Raised when file extension is not allowed"""
    pass


def sanitize_path(
    user_path: str,
    allowed_dir: Path,
    allowed_extensions: Optional[Set[str]] = None
) -> Path:
    """
    Sanitize and validate a user-provided path

    This function prevents directory traversal attacks by:
    1. Resolving the path to its absolute form
    2. Verifying it's within the allowed directory
    3. Checking file extension against whitelist

    Args:
        user_path: User-provided path (relative or absolute)
        allowed_dir: Directory that files are allowed from
        allowed_extensions: Set of allowed file extensions (e.g., {'.txt', '.pdf'})
                             If None, all extensions allowed

    Returns:
        Absolute, sanitized Path object

    Raises:
        PathTraversalError: If path attempts to escape allowed directory
        FileExtensionError: If file extension not in whitelist

    Example:
        >>> allowed_dir = Path("/var/www/uploads")
        >>> safe_path = sanitize_path("../../etc/passwd", allowed_dir)
        PathTraversalError: Path traversal detected

        >>> safe_path = sanitize_path("image.png", allowed_dir, {".png", ".jpg"})
        Path("/var/www/uploads/image.png")
    """
    # Join with allowed directory
    full_path = (allowed_dir / user_path).resolve()

    # Verify it's within allowed directory
    allowed_resolved = allowed_dir.resolve()

    try:
        full_path.relative_to(allowed_resolved)
    except ValueError:
        raise PathTraversalError(
            f"Path traversal detected: {user_path} attempts to access "
            f"{full_path} outside allowed directory {allowed_dir}"
        )

    # Check file extension if whitelist provided
    if allowed_extensions is not None and full_path.is_file():
        if full_path.suffix.lower() not in allowed_extensions:
            raise FileExtensionError(
                f"File extension {full_path.suffix} not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )

    return full_path


def safe_filename(filename: str) -> str:
    """
    Sanitize a user-provided filename

    Removes dangerous characters and ensures safe filename

    Args:
        filename: User-provided filename

    Returns:
        Sanitized filename safe for filesystem

    Example:
        >>> safe_filename("../../etc/passwd")
        "etc_passwd"

        >>> safe_filename("my document.txt")
        "my_document.txt"
    """
    # Remove path separators
    sanitized = filename.replace("/", "_").replace("\\", "_")

    # Remove dangerous characters
    sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)

    # Remove control characters
    sanitized = re.sub(r'[-]', '', sanitized)

    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        sanitized = name[:250] + ('.' + ext if ext else '')

    return sanitized


def validate_file_type(
    file_path: Path,
    allowed_mime_types: Optional[Set[str]] = None,
    allowed_extensions: Optional[Set[str]] = None
) -> bool:
    """
    Validate file type by extension and/or MIME type

    Args:
        file_path: Path to file
        allowed_mime_types: Set of allowed MIME types
        allowed_extensions: Set of allowed extensions (with dot, e.g., '.jpg')

    Returns:
        True if file type is allowed

    Example:
        >>> validate_file_type(Path("image.jpg"), {".jpg", ".png"})
        True

        >>> validate_file_type(Path("script.php"), {".jpg", ".png"})
        False
    """
    if not file_path.exists():
        return False

    # Check extension
    if allowed_extensions is not None:
        if file_path.suffix.lower() not in allowed_extensions:
            return False

    # Check MIME type if requested
    if allowed_mime_types is not None:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type not in allowed_mime_types:
            return False

    return True


# Common allowed extensions for different file types
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm'}
ALLOWED_ARCHIVE_EXTENSIONS = {'.zip', '.tar', '.gz', '.bz2'}
