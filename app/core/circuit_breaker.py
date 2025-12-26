"""
Circuit Breaker Pattern Implementation

Features:
- Automatic failure detection
- Circuit state management (CLOSED, OPEN, HALF_OPEN)
- Recovery timeout handling
- Performance monitoring
- Integration with external services
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from functools import wraps
import random

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, blocking calls
    HALF_OPEN = "half_open"  # Testing if service has recovered

class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascading failures
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        success_threshold: int = 3,
        monitoring_enabled: bool = True
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying recovery
            expected_exception: Exception type to consider as failure
            success_threshold: Success count needed to close circuit in half-open state
            monitoring_enabled: Enable performance monitoring
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        self.monitoring_enabled = monitoring_enabled

        # Circuit state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0

        # Performance monitoring
        self._call_count = 0
        self._success_count_total = 0
        self._failure_count_total = 0
        self._last_call_time: Optional[float] = None
        self._response_times: List[float] = []

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        start_time = time.time()

        async with self._lock:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info("Circuit breaker entering HALF_OPEN state")
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Next attempt in "
                        f"{self._get_time_until_retry():.1f} seconds"
                    )

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Record success
            async with self._lock:
                await self._on_success()

            return result

        except self.expected_exception as e:
            # Record failure
            async with self._lock:
                await self._on_failure()

            raise

        except Exception as e:
            # Non-expected exceptions are treated as failures but don't count toward threshold
            logger.warning(f"Unexpected exception in circuit breaker: {e}")
            raise

        finally:
            # Record performance metrics
            if self.monitoring_enabled:
                response_time = time.time() - start_time
                await self._record_call_metrics(response_time)

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self._last_failure_time is None:
            return True

        return time.time() - self._last_failure_time >= self.recovery_timeout

    def _get_time_until_retry(self) -> float:
        """Get time until next retry attempt"""
        if self._last_failure_time is None:
            return 0.0

        return max(0.0, self.recovery_timeout - (time.time() - self._last_failure_time))

    async def _on_success(self):
        """Handle successful call"""
        self._call_count += 1
        self._success_count_total += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._close_circuit()

        if self._state == CircuitState.CLOSED:
            self._failure_count = 0

    async def _on_failure(self):
        """Handle failed call"""
        self._call_count += 1
        self._failure_count_total += 1
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._open_circuit()
        elif self._state == CircuitState.HALF_OPEN:
            self._open_circuit()

    def _open_circuit(self):
        """Open the circuit"""
        self._state = CircuitState.OPEN
        logger.warning(
            f"Circuit breaker OPENED after {self._failure_count} failures"
        )

    def _close_circuit(self):
        """Close the circuit"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        logger.info("Circuit breaker CLOSED - service recovered")

    async def _record_call_metrics(self, response_time: float):
        """Record performance metrics"""
        self._last_call_time = time.time()
        self._response_times.append(response_time)

        # Keep only last 100 response times
        if len(self._response_times) > 100:
            self._response_times = self._response_times[-100:]

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count"""
        return self._failure_count

    @property
    def call_count(self) -> int:
        """Get total call count"""
        return self._call_count

    @property
    def success_rate(self) -> float:
        """Get success rate percentage"""
        if self._call_count == 0:
            return 100.0
        return (self._success_count_total / self._call_count) * 100

    @property
    def average_response_time(self) -> Optional[float]:
        """Get average response time"""
        if not self._response_times:
            return None
        return sum(self._response_times) / len(self._response_times)

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics"""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "total_calls": self._call_count,
            "total_successes": self._success_count_total,
            "total_failures": self._failure_count_total,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "last_failure_time": datetime.fromtimestamp(self._last_failure_time).isoformat() if self._last_failure_time else None,
            "time_until_retry": self._get_time_until_retry(),
            "recovery_timeout": self.recovery_timeout
        }

    def reset(self):
        """Reset circuit breaker to initial state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info("Circuit breaker reset to CLOSED state")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """Register a new circuit breaker"""
        if name in self._circuit_breakers:
            raise ValueError(f"Circuit breaker '{name}' already registered")

        circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )

        self._circuit_breakers[name] = circuit_breaker
        logger.info(f"Registered circuit breaker: {name}")
        return circuit_breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self._circuit_breakers.get(name)

    def list_all(self) -> List[str]:
        """List all registered circuit breaker names"""
        return list(self._circuit_breakers.keys())

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers"""
        return {
            name: cb.get_metrics()
            for name, cb in self._circuit_breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self._circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()


# Decorator for circuit breaker protection
def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception
):
    """
    Decorator for circuit breaker protection

    Args:
        name: Circuit breaker name
        failure_threshold: Failure threshold
        recovery_timeout: Recovery timeout in seconds
        expected_exception: Exception type to consider as failure
    """
    def decorator(func):
        # Get or create circuit breaker
        cb = circuit_breaker_registry.get(name)
        if cb is None:
            cb = circuit_breaker_registry.register(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception
            )

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)

        return wrapper
    return decorator


