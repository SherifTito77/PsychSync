"""
Assessment Questions Endpoints
Provides assessment questions for different personality frameworks
"""

from fastapi import APIRouter

from app.core.response import create_error_response

router = APIRouter(prefix="/assessments", tags=["assessment-questions"])


# ==================== MBTI ASSESSMENT ====================


@router.get("/assessment-questions/mbti")
async def get_mbti_assessment_questions():
    """
    Get MBTI assessment questions - Simple working version
    """
    try:
        mbti_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "mbti-standard",
                "title": "Myers-Briggs Type Indicator (MBTI) Assessment",
                "description": "Discover your MBTI personality type",
                "instructions": "Choose the option that feels most natural to you",
                "estimated_time": "15-20 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "At parties, you usually:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Talk to many people, even strangers",
                                "value": "E",
                            },
                            {
                                "text": "Talk to a few people you know well",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "You prefer to:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Focus on reality and practical details",
                                "value": "S",
                            },
                            {
                                "text": "Imagine possibilities and explore ideas",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "When making decisions, you:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Prioritize logic and objective analysis",
                                "value": "T",
                            },
                            {
                                "text": "Consider values and impact on people",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "You prefer your life to be:",
                        "dimension": "J-P",
                        "options": [
                            {"text": "Planned and structured", "value": "J"},
                            {"text": "Flexible and spontaneous", "value": "P"},
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "You get energy from:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Being with people and social activities",
                                "value": "E",
                            },
                            {"text": "Quiet time and reflection", "value": "I"},
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "You are more interested in:",
                        "dimension": "S-N",
                        "options": [
                            {"text": "What is actual and present", "value": "S"},
                            {
                                "text": "What could be and future possibilities",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "In decision-making, you value:",
                        "dimension": "T-F",
                        "options": [
                            {"text": "Justice and fairness principles", "value": "T"},
                            {"text": "Harmony and compassion", "value": "F"},
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "You approach tasks with:",
                        "dimension": "J-P",
                        "options": [
                            {"text": "Planning and organization", "value": "J"},
                            {
                                "text": "Adaptability and keeping options open",
                                "value": "P",
                            },
                        ],
                    },
                    {
                        "id": 9,
                        "question_text": "You prefer to learn by:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Hands-on experience and practical application",
                                "value": "S",
                            },
                            {
                                "text": "Understanding theories and underlying principles",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 10,
                        "question_text": "In group discussions, you tend to:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Speak up frequently and share ideas openly",
                                "value": "E",
                            },
                            {
                                "text": "Listen carefully and speak only when necessary",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 11,
                        "question_text": "When analyzing a problem, you focus on:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Logical consistency and objective facts",
                                "value": "T",
                            },
                            {
                                "text": "How it affects people and relationships",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 12,
                        "question_text": "You prefer work that is:",
                        "dimension": "J-P",
                        "options": [
                            {
                                "text": "Well-organized with clear deadlines",
                                "value": "J",
                            },
                            {"text": "Flexible with room for creativity", "value": "P"},
                        ],
                    },
                    {
                        "id": 13,
                        "question_text": "You prefer conversations that are:",
                        "dimension": "S-N",
                        "options": [
                            {"text": "Factual and straightforward", "value": "S"},
                            {"text": "Conceptual and theoretical", "value": "N"},
                        ],
                    },
                    {
                        "id": 14,
                        "question_text": "You recharge your batteries by:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Socializing and interacting with others",
                                "value": "E",
                            },
                            {
                                "text": "Spending time alone in quiet activities",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 15,
                        "question_text": "When giving feedback, you:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Be direct and objective about improvements",
                                "value": "T",
                            },
                            {
                                "text": "Be encouraging and consider feelings",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 16,
                        "question_text": "You prefer to make plans:",
                        "dimension": "J-P",
                        "options": [
                            {
                                "text": "Well in advance with detailed schedules",
                                "value": "J",
                            },
                            {"text": "Spontaneously as situations arise", "value": "P"},
                        ],
                    },
                    {
                        "id": 17,
                        "question_text": "You trust information that is:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Concrete and proven through experience",
                                "value": "S",
                            },
                            {
                                "text": "Based on patterns and intuitive insights",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 18,
                        "question_text": "In meetings, you prefer to:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Actively participate and lead discussions",
                                "value": "E",
                            },
                            {
                                "text": "Observe and contribute when you have something valuable",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 19,
                        "question_text": "You approach conflicts by:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Analyzing the facts logically to find the truth",
                                "value": "T",
                            },
                            {
                                "text": "Considering everyone's feelings and finding compromise",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 20,
                        "question_text": "You prefer your workspace to be:",
                        "dimension": "J-P",
                        "options": [
                            {"text": "Organized, tidy, and systematic", "value": "J"},
                            {"text": "Flexible and creatively arranged", "value": "P"},
                        ],
                    },
                    {
                        "id": 21,
                        "question_text": "When traveling, you prefer to:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Follow a detailed itinerary and planned activities",
                                "value": "S",
                            },
                            {
                                "text": "Explore freely and follow spontaneous interests",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 22,
                        "question_text": "You prefer social situations that are:",
                        "dimension": "E-I",
                        "options": [
                            {"text": "Lively with lots of interaction", "value": "E"},
                            {
                                "text": "Intimate with deep one-on-one conversations",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 23,
                        "question_text": "You make judgments based on:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Impersonal criteria and universal principles",
                                "value": "T",
                            },
                            {
                                "text": "Personal values and impact on individuals",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 24,
                        "question_text": "You approach deadlines with:",
                        "dimension": "J-P",
                        "options": [
                            {
                                "text": "Early completion and time to spare",
                                "value": "J",
                            },
                            {"text": "Last-minute energy under pressure", "value": "P"},
                        ],
                    },
                    {
                        "id": 25,
                        "question_text": "You're more drawn to:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Practical skills and real-world applications",
                                "value": "S",
                            },
                            {
                                "text": "Theoretical concepts and abstract ideas",
                                "value": "N",
                            },
                        ],
                    },
                    {
                        "id": 26,
                        "question_text": "After a long week, you prefer to:",
                        "dimension": "E-I",
                        "options": [
                            {"text": "Go out and socialize with friends", "value": "E"},
                            {
                                "text": "Stay home and recharge with quiet activities",
                                "value": "I",
                            },
                        ],
                    },
                    {
                        "id": 27,
                        "question_text": "You believe rules should be:",
                        "dimension": "T-F",
                        "options": [
                            {
                                "text": "Applied consistently and logically",
                                "value": "T",
                            },
                            {
                                "text": "Flexible based on individual circumstances",
                                "value": "F",
                            },
                        ],
                    },
                    {
                        "id": 28,
                        "question_text": "You prefer to finish projects:",
                        "dimension": "J-P",
                        "options": [
                            {
                                "text": "Completely before moving to the next",
                                "value": "J",
                            },
                            {
                                "text": "When inspiration strikes or deadlines approach",
                                "value": "P",
                            },
                        ],
                    },
                    {
                        "id": 29,
                        "question_text": "You notice:",
                        "dimension": "S-N",
                        "options": [
                            {
                                "text": "Specific details and observable facts",
                                "value": "S",
                            },
                            {"text": "Underlying patterns and meanings", "value": "N"},
                        ],
                    },
                    {
                        "id": 30,
                        "question_text": "In decision-making meetings, you:",
                        "dimension": "E-I",
                        "options": [
                            {
                                "text": "Think out loud and process verbally",
                                "value": "E",
                            },
                            {
                                "text": "Process internally before sharing conclusions",
                                "value": "I",
                            },
                        ],
                    },
                ],
            },
        }
        return mbti_assessment
    except Exception as e:
        return create_error_response(f"Failed to load MBTI assessment: {e!s}")


