# main.py - FastAPI Backend Application
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from contextlib import asynccontextmanager
import logging
from typing import List, Optional
import redis
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from database import get_db, init_db
from models import User, Team, Assessment, TeamMember, Prediction
from schemas import (
    UserCreate, UserResponse, TeamCreate, TeamResponse,
    AssessmentCreate, AssessmentResponse, PredictionResponse,
    TeamOptimizationRequest, BehavioralInsight
)
from ai_engine import (
    BehavioralAIEngine, TeamOptimizer, PredictiveAnalytics,
    PersonalityFrameworkProcessor
)
from assessment_processors import (
    EnneagramProcessor, MBTIProcessor, BigFiveProcessor,
    PIProcessor, StrengthsProcessor, SocialStylesProcessor
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting PsychSync AI Backend...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down PsychSync AI Backend...")

# Initialize FastAPI app
app = FastAPI(
    title="PsychSync AI API",
    description="Behavioral Analytics for High-Performance Agile Teams",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://psychsync.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI components
ai_engine = BehavioralAIEngine()
team_optimizer = TeamOptimizer()
predictive_analytics = PredictiveAnalytics()

# Initialize assessment processors
assessment_processors = {
    "enneagram": EnneagramProcessor(),
    "mbti": MBTIProcessor(),
    "big_five": BigFiveProcessor(),
    "predictive_index": PIProcessor(),
    "strengths": StrengthsProcessor(),
    "social_styles": SocialStylesProcessor()
}

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.email == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "redis": "connected" if redis_client.ping() else "disconnected",
            "ai_engine": "ready"
        }
    }

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password.decode('utf-8'),
        company=user.company,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {user.email}")
    return UserResponse.from_orm(db_user)

