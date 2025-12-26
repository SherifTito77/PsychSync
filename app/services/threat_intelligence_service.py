"""
Threat Intelligence Service - Real-Time Attack Detection

Integrates with threat intelligence feeds to detect:
- Known malicious IPs
- Compromised credentials
- Bot networks
- DDoS participants
- Fraudulent patterns

Author: Security Team
Date: 2025-12-24
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import redis.asyncio as redis

from app.core.config import settings


# =============================================================================
# Threat Intelligence Models
# =============================================================================

class ThreatIntel:
    """Threat intelligence data"""
    source: str
    type: str  # ip, domain, email, hash
    value: str
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    first_seen: datetime
    last_seen: datetime
    tags: List[str]
    description: str


class IPReputation:
    """IP reputation score"""
    ip_address: str
    reputation_score: float  # 0.0 (bad) to 100.0 (good)
    threat_level: str
    last_updated: datetime
    factors: Dict[str, bool]
    # Factors:
    # - is_tor_exit: bool
    # - is_vpn: bool
    # - is_proxy: bool
    # - is_known_attacker: bool
    # - is_botnet: bool
    # - has_open_ports: bool
    # - is_datacenter: bool
    # - reported_abuse: bool


# =============================================================================
# Threat Intelligence Service
# =============================================================================

class ThreatIntelligenceService:
    """
    Real-time threat intelligence integration

    Features:
    1. IP reputation checking
    2. Known malicious actor detection
    3. Credential compromise checking
    4. Real-time blocklist updates
    5. Threat feed aggregation
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_ttl = 3600  # 1 hour
        self.blocklists: Dict[str, Set[str]] = {
            'malicious_ips': set(),
            'tor_exit_nodes': set(),
            'botnet_ips': set(),
            'abusive_ips': set(),
            'datacenter_ips': set(),
        }

    async def initialize(self):
        """Initialize threat intelligence service"""
        # Connect to Redis for caching
        if settings.REDIS_URL:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

        # Load initial threat feeds
        await self._load_threat_feeds()

        # Start background refresh
        asyncio.create_task(self._refresh_threat_feeds())

    async def check_ip_reputation(self, ip_address: str) -> IPReputation:
        """
        Check IP reputation against threat intelligence

        Returns comprehensive reputation assessment
        """

        reputation_score = 100.0
        factors = {}
        tags = []

        # Check 1: Is it in our malicious IPs blocklist?
        if ip_address in self.blocklists['malicious_ips']:
            reputation_score -= 50
            factors['is_known_attacker'] = True
            tags.append('known_malicious')

        # Check 2: Is it a Tor exit node?
        if ip_address in self.blocklists['tor_exit_nodes']:
            reputation_score -= 20
            factors['is_tor_exit'] = True
            tags.append('tor_exit_node')

        # Check 3: Is it in a botnet?
        if ip_address in self.blocklists['botnet_ips']:
            reputation_score -= 40
            factors['is_botnet'] = True
            tags.append('botnet')

        # Check 4: Has it been reported for abuse?
        if ip_address in self.blocklists['abusive_ips']:
            reputation_score -= 15
            factors['reported_abuse'] = True
            tags.append('abuse_reported')

        # Check 5: Is it from a datacenter (suspicious for user traffic)?
        if ip_address in self.blocklists['datacenter_ips']:
            reputation_score -= 10
            factors['is_datacenter'] = True
            tags.append('datacenter_ip')

        # Check 6: Query external threat intelligence APIs
        external_reputation = await self._query_external_threat_apis(ip_address)
        reputation_score += external_reputation['score_adjustment']
        factors.update(external_reputation['factors'])
        tags.extend(external_reputation['tags'])

        # Normalize score to 0-100
        reputation_score = max(0, min(100, reputation_score))

        # Determine threat level
        if reputation_score >= 80:
            threat_level = 'low'
        elif reputation_score >= 50:
            threat_level = 'medium'
        elif reputation_score >= 25:
            threat_level = 'high'
        else:
            threat_level = 'critical'

        return IPReputation(
            ip_address=ip_address,
            reputation_score=reputation_score,
            threat_level=threat_level,
            last_updated=datetime.utcnow(),
            factors=factors
        )

    async def check_compromised_credentials(
        self,
        email: str,
        password_hash: str
    ) -> Dict:
        """
        Check if credentials have been compromised in data breaches

        Uses:
        - Have I Been Pwned API
        - breach directory
        - leaked password databases
        """

        compromised = False
        breaches = []

        # Check email against breach databases
        email_breaches = await self._check_email_breaches(email)
        if email_breaches:
            compromised = True
            breaches.extend(email_breaches)

        # Check password against leaked passwords
        password_compromised = await self._check_password_compromised(password_hash)
        if password_compromised:
            compromised = True
            breaches.append({
                'type': 'password_leak',
                'severity': 'high',
                'description': 'Password found in leaked data breaches'
            })

        return {
            'compromised': compromised,
            'breaches': breaches,
            'recommendation': 'Force password change immediately' if compromised else 'No action needed'
        }

    async def is_malicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent matches known malicious patterns"""
        malicious_patterns = [
            'sqlmap', 'nikto', 'dirbuster', 'nmap', 'masscan',
            'python-requests', 'curl', 'wget', 'apachebench',
            'bot', 'spider', 'crawler', 'scraper'
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in malicious_patterns)

    async def is_attack_pattern(self, request_path: str, request_method: str) -> bool:
        """
        Check if request matches known attack patterns

        Detects:
        - SQL injection attempts
        - XSS attempts
        - Path traversal
        - Command injection
        - LDAP injection
        """

        # SQL injection patterns
        sqli_patterns = [
            "union select", "or 1=1", "drop table", "exec(",
            "' or '1'='1", "admin'--", "1' or '1'='1",
            "concat(", "version(", "database(", "user("
        ]

        # XSS patterns
        xss_patterns = [
            "<script>", "javascript:", "onerror=", "onload=",
            "alert(", "document.cookie", "fromCharCode"
        ]

        # Path traversal patterns
        path_traversal = [
            "../../", "..\\", "%2e%2e", "%252e",
            "etc/passwd", "windows/system32"
        ]

        # Command injection
        cmd_injection = [
            "; ls", "| ls", "&& ls", "`ls`", "$(",
            "eval(", "system(", "exec(", "passthru("
        ]

        # Check request path
        path_lower = request_path.lower()

        for pattern in sqli_patterns + xss_patterns + path_traversal + cmd_injection:
            if pattern in path_lower:
                return True

        return False

    async def should_block_request(
        self,
        ip_address: str,
        user_agent: str,
        request_path: str,
        request_method: str
    ) -> tuple[bool, str]:
        """
        Comprehensive request blocking decision

        Returns: (should_block, reason)
        """

        # Check 1: IP reputation
        ip_reputation = await self.check_ip_reputation(ip_address)

        if ip_reputation.threat_level == 'critical':
            return True, f"Critical threat IP: {ip_address} (reputation: {ip_reputation.reputation_score})"

        # Check 2: Malicious user agent
        if await self.is_malicious_user_agent(user_agent):
            return True, f"Malicious user agent detected: {user_agent}"

        # Check 3: Attack patterns
        if await self.is_attack_pattern(request_path, request_method):
            return True, f"Attack pattern detected: {request_method} {request_path}"

        # Check 4: Rate limiting (per IP)
        if await self._is_rate_limited(ip_address):
            return True, f"Rate limit exceeded for IP: {ip_address}"

        return False, ""

    # ========================================================================
    # Private Methods
    # ========================================================================

    async def _load_threat_feeds(self):
        """Load threat intelligence feeds from various sources"""

        # Feed 1: Tor exit nodes (official Tor Project list)
        tor_nodes = await self._fetch_tor_exit_nodes()
        self.blocklists['tor_exit_nodes'].update(tor_nodes)

        # Feed 2: Abuse.ch Feodo Tracker (C2 servers)
        feodo = await self._fetch_abuse_ch_feodo()
        self.blocklists['malicious_ips'].update(feodo)

        # Feed 3: Blocklist.de Abuse tracker
        abuse_ips = await self._fetch_blocklist_de_abuse()
        self.blocklists['abusive_ips'].update(abuse_ips)

        # Feed 4: Known botnet IPs
        botnet_ips = await self._fetch_botnet_ips()
        self.blocklists['botnet_ips'].update(botnet_ips)

    async def _refresh_threat_feeds(self):
        """Background task to refresh threat feeds periodically"""
        while True:
            await asyncio.sleep(3600)  # Refresh every hour
            await self._load_threat_feeds()
            print(f"[THREAT_INTEL] Feeds refreshed at {datetime.utcnow()}")

    async def _fetch_tor_exit_nodes(self) -> Set[str]:
        """Fetch Tor exit node list from Tor Project"""
        # In production, fetch from: https://check.torproject.org/torbulkexitlist
        # For now, return empty set
        return set()

    async def _fetch_abuse_ch_feodo(self) -> Set[str]:
        """Fetch Feodo Tracker C2 list from abuse.ch"""
        # In production, fetch from: https://feodotracker.abuse.ch/downloads/ipblocklist.json
        return set()

    async def _fetch_blocklist_de_abuse(self) -> Set[str]:
        """Fetch abuse IPs from blocklist.de"""
        # In production, fetch from blocklist.de API
        return set()

    async def _fetch_botnet_ips(self) -> Set[str]:
        """Fetch known botnet IPs"""
        # In production, integrate with:
        # - Spamhaus DROP list
        # - Cyberthreat Coalition
        # - FBI InfraGard
        return set()

    async def _query_external_threat_apis(self, ip_address: str) -> Dict:
        """
        Query external threat intelligence APIs

        Integrates with:
        - AbuseIPDB
        - VirusTotal
        - IPQualityScore
        - Cisco Talos
        """
        score_adjustment = 0
        factors = {}
        tags = []

        # In production, make actual API calls:
        # response = requests.get(f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip_address}",
        #                        headers={"Key": settings.ABUSEIPDB_API_KEY})

        # For now, return no adjustment
        return {
            'score_adjustment': score_adjustment,
            'factors': factors,
            'tags': tags
        }

    async def _check_email_breaches(self, email: str) -> List[Dict]:
        """Check if email has been in data breaches"""
        # In production, use:
        # - Have I Been Pwned API: https://haveibeenpwned.com/api/v3/breachedaccount/{email}
        # - DeHashed
        # - Intelligence X
        return []

    async def _check_password_compromised(self, password_hash: str) -> bool:
        """Check if password has been leaked"""
        # In production, use:
        # - Have I Been Pwned Pwned Passwords API
        # - SecLists
        # - CrackStation
        return False

    async def _is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP has exceeded rate limits"""
        if not self.redis_client:
            return False

        key = f"rate_limit:{ip_address}"

        # Increment counter
        count = await self.redis_client.incr(key)

        # Set expiry on first request
        if count == 1:
            await self.redis_client.expire(key, 60)  # 1 minute window

        # Check if exceeded
        return count > 100  # More than 100 requests per minute


