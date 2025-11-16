# app/services/team_dynamics_service.py
"""
Team Dynamics Analysis and Optimization Service
Analyzes team interaction patterns, collaboration effectiveness, and provides optimization recommendations
"""

import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_