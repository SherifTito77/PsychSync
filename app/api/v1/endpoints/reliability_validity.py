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

from datetime import datetime, timedelta

from app.core.rate_limiter_unified import check_rate_limit
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import asyncio
import logging

from app.core.database import get_db
from app.services.reliability_validity_service import (
    ReliabilityValidityService, ReliabilityType, ValidityType,
    FactorAnalysisMethod, RotationMethod, ReliabilityResult,
    ValidityResult, FactorAnalysisResult, ItemAnalysisResult
)
from app.services.prediction_data_service import PredictionDataCollectionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response schemas

class ReliabilityAnalysisRequest(BaseModel):
    """Request model for reliability analysis."""
    assessment_id: int = Field(..., description="Assessment ID to analyze")
    reliability_type: str = Field("internal_consistency", description="Type of reliability analysis")
    test_retest_interval_days: Optional[int] = Field(7, description="Interval in days for test-retest")
    confidence_level: float = Field(0.95, ge=0.80, le=0.99, description="Confidence level")
    item_ids: Optional[List[str]] = Field(None, description="Specific item IDs to include")

class FactorAnalysisRequest(BaseModel):
    """Request model for factor analysis."""
    assessment_id: int = Field(..., description="Assessment ID to analyze")
    extraction_method: FactorAnalysisMethod = Field(FactorAnalysisMethod.PRINCIPAL_AXIS)
    rotation_method: RotationMethod = Field(RotationMethod.VARIMAX)
    n_factors: Optional[int] = Field(None, description="Number of factors to extract")
    parallel_analysis_samples: int = Field(100, ge=10, le=1000, description="Samples for parallel analysis")

class ValidityAnalysisRequest(BaseModel):
    """Request model for validity analysis."""
    assessment_id: int = Field(..., description="Assessment ID to validate")
    validity_type: ValidityType = Field(..., description="Type of validity analysis")
    criterion_assessment_id: Optional[int] = Field(None, description="Criterion assessment ID")
    criterion_description: Optional[str] = Field("", description="Description of criterion measure")
    time_point_matching: str = Field("respondent_id", description="Column for matching respondents")

class ItemAnalysisRequest(BaseModel):
    """Request model for item analysis."""
    assessment_id: int = Field(..., description="Assessment ID to analyze")
    item_answer_keys: Optional[Dict[str, str]] = Field(None, description="Correct answers for cognitive tests")

class ComprehensiveAnalysisRequest(BaseModel):
    """Request model for comprehensive reliability and validity analysis."""
    assessment_id: int = Field(..., description="Assessment ID to analyze")
    include_reliability: bool = Field(True, description="Include reliability analysis")
    include_validity: bool = Field(True, description="Include validity analysis")
    include_factor_analysis: bool = Field(True, description="Include factor analysis")
    include_item_analysis: bool = Field(True, description="Include item analysis")
    criterion_assessment_ids: Optional[List[int]] = Field(None, description="Criterion assessments for validity")

# Response models

class ReliabilityAnalysisResponse(BaseModel):
    """Response model for reliability analysis."""
    success: bool
    reliability_result: Optional[Dict[str, Any]] = None
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

class FactorAnalysisResponse(BaseModel):
    """Response model for factor analysis."""
    success: bool
    factor_analysis_result: Optional[Dict[str, Any]] = None
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

class ValidityAnalysisResponse(BaseModel):
    """Response model for validity analysis."""
    success: bool
    validity_results: List[Dict[str, Any]] = []
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

class ItemAnalysisResponse(BaseModel):
    """Response model for item analysis."""
    success: bool
    item_analysis_results: Dict[str, Dict[str, Any]] = {}
    analysis_time_seconds: Optional[float] = None
    error_message: Optional[str] = None

class ComprehensiveAnalysisResponse(BaseModel):
    """Response model for comprehensive analysis."""
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


