# app/services/assessment_integration_service.py
"""
Assessment Integration Service
Integrates email-based behavioral analysis with existing psychological assessment framework
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_