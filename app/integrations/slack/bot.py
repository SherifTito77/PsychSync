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
from app.db.models.user import User
from app.db.models.team import Team
from app.services.assessment_service import AssessmentService
from app.integrations.slack.client import SlackClient

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
    
    def _get_user_status(self, user_id: str) -> Dict[str, Any]:
        """Get user's wellness status"""
        # TODO: Integrate with database to fetch real data
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Your Wellness Status"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Overall Score:*\n🟢 78/100"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Trend:*\n📈 +5 from last week"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Last Assessment:*\n2 days ago"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Completed:*\n12/15 this month"
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
                                "text": "View Dashboard"
                            },
                            "url": f"{settings.FRONTEND_URL}/dashboard",
                            "action_id": "view_dashboard"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Take Assessment"
                            },
                            "action_id": "start_assessment",
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
    
    def _get_team_status(self, user_id: str) -> Dict[str, Any]:
        """Get team wellness overview"""
        # TODO: Integrate with database
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "👥 Team Wellness Overview"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Team Average:*\n🟡 72/100"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Participation:*\n85% (11/13)"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Trend:*\n➡️ Stable"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Alerts:*\n⚠️ 2 requiring attention"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Top Concerns:*\n• Work-life balance\n• Team communication"
                    }
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
                            "url": f"{settings.FRONTEND_URL}/team/reports"
                        }
                    ]
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
    
    def _save_checkin(self, user_id: str, mood: str, stress: str, notes: str):
        """Save check-in to database"""
        # TODO: Implement database integration
        logger.info(f"Check-in saved for {user_id}: mood={mood}, stress={stress}")
    
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