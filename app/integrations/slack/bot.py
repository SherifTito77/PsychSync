"""
Slack Bot Handler for PsychSync

Why we need this:
- Enable team members to interact with PsychSync directly from Slack
- Quick access to wellness metrics without leaving Slack
- Automated reminders and check-ins via bot
- Team leaders can query reports via slash commands
- Reduce friction in assessment completion

Features:
- Slash commands (/psychsync, /wellness, /checkin)
- Interactive buttons and modals
- Event handlers (app mentions, reactions)
- Scheduled messages and reminders
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

from app.core.config import settings
from app.core.database import get_async_db
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.response import Response
from app.services.assessment_service import AssessmentService
from app.services.user_service import UserService
from app.integrations.slack.client import SlackClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio

logger = logging.getLogger(__name__)


class SlackBotHandler:
    """
    Slack Bot event and command handler

    Handles:
    - Slash commands (/psychsync, /wellness, /checkin)
    - Interactive components (buttons, modals)
    - Event subscriptions (mentions, messages)
    - Scheduled jobs (daily reminders)
    """

    def __init__(self):
        """Initialize Slack Bolt app"""
        self.app = App(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET
        )
        self.client = SlackClient()
        self.handler = SlackRequestHandler(self.app)

        # Register all handlers
        self._register_commands()
        self._register_events()
        self._register_actions()

    def _register_commands(self):
        """Register all slash commands"""

        # Main command: /psychsync
        @self.app.command("/psychsync")
        def handle_psychsync_command(ack, command, respond):
            """
            Main PsychSync command

            Usage:
                /psychsync - Show help menu
                /psychsync status - Show your wellness status
                /psychsync team - Show team wellness overview
                /psychsync report - Generate team report
            """
            ack()  # Acknowledge command immediately

            user_id = command["user_id"]
            text = command.get("text", "").strip().lower()

            if not text or text == "help":
                respond(self._get_help_message())
            elif text == "status":
                respond(self._get_user_status(user_id))
            elif text == "team":
                respond(self._get_team_status(user_id))
            elif text == "report":
                respond(self._generate_team_report(user_id))
            else:
                respond({
                    "text": f"Unknown command: `{text}`\nType `/psychsync help` for available commands."
                })

        # Quick check-in: /checkin
        @self.app.command("/checkin")
        def handle_checkin_command(ack, command, client):
            """
            Quick wellness check-in

            Opens a modal for quick mood/wellness check-in
            """
            ack()

            # Open modal for check-in
            client.views_open(
                trigger_id=command["trigger_id"],
                view=self._get_checkin_modal()
            )

        # Wellness status: /wellness
        @self.app.command("/wellness")
        def handle_wellness_command(ack, command, respond):
            """
            Show wellness statistics

            Usage:
                /wellness - Your wellness stats
                /wellness team - Team wellness stats
                /wellness @user - Specific user stats (managers only)
            """
            ack()

            user_id = command["user_id"]
            text = command.get("text", "").strip()

            if not text:
                respond(self._get_user_wellness(user_id))
            elif text == "team":
                respond(self._get_team_wellness(user_id))
            else:
                respond({
                    "text": "Usage: `/wellness` or `/wellness team`"
                })

        # Take assessment: /assess
        @self.app.command("/assess")
        def handle_assess_command(ack, command, client):
            """
            Start a new assessment

            Opens modal to select assessment type
            """
            ack()

            client.views_open(
                trigger_id=command["trigger_id"],
                view=self._get_assessment_selection_modal()
            )

    def _register_events(self):
        """Register event handlers"""

        # App mention: @PsychSync
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """
            Handle when bot is mentioned

            Example: "@PsychSync how is my team doing?"
            """
            user = event["user"]
            text = event.get("text", "").lower()

            if "team" in text:
                say(self._get_team_status(user))
            elif "status" in text or "how" in text:
                say(self._get_user_status(user))
            elif "help" in text:
                say(self._get_help_message())
            else:
                say({
                    "text": f"Hi <@{user}>! 👋\n\nI can help you with:\n• Check your wellness status\n• View team insights\n• Take assessments\n\nTry `/psychsync help` for more commands!"
                })

        # Message in bot DM
        @self.app.event("message")
        def handle_message(event, say):
            """Handle direct messages to bot"""
            # Only respond to DMs, not channel messages
            if event.get("channel_type") == "im":
                user = event["user"]
                text = event.get("text", "").lower()

                if "help" in text:
                    say(self._get_help_message())
                elif "assess" in text or "test" in text:
                    say(self._get_assessment_prompt())
                else:
                    say(f"Hi <@{user}>! Type 'help' to see what I can do.")

        # Reaction added (for gamification)
        @self.app.event("reaction_added")
        def handle_reaction(event, logger):
            """Track reactions for engagement metrics"""
            # Could track team engagement via reactions
            logger.info(f"Reaction added: {event['reaction']} by {event['user']}")

    def _register_actions(self):
        """Register interactive action handlers"""

        # Handle check-in submission
        @self.app.view("checkin_modal")
        def handle_checkin_submission(ack, body, view, client):
            """Process check-in form submission"""
            ack()

            user_id = body["user"]["id"]
            values = view["state"]["values"]

            # Extract form values
            mood = values["mood_block"]["mood_select"]["selected_option"]["value"]
            stress = values["stress_block"]["stress_select"]["selected_option"]["value"]
            notes = values.get("notes_block", {}).get("notes_input", {}).get("value", "")

            # Save check-in (integrate with your database)
            self._save_checkin(user_id, mood, stress, notes)

            # Send confirmation
            client.chat_postMessage(
                channel=user_id,
                text=f"✅ Thanks for checking in! Your wellness score today: {self._calculate_score(mood, stress)}/100"
            )

        # Handle assessment selection
        @self.app.view("assessment_modal")
        def handle_assessment_selection(ack, body, view, client):
            """Process assessment type selection"""
            ack()

            user_id = body["user"]["id"]
            values = view["state"]["values"]
            assessment_type = values["assessment_block"]["assessment_select"]["selected_option"]["value"]

            # Generate assessment link
            assessment_url = f"{settings.FRONTEND_URL}/assessments/start?type={assessment_type}"

            client.chat_postMessage(
                channel=user_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"🎯 Ready to start your *{assessment_type}* assessment!"
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
                    }
                ]
            )

        # Handle button clicks
        @self.app.action("view_dashboard")
        def handle_view_dashboard(ack, body, client):
            """Handle dashboard button click"""
            ack()
            # Button actions are handled by URL in the button definition

        @self.app.action("start_assessment")
        def handle_start_assessment(ack, body, client):
            """Handle start assessment button"""
            ack()
            # Open assessment modal or redirect

    def _get_help_message(self) -> Dict[str, Any]:
        """Generate help message with all available commands"""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🧠 PsychSync Commands"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Quick Commands:*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "`/checkin`\nQuick wellness check-in"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "`/assess`\nStart new assessment"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "`/wellness`\nView your stats"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "`/wellness team`\nView team stats"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Main Commands:*\n• `/psychsync status` - Your wellness overview\n• `/psychsync team` - Team wellness overview\n• `/psychsync report` - Generate team report"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Need help?* Just mention me: @PsychSync"
                    }
                }
            ]
        }

    async def _get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's wellness status with real database integration"""
        try:
            # Get database session
            async with get_async_db() as db:
                # Find user by Slack ID
                result = await db.execute(
                    select(User).where(User.slack_user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    return {
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "❌ *User not found. Please link your Slack account first.*"
                                }
                            }
                        ]
                    }

                # Get recent assessments and responses
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                recent_responses = await db.execute(
                    select(Response)
                    .where(Response.user_id == user.id)
                    .where(Response.created_at >= thirty_days_ago)
                    .order_by(Response.created_at.desc())
                    .limit(10)
                )
                responses = recent_responses.scalars().all()

                # Calculate wellness metrics
                total_assessments = len(responses)
                if total_assessments > 0:
                    avg_score = sum(r.score or 0 for r in responses) / total_assessments
                    last_assessment = responses[0].created_at if responses else None
                else:
                    avg_score = 0
                    last_assessment = None

                # Determine wellness level
                if avg_score >= 80:
                    wellness_level = "Excellent"
                    emoji = "🟢"
                elif avg_score >= 60:
                    wellness_level = "Good"
                    emoji = "🟡"
                elif avg_score >= 40:
                    wellness_level = "Okay"
                    emoji = "🟠"
                else:
                    wellness_level = "Needs Attention"
                    emoji = "🔴"

                last_assessment_str = last_assessment.strftime("%B %d, %Y") if last_assessment else "No assessments"

                return {
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} Your Wellness Status"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Wellness Level:*\n{wellness_level}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Average Score:*\n{avg_score:.1f}/100"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Assessments:*\n{total_assessments} (30 days)"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Last Assessment:*\n{last_assessment_str}"
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
                                        "text": "📝 Complete Assessment"
                                    },
                                    "style": "primary",
                                    "url": f"{settings.FRONTEND_URL}/assessments"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "📊 View Detailed Report"
                                    },
                                    "url": f"{settings.FRONTEND_URL}/dashboard"
                                }
                            ]
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Error getting user status for {user_id}: {e}")
            return {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "❌ *Error retrieving wellness data. Please try again later.*"
                        }
                    }
                ]
            }

    async def _get_team_status(self, user_id: str) -> Dict[str, Any]:
        """Get team wellness overview with real database integration"""
        try:
            # Get database session
            async with get_async_db() as db:
                # Find user by Slack ID
                result = await db.execute(
                    select(User).where(User.slack_user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user or not user.team_id:
                    return {
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "❌ *Team not found. Please ensure you're assigned to a team.*"
                                }
                            }
                        ]
                    }

                # Get team information
                team_result = await db.execute(
                    select(Team).where(Team.id == user.team_id)
                )
                team = team_result.scalar_one_or_none()

                if not team:
                    return {
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "❌ *Team information not found.*"
                                }
                            }
                        ]
                    }

                # Get team members' recent assessments
                thirty_days_ago = datetime.utcnow() - timedelta(days=30)

                # Count team members
                team_members_count = await db.execute(
                    select(func.count(User.id))
                    .where(User.team_id == user.team_id)
                    .where(User.is_active == True)
                )
                total_members = team_members_count.scalar() or 0

                # Get team member responses
                team_responses = await db.execute(
                    select(Response, User.full_name)
                    .join(User, Response.user_id == User.id)
                    .where(User.team_id == user.team_id)
                    .where(Response.created_at >= thirty_days_ago)
                    .order_by(Response.created_at.desc())
                )
                responses_with_names = team_responses.all()

                # Calculate team metrics
                members_with_assessments = set()
                total_score = 0
                assessment_count = 0

                for response, name in responses_with_names:
                    members_with_assessments.add(response.user_id)
                    if response.score:
                        total_score += response.score
                        assessment_count += 1

                # Calculate metrics
                participation_rate = (len(members_with_assessments) / total_members * 100) if total_members > 0 else 0
                team_average = (total_score / assessment_count) if assessment_count > 0 else 0

                # Determine wellness level for team
                if team_average >= 80:
                    wellness_level = "Excellent"
                    emoji = "🟢"
                elif team_average >= 60:
                    wellness_level = "Good"
                    emoji = "🟡"
                elif team_average >= 40:
                    wellness_level = "Okay"
                    emoji = "🟠"
                else:
                    wellness_level = "Needs Attention"
                    emoji = "🔴"

                # Simple trend calculation (compare with previous period)
                sixty_days_ago = datetime.utcnow() - timedelta(days=60)
                previous_responses = await db.execute(
                    select(Response)
                    .join(User, Response.user_id == User.id)
                    .where(User.team_id == user.team_id)
                    .where(Response.created_at >= sixty_days_ago)
                    .where(Response.created_at < thirty_days_ago)
                )
                previous_scores = [r.score for r in previous_responses.scalars().all() if r.score]
                previous_average = sum(previous_scores) / len(previous_scores) if previous_scores else 0

                if team_average > previous_average + 5:
                    trend = "📈 Improving"
                elif team_average < previous_average - 5:
                    trend = "📉 Declining"
                else:
                    trend = "➡️ Stable"

                return {
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"👥 {team.name} Wellness Overview"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Team Average:*\n{emoji} {team_average:.1f}/100"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Participation:*\n{participation_rate:.0f}% ({len(members_with_assessments)}/{total_members})"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Wellness Level:*\n{wellness_level}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Trend:*\n{trend}"
                                }
                            ]
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"📊 Based on {assessment_count} assessments in the last 30 days"
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
                                        "text": "📈 View Team Report"
                                    },
                                    "url": f"{settings.FRONTEND_URL}/teams/{team.id}/analytics"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "📋 Schedule Assessment"
                                    },
                                    "style": "primary",
                                    "url": f"{settings.FRONTEND_URL}/teams/{team.id}/assessments"
                                }
                            ]
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Error getting team status for {user_id}: {e}")
            return {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "❌ *Error retrieving team data. Please try again later.*"
                        }
                    }
                ]
            }

    def _get_checkin_modal(self) -> Dict[str, Any]:
        """Generate check-in modal"""
        return {
            "type": "modal",
            "callback_id": "checkin_modal",
            "title": {
                "type": "plain_text",
                "text": "Daily Check-in"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "How are you feeling today?"
                    }
                },
                {
                    "type": "input",
                    "block_id": "mood_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "mood_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select your mood"
                        },
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "😊 Great"},
                                "value": "great"
                            },
                            {
                                "text": {"type": "plain_text", "text": "🙂 Good"},
                                "value": "good"
                            },
                            {
                                "text": {"type": "plain_text", "text": "😐 Okay"},
                                "value": "okay"
                            },
                            {
                                "text": {"type": "plain_text", "text": "😟 Not great"},
                                "value": "not_great"
                            },
                            {
                                "text": {"type": "plain_text", "text": "😢 Struggling"},
                                "value": "struggling"
                            }
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Mood"
                    }
                },
                {
                    "type": "input",
                    "block_id": "stress_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "stress_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select stress level"
                        },
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "1 - Very Low"},
                                "value": "1"
                            },
                            {
                                "text": {"type": "plain_text", "text": "2 - Low"},
                                "value": "2"
                            },
                            {
                                "text": {"type": "plain_text", "text": "3 - Moderate"},
                                "value": "3"
                            },
                            {
                                "text": {"type": "plain_text", "text": "4 - High"},
                                "value": "4"
                            },
                            {
                                "text": {"type": "plain_text", "text": "5 - Very High"},
                                "value": "5"
                            }
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Stress Level"
                    }
                },
                {
                    "type": "input",
                    "block_id": "notes_block",
                    "optional": True,
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "notes_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Anything on your mind? (optional)"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Notes"
                    }
                }
            ]
        }

    def _get_assessment_selection_modal(self) -> Dict[str, Any]:
        """Generate assessment selection modal"""
        return {
            "type": "modal",
            "callback_id": "assessment_modal",
            "title": {
                "type": "plain_text",
                "text": "Start Assessment"
            },
            "submit": {
                "type": "plain_text",
                "text": "Continue"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Choose an assessment to complete:"
                    }
                },
                {
                    "type": "input",
                    "block_id": "assessment_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "assessment_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select assessment type"
                        },
                        "options": [
                            {
                                "text": {"type": "plain_text", "text": "🔥 Burnout Assessment"},
                                "value": "burnout"
                            },
                            {
                                "text": {"type": "plain_text", "text": "😰 Stress Level Check"},
                                "value": "stress"
                            },
                            {
                                "text": {"type": "plain_text", "text": "😊 Wellbeing Survey"},
                                "value": "wellbeing"
                            },
                            {
                                "text": {"type": "plain_text", "text": "👥 Team Dynamics"},
                                "value": "team_dynamics"
                            }
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Assessment Type"
                    }
                }
            ]
        }

    async def _save_checkin(self, user_id: str, mood: str, stress: str, notes: str):
        """Save check-in to database with proper integration"""
        try:
            # Get database session
            async with get_async_db() as db:
                # Find user by Slack ID
                result = await db.execute(
                    select(User).where(User.slack_user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found for Slack ID {user_id}")
                    return False

                # Calculate wellness score
                wellness_score = self._calculate_score(mood, stress)

                # Create a simple assessment response record for the check-in
                checkin_response = Response(
                    user_id=user.id,
                    assessment_id=None,  # This is a check-in, not tied to a formal assessment
                    question_text="Daily Wellness Check-in",
                    response_text=f"Mood: {mood}, Stress: {stress}, Notes: {notes}",
                    score=wellness_score,
                    response_type="daily_checkin",
                    created_at=datetime.utcnow()
                )

                # Save to database
                db.add(checkin_response)
                await db.commit()

                logger.info(f"Check-in saved for user {user.id} (Slack: {user_id}): score={wellness_score}")
                return True

        except Exception as e:
            logger.error(f"Error saving check-in for {user_id}: {e}")
            return False

    def _calculate_score(self, mood: str, stress: str) -> int:
        """Calculate wellness score from check-in"""
        mood_scores = {"great": 100, "good": 80, "okay": 60, "not_great": 40, "struggling": 20}
        stress_scores = {"1": 20, "2": 15, "3": 10, "4": 5, "5": 0}

        mood_value = mood_scores.get(mood, 60)
        stress_penalty = int(stress_scores.get(stress, 10))

        return min(100, mood_value - stress_penalty)

    def get_handler(self) -> SlackRequestHandler:
        """Get FastAPI request handler"""
        return self.handler


# Global bot instance
slack_bot = SlackBotHandler()
