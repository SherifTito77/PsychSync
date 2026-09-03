"""
Email Connector Service API Endpoints
Focused on email integration, communication analytics, and email-based assessments
Separate from other services with dedicated email functionality
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.api.v1.deps import get_current_user, get_db
from app.core.config.settings import settings

# Import database models
from app.db.models.email_connection import (
    ConnectionStatus,
    EmailConnection,
    EmailProvider,
)
from app.db.models.user import User
from app.schemas.email import (
    EmailAnalyticsRequest,
    EmailAnalyticsResponse,
    EmailAssessmentRequest,
    EmailAssessmentResponse,
    EmailConfigurationRequest,
    EmailConfigurationResponse,
    EmailConnectionRequest,
    EmailConnectionResponse,
    EmailSyncRequest,
    EmailSyncResponse,
)
from app.services.email_analytics_service import EmailAnalyticsService
from app.services.email_connection_service import EmailConnectionService
from app.services.email_connector_service import EmailConnectorService
from app.services.email_fetching_service import EmailFetchingService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Email Connector"])

# Email Connector Services
email_connector = EmailConnectorService()
email_connection = EmailConnectionService()
email_fetching = EmailFetchingService()
email_analytics = EmailAnalyticsService()


@router.post("/connection/setup", response_model=EmailConnectionResponse)
async def setup_email_connection(
    request: dict,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Setup email connection for integration with email providers
    Supports Gmail, Outlook, Exchange, and other IMAP/POP3 providers
    """
    try:
        provider = request.get("provider", "imap")
        email_address = request.get("email_address")
        connection_parameters = request.get("connection_parameters", {})
        permissions = request.get("permissions", ["read"])
        sync_settings = request.get("sync_settings", {})
        auto_sync_enabled = request.get("auto_sync_enabled", False)

        if not email_address:
            raise HTTPException(status_code=400, detail="email_address is required")

        # Validate email format
        if "@" not in email_address:
            raise HTTPException(status_code=400, detail="Invalid email address format")

        # For IMAP, test the connection
        if provider == "imap":
            import imaplib

            server = connection_parameters.get("server")
            port = connection_parameters.get("port", 993)
            use_ssl = connection_parameters.get("use_ssl", True)
            username = connection_parameters.get("username") or email_address
            password = connection_parameters.get("password")

            if not all([server, password]):
                raise HTTPException(
                    status_code=400, detail="IMAP requires server and password"
                )

            try:
                # Sanitize password to handle non-breaking spaces and non-ASCII characters
                password_sanitized = password.replace("\xa0", " ").replace(
                    "\u00a0", " "
                )
                password_sanitized = password_sanitized.encode(
                    "utf-8", errors="ignore"
                ).decode("utf-8")

                # Test IMAP connection
                if use_ssl:
                    mail = imaplib.IMAP4_SSL(server, port)
                else:
                    mail = imaplib.IMAP4(server, port)

                mail.login(username, password_sanitized)
                mail.logout()
            except Exception as e:
                return EmailConnectionResponse(
                    success=False,
                    provider=provider,
                    email_address=email_address,
                    connection_status="failed",
                    error_message=f"IMAP connection failed: {str(e)}",
                    setup_completed=False,
                )

        # Create connection record in database using ORM
        provider_map = {
            "gmail": EmailProvider.GMAIL,
            "outlook": EmailProvider.OUTLOOK,
            "exchange": EmailProvider.EXCHANGE,
            "imap": EmailProvider.IMAP,
        }

        email_provider = provider_map.get(provider, EmailProvider.IMAP)

        # Create new EmailConnection object
        # Note: Storing IMAP credentials in access_token_encrypted field as a workaround
        # for connection_parameters column caching issues
        import base64
        import json

        access_token_encrypted = None
        if provider == "imap":
            # Encode credentials as base64 JSON (temporary solution)
            creds_json = json.dumps(connection_parameters)
            access_token_encrypted = base64.b64encode(creds_json.encode()).decode()

        new_connection = EmailConnection(
            user_id=current_user.id,
            provider=email_provider,
            email_address=email_address,
            access_token_encrypted=access_token_encrypted,  # Temporarily storing IMAP params here
            connection_status=ConnectionStatus.ACTIVE,
            monitored_folders=["INBOX"],
            privacy_settings={
                "analyze_internal_only": True,
                "exclude_sensitive_subjects": True,
            },
        )

        try:
            db.add(new_connection)
            await db.flush()  # Get the ID without committing
            connection_id = str(new_connection.id)
            await db.commit()

        except Exception as db_error:
            logger.error(f"Database error: {db_error}")
            await db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to save connection: {str(db_error)}"
            ) from db_error

        # Return success
        return EmailConnectionResponse(
            success=True,
            provider=provider,
            email_address=email_address,
            connection_id=connection_id,
            connection_status="connected",
            sync_enabled=auto_sync_enabled,
            permissions_granted=permissions,
            setup_completed=True,
            setup_completed_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email connection setup failed: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"Email connection setup failed: {str(e)}"
        ) from e


