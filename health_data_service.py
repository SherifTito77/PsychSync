"""
Health Data Integration Service
Backend API for wearable device integration and health data processing
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import asyncio
import aiohttp
import logging

# Database Models
Base = declarative_base()

class HealthDevice(Base):
    __tablename__ = "health_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    device_type = Column(String, index=True)
    device_name = Column(String)
    device_id = Column(String, unique=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    is_connected = Column(Boolean, default=True)
    capabilities = Column(JSON)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="health_devices")
    health_data = relationship("HealthDataPoint", back_populates="device")

class HealthDataPoint(Base):
    __tablename__ = "health_data_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    device_id = Column(Integer, ForeignKey("health_devices.id"), index=True)
    metric_type = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    timestamp = Column(DateTime, index=True)
    source_data = Column(JSON)
    quality_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="health_data")
    device = relationship("HealthDevice", back_populates="health_data")

# Pydantic Models
class DeviceConnectRequest(BaseModel):
    device_type: str
    authorization_code: Optional[str] = None
    access_token: Optional[str] = None
    device_id: Optional[str] = None

class DeviceConnectResponse(BaseModel):
    success: bool
    device_id: Optional[int] = None
    message: str

class HealthDataPointCreate(BaseModel):
    metric_type: str
    value: float
    unit: str
    timestamp: datetime
    source_data: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = 1.0

class HealthDataSummary(BaseModel):
    user_id: int
    time_range: str
    metrics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    wellness_score: float
    trend: float

# Device Adapters
class DeviceAdapter:
    def __init__(self, device_type: str):
        self.device_type = device_type
        self.logger = logging.getLogger(f"health_adapter.{device_type}")

    async def connect(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to device/service and return access tokens"""
        raise NotImplementedError

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        raise NotImplementedError

    async def fetch_data(self, access_token: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Fetch historical data from device"""
        raise NotImplementedError

    async def setup_webhook(self, access_token: str, webhook_url: str) -> bool:
        """Setup webhook for real-time data"""
        raise NotImplementedError

    def normalize_data(self, raw_data: List[Dict]) -> List[HealthDataPointCreate]:
        """Normalize device-specific data to standard format"""
        raise NotImplementedError

class AppleHealthAdapter(DeviceAdapter):
    def __init__(self):
        super().__init__("apple_health")

    async def connect(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        # Apple HealthKit integration would use iOS HealthKit framework
        # This is a simplified implementation
        return {
            "access_token": "mock_apple_token",
            "refresh_token": "mock_refresh_token",
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "device_id": credentials.get("device_id", "apple_device_1")
        }

    async def fetch_data(self, access_token: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock Apple Health data
        mock_data = []
        current_date = start_date

        while current_date <= end_date:
            mock_data.extend([
                {
                    "metric_type": "steps",
                    "value": 8000 + (hash(str(current_date)) % 4000),
                    "unit": "count",
                    "timestamp": current_date + timedelta(hours=12),
                    "source": "apple_health"
                },
                {
                    "metric_type": "heart_rate",
                    "value": 60 + (hash(f"hr_{current_date}") % 40),
                    "unit": "bpm",
                    "timestamp": current_date + timedelta(hours=14),
                    "source": "apple_health"
                },
                {
                    "metric_type": "sleep_duration",
                    "value": 6.5 + (hash(f"sleep_{current_date}") % 3),
                    "unit": "hours",
                    "timestamp": current_date + timedelta(hours=7),
                    "source": "apple_health"
                }
            ])
            current_date += timedelta(days=1)

        return mock_data

    def normalize_data(self, raw_data: List[Dict]) -> List[HealthDataPointCreate]:
        normalized = []
        for point in raw_data:
            normalized.append(HealthDataPointCreate(
                metric_type=point["metric_type"],
                value=point["value"],
                unit=point["unit"],
                timestamp=point["timestamp"],
                source_data={"source": point.get("source", "unknown")}
            ))
        return normalized

class FitbitAdapter(DeviceAdapter):
    def __init__(self):
        super().__init__("fitbit")
        self.api_base = "https://api.fitbit.com/1/user"

    async def connect(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        auth_code = credentials.get("authorization_code")
        if not auth_code:
            raise ValueError("Authorization code required for Fitbit")

        # Exchange auth code for access token
        token_url = "https://api.fitbit.com/oauth2/token"
        token_data = {
            "client_id": "your_fitbit_client_id",
            "grant_type": "authorization_code",
            "redirect_uri": "your_redirect_uri",
            "code": auth_code
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=token_data) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail="Fitbit token exchange failed")

                token_response = await response.json()
                return {
                    "access_token": token_response["access_token"],
                    "refresh_token": token_response["refresh_token"],
                    "expires_at": datetime.utcnow() + timedelta(seconds=token_response["expires_in"]),
                    "device_id": f"fitbit_{token_response.get('user_id', 'unknown')}"
                }

    async def fetch_data(self, access_token: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        headers = {"Authorization": f"Bearer {access_token}"}
        data = []

        # Fetch steps data
        steps_url = f"{self.api_base}/-/activities/steps/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"

        async with aiohttp.ClientSession() as session:
            async with session.get(steps_url, headers=headers) as response:
                if response.status == 200:
                    steps_data = await response.json()
                    for date_str, daily_steps in steps_data["activities-steps"].items():
                        data.append({
                            "metric_type": "steps",
                            "value": int(daily_steps["value"]),
                            "unit": "count",
                            "timestamp": datetime.strptime(date_str, "%Y-%m-%d") + timedelta(hours=12),
                            "source": "fitbit"
                        })

        # Fetch heart rate data
        hr_url = f"{self.api_base}/-/activities/heart/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"

        async with session.get(hr_url, headers=headers) as response:
            if response.status == 200:
                hr_data = await response.json()
                for date_str, daily_hr in hr_data["activities-heart"].items():
                    if "restingHeartRate" in daily_hr:
                        data.append({
                            "metric_type": "resting_heart_rate",
                            "value": daily_hr["restingHeartRate"],
                            "unit": "bpm",
                            "timestamp": datetime.strptime(date_str, "%Y-%m-%d") + timedelta(hours=7),
                            "source": "fitbit"
                        })

        return data

    def normalize_data(self, raw_data: List[Dict]) -> List[HealthDataPointCreate]:
        normalized = []
        for point in raw_data:
            normalized.append(HealthDataPointCreate(
                metric_type=point["metric_type"],
                value=point["value"],
                unit=point["unit"],
                timestamp=point["timestamp"],
                source_data={"source": point.get("source", "fitbit")}
            ))
        return normalized

class GarminAdapter(DeviceAdapter):
    def __init__(self):
        super().__init__("garmin")

    async def connect(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        # Garmin Connect API integration
        return {
            "access_token": "mock_garmin_token",
            "refresh_token": "mock_garmin_refresh",
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "device_id": f"garmin_{credentials.get('device_id', '1')}"
        }

    async def fetch_data(self, access_token: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock Garmin data with focus on fitness metrics
        mock_data = []
        current_date = start_date

        while current_date <= end_date:
            mock_data.extend([
                {
                    "metric_type": "steps",
                    "value": 10000 + (hash(str(current_date)) % 5000),
                    "unit": "count",
                    "timestamp": current_date + timedelta(hours=12),
                    "source": "garmin"
                },
                {
                    "metric_type": "body_battery",
                    "value": 50 + (hash(f"bb_{current_date}") % 50),
                    "unit": "percent",
                    "timestamp": current_date + timedelta(hours=7),
                    "source": "garmin"
                },
                {
                    "metric_type": "training_load",
                    "value": 30 + (hash(f"tl_{current_date}") % 40),
                    "unit": "score",
                    "timestamp": current_date + timedelta(hours=20),
                    "source": "garmin"
                }
            ])
            current_date += timedelta(days=1)

        return mock_data

    def normalize_data(self, raw_data: List[Dict]) -> List[HealthDataPointCreate]:
        normalized = []
        for point in raw_data:
            normalized.append(HealthDataPointCreate(
                metric_type=point["metric_type"],
                value=point["value"],
                unit=point["unit"],
                timestamp=point["timestamp"],
                source_data={"source": point.get("source", "garmin")}
            ))
        return normalized

class HealthDataService:
    def __init__(self, db: Session):
        self.db = db
        self.adapters = {
            "apple_health": AppleHealthAdapter(),
            "fitbit": FitbitAdapter(),
            "garmin": GarminAdapter(),
            # Add more adapters as needed
        }
        self.logger = logging.getLogger("health_data_service")

    async def connect_device(self, user_id: int, device_connect: DeviceConnectRequest) -> DeviceConnectResponse:
        """Connect a new health device for user"""
        try:
            adapter = self.adapters.get(device_connect.device_type)
            if not adapter:
                return DeviceConnectResponse(
                    success=False,
                    message=f"Unsupported device type: {device_connect.device_type}"
                )

            # Connect to device/service
            credentials = {
                "authorization_code": device_connect.authorization_code,
                "access_token": device_connect.access_token,
                "device_id": device_connect.device_id
            }

            connection_data = await adapter.connect(credentials)

            # Create device record
            device = HealthDevice(
                user_id=user_id,
                device_type=device_connect.device_type,
                device_name=device_connect.device_type.replace("_", " ").title(),
                device_id=connection_data["device_id"],
                access_token=connection_data["access_token"],
                refresh_token=connection_data.get("refresh_token"),
                token_expires_at=connection_data["expires_at"],
                is_connected=True,
                capabilities=["steps", "heart_rate", "sleep"]  # Device-specific capabilities
            )

            self.db.add(device)
            self.db.commit()
            self.db.refresh(device)

            # Initial data sync
            await self.sync_device_data(device.id)

            return DeviceConnectResponse(
                success=True,
                device_id=device.id,
                message="Device connected successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to connect device {device_connect.device_type}: {str(e)}")
            return DeviceConnectResponse(
                success=False,
                message=f"Connection failed: {str(e)}"
            )

    async def sync_device_data(self, device_id: int) -> bool:
        """Sync data from connected device"""
        try:
            device = self.db.query(HealthDevice).filter(HealthDevice.id == device_id).first()
            if not device or not device.is_connected:
                return False

            adapter = self.adapters.get(device.device_type)
            if not adapter:
                return False

            # Check if token needs refresh
            if device.token_expires_at and device.token_expires_at <= datetime.utcnow():
                if device.refresh_token:
                    token_data = await adapter.refresh_token(device.refresh_token)
                    device.access_token = token_data["access_token"]
                    device.token_expires_at = token_data["expires_at"]
                    self.db.commit()
                else:
                    device.is_connected = False
                    self.db.commit()
                    return False

            # Fetch data from last sync or last 30 days
            start_date = device.last_sync or (datetime.utcnow() - timedelta(days=30))
            end_date = datetime.utcnow()

            raw_data = await adapter.fetch_data(device.access_token, start_date, end_date)
            normalized_data = adapter.normalize_data(raw_data)

            # Store data points
            for data_point in normalized_data:
                existing_point = self.db.query(HealthDataPoint).filter(
                    HealthDataPoint.user_id == device.user_id,
                    HealthDataPoint.metric_type == data_point.metric_type,
                    HealthDataPoint.timestamp == data_point.timestamp
                ).first()

                if not existing_point:
                    db_point = HealthDataPoint(
                        user_id=device.user_id,
                        device_id=device.id,
                        metric_type=data_point.metric_type,
                        value=data_point.value,
                        unit=data_point.unit,
                        timestamp=data_point.timestamp,
                        source_data=data_point.source_data or {},
                        quality_score=data_point.quality_score
                    )
                    self.db.add(db_point)

            # Update last sync time
            device.last_sync = datetime.utcnow()
            self.db.commit()

            self.logger.info(f"Synced {len(normalized_data)} data points for device {device_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync device {device_id}: {str(e)}")
            return False

    async def get_health_summary(self, user_id: int, time_range: str = "7days") -> HealthDataSummary:
        """Get comprehensive health summary for user"""
        # Calculate date range
        if time_range == "7days":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif time_range == "30days":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif time_range == "90days":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=7)

        # Fetch health data points
        data_points = self.db.query(HealthDataPoint).filter(
            HealthDataPoint.user_id == user_id,
            HealthDataPoint.timestamp >= start_date
        ).order_by(HealthDataPoint.timestamp.desc()).all()

        # Calculate metrics
        metrics = {}
        metric_types = set(point.metric_type for point in data_points)

        for metric_type in metric_types:
            metric_data = [p for p in data_points if p.metric_type == metric_type]
            if metric_data:
                values = [p.value for p in metric_data]
                metrics[metric_type] = {
                    "current": values[0] if values else 0,
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                    "unit": metric_data[0].unit
                }

        # Generate insights
        insights = await self.generate_insights(metrics, data_points)

        # Calculate wellness score
        wellness_score = await self.calculate_wellness_score(metrics)

        # Calculate trend
        trend = await self.calculate_trend(user_id, start_date)

        return HealthDataSummary(
            user_id=user_id,
            time_range=time_range,
            metrics=metrics,
            insights=insights,
            wellness_score=wellness_score,
            trend=trend
        )

    async def generate_insights(self, metrics: Dict[str, Any], data_points: List[HealthDataPoint]) -> List[Dict[str, Any]]:
        """Generate health insights based on metrics"""
        insights = []

        # Steps insight
        if "steps" in metrics:
            steps_avg = metrics["steps"]["average"]
            if steps_avg < 5000:
                insights.append({
                    "type": "activity",
                    "level": "warning",
                    "title": "Low Activity Level",
                    "message": f"Your average daily steps are {steps_avg:.0f}.",
                    "recommendation": "Aim for at least 7,000 steps per day for better health."
                })

        # Heart rate insight
        if "resting_heart_rate" in metrics:
            rhr = metrics["resting_heart_rate"]["average"]
            if rhr > 80:
                insights.append({
                    "type": "cardio",
                    "level": "info",
                    "title": "Elevated Resting Heart Rate",
                    "message": f"Your average resting heart rate is {rhr:.0f} bpm.",
                    "recommendation": "Consider stress management and regular exercise."
                })

        # Sleep insight
        if "sleep_duration" in metrics:
            sleep_avg = metrics["sleep_duration"]["average"]
            if sleep_avg < 7:
                insights.append({
                    "type": "sleep",
                    "level": "warning",
                    "title": "Insufficient Sleep",
                    "message": f"You're averaging {sleep_avg:.1f} hours of sleep per night.",
                    "recommendation": "Aim for 7-9 hours of sleep for optimal recovery."
                })

        return insights

    async def calculate_wellness_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall wellness score"""
        score = 0
        total_weight = 0

        # Define goals and weights for different metrics
        metric_goals = {
            "steps": {"goal": 10000, "weight": 0.2},
            "resting_heart_rate": {"goal": 70, "weight": 0.15, "inverse": True},
            "sleep_duration": {"goal": 8, "weight": 0.25},
            "body_battery": {"goal": 80, "weight": 0.2},
        }

        for metric_type, config in metric_goals.items():
            if metric_type in metrics:
                current = metrics[metric_type]["average"]
                goal = config["goal"]

                if config.get("inverse"):
                    # For metrics where lower is better (like resting heart rate)
                    achievement = min(goal / current, 1) if current > 0 else 1
                else:
                    achievement = min(current / goal, 1)

                score += achievement * config["weight"]
                total_weight += config["weight"]

        return (score / total_weight * 100) if total_weight > 0 else 0

    async def calculate_trend(self, user_id: int, start_date: datetime) -> float:
        """Calculate health trend over time period"""
        # Compare first half vs second half of time period
        mid_point = start_date + (datetime.utcnow() - start_date) / 2

        first_half = self.db.query(HealthDataPoint).filter(
            HealthDataPoint.user_id == user_id,
            HealthDataPoint.timestamp >= start_date,
            HealthDataPoint.timestamp < mid_point
        ).all()

        second_half = self.db.query(HealthDataPoint).filter(
            HealthDataPoint.user_id == user_id,
            HealthDataPoint.timestamp >= mid_point
        ).all()

        # Calculate simple trend based on step count
        first_half_steps = sum(p.value for p in first_half if p.metric_type == "steps")
        second_half_steps = sum(p.value for p in second_half if p.metric_type == "steps")

        if first_half_steps > 0:
            trend = ((second_half_steps - first_half_steps) / first_half_steps) * 100
            return round(trend, 1)

        return 0.0

# API Routes
router = APIRouter(prefix="/api/health-data", tags=["health-data"])

@router.post("/connect/{user_id}")
async def connect_health_device(
    user_id: int,
    device_connect: DeviceConnectRequest,
    db: Session = Depends(get_db)
):
    """Connect a new health device"""
    service = HealthDataService(db)
    result = await service.connect_device(user_id, device_connect)
    return result

@router.post("/sync/{device_id}")
async def sync_device_data(
    device_id: int,
    db: Session = Depends(get_db)
):
    """Sync data from connected device"""
    service = HealthDataService(db)
    success = await service.sync_device_data(device_id)
    return {"success": success, "message": "Sync completed" if success else "Sync failed"}

@router.get("/summary/{user_id}")
async def get_health_summary(
    user_id: int,
    time_range: str = "7days",
    db: Session = Depends(get_db)
):
    """Get health data summary"""
    service = HealthDataService(db)
    summary = await service.get_health_summary(user_id, time_range)
    return summary

@router.get("/connections/{user_id}")
async def get_connected_devices(user_id: int, db: Session = Depends(get_db)):
    """Get list of connected devices"""
    devices = db.query(HealthDevice).filter(HealthDevice.user_id == user_id).all()
    return {
        "devices": [
            {
                "id": device.id,
                "type": device.device_type,
                "name": device.device_name,
                "connected": device.is_connected,
                "last_sync": device.last_sync,
                "capabilities": device.capabilities
            }
            for device in devices
        ]
    }

@router.delete("/disconnect/{user_id}/{device_id}")
async def disconnect_device(
    user_id: int,
    device_id: int,
    db: Session = Depends(get_db)
):
    """Disconnect health device"""
    device = db.query(HealthDevice).filter(
        HealthDevice.id == device_id,
        HealthDevice.user_id == user_id
    ).first()

    if device:
        device.is_connected = False
        db.commit()
        return {"success": True, "message": "Device disconnected"}

    raise HTTPException(status_code=404, detail="Device not found")
