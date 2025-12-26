"""
Slack Integration Service
Handles Slack bot commands and team assessment integration
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
import json
import asyncio
from datetime import datetime, timedelta

from app.services.assessment_service import AssessmentService
from app.services.team_optimization_service import TeamOptimizationService
from app.services.compatibility_analysis_service import TeamCompatibilityAnalysisService
from app.core.config import settings

logger = logging.getLogger(__name__)


class SlackIntegrationService:
    """Service for integrating with Slack team management and assessments"""

    def __init__(self, db):
        self.db = db
        self.assessment_service = AssessmentService(db)
        self.team_optimization_service = TeamOptimizationService(db)
        self.compatibility_service = TeamCompatibilityAnalysisService(db)

        # Slack command registry
        self.commands = {
            '/team-assessment': self.handle_team_assessment,
            '/team-status': self.handle_team_status,
            '/team-compatibility': self.handle_team_compatibility,
            '/team-insights': self.handle_team_insights,
            '/quick-poll': self.handle_quick_poll,
            '/team-checkin': self.handle_team_checkin,
            '/help': self.handle_help
        }

    async def process_slash_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Slack slash command"""
        try:
            command = command_data.get('command', '').lower()
            user_id = command_data.get('user_id')
            channel_id = command_data.get('channel_id')
            team_id = command_data.get('team_id')
            text = command_data.get('text', '').strip()
            response_url = command_data.get('response_url')

            # Verify team exists in our system
            slack_team_id = await self._get_internal_team_id(team_id)
            if not slack_team_id:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Your Slack workspace isn't connected to PsychSync yet. Please contact your administrator."
                }

            # Process command
            if command in self.commands:
                # Acknowledge immediately (Slash commands must respond within 3 seconds)
                initial_response = {
                    "response_type": "in_channel",
                    "text": f"🔄 Processing `/command`..."
                }

                # Process command asynchronously
                asyncio.create_task(
                    self._process_command_async(
                        command, text, user_id, channel_id,
                        slack_team_id, response_url
                    )
                )

                return initial_response
            else:
                return {
                    "response_type": "ephemeral",
                    "text": f"❌ Unknown command: {command}. Type `/help` for available commands."
                }

        except Exception as e:
            logger.error(f"Error processing Slack command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ An error occurred while processing your command. Please try again."
            }

    async def _process_command_async(
        self, command: str, text: str, user_id: str,
        channel_id: str, team_id: UUID, response_url: str
    ):
        """Process command asynchronously and update response"""
        try:
            # Execute command handler
            result = await self.commands[command](
                text=text,
                user_id=user_id,
                channel_id=channel_id,
                team_id=team_id
            )

            # Update the original response with results
            await self._update_slack_response(response_url, result)

        except Exception as e:
            logger.error(f"Error in async command processing: {str(e)}")
            error_response = {
                "response_type": "ephemeral",
                "text": "❌ An error occurred while processing your command."
            }
            await self._update_slack_response(response_url, error_response)

    async def handle_team_assessment(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /team-assessment command"""
        try:
            # Parse command arguments
            args = text.split()
            assessment_type = args[0] if args else "quick"
            duration = args[1] if len(args) > 1 else "5min"

            # Create quick assessment for team
            assessment_data = {
                "title": f"Team Quick Check-in",
                "description": f"Quick team pulse check - {duration}",
                "assessment_type": "team_pulse",
                "questions": [
                    {
                        "text": "How's your energy level today?",
                        "type": "scale",
                        "scale": "1-5"
                    },
                    {
                        "text": "How aligned do you feel with team goals?",
                        "type": "scale",
                        "scale": "1-5"
                    },
                    {
                        "text": "Any blockers or challenges?",
                        "type": "text",
                        "optional": True
                    }
                ]
            }

            # Generate assessment
            result = await self.assessment_service.create_assessment(
                title=assessment_data["title"],
                description=assessment_data["description"],
                organization_id=None,  # Will get from team
                created_by_id=UUID(user_id) if self._is_valid_uuid(user_id) else None,
                team_id=team_id,
                questions=assessment_data["questions"]
            )

            if result.get("success"):
                assessment_url = f"{settings.FRONTEND_URL}/assessments/{result['assessment_id']}"

                return {
                    "response_type": "in_channel",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"📊 *Team Assessment Created*\n\n{assessment_data['description']}"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Start Assessment"
                                    },
                                    "url": assessment_url,
                                    "style": "primary"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"📝 {len(assessment_data['questions'])} questions • ⏱️ {duration} • Team: {channel_id}"
                                }
                            ]
                        }
                    ]
                }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Failed to create team assessment. Please try again."
                }

        except Exception as e:
            logger.error(f"Error in team assessment command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error creating team assessment."
            }

    async def handle_team_status(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /team-status command"""
        try:
            # Get team analytics
            analytics = await self.team_optimization_service.get_team_analytics(team_id)

            if "error" in analytics:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Could not retrieve team status. Make sure team assessments have been completed."
                }

            # Format team status for Slack
            completion_rate = analytics.get('completion_rate', 0) * 100
            avg_performance = analytics.get('avg_performance_score', 0) * 100
            team_size = analytics.get('team_size', 0)

            # Determine status emoji
            if completion_rate > 80:
                status_emoji = "🟢"
            elif completion_rate > 60:
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"

            return {
                "response_type": "in_channel",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{status_emoji} *Team Status Overview*"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Team Size:*\n{team_size} members"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Completion Rate:*\n{completion_rate:.1f}%"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Performance Score:*\n{avg_performance:.1f}/100"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Last Update:*\n{datetime.now().strftime('%b %d, %H:%M')}"
                            }
                        ]
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Detailed Analytics"
                                },
                                "url": f"{settings.FRONTEND_URL}/analytics/team/{team_id}",
                                "style": "primary"
                            }
                        ]
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error in team status command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error retrieving team status."
            }

    async def handle_team_compatibility(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /team-compatibility command"""
        try:
            # Parse team members if specified
            args = text.split()
            member1_id = args[0] if args else None
            member2_id = args[1] if len(args) > 1 else None

            if member1_id and member2_id:
                # Check compatibility between specific members
                compatibility = await self.compatibility_service.analyze_member_compatibility(
                    UUID(member1_id), UUID(member2_id)
                )

                return {
                    "response_type": "in_channel",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"🤝 *Member Compatibility Analysis*"
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Overall Score:*\n{compatibility.overall_score:.1%}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Personality Fit:*\n{compatibility.personality_fit:.1%}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Skills Complement:*\n{compatibility.skills_complement:.1%}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Work Style Match:*\n{compatibility.work_style_match:.1%}"
                                }
                            ]
                        }
                    ]
                }
            else:
                # Analyze overall team compatibility
                team_compatibility = await self.compatibility_service.analyze_team_compatibility(team_id)

                return {
                    "response_type": "in_channel",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"👥 *Team Compatibility Report*"
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Overall Compatibility:*\n{team_compatibility.overall_compatibility:.1%}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Team Balance Score:*\n{team_compatibility.team_balance_score:.1%}"
                                }
                            ]
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "View Full Report"
                                    },
                                    "url": f"{settings.FRONTEND_URL}/team/compatibility/{team_id}",
                                    "style": "primary"
                                }
                            ]
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Error in team compatibility command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error analyzing team compatibility."
            }

    async def handle_team_insights(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /team-insights command"""
        try:
            # Get team insights and recommendations
            insights = await self.team_optimization_service.get_team_insights(team_id)

            if "error" in insights:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Could not retrieve team insights. Please ensure team assessments are completed."
                }

            # Extract key insights
            strengths = insights.get('strengths', [])
            recommendations = insights.get('recommendations', [])
            trends = insights.get('performance_trends', [])

            # Format insights for Slack
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "💡 *Team Insights & Recommendations*"
                    }
                },
                {
                    "type": "divider"
                }
            ]

            # Add strengths
            if strengths:
                strengths_text = "\n".join([f"• {strength}" for strength in strengths[:3]])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🎯 Team Strengths:*\n{strengths_text}"
                    }
                })

            # Add top recommendations
            if recommendations:
                top_recommendations = recommendations[:2]
                recs_text = "\n".join([f"• {rec}" for rec in top_recommendations])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📈 Recommendations:*\n{recs_text}"
                    }
                })

            # Add performance trend
            if trends:
                trend = trends[0] if trends else "stable"
                trend_emoji = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{trend_emoji} *Recent Performance Trend:* {trend.title()}"
                    }
                })

            # Add action button
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Detailed Insights"
                        },
                        "url": f"{settings.FRONTEND_URL}/team/insights/{team_id}",
                        "style": "primary"
                    }
                ]
            })

            return {
                "response_type": "in_channel",
                "blocks": blocks
            }

        except Exception as e:
            logger.error(f"Error in team insights command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error retrieving team insights."
            }

    async def handle_quick_poll(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /quick-poll command"""
        try:
            # Parse poll question
            if not text:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Please provide a poll question. Usage: `/quick-poll \"Question here\"`"
                }

            # Create poll options (thumbs up/down, or custom)
            options = ["👍", "👎"]

            return {
                "response_type": "in_channel",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📊 *Quick Poll*\n\n{text}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "👍"
                                },
                                "value": f"poll:thumbs_up:{user_id}",
                                "action_id": "thumbs_up"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "👎"
                                },
                                "value": f"poll:thumbs_down:{user_id}",
                                "action_id": "thumbs_down"
                            }
                        ]
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error in quick poll command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error creating quick poll."
            }

    async def handle_team_checkin(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /team-checkin command"""
        try:
            # Create daily check-in
            checkin_questions = [
                "What's your main priority today?",
                "Any blockers you need help with?",
                "How are you feeling (1-5)?"
            ]

            checkin_url = f"{settings.FRONTEND_URL}/team/checkin/{team_id}"

            return {
                "response_type": "in_channel",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🌅 *Daily Team Check-in*\n\nQuick daily sync to align the team"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Start Check-in"
                                },
                                "url": checkin_url,
                                "style": "primary"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"📝 {len(checkin_questions)} questions • ⏱️ 2 minutes • Daily sync"
                            }
                        ]
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error in team checkin command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error creating team check-in."
            }

    async def handle_help(
        self, text: str, user_id: str, channel_id: str, team_id: UUID
    ) -> Dict[str, Any]:
        """Handle /help command"""
        try:
            return {
                "response_type": "ephemeral",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🤖 *PsychSync Slack Bot Commands*\n\nHere are the available commands:"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*`/team-assessment [type] [duration]`*\nCreate quick team assessment"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*`/team-status`*\nView team performance overview"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*`/team-compatibility [user1] [user2]`*\nAnalyze team compatibility"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*`/team-insights`*\nGet AI-powered team insights"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*`/quick-poll \"question\"`*\nCreate instant team poll"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*`/team-checkin`*\nStart daily team check-in"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*`/help`*\nShow this help message"
                            }
                        ]
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error in help command: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error displaying help."
            }

    async def handle_interactive_component(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive components (button clicks, etc.)"""
        try:
            action = payload.get('actions', [{}])[0]
            action_id = action.get('action_id')
            user_id = payload.get('user', {}).get('id')

            if action_id == 'thumbs_up' or action_id == 'thumbs_down':
                # Handle poll response
                return await self._handle_poll_response(payload)
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Unknown action."
                }

        except Exception as e:
            logger.error(f"Error handling interactive component: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error processing your action."
            }

    async def _handle_poll_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle poll button responses"""
        try:
            action = payload.get('actions', [{}])[0]
            original_message = payload.get('original_message', {})

            # Update the original message to show poll results
            # (This is simplified - in production, you'd track votes in database)

            return {
                "replace_original": True,
                "text": "Thanks for your vote! 📊"
            }

        except Exception as e:
            logger.error(f"Error handling poll response: {str(e)}")
            return {
                "response_type": "ephemeral",
                "text": "❌ Error recording your vote."
            }

    async def _get_internal_team_id(self, slack_team_id: str) -> Optional[UUID]:
        """Convert Slack team ID to internal team ID"""
        try:
            # In production, this would query your database
            # For now, return a placeholder
            return UUID('00000000-0000-0000-0000-000000000001')
        except Exception:
            return None

    async def _update_slack_response(self, response_url: str, response_data: Dict[str, Any]):
        """Update original Slack response with processed results"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(response_url, json=response_data) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to update Slack response: {resp.status}")
        except Exception as e:
            logger.error(f"Error updating Slack response: {str(e)}")

    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            UUID(uuid_string)
            return True
        except ValueError:
            return False

    async def verify_slack_request(self, headers: Dict[str, str], body: str) -> bool:
        """Verify that request is from Slack"""
        try:
            import hmac
            import hashlib

            slack_signing_secret = settings.SLACK_SIGNING_SECRET
            if not slack_signing_secret:
                return True  # Skip verification if not configured

            timestamp = headers.get('X-Slack-Request-Timestamp')
            slack_signature = headers.get('X-Slack-Signature')

            if not timestamp or not slack_signature:
                return False

            # Check timestamp (prevent replay attacks)
            if abs(int(time.time()) - int(timestamp)) > 300:
                return False

            # Create signature
            sig_basestring = f"v0:{timestamp}:{body}"
            my_signature = 'v0=' + hmac.new(
                slack_signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(my_signature, slack_signature)

        except Exception as e:
            logger.error(f"Error verifying Slack request: {str(e)}")
            return False