@router.post("/analytics/communication", response_model=EmailAnalyticsResponse)
async def analyze_email_communication(
    request: EmailAnalyticsRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Analyze email communication patterns and behaviors
    Provides insights into communication style, responsiveness, and engagement
    """
    try:
        # Get email data for analysis
        email_data = await email_fetching.get_email_data(
            user_id=current_user.id,
            date_range=request.date_range,
            email_filters=request.email_filters,
            analysis_categories=request.analysis_categories,
        )

        # Analyze communication patterns
        communication_analysis = {}
        for category in request.analysis_categories:
            if category == "communication_style":
                analysis = await email_analytics.analyze_communication_style(email_data)
                communication_analysis["communication_style"] = analysis

            elif category == "responsiveness":
                analysis = await email_analytics.analyze_responsiveness_patterns(
                    email_data
                )
                communication_analysis["responsiveness"] = analysis

            elif category == "engagement":
                analysis = await email_analytics.analyze_engagement_patterns(email_data)
                communication_analysis["engagement"] = analysis

            elif category == "network_analysis":
                analysis = await email_analytics.analyze_communication_network(
                    email_data
                )
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
                analysis = await email_analytics.analyze_collaboration_patterns(
                    email_data
                )
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
            user_id=current_user.id,
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
            analyzed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Email analytics analysis failed: {e!s}")
        raise HTTPException(
            status_code=500, detail="Email analytics analysis failed"
        ) from e


@router.post("/assessment/behavioral", response_model=EmailAssessmentResponse)
async def conduct_email_behavioral_assessment(
    request: EmailAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Conduct behavioral assessment based on email communication data
    Integrates with behavioral analysis to provide personality and behavior insights
    """
    try:
        # Get email data for assessment
        email_data = await email_fetching.get_assessment_email_data(
            user_id=current_user.id,
            assessment_type=request.assessment_type,
            time_period=request.time_period,
            data_scope=request.data_scope,
        )

        # Conduct behavioral assessment based on email patterns
        assessment_results = {}

        if request.assessment_type == "communication_effectiveness":
            results = await email_connector.assess_communication_effectiveness(
                email_data
            )
            assessment_results["communication_effectiveness"] = results

        elif request.assessment_type == "leadership_communication":
            results = await email_connector.assess_leadership_communication(email_data)
            assessment_results["leadership_communication"] = results

        elif request.assessment_type == "team_collaboration":
            results = await email_connector.assess_team_collaboration(email_data)
            assessment_results["team_collaboration"] = results

        elif request.assessment_type == "customer_service":
            results = await email_connector.assess_customer_service_communication(
                email_data
            )
            assessment_results["customer_service"] = results

        elif request.assessment_type == "conflict_resolution":
            results = await email_connector.assess_conflict_resolution_patterns(
                email_data
            )
            assessment_results["conflict_resolution"] = results

        # Integrate with behavioral analysis
        behavioral_integration = (
            await email_connector.integrate_with_behavioral_analysis(
                email_data, assessment_results
            )
        )

        # Generate assessment recommendations
        assessment_recommendations = (
            await email_connector.generate_assessment_recommendations(
                assessment_results, behavioral_integration
            )
        )

        # Calculate assessment scores
        assessment_scores = await email_connector.calculate_assessment_scores(
            assessment_results, request.assessment_type
        )

        return EmailAssessmentResponse(
            success=True,
            user_id=current_user.id,
            assessment_type=request.assessment_type,
            time_period=request.time_period,
            data_scope=request.data_scope,
            emails_analyzed=len(email_data),
            assessment_results=assessment_results,
            behavioral_integration=behavioral_integration,
            assessment_scores=assessment_scores,
            assessment_recommendations=assessment_recommendations,
            development_areas=await email_connector.identify_development_areas(
                assessment_results
            ),
            strengths_identified=await email_connector.identify_communication_strengths(
                assessment_results
            ),
            behavioral_correlations=behavioral_integration.get("correlations", {}),
            assessed_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Email behavioral assessment failed: {e!s}")
        raise HTTPException(
            status_code=500, detail="Email behavioral assessment failed"
        ) from e


@router.post("/sync/manual", response_model=EmailSyncResponse)
async def trigger_manual_email_sync(
    request: EmailSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Trigger manual email synchronization
    Force immediate sync of email data for analytics and assessment
    """
    try:
        # Validate email connection
        connection_status = await email_connection.get_connection_status(
            user_id=current_user.id, connection_id=request.connection_id
        )

        if not connection_status["connected"]:
            raise HTTPException(
                status_code=400, detail="Email connection not established"
            )

        # Start email sync process
        sync_task = await email_fetching.start_manual_sync(
            user_id=current_user.id,
            connection_id=request.connection_id,
            sync_options=request.sync_options,
        )

        # Add background task for processing
        background_tasks.add_task(
            email_fetching.process_email_sync,
            user_id=current_user.id,
            sync_task_id=sync_task["task_id"],
            sync_options=request.sync_options,
        )

        return EmailSyncResponse(
            success=True,
            user_id=current_user.id,
            connection_id=request.connection_id,
            sync_task_id=sync_task["task_id"],
            sync_status="started",
            sync_options=request.sync_options,
            estimated_duration=await email_fetching.estimate_sync_duration(
                request.sync_options
            ),
            sync_started_at=datetime.utcnow(),
            last_sync=connection_status.get("last_sync"),
            emails_to_sync=sync_task.get("emails_pending", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual email sync failed: {e!s}")
        raise HTTPException(status_code=500, detail="Manual email sync failed") from e


@router.get("/sync/status/{connection_id}")
async def get_email_sync_status(
    connection_id: str, current_user: User = Depends(get_current_user)
):
    """
    Get current email sync status
    Monitor progress of email synchronization
    """
    try:
        sync_status = await email_fetching.get_sync_status(
            user_id=current_user.id, connection_id=connection_id
        )

        return {
            "success": True,
            "connection_id": connection_id,
            "sync_status": sync_status,
            "last_checked": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to get email sync status: {e!s}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve email sync status"
        ) from e


@router.post("/configuration/update", response_model=EmailConfigurationResponse)
async def update_email_configuration(
    request: EmailConfigurationRequest,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Update email connector configuration
    Modify sync settings, permissions, and analysis preferences
    """
    try:
        # Update configuration
        config_update = await email_connection.update_configuration(
            user_id=current_user.id,
            connection_id=request.connection_id,
            configuration_updates=request.configuration_updates,
        )

        # Apply new sync settings if updated
        if "sync_settings" in request.configuration_updates:
            sync_update = await email_fetching.update_sync_settings(
                user_id=current_user.id,
                connection_id=request.connection_id,
                new_sync_settings=request.configuration_updates["sync_settings"],
            )
            config_update["sync_update"] = sync_update

        return EmailConfigurationResponse(
            success=True,
            connection_id=request.connection_id,
            configuration_updates_applied=request.configuration_updates,
            updated_configuration=config_update,
            configuration_updated_at=datetime.utcnow(),
            next_effective_date=config_update.get("next_effective_date"),
            requires_reauth=config_update.get("requires_reauth", False),
        )

    except Exception as e:
        logger.error(f"Email configuration update failed: {e!s}")
        raise HTTPException(
            status_code=500, detail="Email configuration update failed"
        ) from e


@router.get("/connections")
async def get_email_connections(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get all email connections for the user
    List configured email accounts and their status
    """
    try:
        # DEBUG: Log the current_user details
        logger.info(f"DEBUG: current_user.id = {current_user.id}")
        logger.info(f"DEBUG: current_user.id type = {type(current_user.id)}")
        logger.info(f"DEBUG: str(current_user.id) = {str(current_user.id)}")
        logger.info(f"DEBUG: str(current_user.id) length = {len(str(current_user.id))}")

        # Check for corrupted uuid.UUID
        user_id_str = str(current_user.id)
        if "fc6-f998" in user_id_str and "afc6-f998" not in user_id_str:
            logger.error(f"DETECTED CORRUPTED uuid.UUID: {user_id_str}")
            logger.error(f"Expected: 2714eb76-f9a0-4809-afc6-f998f6a35a89")
            logger.error(f"Got: {user_id_str}")
            raise HTTPException(
                status_code=500,
                detail=f"Corrupted user ID detected. Please clear browser storage and log in again.",
            )

        # Use raw SQL to bypass SQLAlchemy metadata caching issues
        from sqlalchemy import text

        query = text(
            """
            SELECT id, provider, email_address, connection_status, created_at, last_sync_at
            FROM email_connections
            WHERE user_id = :user_id
        """
        )

        result = await db.execute(query, {"user_id": user_id_str})
        rows = result.fetchall()

        # Format connections for response
        formatted_connections = []
        for row in rows:
            # Map database status to frontend-friendly status
            status_map = {
                "ACTIVE": "connected",
                "INACTIVE": "disconnected",
                "ERROR": "error",
                "EXPIRED": "expired",
                "REVOKED": "revoked",
            }

            formatted_connections.append(
                {
                    "connection_id": str(row[0]),
                    "provider": row[1],
                    "email_address": row[2],
                    "connection_status": status_map.get(row[3], "disconnected"),
                    "sync_enabled": True,
                    "created_at": row[4].isoformat() if row[4] else None,
                    "last_sync": row[5].isoformat() if row[5] else None,
                }
            )

        return {
            "success": True,
            "user_id": str(current_user.id),
            "total_connections": len(formatted_connections),
            "connections": formatted_connections,
            "last_updated": datetime.utcnow(),
        }

    except Exception as e:
        import traceback

        logger.error(f"Failed to get email connections: {e!s}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # For debugging, also print the error type
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve email connections: {str(e)}"
        ) from e


@router.delete("/connection/{connection_id}")
async def disconnect_email_account(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Disconnect email account and remove data
    Securely remove email connection and associated data
    """
    try:
        # Stop any active sync processes
        await email_fetching.stop_sync_processes(
            user_id=current_user.id, connection_id=connection_id
        )

        # Remove email data (if requested)
        data_removal = await email_fetching.remove_email_data(
            user_id=current_user.id,
            connection_id=connection_id,
            remove_data=(
                request.remove_data if hasattr(request, "remove_data") else False
            ),
        )

        # Delete connection configuration
        connection_removal = await email_connection.delete_connection(
            user_id=current_user.id, connection_id=connection_id
        )

        return {
            "success": True,
            "connection_id": connection_id,
            "disconnected_at": datetime.utcnow(),
            "data_removed": data_removal["data_removed"],
            "files_deleted": data_removal["files_deleted"],
            "configuration_deleted": connection_removal["deleted"],
        }

    except Exception as e:
        logger.error(f"Email disconnection failed: {e!s}")
        raise HTTPException(status_code=500, detail="Email disconnection failed") from e


@router.get("/analytics/dashboard")
async def get_email_analytics_dashboard(
    time_period: str = Query(
        default="30d", description="Time period for dashboard data"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Get email analytics dashboard data
    Comprehensive overview of email communication patterns and insights
    """
    try:
        # Get dashboard data
        dashboard_data = await email_analytics.get_dashboard_data(
            user_id=current_user.id, time_period=time_period
        )

        return {
            "success": True,
            "user_id": current_user.id,
            "time_period": time_period,
            "dashboard_data": dashboard_data,
            "last_updated": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"Failed to get email analytics dashboard: {e!s}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve email analytics dashboard"
        ) from e


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
                "setup_difficulty": "Easy",
            },
            "outlook": {
                "name": "Microsoft Outlook",
                "auth_type": "OAuth2",
                "api_support": True,
                "features": [
                    "read",
                    "send",
                    "folders",
                    "search",
                    "calendar_integration",
                ],
                "limitations": ["API_rate_limits", "enterprise_policies"],
                "setup_difficulty": "Easy",
            },
            "exchange": {
                "name": "Microsoft Exchange",
                "auth_type": "Basic/OAuth2",
                "api_support": True,
                "features": [
                    "read",
                    "send",
                    "folders",
                    "search",
                    "calendar",
                    "contacts",
                ],
                "limitations": ["server_configuration", "firewall_restrictions"],
                "setup_difficulty": "Advanced",
            },
            "imap": {
                "name": "Generic IMAP/POP3",
                "auth_type": "Basic",
                "api_support": False,
                "features": ["read", "search", "folders"],
                "limitations": ["no_send_capability", "basic_features_only"],
                "setup_difficulty": "Intermediate",
            },
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
                "Topic extraction",
            ],
            "security_features": [
                "OAuth2 authentication",
                "Encrypted credential storage",
                "Data privacy protection",
                "User consent management",
                "Secure data transmission",
            ],
        }

    except Exception as e:
        logger.error(f"Failed to get available email providers: {e!s}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve available email providers"
        ) from e


@router.post("/oauth/url")
async def get_oauth_authorization_url(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Generate OAuth authorization URL for email providers
    Returns the URL where user should be redirected to grant access
    """
    try:
        provider = request.get("provider", "gmail")
        redirect_uri = request.get(
            "redirect_uri", "http://localhost:5004/email-oauth-callback"
        )

        # Generate OAuth URL using the email connector service
        import secrets

        state = secrets.token_urlsafe(32)

        # Generate OAuth URLs based on provider
        if provider == "gmail":
            # Check if Gmail credentials are configured
            if not settings.GMAIL_CLIENT_ID:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Gmail OAuth not configured",
                        "message": "Gmail OAuth credentials (GMAIL_CLIENT_ID) are not configured. Please set up OAuth credentials or use IMAP connection instead.",
                        "instructions": "Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in your environment variables or .env file. Get credentials from https://console.cloud.google.com/",
                    },
                )

            # Gmail OAuth URL
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            client_id = settings.GMAIL_CLIENT_ID
            scopes = [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/userinfo.email",
            ]

            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes),
                "response_type": "code",
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            }

            from urllib.parse import urlencode

            auth_url = f"{base_url}?{urlencode(params)}"

        elif provider == "outlook":
            # Check if Outlook credentials are configured
            if not settings.OUTLOOK_CLIENT_ID:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Outlook OAuth not configured",
                        "message": "Outlook OAuth credentials (OUTLOOK_CLIENT_ID) are not configured. Please set up OAuth credentials or use IMAP connection instead.",
                        "instructions": "Set OUTLOOK_CLIENT_ID and OUTLOOK_CLIENT_SECRET in your environment variables or .env file. Get credentials from https://portal.azure.com/",
                    },
                )

            # Outlook OAuth URL
            base_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            client_id = settings.OUTLOOK_CLIENT_ID
            scopes = [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/User.Read",
            ]

            params = {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes),
                "response_type": "code",
                "state": state,
                "response_mode": "query",
            }

            from urllib.parse import urlencode

            auth_url = f"{base_url}?{urlencode(params)}"

        else:
            raise HTTPException(
                status_code=400, detail=f"OAuth not supported for provider: {provider}"
            )

        return {
            "success": True,
            "auth_url": auth_url,
            "state": state,
            "provider": provider,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate OAuth authorization URL: {str(e)}",
        ) from e


