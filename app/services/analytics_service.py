
#app/services/Analytics_services.py
"""
Analytics Service for PsychSync

Provides:
- Team performance analytics
- Wellness trend analysis
- Predictive insights using AI engine
- Compatibility analysis
- Role optimization recommendations
- Assessment analytics
- User analytics
- Team analytics
- System analytics
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_