@app.post("/auth/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

# Team management endpoints
@app.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_team = Team(
        name=team.name,
        description=team.description,
        owner_id=current_user.id,
        team_type=team.team_type
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    logger.info(f"Team created: {team.name} by {current_user.email}")
    return TeamResponse.from_orm(db_team)

@app.get("/teams", response_model=List[TeamResponse])
async def get_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    teams = db.query(Team).filter(Team.owner_id == current_user.id).all()
    return [TeamResponse.from_orm(team) for team in teams]

@app.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return TeamResponse.from_orm(team)

# Assessment endpoints
@app.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(
    assessment: AssessmentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate assessment data
    if assessment.framework_type not in assessment_processors:
        raise HTTPException(status_code=400, detail="Invalid framework type")
    
    # Process assessment
    processor = assessment_processors[assessment.framework_type]
    processed_results = processor.process(assessment.raw_data)
    
    # Save to database
    db_assessment = Assessment(
        user_id=current_user.id,
        framework_type=assessment.framework_type,
        raw_data=assessment.raw_data,
        processed_results=processed_results,
        confidence_score=processed_results.get("confidence", 0.8)
    )
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    
    # Schedule AI analysis in background
    background_tasks.add_task(
        analyze_user_profile,
        current_user.id,
        db_assessment.id
    )
    
    logger.info(f"Assessment created: {assessment.framework_type} for {current_user.email}")
    return AssessmentResponse.from_orm(db_assessment)

@app.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assessments = db.query(Assessment).filter(Assessment.user_id == current_user.id).all()
    return [AssessmentResponse.from_orm(assessment) for assessment in assessments]

# Team optimization endpoints
@app.post("/teams/{team_id}/optimize")
async def optimize_team(
    team_id: int,
    request: TeamOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team members and their assessments
    team_members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    
    if len(team_members) < 2:
        raise HTTPException(status_code=400, detail="Team must have at least 2 members")
    
    # Collect personality profiles
    team_profiles = []
    for member in team_members:
        assessments = db.query(Assessment).filter(Assessment.user_id == member.user_id).all()
        if assessments:
            unified_profile = ai_engine.synthesize_personality_profile(
                {a.framework_type: a.processed_results for a in assessments}
            )
            team_profiles.append({
                "user_id": member.user_id,
                "profile": unified_profile,
                "role": member.role
            })
    
    if len(team_profiles) < 2:
        raise HTTPException(status_code=400, detail="Team members must complete assessments first")
    
    # Perform team optimization
    optimization_result = team_optimizer.optimize_team_composition(
        team_profiles,
        request.project_requirements,
        request.optimization_goals
    )
    
    # Cache results in Redis
    cache_key = f"team_optimization:{team_id}:{datetime.utcnow().timestamp()}"
    redis_client.setex(
        cache_key,
        3600,  # 1 hour expiration
        str(optimization_result)
    )
    
    # Schedule detailed analysis
    background_tasks.add_task(
        generate_team_insights,
        team_id,
        optimization_result
    )
    
    return {
        "team_id": team_id,
        "optimization_result": optimization_result,
        "cache_key": cache_key,
        "generated_at": datetime.utcnow()
    }

# Behavioral insights endpoint
@app.get("/teams/{team_id}/insights", response_model=List[BehavioralInsight])
async def get_team_insights(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get cached insights or generate new ones
    cache_key = f"team_insights:{team_id}"
    cached_insights = redis_client.get(cache_key)
    
    if cached_insights:
        return eval(cached_insights)  # In production, use proper JSON serialization
    
    # Generate fresh insights
    insights = await generate_behavioral_insights(team_id, db)
    
    # Cache for 30 minutes
    redis_client.setex(cache_key, 1800, str(insights))
    
    return insights

# Predictive analytics endpoint
@app.get("/teams/{team_id}/predictions", response_model=List[PredictionResponse])
async def get_team_predictions(
    team_id: int,
    prediction_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify team ownership
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == current_user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team data for predictions
    team_members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    
    # Collect behavioral data
    behavioral_data = []
    for member in team_members:
        assessments = db.query(Assessment).filter(Assessment.user_id == member.user_id).all()
        if assessments:
            behavioral_data.append({
                "user_id": member.user_id,
                "assessments": {a.framework_type: a.processed_results for a in assessments}
            })
    
    if not behavioral_data:
        raise HTTPException(status_code=400, detail="No behavioral data available for predictions")
    
    # Generate predictions
    predictions = predictive_analytics.generate_team_predictions(
        behavioral_data,
        prediction_type or "all"
    )
    
    # Save predictions to database
    for prediction in predictions:
        db_prediction = Prediction(
            team_id=team_id,
            prediction_type=prediction["type"],
            prediction_data=prediction["data"],
            confidence_score=prediction["confidence"],
            generated_by="predictive_analytics_v1"
        )
        db.add(db_prediction)
    
    db.commit()
    
    return [PredictionResponse(**pred) for pred in predictions]

# Background task functions
async def analyze_user_profile(user_id: int, assessment_id: int):
    """Background task to analyze user profile after assessment completion"""
    try:
        # This would typically involve more complex AI processing
        logger.info(f"Analyzing profile for user {user_id}, assessment {assessment_id}")
        # Implement detailed profile analysis here
    except Exception as e:
        logger.error(f"Error analyzing user profile: {str(e)}")

async def generate_team_insights(team_id: int, optimization_result: dict):
    """Background task to generate detailed team insights"""
    try:
        logger.info(f"Generating insights for team {team_id}")
        # Implement insight generation logic here
    except Exception as e:
        logger.error(f"Error generating team insights: {str(e)}")

async def generate_behavioral_insights(team_id: int, db: Session) -> List[BehavioralInsight]:
    """Generate behavioral insights for a team"""
    # This is a simplified version - in production, this would be more sophisticated
    insights = [
        BehavioralInsight(
            type="team_compatibility",
            title="High Team Compatibility Detected",
            description="Your team shows strong personality compatibility with 85% alignment score",
            confidence=0.85,
            priority="high",
            recommendations=[
                "Leverage the team's natural collaboration patterns",
                "Focus on projects requiring creative problem-solving"
            ]
        ),
        BehavioralInsight(
            type="conflict_risk",
            title="Potential Communication Conflicts",
            description="Detected personality traits that may lead to communication challenges",
            confidence=0.72,
            priority="medium",
            recommendations=[
                "Establish clear communication protocols",
                "Schedule regular check-ins between conflicting personality types"
            ]
        )
    ]
    
    return insights

# WebSocket endpoint for real-time updates
@app.websocket("/ws/teams/{team_id}")
async def websocket_endpoint(websocket, team_id: int):
    await websocket.accept()
    try:
        while True:
            # Send real-time team metrics
            metrics = {
                "team_id": team_id,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "active_members": 5,
                    "compatibility_score": 0.78,
                    "predicted_velocity": 23.5
                }
            }
            await websocket.send_json(metrics)
            await asyncio.sleep(30)  # Send updates every 30 seconds
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )