"""
UAT Feedback Questions for Team Leaders
Comprehensive feedback collection system for user acceptance testing
"""

class UATFeedbackQuestion:
    def __init__(self, question_id, category, question_text, question_type, options=None, required=False):
        self.question_id = question_id
        self.category = category  # Usability, Functionality, BusinessValue, Performance, Overall
        self.question_text = question_text
        self.question_type = question_type  # rating, text, multiple_choice, boolean
        self.options = options  # For multiple choice questions
        self.required = required

class UATFeedbackSystem:
    """Comprehensive feedback system for team leader UAT"""

    def __init__(self):
        self.feedback_questions = self._generate_feedback_questions()

    def _generate_feedback_questions(self):
        """Generate comprehensive feedback questions for team leaders"""

        questions = []

        # === USABILITY QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-001",
            category="Usability",
            question_text="How easy was it to navigate the team leader dashboard?",
            question_type="rating",
            options=["Very Difficult (1)", "Difficult (2)", "Neutral (3)", "Easy (4)", "Very Easy (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-002",
            category="Usability",
            question_text="How intuitive was the process of creating your first team?",
            question_type="rating",
            options=["Very Confusing (1)", "Confusing (2)", "Neutral (3)", "Intuitive (4)", "Very Intuitive (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-003",
            category="Usability",
            question_text="Were the assessment creation steps clear and easy to follow?",
            question_type="rating",
            options=["Very Unclear (1)", "Unclear (2)", "Neutral (3)", "Clear (4)", "Very Clear (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-004",
            category="Usability",
            question_text="How would you rate the overall user interface design?",
            question_type="rating",
            options=["Poor (1)", "Fair (2)", "Good (3)", "Very Good (4)", "Excellent (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-005",
            category="Usability",
            question_text="Which aspect of the interface was most confusing? (Select all that apply)",
            question_type="multiple_choice",
            options=[
                "Team member invitation process",
                "Assessment configuration",
                "Results interpretation",
                "Dashboard navigation",
                "Report generation",
                "Settings configuration",
                "None - everything was clear"
            ],
            required=False
        ))

        # === FUNCTIONALITY QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-006",
            category="Functionality",
            question_text="Did all the features you expected work correctly?",
            question_type="boolean",
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-007",
            category="Functionality",
            question_text="How well did the assessment results reflect your team's characteristics?",
            question_type="rating",
            options=["Not at all (1)", "Poorly (2)", "Somewhat (3)", "Well (4)", "Very Well (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-008",
            category="Functionality",
            question_text="Were the team analytics and insights helpful for understanding your team?",
            question_type="rating",
            options=["Not Helpful (1)", "Slightly Helpful (2)", "Moderately Helpful (3)", "Helpful (4)", "Very Helpful (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-009",
            category="Functionality",
            question_text="Which features worked better than expected?",
            question_type="text",
            required=False
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-010",
            category="Functionality",
            question_text="Which features need improvement?",
            question_type="text",
            required=False
        ))

        # === BUSINESS VALUE QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-011",
            category="BusinessValue",
            question_text="How much time do you think this platform will save you in team management?",
            question_type="multiple_choice",
            options=[
                "No time savings",
                "1-2 hours per week",
                "3-5 hours per week",
                "6-10 hours per week",
                "More than 10 hours per week"
            ],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-012",
            category="BusinessValue",
            question_text="How valuable are the assessment insights for team development?",
            question_type="rating",
            options=["Not Valuable (1)", "Slightly Valuable (2)", "Moderately Valuable (3)", "Valuable (4)", "Very Valuable (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-013",
            category="BusinessValue",
            question_text="Would you recommend this platform to other team leaders?",
            question_type="rating",
            options=["Definitely Not (1)", "Probably Not (2)", "Might or Might Not (3)", "Probably Yes (4)", "Definitely Yes (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-014",
            category="BusinessValue",
            question_text="What specific business problem does this platform solve for you?",
            question_type="text",
            required=False
        ))

        # === PERFORMANCE QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-015",
            category="Performance",
            question_text="How would you rate the platform's response time?",
            question_type="rating",
            options=["Very Slow (1)", "Slow (2)", "Acceptable (3)", "Fast (4)", "Very Fast (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-016",
            category="Performance",
            question_text="Did you experience any crashes or technical issues?",
            question_type="multiple_choice",
            options=[
                "No issues at all",
                "Minor issues that didn't affect workflow",
                "Moderate issues that caused some delays",
                "Major issues that prevented completion",
                "System was completely unusable"
            ],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-017",
            category="Performance",
            question_text="How reliable was the platform during testing?",
            question_type="rating",
            options=["Very Unreliable (1)", "Unreliable (2)", "Neutral (3)", "Reliable (4)", "Very Reliable (5)"],
            required=True
        ))

        # === OVERALL EXPERIENCE QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-018",
            category="Overall",
            question_text="Overall, how satisfied are you with the PsychSync platform?",
            question_type="rating",
            options=["Very Dissatisfied (1)", "Dissatisfied (2)", "Neutral (3)", "Satisfied (4)", "Very Satisfied (5)"],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-019",
            category="Overall",
            question_text="How does this platform compare to other team management tools you've used?",
            question_type="multiple_choice",
            options=[
                "Much better than alternatives",
                "Better than most alternatives",
                "Similar to alternatives",
                "Not as good as alternatives",
                "I haven't used similar tools before"
            ],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-020",
            category="Overall",
            question_text="What additional features would make this platform more valuable for your team?",
            question_type="text",
            required=False
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-021",
            category="Overall",
            question_text="Is there anything else you'd like to share about your experience?",
            question_type="text",
            required=False
        ))

        # === ROLE-SPECIFIC QUESTIONS ===

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-022",
            category="Overall",
            question_text="How long have you been in a team leadership role?",
            question_type="multiple_choice",
            options=[
                "Less than 1 year",
                "1-3 years",
                "3-5 years",
                "5-10 years",
                "More than 10 years"
            ],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-023",
            category="Overall",
            question_text="What is the size of your team?",
            question_type="multiple_choice",
            options=[
                "2-5 members",
                "6-10 members",
                "11-20 members",
                "21-50 members",
                "More than 50 members"
            ],
            required=True
        ))

        questions.append(UATFeedbackQuestion(
            question_id="UAT-QL-024",
            category="Overall",
            question_text="What industry does your organization operate in?",
            question_type="multiple_choice",
            options=[
                "Technology/Software",
                "Healthcare",
                "Finance/Banking",
                "Education",
                "Manufacturing",
                "Retail",
                "Consulting",
                "Government/Public Sector",
                "Other"
            ],
            required=True
        ))

        return questions

    def generate_feedback_form(self, team_leader_id="default"):
        """Generate feedback form for team leader UAT"""

        return {
            "form_metadata": {
                "form_id": f"uat_feedback_{team_leader_id}",
                "team_leader_id": team_leader_id,
                "created_date": "2025-12-13",
                "estimated_completion_time": "15-20 minutes",
                "form_type": "Team Leader UAT Feedback"
            },
            "instructions": {
                "title": "Team Leader User Acceptance Testing Feedback",
                "description": "Your feedback is crucial for improving the PsychSync platform. Please be honest and thorough in your responses.",
                "estimated_time": "15-20 minutes",
                "confidentiality": "All responses are confidential and will only be used for product improvement."
            },
            "questions": [
                {
                    "section": "User Experience",
                    "description": "Please rate your experience using the platform",
                    "questions": [
                        {
                            "id": q.question_id,
                            "text": q.question_text,
                            "type": q.question_type,
                            "options": q.options,
                            "required": q.required,
                            "category": q.category
                        } for q in self.feedback_questions if q.category in ["Usability", "Performance"]
                    ]
                },
                {
                    "section": "Functionality & Features",
                    "description": "Tell us about the platform's capabilities",
                    "questions": [
                        {
                            "id": q.question_id,
                            "text": q.question_text,
                            "type": q.question_type,
                            "options": q.options,
                            "required": q.required,
                            "category": q.category
                        } for q in self.feedback_questions if q.category == "Functionality"
                    ]
                },
                {
                    "section": "Business Value",
                    "description": "How valuable is this platform for your work?",
                    "questions": [
                        {
                            "id": q.question_id,
                            "text": q.question_text,
                            "type": q.question_type,
                            "options": q.options,
                            "required": q.required,
                            "category": q.category
                        } for q in self.feedback_questions if q.category == "BusinessValue"
                    ]
                },
                {
                    "section": "Overall Experience",
                    "description": "Your overall assessment",
                    "questions": [
                        {
                            "id": q.question_id,
                            "text": q.question_text,
                            "type": q.question_type,
                            "options": q.options,
                            "required": q.required,
                            "category": q.category
                        } for q in self.feedback_questions if q.category == "Overall"
                    ]
                }
            ],
            "demographics": {
                "title": "About You (Optional)",
                "description": "This information helps us understand different user needs",
                "questions": [
                    {
                        "id": q.question_id,
                        "text": q.question_text,
                        "type": q.question_type,
                        "options": q.options,
                        "required": False,
                        "category": q.category
                    } for q in self.feedback_questions if q.question_id in ["UAT-QL-022", "UAT-QL-023", "UAT-QL-024"]
                ]
            }
        }

    def analyze_feedback_results(self, feedback_data):
        """Analyze feedback results and generate insights"""

        # Calculate average scores for rating questions
        rating_scores = []
        for question in self.feedback_questions:
            if question.question_type == "rating" and question.question_id in feedback_data:
                response = feedback_data[question.question_id]
                if isinstance(response, str) and response.isdigit():
                    rating_scores.append(int(response))

        average_score = sum(rating_scores) / len(rating_scores) if rating_scores else 0

        # Count boolean responses
        boolean_positive = 0
        boolean_total = 0
        for question in self.feedback_questions:
            if question.question_type == "boolean" and question.question_id in feedback_data:
                boolean_total += 1
                if feedback_data[question.question_id] in ["Yes", "true", "True", True]:
                    boolean_positive += 1

        boolean_success_rate = (boolean_positive / boolean_total * 100) if boolean_total > 0 else 0

        # Generate insights
        insights = {
            "overall_score": average_score,
            "boolean_success_rate": boolean_success_rate,
            "total_respondents": 1,  # Would be calculated from multiple responses
            "rating_distribution": self._calculate_rating_distribution(feedback_data),
            "category_scores": self._calculate_category_scores(feedback_data),
            "key_improvements": self._identify_key_improvements(feedback_data),
            "strengths": self._identify_strengths(feedback_data)
        }

        return insights

    def _calculate_rating_distribution(self, feedback_data):
        """Calculate distribution of rating responses"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for question in self.feedback_questions:
            if question.question_type == "rating" and question.question_id in feedback_data:
                response = feedback_data[question.question_id]
                if isinstance(response, str) and response.isdigit():
                    rating = int(response)
                    if rating in distribution:
                        distribution[rating] += 1

        return distribution

    def _calculate_category_scores(self, feedback_data):
        """Calculate average scores by category"""
        category_scores = {}

        for category in ["Usability", "Functionality", "BusinessValue", "Overall"]:
            category_questions = [q for q in self.feedback_questions if q.category == category and q.question_type == "rating"]
            if category_questions:
                scores = []
                for q in category_questions:
                    if q.question_id in feedback_data:
                        response = feedback_data[q.question_id]
                        if isinstance(response, str) and response.isdigit():
                            scores.append(int(response))

                category_scores[category] = sum(scores) / len(scores) if scores else 0

        return category_scores

    def _identify_key_improvements(self, feedback_data):
        """Identify key areas for improvement from feedback"""
        improvements = []

        # Check for text responses mentioning improvements
        for question in self.feedback_questions:
            if question.question_type == "text" and question.question_id in feedback_data:
                response = feedback_data[question.question_id]
                if response and "improve" in response.lower():
                    improvements.append(response)

        return improvements

    def _identify_strengths(self, feedback_data):
        """Identify platform strengths from feedback"""
        strengths = []

        # Check for text responses mentioning positive aspects
        for question in self.feedback_questions:
            if question.question_type == "text" and question.question_id in feedback_data:
                response = feedback_data[question.question_id]
                if response and any(word in response.lower() for word in ["good", "excellent", "love", "great", "helpful"]):
                    strengths.append(response)

        return strengths

    def generate_feedback_report(self, all_feedback_data):
        """Generate comprehensive feedback report"""

        # Analyze all responses
        total_responses = len(all_feedback_data)
        all_insights = []

        for feedback in all_feedback_data:
            insights = self.analyze_feedback_results(feedback)
            all_insights.append(insights)

        # Calculate aggregate metrics
        aggregate_scores = {}
        for category in ["Usability", "Functionality", "BusinessValue", "Overall"]:
            category_scores = [insight["category_scores"].get(category, 0) for insight in all_insights if category in insight["category_scores"]]
            if category_scores:
                aggregate_scores[category] = sum(category_scores) / len(category_scores)

        overall_score = sum(insight["overall_score"] for insight in all_insights) / len(all_insights)

        report = {
            "report_metadata": {
                "total_respondents": total_responses,
                "report_date": "2025-12-13",
                "test_duration": "2.5 hours",
                "feedback_form_version": "1.0"
            },
            "executive_summary": {
                "overall_satisfaction": round(overall_score, 2),
                "key_findings": self._generate_key_findings(aggregate_scores, all_insights),
                "recommendations": self._generate_recommendations(aggregate_scores),
                "go_no_go_decision": self._make_go_no_go_decision(overall_score, aggregate_scores)
            },
            "detailed_analysis": {
                "category_scores": aggregate_scores,
                "average_scores_by_category": aggregate_scores,
                "improvement_themes": self._analyze_improvement_themes(all_insights),
                "strengths_highlighted": self._analyze_strength_themes(all_insights),
                "user_segments": self._analyze_user_segments(all_feedback_data)
            },
            "action_items": self._generate_action_items(aggregate_scores, all_insights)
        }

        return report

    def _generate_key_findings(self, scores, insights):
        """Generate key findings from analysis"""
        findings = []

        if scores.get("Usability", 0) >= 4:
            findings.append("Users find the platform highly intuitive and easy to use")
        elif scores.get("Usability", 0) <= 2:
            findings.append("Significant usability issues need to be addressed")

        if scores.get("BusinessValue", 0) >= 4:
            findings.append("Team leaders see clear business value in the platform")
        elif scores.get("BusinessValue", 0) <= 2:
            findings.append("Business value proposition needs improvement")

        return findings

    def _generate_recommendations(self, scores):
        """Generate recommendations based on scores"""
        recommendations = []

        for category, score in scores.items():
            if score <= 2:
                recommendations.append(f"Major improvements needed in {category}")
            elif score <= 3:
                recommendations.append(f"Enhancements recommended for {category}")

        return recommendations

    def _make_go_no_go_decision(self, overall_score, scores):
        """Make go/no-go recommendation"""
        if overall_score >= 4 and all(score >= 3.5 for score in scores.values()):
            return "GO - Ready for production launch"
        elif overall_score >= 3.5 and all(score >= 3 for score in scores.values()):
            return "CONDITIONAL GO - Minor fixes required before launch"
        elif overall_score >= 3:
            return "HOLD - Significant improvements needed before launch"
        else:
            return "NO GO - Major rework required"

    def _analyze_improvement_themes(self, insights):
        """Analyze common improvement themes"""
        themes = {}
        for insight in insights:
            for improvement in insight.get("key_improvements", []):
                theme = improvement.lower().split()[0]  # Simple theme extraction
                themes[theme] = themes.get(theme, 0) + 1

        return themes

    def _analyze_strength_themes(self, insights):
        """Analyze common strength themes"""
        themes = {}
        for insight in insights:
            for strength in insight.get("strengths", []):
                theme = strength.lower().split()[0]
                themes[theme] = themes.get(theme, 0) + 1

        return themes

    def _analyze_user_segments(self, feedback_data):
        """Analyze user segments based on demographics"""
        segments = {
            "experience_levels": {},
            "team_sizes": {},
            "industries": {}
        }

        for feedback in feedback_data:
            if "UAT-QL-022" in feedback:  # Experience level
                exp = feedback["UAT-QL-022"]
                segments["experience_levels"][exp] = segments["experience_levels"].get(exp, 0) + 1

            if "UAT-QL-023" in feedback:  # Team size
                size = feedback["UAT-QL-023"]
                segments["team_sizes"][size] = segments["team_sizes"].get(size, 0) + 1

            if "UAT-QL-024" in feedback:  # Industry
                industry = feedback["UAT-QL-024"]
                segments["industries"][industry] = segments["industries"].get(industry, 0) + 1

        return segments

    def _generate_action_items(self, scores, insights):
        """Generate actionable items based on feedback"""
        action_items = []

        for category, score in scores.items():
            if score <= 2:
                action_items.append({
                    "priority": "High",
                    "category": category,
                    "action": f"Complete review and redesign of {category} features",
                    "timeline": "2-4 weeks",
                    "owner": "Product Team"
                })
            elif score <= 3:
                action_items.append({
                    "priority": "Medium",
                    "category": category,
                    "action": f"Enhance {category} functionality based on user feedback",
                    "timeline": "1-2 weeks",
                    "owner": "Development Team"
                })

        return action_items

def main():
    """Generate comprehensive UAT feedback system for team leaders"""
    print("📝 Generating Team Leader UAT Feedback System")
    print("=" * 50)

    # Create feedback system
    feedback_system = UATFeedbackSystem()

    # Display summary
    questions = feedback_system.feedback_questions
    feedback_form = feedback_system.generate_feedback_form()

    print(f"📋 Feedback Questions Generated:")
    print(f"   Total Questions: {len(questions)}")
    print(f"   Required Questions: {len([q for q in questions if q.required])}")
    print(f"   Optional Questions: {len([q for q in questions if not q.required])}")
    print(f"   Estimated Completion Time: {feedback_form['instructions']['estimated_time']}")

    # Display question categories
    categories = {}
    for q in questions:
        categories[q.category] = categories.get(q.category, 0) + 1

    print(f"\n📊 Questions by Category:")
    for category, count in categories.items():
        print(f"   {category}: {count} questions")

    # Display form structure
    print(f"\n📄 Feedback Form Structure:")
    for section in feedback_form["questions"]:
        print(f"   Section: {section['section']}")
        print(f"   Questions: {len(section['questions'])}")

    print(f"\n✅ Team Leader UAT Feedback System Generated Successfully!")
    print(f"   Ready to collect comprehensive user acceptance testing feedback")

if __name__ == "__main__":
    main()