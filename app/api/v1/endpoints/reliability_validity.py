"""
Reliability and Validity Analysis API Endpoints

REST API endpoints for comprehensive psychometric analysis including:
- Internal consistency reliability (Cronbach's Alpha, McDonald's Omega)
- Test-retest reliability analysis
- Factor analysis for construct validity
- Convergent and discriminant validity
- Item analysis and statistics
- Reliability and validity dashboards
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.services.prediction_data_service import PredictionDataCollectionService
from app.services.reliability_validity_service import (
    FactorAnalysisMethod,
    ReliabilityValidityService,
    RotationMethod,
    ValidityType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reliability-validity", tags=["Reliability & Validity"])


@router.get("", response_model=Dict[str, Any])
async def get_reliability_validity_info():
    """Get information about the reliability and validity analysis API."""
    return {
        "success": True,
        "name": "Reliability and Validity Analysis API",
        "version": "1.0.0",
        "description": "Endpoints for psychometric reliability and validity analysis.",
        "endpoints": [
            {"path": "/reliability/analyze", "method": "POST"},
            {"path": "/factor-analysis", "method": "POST"},
            {"path": "/validity/analyze", "method": "POST"},
            {"path": "/items/analyze", "method": "POST"},
            {"path": "/comprehensive/analyze", "method": "POST"},
            {"path": "/dashboard/{assessment_id}", "method": "GET"},
        ],
    }


# Pydantic models for request/response schemas


class ReliabilityAnalysisRequest(BaseModel):
    assessment_id: uuid.UUID = Field(..., description="Assessment ID to analyze")
    reliability_type: str = Field(
        "internal_consistency", description="Type of reliability analysis"
    )
    test_retest_interval_days: Optional[int] = Field(
        7, description="Interval in days for test-retest"
    )
    confidence_level: float = Field(
        0.95, ge=0.80, le=0.99, description="Confidence level"
    )
    item_ids: Optional[List[str]] = Field(
        None, description="Specific item IDs to include"
    )


class FactorAnalysisRequest(BaseModel):
    assessment_id: uuid.UUID = Field(..., description="Assessment ID to analyze")
    extraction_method: FactorAnalysisMethod = Field(FactorAnalysisMethod.PRINCIPAL_AXIS)
    rotation_method: RotationMethod = Field(RotationMethod.VARIMAX)
    n_factors: Optional[int] = Field(None, description="Number of factors to extract")
    parallel_analysis_samples: int = Field(
        100, ge=10, le=200, description="Samples for parallel analysis"
    )


class ValidityAnalysisRequest(BaseModel):
    assessment_id: uuid.UUID = Field(..., description="Assessment ID to validate")
    validity_type: ValidityType = Field(..., description="Type of validity analysis")
    criterion_assessment_id: Optional[uuid.UUID] = Field(
        None, description="Criterion assessment ID"
    )
    criterion_description: Optional[str] = Field(
        "", description="Description of criterion measure"
    )
    time_point_matching: str = Field(
        "respondent_id", description="Column for matching respondents"
    )


class ItemAnalysisRequest(BaseModel):
    assessment_id: uuid.UUID = Field(..., description="Assessment ID to analyze")
    item_answer_keys: Optional[Dict[str, str]] = Field(
        None, description="Correct answers for cognitive tests"
    )


class ComprehensiveAnalysisRequest(BaseModel):
    assessment_id: uuid.UUID = Field(..., description="Assessment ID to analyze")
    include_reliability: bool = Field(True, description="Include reliability analysis")
    include_validity: bool = Field(True, description="Include validity analysis")
    include_factor_analysis: bool = Field(True, description="Include factor analysis")
    include_item_analysis: bool = Field(True, description="Include item analysis")
    criterion_assessment_ids: Optional[List[uuid.UUID]] = Field(
        None, description="Criterion assessments for validity"
    )


# Response models


class ReliabilityAnalysisResponse(BaseModel):
    success: bool
    reliability_result: Optional[Dict[str, Any]] = None
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class FactorAnalysisResponse(BaseModel):
    success: bool
    factor_analysis_result: Optional[Dict[str, Any]] = None
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ValidityAnalysisResponse(BaseModel):
    success: bool
    validity_results: List[Dict[str, Any]] = []
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ItemAnalysisResponse(BaseModel):
    success: bool
    item_analysis_results: Dict[str, Dict[str, Any]] = {}
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ComprehensiveAnalysisResponse(BaseModel):
    success: bool
    reliability_results: Optional[Dict[str, Any]] = None
    validity_results: List[Dict[str, Any]] = []
    factor_analysis_results: Optional[Dict[str, Any]] = None
    item_analysis_results: Optional[Dict[str, Any]] = None
    overall_quality_score: Optional[float] = None
    recommendations: List[str] = []
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None


# Initialize services
reliability_service = ReliabilityValidityService()
data_service = PredictionDataCollectionService()


def pivot_response_data(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long response data into wide format (Respondents x Items)."""
    if df.empty:
        return pd.DataFrame()

    required_cols = ["user_id", "question_id", "answer_value"]
    if not all(col in df.columns for col in required_cols):
        logger.warning(
            f"Missing required columns for pivoting. Found: {list(df.columns)}"
        )
        return pd.DataFrame()

    if "created_at" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["created_at"]):
            df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at").drop_duplicates(
            ["user_id", "question_id"], keep="last"
        )
    else:
        df = df.drop_duplicates(["user_id", "question_id"], keep="last")

    df = df.copy()
    df["user_id"] = df["user_id"].astype(str)
    df["question_id"] = df["question_id"].astype(str)

    try:
        pivot_df = df.pivot(
            index="user_id", columns="question_id", values="answer_value"
        )
        pivot_df = pivot_df.apply(pd.to_numeric, errors="coerce")
        return pivot_df
    except Exception as e:
        logger.error(f"Error pivoting response data: {str(e)}")
        return pd.DataFrame()


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/reliability/analyze", response_model=ReliabilityAnalysisResponse)
async def analyze_reliability(
    request: ReliabilityAnalysisRequest, db: AsyncSession = Depends(get_db)
):
    """Calculate reliability coefficients (Cronbach's Alpha, McDonald's Omega)."""
    try:
        start_time = datetime.now()

        data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}",
            )

        response_df = pd.DataFrame(data_result["data"])
        item_responses = pivot_response_data(response_df)

        if item_responses.empty:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message="No valid response data available for analysis",
            )

        if len(item_responses.columns) < 2:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message="Assessment must have at least 2 items for reliability analysis",
            )

        if request.reliability_type == "internal_consistency":
            alpha_result = await reliability_service.calculate_cronbach_alpha(
                item_responses, request.item_ids, request.confidence_level
            )
            omega_result = await reliability_service.calculate_mcdonald_omega(
                item_responses, request.item_ids
            )

            reliability_result = {
                "cronbach_alpha": {
                    "coefficient": alpha_result.coefficient,
                    "confidence_interval": alpha_result.confidence_interval,
                    "interpretation": alpha_result.interpretation,
                    "item_statistics": alpha_result.item_statistics,
                    "recommendations": alpha_result.recommendations,
                },
                "mcdonald_omega": {
                    "coefficient": omega_result.coefficient,
                    "interpretation": omega_result.interpretation,
                },
                "sample_size": alpha_result.sample_size,
                "assessment_id": request.assessment_id,
                "analysis_date": datetime.now().isoformat(),
            }

        elif request.reliability_type == "test_retest":
            if not request.test_retest_interval_days:
                return ReliabilityAnalysisResponse(
                    success=False,
                    error_message="Test-retest interval must be specified",
                )
            reliability_result = {
                "coefficient": 0.0,
                "interpretation": "Test-retest analysis requires time-separated data collection",
                "assessment_id": request.assessment_id,
            }
        else:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message=f"Unsupported reliability type: {request.reliability_type}",
            )

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ReliabilityAnalysisResponse(
            success=True,
            reliability_result=reliability_result,
            analysis_time_seconds=analysis_time,
        )

    except Exception as e:
        logger.error(f"Error in reliability analysis: {str(e)}")
        return ReliabilityAnalysisResponse(success=False, error_message=str(e))


