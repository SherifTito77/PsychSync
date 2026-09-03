# app/services/ai_insights_service.py
"""
AI-Generated Insights Service
Uses GPT-4 to generate natural language insights from team personality data.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.cache import cache_get, cache_set
from app.core.cache_stamped_protection import cache_stampede_protect

logger = logging.getLogger(__name__)


class AIInsightsService:
    """
    Service for generating AI-powered insights about team personality composition.
    """

    # Prompts for different types of insights
    TEAM_INSIGHTS_PROMPT = """You are an expert organizational psychologist and team dynamics consultant.

Given the following team personality data (Big Five model: OCEAN), generate 3-5 actionable insights for the team manager.

Team Data:
- Team Size: {team_size} members
- Composition Type: {composition_type}
- Openness: {openness} (avg: {openness_avg}/5)
- Conscientiousness: {conscientiousness} (avg: {conscientiousness_avg}/5)
- Extraversion: {extraversion} (avg: {extraversion_avg}/5)
- Agreeableness: {agreeableness} (avg: {agreeableness_avg}/5)
- Neuroticism: {neuroticism} (avg: {neuroticism_avg}/5)
- Internal Compatibility: {compatibility}/1.0
- Diversity Score: {diversity}/1.0

Current Strengths: {strengths}
Current Gaps: {gaps}

Generate 3-5 specific, actionable insights. Each insight should:
1. Start with a clear heading
2. Explain the psychological rationale
3. Provide a concrete action the manager can take this week

Format your response as a JSON array of objects with "heading", "rationale", and "action" fields.

Example:
[
  {{
    "heading": "Leverage Creative Problem-Solving",
    "rationale": "Your team scores high in Openness (avg 4.2/5), which means they thrive on innovation and novel approaches.",
    "action": "In your next team meeting, introduce a 'wild idea' brainstorming session where no idea is too crazy. Your team will excel at generating creative solutions."
  }}
]

