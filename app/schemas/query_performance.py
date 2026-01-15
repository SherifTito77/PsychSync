# app/schemas/query_performance.py
"""
Pydantic schemas for Query Performance Optimization
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Slow Query Schemas
class SlowQueryBase(BaseModel):
    """SlowQueryBase class.

Description of class purpose and functionality.
    """
    query_text: str
    query_signature: str = Field(..., min_length=1, max_length=200)
    performance_tier: str = Field(..., pattern="^(critical|slow|moderate|acceptable)$")
    execution_count: int = Field(..., ge=1)
    total_time_ms: float = Field(..., ge=0)
    avg_time_ms: float = Field(..., ge=0)
    max_time_ms: float = Field(..., ge=0)
    min_time_ms: float = Field(..., ge=0)


class SlowQueryCreate(SlowQueryBase):
    """Schema definition for SlowQuery.

Validates and serializes data for API requests/responses.
    """
    query_hash: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    selectivity: Optional[float] = None
    bottleneck_type: Optional[str] = None
    optimization_potential: Optional[str] = None
    ai_suggestion: Optional[str] = None
    suggested_index: Optional[str] = None
    rewritten_query: Optional[str] = None
    estimated_improvement: Optional[float] = None


class SlowQueryUpdate(BaseModel):
    """Schema definition for SlowQuery.

Validates and serializes data for API requests/responses.
    """
    is_optimized: Optional[bool] = None
    optimization_applied_at: Optional[datetime] = None
    ai_suggestion: Optional[str] = None
    suggested_index: Optional[str] = None
    rewritten_query: Optional[str] = None


class SlowQueryInDB(SlowQueryBase):
    """SlowQueryInDB class.

Description of class purpose and functionality.
    """
    id: UUID
    query_hash: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None
    selectivity: Optional[float] = None
    bottleneck_type: Optional[str] = None
    optimization_potential: Optional[str] = None
    impact_score: float
    ai_suggestion: Optional[str] = None
    suggested_index: Optional[str] = None
    rewritten_query: Optional[str] = None
    estimated_improvement: Optional[float] = None
    is_optimized: bool
    optimization_applied_at: Optional[datetime] = None
    first_detected: datetime
    last_detected: datetime

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class SlowQuery(SlowQueryInDB):
    """SlowQuery class.

Description of class purpose and functionality.
    """
    pass


# Index Recommendation Schemas
class IndexRecommendationBase(BaseModel):
    """IndexRecommendationBase class.

Description of class purpose and functionality.
    """
    table_name: str
    index_name: str
    columns: list[str]
    index_type: str = Field(..., pattern="^(btree|hash|gin|gist)$")
    estimated_benefit: str = Field(..., pattern="^(high|medium|low)$")
    create_statement: str
    priority: str = Field(..., pattern="^(urgent|high|medium|low)$")


class IndexRecommendationCreate(IndexRecommendationBase):
    """Schema definition for IndexRecommendation.

Validates and serializes data for API requests/responses.
    """
    query_id: UUID
    estimated_speedup: Optional[float] = None
    affected_queries: int = 1
    size_estimate_mb: Optional[float] = None
    write_overhead: Optional[str] = None
    storage_overhead_mb: Optional[float] = None


class IndexRecommendationUpdate(BaseModel):
    """Schema definition for IndexRecommendation.

Validates and serializes data for API requests/responses.
    """
    is_created: Optional[bool] = None
    created_at: Optional[datetime] = None
    priority: Optional[str] = None


class IndexRecommendationInDB(IndexRecommendationBase):
    """IndexRecommendationInDB class.

Description of class purpose and functionality.
    """
    id: UUID
    query_id: UUID
    estimated_speedup: Optional[float] = None
    affected_queries: int
    size_estimate_mb: Optional[float] = None
    write_overhead: Optional[str] = None
    storage_overhead_mb: Optional[float] = None
    is_created: bool
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class IndexRecommendation(IndexRecommendationInDB):
    """IndexRecommendation class.

Description of class purpose and functionality.
    """
    pass


# Query Performance History Schema
class QueryPerformanceHistoryBase(BaseModel):
    """QueryPerformanceHistoryBase class.

Description of class purpose and functionality.
    """
    execution_time_ms: float
    rows_examined: Optional[int] = None
    rows_returned: Optional[int] = None


class QueryPerformanceHistoryInDB(QueryPerformanceHistoryBase):
    """QueryPerformanceHistoryInDB class.

Description of class purpose and functionality.
    """
    id: UUID
    query_id: UUID
    recorded_at: datetime
    context: Optional[dict[str, Any]] = None

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class QueryPerformanceHistory(QueryPerformanceHistoryInDB):
    """QueryPerformanceHistory class.

Description of class purpose and functionality.
    """
    pass


# Optimization Report Schemas
class QueryOptimizationReportBase(BaseModel):
    """QueryOptimizationReportBase class.

Description of class purpose and functionality.
    """
    report_date: datetime
    total_queries_analyzed: int
    slow_queries_count: int
    critical_queries_count: int
    avg_query_time_ms: float
    p95_query_time_ms: float
    p99_query_time_ms: float


class QueryOptimizationReportInDB(QueryOptimizationReportBase):
    """QueryOptimizationReportInDB class.

Description of class purpose and functionality.
    """
    id: UUID
    total_optimization_potential_ms: float
    estimated_speedup_percentage: float
    missing_indexes_count: int
    n_plus_1_count: int
    full_table_scans: int
    inefficient_joins: int
    ai_summary: Optional[str] = None
    ai_insights: Optional[dict[str, Any]] = None
    top_slow_queries: Optional[list[dict[str, Any]]] = None
    performance_trend: Optional[str] = None
    optimization_progress: Optional[float] = None

    class Config:
        """Config class.

Description of class purpose and functionality.
        """
        from_attributes = True


class QueryOptimizationReport(QueryOptimizationReportInDB):
    """QueryOptimizationReport class.

Description of class purpose and functionality.
    """
    pass


# Summary and Analysis Schemas
class QueryPerformanceSummary(BaseModel):
    """QueryPerformanceSummary class.

Description of class purpose and functionality.
    """
    total_queries: int
    slow_queries: int
    critical_queries: int
    avg_query_time_ms: float
    overall_performance_grade: str  # A+ to F
    optimization_potential_ms: float
    estimated_improvement_percentage: float


class QueryOptimizationTrend(BaseModel):
    """QueryOptimizationTrend class.

Description of class purpose and functionality.
    """
    date: datetime
    avg_query_time_ms: float
    slow_queries_count: int
    critical_queries_count: int
    optimization_progress: float


class OptimizationRecommendation(BaseModel):
    """OptimizationRecommendation class.

Description of class purpose and functionality.
    """
    priority: str
    category: str  # index, query_rewrite, schema_change
    recommendation: str
    affected_queries: list[str]
    estimated_speedup: float  # e.g., 10.0 for 10x faster
    estimated_effort: str  # low, medium, high
    create_statement: Optional[str] = None
    rewritten_query: Optional[str] = None
