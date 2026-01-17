"""
Product Management Prompts - Integration Examples

This file demonstrates how to integrate the 50 product management prompts
with popular tools and workflows.

Examples include:
- Jira integration for issue tracking
- Notion integration for documentation
- Slack integration for team notifications
- Email integration for reports
"""

import asyncio
import json
from typing import Dict, Any, List
from pathlib import Path

# These would be imported in actual usage
# from app.services.product_management_service import ProductManagementPromptsService
# from app.db.database import async_session_maker
# import requests


# ============================================================================
# Jira Integration Example
# ============================================================================

class JiraProductPromptsIntegration:
    """
    Integration between Product Management Prompts and Jira.

    Creates Jira issues, epics, and tasks from prompt execution results.
    """

    def __init__(self, jira_url: str, api_token: str, email: str):
        self.jira_url = jira_url
        self.api_token = api_token
        self.email = email
        self.auth = (email, api_token)

    async def create_epic_from_prompt(
        self,
        prompt_id: str,
        execution_result: Dict[str, Any],
        project_key: str
    ) -> str:
        """
        Create a Jira epic from a prompt execution.

        Example:
            integration = JiraProductPromptsIntegration(jira_url, token, email)
            result = await execute_prompt('rs_001', {...})
            epic_key = await integration.create_epic_from_prompt('rs_001', result, 'PROD')
        """
        epic_data = {
            "fields": {
                "project": {"key": project_key},
                "summary": f"[PM Prompt] {execution_result['prompt']['prompt']}",
                "description": self._format_jira_description(execution_result),
                "issuetype": {"name": "Epic"},
                "labels": ["product-management-prompt", prompt_id]
            }
        }

        # In production, use requests.post()
        # response = requests.post(
        #     f"{self.jira_url}/rest/api/3/issue",
        #     auth=self.auth,
        #     json=epic_data
        # )
        # return response.json()['key']

        return f"{project_key}-123"  # Mock response

    def _format_jira_description(self, execution_result: Dict[str, Any]) -> str:
        """Format execution result as Jira description."""
        prompt = execution_result['prompt']

        description = f"""
h1. Product Management Prompt: {prompt['prompt']}

*Prompt ID:* {prompt['id']}
*Type:* {prompt['type']}
*Complexity:* {prompt['complexity']}
*Estimated Time:* {prompt['estimated_time']}

h2. Expected Outputs
{self._format_list(prompt['outputs'])}

h2. Use Cases
{self._format_list(prompt['use_cases'])}

h2. Execution Details
*Execution ID:* {execution_result['execution_id']}
*Executed At:* {execution_result['executed_at']}
*AI Enhanced:* {execution_result['use_ai']}

h3. AI Suggestions
{execution_result.get('ai_suggestion', 'N/A')}
        """.strip()
        return description

    def _format_list(self, items: List[str]) -> str:
        """Format a list as Jira markup."""
        return '\n'.join(f'* {item}' for item in items)


# ============================================================================
# Notion Integration Example
# ============================================================================