@check_rate_limit(identifier="public", limit_name="public")
@router.post("/reliability/analyze", response_model=ReliabilityAnalysisResponse)
async def analyze_reliability(
    request: ReliabilityAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Conduct reliability analysis for an assessment.

    This endpoint calculates various reliability coefficients including
    Cronbach's Alpha, McDonald's Omega, and test-retest reliability.
    """
    try:
        start_time = datetime.now()

        # Collect response data for the assessment
        data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}"
            )

        response_df = data_result["data"]

        if response_df.empty:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message="No response data available for the specified assessment"
            )

        # Identify item columns (assuming they contain response data)
        item_columns = [col for col in response_df.columns
                       if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]

        if len(item_columns) < 2:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message="Assessment must have at least 2 items for reliability analysis"
            )

        # Extract item responses
        item_responses = response_df[item_columns]

        # Perform reliability analysis based on type
        if request.reliability_type == "internal_consistency":
            # Calculate both Cronbach's Alpha and McDonald's Omega
            alpha_result = await reliability_service.calculate_cronbach_alpha(
                item_responses, request.item_ids, request.confidence_level
            )

            omega_result = await reliability_service.calculate_mcdonald_omega(
                item_responses, request.item_ids
            )

            # Combine results
            reliability_result = {
                "cronbach_alpha": {
                    "coefficient": alpha_result.coefficient,
                    "confidence_interval": alpha_result.confidence_interval,
                    "interpretation": alpha_result.interpretation,
                    "item_statistics": alpha_result.item_statistics,
                    "recommendations": alpha_result.recommendations
                },
                "mcdonald_omega": {
                    "coefficient": omega_result.coefficient,
                    "interpretation": omega_result.interpretation
                },
                "sample_size": alpha_result.sample_size,
                "assessment_id": request.assessment_id,
                "analysis_date": datetime.now().isoformat()
            }

        elif request.reliability_type == "test_retest":
            # For test-retest, need time-separated data
            if not request.test_retest_interval_days:
                return ReliabilityAnalysisResponse(
                    success=False,
                    error_message="Test-retest interval must be specified"
                )

            # This would require collecting data from two time points
            # For now, provide a placeholder implementation
            reliability_result = {
                "coefficient": 0.0,
                "interpretation": "Test-retest analysis requires time-separated data collection",
                "assessment_id": request.assessment_id
            }

        else:
            return ReliabilityAnalysisResponse(
                success=False,
                error_message=f"Unsupported reliability type: {request.reliability_type}"
            )

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ReliabilityAnalysisResponse(
            success=True,
            reliability_result=reliability_result,
            analysis_time_seconds=analysis_time
        )

    except Exception as e:
        logger.error(f"Error in reliability analysis: {str(e)}")
        return ReliabilityAnalysisResponse(
            success=False,
            error_message=str(e)
        )

@router.post("/factor-analysis", response_model=FactorAnalysisResponse)
async def conduct_factor_analysis(
    request: FactorAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Conduct exploratory factor analysis for construct validity.

    This endpoint performs factor analysis with various extraction methods
    and rotations to assess the underlying factor structure.
    """
    try:
        start_time = datetime.now()

        # Collect response data
        data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return FactorAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}"
            )

        response_df = data_result["data"]

        if response_df.empty:
            return FactorAnalysisResponse(
                success=False,
                error_message="No response data available for the specified assessment"
            )

        # Identify item columns
        item_columns = [col for col in response_df.columns
                       if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]

        if len(item_columns) < 3:
            return FactorAnalysisResponse(
                success=False,
                error_message="Factor analysis requires at least 3 items"
            )

        # Extract item responses
        item_responses = response_df[item_columns]

        # Conduct factor analysis
        fa_result = await reliability_service.conduct_factor_analysis(
            response_matrix=item_responses,
            extraction_method=request.extraction_method,
            rotation_method=request.rotation_method,
            n_factors=request.n_factors,
            parallel_analysis_samples=request.parallel_analysis_samples
        )

        # Prepare result for JSON serialization
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
            "analysis_date": datetime.now().isoformat()
        }

        if fa_result.factor_correlations is not None:
            factor_analysis_result["factor_correlations"] = fa_result.factor_correlations.tolist()

        analysis_time = (datetime.now() - start_time).total_seconds()

        return FactorAnalysisResponse(
            success=True,
            factor_analysis_result=factor_analysis_result,
            analysis_time_seconds=analysis_time
        )

    except Exception as e:
        logger.error(f"Error in factor ana lysis: {str(e)}")
        return FactorAnalysisResponse(
            success=False,
            error_message=str(e)
        )