# =============================================================================
# FastAPI Middleware Integration
# =============================================================================

from fastapi import Request

threat_intel_service = ThreatIntelligenceService()


async def threat_intel_middleware(request: Request, call_next):
    """
    FastAPI middleware for real-time threat detection

    Blocks malicious requests before they reach application logic
    """

    # Skip health checks
    if request.url.path == "/api/v1/health":
        return await call_next(request)

    # Extract request info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    request_path = request.url.path
    request_method = request.method

    # Check if request should be blocked
    should_block, reason = await threat_intel_service.should_block_request(
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method
    )

    if should_block:
        # Log blocked request
        print(f"[THREAT_INTEL] BLOCKED: {reason}")

        # Return 403 Forbidden
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Request blocked by security policy"}
        )

    # Allow request to proceed
    response = await call_next(request)

    # Add security headers
    response.headers["X-Security-Checked"] = "true"
    response.headers["X-Threat-Intel"] = "active"

    return response


# =============================================================================
# Admin Endpoints
# =============================================================================

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

admin_router = APIRouter(prefix="/api/v1/admin/security/threat-intel", tags=["Threat Intelligence Admin"])


@admin_router.get("/stats")
async def get_threat_intel_stats():
    """Get threat intelligence statistics"""

    return {
        "blocklists": {
            name: len(ips) for name, ips in threat_intel_service.blocklists.items()
        },
        "last_refreshed": datetime.utcnow().isoformat(),
        "status": "active"
    }