# ==================== ENNEAGRAM ASSESSMENT ====================


@router.get("/assessment-questions/enneagram")
async def get_enneagram_assessment_questions():
    """
    Get Enneagram assessment questions
    """
    try:
        enneagram_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "enneagram-standard",
                "title": "Enneagram Personality Assessment",
                "description": "Discover your Enneagram personality type",
                "instructions": "Choose the option that best describes you most of the time",
                "estimated_time": "20-25 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "I have a strong inner critic that constantly evaluates my actions",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type1"},
                            {"text": "Somewhat true", "value": "type1_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "I find it essential to help others and meet their needs",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type2"},
                            {"text": "Somewhat true", "value": "type2_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "I am driven to achieve success and be recognized for my accomplishments",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type3"},
                            {"text": "Somewhat true", "value": "type3_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "I often feel misunderstood and different from others",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type4"},
                            {"text": "Somewhat true", "value": "type4_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "I prefer to observe and analyze rather than actively participate",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type5"},
                            {"text": "Somewhat true", "value": "type5_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "I am constantly vigilant for potential threats or dangers",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type6"},
                            {"text": "Somewhat true", "value": "type6_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "I always look for new adventures and experiences",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type7"},
                            {"text": "Somewhat true", "value": "type7_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "I take charge of situations and don't back down from challenges",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type8"},
                            {"text": "Somewhat true", "value": "type8_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 9,
                        "question_text": "I avoid conflict and prefer to go along with others to maintain peace",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type9"},
                            {"text": "Somewhat true", "value": "type9_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 10,
                        "question_text": "I feel a strong need to follow rules and do things the 'right' way",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type1"},
                            {"text": "Somewhat true", "value": "type1_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 11,
                        "question_text": "I often put others' needs before my own",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type2"},
                            {"text": "Somewhat true", "value": "type2_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 12,
                        "question_text": "I am highly concerned with how others perceive me",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type3"},
                            {"text": "Somewhat true", "value": "type3_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 13,
                        "question_text": "I have intense emotions and can be melodramatic at times",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type4"},
                            {"text": "Somewhat true", "value": "type4_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 14,
                        "question_text": "I need plenty of alone time to recharge and think",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type5"},
                            {"text": "Somewhat true", "value": "type5_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 15,
                        "question_text": "I often doubt my own decisions and seek reassurance from others",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type6"},
                            {"text": "Somewhat true", "value": "type6_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 16,
                        "question_text": "I dislike routine and prefer to keep my options open",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type7"},
                            {"text": "Somewhat true", "value": "type7_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 17,
                        "question_text": "I confront problems directly and don't mind making tough decisions",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type8"},
                            {"text": "Somewhat true", "value": "type8_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                    {
                        "id": 18,
                        "question_text": "I tend to procrastinate and avoid difficult tasks",
                        "type": "single-choice",
                        "options": [
                            {"text": "Very true", "value": "type9"},
                            {"text": "Somewhat true", "value": "type9_moderate"},
                            {"text": "Not very true", "value": "other"},
                        ],
                    },
                ],
            },
        }
        return enneagram_assessment
    except Exception as e:
        return create_error_response(f"Failed to load Enneagram assessment: {e!s}")


# ==================== BIG FIVE ASSESSMENT ====================


@router.get("/assessment-questions/big-five")
async def get_big_five_assessment_questions():
    """
    Get Big Five (OCEAN) assessment questions
    """
    try:
        big_five_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "big-five-standard",
                "title": "Big Five Personality Assessment (OCEAN)",
                "description": "Discover your Big Five personality traits",
                "instructions": "Rate how much each statement describes you",
                "estimated_time": "15-20 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "I am the life of the party",
                        "type": "likert",
                        "trait": "E",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "I sympathize with others' feelings",
                        "type": "likert",
                        "trait": "A",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "I get chores done right away",
                        "type": "likert",
                        "trait": "C",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "I have a vivid imagination",
                        "type": "likert",
                        "trait": "O",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "I worry about things",
                        "type": "likert",
                        "trait": "N",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "I start conversations",
                        "type": "likert",
                        "trait": "E",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "I feel others' emotions",
                        "type": "likert",
                        "trait": "A",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "I like order",
                        "type": "likert",
                        "trait": "C",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 9,
                        "question_text": "I have excellent ideas",
                        "type": "likert",
                        "trait": "O",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                    {
                        "id": 10,
                        "question_text": "I am easily disturbed",
                        "type": "likert",
                        "trait": "N",
                        "options": [
                            {"text": "Strongly Disagree", "value": 1},
                            {"text": "Disagree", "value": 2},
                            {"text": "Neutral", "value": 3},
                            {"text": "Agree", "value": 4},
                            {"text": "Strongly Agree", "value": 5},
                        ],
                    },
                ],
            },
        }
        return big_five_assessment
    except Exception as e:
        return create_error_response(f"Failed to load Big Five assessment: {e!s}")


# ==================== DISC ASSESSMENT ====================


@router.get("/assessment-questions/disc")
async def get_disc_assessment_questions():
    """
    Get DISC assessment questions
    """
    try:
        disc_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "disc-standard",
                "title": "DISC Personality Assessment",
                "description": "Discover your DISC personality type",
                "instructions": "Choose the answer that is most true for you",
                "estimated_time": "15-20 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "In group situations, I tend to be",
                        "type": "single-choice",
                        "options": [
                            {"text": "Direct and assertive", "value": "D"},
                            {"text": "Optimistic and friendly", "value": "I"},
                            {"text": "Patient and reliable", "value": "S"},
                            {"text": "Analytical and precise", "value": "C"},
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "When faced with a problem, I",
                        "type": "single-choice",
                        "options": [
                            {"text": "Take immediate action", "value": "D"},
                            {"text": "Involve others for solutions", "value": "I"},
                            {"text": "Maintain stability and support", "value": "S"},
                            {"text": "Analyze all details first", "value": "C"},
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "My communication style is typically",
                        "type": "single-choice",
                        "options": [
                            {"text": "Bold and straightforward", "value": "D"},
                            {"text": "Enthusiastic and inspiring", "value": "I"},
                            {"text": "Calm and supportive", "value": "S"},
                            {"text": "Logical and detailed", "value": "C"},
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "When making decisions, I prefer to",
                        "type": "single-choice",
                        "options": [
                            {"text": "Decide quickly and act", "value": "D"},
                            {"text": "Consider impact on people", "value": "I"},
                            {"text": "Take time to decide", "value": "S"},
                            {"text": "Research thoroughly first", "value": "C"},
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "In conflict situations, I tend to",
                        "type": "single-choice",
                        "options": [
                            {"text": "Confront it directly", "value": "D"},
                            {"text": "Try to smooth things over", "value": "I"},
                            {"text": "Avoid confrontation", "value": "S"},
                            {"text": "Analyze the causes", "value": "C"},
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "I work best when I can",
                        "type": "single-choice",
                        "options": [
                            {"text": "Lead and direct others", "value": "D"},
                            {"text": "Inspire and motivate people", "value": "I"},
                            {"text": "Support and help the team", "value": "S"},
                            {"text": "Focus on accuracy and quality", "value": "C"},
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "My approach to deadlines is",
                        "type": "single-choice",
                        "options": [
                            {"text": "Work intensely to finish early", "value": "D"},
                            {"text": "Rely on last-minute energy", "value": "I"},
                            {"text": "Plan and work steadily", "value": "S"},
                            {"text": "Need extra time for perfection", "value": "C"},
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "When receiving feedback, I typically",
                        "type": "single-choice",
                        "options": [
                            {"text": "Defend my position", "value": "D"},
                            {"text": "Take it personally at first", "value": "I"},
                            {"text": "Accept it quietly", "value": "S"},
                            {"text": "Want detailed explanations", "value": "C"},
                        ],
                    },
                ],
            },
        }
        return disc_assessment
    except Exception as e:
        return create_error_response(f"Failed to load DISC assessment: {e!s}")


# ==================== PREDICTIVE INDEX ASSESSMENT ====================


@router.get("/assessment-questions/predictive-index")
async def get_predictive_index_assessment_questions():
    """
    Get Predictive Index assessment questions
    """
    try:
        predictive_index_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "predictive-index-standard",
                "title": "Predictive Index Behavioral Assessment",
                "description": "Understand your workplace behaviors and drives",
                "instructions": "Choose the word that describes you MOST and LEAST in each set",
                "estimated_time": "10-15 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "Which word BEST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Analytical", "value": "A"},
                            {"text": "Social", "value": "B"},
                            {"text": "Patient", "value": "C"},
                            {"text": "Formal", "value": "D"},
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "Which word LEAST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Analytical", "value": "A"},
                            {"text": "Social", "value": "B"},
                            {"text": "Patient", "value": "C"},
                            {"text": "Formal", "value": "D"},
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "Which word BEST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Driving", "value": "A"},
                            {"text": "Warm", "value": "B"},
                            {"text": "Peaceful", "value": "C"},
                            {"text": "Precise", "value": "D"},
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "Which word LEAST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Driving", "value": "A"},
                            {"text": "Warm", "value": "B"},
                            {"text": "Peaceful", "value": "C"},
                            {"text": "Precise", "value": "D"},
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "Which word BEST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Forceful", "value": "A"},
                            {"text": "Empathetic", "value": "B"},
                            {"text": "Consistent", "value": "C"},
                            {"text": "Structured", "value": "D"},
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "Which word LEAST describes you?",
                        "type": "word-selection",
                        "options": [
                            {"text": "Forceful", "value": "A"},
                            {"text": "Empathetic", "value": "B"},
                            {"text": "Consistent", "value": "C"},
                            {"text": "Structured", "value": "D"},
                        ],
                    },
                ],
            },
        }
        return predictive_index_assessment
    except Exception as e:
        return create_error_response(
            f"Failed to load Predictive Index assessment: {e!s}"
        )


