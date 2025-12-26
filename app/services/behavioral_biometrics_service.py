"""
Behavioral Biometrics Service - Advanced Anomaly Detection

Implements user behavior analysis to detect suspicious activities indicative of:
- Account takeover attempts
- Automated bot attacks
- Unusual access patterns
- Session hijacking attempts

Author: Security Team
Date: 2025-12-24
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, status
from pydantic import BaseModel

from app.db.models.user import User
from app.core.database import get_db


# =============================================================================
# Data Models
# =============================================================================

class BehavioralMetrics(BaseModel):
    """Real-time behavioral metrics"""
    ip_address: str
    user_agent: str
    accept_language: str
    accept_encoding: str
    screen_resolution: Optional[str] = None
    timezone_offset: Optional[int] = None
    keystroke_dynamics: Optional[Dict] = None
    mouse_movement: Optional[Dict] = None
    session_duration: Optional[float] = None
    navigation_pattern: Optional[List[str]] = None


class RiskScore(BaseModel):
    """Risk assessment result"""
    score: float  # 0.0 to 100.0
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[str]
    recommended_action: str


class AnomalyEvent(BaseModel):
    """Detected anomaly event"""
    event_type: str
    severity: str
    description: str
    confidence: float
    detected_at: datetime
    indicators: Dict


# =============================================================================
# Behavioral Biometrics Service
# =============================================================================

class BehavioralBiometricsService:
    """
    Advanced behavioral analysis for security

    Tracks and analyzes:
    1. Device fingerprinting
    2. Location patterns
    3. Timing patterns
    4. Navigation patterns
    5. Keystroke dynamics
    6. Mouse movement patterns
    7. Session behavior
    """

    def __init__(self):
        self.redis_client = None  # For fast pattern lookup
        self.risk_thresholds = {
            'LOW': 20,
            'MEDIUM': 50,
            'HIGH': 75,
            'CRITICAL': 90
        }

    async def analyze_request(
        self,
        request: Request,
        user_id: Optional[int],
        db: Session
    ) -> RiskScore:
        """
        Analyze incoming request for anomalous behavior

        Returns risk score and recommended actions
        """

        risk_factors = []
        risk_score = 0.0

        # Extract metrics
        metrics = self._extract_metrics(request)

        # Check 1: Device fingerprint consistency
        device_risk = await self._check_device_fingerprint(user_id, metrics, db)
        if device_risk['score'] > 0:
            risk_score += device_risk['score']
            risk_factors.extend(device_risk['factors'])

        # Check 2: Geographic location anomalies
        location_risk = await self._check_location_anomalies(user_id, metrics.ip_address, db)
        if location_risk['score'] > 0:
            risk_score += location_risk['score']
            risk_factors.extend(location_risk['factors'])

        # Check 3: Time-based anomalies
        time_risk = await self._check_time_patterns(user_id, db)
        if time_risk['score'] > 0:
            risk_score += time_risk['score']
            risk_factors.extend(time_risk['factors'])

        # Check 4: Velocity checks (rapid actions)
        velocity_risk = await self._check_velocity(user_id, metrics.ip_address, db)
        if velocity_risk['score'] > 0:
            risk_score += velocity_risk['score']
            risk_factors.extend(velocity_risk['factors'])

        # Check 5: Bot detection
        bot_risk = await self._detect_bot(metrics)
        if bot_risk['score'] > 0:
            risk_score += bot_risk['score']
            risk_factors.extend(bot_risk['factors'])

        # Normalize score to 0-100
        risk_score = min(risk_score, 100.0)

        # Determine risk level
        if risk_score >= self.risk_thresholds['CRITICAL']:
            level = 'CRITICAL'
            action = 'Block request and require re-authentication with MFA'
        elif risk_score >= self.risk_thresholds['HIGH']:
            level = 'HIGH'
            action = 'Require additional verification (SMS, email, security question)'
        elif risk_score >= self.risk_thresholds['MEDIUM']:
            level = 'MEDIUM'
            action = 'Show security warning and monitor session'
        else:
            level = 'LOW'
            action = 'Allow request with normal processing'

        # Log high-risk events
        if level in ['HIGH', 'CRITICAL']:
            await self._log_security_event(
                user_id=user_id,
                event_type=f'behavioral_risk_{level.lower()}',
                risk_score=risk_score,
                factors=risk_factors,
                metrics=metrics.dict()
            )

        return RiskScore(
            score=risk_score,
            level=level,
            factors=risk_factors,
            recommended_action=action
        )

    def _extract_metrics(self, request: Request) -> BehavioralMetrics:
        """Extract behavioral metrics from request"""
        return BehavioralMetrics(
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            accept_language=request.headers.get("accept-language", ""),
            accept_encoding=request.headers.get("accept-encoding", ""),
            screen_resolution=request.headers.get("x-screen-resolution"),
            timezone_offset=request.headers.get("x-timezone-offset"),
        )

    async def _check_device_fingerprint(
        self,
        user_id: Optional[int],
        metrics: BehavioralMetrics,
        db: Session
    ) -> Dict:
        """
        Check if device fingerprint matches known devices

        Returns risk score and factors
        """
        if not user_id:
            return {'score': 0, 'factors': []}

        # Generate device fingerprint
        fingerprint = self._generate_device_fingerprint(metrics)

        # Get known devices for user
        known_devices = await self._get_user_devices(user_id, db)

        # Check if this is a known device
        if fingerprint in [d['fingerprint'] for d in known_devices]:
            # Known device - low risk
            return {'score': 0, 'factors': []}
        else:
            # Unknown device - moderate risk
            return {
                'score': 15,
                'factors': [f'Access from unrecognized device (fingerprint: {fingerprint[:8]}...)']
            }

    async def _check_location_anomalies(
        self,
        user_id: Optional[int],
        ip_address: str,
        db: Session
    ) -> Dict:
        """
        Check for geographic location anomalies

        Detects:
        - Impossible travel (two locations too far apart in short time)
        - Access from high-risk countries
        - Tor exit nodes
        - Known proxy/VPN services
        """
        if not user_id:
            return {'score': 0, 'factors': []}

        risk_score = 0
        factors = []

        # Get location from IP
        location = await self._geolocate_ip(ip_address)

        # Get recent login locations
        recent_locations = await self._get_recent_locations(user_id, hours=24, db=db)

        for recent_loc in recent_locations:
            # Check for impossible travel
            distance = self._calculate_distance(location, recent_loc)
            time_diff = (datetime.utcnow() - recent_loc['timestamp']).total_seconds()

            # Impossible: > 500km in < 30 minutes
            if distance > 500 and time_diff < 1800:
                risk_score += 40
                factors.append(f'Impossible travel detected: {distance:.0f}km in {int(time_diff/60)} minutes')

            # Suspicious: > 1000km in < 2 hours
            if distance > 1000 and time_diff < 7200:
                risk_score += 25
                factors.append(f'Rapid long-distance travel: {distance:.0f}km in {int(time_diff/60)} minutes')

        # Check for high-risk location
        if await self._is_high_risk_location(location):
            risk_score += 20
            factors.append(f'Access from high-risk location: {location["country"]}')

        # Check if Tor exit node
        if await self._is_tor_exit_node(ip_address):
            risk_score += 30
            factors.append('Access from Tor exit node')

        # Check if known proxy/VPN
        if await self._is_proxy_or_vpn(ip_address):
            risk_score += 15
            factors.append('Access from proxy/VPN service')

        return {'score': risk_score, 'factors': factors}

    async def _check_time_patterns(
        self,
        user_id: Optional[int],
        db: Session
    ) -> Dict:
        """
        Check for unusual time patterns

        Detects:
        - Access outside normal hours
        - Access at unusual times for this user
        """
        if not user_id:
            return {'score': 0, 'factors': []}

        risk_score = 0
        factors = []

        # Get user's typical access hours
        typical_hours = await self._get_user_typical_hours(user_id, db)

        current_hour = datetime.utcnow().hour

        # Check if access is outside typical hours
        if typical_hours and current_hour not in typical_hours:
            # But allow some flexibility
            if current_hour not in range(typical_hours[0] - 2, typical_hours[-1] + 3):
                risk_score += 10
                factors.append(f'Access outside typical hours (current: {current_hour}, typical: {typical_hours})')

        return {'score': risk_score, 'factors': factors}

    async def _check_velocity(
        self,
        user_id: Optional[int],
        ip_address: str,
        db: Session
    ) -> Dict:
        """
        Check velocity of requests (rapid automated activity)

        Detects:
        - Too many requests in short time
        - Requests from multiple IPs rapidly
        - Actions faster than humanly possible
        """
        if not user_id:
            return {'score': 0, 'factors': []}

        risk_score = 0
        factors = []

        # Check request rate
        recent_requests = await self._get_recent_requests(user_id, minutes=1, db=db)

        if len(recent_requests) > 30:
            risk_score += 35
            factors.append(f'Very high request rate: {len(recent_requests)} requests/minute')
        elif len(recent_requests) > 10:
            risk_score += 15
            factors.append(f'Elevated request rate: {len(recent_requests)} requests/minute')

        # Check for multiple IPs
        unique_ips = set(r['ip_address'] for r in recent_requests)
        if len(unique_ips) > 3:
            risk_score += 20
            factors.append(f'Multiple IPs in short time: {len(unique_ips)} different IPs')

        # Check for actions faster than human
        if len(recent_requests) > 5:
            # Calculate minimum time between requests
            timestamps = [r['timestamp'] for r in recent_requests]
            timestamps.sort()
            min_diff = min((timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1))

            if min_diff < 0.5:  # Less than 500ms between requests
                risk_score += 25
                factors.append('Requests faster than humanly possible (< 500ms apart)')

        return {'score': risk_score, 'factors': factors}

    async def _detect_bot(self, metrics: BehavioralMetrics) -> Dict:
        """
        Detect automated bots

        Checks:
        - User agent patterns
        - Header inconsistencies
        - Missing JavaScript capabilities
        """
        risk_score = 0
        factors = []

        user_agent = metrics.user_agent.lower()

        # Known bot user agents
        bot_patterns = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python']
        if any(pattern in user_agent for pattern in bot_patterns):
            risk_score += 50
            factors.append(f'Suspicious user agent: {metrics.user_agent}')

        # Missing common browser headers
        if not metrics.accept_language:
            risk_score += 15
            factors.append('Missing Accept-Language header')

        # Check for empty or suspicious user agent
        if not metrics.user_agent or metrics.user_agent in ['-', '']:
            risk_score += 20
            factors.append('Empty or missing User-Agent')

        return {'score': risk_score, 'factors': factors}

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _generate_device_fingerprint(self, metrics: BehavioralMetrics) -> str:
        """Generate unique device fingerprint"""
        fingerprint_data = {
            'user_agent': metrics.user_agent,
            'accept_language': metrics.accept_language,
            'accept_encoding': metrics.accept_encoding,
            'screen_resolution': metrics.screen_resolution,
            'timezone_offset': metrics.timezone_offset,
        }

        # Hash to create fingerprint
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    async def _geolocate_ip(self, ip_address: str) -> Dict:
        """
        Get geographic location from IP address

        In production, use a service like:
        - MaxMind GeoIP2
        - IPInfo.io
        - Abstract API
        """
        # Simplified implementation
        # In production, integrate with real geolocation service
        return {
            'country': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0
        }

    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """Calculate distance between two locations in kilometers"""
        # Haversine formula
        lat1, lon1 = loc1['latitude'], loc1['longitude']
        lat2, lon2 = loc2['latitude'], loc2['longitude']

        from math import radians, cos, sin, asin, sqrt

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        km = 6371 * c
        return km

    async def _is_high_risk_location(self, location: Dict) -> bool:
        """Check if location is high-risk"""
        # List of high-risk countries (example)
        high_risk_countries = [
            'KP',  # North Korea
            'IR',  # Iran
            'CU',  # Cuba
            'SY',  # Syria
            'SD',  # Sudan
        ]

        return location.get('country', '') in high_risk_countries

    async def _is_tor_exit_node(self, ip_address: str) -> bool:
        """Check if IP is a Tor exit node"""
        # In production, use a service like:
        # - Tor Project's exit node list
        # - AbuseIPDB
        # - IPQualityScore
        return False

    async def _is_proxy_or_vpn(self, ip_address: str) -> bool:
        """Check if IP is a proxy or VPN"""
        # In production, use a service like:
        # - IPQualityScore
        # - ProxyCheck
        # - Abstract API
        return False

    async def _get_user_devices(self, user_id: int, db: Session) -> List[Dict]:
        """Get known devices for user"""
        # Query from database
        # In production, store device fingerprints in user_devices table
        return []

    async def _get_recent_locations(self, user_id: int, hours: int, db: Session) -> List[Dict]:
        """Get recent login locations for user"""
        # Query from database
        # In production, query login_history table
        return []

    async def _get_user_typical_hours(self, user_id: int, db: Session) -> Optional[List[int]]:
        """Get user's typical access hours"""
        # Analyze login history
        # In production, calculate from historical data
        return None

    async def _get_recent_requests(self, user_id: int, minutes: int, db: Session) -> List[Dict]:
        """Get recent requests for user"""
        # Query from database or Redis
        # In production, store request logs
        return []

    async def _log_security_event(self, user_id: Optional[int], event_type: str, **kwargs):
        """Log security event"""
        # In production, send to monitoring system
        print(f"[SECURITY BEHAVIORAL] {event_type}: {kwargs}")


# =============================================================================
# FastAPI Integration
# =============================================================================

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/security/behavioral", tags=["Behavioral Security"])

behavioral_service = BehavioralBiometricsService()


@router.post("/analyze")
async def analyze_behavior(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Analyze request for anomalous behavior

    Returns risk score and recommended actions
    """
    # Get user from session (if authenticated)
    user_id = getattr(request.state, 'user_id', None)

    # Analyze behavior
    risk_score = await behavioral_service.analyze_request(request, user_id, db)

    # Take action based on risk
    if risk_score.level == 'CRITICAL':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unusual activity detected. Please verify your identity."
        )

    return risk_score


@router.post("/metrics/collect")
async def collect_behavioral_metrics(
    metrics: BehavioralMetrics,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Collect behavioral metrics for analysis

    Called from frontend to track user behavior patterns
    """
    user_id = getattr(request.state, 'user_id', None)

    # Store metrics for analysis
    # In production, store in behavioral_metrics table

    return {"message": "Metrics collected"}
