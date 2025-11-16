# app/services/wellness_monitoring_service.py
"""
Employee Wellness and Burnout Prevention Service
Monitors psychological wellness, detects burnout risk factors, and provides proactive interventions
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_