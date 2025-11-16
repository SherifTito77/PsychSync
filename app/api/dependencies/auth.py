# app/api/dependencies/auth.py
"""
Clean authentication dependencies for FastAPI endpoints
Single source of truth for all authentication logic
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_