@router.post("/factor-analysis", response_model=FactorAnalysisResponse)
async def conduct_factor_analysis(
    request: FactorAnalysisRequest, db: AsyncSession = Depends(get_db)
):
    """Conduct exploratory factor analysis for construct validity."""
    try:
        start_time = datetime.now()

        data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return FactorAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}",
            )

        response_df = pd.DataFrame(data_result["data"])
        item_responses = pivot_response_data(response_df)

        if item_responses.empty:
            return FactorAnalysisResponse(
                success=False,
                error_message="No valid response data available for analysis",
            )

        if len(item_responses.columns) < 3:
            return FactorAnalysisResponse(
                success=False, error_message="Factor analysis requires at least 3 items"
            )

        fa_result = await reliability_service.conduct_factor_analysis(
            response_matrix=item_responses,
            extraction_method=request.extraction_method,
            rotation_method=request.rotation_method,
            n_factors=request.n_factors,
            parallel_analysis_samples=request.parallel_analysis_samples,
        )

        factor_analysis_result = {
            "extraction_method": fa_result.extraction_method.value,
            "rotation_method": fa_result.rotation_method.value,
            "eigenvalues": fa_result.eigenvalues.tolist(),
            "factor_loadings": fa_result.factor_loadings.to_dict(),
            "communalities": fa_result.communalities.tolist(),
            "uniqueness": fa_result.uniqueness.tolist(),
            "variance_explained": fa_result.variance_explained.tolist(),
            "cumulative_variance": fa_result.cumulative_variance.tolist(),
            "n_factors_suggested": fa_result.kaiser_criterion,
            "n_factors_parallel": fa_result.parallel_analysis,
            "factor_interpretation": fa_result.factor_interpretation,
            "assessment_id": request.assessment_id,
            "analysis_date": datetime.now().isoformat(),
        }

        if fa_result.factor_correlations is not None:
            factor_analysis_result["factor_correlations"] = (
                fa_result.factor_correlations.tolist()
            )

        analysis_time = (datetime.now() - start_time).total_seconds()

        return FactorAnalysisResponse(
            success=True,
            factor_analysis_result=factor_analysis_result,
            analysis_time_seconds=analysis_time,
        )

    except Exception as e:
        logger.error(f"Error in factor analysis: {str(e)}")
        return FactorAnalysisResponse(success=False, error_message=str(e))


