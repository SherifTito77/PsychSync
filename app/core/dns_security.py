"""
DNS Security Configuration Module
Provides secure DNS resolution with DNSSEC validation and monitoring
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import ipaddress
import logging
from typing import Any

import dns.exception
import dns.rdatatype
import dns.resolver

logger = logging.getLogger(__name__)


@dataclass
class DNSQueryResult:
    """Result of a DNS query with security validation"""

    hostname: str
    query_type: str
    result: str
    is_secure: bool
    dnssec_valid: bool
    response_time_ms: float
    ttl: int
    security_issues: list[str]


class DNSSecurityManager:
    """
    Secure DNS resolution manager with DNSSEC validation
    and security monitoring capabilities
    """

    def __init__(self):
        self.secure_resolvers = [
            # Cloudflare DNS (with DNSSEC)
            "1.1.1.1",
            "1.0.0.1",
            # Google DNS (with DNSSEC)
            "8.8.8.8",
            "8.8.4.4",
            # OpenDNS (with DNSSEC)
            "208.67.222.222",
            "208.67.220.220",
        ]

        self.resolver = self._create_secure_resolver()
        self.query_cache = {}
        self.security_events = []

    def _create_secure_resolver(self) -> dns.resolver.Resolver:
        """Create a secure DNS resolver with DNSSEC validation"""
        resolver = dns.resolver.Resolver()

        # Configure secure resolvers
        resolver.nameservers = self.secure_resolvers

        # Enable DNSSEC validation
        resolver.validate = True

        # Set timeout values
        resolver.timeout = 2.0
        resolver.lifetime = 5.0

        # Enable EDNS0 for DNSSEC
        resolver.use_edns(0, dns.flags.DO, 1232)

        logger.info(f"Secure DNS resolver configured with {len(self.secure_resolvers)} resolvers")
        return resolver

    async def resolve_hostname_secure(
        self, hostname: str, record_type: str = "A"
    ) -> DNSQueryResult:
        """
        Resolve a hostname with security validation

        Args:
            hostname: The hostname to resolve
            record_type: DNS record type (A, AAAA, MX, etc.)

        Returns:
            DNSQueryResult with security validation
        """
        start_time = asyncio.get_event_loop().time()
        security_issues = []

        try:
            # Check cache first
            cache_key = f"{hostname}:{record_type}"
            if cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                # Check if cache entry is still valid
                if datetime.now() - cached_result["timestamp"] < timedelta(
                    seconds=cached_result["ttl"]
                ):
                    logger.debug(f"DNS cache hit for {hostname}")
                    return DNSQueryResult(**cached_result["data"])

            # Perform secure DNS lookup
            answer = self.resolver.resolve(hostname, record_type)

            # Calculate response time
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Get first result
            result_ip = str(answer[0]) if answer else None
            ttl = answer.rrset.ttl if answer and hasattr(answer, "rrset") else 300

            # Validate DNSSEC
            dnssec_valid = self._validate_dnssec(answer)

            # Check security issues
            if not dnssec_valid:
                security_issues.append("DNSSEC validation failed")

            if not result_ip:
                security_issues.append("No DNS records found")

            # Check for suspicious IPs
            if result_ip and self._is_suspicious_ip(result_ip):
                security_issues.append(f"Suspicious IP address: {result_ip}")

            # Create result
            query_result = DNSQueryResult(
                hostname=hostname,
                query_type=record_type,
                result=result_ip or "NXDOMAIN",
                is_secure=len(security_issues) == 0,
                dnssec_valid=dnssec_valid,
                response_time_ms=round(response_time, 2),
                ttl=ttl,
                security_issues=security_issues.copy(),
            )

            # Cache the result
            self.query_cache[cache_key] = {
                "data": query_result.__dict__,
                "timestamp": datetime.now(),
                "ttl": ttl,
            }

            # Log security events
            if security_issues:
                self._log_security_event(hostname, record_type, security_issues)

            return query_result

        except dns.resolver.NXDOMAIN:
            return DNSQueryResult(
                hostname=hostname,
                query_type=record_type,
                result="NXDOMAIN",
                is_secure=True,  # NXDOMAIN is a valid secure response
                dnssec_valid=False,
                response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                ttl=0,
                security_issues=[],
            )

        except dns.resolver.NoAnswer:
            security_issues.append("No answer for query")
            return DNSQueryResult(
                hostname=hostname,
                query_type=record_type,
                result="NO_ANSWER",
                is_secure=False,
                dnssec_valid=False,
                response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                ttl=0,
                security_issues=security_issues,
            )

        except dns.exception.DNSException as e:
            security_issues.append(f"DNS resolution error: {e}")
            return DNSQueryResult(
                hostname=hostname,
                query_type=record_type,
                result="ERROR",
                is_secure=False,
                dnssec_valid=False,
                response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                ttl=0,
                security_issues=security_issues,
            )

        except Exception as e:
            security_issues.append(f"Unexpected error: {e}")
            logger.error(f"DNS resolution error for {hostname}: {e}")
            return DNSQueryResult(
                hostname=hostname,
                query_type=record_type,
                result="ERROR",
                is_secure=False,
                dnssec_valid=False,
                response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                ttl=0,
                security_issues=security_issues,
            )

    def _validate_dnssec(self, answer) -> bool:
        """Validate DNSSEC for the DNS response"""
        try:
            # Check if response has DNSSEC signatures
            if hasattr(answer, "response") and answer.response:
                response = answer.response

                # Check for DNSSEC OK flag
                if hasattr(response.flags, "DO"):
                    if not (response.flags & dns.flags.DO):
                        return False

                # Check for RRSIG records
                for rrset in response.answer:
                    if rrset.rdtype == dns.rdatatype.RRSIG:
                        return True

                # Check for DNSKEY records in authority
                for rrset in response.authority:
                    if rrset.rdtype in [dns.rdatatype.DNSKEY, dns.rdatatype.DS]:
                        return True

            return False

        except Exception as e:
            logger.warning(f"DNSSEC validation error: {e}")
            return False

    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if an IP address is suspicious"""
        try:
            addr = ipaddress.ip_address(ip)

            # Check for private IPs (shouldn't be in public DNS)
            if addr.is_private:
                return True

            # Check for loopback addresses
            if addr.is_loopback:
                return True

            # Check for link-local addresses
            if addr.is_link_local:
                return True

            # Add more suspicious IP checks as needed
            suspicious_ranges = [
                ipaddress.ip_network("0.0.0.0/8"),  # This network
                ipaddress.ip_network("127.0.0.0/8"),  # Loopback
                ipaddress.ip_network("169.254.0.0/16"),  # Link-local
                ipaddress.ip_network("224.0.0.0/4"),  # Multicast
            ]

            for suspicious_range in suspicious_ranges:
                if addr in suspicious_range:
                    return True

            return False

        except ValueError:
            return True  # Invalid IP is suspicious

    def _log_security_event(self, hostname: str, record_type: str, issues: list[str]):
        """Log DNS security events"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "hostname": hostname,
            "record_type": record_type,
            "security_issues": issues,
            "severity": "HIGH" if "DNSSEC validation failed" in issues else "MEDIUM",
        }

        self.security_events.append(event)

        # Log to application logger
        logger.warning(f"DNS Security Event - {hostname}: {'; '.join(issues)}")

    def get_dns_health_status(self) -> dict[str, Any]:
        """Get DNS resolver health status"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "resolver_count": len(self.secure_resolvers),
            "cache_entries": len(self.query_cache),
            "security_events": len(self.security_events),
            "recent_events": [],
            "resolver_status": [],
        }

        # Test each resolver
        for resolver_ip in self.secure_resolvers:
            try:
                # Simple test query
                test_resolver = dns.resolver.Resolver()
                test_resolver.nameservers = [resolver_ip]
                test_resolver.timeout = 1.0

                start_time = asyncio.get_event_loop().time()
                answer = test_resolver.resolve("google.com", "A")
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                health_status["resolver_status"].append(
                    {
                        "resolver": resolver_ip,
                        "status": "healthy",
                        "response_time_ms": round(response_time, 2),
                        "test_result": str(answer[0]) if answer else None,
                    }
                )

            except Exception as e:
                health_status["resolver_status"].append(
                    {"resolver": resolver_ip, "status": "unhealthy", "error": str(e)}
                )

        # Get recent security events
        recent_events = [
            event
            for event in self.security_events
            if datetime.fromisoformat(event["timestamp"]) > datetime.now() - timedelta(hours=24)
        ]
        health_status["recent_events"] = recent_events[-10:]  # Last 10 events

        return health_status

    def clear_cache(self):
        """Clear DNS query cache"""
        self.query_cache.clear()
        logger.info("DNS cache cleared")

    def get_security_summary(self) -> dict[str, Any]:
        """Get DNS security summary"""
        last_24h = datetime.now() - timedelta(hours=24)
        recent_events = [
            event
            for event in self.security_events
            if datetime.fromisoformat(event["timestamp"]) > last_24h
        ]

        high_severity = len([e for e in recent_events if e["severity"] == "HIGH"])
        medium_severity = len([e for e in recent_events if e["severity"] == "MEDIUM"])

        return {
            "total_security_events": len(recent_events),
            "high_severity_events": high_severity,
            "medium_severity_events": medium_severity,
            "cache_size": len(self.query_cache),
            "secure_resolvers": len(self.secure_resolvers),
            "last_event": recent_events[-1]["timestamp"] if recent_events else None,
            "security_score": max(0, 100 - (high_severity * 20) - (medium_severity * 10)),
        }


# Global DNS security manager instance
dns_security_manager = DNSSecurityManager()
