#!/usr/bin/env python3
"""
Safe File Handling Utilities - Preventing File-Based Attacks

Prevents:
- Path Traversal (..)
- Arbitrary file write/read
- File inclusion attacks
- Zip slip attacks
- File size bombs
- Malicious file uploads

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import hashlib
import os
import re

# Optional dependency for file type detection
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None
import logging
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Raised when file validation fails"""


class SafeFileHandler:
    """
    Secure file handling utilities.

    CRITICAL: Always validate files before processing!
    """

    # Allowed MIME types for file uploads
    ALLOWED_MIME_TYPES = {
        "text/plain",
        "text/csv",
        "application/json",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "application/vnd.ms-excel",  # xls
        "application/zip",
    }

    # Dangerous file extensions to block
    BLOCKED_EXTENSIONS = {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".scr",
        ".pif",
        ".vbs",
        ".js",
        ".jar",
        ".app",
        ".deb",
        ".rpm",
        ".sh",
        ".ps1",
        ".vb",
        ".vbe",
        ".ws",
        ".wsf",
        ".dll",
        ".sys",
        ".cpl",
        ".msi",
    }

    # Maximum file sizes (bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB

    # ==================== File Upload Validation ====================

    @staticmethod
    def validate_file_upload(
        file_content: bytes,
        filename: str,
        content_type: str | None = None,
        max_size: int | None = None,
    ) -> dict:
        """
        Validate uploaded file.

        Performs comprehensive security checks:
        1. File size limits
        2. Filename validation
        3. Extension checking
        4. MIME type verification
        5. Content inspection (magic bytes)

        Returns:
            dict with validation results

        Raises:
            FileValidationError: If validation fails
        """
        if max_size is None:
            max_size = SafeFileHandler.MAX_FILE_SIZE

        # Check file size
        file_size = len(file_content)
        if file_size > max_size:
            raise FileValidationError(f"File too large. Maximum size: {max_size} bytes")

        if file_size == 0:
            raise FileValidationError("File is empty")

        # Validate filename
        safe_filename = SafeFileHandler.validate_filename(filename)

        # Check extension
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext in SafeFileHandler.BLOCKED_EXTENSIONS:
            raise FileValidationError(f"File extension not allowed: {ext}")

        # Verify MIME type
        detected_mime = SafeFileHandler.detect_mime_type(file_content)

        # If content-type provided, verify it matches
        if content_type and content_type != detected_mime:
            # Some MIME types are equivalent
            equivalent_types = {
                "text/plain": ["text/csv", "application/json"],
                "application/json": ["text/plain"],
            }

            if content_type not in equivalent_types.get(detected_mime, []):
                logger.warning(
                    f"Content-Type mismatch: declared={content_type}, detected={detected_mime}"
                )
                raise FileValidationError(
                    "Declared content type doesn't match file content"
                )

        # Check if MIME type is allowed
        if detected_mime not in SafeFileHandler.ALLOWED_MIME_TYPES:
            raise FileValidationError(f"File type not allowed: {detected_mime}")

        return {
            "filename": safe_filename,
            "size": file_size,
            "mime_type": detected_mime,
            "extension": ext,
            "is_valid": True,
        }

    @staticmethod
    def validate_filename(filename: str, max_length: int = 255) -> str:
        """
        Validate and sanitize filename.

        Prevents path traversal and dangerous filenames.
        """
        if not filename:
            raise FileValidationError("Filename cannot be empty")

        # Remove directory components
        filename = os.path.basename(filename)

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Check length
        if len(filename) > max_length:
            raise FileValidationError(
                f"Filename too long. Maximum: {max_length} characters"
            )

        # Check for dangerous characters
        dangerous_chars = ["..", "/", "\\", ":", "*", "?", '"', "<", ">", "|", "\x00"]
        for char in dangerous_chars:
            if char in filename:
                raise FileValidationError(
                    f"Filename contains dangerous character: {char}"
                )

        # Check for Windows reserved names
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        name_without_ext = os.path.splitext(filename)[0].upper()
        if name_without_ext in reserved_names:
            raise FileValidationError(
                f"Filename is a reserved system name: {name_without_ext}"
            )

        # Sanitize: replace remaining unsafe chars with underscore
        safe_filename = re.sub(r"[^\w\-_\.]", "_", filename)

        return safe_filename

    @staticmethod
    def detect_mime_type(file_content: bytes) -> str:
        """
        Detect MIME type from file content (magic bytes).

        Uses python-magic library for accurate detection.
        Falls back to basic detection if library unavailable.
        """
        if not MAGIC_AVAILABLE:
            # Basic fallback detection based on file signatures
            if file_content.startswith(b"PK\x03\x04"):
                return "application/zip"
            if file_content.startswith(b"%PDF"):
                return "application/pdf"
            if file_content.startswith(b"\x89PNG\r\n\x1a\n"):
                return "image/png"
            if file_content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg"
            return "application/octet-stream"

        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception as e:
            logger.error(f"Failed to detect MIME type: {e}")
            return "application/octet-stream"

    # ==================== Secure File Storage ====================

    @staticmethod
    def save_upload(
        file_content: bytes,
        filename: str,
        upload_dir: str,
        generate_unique_name: bool = True,
    ) -> str:
        """
        Securely save uploaded file.

        Args:
            file_content: File content bytes
            filename: Original filename
            upload_dir: Directory to save file
            generate_unique_name: Generate unique filename to prevent conflicts

        Returns:
            Path to saved file (relative to upload_dir)

        Raises:
            FileValidationError: If validation fails
        """
        # Validate file
        validation_result = SafeFileHandler.validate_file_upload(file_content, filename)

        # Create upload directory if needed
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        if generate_unique_name:
            # Use timestamp and random suffix
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            import uuid

            unique_id = uuid.uuid4().hex[:8]
            ext = validation_result["extension"]
            safe_filename = f"{timestamp}_{unique_id}{ext}"
        else:
            safe_filename = validation_result["filename"]

        # Save file
        file_path = upload_path / safe_filename

        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise FileValidationError("Failed to save file") from e

        logger.info(f"File saved successfully: {file_path}")

        return str(safe_filename)

    # ==================== File Reading ====================

    @staticmethod
    def safe_read_file(
        file_path: str,
        base_dir: str | None = None,
        max_size: int = 1024 * 1024,  # 1 MB
    ) -> bytes:
        """
        Safely read file with path traversal protection.

        Args:
            file_path: Path to file (can be relative)
            base_dir: Base directory (for relative paths)
            max_size: Maximum file size to read

        Returns:
            File content as bytes

        Raises:
            FileValidationError: If validation fails
        """
        # Resolve full path
        full_path = Path(file_path).resolve()

        # If base_dir provided, ensure file is under it
        if base_dir:
            base_path = Path(base_dir).resolve()

            # Check if file is under base_dir (prevents ../.. attacks)
            try:
                full_path.relative_to(base_path)
            except ValueError:
                raise FileValidationError(
                    "File path outside base directory (path traversal attempt)"
                )

        # Check file exists
        if not full_path.exists():
            raise FileValidationError("File does not exist")

        # Check it's a file (not directory/symlink)
        if not full_path.is_file():
            raise FileValidationError("Path is not a file")

        # Check file size
        file_size = full_path.stat().st_size
        if file_size > max_size:
            raise FileValidationError(f"File too large. Maximum: {max_size} bytes")

        # Read file
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise FileValidationError("Failed to read file") from e

    # ==================== Archive Extraction ====================

    @staticmethod
    def extract_zip(
        zip_path: str,
        extract_to: str,
        max_files: int = 1000,
        max_total_size: int = 1024 * 1024 * 1024,  # 1 GB
    ) -> list[str]:
        """
        Safely extract ZIP file with zip-slip protection.

        Prevents:
        - Zip slip (path traversal via archives)
        - File size bombs
        - Excessive file counts

        Returns:
            List of extracted file paths
        """
        extract_path = Path(extract_to).resolve()
        extracted_files = []
        total_size = 0

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Check file count
                if len(zip_ref.namelist()) > max_files:
                    raise FileValidationError(
                        f"ZIP contains too many files. Maximum: {max_files}"
                    )

                for member in zip_ref.namelist():
                    # Check for path traversal (zip-slip)
                    member_path = (extract_path / member).resolve()

                    # Ensure resolved path is under extract_path
                    try:
                        member_path.relative_to(extract_path)
                    except ValueError:
                        raise FileValidationError(
                            f"Path traversal attempt in ZIP: {member}"
                        )

                    # Get file size
                    info = zip_ref.getinfo(member)

                    # Check total size
                    total_size += info.file_size
                    if total_size > max_total_size:
                        raise FileValidationError(
                            f"Extracted files too large. Maximum: {max_total_size} bytes"
                        )

                    # Skip directories (they're created automatically)
                    if member.endswith("/"):
                        continue

                    # Extract file
                    zip_ref.extract(member, extract_path)
                    extracted_files.append(str(member_path))

                logger.info(f"Extracted {len(extracted_files)} files from ZIP")
                return extracted_files

        except zipfile.BadZipFile:
            raise FileValidationError("Invalid ZIP file")
        except Exception as e:
            logger.error(f"Failed to extract ZIP: {e}")
            raise FileValidationError("Failed to extract ZIP file") from e

    @staticmethod
    def extract_tar(
        tar_path: str,
        extract_to: str,
        max_files: int = 1000,
        max_total_size: int = 1024 * 1024 * 1024,  # 1 GB
    ) -> list[str]:
        """
        Safely extract TAR/TAR.GZ/TAR.BZ2 file.

        Same protections as extract_zip.
        """
        extract_path = Path(extract_to).resolve()
        extracted_files = []
        total_size = 0

        try:
            with tarfile.open(tar_path, "r:*") as tar_ref:
                # Check file count
                if len(tar_ref.getmembers()) > max_files:
                    raise FileValidationError(
                        f"Archive contains too many files. Maximum: {max_files}"
                    )

                for member in tar_ref.getmembers():
                    # Skip directories and symlinks
                    if not member.isfile():
                        continue

                    # Check for path traversal
                    member_path = (extract_path / member.name).resolve()

                    try:
                        member_path.relative_to(extract_path)
                    except ValueError:
                        raise FileValidationError(
                            f"Path traversal attempt in archive: {member.name}"
                        )

                    # Check total size
                    total_size += member.size
                    if total_size > max_total_size:
                        raise FileValidationError(
                            f"Extracted files too large. Maximum: {max_total_size} bytes"
                        )

                    # Extract file
                    tar_ref.extract(member, extract_path)
                    extracted_files.append(str(member_path))

                logger.info(f"Extracted {len(extracted_files)} files from archive")
                return extracted_files

        except tarfile.TarError:
            raise FileValidationError("Invalid TAR file")
        except Exception as e:
            logger.error(f"Failed to extract TAR: {e}")
            raise FileValidationError("Failed to extract TAR file") from e

    # ==================== File Hashing ====================

    @staticmethod
    def hash_file(file_path: str, algorithm: str = "sha256") -> str:
        """
        Calculate file hash.

        Useful for integrity verification.
        """
        hash_func = getattr(hashlib, algorithm, None)
        if not hash_func:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        hasher = hash_func()

        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)

            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash file: {e}")
            raise FileValidationError("Failed to hash file") from e

    # ==================== Temporary Files ====================

    @staticmethod
    def create_temp_file(
        content: bytes, suffix: str = ".tmp", prefix: str = "psychsync_"
    ) -> str:
        """
        Create secure temporary file.

        Uses tempfile module for secure temporary file creation.
        """
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                suffix=suffix,
                prefix=prefix,
                delete=False,  # We'll manage cleanup
            ) as tmp_file:
                tmp_file.write(content)
                temp_path = tmp_file.name

            logger.info(f"Created temp file: {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Failed to create temp file: {e}")
            raise FileValidationError("Failed to create temporary file") from e

    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Safely remove temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp file: {e}")


