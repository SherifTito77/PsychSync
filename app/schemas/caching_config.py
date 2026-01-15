# app/schemas/caching_config.py
"""
Pydantic schemas for Caching Configuration
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CacheEntryBase(BaseModel):
    """Base schema for cache entry"""
    cache_key: str = Field(..., description="Cache key/identifier")
    cache_type: str = Field(..., description="Type: redis, memcached, in_memory, cdn")
    endpoint_path: str = Field(..., description="API endpoint or resource path")
    data_size_bytes: int = Field(..., description="Size of cached data in bytes")
    ttl_seconds: int = Field(..., description="Time to live in seconds")


class CacheEntryCreate(CacheEntryBase):
    """Schema for creating cache entry"""
    hit_count: int = Field(default=0, description="Number of cache hits")
    miss_count: int = Field(default=0, description="Number of cache misses")


class CacheEntry(CacheEntryBase):
    """Schema for cache entry response"""
    id: UUID
    hit_count: int
    miss_count: int
    hit_rate: float
    miss_rate: float
    last_accessed: datetime
    created_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class CachePerformanceBase(BaseModel):
    """Base schema for cache performance"""
    cache_type: str = Field(..., description="Type of cache")
    measurement_period: str = Field(..., description="Period: hourly, daily, weekly")


class CachePerformanceCreate(CachePerformanceBase):
    """Schema for creating cache performance record"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    avg_response_time_ms: float
    memory_usage_mb: float
    eviction_count: int


class CachePerformance(CachePerformanceBase):
    """Schema for cache performance response"""
    id: UUID
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    miss_rate: float
    avg_response_time_ms: float
    memory_usage_mb: float
    eviction_count: int
    measured_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class CacheOptimizationBase(BaseModel):
    """Base schema for cache optimization"""
    cache_key: str = Field(..., description="Cache key to optimize")
    optimization_type: str = Field(..., description="Type: ttl_adjust, size_reduce, preload, invalidate")


class CacheOptimizationCreate(CacheOptimizationBase):
    """Schema for creating optimization suggestion"""
    current_hit_rate: float
    expected_hit_rate: float
    estimated_improvement_mb: float
    implementation_effort: str = Field(..., description="effort: low, medium, high")
    ai_recommendation: Optional[str] = Field(None, description="AI-generated recommendation")


class CacheOptimization(CacheOptimizationBase):
    """Schema for cache optimization response"""
    id: UUID
    current_hit_rate: float
    expected_hit_rate: float
    estimated_improvement_mb: float
    implementation_effort: str
    ai_recommendation: Optional[str]
    is_applied: bool
    created_at: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class CacheConfigurationReportBase(BaseModel):
    """Base schema for cache configuration report"""
    report_date: datetime = Field(..., description="When report was generated")
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")


class CacheConfigurationReportCreate(CacheConfigurationReportBase):
    """Schema for creating cache configuration report"""
    total_cache_entries: int
    active_cache_types: list[str]
    overall_hit_rate: float
    total_memory_usage_mb: float
    avg_response_time_ms: float
    optimization_opportunities: int
    potential_improvement_mb: float
    top_slow_cache_keys: list[str]
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]


class CacheConfigurationReport(CacheConfigurationReportBase):
    """Schema for cache configuration report response"""
    id: UUID
    total_cache_entries: int
    active_cache_types: list[str]
    overall_hit_rate: float
    total_memory_usage_mb: float
    avg_response_time_ms: float
    optimization_opportunities: int
    potential_improvement_mb: float
    top_slow_cache_keys: list[str]
    configuration_grade: str
    ai_summary: str
    ai_insights: dict[str, Any]
    recommendations: list[str]

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class CacheSummary(BaseModel):
    """Summary of cache configuration"""
    total_cache_entries: int
    overall_hit_rate: float
    total_memory_usage_mb: float
    avg_response_time_ms: float
    configuration_grade: str
    optimization_opportunities: int
    potential_improvement_mb: float
    active_cache_types: list[str]