class NotionProductPromptsIntegration:
    """
    Integration between Product Management Prompts and Notion.

    Creates Notion pages and databases for prompt results.
    """

    def __init__(self, integration_token: str):
        self.integration_token = integration_token
        self.base_url = "https://api.notion.com/v1"

    async def create_prompt_database(
        self,
        parent_page_id: str
    ) -> str:
        """
        Create a database in Notion to track prompt executions.

        Returns the database ID.
        """
        headers = {
            "Authorization": f"Bearer {self.integration_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        database_schema = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [
                {
                    "type": "text",
                    "text": {"content": "Product Management Prompts"}
                }
            ],
            "properties": {
                "Prompt ID": {"title": {}},
                "Prompt Text": {"type": "text", "text": {}},
                "Type": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Strategic"},
                            {"name": "Tactical"},
                            {"name": "Analytical"},
                            {"name": "Technical"},
                            {"name": "Creative"},
                            {"name": "Experimental"}
                        ]
                    }
                },
                "Complexity": {
                    "type": "select",
                    "select": {
                        "options": [
                            {"name": "Low"},
                            {"name": "Medium"},
                            {"name": "High"}
                        ]
                    }
                },
                "Status": {
                    "type": "status",
                    "status": {
                        "options": [
                            {"name": "Not Started", "color": "gray"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Completed", "color": "green"}
                        ]
                    }
                },
                "Execution Date": {"type": "date", "date": {}},
                "AI Enhanced": {"type": "checkbox", "checkbox": {}}
            }
        }

        # In production:
        # response = requests.post(
        #     f"{self.base_url}/databases",
        #     headers=headers,
        #     json=database_schema
        # )
        # return response.json()['id']

        return "database_id_123"  # Mock response

    async def add_execution_to_database(
        self,
        database_id: str,
        execution_result: Dict[str, Any]
    ) -> str:
        """Add a prompt execution to the Notion database."""
        headers = {
            "Authorization": f"Bearer {self.integration_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        prompt = execution_result['prompt']

        page_data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Prompt ID": {
                    "title": [
                        {"text": {"content": prompt['id']}}
                    ]
                },
                "Prompt Text": {
                    "type": "text",
                    "text": {"content": prompt['prompt']}
                },
                "Type": {
                    "type": "select",
                    "select": {"name": prompt['type'].title()}
                },
                "Complexity": {
                    "type": "select",
                    "select": {"name": prompt['complexity'].title()}
                },
                "Status": {
                    "type": "status",
                    "status": {"name": "Completed"}
                },
                "Execution Date": {
                    "type": "date",
                    "date": {"start": execution_result['executed_at']}
                },
                "AI Enhanced": {
                    "type": "checkbox",
                    "checkbox": execution_result['use_ai']
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Expected Outputs"}}]
                    }
                }
            ]
        }

        # Add outputs as bullet points
        for output in prompt['outputs']:
            page_data["children"].append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": output}}]
                }
            })

        # In production:
        # response = requests.post(
        #     f"{self.base_url}/pages",
        #     headers=headers,
        #     json=page_data
        # )
        # return response.json()['id']

        return "page_id_123"  # Mock response


# ============================================================================
# Slack Integration Example
# ============================================================================

