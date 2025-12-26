"""
Email Connector Service API Endpoints
Focused on email integration, communication analytics, and email-based assessments
Separate from other services with dedicated email functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from app.api.v1.deps import get_current_user, get_db
from app.services.email_connector_service import EmailConnectorService
from app.services.email_connection_service import EmailConnectionService
from app.services.email_fetching_service import EmailFetchingService
from app.services.email_analytics_service import EmailAnalyticsService
from app.schemas.email import (
    EmailConnectionRequest,
    EmailConnectionResponse,
    EmailAnalyticsRequest,
    EmailAnalyticsResponse,
    EmailAssessmentRequest,
    EmailAssessmentResponse,
    EmailSyncRequest,
    EmailSyncResponse,
    EmailConfigurationRequest,
    EmailConfigurationResponse
)
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Email Connector Services
email_connector = EmailConnectorService()
email_connection = EmailConnectionService()
email_fetching = EmailFetchingService()
email_analytics = EmailAnalyticsService()


@router.post("/connection/setup", response_model=EmailConnectionResponse)
async def setup_email_connection(
    request: EmailConnectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Setup email connection for integration with email providers
    Supports Gmail, Outlook, Exchange, and other IMAP/POP3 providers
    """
    try:
        # Validate email connection parameters
        validation_result = await email_connection.validate_connection_parameters(
            provider=request.provider,
            email_address=request.email_address,
            connection_parameters=request.connection_parameters
        )

        if not validation_result["valid"]:
            return EmailConnectionResponse(
                success=False,
                provider=request.provider,
                email_address=request.email_address,
                connection_status="failed",
                error_message=validation_result["error"],
                setup_completed=False
            )

        # Test email connection
        connection_test = await email_connection.test_email_connection(
            provider=request.provider,
            connection_parameters=request.connection_parameters
        )

        if not connection_test["success"]:
            return EmailConnectionResponse(
                success=False,
                provider=request.provider,
                email_address=request.email_address,
                connection_status="failed",
                error_message=connection_test["error"],
                setup_completed=False
            )

        # Store email connection configuration (encrypted)
        connection_config = await email_connection.store_connection_configuration(
            user_id=current_user["id"],
            provider=request.provider,
            email_address=request.email_address,
            connection_parameters=request.connection_parameters,
            permissions=request.permissions,
            sync_settings=request.sync_settings
        )

        # Initialize email syncing if requested
        if request.auto_sync_enabled:
            sync_initialization = await email_fetching.initialize_email_sync(
                user_id=current_user["id"],
                connection_id=connection_config["connection_id"],
                sync_settings=request.sync_settings
            )
            connection_config["sync_status"] = sync_initialization

        return EmailConnectionResponse(
            success=True,
            provider=request.provider,
            email_address=request.email_address,
            connection_id=connection_config["connection_id"],
            connection_status="connected",
            sync_enabled=request.auto_sync_enabled,
            permissions_granted=request.permissions,
            setup_completed=True,
            setup_completed_at=datetime.utcnow(),
            next_sync=connection_config.get("next_sync"),
            capabilities=await email_connection.get_provider_capabilities(request.provider)
        )

    except Exception as e:
        logger.error(f"Email connection setup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email connection setup failed"
        )


@router.post("/analytics/communication", response_model=EmailAnalyticsResponse)
async def analyze_email_communication(
    request: EmailAnalyticsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Analyze email communication patterns and behaviors
    Provides insights into communication style, responsiveness, and engagement
    """
    try:
        # Get email data for analysis
        email_data = await email_fetching.get_email_data(
            user_id=current_user["id"],
            date_range=request.date_range,
            email_filters=request.email_filters,
            analysis_categories=request.analysis_categories
        )

        # Analyze communication patterns
        communication_analysis = {}
        for category in request.analysis_categories:
            if category == "communication_style":
                analysis = await email_analytics.analyze_communication_style(email_data)
                communication_analysis["communication_style"] = analysis

            elif category == "responsiveness":
                analysis = await email_analytics.analyze_responsiveness_patterns(email_data)
                communication_analysis["responsiveness"] = analysis

            elif category == "engagement":
                analysis = await email_analytics.analyze_engagement_patterns(email_data)
                communication_analysis["engagement"] = analysis

            elif category == "network_analysis":
                analysis = await email_analytics.analyze_communication_network(email_data)
                communication_analysis["network_analysis"] = analysis

            elif category == "sentiment_analysis":
                analysis = await email_analytics.analyze_sentiment_patterns(email_data)
                communication_analysis["sentiment_analysis"] = analysis

            elif category == "topic_analysis":
                analysis = await email_analytics.analyze_topic_patterns(email_data)
                communication_analysis["topic_analysis"] = analysis

            elif category == "time_patterns":
                analysis = await email_analytics.analyze_temporal_patterns(email_data)
                communication_analysis["time_patterns"] = analysis

            elif category == "collaboration":
                analysis = await email_analytics.analyze_collaboration_patterns(email_data)
                communication_analysis["collaboration"] = analysis

        # Generate communication insights
        communication_insights = await email_analytics.generate_communication_insights(
            communication_analysis, request.analysis_categories
        )

        # Calculate communication metrics
        communication_metrics = await email_analytics.calculate_communication_metrics(
            email_data, communication_analysis
        )

        return EmailAnalyticsResponse(
            success=True,
            user_id=current_user["id"],
            analysis_period=request.date_range,
            analysis_categories=request.analysis_categories,
            total_emails_analyzed=len(email_data),
            communication_analysis=communication_analysis,
            communication_insights=communication_insights,
            communication_metrics=communication_metrics,
            communication_style_profile=await email_analytics.create_communication_profile(
                communication_analysis
            ),
            behavioral_indicators=await email_analytics.identify_behavioral_indicators(
                communication_analysis
            ),
            collaboration_patterns=communication_analysis.get("collaboration", {}),
            network_insights=communication_analysis.get("network_analysis", {}),
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Email analytics analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email analytics analysis failed"
        )


@router.post("/assessment/behavioral", response_model=EmailAssessmentResponse)
async def conduct_email_behavioral_assessment(
    request: EmailAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Conduct behavioral assessment based on email communication data
    Integrates with behavioral analysis to provide personality and behavior insights
    """
    try:
        # Get email data for assessment
        email_data = await email_fetching.get_assessment_email_data(
            user_id=current_user["id"],
            assessment_type=request.assessment_type,
            time_period=request.time_period,
            data_scope=request.data_scope
        )

        # Conduct behavioral assessment based on email patterns
        assessment_results = {}

        if request.assessment_type == "communication_effectiveness":
            results = await email_connector.assess_communication_effectiveness(email_data)
            assessment_results["communication_effectiveness"] = results

        elif request.assessment_type == "leadership_communication":
            results = await email_connector.assess_leadership_communication(email_data)
            assessment_results["leadership_communication"] = results

        elif request.assessment_type == "team_collaboration":
            results = await email_connector.assess_team_collaboration(email_data)
            assessment_results["team_collaboration"] = results

        elif request.assessment_type == "customer_service":
            results = await email_connector.assess_customer_service_communication(email_data)
            assessment_results["customer_service"] = results

        elif request.assessment_type == "conflict_resolution":
            results = await email_connector.assess_conflict_resolution_patterns(email_data)
            assessment_results["conflict_resolution"] = results

        # Integrate with behavioral analysis
        behavioral_integration = await email_connector.integrate_with_behavioral_analysis(
            email_data, assessment_results
        )

        # Generate assessment recommendations
        assessment_recommendations = await email_connector.generate_assessment_recommendations(
            assessment_results, behavioral_integration
        )

        # Calculate assessment scores
        assessment_scores = await email_connector.calculate_assessment_scores(
            assessment_results, request.assessment_type
        )

        return EmailAssessmentResponse(
            success=True,
            user_id=current_user["id"],
            assessment_type=request.assessment_type,
            time_period=request.time_period,
            data_scope=request.data_scope,
            emails_analyzed=len(email_data),
            assessment_results=assessment_results,
            behavioral_integration=behavioral_integration,
            assessment_scores=assessment_scores,
            assessment_recommendations=assessment_recommendations,
            development_areas=await email_connector.identify_development_areas(assessment_results),
            strengths_identified=await email_connector.identify_communication_strengths(
                assessment_results
            ),
            behavioral_correlations=behavioral_integration.get("correlations", {}),
            assessed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Email behavioral assessment failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email behavioral assessment failed"
        )


@router.post("/sync/manual", response_model=EmailSyncResponse)
async def trigger_manual_email_sync(
    request: EmailSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Trigger manual email synchronization
    Force immediate sync of email data for analytics and assessment
    """
    try:
        # Validate email connection
        connection_status = await email_connection.get_connection_status(
            user_id=current_user["id"],
            connection_id=request.connection_id
        )

        if not connection_status["connected"]:
            raise HTTPException(
                status_code=400,
                detail="Email connection not established"
            )

        # Start email sync process
        sync_task = await email_fetching.start_manual_sync(
            user_id=current_user["id"],
            connection_id=request.connection_id,
            sync_options=request.sync_options
        )

        # Add background task for processing
        background_tasks.add_task(
            email_fetching.process_email_sync,
            user_id=current_user["id"],
            sync_task_id=sync_task["task_id"],
            sync_options=request.sync_options
        )

        return EmailSyncResponse(
            success=True,
            user_id=current_user["id"],
            connection_id=request.connection_id,
            sync_task_id=sync_task["task_id"],
            sync_status="started",
            sync_options=request.sync_options,
            estimated_duration=await email_fetching.estimate_sync_duration(request.sync_options),
            sync_started_at=datetime.utcnow(),
            last_sync=connection_status.get("last_sync"),
            emails_to_sync=sync_task.get("emails_pending", 0)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual email sync failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Manual email sync failed"
        )


@router.get("/sync/status/{connection_id}")
async def get_email_sync_status(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get current email sync status
    Monitor progress of email synchronization
    """
    try:
        sync_status = await email_fetching.get_sync_status(
            user_id=current_user["id"],
            connection_id=connection_id
        )

        return {
            "success": True,
            "connection_id": connection_id,
            "sync_status": sync_status,
            "last_checked": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get email sync status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve email sync status"
        )


@router.post("/configuration/update", response_model=EmailConfigurationResponse)
async def update_email_configuration(
    request: EmailConfigurationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Update email connector configuration
    Modify sync settings, permissions, and analysis preferences
    """
    try:
        # Update configuration
        config_update = await email_connection.update_configuration(
            user_id=current_user["id"],
            connection_id=request.connection_id,
            configuration_updates=request.configuration_updates
        )

        # Apply new sync settings if updated
        if "sync_settings" in request.configuration_updates:
            sync_update = await email_fetching.update_sync_settings(
                user_id=current_user["id"],
                connection_id=request.connection_id,
                new_sync_settings=request.configuration_updates["sync_settings"]
            )
            config_update["sync_update"] = sync_update

        return EmailConfigurationResponse(
            success=True,
            connection_id=request.connection_id,
            configuration_updates_applied=request.configuration_updates,
            updated_configuration=config_update,
            configuration_updated_at=datetime.utcnow(),
            next_effective_date=config_update.get("next_effective_date"),
            requires_reauth=config_update.get("requires_reauth", False)
        )

    except Exception as e:
        logger.error(f"Email configuration update failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email configuration update failed"
        )


@router.get("/connections")
async def get_email_connections(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all email connections for the user
    List configured email accounts and their status
    """
    try:
        connections = await email_connection.get_user_connections(current_user["id"])

        # Get status for each connection
        connection_statuses = []
        for connection in connections:
            status = await email_connection.get_connection_status(
                user_id=current_user["id"],
                connection_id=connection["connection_id"]
            )
            connection_statuses.append({
                **connection,
                "status": status
            })

        return {
            "success": True,
            "user_id": current_user["id"],
            "total_connections": len(connection_statuses),
            "connections": connection_statuses,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get email connections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve email connections"
        )


@router.delete("/connection/{connection_id}")
async def disconnect_email_account(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Disconnect email account and remove data
    Securely remove email connection and associated data
    """
    try:
        # Stop any active sync processes
        await email_fetching.stop_sync_processes(
            user_id=current_user["id"],
            connection_id=connection_id
        )

        # Remove email data (if requested)
        data_removal = await email_fetching.remove_email_data(
            user_id=current_user["id"],
            connection_id=connection_id,
            remove_data=request.remove_data if hasattr(request, 'remove_data') else False
        )

        # Delete connection configuration
        connection_removal = await email_connection.delete_connection(
            user_id=current_user["id"],
            connection_id=connection_id
        )

        return {
            "success": True,
            "connection_id": connection_id,
            "disconnected_at": datetime.utcnow(),
            "data_removed": data_removal["data_removed"],
            "files_deleted": data_removal["files_deleted"],
            "configuration_deleted": connection_removal["deleted"]
        }

    except Exception as e:
        logger.error(f"Email disconnection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Email disconnection failed"
        )


@router.get("/analytics/dashboard")
async def get_email_analytics_dashboard(
    time_period: str = Query(default="30d", description="Time period for dashboard data"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get email analytics dashboard data
    Comprehensive overview of email communication patterns and insights
    """
    try:
        # Get dashboard data
        dashboard_data = await email_analytics.get_dashboard_data(
            user_id=current_user["id"],
            time_period=time_period
        )

        return {
            "success": True,
            "user_id": current_user["id"],
            "time_period": time_period,
            "dashboard_data": dashboard_data,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get email analytics dashboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve email analytics dashboard"
        )


@router.get("/providers/available", dependencies=[Depends(get_current_user)])
async def get_available_email_providers():
    """
    Get list of available email providers and their capabilities
    """
    try:
        providers = {
            "gmail": {
                "name": "Gmail",
                "auth_type": "OAuth2",
                "api_support": True,
                "features": ["read", "send", "labels", "search", "filters"],
                "limitations": ["API_rate_limits", "scope_permissions"],
                "setup_difficulty": "Easy"
            },
            "outlook": {
                "name": "Microsoft Outlook",
                "auth_type": "OAuth2",
                "api_support": True,
                "features": ["read", "send", "folders", "search", "calendar_integration"],
                "limitations": ["API_rate_limits", "enterprise_policies"],
                "setup_difficulty": "Easy"
            },
            "exchange": {
                "name": "Microsoft Exchange",
                "auth_type": "Basic/OAuth2",
                "api_support": True,
                "features": ["read", "send", "folders", "search", "calendar", "contacts"],
                "limitations": ["server_configuration", "firewall_restrictions"],
                "setup_difficulty": "Advanced"
            },
            "imap": {
                "name": "Generic IMAP/POP3",
                "auth_type": "Basic",
                "api_support": False,
                "features": ["read", "search", "folders"],
                "limitations": ["no_send_capability", "basic_features_only"],
                "setup_difficulty": "Intermediate"
            }
        }

        return {
            "success": True,
            "providers": providers,
            "general_capabilities": [
                "Email reading and parsing",
                "Communication pattern analysis",
                "Sentiment analysis",
                "Response time tracking",
                "Network analysis",
                "Topic extraction"
            ],
            "security_features": [
                "OAuth2 authentication",
                "Encrypted credential storage",
                "Data privacy protection",
                "User consent management",
                "Secure data transmission"
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get available email providers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available email providers"
        )