# ==================== SOCIAL STYLES ASSESSMENT ====================


@router.get("/assessment-questions/social-styles")
async def get_social_styles_assessment_questions():
    """
    Get Social Styles assessment questions
    """
    try:
        social_styles_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "social-styles-standard",
                "title": "Social Styles Assessment",
                "description": "Discover your social style and communication preferences",
                "instructions": "Choose the response that is most like you",
                "estimated_time": "10-15 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "When working with others, I tend to be",
                        "type": "single-choice",
                        "options": [
                            {"text": "Direct and fast-paced", "value": "Driver"},
                            {"text": "Direct and slower-paced", "value": "Analytical"},
                            {"text": "Indirect and slower-paced", "value": "Amiable"},
                            {"text": "Indirect and fast-paced", "value": "Expressive"},
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "In meetings, I usually",
                        "type": "single-choice",
                        "options": [
                            {
                                "text": "Focus on results and efficiency",
                                "value": "Driver",
                            },
                            {
                                "text": "Focus on facts and details",
                                "value": "Analytical",
                            },
                            {
                                "text": "Focus on relationships and harmony",
                                "value": "Amiable",
                            },
                            {
                                "text": "Focus on ideas and enthusiasm",
                                "value": "Expressive",
                            },
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "When making decisions, I prefer",
                        "type": "single-choice",
                        "options": [
                            {
                                "text": "Quick decisions based on logic",
                                "value": "Driver",
                            },
                            {
                                "text": "Careful analysis of all options",
                                "value": "Analytical",
                            },
                            {
                                "text": "Considering everyone's feelings",
                                "value": "Amiable",
                            },
                            {
                                "text": "Trusting my intuition and vision",
                                "value": "Expressive",
                            },
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "My communication style is",
                        "type": "single-choice",
                        "options": [
                            {"text": "Brief and to the point", "value": "Driver"},
                            {"text": "Detailed and thorough", "value": "Analytical"},
                            {"text": "Supportive and listening", "value": "Amiable"},
                            {
                                "text": "Animated and storytelling",
                                "value": "Expressive",
                            },
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "When dealing with conflict, I",
                        "type": "single-choice",
                        "options": [
                            {"text": "Address it head-on", "value": "Driver"},
                            {
                                "text": "Analyze the situation first",
                                "value": "Analytical",
                            },
                            {"text": "Try to maintain harmony", "value": "Amiable"},
                            {
                                "text": "Express my feelings openly",
                                "value": "Expressive",
                            },
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "I prefer to work",
                        "type": "single-choice",
                        "options": [
                            {
                                "text": "Independently with clear goals",
                                "value": "Driver",
                            },
                            {
                                "text": "Alone with detailed instructions",
                                "value": "Analytical",
                            },
                            {
                                "text": "In a supportive team environment",
                                "value": "Amiable",
                            },
                            {"text": "With people and variety", "value": "Expressive"},
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "When receiving feedback, I",
                        "type": "single-choice",
                        "options": [
                            {
                                "text": "Want it direct and actionable",
                                "value": "Driver",
                            },
                            {
                                "text": "Appreciate data and specifics",
                                "value": "Analytical",
                            },
                            {
                                "text": "Need reassurance and support",
                                "value": "Amiable",
                            },
                            {
                                "text": "Prefer positive recognition",
                                "value": "Expressive",
                            },
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "My approach to time is",
                        "type": "single-choice",
                        "options": [
                            {"text": "Time-conscious and efficient", "value": "Driver"},
                            {
                                "text": "Plan ahead and stick to schedule",
                                "value": "Analytical",
                            },
                            {"text": "Flexible and accommodating", "value": "Amiable"},
                            {
                                "text": "Spontaneous and energetic",
                                "value": "Expressive",
                            },
                        ],
                    },
                ],
            },
        }
        return social_styles_assessment
    except Exception as e:
        return create_error_response(f"Failed to load Social Styles assessment: {e!s}")


# ==================== STRENGTHSFINDER ASSESSMENT ====================


@router.get("/assessment-questions/strengthsfinder")
async def get_strengthsfinder_assessment_questions():
    """
    Get CliftonStrengths (StrengthsFinder) assessment questions
    """
    try:
        strengthsfinder_assessment = {
            "success": True,
            "status": "ok",
            "assessment": {
                "id": "strengthsfinder-standard",
                "title": "CliftonStrengths Assessment",
                "description": "Discover your top 5 talent themes",
                "instructions": "Choose the statement that best describes you between each pair",
                "estimated_time": "30-45 minutes",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I can quickly sense what others are feeling",
                                "value": "Empathy",
                            },
                            {
                                "text": "I enjoy thinking about complex problems",
                                "value": "Analytical",
                            },
                        ],
                    },
                    {
                        "id": 2,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I love to start new projects",
                                "value": "Activator",
                            },
                            {
                                "text": "I work hard to complete what I start",
                                "value": "Focus",
                            },
                        ],
                    },
                    {
                        "id": 3,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I enjoy being the center of attention",
                                "value": "Woo",
                            },
                            {
                                "text": "I prefer deep one-on-one conversations",
                                "value": "Individualization",
                            },
                        ],
                    },
                    {
                        "id": 4,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I am always looking for ways to improve",
                                "value": "Maximizer",
                            },
                            {
                                "text": "I am satisfied with good enough",
                                "value": "Consistency",
                            },
                        ],
                    },
                    {
                        "id": 5,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I need to understand the 'why' before acting",
                                "value": "Analytical",
                            },
                            {
                                "text": "I trust my instincts and act quickly",
                                "value": "Activator",
                            },
                        ],
                    },
                    {
                        "id": 6,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I set ambitious goals for myself",
                                "value": "Achiever",
                            },
                            {
                                "text": "I go with the flow and adapt easily",
                                "value": "Adaptability",
                            },
                        ],
                    },
                    {
                        "id": 7,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I enjoy organizing people and resources",
                                "value": "Arranger",
                            },
                            {
                                "text": "I enjoy thinking strategically about the future",
                                "value": "Strategic",
                            },
                        ],
                    },
                    {
                        "id": 8,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I believe everyone has potential",
                                "value": "Developer",
                            },
                            {
                                "text": "I recognize and celebrate others' achievements",
                                "value": "Positivity",
                            },
                        ],
                    },
                    {
                        "id": 9,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I confidently take charge of situations",
                                "value": "Command",
                            },
                            {
                                "text": "I build trust through consistency",
                                "value": "Responsibility",
                            },
                        ],
                    },
                    {
                        "id": 10,
                        "question_text": "Which statement is more like you?",
                        "type": "paired-choice",
                        "options": [
                            {
                                "text": "I learn for the joy of learning",
                                "value": "Learner",
                            },
                            {
                                "text": "I love to share what I've learned",
                                "value": "Input",
                            },
                        ],
                    },
                ],
            },
        }
        return strengthsfinder_assessment
    except Exception as e:
        return create_error_response(
            f"Failed to load StrengthsFinder assessment: {e!s}"
        )
