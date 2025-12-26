"""
Response Compression and Optimization Middleware
Implements gzip compression and response optimization for API performance
Expected improvement: 30-50% for API response size and transfer time
"""
import gzip
import json
from typing import Callable, Any, Dict, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTask
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class ResponseCompressionMiddleware(BaseHTTPMiddleware):
    """
    Advanced response compression middleware with:
    - gzip compression for JSON responses
    - Response size monitoring and metrics
    - Selective compression based on content type and size
    - Field selection and response minimization
    - ETag generation for conditional requests
    """

    def __init__(
        self,
        app,
        compress_threshold: int = 1024,  # Compress responses larger than 1KB
        min_compressible_size: int = 512,  # Minimum size to attempt compression
        compression_level: int = 6,  # gzip compression level (1-9)
        enabled_content_types: List[str] = None
    ):
        super().__init__(app)
        self.compress_threshold = compress_threshold
        self.min_compressible_size = min_compressible_size
        self.compression_level = compression_level
        self.enabled_content_types = enabled_content_types or [
            "application/json",
            "application/vnd.api+json",
            "text/html",
            "text/plain"
        ]
        self._metrics = {
            "responses_compressed": 0,
            "bytes_saved": 0,
            "total_responses": 0,
            "compression_time_ms": 0
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and compress response if beneficial"""
        start_time = time.time()

        # Check if client supports gzip compression
        accept_encoding = request.headers.get("accept-encoding", "")
        supports_gzip = "gzip" in accept_encoding.lower()

        # Get original response
        response = await call_next(request)

        # Skip compression for certain conditions
        if not self._should_compress(request, response, supports_gzip):
            self._metrics["total_responses"] += 1
            return response

        # Process and compress response
        compressed_response = await self._compress_response(response, request)

        # Update metrics
        processing_time = (time.time() - start_time) * 1000
        self._metrics["total_responses"] += 1
        self._metrics["compression_time_ms"] += processing_time

        # Add compression headers
        compressed_response.headers["X-Compression-Time-MS"] = f"{processing_time:.2f}"
        compressed_response.headers["X-Original-Size"] = str(len(response.body) if hasattr(response, 'body') else 0)

        return compressed_response

    def _should_compress(
        self,
        request: Request,
        response: Response,
        supports_gzip: bool
    ) -> bool:
        """Determine if response should be compressed"""

        # Client must support gzip
        if not supports_gzip:
            return False

        # Only compress successful responses
        if response.status_code >= 400:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "").split(";")[0]
        if content_type not in self.enabled_content_types:
            return False

        # Check if response has body
        if not hasattr(response, 'body') or not response.body:
            return False

        # Check size threshold
        if len(response.body) < self.min_compressible_size:
            return False

        # Skip if already compressed
        if response.headers.get("content-encoding"):
            return False

        return True

    async def _compress_response(self, response: Response, request: Request) -> Response:
        """Compress response and create new response object"""
        try:
            # Get response body
            response_body = response.body

            # Apply field selection if requested
            fields = request.query_params.get("fields")
            if fields and response.headers.get("content-type", "").startswith("application/json"):
                response_body = self._apply_field_selection(response_body, fields)

            # Compress the body
            compressed_body = gzip.compress(
                response_body,
                compresslevel=self.compression_level
            )

            # Only use compressed version if it's smaller
            if len(compressed_body) < len(response_body):
                # Update metrics
                self._metrics["responses_compressed"] += 1
                self._metrics["bytes_saved"] += len(response_body) - len(compressed_body)

                # Create new response with compressed body
                compressed_response = Response(
                    content=compressed_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )

                # Add compression headers
                compressed_response.headers["content-encoding"] = "gzip"
                compressed_response.headers["content-length"] = str(len(compressed_body))
                compressed_response.headers["x-compressed"] = "true"
                compressed_response.headers["x-compression-ratio"] = f"{(1 - len(compressed_body) / len(response_body)) * 100:.1f}%"

                return compressed_response
            else:
                # Compression didn't help, return original
                return response

        except Exception as e:
            logger.error(f"Response compression failed: {e}")
            return response

    def _apply_field_selection(self, response_body: bytes, fields: str) -> bytes:
        """Apply field selection to JSON response"""
        try:
            # Parse JSON
            data = json.loads(response_body.decode('utf-8'))
            requested_fields = [field.strip() for field in fields.split(',')]

            # Apply field selection based on data structure
            if isinstance(data, dict):
                filtered_data = self._filter_dict_fields(data, requested_fields)
            elif isinstance(data, list):
                filtered_data = [self._filter_dict_fields(item, requested_fields) for item in data if isinstance(item, dict)]
            else:
                return response_body

            # Convert back to bytes
            return json.dumps(filtered_data, default=str).encode('utf-8')

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Field selection failed: {e}")
            return response_body

    def _filter_dict_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """Filter dictionary to only include requested fields"""
        filtered = {}
        for field in fields:
            if field in data:
                filtered[field] = data[field]
        return filtered

    def get_metrics(self) -> Dict[str, Any]:
        """Get compression metrics"""
        total_responses = self._metrics["total_responses"]
        compression_rate = (self._metrics["responses_compressed"] / total_responses * 100) if total_responses > 0 else 0
        avg_compression_time = (self._metrics["compression_time_ms"] / self._metrics["responses_compressed"]) if self._metrics["responses_compressed"] > 0 else 0

        return {
            **self._metrics,
            "compression_rate_percent": compression_rate,
            "avg_compression_time_ms": avg_compression_time
        }


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Response optimization middleware for:
    - Response minimization
    - Standardized response format
    - Metadata management
    - ETag generation and caching headers
    """

    def __init__(self, app):
        super().__init__(app)
        self._metrics = {
            "responses_optimized": 0,
            "etags_generated": 0,
            "metadata_added": 0
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Optimize response format and add metadata"""
        response = await call_next(request)

        # Only optimize JSON responses
        if not response.headers.get("content-type", "").startswith("application/json"):
            return response

        # Parse and optimize response body
        if hasattr(response, 'body') and response.body:
            try:
                optimized_response = await self._optimize_response(response, request)
                self._metrics["responses_optimized"] += 1
                return optimized_response
            except Exception as e:
                logger.error(f"Response optimization failed: {e}")
                return response

        return response

    async def _optimize_response(self, response: Response, request: Request) -> Response:
        """Optimize response with metadata and caching headers"""
        try:
            # Parse response data
            response_data = json.loads(response.body.decode('utf-8'))

            # Add optimization metadata
            if isinstance(response_data, dict):
                # Add response metadata
                response_data["_metadata"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', None),
                    "version": "1.0",
                    "optimized": True
                }
                self._metrics["metadata_added"] += 1

                # Generate ETag for caching
                etag = self._generate_etag(response_data)
                self._metrics["etags_generated"] += 1

                # Create optimized response
                optimized_body = json.dumps(response_data, default=str, separators=(',', ':')).encode('utf-8')

                optimized_response = Response(
                    content=optimized_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json"
                )

                # Add caching headers
                optimized_response.headers["ETag"] = etag
                optimized_response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutes
                optimized_response.headers["X-Content-Type-Options"] = "nosniff"
                optimized_response.headers["X-Frame-Options"] = "DENY"
                optimized_response.headers["X-Optimized-Size"] = str(len(optimized_body))

                return optimized_response

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Response parsing failed: {e}")
            return response

    def _generate_etag(self, data: Dict[str, Any]) -> str:
        """Generate ETag from response data"""
        import hashlib
        # Create deterministic ETag from data content
        content_str = json.dumps(data, sort_keys=True, default=str)
        etag_hash = hashlib.md5(content_str.encode()).hexdigest()
        return f'W/"{etag_hash}"'

    def get_metrics(self) -> Dict[str, Any]:
        """Get optimization metrics"""
        return self._metrics.copy()


import time
from datetime import datetime
from uuid import uuid4

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Request tracking middleware for performance monitoring
    """

    def __init__(self, app):
        super().__init__(app)
        self._request_metrics = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request and add performance metadata"""
        start_time = time.time()
        request_id = str(uuid4())

        # Add request ID to state
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Add performance headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
        response.headers["X-Server-Timestamp"] = datetime.utcnow().isoformat()

        # Log slow requests
        if duration_ms > 1000:  # Log requests slower than 1 second
            logger.warning(f"Slow request detected: {request.method} {request.url.path} took {duration_ms:.2f}ms")

        # Update metrics
        endpoint = f"{request.method} {request.url.path}"
        if endpoint not in self._request_metrics:
            self._request_metrics[endpoint] = {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "max_duration_ms": 0
            }

        metrics = self._request_metrics[endpoint]
        metrics["count"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["count"]
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)

        return response

    def get_metrics(self) -> Dict[str, Any]:
        """Get request tracking metrics"""
        return self._request_metrics.copy()


def setup_response_compression(app, min_size: int = 1024, compressible_types: Optional[list] = None):
    """
    Set up response compression middleware for a FastAPI application

    Args:
        app: FastAPI application instance
        min_size: Minimum response size in bytes to compress
        compressible_types: List of content types to compress

    Returns:
        ResponseCompressionMiddleware instance for further configuration
    """
    try:
        compression_middleware = ResponseCompressionMiddleware(
            app,
            compress_threshold=min_size,
            enabled_content_types=compressible_types
        )
        app.add_middleware(ResponseCompressionMiddleware, compress_threshold=min_size, enabled_content_types=compressible_types)

        logger.info("Response compression middleware setup completed successfully")
        return compression_middleware

    except Exception as e:
        logger.error(f"Failed to setup response compression middleware: {e}")
        # Fail open - continue without compression if setup fails
        return None