# Circuit breaker for external services
class ServiceCircuitBreaker:
    """Specialized circuit breaker for external services"""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        timeout: float = 10.0
    ):
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout

        # Create circuit breaker
        self.circuit_breaker = circuit_breaker_registry.register(
            name=f"service_{service_name}",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=Exception
        )

    async def call(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """
        Make service call with circuit breaker protection

        Args:
            method: HTTP method
            endpoint: Service endpoint
            **kwargs: Additional arguments for httpx

        Returns:
            Service response
        """
        import httpx

        async def make_call():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}{endpoint}"
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

        return await self.circuit_breaker.call(make_call)

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for this service"""
        return {
            "service_name": self.service_name,
            "base_url": self.base_url,
            "circuit_breaker": self.circuit_breaker.get_metrics()
        }


# Circuit breaker monitoring and health checks
class CircuitBreakerMonitor:
    """Monitor circuit breaker health and performance"""

    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get overall system health based on circuit breakers"""
        metrics = circuit_breaker_registry.get_all_metrics()

        total_circuits = len(metrics)
        open_circuits = sum(
            1 for m in metrics.values()
            if m["state"] == CircuitState.OPEN.value
        )
        half_open_circuits = sum(
            1 for m in metrics.values()
            if m["state"] == CircuitState.HALF_OPEN.value
        )

        # Calculate overall health score
        health_score = 100.0
        if total_circuits > 0:
            open_penalty = (open_circuits / total_circuits) * 50
            half_open_penalty = (half_open_circuits / total_circuits) * 25
            health_score = max(0.0, 100.0 - open_penalty - half_open_penalty)

        return {
            "total_circuits": total_circuits,
            "closed_circuits": total_circuits - open_circuits - half_open_circuits,
            "half_open_circuits": half_open_circuits,
            "open_circuits": open_circuits,
            "health_score": health_score,
            "status": "healthy" if health_score >= 75 else "degraded" if health_score >= 50 else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breakers": metrics
        }

    @staticmethod
    def get_circuits_requiring_attention() -> List[Dict[str, Any]]:
        """Get circuit breakers that need attention"""
        metrics = circuit_breaker_registry.get_all_metrics()
        attention_needed = []

        for name, metric in metrics.items():
            issues = []

            # Check for open circuits
            if metric["state"] == CircuitState.OPEN.value:
                issues.append("Circuit is OPEN")

            # Check for low success rate
            if metric["success_rate"] < 80:
                issues.append(f"Low success rate: {metric['success_rate']:.1f}%")

            # Check for high failure count
            if metric["failure_count"] >= metric["failure_threshold"] * 0.8:
                issues.append(f"High failure count: {metric['failure_count']}")

            # Check for slow response times
            if metric["average_response_time"] and metric["average_response_time"] > 5.0:
                issues.append(f"Slow response time: {metric['average_response_time']:.2f}s")

            if issues:
                attention_needed.append({
                    "name": name,
                    "state": metric["state"],
                    "issues": issues,
                    "metrics": metric
                })

        return attention_needed


# Global circuit breaker monitor
circuit_breaker_monitor = CircuitBreakerMonitor()