@router.post("/validity/analyze", response_model=ValidityAnalysisResponse)
async def analyze_validity(
    request: ValidityAnalysisRequest, db: AsyncSession = Depends(get_db)
):
    """Calculate validity coefficients (convergent and discriminant)."""
    try:
        start_time = datetime.now()
        validity_results = []

        target_data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[request.assessment_id]
        )

        if not target_data_result["success"]:
            return ValidityAnalysisResponse(
                success=False,
                error_message=f"Failed to collect target assessment data: {target_data_result.get('error')}",
            )

        target_raw_df = pd.DataFrame(target_data_result["data"])
        target_pivot_df = pivot_response_data(target_raw_df)

        if target_pivot_df.empty:
            return ValidityAnalysisResponse(
                success=False,
                error_message="No response data available for the target assessment",
            )

        target_scores = target_pivot_df.sum(axis=1)

        if request.validity_type == ValidityType.CONVERGENT:
            if not request.criterion_assessment_id:
                return ValidityAnalysisResponse(
                    success=False,
                    error_message="Criterion assessment ID is required for convergent validity analysis",
                )

            criterion_data_result = await data_service.collect_assessment_data(
                db=db, assessment_ids=[request.criterion_assessment_id]
            )

            if not criterion_data_result["success"]:
                return ValidityAnalysisResponse(
                    success=False,
                    error_message=f"Failed to collect criterion assessment data: {criterion_data_result.get('error')}",
                )

            criterion_raw_df = pd.DataFrame(criterion_data_result["data"])
            criterion_pivot_df = pivot_response_data(criterion_raw_df)

            if criterion_pivot_df.empty:
                return ValidityAnalysisResponse(
                    success=False,
                    error_message="No response data available for the criterion assessment",
                )

            criterion_scores = criterion_pivot_df.sum(axis=1)

            validity_result = await reliability_service.calculate_convergent_validity(
                assessment_scores=target_scores,
                criterion_scores=criterion_scores,
                criterion_description=request.criterion_description
                or f"Assessment {request.criterion_assessment_id}",
            )

            validity_results.append(
                {
                    "validity_type": "convergent",
                    "coefficient": validity_result.coefficient,
                    "significance_level": validity_result.significance_level,
                    "confidence_interval": validity_result.confidence_interval,
                    "interpretation": validity_result.interpretation,
                    "sample_size": validity_result.sample_size,
                    "criterion_description": validity_result.criterion_description,
                    "recommendations": validity_result.recommendations,
                }
            )

        elif request.validity_type == ValidityType.DISCRIMINANT:
            validity_results.append(
                {
                    "validity_type": "discriminant",
                    "coefficient": 0.0,
                    "interpretation": "Discriminant validity analysis requires unrelated construct data",
                    "recommendations": [
                        "Collect data from theoretically unrelated constructs"
                    ],
                }
            )

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ValidityAnalysisResponse(
            success=True,
            validity_results=validity_results,
            analysis_time_seconds=analysis_time,
        )

    except Exception as e:
        logger.error(f"Error in validity analysis: {str(e)}")
        return ValidityAnalysisResponse(success=False, error_message=str(e))