# ==================== Integration with FastAPI ====================


from fastapi import UploadFile


class SecureFileUpload:
    """Secure file upload handler for FastAPI"""

    @staticmethod
    async def read_upload(
        upload: UploadFile,
        max_size: int = 100 * 1024 * 1024,  # 100 MB
    ) -> bytes:
        """
        Safely read uploaded file with size limit.

        Prevents denial of service via huge files.
        """
        content = []
        total_size = 0

        # Read in chunks to enforce size limit during reading
        chunk_size = 8192

        while chunk := await upload.read(chunk_size):
            total_size += len(chunk)

            if total_size > max_size:
                # Close file
                await upload.close()
                raise FileValidationError(f"File too large. Maximum: {max_size} bytes")

            content.append(chunk)

        await upload.close()

        return b"".join(content)

    @staticmethod
    async def process_upload(
        upload: UploadFile, upload_dir: str, max_size: int | None = None
    ) -> dict:
        """
        Process file upload with full validation.

        Returns:
            dict with file info and saved path
        """
        # Read file
        file_content = await SecureFileUpload.read_upload(upload, max_size)

        # Save with validation
        saved_path = SafeFileHandler.save_upload(
            file_content, upload.filename or "unnamed", upload_dir
        )

        return {
            "filename": upload.filename,
            "saved_path": saved_path,
            "size": len(file_content),
            "content_type": upload.content_type,
        }


# ==================== Usage Examples ====================


def example_usage():
    """Example usage of safe file handling"""

    # Example 1: Validate uploaded file
    print("File Upload Validation:")
    file_content = b"Hello, World!"

    try:
        result = SafeFileHandler.validate_file_upload(file_content, "test.txt")
        print(f"  Valid: {result}")
    except FileValidationError as e:
        print(f"  Error: {e}")

    # Example 2: Save upload
    print("\nSaving Upload:")
    try:
        saved = SafeFileHandler.save_upload(file_content, "test.txt", "/tmp/uploads")
        print(f"  Saved: {saved}")
    except FileValidationError as e:
        print(f"  Error: {e}")

    # Example 3: Safe file read
    print("\nSafe File Read:")
    try:
        content = SafeFileHandler.safe_read_file(
            "/etc/passwd",  # Try to read sensitive file
            base_dir="/tmp",  # Will be blocked
        )
        print(f"  Content: {content[:50]}")
    except FileValidationError as e:
        print(f"  Blocked: {e}")


if __name__ == "__main__":
    import re

    print("Safe File Handling Utilities")
    print("Prevents: Path traversal, arbitrary file write, zip slip")
    print("=" * 60)
    example_usage()