class SlackProductPromptsIntegration:
    """
    Integration between Product Management Prompts and Slack.

    Posts prompt executions and results to Slack channels.
    """

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def post_execution_to_channel(
        self,
        execution_result: Dict[str, Any],
        channel: str = "#product"
    ) -> bool:
        """Post a prompt execution to a Slack channel."""
        prompt = execution_result['prompt']

        message = {
            "channel": channel,
            "username": "Product Management Bot",
            "icon_emoji": ":rocket:",
            "attachments": [
                {
                    "color": "#36a64f",
                    "title": f"Product Prompt Executed: {prompt['prompt']}",
                    "fields": [
                        {
                            "title": "Prompt ID",
                            "value": prompt['id'],
                            "short": True
                        },
                        {
                            "title": "Type",
                            "value": prompt['type'].title(),
                            "short": True
                        },
                        {
                            "title": "Complexity",
                            "value": prompt['complexity'].title(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": prompt['estimated_time'],
                            "short": True
                        }
                    ],
                    "footer": f"Execution ID: {execution_result['execution_id']}",
                    "ts": execution_result['executed_at']
                }
            ]
        }

        # Add AI suggestion if available
        if execution_result.get('ai_suggestion'):
            message['attachments'][0]['text'] = f"*AI Suggestions:*\n{execution_result['ai_suggestion']}"

        # In production:
        # response = requests.post(self.webhook_url, json=message)
        # return response.status_code == 200

        return True  # Mock response

    async def post_workflow_summary(
        self,
        workflow_name: str,
        executions: List[Dict[str, Any]],
        channel: str = "#product"
    ):
        """Post a summary of workflow execution to Slack."""
        fields = [
            {
                "title": "Workflow",
                "value": workflow_name.replace('_', ' ').title(),
                "short": True
            },
            {
                "title": "Prompts Executed",
                "value": str(len(executions)),
                "short": True
            }
        ]

        message = {
            "channel": channel,
            "username": "Product Management Bot",
            "icon_emoji": ":white_check_mark:",
            "attachments": [
                {
                    "color": "#good",
                    "title": f"✅ Workflow Completed: {workflow_name}",
                    "fields": fields,
                    "footer": "Product Management Prompts",
                    "ts": executions[-1]['executed_at'] if executions else None
                }
            ]
        }

        # In production:
        # requests.post(self.webhook_url, json=message)
        pass


# ============================================================================
# Email Integration Example
# ============================================================================

class EmailProductPromptsIntegration:
    """
    Integration for emailing prompt execution results.

    Useful for sharing with stakeholders who aren't on the platform.
    """

    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    async def send_execution_report(
        self,
        execution_result: Dict[str, Any],
        recipients: List[str],
        include_ai_suggestions: bool = True
    ):
        """Send an email report of a prompt execution."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        prompt = execution_result['prompt']

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Product Management Prompt: {prompt['prompt']}"
        msg['From'] = self.email
        msg['To'] = ', '.join(recipients)

        # Create HTML content
        html_content = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              .header {{ background-color: #4A90E2; color: white; padding: 20px; }}
              .content {{ padding: 20px; }}
              .prompt {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
              .field {{ margin: 10px 0; }}
              .label {{ font-weight: bold; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h2>Product Management Prompt Execution</h2>
            </div>
            <div class="content">
              <div class="prompt">
                <h3>{prompt['prompt']}</h3>
                <div class="field">
                  <span class="label">Prompt ID:</span> {prompt['id']}<br>
                  <span class="label">Type:</span> {prompt['type'].title()}<br>
                  <span class="label">Complexity:</span> {prompt['complexity'].title()}<br>
                  <span class="label">Estimated Time:</span> {prompt['estimated_time']}
                </div>
              </div>

              <h4>Expected Outputs:</h4>
              <ul>
                {"".join(f"<li>{output}</li>" for output in prompt['outputs'])}
              </ul>

              <h4>Use Cases:</h4>
              <ul>
                {"".join(f"<li>{uc}</li>" for uc in prompt['use_cases'])}
              </ul>

              <p>
                <strong>Execution ID:</strong> {execution_result['execution_id']}<br>
                <strong>Executed At:</strong> {execution_result['executed_at']}<br>
                <strong>AI Enhanced:</strong> {"Yes" if execution_result['use_ai'] else "No"}
              </p>

              {f"<h4>AI Suggestions:</h4><p>{execution_result.get('ai_suggestion', '')}</p>" if include_ai_suggestions and execution_result.get('ai_suggestion') else ""}
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        # In production:
        # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
        #     server.starttls()
        #     server.login(self.email, self.password)
        #     server.send_message(msg)
        pass


# ============================================================================
# Example Usage
# ============================================================================

async def example_workflow_integration():
    """
    Example: Complete workflow integration with multiple tools.

    This demonstrates executing a prompt and syncing results to:
    1. Jira (create epic)
    2. Notion (log execution)
    3. Slack (notify team)
    4. Email (send report)
    """

    # Initialize integrations (with mock credentials)
    jira = JiraProductPromptsIntegration(
        jira_url="https://your-domain.atlassian.net",
        api_token="your-api-token",
        email="your-email@example.com"
    )

    notion = NotionProductPromptsIntegration(
        integration_token="your-notion-integration-token"
    )

    slack = SlackProductPromptsIntegration(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    )

    email = EmailProductPromptsIntegration(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        email="your-email@example.com",
        password="your-app-password"
    )

    # Execute a prompt (this would use the actual service)
    execution_result = {
        'prompt': {
            'id': 'rs_001',
            'prompt': 'Create a roadmap based on user value vs complexity.',
            'type': 'strategic',
            'complexity': 'medium',
            'estimated_time': '2-3 hours',
            'outputs': ['Prioritized feature matrix', 'Timeline visualization'],
            'use_cases': ['Quarterly planning', 'Product strategy reviews']
        },
        'execution_id': 12345,
        'executed_at': '2025-01-17T10:30:00Z',
        'use_ai': True,
        'ai_suggestion': 'Here\'s a strategic roadmap based on your criteria...'
    }

    # 1. Create Jira epic
    epic_key = await jira.create_epic_from_prompt(
        prompt_id='rs_001',
        execution_result=execution_result,
        project_key='PROD'
    )
    print(f"✅ Created Jira epic: {epic_key}")

    # 2. Log in Notion
    notion_page_id = await notion.add_execution_to_database(
        database_id='database_id_123',
        execution_result=execution_result
    )
    print(f"✅ Created Notion page: {notion_page_id}")

    # 3. Post to Slack
    await slack.post_execution_to_channel(
        execution_result=execution_result,
        channel="#product"
    )
    print(f"✅ Posted to Slack")

    # 4. Send email report
    await email.send_execution_report(
        execution_result=execution_result,
        recipients=['stakeholders@example.com']
    )
    print(f"✅ Sent email report")

    print("\n🎉 Workflow integration complete!")


if __name__ == '__main__':
    # Run the example
    asyncio.run(example_workflow_integration())
