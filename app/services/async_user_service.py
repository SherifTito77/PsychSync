# app/services/async_user_service.py
"""
Async User Service with Redis caching implementation
Handles all user-related business logic with performance optimization
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select, func, and_, or_