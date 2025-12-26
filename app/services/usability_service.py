"""
Usability Testing Service
Provides comprehensive usability testing frameworks, user feedback collection, and UX analysis tools
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class UsabilityTestType(str, Enum):
    """Types of usability tests"""
    MODERATED_TEST = "moderated_test"
    UNMODERATED_TEST = "unmoderated_test"
    A_B_TEST = "ab_test"
    TREE_TESTING = "tree_testing"
    CARD_SORTING = "card_sorting"
    FIRST_CLICK_TEST = "first_click_test"
    THINK_ALOUD_PROTOCOL = "think_aloud_protocol"
    SYSTEM_USABILITY_SCALE = "system_usability_scale"
    HEURISTIC_EVALUATION = "heuristic_evaluation"
    COGNITIVE_WALKTHROUGH = "cognitive_walkthrough"
    SURVEY = "survey"
    INTERVIEW = "interview"

class UsabilityMetric(str, Enum):
    """Usability metrics to measure"""
    TASK_SUCCESS_RATE = "task_success_rate"
    TIME_ON_TASK = "time_on_task"
    ERROR_RATE = "error_rate"
    SATISFACTION_SCORE = "satisfaction_score"
    LEARNABILITY = "learnability"
    EFFICIENCY = "efficiency"
    MEMORABILITY = "memorability"
    ERROR_RECOVERY = "error_recovery"
    NAVIGATION_EFFICIENCY = "navigation_efficiency"
    COMPLETION_RATE = "completion_rate"

class TaskDifficulty(str, Enum):
    """Task difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class UsabilityTask:
    """Individual usability test task"""

    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        instructions: str,
        difficulty: TaskDifficulty,
        category: str,
        success_criteria: List[str],
        expected_time: int,  # in seconds
        prerequisites: List[str] = None,
        test_data: Dict = None,
        screenshots: List[str] = None
    ):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.instructions = instructions
        self.difficulty = difficulty
        self.category = category
        self.success_criteria = success_criteria
        self.expected_time = expected_time
        self.prerequisites = prerequisites or []
        self.test_data = test_data or {}
        self.screenshots = screenshots or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "instructions": self.instructions,
            "difficulty": self.difficulty.value,
            "category": self.category,
            "success_criteria": self.success_criteria,
            "expected_time": self.expected_time,
            "prerequisites": self.prerequisites,
            "test_data": self.test_data,
            "screenshots": self.screenshots
        }

class UsabilityTestSession:
    """Complete usability test session with participant"""

    def __init__(
        self,
        session_id: str,
        test_type: UsabilityTestType,
        participant_id: str,
        participant_info: Dict,
        test_date: datetime,
        moderator_id: str = None,
        environment: str = "lab",
        device: str = "desktop",
        browser: str = "chrome",
        tasks: List[UsabilityTask] = None
    ):
        self.session_id = session_id
        self.test_type = test_type
        self.participant_id = participant_id
        self.participant_info = participant_info
        self.test_date = test_date
        self.moderator_id = moderator_id
        self.environment = environment
        self.device = device
        self.browser = browser
        self.tasks = tasks or []
        self.task_results = []
        self.session_notes = []
        self.audio_recording = None
        self.video_recording = None
        self.screen_recording = None
        self.session_duration = 0
        self.started_at = None
        self.completed_at = None

    def add_task_result(self, task_result: Dict[str, Any]):
        """Add result for completed task"""
        self.task_results.append(task_result)

    def add_session_note(self, note: str, timestamp: datetime = None, note_type: str = "observation"):
        """Add observation note during session"""
        note_entry = {
            "note": note,
            "timestamp": timestamp or datetime.utcnow(),
            "note_type": note_type
        }
        self.session_notes.append(note_entry)

    def calculate_session_metrics(self) -> Dict[str, Any]:
        """Calculate overall session metrics"""
        if not self.task_results:
            return {}

        total_tasks = len(self.task_results)
        successful_tasks = sum(1 for result in self.task_results if result.get("success", False))

        time_on_tasks = [result.get("completion_time", 0) for result in self.task_results]
        avg_time_on_task = sum(time_on_tasks) / len(time_on_tasks) if time_on_tasks else 0

        errors = sum(result.get("errors", 0) for result in self.task_results)

        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
            "avg_time_on_task": avg_time_on_task,
            "total_errors": errors,
            "error_rate": (errors / total_tasks) * 100 if total_tasks > 0 else 0,
            "session_duration": self.session_duration
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "test_type": self.test_type.value,
            "participant_id": self.participant_id,
            "participant_info": self.participant_info,
            "test_date": self.test_date.isoformat(),
            "moderator_id": self.moderator_id,
            "environment": self.environment,
            "device": self.device,
            "browser": self.browser,
            "tasks": [task.to_dict() for task in self.tasks],
            "task_results": self.task_results,
            "session_notes": self.session_notes,
            "session_duration": self.session_duration,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metrics": self.calculate_session_metrics()
        }

