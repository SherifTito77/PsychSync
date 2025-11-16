
#app/api/routes/assessment_routes.py
"""
FastAPI routes for clinical assessments.
Handles assessment administration, scoring, and results retrieval.

File: app/api/routes/assessment_routes.py
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
import uuid

# Import assessment modules
from app.assessments.scoring_engine import ScoringEngine

# Initialize router
router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])

# Initialize scoring engine
scorer = ScoringEngine()


# ============================================================================
# Request/Response Models
# ============================================================================

class AssessmentListItem(BaseModel):
    """Summary of available assessment."""
    assessment_id: str
    name: str
    acronym: str
    category: str
    num_items: int
    estimated_duration_minutes: int
    description: str


class StartAssessmentRequest(BaseModel):
    """Request to start an assessment."""
    assessment_id: str
    client_id: str
    clinician_id: str
    context: str = Field(..., regex="^(intake|progress|discharge|follow_up|research)$")


class SubmitResponseRequest(BaseModel):
    """Submit response to assessment item."""
    administration_id: str
    item_number: int
    response_value: int
    response_time_seconds: Optional[int] = None


class CompleteAssessmentRequest(BaseModel):
    """Complete an assessment."""
    administration_id: str
    responses: Dict[int, int] = Field(..., description="item_number -> response_value")
    client_demographics: Optional[Dict] = None


class AssessmentResultResponse(BaseModel):
    """Assessment results."""
    administration_id: str
    assessment_id: str
    client_id: str
    total_score: float
    subscale_scores: Dict[str, float]
    severity_level: str
    interpretation: str
    clinical_significance: str
    recommendations: List[str]
    completed_at: str


# ============================================================================
# Assessment Catalog Endpoints
# ============================================================================

@router.get("/catalog", response_model=List[AssessmentListItem])
async def get_assessment_catalog(
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get catalog of available assessments.
    
    **Query Parameters:**
    - category: Filter by category (screening, personality, etc.)
    - search: Search by name or acronym
    
    **Returns:**
    List of available assessments with metadata
    """
    # In production, query from database
    # For demo, return static list
    
    catalog = [
        {
            "assessment_id": "phq9",
            "name": "Patient Health Questionnaire-9",
            "acronym": "PHQ-9",
            "category": "screening",
            "num_items": 9,
            "estimated_duration_minutes": 3,
            "description": "Brief screening tool for depression severity"
        },
        {
            "assessment_id": "gad7",
            "name": "Generalized Anxiety Disorder-7",
            "acronym": "GAD-7",
            "category": "screening",
            "num_items": 7,
            "estimated_duration_minutes": 2,
            "description": "Screening for generalized anxiety disorder"
        },
        {
            "assessment_id": "dass21",
            "name": "Depression Anxiety Stress Scale",
            "acronym": "DASS-21",
            "category": "screening",
            "num_items": 21,
            "estimated_duration_minutes": 5,
            "description": "Measures depression, anxiety, and stress"
        },
        {
            "assessment_id": "pcl5",
            "name": "PTSD Checklist for DSM-5",
            "acronym": "PCL-5",
            "category": "trauma",
            "num_items": 20,
            "estimated_duration_minutes": 5,
            "description": "Screens for PTSD symptoms"
        },
        {
            "assessment_id": "audit",
            "name": "Alcohol Use Disorders Identification Test",
            "acronym": "AUDIT",
            "category": "screening",
            "num_items": 10,
            "estimated_duration_minutes": 3,
            "description": "Screens for alcohol misuse and dependence"
        },
        {
            "assessment_id": "ace",
            "name": "Adverse Childhood Experiences Questionnaire",
            "acronym": "ACE",
            "category": "trauma",
            "num_items": 10,
            "estimated_duration_minutes": 3,
            "description": "Assesses childhood trauma exposure"
        },
        {
            "assessment_id": "bdi",
            "name": "Beck Depression Inventory-II",
            "acronym": "BDI-II",
            "category": "behavioral",
            "num_items": 21,
            "estimated_duration_minutes": 10,
            "description": "Gold standard depression assessment"
        },
        {
            "assessment_id": "stai",
            "name": "State-Trait Anxiety Inventory",
            "acronym": "STAI",
            "category": "behavioral",
            "num_items": 40,
            "estimated_duration_minutes": 10,
            "description": "Measures state and trait anxiety"
        }
    ]
    
    # Apply filters
    if category:
        catalog = [a for a in catalog if a["category"] == category]
    
    if search:
        search_lower = search.lower()
        catalog = [
            a for a in catalog 
            if search_lower in a["name"].lower() or search_lower in a["acronym"].lower()
        ]
    
    return catalog


