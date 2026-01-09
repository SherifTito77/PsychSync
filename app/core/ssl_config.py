"""
SSL/TLS Configuration for Production Security
Enterprise-grade SSL configuration with modern security practices
"""

import logging
from pathlib import Path
import ssl
from typing import Any

logger = logging.getLogger(__name__)


class SSLConfig:
    """Production-ready SSL configuration class"""

    def __init__(self):
        self.cert_path = Path("certs/psychsync.crt")
        self.key_path = Path("certs/psychsync.key")

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create a secure SSL context for production use

        Returns:
            ssl.SSLContext: Configured SSL context with modern security settings
        """
        try:
            # Create SSL context with TLS
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load certificates
            if self.cert_path.exists() and self.key_path.exists():
                context.load_cert_chain(certfile=str(self.cert_path), keyfile=str(self.key_path))
                logger.info("SSL certificates loaded successfully")
            else:
                raise FileNotFoundError("SSL certificates not found")

            # Configure modern TLS settings
            self._configure_tls_versions(context)
            self._configure_cipher_suites(context)
            self._configure_security_options(context)

            logger.info("SSL context configured with modern security settings")
            return context

        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            raise

    def _configure_tls_versions(self, context: ssl.SSLContext) -> None:
        """Configure secure TLS versions"""
        # Enable only TLS 1.2 and 1.3 (disable older insecure versions)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3

        logger.info("TLS versions configured: TLSv1.2, TLSv1.3")

    def _configure_cipher_suites(self, context: ssl.SSLContext) -> None:
        """Configure strong cipher suites"""
        # Strong cipher suites for TLS 1.2
        strong_ciphers = [
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-CHACHA20-POLY1305",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-SHA384",
            "ECDHE-RSA-AES256-SHA384",
            "ECDHE-ECDSA-AES128-SHA256",
            "ECDHE-RSA-AES128-SHA256",
        ]

        try:
            context.set_ciphers(":".join(strong_ciphers))
            logger.info("Strong cipher suites configured")
        except Exception as e:
            logger.warning(f"Failed to set custom cipher suites: {e}")

    def _configure_security_options(self, context: ssl.SSLContext) -> None:
        """Configure additional security options"""
        try:
            # Enable HSTS (handled in middleware, but configure SSL options)
            context.options |= ssl.OP_NO_SSLv2
            context.options |= ssl.OP_NO_SSLv3
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1

            # Prefer server ciphers
            context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE

            logger.info("SSL security options configured")
        except Exception as e:
            logger.warning(f"Failed to set some SSL options: {e}")

    def verify_certificates(self) -> dict[str, Any]:
        """
        Verify SSL certificate configuration

        Returns:
            Dict with verification results
        """
        results = {
            "certificates_exist": False,
            "cert_file_readable": False,
            "key_file_readable": False,
            "cert_permissions_ok": False,
            "key_permissions_ok": False,
            "cert_valid": False,
            "issues": [],
        }

        try:
            # Check certificate files exist
            if self.cert_path.exists() and self.key_path.exists():
                results["certificates_exist"] = True
                logger.info("Certificate files found")
            else:
                results["issues"].append("Certificate files not found")
                return results

            # Check file permissions
            cert_stat = self.cert_path.stat()
            key_stat = self.key_path.stat()

            # Certificate should be readable by owner and group (640)
            if oct(cert_stat.st_mode)[-3:] in ["640", "600"]:
                results["cert_permissions_ok"] = True
                results["cert_file_readable"] = True
            else:
                results["issues"].append(
                    f"Certificate file permissions too open: {oct(cert_stat.st_mode)[-3:]}"
                )

            # Private key should only be readable by owner (600)
            if oct(key_stat.st_mode)[-3:] == "600":
                results["key_permissions_ok"] = True
                results["key_file_readable"] = True
            else:
                results["issues"].append(
                    f"Private key file permissions too open: {oct(key_stat.st_mode)[-3:]}"
                )

            # Try to load certificate
            try:
                context = ssl.create_default_context()
                context.load_cert_chain(certfile=str(self.cert_path), keyfile=str(self.key_path))
                results["cert_valid"] = True
                logger.info("Certificate validation successful")
            except Exception as e:
                results["issues"].append(f"Certificate validation failed: {e}")

        except Exception as e:
            results["issues"].append(f"Certificate verification error: {e}")
            logger.error(f"Certificate verification failed: {e}")

        return results

    def get_ssl_config_dict(self) -> dict[str, Any]:
        """
        Get SSL configuration for uvicorn

        Returns:
            Dict with SSL configuration parameters
        """
        return {
            "ssl_keyfile": str(self.key_path),
            "ssl_certfile": str(self.cert_path),
            "ssl_version": ssl.PROTOCOL_TLS,
            "ssl_ciphers": (
                "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
                "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"
                "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
            ),
        }


# Global SSL configuration instance
ssl_config = SSLConfig()