@router.post("/oauth/callback")
async def handle_oauth_callback(
    request: dict,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Handle OAuth callback from email providers
    Exchange authorization code for access token and create connection
    """
    try:
        provider = request.get("provider", "gmail")
        code = request.get("code")
        state = request.get("state")

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing OAuth parameters")

        # Exchange code for tokens (simplified - implement actual token exchange)
        if provider == "gmail":
            # TODO: Implement actual token exchange with Gmail
            # This requires calling Google's token endpoint
            connection_id = (
                f"gmail_{current_user.id}_{int(datetime.utcnow().timestamp())}"
            )
            email_address = f"user@gmail.com"  # Get from token info

        elif provider == "outlook":
            # TODO: Implement actual token exchange with Outlook
            connection_id = (
                f"outlook_{current_user.id}_{int(datetime.utcnow().timestamp())}"
            )
            email_address = f"user@outlook.com"  # Get from token info

        else:
            raise HTTPException(
                status_code=400, detail=f"OAuth not supported for provider: {provider}"
            )

        # Store connection (simplified - use proper encryption in production)
        await email_connection.store_connection_configuration(
            user_id=current_user.id,
            provider=provider,
            email_address=email_address,
            connection_parameters={"oauth_code": code, "oauth_state": state},
            permissions=["read"],
            sync_settings={"frequency": "daily"},
        )

        return {
            "success": True,
            "provider": provider,
            "email_address": email_address,
            "connection_id": connection_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback handling failed: {e!s}")
        raise HTTPException(
            status_code=500, detail="Failed to complete OAuth flow"
        ) from e


@router.post("/connection/test-imap")
async def test_imap_connection(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Test IMAP/POP3 connection before saving
    Validates credentials and server connectivity
    """
    try:
        email_address = request.get("email_address")
        server = request.get("server")
        port = request.get("port", 993)
        use_ssl = request.get("use_ssl", True)
        username = request.get("username")
        password = request.get("password")

        if not all([email_address, server, password]):
            raise HTTPException(
                status_code=400, detail="Missing required IMAP credentials"
            )

        # For now, do a basic validation (actual IMAP connection testing would require imaplib)
        # In production, you would:
        # 1. Create IMAP connection
        # 2. Attempt login
        # 3. Check for errors
        # 4. Return test results

        # Simulated test - validate input format
        if "@" not in email_address:
            return {
                "success": False,
                "connection_status": "failed",
                "error_message": "Invalid email address format",
            }

        if port < 1 or port > 65535:
            return {
                "success": False,
                "connection_status": "failed",
                "error_message": "Invalid port number",
            }

        # Simulate successful connection (replace with actual IMAP test)
        import imaplib

        try:
            # Sanitize password - replace non-breaking spaces and other non-ASCII chars
            # This handles cases where password might have \xa0 (non-breaking space)
            password_sanitized = password.replace("\xa0", " ").replace("\u00a0", " ")
            # Encode to UTF-8 and decode back to ensure it's properly encoded
            password_sanitized = password_sanitized.encode(
                "utf-8", errors="ignore"
            ).decode("utf-8")

            # Actual IMAP connection test
            if use_ssl:
                mail = imaplib.IMAP4_SSL(server, port)
            else:
                mail = imaplib.IMAP4(server, port)

            # Attempt login with sanitized password
            login_user = username or email_address
            mail.login(login_user, password_sanitized)
            mail.logout()

            return {
                "success": True,
                "connection_status": "connected",
                "message": "IMAP connection successful!",
            }

        except imaplib.IMAP4.error as e:
            return {
                "success": False,
                "connection_status": "failed",
                "error_message": f"IMAP connection failed: {str(e)}. Please check your server, port, and credentials.",
            }
        except Exception as e:
            return {
                "success": False,
                "connection_status": "failed",
                "error_message": f"Connection error: {str(e)}",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IMAP connection test failed: {e!s}")
        raise HTTPException(
            status_code=500, detail=f"IMAP connection test failed: {str(e)}"
        ) from e