@router.post("/validity/analyze", response_model=ValidityAnalysisResponse)
async def analyze_validity(
    request: ValidityAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Conduct validity analysis for an assessment.

    This endpoint calculates various validity coefficients including
    convergent and discriminant validity.
    """
    try:
        start_time = datetime.now()
        validity_results = []

        # Collect data for the target assessment
        target_data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[request.assessment_id]
        )

        if not target_data_result["success"]:
            return ValidityAnalysisResponse(
                success=False,
                error_message=f"Failed to collect target assessment data: {target_data_result.get('error')}"
            )

        target_df = target_data_result["data"]

        if target_df.empty:
            return ValidityAnalysisResponse(
                success=False,
                error_message="No response data available for the target assessment"
            )

        # Calculate total scores for the target assessment
        item_columns = [col for col in target_df.columns
                       if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]

        target_scores = target_df[item_columns].sum(axis=1)

        if request.validity_type == ValidityType.CONVERGENT:
            # Need criterion assessment data
            if not request.criterion_assessment_id:
                return ValidityAnalysisResponse(
                    success=False,
                    error_message="Criterion assessment ID is required for convergent validity analysis"
                )

            # Collect criterion assessment data
            criterion_data_result = await data_service.collect_assessment_data(
                db=db,
                assessment_ids=[request.criterion_assessment_id]
            )

            if not criterion_data_result["success"]:
                return ValidityAnalysisResponse(
                    success=False,
                    error_message=f"Failed to collect criterion assessment data: {criterion_data_result.get('error')}"
                )

            criterion_df = criterion_data_result["data"]

            # Calculate criterion scores
            criterion_item_columns = [col for col in criterion_df.columns
                                   if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]
            criterion_scores = criterion_df[criterion_item_columns].sum(axis=1)

            # Calculate convergent validity
            validity_result = await reliability_service.calculate_convergent_validity(
                assessment_scores=target_scores,
                criterion_scores=criterion_scores,
                criterion_description=request.criterion_description or f"Assessment {request.criterion_assessment_id}"
            )

            validity_results.append({
                "validity_type": "convergent",
                "coefficient": validity_result.coefficient,
                "significance_level": validity_result.significance_level,
                "confidence_interval": validity_result.confidence_interval,
                "interpretation": validity_result.interpretation,
                "sample_size": validity_result.sample_size,
                "criterion_description": validity_result.criterion_description,
                "recommendations": validity_result.recommendations
            })

        elif request.validity_type == ValidityType.DISCRIMINANT:
            # For discriminant validity, we would need unrelated construct data
            # This is a placeholder implementation
            validity_results.append({
                "validity_type": "discriminant",
                "coefficient": 0.0,
                "interpretation": "Discriminant validity analysis requires unrelated construct data",
                "recommendations": ["Collect data from theoretically unrelated constructs"]
            })

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ValidityAnalysisResponse(
            success=True,
            validity_results=validity_results,
            analysis_time_seconds=analysis_time
        )

    except Exception as e:
        logger.error(f"Error in validity analysis: {str(e)}")
        return ValidityAnalysisResponse(
            success=False,
            error_message=str(e)
        )

@router.post("/items/analyze", response_model=ItemAnalysisResponse)
async def analyze_items(
    request: ItemAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Conduct comprehensive item analysis.

    This endpoint analyzes individual item statistics including
    difficulty, discrimination, and distractor analysis.
    """
    try:
        start_time = datetime.now()

        # Collect response data
        data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return ItemAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}"
            )

        response_df = data_result["data"]

        if response_df.empty:
            return ItemAnalysisResponse(
                success=False,
                error_message="No response data available for the specified assessment"
            )

        # Identify item columns
        item_columns = [col for col in response_df.columns
                       if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]

        if len(item_columns) < 1:
            return ItemAnalysisResponse(
                success=False,
                error_message="No items found for analysis"
            )

        # Extract item responses and calculate total scores
        item_responses = response_df[item_columns]
        total_scores = item_responses.sum(axis=1)

        # Conduct item analysis
        item_analysis_results = await reliability_service.conduct_item_analysis(
            response_matrix=item_responses,
            total_scores=total_scores,
            item_answer_keys=request.item_answer_keys
        )

        # Prepare results for JSON serialization
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
                "distractor_analysis": result.distractor_analysis
            }

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ItemAnalysisResponse(
            success=True,
            item_analysis_results=serialized_results,
            analysis_time_seconds=analysis_time
        )

    except Exception as e:
        logger.error(f"Error in item analysis: {str(e)}")
        return ItemAnalysisResponse(
            success=False,
            error_message=str(e)
        )