@router.get("/catalog/{assessment_id}")
async def get_assessment_details(assessment_id: str):
    """
    Get detailed information about a specific assessment.
    
    **Returns:**
    - Full assessment details including items, scoring rules, norms
    """
    # In production, query from database
    
    if assessment_id not in scorer.scoring_methods:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment {assessment_id} not found"
        )
    
    # Return details (simplified for demo)
    details = {
        "assessment_id": assessment_id,
        "name": assessment_id.upper(),
        "category": "screening",
        "num_items": 10,
        "has_subscales": assessment_id in ['dass21', 'pcl5', 'stai'],
        "scoring_available": True,
        "normative_data_available": False
    }
    
    return details


# ============================================================================
# Assessment Administration Endpoints
# ============================================================================

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_assessment(request: StartAssessmentRequest):
    """
    Start a new assessment administration.
    
    **Returns:**
    - administration_id: Unique ID for this administration
    - assessment_items: List of items to present
    """
    # Generate unique administration ID
    administration_id = f"admin_{uuid.uuid4().hex[:12]}"
    
    # In production: Create database record
    # AssessmentAdministration.objects.create(...)
    
    # Get assessment items (simplified)
    # In production: Query from AssessmentItem table
    
    return {
        "administration_id": administration_id,
        "assessment_id": request.assessment_id,
        "client_id": request.client_id,
        "status": "in_progress",
        "started_at": datetime.utcnow().isoformat(),
        "message": "Assessment started. Submit responses using /submit endpoint."
    }


@router.post("/submit-response")
async def submit_response(request: SubmitResponseRequest):
    """
    Submit response to a single assessment item.
    
    **Use case:** Real-time response submission during assessment
    
    **Returns:**
    Success confirmation
    """
    # In production: Save to AssessmentResponse table
    
    return {
        "success": True,
        "administration_id": request.administration_id,
        "item_number": request.item_number,
        "recorded_at": datetime.utcnow().isoformat()
    }


@router.post("/complete", response_model=AssessmentResultResponse)
async def complete_assessment(request: CompleteAssessmentRequest):
    """
    Complete assessment and calculate scores.
    
    **Workflow:**
    1. Submit all responses
    2. Calculate scores using scoring engine
    3. Generate interpretation and recommendations
    4. Store results
    
    **Returns:**
    Complete assessment results with clinical interpretation
    """
    try:
        # Score the assessment
        result = scorer.score_assessment(
            assessment_id=request.administration_id.split('_')[0],  # Extract assessment type
            responses=request.responses,
            demographics=request.client_demographics
        )
        
        # In production: Update AssessmentAdministration record
        # Update status to 'completed'
        # Save scores and interpretation
        
        return {
            "administration_id": request.administration_id,
            "assessment_id": result.assessment_id,
            "client_id": "client_123",  # From request context
            "total_score": result.total_score,
            "subscale_scores": result.subscale_scores,
            "severity_level": result.severity_level,
            "interpretation": result.interpretation,
            "clinical_significance": result.clinical_significance,
            "recommendations": result.recommendations,
            "completed_at": result.scored_at
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing assessment: {str(e)}"
        )


# ============================================================================
# Results Retrieval Endpoints
# ============================================================================

@router.get("/results/{administration_id}", response_model=AssessmentResultResponse)
async def get_assessment_results(administration_id: str):
    """
    Retrieve results for a completed assessment.
    
    **Returns:**
    Assessment results including scores and interpretation
    """
    # In production: Query AssessmentAdministration
    
    # Mock response
    return {
        "administration_id": administration_id,
        "assessment_id": "phq9",
        "client_id": "client_123",
        "total_score": 12.0,
        "subscale_scores": {},
        "severity_level": "Moderate",
        "interpretation": "Client shows moderate depression symptoms.",
        "clinical_significance": "moderate",
        "recommendations": [
            "Psychotherapy recommended",
            "Consider medication evaluation"
        ],
        "completed_at": datetime.utcnow().isoformat()
    }