class SUS量表:
    """System Usability Scale (SUS) questionnaire"""

    def __init__(self):
        self.questions = [
            "I think that I would like to use this system frequently.",
            "I found the system unnecessarily complex.",
            "I thought the system was easy to use.",
            "I think that I would need the support of a technical person to be able to use this system.",
            "I found the various functions in this system were well integrated.",
            "I thought there was too much inconsistency in this system.",
            "I would imagine that most people would learn to use this system very quickly.",
            "I found the system very cumbersome to use.",
            "I felt very confident using the system."
        ]
        self.scoring = [1, 5, 1, 5, 1, 5, 1, 5, 1]  # Odd-numbered questions positive, even negative

    def calculate_score(self, responses: List[int]) -> float:
        """Calculate SUS score from questionnaire responses"""
        if len(responses) != len(self.questions):
            raise ValueError("Must have 10 responses")

        for i, response in enumerate(responses):
            if response < 1 or response > 5:
                raise ValueError("Responses must be on 1-5 scale")

        total_score = 0
        for i, response in enumerate(responses):
            # Convert scores: for even questions, score = 6 - response
            if i % 2 == 1:  # Even question (0-indexed)
                score = 6 - response
            else:
                score = response
            total_score += score

        return total_score * 2.5  # Convert to 0-100 scale

    def interpret_score(self, score: float) -> Dict[str, Any]:
        """Interpret SUS score with adjective ratings"""
        if score >= 90:
            adjective = "Excellent"
            grade = "A"
        elif score >= 80:
            adjective = "Good"
            grade = "B"
        elif score >= 70:
            adjective = "OK"
            grade = "C"
        elif score >= 60:
            adjective = "Poor"
            grade = "D"
        else:
            adjective = "Awful"
            grade = "F"

        return {
            "score": round(score, 1),
            "adjective": adjective,
            "grade": grade,
            "acceptability": "Acceptable" if score >= 70 else "Not Acceptable",
            "interpretation": self._get_interpretation(score)
        }

    def _get_interpretation(self, score: float) -> str:
        """Get detailed interpretation of SUS score"""
        if score >= 90:
            return "Users are extremely satisfied with the system. Minimal UX improvements needed."
        elif score >= 80:
            return "Users are satisfied with the system. Minor UX improvements may be beneficial."
        elif score >= 70:
            return "Users are moderately satisfied. Some UX improvements are recommended."
        elif score >= 60:
            return "Users have significant usability concerns. Major UX improvements needed."
        else:
            return "Users have serious usability problems. Complete UX overhaul recommended."