@router.post("/items/analyze", response_model=ItemAnalysisResponse)
async def analyze_items(
    request: ItemAnalysisRequest, db: AsyncSession = Depends(get_db)
):
    """Analyze individual item statistics (difficulty, discrimination, distractors)."""
    try:
        start_time = datetime.now()

        data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return ItemAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}",
            )

        response_df = pd.DataFrame(data_result["data"])
        item_responses = pivot_response_data(response_df)

        if item_responses.empty:
            return ItemAnalysisResponse(
                success=False,
                error_message="No valid response data available for analysis",
            )

        total_scores = item_responses.sum(axis=1)

        item_analysis_results = await reliability_service.conduct_item_analysis(
            response_matrix=item_responses,
            total_scores=total_scores,
            item_answer_keys=request.item_answer_keys,
        )

        serialized_results = {}
        for item_id, result in item_analysis_results.items():
            serialized_results[item_id] = {
                "item_id": result.item_id,
                "difficulty": result.difficulty,
                "discrimination": result.discrimination,
                "item_total_correlation": result.item_total_correlation,
                "item_reliability": result.item_reliability,
                "item_validity": result.item_validity,
                "skewness": result.skewness,
                "kurtosis": result.kurtosis,
                "option_frequencies": result.option_frequencies,
                "distractor_analysis": result.distractor_analysis,
            }

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ItemAnalysisResponse(
            success=True,
            item_analysis_results=serialized_results,
            analysis_time_seconds=analysis_time,
        )

    except Exception as e:
        logger.error(f"Error in item analysis: {str(e)}")
        return ItemAnalysisResponse(success=False, error_message=str(e))


