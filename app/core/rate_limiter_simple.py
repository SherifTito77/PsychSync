# app/core/rate_limiter_simple.py
import time
from typing import Optional


class SimpleUnifiedRateLimiter:
    """Simple in-memory rate limiter for components that don't need Redis."""

    def __init__(self, requests: int = 10, window: int = 60):
        self.requests = requests
        self.window = window
        self.history = []

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self.history = [t for t in self.history if t > now - self.window]
        if len(self.history) < self.requests:
            self.history.append(now)
            return True
        return False