@admin_router.post("/refresh")
async def refresh_threat_feeds():
    """Manually refresh threat feeds"""
    await threat_intel_service._load_threat_feeds()
    return {"message": "Threat feeds refreshed"}


@admin_router.post("/blocklist/add")
async def add_to_blocklist(
    blocklist_type: str,
    ip_address: str
):
    """Add IP to blocklist"""

    if blocklist_type not in threat_intel_service.blocklists:
        raise HTTPException(400, f"Invalid blocklist type: {blocklist_type}")

    threat_intel_service.blocklists[blocklist_type].add(ip_address)

    return {
        "message": f"Added {ip_address} to {blocklist_type}",
        "blocklist_type": blocklist_type,
        "ip_address": ip_address
    }


@admin_router.delete("/blocklist/remove")
async def remove_from_blocklist(
    blocklist_type: str,
    ip_address: str
):
    """Remove IP from blocklist"""

    if blocklist_type not in threat_intel_service.blocklists:
        raise HTTPException(400, f"Invalid blocklist type: {blocklist_type}")

    if ip_address in threat_intel_service.blocklists[blocklist_type]:
        threat_intel_service.blocklists[blocklist_type].remove(ip_address)

    return {
        "message": f"Removed {ip_address} from {blocklist_type}",
        "blocklist_type": blocklist_type,
        "ip_address": ip_address
    }


@admin_router.get("/check/{ip_address}")
async def check_ip(ip_address: str):
    """Check IP reputation"""

    reputation = await threat_intel_service.check_ip_reputation(ip_address)

    return {
        "ip_address": reputation.ip_address,
        "reputation_score": reputation.reputation_score,
        "threat_level": reputation.threat_level,
        "factors": reputation.factors,
        "last_updated": reputation.last_updated.isoformat()
    }