@router.post("/comprehensive/analyze", response_model=ComprehensiveAnalysisResponse)
async def conduct_comprehensive_analysis(
    request: ComprehensiveAnalysisRequest, db: AsyncSession = Depends(get_db)
):
    """Conduct comprehensive reliability and validity analysis."""
    try:
        start_time = datetime.now()
        overall_results = {}
        recommendations = []

        data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[request.assessment_id]
        )

        if not data_result.get("success") or not data_result.get("data"):
            return ComprehensiveAnalysisResponse(
                success=True,
                overall_quality_score=0.0,
                recommendations=[
                    "No assessment response data available yet. Complete some assessments to generate analysis."
                ],
                analysis_time_seconds=0.0,
            )

        # Reliability Analysis
        if request.include_reliability:
            try:
                reliability_request = ReliabilityAnalysisRequest(
                    assessment_id=request.assessment_id,
                    reliability_type="internal_consistency",
                )
                reliability_response = await analyze_reliability(
                    reliability_request, db
                )

                if reliability_response.success:
                    overall_results["reliability"] = (
                        reliability_response.reliability_result
                    )

                    cronbach_alpha = reliability_response.reliability_result.get(
                        "cronbach_alpha", {}
                    ).get("coefficient", 0.0)
                    if cronbach_alpha < 0.70:
                        recommendations.append(
                            "Low internal consistency reliability. Consider item revision."
                        )
                else:
                    recommendations.append(
                        "Reliability analysis failed. Check data quality."
                    )

            except Exception as e:
                logger.error(f"Error in reliability analysis: {str(e)}")
                recommendations.append("Unable to complete reliability analysis.")

        # Factor Analysis
        if request.include_factor_analysis:
            try:
                factor_request = FactorAnalysisRequest(
                    assessment_id=request.assessment_id
                )
                factor_response = await conduct_factor_analysis(factor_request, db)

                if factor_response.success:
                    overall_results["factor_analysis"] = (
                        factor_response.factor_analysis_result
                    )
                else:
                    recommendations.append(
                        "Factor analysis failed. Check sample size and data assumptions."
                    )

            except Exception as e:
                logger.error(f"Error in factor analysis: {str(e)}")
                recommendations.append("Unable to complete factor analysis.")

        # Item Analysis
        if request.include_item_analysis:
            try:
                item_request = ItemAnalysisRequest(assessment_id=request.assessment_id)
                item_response = await analyze_items(item_request, db)

                if item_response.success:
                    overall_results["item_analysis"] = (
                        item_response.item_analysis_results
                    )

                    poor_discrimination_items = []
                    for (
                        item_id,
                        item_stats,
                    ) in item_response.item_analysis_results.items():
                        if abs(item_stats["discrimination"]) < 0.30:
                            poor_discrimination_items.append(item_id)

                    if poor_discrimination_items:
                        recommendations.append(
                            f"Items with poor discrimination: {poor_discrimination_items[:5]}"
                        )
                else:
                    recommendations.append(
                        "Item analysis failed. Check response data format."
                    )

            except Exception as e:
                logger.error(f"Error in item analysis: {str(e)}")
                recommendations.append("Unable to complete item analysis.")

        overall_quality_score = _calculate_overall_quality_score(overall_results)

        if overall_quality_score >= 0.80:
            recommendations.append(
                "Excellent psychometric quality. Assessment is ready for use."
            )
        elif overall_quality_score >= 0.60:
            recommendations.append(
                "Good psychometric quality with minor areas for improvement."
            )
        else:
            recommendations.append(
                "Significant psychometric issues found. Major revision recommended."
            )

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ComprehensiveAnalysisResponse(
            success=True,
            reliability_results=overall_results.get("reliability"),
            validity_results=overall_results.get("validity", []),
            factor_analysis_results=overall_results.get("factor_analysis"),
            item_analysis_results=overall_results.get("item_analysis"),
            overall_quality_score=overall_quality_score,
            recommendations=recommendations,
            analysis_time_seconds=analysis_time,
        )

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        return ComprehensiveAnalysisResponse(success=False, error_message=str(e))