@router.get("/client/{client_id}/history")
async def get_client_assessment_history(
    client_id: str,
    assessment_id: Optional[str] = None,
    limit: int = 50
):
    """
    Get assessment history for a client.
    
    **Query Parameters:**
    - assessment_id: Filter by specific assessment
    - limit: Number of records to return
    
    **Returns:**
    List of assessment administrations with scores over time
    """
    # In production: Query AssessmentAdministration filtered by client_id
    
    # Mock response
    history = [
        {
            "administration_id": f"admin_{i}",
            "assessment_id": assessment_id or "phq9",
            "administration_date": f"2024-{i:02d}-01",
            "total_score": 15 - i,
            "severity_level": "Moderate" if 15-i > 10 else "Mild",
            "status": "completed"
        }
        for i in range(1, min(limit, 6))
    ]
    
    return {
        "client_id": client_id,
        "total_assessments": len(history),
        "assessments": history
    }


@router.get("/client/{client_id}/progress")
async def get_client_progress_chart(
    client_id: str,
    assessment_id: str
):
    """
    Get progress data for charting.
    
    **Returns:**
    Time series data suitable for frontend charts
    """
    # Mock progress data
    progress_data = {
        "client_id": client_id,
        "assessment_id": assessment_id,
        "data_points": [
            {"date": "2024-01-01", "score": 18, "severity": "Moderate"},
            {"date": "2024-02-01", "score": 15, "severity": "Moderate"},
            {"date": "2024-03-01", "score": 12, "severity": "Moderate"},
            {"date": "2024-04-01", "score": 9, "severity": "Mild"},
            {"date": "2024-05-01", "score": 7, "severity": "Mild"}
        ],
        "baseline_score": 18,
        "current_score": 7,
        "change": -11,
        "percent_change": -61.1,
        "trend": "improving"
    }
    
    return progress_data


# ============================================================================
# Batch Operations
# ============================================================================

@router.post("/batch/score")
async def batch_score_assessments(
    assessments: List[CompleteAssessmentRequest]
):
    """
    Score multiple assessments in batch.
    
    **Use case:** Batch processing for research or reporting
    
    **Returns:**
    List of assessment results
    """
    results = []
    
    for assessment in assessments:
        try:
            result = scorer.score_assessment(
                assessment_id=assessment.administration_id.split('_')[0],
                responses=assessment.responses,
                demographics=assessment.client_demographics
            )
            results.append({
                "administration_id": assessment.administration_id,
                "success": True,
                "result": result.to_dict()
            })
        except Exception as e:
            results.append({
                "administration_id": assessment.administration_id,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_processed": len(assessments),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/scoring-rules/{assessment_id}")
async def get_scoring_rules(assessment_id: str):
    """
    Get scoring rules and interpretation guidelines.
    
    **Returns:**
    Cutoffs, severity levels, and clinical recommendations
    """
    # Scoring rules by assessment
    rules = {
        "phq9": {
            "total_range": [0, 27],
            "cutoffs": [
                {"range": [0, 4], "severity": "None-Minimal", "clinical_sig": "none"},
                {"range": [5, 9], "severity": "Mild", "clinical_sig": "mild"},
                {"range": [10, 14], "severity": "Moderate", "clinical_sig": "moderate"},
                {"range": [15, 19], "severity": "Moderately Severe", "clinical_sig": "severe"},
                {"range": [20, 27], "severity": "Severe", "clinical_sig": "severe"}
            ],
            "special_items": {
                "item_9": "Suicide risk - requires immediate assessment if >0"
            }
        },
        "gad7": {
            "total_range": [0, 21],
            "cutoffs": [
                {"range": [0, 4], "severity": "Minimal", "clinical_sig": "none"},
                {"range": [5, 9], "severity": "Mild", "clinical_sig": "mild"},
                {"range": [10, 14], "severity": "Moderate", "clinical_sig": "moderate"},
                {"range": [15, 21], "severity": "Severe", "clinical_sig": "severe"}
            ]
        }
    }
    
    if assessment_id not in rules:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scoring rules not available for {assessment_id}"
        )
    
    return rules[assessment_id]


@router.get("/health")
async def health_check():
    """Health check for assessment service."""
    return {
        "status": "healthy",
        "service": "Assessment Service",
        "scoring_engine": "operational",
        "available_assessments": len(scorer.scoring_methods),
        "timestamp": datetime.utcnow().isoformat()
    }


# Integration with main FastAPI app
# Add to main.py:
"""
from app.api.routes import assessment_routes

app.include_router(assessment_routes.router)
"""

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(
        title="PsychSync Assessment API",
        description="Clinical assessment administration and scoring",
        version="1.0.0"
    )
    
    app.include_router(router)
    
    print("Starting Assessment API server...")
    print("API docs: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/api/v1/assessments/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)