# ============================================================================
# FILE 12: app/tasks/psychometric_tasks.py
# Background tasks for psychometric processing
# ============================================================================

from celery import shared_task
from typing import Dict, List
from datetime import datetime, timedelta
import logging
from app.services.psychometric_service import PsychometricService
from app.db.session import get_db
from app.db.models.psychometric_session import PsychometricSession, ProgressReport

logger = logging.getLogger(__name__)

@shared_task(name="analyze_session_async")
def analyze_session_async(
    session_text: str,
    client_id: str,
    session_id: str,
    session_date: str
):
    """Async task to analyze therapy session"""
    try:
        service = PsychometricService()
        
        result = service.analyze_client_session(
            session_text,
            client_id,
            session_id,
            datetime.fromisoformat(session_date)
        )
        
        # Store results in database
        with get_db() as db:
            session = PsychometricSession(
                client_id=client_id,
                session_date=datetime.fromisoformat(session_date),
                session_type="therapy",
                sentiment_analysis=result["sentiment_analysis"],
                emotion_analysis=result["emotion_analysis"],
                psycholinguistic_markers=result["psycholinguistic_markers"],
                linguistic_features=result["linguistic_features"],
                key_insights=result["key_insights"],
                red_flags=result["red_flags"]
            )
            db.add(session)
            db.commit()
        
        logger.info(f"Session analysis completed for client {client_id}")
        return result
        
    except Exception as e:
        logger.error(f"Session analysis task failed: {e}")
        raise

@shared_task(name="generate_progress_report_async")
def generate_progress_report_async(
    client_id: str,
    start_date: str,
    end_date: str
):
    """Async task to generate progress report"""
    try:
        service = PsychometricService()
        
        # Fetch session analyses from database
        with get_db() as db:
            sessions = db.query(PsychometricSession).filter(
                PsychometricSession.client_id == client_id,
                PsychometricSession.session_date >= datetime.fromisoformat(start_date),
                PsychometricSession.session_date <= datetime.fromisoformat(end_date)
            ).all()
        
        # Convert to dict format
        session_analyses = [
            {
                "session_id": str(s.id),
                "session_date": s.session_date.isoformat(),
                "sentiment_analysis": s.sentiment_analysis,
                "emotion_analysis": s.emotion_analysis
            }
            for s in sessions
        ]
        
        # Generate report
        report = service.generate_client_progress_report(
            client_id,
            session_analyses,
            datetime.fromisoformat(start_date),
            datetime.fromisoformat(end_date)
        )
        
        # Store report
        with get_db() as db:
            progress_report = ProgressReport(
                client_id=client_id,
                start_date=datetime.fromisoformat(start_date),
                end_date=datetime.fromisoformat(end_date),
                trend_analysis=report["trend_analysis"],
                cyclical_patterns=report["cyclical_patterns"],
                emotional_state=report["emotional_state"],
                anomalies=report["anomalies"],
                progress_level=report["progress_level"],
                recommendations=report["recommendations"],
                session_count=len(session_analyses)
            )
            db.add(progress_report)
            db.commit()
        
        logger.info(f"Progress report generated for client {client_id}")
        return report
        
    except Exception as e:
        logger.error(f"Progress report task failed: {e}")
        raise

@shared_task(name="detect_anomalies_batch")
def detect_anomalies_batch(client_ids: List[str]):
    """Batch anomaly detection for multiple clients"""
    try:
        service = PsychometricService()
        results = {}
        
        for client_id in client_ids:
            # Fetch recent sessions
            with get_db() as db:
                sessions = db.query(PsychometricSession).filter(
                    PsychometricSession.client_id == client_id,
                    PsychometricSession.session_date >= datetime.utcnow() - timedelta(days=30)
                ).all()
            
            if len(sessions) < 10:
                continue
            
            # Prepare data points
            data_points = [
                {
                    "timestamp": s.session_date.isoformat(),
                    "sentiment": s.sentiment_analysis.get("overall_score", 0),
                    "dominant_emotion": s.emotion_analysis.get("dominant_emotion", "neutral")
                }
                for s in sessions
            ]
            
            # Detect anomalies
            anomalies = service.anomaly_detector.detect_anomalies(
                data_points,
                ["sentiment"]
            )
            
            if anomalies.get("anomalies_detected", 0) > 0:
                results[client_id] = anomalies
                logger.warning(f"Anomalies detected for client {client_id}: {anomalies['anomalies_detected']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Batch anomaly detection failed: {e}")
        raise