@router.post("/comprehensive/analyze", response_model=ComprehensiveAnalysisResponse)
async def conduct_comprehensive_analysis(
    request: ComprehensiveAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Conduct comprehensive reliability and validity analysis.

    This endpoint provides a complete psychometric analysis including
    reliability, validity, factor analysis, and item analysis.
    """
    try:
        start_time = datetime.now()
        overall_results = {}
        recommendations = []

        # Collect response data once
        data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[request.assessment_id]
        )

        if not data_result["success"]:
            return ComprehensiveAnalysisResponse(
                success=False,
                error_message=f"Failed to collect assessment data: {data_result.get('error')}"
            )

        # Reliability Analysis
        if request.include_reliability:
            try:
                reliability_request = ReliabilityAnalysisRequest(
                    assessment_id=request.assessment_id,
                    reliability_type="internal_consistency"
                )
                reliability_response = await analyze_reliability(reliability_request, db)

                if reliability_response.success:
                    overall_results["reliability"] = reliability_response.reliability_result

                    # Extract reliability score for quality assessment
                    cronbach_alpha = reliability_response.reliability_result.get("cronbach_alpha", {}).get("coefficient", 0.0)
                    if cronbach_alpha < 0.70:
                        recommendations.append("Low internal consistency reliability. Consider item revision.")
                else:
                    recommendations.append("Reliability analysis failed. Check data quality.")

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
                    overall_results["factor_analysis"] = factor_response.factor_analysis_result
                else:
                    recommendations.append("Factor analysis failed. Check sample size and data assumptions.")

            except Exception as e:
                logger.error(f"Error in factor analysis: {str(e)}")
                recommendations.append("Unable to complete factor analysis.")

        # Item Analysis
        if request.include_item_analysis:
            try:
                item_request = ItemAnalysisRequest(
                    assessment_id=request.assessment_id
                )
                item_response = await analyze_items(item_request, db)

                if item_response.success:
                    overall_results["item_analysis"] = item_response.item_analysis_results

                    # Check for problematic items
                    poor_discrimination_items = []
                    for item_id, item_stats in item_response.item_analysis_results.items():
                        if abs(item_stats["discrimination"]) < 0.30:
                            poor_discrimination_items.append(item_id)

                    if poor_discrimination_items:
                        recommendations.append(f"Items with poor discrimination: {poor_discrimination_items[:5]}")
                else:
                    recommendations.append("Item analysis failed. Check response data format.")

            except Exception as e:
                logger.error(f"Error in item analysis: {str(e)}")
                recommendations.append("Unable to complete item analysis.")

        # Calculate overall quality score
        overall_quality_score = _calculate_overall_quality_score(overall_results)

        # Add general recommendations
        if overall_quality_score >= 0.80:
            recommendations.append("Excellent psychometric quality. Assessment is ready for use.")
        elif overall_quality_score >= 0.60:
            recommendations.append("Good psychometric quality with minor areas for improvement.")
        else:
            recommendations.append("Significant psychometric issues found. Major revision recommended.")

        analysis_time = (datetime.now() - start_time).total_seconds()

        return ComprehensiveAnalysisResponse(
            success=True,
            reliability_results=overall_results.get("reliability"),
            validity_results=overall_results.get("validity", []),
            factor_analysis_results=overall_results.get("factor_analysis"),
            item_analysis_results=overall_results.get("item_analysis"),
            overall_quality_score=overall_quality_score,
            recommendations=recommendations,
            analysis_time_seconds=analysis_time
        )

    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {str(e)}")
        return ComprehensiveAnalysisResponse(
            success=False,
            error_message=str(e)
        )

@router.get("/dashboard/{assessment_id}")
async def get_reliability_validity_dashboard(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get reliability and validity dashboard data for an assessment.

    This endpoint provides a comprehensive overview of psychometric quality
    for quick assessment evaluation.
    """
    try:
        # Collect basic assessment data
        data_result = await data_service.collect_assessment_data(
            db=db,
            assessment_ids=[assessment_id]
        )

        if not data_result["success"]:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error_message": f"Assessment {assessment_id} not found or no data available"
                }
            )

        response_df = data_result["data"]
        item_columns = [col for col in response_df.columns
                       if col not in ['user_id', 'assessment_id', 'team_id', 'response_date']]

        # Calculate basic statistics
        total_respondents = len(response_df)
        total_items = len(item_columns)

        # Quick reliability estimate (Cronbach's Alpha)
        item_responses = response_df[item_columns]
        item_variances = item_responses.var(axis=0, ddof=1)
        total_score = item_responses.sum(axis=1)
        total_variance = total_score.var(ddof=1)

        if total_items > 1 and total_variance > 0:
            alpha = (total_items / (total_items - 1)) * (1 - (item_variances.sum() / total_variance))
            alpha = max(0.0, min(1.0, alpha))
        else:
            alpha = 0.0

        # Dashboard data
        dashboard_data = {
            "assessment_id": assessment_id,
            "total_respondents": total_respondents,
            "total_items": total_items,
            "cronbach_alpha": alpha,
            "data_quality": {
                "completeness": (1 - item_responses.isnull().sum().sum() / (total_respondents * total_items)),
                "sample_size_adequacy": total_respondents >= 100,
                "item_count_adequacy": total_items >= 5
            },
            "reliability_status": "excellent" if alpha >= 0.90 else
                               "good" if alpha >= 0.80 else
                               "acceptable" if alpha >= 0.70 else "poor",
            "last_analysis": datetime.now().isoformat()
        }

        return {
            "success": True,
            "dashboard": dashboard_data
        }

    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_message": str(e)
            }
        )