Respond ONLY with valid JSON, no additional text."""

    @staticmethod
    async def generate_team_insights(
        team_data: Dict[str, Any], use_cache: bool = True
    ) -> List[Dict[str, str]]:
        """
        Generate AI-powered insights for a team based on personality data.
        Uses cache stampede protection to prevent multiple concurrent API calls.

        Args:
            team_data: Dictionary with team personality data
            use_cache: If True, check cache for existing insights

        Returns:
            List of insight dictionaries with heading, rationale, and action
        """
        if not use_cache:
            # Bypass cache if requested
            return await AIInsightsService._generate_with_openai(team_data)

        # Use cache stampede protection to prevent multiple API calls
        cache_key = f"team_insights:{team_data.get('team_id')}"

        async def generate_insights():
            """Generator function for cache stampede protection"""
            try:
                insights = await AIInsightsService._generate_with_openai(team_data)
                return insights
            except Exception as e:
                logger.error(f"Error generating AI insights: {e}")
                raise

        try:
            # Cache stampede protection ensures only one request calls OpenAI
            insights = await cache_stampede_protect(
                cache_key=cache_key,
                generator=generate_insights,
                expire=86400,  # 24 hours
                lock_timeout=30,  # Max 30 seconds to generate
                wait_timeout=15,  # Wait up to 15 seconds for other request
            )
            return insights

        except Exception as e:
            # Fall back to rule-based insights if AI fails
            print(f"AI insights generation failed: {e}, using rule-based fallback")

        return AIInsightsService._generate_rule_based_insights(team_data)

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _generate_with_openai(
        team_data: Dict[str, Any]
    ) -> Optional[List[Dict[str, str]]]:
        """
        Generate insights using OpenAI GPT-4 API.

        Features:
        - Retry with exponential backoff on connection errors
        - 30-second timeout to prevent hanging
        - Graceful fallback to rule-based insights

        Args:
            team_data: Team personality data

        Returns:
            List of insights or None if API call fails
        """
        try:
            import openai
            from openai import APITimeoutError, RateLimitError

            # Check if API key is available
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not configured")
                return None

            # Create client with explicit timeout
            client = openai.AsyncOpenAI(
                api_key=api_key, timeout=30.0  # 30-second timeout
            )

            # Build prompt
            prompt = AIInsightsService.TEAM_INSIGHTS_PROMPT.format(
                team_size=team_data.get("team_size", 0),
                composition_type=team_data.get("composition_type", "Unknown"),
                openness=team_data.get("openness", {}),
                openness_avg=team_data.get("openness", {}).get("avg", 0),
                conscientiousness=team_data.get("conscientiousness", {}),
                conscientiousness_avg=team_data.get("conscientiousness", {}).get(
                    "avg", 0
                ),
                extraversion=team_data.get("extraversion", {}),
                extraversion_avg=team_data.get("extraversion", {}).get("avg", 0),
                agreeableness=team_data.get("agreeableness", {}),
                agreeableness_avg=team_data.get("agreeableness", {}).get("avg", 0),
                neuroticism=team_data.get("neuroticism", {}),
                neuroticism_avg=team_data.get("neuroticism", {}).get("avg", 0),
                compatibility=team_data.get("internal_compatibility", 0),
                diversity=team_data.get("diversity_score", 0),
                strengths=", ".join(team_data.get("strengths", [])),
                gaps=", ".join(team_data.get("gaps", [])),
            )

            logger.info(f"Calling OpenAI API for team {team_data.get('team_id')}")

            # Call GPT-4
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert organizational psychologist.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Try to parse JSON
            insights = json.loads(content)

            # Validate structure
            if isinstance(insights, list) and all(
                "heading" in insight and "rationale" in insight and "action" in insight
                for insight in insights
            ):
                logger.info(
                    f"Successfully generated AI insights for team {team_data.get('team_id')}"
                )
                return insights

        except (APITimeoutError, RateLimitError) as e:
            logger.error(f"OpenAI API error (will retry): {e}")
            raise  # Re-raise for tenacity to retry

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return None

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return None

        return None

    @staticmethod
    def _generate_rule_based_insights(
        team_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate rule-based insights (fallback when AI is unavailable).

        Args:
            team_data: Team personality data

        Returns:
            List of insight dictionaries
        """
        insights = []

        # Get average scores
        openness = team_data.get("openness", {}).get("avg", 0)
        conscientiousness = team_data.get("conscientiousness", {}).get("avg", 0)
        extraversion = team_data.get("extraversion", {}).get("avg", 0)
        agreeableness = team_data.get("agreeableness", {}).get("avg", 0)
        neuroticism = team_data.get("neuroticism", {}).get("avg", 0)

        strengths = team_data.get("strengths", [])
        gaps = team_data.get("gaps", [])
        diversity = team_data.get("diversity_score", 0)
        compatibility = team_data.get("internal_compatibility", 0)

        # Insight 1: Leverage highest dimension
        highest_dim = max(
            [
                ("Openness", openness),
                ("Conscientiousness", conscientiousness),
                ("Extraversion", extraversion),
                ("Agreeableness", agreeableness),
                ("Stability", 5 - neuroticism),  # Invert neuroticism
            ],
            key=lambda x: x[1],
        )

        if highest_dim[1] >= 3.5:
            if highest_dim[0] == "Openness":
                insights.append(
                    {
                        "heading": "Leverage Creative Problem-Solving",
                        "rationale": f"Your team scores high in Openness ({highest_dim[1]:.1f}/5), which means they thrive on innovation and novel approaches to challenges.",
                        "action": "In your next team meeting, introduce a 'wild idea' brainstorming session where no idea is too crazy. Your team will excel at generating creative solutions.",
                    }
                )
            elif highest_dim[0] == "Conscientiousness":
                insights.append(
                    {
                        "heading": "Capitalize on Organizational Strength",
                        "rationale": f"Your team scores high in Conscientiousness ({highest_dim[1]:.1f}/5), indicating strong self-discipline and attention to detail.",
                        "action": "Assign complex, multi-step projects that require careful planning and follow-through. Your team will execute reliably.",
                    }
                )
            elif highest_dim[0] == "Extraversion":
                insights.append(
                    {
                        "heading": "Maximize Collaborative Energy",
                        "rationale": f"Your team scores high in Extraversion ({highest_dim[1]:.1f}/5), meaning they gain energy from social interaction and collaboration.",
                        "action": "Schedule regular team check-ins and collaborative work sessions. Avoid isolating team members for long periods.",
                    }
                )
            elif highest_dim[0] == "Agreeableness":
                insights.append(
                    {
                        "heading": "Foster Collaborative Culture",
                        "rationale": f"Your team scores high in Agreeableness ({highest_dim[1]:.1f}/5), indicating a cooperative and supportive team dynamic.",
                        "action": "Continue fostering the positive team culture. Consider peer mentoring programs to leverage this natural cooperation.",
                    }
                )
            elif highest_dim[0] == "Stability":
                insights.append(
                    {
                        "heading": "Build on Emotional Resilience",
                        "rationale": f"Your team shows high emotional stability (low Neuroticism: {neuroticism:.1f}/5), meaning they handle stress well.",
                        "action": "Your team can handle high-pressure situations. Consider them for critical projects or crisis response.",
                    }
                )

        # Insight 2: Address lowest dimension (gap)
        lowest_dim = min(
            [
                ("Openness", openness),
                ("Conscientiousness", conscientiousness),
                ("Extraversion", extraversion),
                ("Agreeableness", agreeableness),
                ("Neuroticism", neuroticism),
            ],
            key=lambda x: x[1],
        )

        if lowest_dim[1] <= 2.5:
            if lowest_dim[0] == "Openness":
                insights.append(
                    {
                        "heading": "Encourage Openness to New Ideas",
                        "rationale": f"Your team scores lower in Openness ({lowest_dim[1]:.1f}/5), which may indicate resistance to change or preference for established methods.",
                        "action": "When introducing changes, provide clear rationale and gradual implementation. Pair team members to challenge each other's thinking.",
                    }
                )
            elif lowest_dim[0] == "Conscientiousness":
                insights.append(
                    {
                        "heading": "Strengthen Project Management",
                        "rationale": f"Your team scores lower in Conscientiousness ({lowest_dim[1]:.1f}/5), which may lead to challenges with organization and follow-through.",
                        "action": "Implement structured project management tools (Asana, Jira) with clear deadlines and check-ins. Break large projects into smaller, manageable tasks.",
                    }
                )
            elif lowest_dim[0] == "Extraversion":
                insights.append(
                    {
                        "heading": "Balance Communication Styles",
                        "rationale": f"Your team scores lower in Extraversion ({lowest_dim[1]:.1f}/5), indicating members may prefer independent work and need time to recharge.",
                        "action": "Provide options for both collaborative and focused individual work. Share meeting agendas in advance so introverted members can prepare.",
                    }
                )
            elif lowest_dim[0] == "Agreeableness":
                insights.append(
                    {
                        "heading": "Proactively Manage Conflict",
                        "rationale": f"Your team scores lower in Agreeableness ({lowest_dim[1]:.1f}/5), which may lead to more direct but potentially friction-prone communication.",
                        "action": "Establish clear conflict resolution protocols. Encourage respectful debate and remind team members that disagreement is healthy when handled constructively.",
                    }
                )
            elif lowest_dim[0] == "Neuroticism":
                insights.append(
                    {
                        "heading": "Support Stress Management",
                        "rationale": f"Your team scores higher in Neuroticism ({lowest_dim[1]:.1f}/5), indicating members may be more susceptible to stress and pressure.",
                        "action": "Check in regularly on team well-being. Provide resources for stress management and consider workload balancing during high-pressure periods.",
                    }
                )

        # Insight 3: Diversity and compatibility
        if diversity < 0.3:
            insights.append(
                {
                    "heading": "Increase Perspective Diversity",
                    "rationale": f"Your team has low personality diversity ({diversity:.2f}/1.0), which can lead to groupthink and missed perspectives.",
                    "action": "When hiring, look for candidates who complement the team's personality profile. Consider cross-training with other teams to expose your team to different working styles.",
                }
            )
        elif diversity > 0.7:
            insights.append(
                {
                    "heading": "Harness Diverse Strengths",
                    "rationale": f"Your team has high personality diversity ({diversity:.2f}/1.0), which is a strength for innovation but may require extra coordination.",
                    "action": "Leverage diverse perspectives in brainstorming and problem-solving. Establish clear communication norms to ensure different styles complement rather than conflict.",
                }
            )

        if compatibility < 0.6:
            insights.append(
                {
                    "heading": "Improve Team Collaboration",
                    "rationale": f"Your team has lower internal compatibility ({compatibility:.2f}/1.0), which may lead to interpersonal friction or miscommunication.",
                    "action": "Invest in team building activities that help members understand each other's communication styles. Consider personality-based training workshops.",
                }
            )

        # Ensure we have at least 3 insights
        while len(insights) < 3:
            insights.append(
                {
                    "heading": "Continue Team Development",
                    "rationale": "Regular team development and check-ins are essential for maintaining high performance.",
                    "action": "Schedule monthly 1-on-1s with each team member to discuss their development goals and how the team can better support them.",
                }
            )

        return insights[:5]  # Return max 5 insights


# Singleton instance
ai_insights_service = AIInsightsService()