@router.get("/dashboard/{assessment_id}")
async def get_reliability_validity_dashboard(
    assessment_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Get reliability and validity dashboard data for an assessment."""
    try:
        data_result = await data_service.collect_assessment_data(
            db=db, assessment_ids=[assessment_id]
        )

        if not data_result.get("success") or not data_result.get("data"):
            return {
                "success": True,
                "dashboard": {
                    "assessment_id": str(assessment_id),
                    "total_respondents": 0,
                    "total_items": 0,
                    "cronbach_alpha": 0.0,
                    "data_quality": {
                        "completeness": 0.0,
                        "sample_size_adequacy": False,
                        "item_count_adequacy": False,
                    },
                    "reliability_status": "no_data",
                    "last_analysis": datetime.now().isoformat(),
                    "message": "No assessment response data available yet. Complete some assessments to see analysis.",
                },
            }

        response_df = pd.DataFrame(data_result["data"])
        item_responses = pivot_response_data(response_df)

        if item_responses.empty:
            return {
                "success": True,
                "dashboard": {
                    "assessment_id": str(assessment_id),
                    "total_respondents": 0,
                    "total_items": 0,
                    "cronbach_alpha": 0.0,
                    "data_quality": {
                        "completeness": 0.0,
                        "sample_size_adequacy": False,
                        "item_count_adequacy": False,
                    },
                    "reliability_status": "no_data",
                    "last_analysis": datetime.now().isoformat(),
                    "message": "Response data could not be processed. Check assessment question format.",
                },
            }

        total_respondents = len(item_responses)
        total_items = len(item_responses.columns)

        item_variances = item_responses.var(axis=0, ddof=1)
        total_score = item_responses.sum(axis=1)
        total_variance = total_score.var(ddof=1)

        if total_items > 1 and total_variance > 0:
            alpha = (total_items / (total_items - 1)) * (
                1 - (item_variances.sum() / total_variance)
            )
            alpha = max(0.0, min(1.0, alpha))
        else:
            alpha = 0.0

        dashboard_data = {
            "assessment_id": assessment_id,
            "total_respondents": total_respondents,
            "total_items": total_items,
            "cronbach_alpha": alpha,
            "data_quality": {
                "completeness": (
                    1
                    - item_responses.isnull().sum().sum()
                    / (total_respondents * total_items)
                ),
                "sample_size_adequacy": total_respondents >= 100,
                "item_count_adequacy": total_items >= 5,
            },
            "reliability_status": (
                "excellent"
                if alpha >= 0.90
                else (
                    "good"
                    if alpha >= 0.80
                    else "acceptable" if alpha >= 0.70 else "poor"
                )
            ),
            "last_analysis": datetime.now().isoformat(),
        }

        return {"success": True, "dashboard": dashboard_data}

    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        return JSONResponse(
            status_code=500, content={"success": False, "error_message": str(e)}
        )


def _calculate_overall_quality_score(analysis_results: Dict[str, Any]) -> float:
    """Calculate overall psychometric quality score."""
    score = 0.0
    weights = 0.0

    # Reliability contribution (40% weight)
    if "reliability" in analysis_results:
        cronbach_alpha = (
            analysis_results["reliability"]
            .get("cronbach_alpha", {})
            .get("coefficient", 0.0)
        )
        score += cronbach_alpha * 0.4
        weights += 0.4

    # Factor analysis contribution (30% weight)
    if "factor_analysis" in analysis_results:
        fa_results = analysis_results["factor_analysis"]
        variance_explained = fa_results.get("variance_explained", [0.0])
        total_variance = (
            sum(variance_explained[:3])
            if len(variance_explained) >= 3
            else sum(variance_explained)
        )
        score += min(total_variance, 1.0) * 0.3
        weights += 0.3

    # Item analysis contribution (30% weight)
    if "item_analysis" in analysis_results:
        item_results = analysis_results["item_analysis"]
        if item_results:
            discriminations = [
                item.get("discrimination", 0.0) for item in item_results.values()
            ]
            avg_discrimination = np.mean([abs(d) for d in discriminations])
            score += min(avg_discrimination, 1.0) * 0.3
            weights += 0.3

    if weights > 0:
        return score / weights
    else:
        return 0.0