class UsabilityTestingService:
    """Comprehensive usability testing service"""

    def __init__(self):
        self.test_sessions = []
        self.sus_scale = SUS量表()
        self.test_environments = ["lab", "remote", "field", "online"]
        self.device_types = ["desktop", "laptop", "tablet", "mobile"]

    def create_core_usability_test_suite(self) -> List[UsabilityTask]:
        """Create core usability test suite for PsychSync"""

        tasks = [
            # Onboarding and Registration
            UsabilityTask(
                task_id="UT_001",
                title="New User Registration",
                description="Test how easily new users can register for PsychSync",
                instructions="As a new user, create an account using your email and a password. Complete the email verification process.",
                difficulty=TaskDifficulty.BEGINNER,
                category="onboarding",
                success_criteria=[
                    "User can find registration page",
                    "Registration form is clear and understandable",
                    "Email verification process works smoothly",
                    "User successfully creates account"
                ],
                expected_time=180,
                prerequisites=[]
            ),

            UsabilityTask(
                task_id="UT_002",
                title="First Assessment Experience",
                description="Test how easily users can take their first assessment",
                instructions="As a new user, select and complete the Big Five personality assessment. Answer all questions honestly.",
                difficulty=TaskDifficulty.BEGINNER,
                category="assessment",
                success_criteria=[
                    "User can find assessment page",
                    "Assessment interface is intuitive",
                    "Questions are clear and unambiguous",
                    "User can complete assessment without help",
                    "Results are displayed clearly"
                ],
                expected_time=300,
                prerequisites=["User has active account"]
            ),

            # Team Management
            UsabilityTask(
                task_id="UT_003",
                title="Create First Team",
                description="Test how easily users can create and manage teams",
                instructions="Create your first team for team optimization. Add at least one team member or complete a solo assessment.",
                difficulty=TaskDifficulty.INTERMEDIATE,
                category="team_management",
                success_criteria=[
                    "User can find team creation option",
                    "Team creation form is easy to complete",
                    "Team member invitation process works",
                    "Team dashboard is clear and informative"
                ],
                expected_time=240,
                prerequisites=["User has active account"]
            ),

            UsabilityTask(
                task_id="UT_004",
                title="Run Team Optimization",
                description="Test the team optimization feature usability",
                instructions="Select your team and run a team optimization analysis. Review the recommendations and insights provided.",
                difficulty=TaskDifficulty.INTERMEDIATE,
                category="team_optimization",
                success_criteria=[
                    "User can start optimization process",
                    "Progress indicators are clear",
                    "Results are easy to understand",
                    "Recommendations are actionable",
                    "User can save or apply recommendations"
                ],
                expected_time=180,
                prerequisites=["User has active team"]
            ),

            # Data Management
            UsabilityTask(
                task_id="UT_005",
                title="Export Personal Data",
                description="Test GDPR data export functionality",
                instructions="Request a copy of all your personal data in JSON format. Download and review the exported file.",
                difficulty=TaskDifficulty.ADVANCED,
                category="data_management",
                success_criteria=[
                    "User can find data export option",
                    "Export request process is clear",
                    "Download link works correctly",
                    "Exported file contains all expected data",
                    "Data format is readable and well-structured"
                ],
                expected_time=120,
                prerequisites=["User has active account"]
            ),

            UsabilityTask(
                task_id="UT_006",
                title="Update Privacy Settings",
                description="Test privacy and consent management settings",
                instructions="Navigate to privacy settings and manage your consent preferences. Try changing some settings.",
                difficulty=TaskDifficulty.INTERMEDIATE,
                category="privacy",
                success_criteria=[
                    "User can find privacy settings",
                    "Consent options are clearly explained",
                    "Settings changes are saved successfully",
                    "Consent history is accessible",
                    "Changes take effect immediately"
                ],
                expected_time=150,
                prerequisites=["User has active account"]
            ),

            # Dashboard and Analytics
            UsabilityTask(
                test_id="UT_007",
                title="Navigate Dashboard",
                description="Test dashboard navigation and information discovery",
                instructions="Explore the main dashboard. Find and review at least 3 different types of information or analytics.",
                difficulty=TaskDifficulty.BEGINNER,
                category="dashboard",
                success_criteria=[
                    "Dashboard layout is intuitive",
                    "Key information is easy to find",
                    "Navigation between sections is smooth",
                    "User can find personal analytics",
                    "System status indicators are clear"
                ],
                expected_time=120,
                prerequisites=["User has active account"]
            ),

            UsabilityTask(
                test_id="UT_008",
                title="Generate Assessment Report",
                description="Test assessment report generation and sharing",
                instructions="Generate a comprehensive assessment report for one of your completed assessments.",
                difficulty=TaskDifficulty.INTERMEDIATE,
                category="reporting",
                success_criteria=[
                    "User can access report generation",
                    "Report options are clear",
                    "Generated report contains all expected information",
                    "Report formatting is professional",
                    "Sharing options work correctly"
                ],
                expected_time=180,
                prerequisites=["User has completed assessment"]
            )
        ]

        return tasks

    def create_mobile_usability_test_suite(self) -> List[UsabilityTask]:
        """Create mobile-specific usability test suite"""

        mobile_tasks = [
            UsabilityTask(
                task_id="MOB_001",
                title="Mobile Navigation",
                description="Test mobile app navigation and touch interactions",
                instructions="Using a mobile device, navigate through the entire app. Test all main features using touch interactions.",
                difficulty=TaskDifficulty.BEGINNER,
                category="mobile",
                success_criteria=[
                    "Touch targets are appropriately sized",
                    "Navigation is thumb-friendly",
                    "No horizontal scrolling required",
                    "All features work on mobile",
                    "Text is readable without zooming"
                ],
                expected_time=300,
                prerequisites=["User has active account"]
            ),

            UsabilityTask(
                task_id="MOB_002",
                title="Mobile Assessment Experience",
                description="Test assessment completion on mobile device",
                instructions="Complete the Big Five assessment using a mobile device. Pay attention to question presentation and answer selection.",
                difficulty=TaskDifficulty.BEGINNER,
                category="mobile_assessment",
                success_criteria=[
                    "Questions display correctly on mobile",
                    "Answer selection is easy with touch",
                    "Progress is clearly indicated",
                    "Results display properly on mobile",
                    "No accidental submissions occur"
                ],
                expected_time=360,
                prerequisites=["User has active account"]
            )
        ]

        return mobile_tasks

    def conduct_sus_evaluation(self, participant_id: str, session_context: Dict) -> Dict[str, Any]:
        """Conduct System Usability Scale evaluation"""

        evaluation = {
            "evaluation_id": f"SUS_{participant_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "participant_id": participant_id,
            "evaluation_date": datetime.utcnow().isoformat(),
            "session_context": session_context,
            "questions": self.sus_scale.questions,
            "responses": [],
            "score": None,
            "interpretation": None
        }

        return evaluation

    def calculate_sus_score(self, evaluation: Dict[str, Any], responses: List[int]) -> Dict[str, Any]:
        """Calculate SUS score for evaluation"""

        try:
            score = self.sus_scale.calculate_score(responses)
            interpretation = self.sus_scale.interpret_score(score)

            evaluation["responses"] = responses
            evaluation["score"] = score
            evaluation["interpretation"] = interpretation

            return evaluation

        except ValueError as e:
            evaluation["error"] = str(e)
            return evaluation

    def create_heuristic_evaluation_checklist(self) -> List[Dict[str, Any]]:
        """Create Nielsen's 10 usability heuristics evaluation checklist"""

        heuristics = [
            {
                "heuristic": "Visibility of system status",
                "description": "The system should always keep users informed about what is going on, through appropriate feedback within reasonable time.",
                "checkpoints": [
                    "System status is clearly visible",
                    "Feedback is provided within reasonable time",
                    "Progress indicators are accurate",
                    "System state is communicated effectively",
                    "Status updates are timely and relevant"
                ],
                "severity": "critical"
            },
            {
                "heuristic": "Match between system and the real world",
                "description": "The system should speak the users' language, with words, phrases and concepts familiar to the user, rather than system-oriented terms.",
                "checkpoints": [
                    "Language is natural and user-friendly",
                    "Technical jargon is minimized",
                    "Icons and symbols are intuitive",
                    "Metaphors are consistent and helpful",
                    "Real-world conventions are followed"
                ],
                "severity": "critical"
            },
            {
                "heuristic": "User control and freedom",
                "description": "Users often choose system functions by mistake and will need a clearly marked 'emergency exit' to leave the unwanted state.",
                "checkpoints": [
                    "Undo/redo functionality is available",
                    "Clear exit paths from unwanted states",
                    "Easy to cancel operations",
                    "Confirmation dialogs for destructive actions",
                    "Users can reverse unintended actions"
                ],
                "severity": "critical"
            },
            {
                "heuristic": "Consistency and standards",
                "description": "Users should not have to wonder whether different words, situations, or actions mean the same thing.",
                "checkpoints": [
                    "Consistent terminology across interface",
                    "Design patterns are consistent",
                    "Standards and conventions are followed",
                    "Similar elements behave similarly",
                    "Visual consistency is maintained"
                ],
                "severity": "high"
            },
            {
                "heuristic": "Error prevention",
                "description": "Even better than good error messages is a careful design which prevents a problem from occurring in the first place.",
                "checkpoints": [
                    "Preventive measures in place",
                    "Clear constraints and restrictions",
                    "Confirmation for critical actions",
                    "Input validation and formatting",
                    "Helpful error prevention strategies"
                ],
                "severity": "critical"
            },
            {
                "heuristic": "Recognition rather than recall",
                "description": "Objects, actions, and options should be visible. The user should not have to remember information from one part of the dialogue to another.",
                "checkpoints": [
                    "Information is visible rather than remembered",
                    "Help is easily accessible",
                    "Options are clearly presented",
                    "Context is maintained",
                    "Previous actions are visible"
                ],
                "severity": "high"
            },
            {
                "heuristic": "Flexibility and efficiency of use",
                description": "Accelerators -- unseen by the novice user -- may often speed up the interaction for the expert user such that the system can cater to both inexperienced and experienced users.",
                "checkpoints": [
                    "Shortcuts are available for experts",
                    "Customization options are provided",
                    "Efficiency for experienced users",
                    "Flexible interaction patterns",
                    "Accelerators are discoverable"
                ],
                "severity": "medium"
            },
            {
                "heuristic": "Aesthetic and minimalist design",
                "description": "Dialogues should not contain information which is irrelevant or rarely needed.",
                "checkpoints": [
                    "Clean and uncluttered interface",
                    "Relevant information is prioritized",
                    "Visual hierarchy is clear",
                    "Minimalist design approach",
                    "No unnecessary elements"
                ],
                "severity": "low"
            },
            {
                "heuristic": "Help users recognize, diagnose, and recover from errors",
                "description": "Error messages should be expressed in plain language (no codes), precisely indicate the problem, and constructively suggest a solution.",
                "checkpoints": [
                    "Error messages are clear and helpful",
                    "Problems are precisely identified",
                    "Constructive solutions are suggested",
                    "Recovery paths are clear",
                    "Error prevention guidance is provided"
                ],
                "severity": "critical"
            },
            {
                "heuristic": "Help and documentation",
                "description": "Even though it is better if the system can be used without documentation, it may be necessary to provide help and documentation.",
                "checkpoints": [
                    "Help is easily accessible",
                    "Documentation is comprehensive",
                    "Context-sensitive help is available",
                    "Tutorials are helpful",
                    "FAQ answers common questions"
                ],
                "severity": "medium"
            }
        ]

        return heuristics

    def conduct_first_click_test(self, task_description: str, target_page: str) -> Dict[str, Any]:
        """Setup first click usability test"""

        first_click_test = {
            "test_id": f"FCT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "task_description": task_description,
            "target_page": target_page,
            "test_date": datetime.utcnow().isoformat(),
            "instructions": [
                "Show participant the task description",
                "Ask where they would click first",
                "Record their first-click choice",
                "Ask why they chose that location",
                "Measure time to first click",
                "Record success/failure of first click"
            ],
            "metrics": {
                "first_click_accuracy": 0,
                "time_to_first_click": 0,
                "confidence_before_task": 0,
                "confidence_after_task": 0,
                "task_completion_time": 0
            }
        }

        return first_click_test

    def generate_usability_report(self, session_id: str = None, include_sus: bool = True) -> str:
        """Generate comprehensive usability testing report"""

        if session_id:
            # Generate report for specific session
            session = next((s for s in self.test_sessions if s.session_id == session_id), None)
            if not session:
                return "Session not found"
        else:
            # Generate aggregate report
            session = None

        report_data = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": "aggregate" if not session else "session",
                "session_id": session.session_id if session else None
            },
            "summary": self._calculate_summary_metrics(),
            "recommendations": self._generate_usability_recommendations(),
            "next_steps": self._generate_next_steps()
        }

        if session:
            report_data["session_data"] = session.to_dict()
            report_data["individual_metrics"] = session.calculate_session_metrics()

        if include_sus and session:
            report_data["sus_results"] = self._aggregate_sus_data()

        return json.dumps(report_data, indent=2, default=str)

    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """Calculate summary metrics for all test sessions"""

        if not self.test_sessions:
            return {"message": "No test sessions available"}

        total_sessions = len(self.test_sessions)
        all_metrics = [session.calculate_session_metrics() for session in self.test_sessions]

        total_tasks = sum(metrics.get("total_tasks", 0) for metrics in all_metrics)
        total_successful = sum(metrics.get("successful_tasks", 0) for metrics in all_metrics)

        avg_success_rate = sum(metrics.get("success_rate", 0) for metrics in all_metrics) / len(all_metrics)
        avg_time_on_task = sum(metrics.get("avg_time_on_task", 0) for metrics in all_metrics) / len(all_metrics)

        return {
            "total_sessions": total_sessions,
            "total_tasks_attempted": total_tasks,
            "total_successful_tasks": total_successful,
            "overall_success_rate": avg_success_rate,
            "average_time_on_task": avg_time_on_task
        }

    def _generate_usability_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable usability recommendations"""

        return [
            {
                "category": "Navigation",
                "issue": "Complex navigation paths",
                "recommendation": "Simplify main navigation and improve information architecture",
                "priority": "high",
                "impact": "significant"
            },
            {
                "category": "Onboarding",
                "issue": "Unclear initial user journey",
                "recommendation": "Create guided onboarding flow with progressive disclosure",
                "priority": "high",
                "impact": "significant"
            },
            {
                "category": "Forms",
                "issue": "Complex forms with validation issues",
                "recommendation": "Simplify forms and provide better validation feedback",
                "priority": "medium",
                "impact": "moderate"
            },
            {
                "category": "Mobile",
                "issue": "Mobile usability challenges",
                "recommendation": "Optimize mobile experience and touch interactions",
                "priority": "high",
                "impact": "significant"
            }
        ]

    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for usability improvement"""

        return [
            "Schedule moderated usability testing sessions with target users",
            "Implement high-priority usability improvements identified",
            "Create user personas based on research findings",
            "Establish usability metrics and tracking",
            "Plan A/B testing for key interface improvements",
            "Develop accessibility compliance roadmap",
            "Create user feedback collection system",
            "Establish regular usability testing schedule"
        ]

    def _aggregate_sus_data(self) -> Dict[str, Any]:
        """Aggregate SUS scores across all sessions"""

        sus_scores = []
        for session in self.test_sessions:
            for task_result in session.task_results:
                if "sus_score" in task_result:
                    sus_scores.append(task_result["sus_score"])

        if not sus_scores:
            return {"message": "No SUS data available"}

        avg_score = sum(sus_scores) / len(sus_scores)
        interpretation = self.sus_scale.interpret_score(avg_score)

        return {
            "total_respondents": len(sus_scores),
            "average_score": round(avg_score, 1),
            "score_distribution": {
                "excellent": sum(1 for score in sus_scores if score >= 90),
                "good": sum(1 for score in sus_scores if 80 <= score < 90),
                "ok": sum(1 for score in sus_scores if 70 <= score < 80),
                "poor": sum(1 for score in sus_scores if 60 <= score < 70),
                "awful": sum(1 for score in sus_scores if score < 60)
            },
            "interpretation": interpretation
        }