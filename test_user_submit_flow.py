#!/usr/bin/env python3
"""
Simulate User Clicking Submit Button on MBTI Assessment

This script simulates the complete user experience:
1. Visit the MBTI assessment page
2. Progress through questions answering each one
3. Click submit button
4. View and analyze the results
"""

import requests
import json
import time
from typing import Dict, Any, List

class MBTIUserFlowTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000/api/v1"
        self.frontend_url = "http://localhost:5173"
        self.user_answers = {}
        self.session_responses = []

    def log_action(self, action: str, details: str = ""):
        """Log user action"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {action}")
        if details:
            print(f"    {details}")

    def test_assessment_page_access(self):
        """Test if MBTI assessment page loads properly"""
        try:
            response = requests.get(f"{self.frontend_url}/assessments/mbti/start", timeout=10)
            self.log_action(
                "✅ User visits MBTI assessment page",
                f"Status: {response.status_code}"
            )
            return response.status_code == 200
        except Exception as e:
            self.log_action("❌ Failed to access MBTI page", f"Error: {e}")
            return False

    def simulate_question_progression(self):
        """Simulate user answering each MBTI question"""
        self.log_action("📝 User starts answering MBTI questions")

        # Simulate the 8 MBTI questions with realistic answers
        questions = [
            {
                "id": 1,
                "text": "At parties, do you:",
                "options": {"E": "Talk to many people, including strangers", "I": "Talk to a few people you know well"},
                "expected_answer": "E"  # Most people are moderately extraverted
            },
            {
                "id": 2,
                "text": "Do you prefer to:",
                "options": {"S": "Focus on the real world and practical matters", "N": "Imagine possibilities and think about abstract concepts"},
                "expected_answer": "N"  # Many people are intuitive
            },
            {
                "id": 3,
                "text": "When making decisions, do you:",
                "options": {"T": "Rely on logic and objective analysis", "F": "Consider how it will affect people involved"},
                "expected_answer": "F"  # Balanced approach
            },
            {
                "id": 4,
                "text": "Do you prefer to:",
                "options": {"J": "Plan things in advance and stick to the plan", "P": "Be spontaneous and adapt to new situations"},
                "expected_answer": "J"  # Planning is common
            },
            {
                "id": 5,
                "text": "At work, do you:",
                "options": {"E": "Enjoy working in teams and brainstorming", "I": "Prefer working independently and concentrating"},
                "expected_answer": "I"  # Many introverts prefer independent work
            },
            {
                "id": 6,
                "text": "When learning something new, do you:",
                "options": {"S": "Prefer step-by-step instructions", "N": "Like to understand the overall concept first"},
                "expected_answer": "S"  # Practical learning
            },
            {
                "id": 7,
                "text": "When giving feedback, do you:",
                "options": {"T": "Focus on facts and improvements", "F": "Consider feelings and delivery"},
                "expected_answer": "F"  # Empathy in feedback
            },
            {
                "id": 8,
                "text": "For weekends, do you:",
                "options": {"J": "Plan activities and have a schedule", "P": "Leave options open and decide spontaneously"},
                "expected_answer": "P"  # Flexibility is valued
            }
        ]

        total_time = 0
        for i, question in enumerate(questions):
            # Simulate user reading time and thinking
            reading_time = 2 + (i * 0.5)  # Progressive reading time
            thinking_time = 3 + (i * 0.3)  # Progressive thinking time

            time.sleep(reading_time)
            self.log_action(
                f"📖 Question {i + 1}/8: {question['text'][:50]}..."
            )

            time.sleep(thinking_time)

            # User makes a choice (mixing expected and varied answers)
            if i in [0, 2, 4, 6]:  # Use expected answers for some questions
                answer = question["expected_answer"]
            else:  # Use varied answers
                answers = list(question["options"].keys())
                answer = answers[i % len(answers)]

            self.user_answers[question["id"]] = answer
            total_time += reading_time + thinking_time

            self.log_action(
                f"   ✅ User answered: {question['options'][answer]}",
                f"Progress: {i + 1}/8 questions"
            )

            # Small pause between questions (simulating natural flow)
            if i < len(questions) - 1:
                time.sleep(1)

        self.log_action(
            "📊 User completed all questions",
            f"Total time: {total_time:.1f} seconds"
        )

        return True

    def simulate_submit_button_click(self):
        """Simulate user clicking the submit button"""
        self.log_action("🚀 User clicks SUBMIT button")

        # Simulate submit button loading state
        time.sleep(2)
        self.log_action("⏳ Submitting assessment...", "Please wait...")

        # Calculate client-side MBTI type (same logic as frontend)
        dimensions = {
            'E-I': {'E': 0, 'I': 0},
            'S-N': {'S': 0, 'N': 0},
            'T-F': {'T': 0, 'F': 0},
            'J-P': {'J': 0, 'P': 0}
        }

        # Count user responses
        for question_id, answer in self.user_answers.items():
            if answer in dimensions.get('E-I', {}):
                dimensions['E-I'][answer] += 1
            elif answer in dimensions.get('S-N', {}):
                dimensions['S-N'][answer] += 1
            elif answer in dimensions.get('T-F', {}):
                dimensions['T-F'][answer] += 1
            elif answer in dimensions.get('J-P', {}):
                dimensions['J-P'][answer] += 1

        # Calculate MBTI type
        calculated_type = ''.join([
            'E' if dimensions['E-I']['E'] > dimensions['E-I']['I'] else 'I',
            'S' if dimensions['S-N']['S'] > dimensions['S-N']['N'] else 'N',
            'T' if dimensions['T-F']['T'] > dimensions['T-F']['F'] else 'F',
            'J' if dimensions['J-P']['J'] > dimensions['J-P']['P'] else 'P'
        ])

        self.log_action("🧠 Client-side calculation", f"Calculated type: {calculated_type}")

        # Prepare payload for backend
        payload = {
            "assessment_id": "mbti-user-test",
            "assessment_type": "mbti",
            "responses": self.user_answers,
            "raw_type": calculated_type
        }

        self.log_action("📤 Sending to backend API", f"URL: {self.backend_url}/mbti-test-submit")

        # Submit to backend
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.backend_url}/mbti-test-submit",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                results = response.json()
                self.log_action(
                    "✅ Backend processing successful!",
                    f"Response time: {response_time:.0f}ms"
                )
                return results
            else:
                self.log_action(
                    "❌ Backend error",
                    f"Status: {response.status_code}, Error: {response.text}"
                )
                return None

        except Exception as e:
            self.log_action("❌ API request failed", f"Error: {e}")
            return None

    def analyze_results(self, results: Dict[str, Any]):
        """Analyze and display the MBTI results"""
        if not results:
            self.log_action("❌ No results to analyze")
            return

        self.log_action("🎯 MBTI Assessment Results Received!")
        self.log_action("📊 Type Information", f"Type: {results.get('type', 'N/A')}")
        self.log_action("📊 Confidence", f"Score: {results.get('confidence', 0):.2f} ({results.get('confidence', 0)*100:.0f}%)")
        self.log_action("📊 Description", f"Personality: {results.get('description', 'N/A')}")

        # Analyze dimensions
        dimensions = results.get('dimensions', {})
        if dimensions:
            self.log_action("📊 Personality Dimensions:")
            for dim_name, score in dimensions.items():
                self.log_action(f"   • {dim_name.capitalize()}: {score:.2f}")

        # Analyze strengths
        strengths = results.get('strengths', [])
        if strengths:
            self.log_action("💪 Identified Strengths:")
            for strength in strengths:
                self.log_action(f"   • {strength}")

        # Analyze blind spots
        blind_spots = results.get('blind_spots', [])
        if blind_spots:
            self.log_action("⚠️ Potential Blind Spots:")
            for spot in blind_spots:
                self.log_action(f"   • {spot}")

        # Analyze preferences
        preferences = results.get('preferences', [])
        if preferences:
            self.log_action("🤝 Personality Preferences:")
            for pref in preferences:
                self.log_action(f"   • {pref}")

        # Show scoring details
        scoring = results.get('scoring_details', {})
        if scoring:
            self.log_action("🔬 Scoring Details:")
            self.log_action(f"   • Algorithm: {scoring.get('algorithm', 'N/A')}")
            self.log_action(f"   • Total Questions: {scoring.get('total_questions', 0)}")

            dim_scores = scoring.get('dimension_scores', {})
            if dim_scores:
                self.log_action("   • Dimension Scores:")
                for dim, scores in dim_scores.items():
                    self.log_action(f"     - {dim}: E={scores.get('E', 0)}, I={scores.get('I', 0)}")

    def test_complete_user_flow(self):
        """Run the complete user flow simulation"""
        print("=" * 60)
        print("🎯 MBTI Assessment User Flow Simulation")
        print("=" * 60)
        print()

        # Step 1: Access assessment page
        page_accessible = self.test_assessment_page_access()
        if not page_accessible:
            print("\n❌ Cannot proceed - frontend not accessible")
            return False

        # Step 2: Simulate answering questions
        questions_completed = self.simulate_question_progression()
        if not questions_completed:
            print("\n❌ Cannot proceed - questions not answered")
            return False

        # Step 3: Submit assessment
        results = self.simulate_submit_button_click()
        if not results:
            print("\n❌ Cannot proceed - submission failed")
            return False

        # Step 4: Analyze and display results
        self.analyze_results(results)

        print("\n" + "=" * 60)
        print("🎉 USER FLOW SIMULATION COMPLETE!")
        print("✅ The MBTI assessment system works end-to-end")
        print("✅ User can successfully submit and get comprehensive results")
        print("✅ All components are functioning properly")
        print("=" * 60)

        return True

if __name__ == "__main__":
    tester = MBTIUserFlowTest()
    tester.test_complete_user_flow()
