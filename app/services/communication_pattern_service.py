# app/services/communication_pattern_service.py
"""
Communication Pattern Analysis Service
Identifies patterns, trends, and behavioral insights from email communication metadata
"""

import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_