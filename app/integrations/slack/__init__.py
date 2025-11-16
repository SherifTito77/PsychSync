"""
Slack Integration Module for PsychSync

Why we need this:
- Send team notifications about assessment completions
- Alert managers about team member wellbeing concerns
- Enable team collaboration through Slack
- Automate report sharing to Slack channels
- Provide bot commands for quick insights

Setup:
1. Create Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes: chat:write, channels:read, users:read
3. Install app to workspace
4. Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in .env
"""

from .client import SlackClient
from .notifications import SlackNotificationService
from .bot import SlackBotHandler

__all__ = [
    'SlackClient',
    'SlackNotificationService', 
    'SlackBotHandler'
]