def _calculate_overall_quality_score(analysis_results: Dict[str, Any]) -> float:
    """Calculate overall psychometric quality score."""
    score = 0.0
    weights = 0.0

    # Reliability contribution (40% weight)
    if "reliability" in analysis_results:
        cronbach_alpha = analysis_results["reliability"].get("cronbach_alpha", {}).get("coefficient", 0.0)
        score += cronbach_alpha * 0.4
        weights += 0.4

    # Factor analysis contribution (30% weight)
    if "factor_analysis" in analysis_results:
        fa_results = analysis_results["factor_analysis"]
        # Use proportion of variance explained as quality metric
        variance_explained = fa_results.get("variance_explained", [0.0])
        total_variance = sum(variance_explained[:3]) if len(variance_explained) >= 3 else sum(variance_explained)
        score += min(total_variance, 1.0) * 0.3
        weights += 0.3

    # Item analysis contribution (30% weight)
    if "item_analysis" in analysis_results:
        item_results = analysis_results["item_analysis"]
        if item_results:
            # Average discrimination as quality metric
            discriminations = [item.get("discrimination", 0.0) for item in item_results.values()]
            avg_discrimination = np.mean([abs(d) for d in discriminations])
            score += min(avg_discrimination, 1.0) * 0.3
            weights += 0.3

    # Normalize score
    if weights > 0:
        return score / weights
    else:
        return 0.0
