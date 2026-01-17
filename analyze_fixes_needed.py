#!/usr/bin/env python3
"""
Analyze the test failures and provide insights
"""

import math

def analyze_test_failures():
    """Analyze why tests failed"""
    print("🔍 Analyzing Test Failures...")

    # Issue 1: Mixed Response with Missing Questions
    print("\n1️⃣ Issue: Mixed Response with Missing Questions")
    print("   Problem: Expected invalid but got valid")
    print("   Analysis: The test has 5 responses, so it's considered 'complete'")
    print("   Root Cause: Test logic assumes missing questions make it invalid")
    print("   Fix: Should check against expected total question count")

    # Issue 2: Very Large Scores
    print("\n2️⃣ Issue: Very Large Scores Off by 1")
    print("   Problem: Expected 2999997 but got 2999998")
    print("   Analysis: Possible floating point precision or calculation error")
    print("   Investigation needed")

    # Issue 3: None and String Scores
    print("\n3️⃣ Issue: Boolean Score Treated as Valid")
    print("   Problem: True was treated as valid numeric score")
    print("   Analysis: isinstance(True, (int, float)) returns True in Python")
    print("   Fix: Need explicit check to exclude booleans")

def test_issue_reproduction():
    """Reproduce the specific issues"""
    print("\n🧪 Reproducing Issues...")

    # Test issue 1: Missing questions logic
    print("\nIssue 1 - Missing Questions:")
    responses = [
        {'question_id': 'phq9_1', 'score': 2},
        {'question_id': 'phq9_2', 'score': 1},
        {'question_id': 'phq9_7', 'score': 0},
        {'question_id': 'phq9_8', 'score': 1},
        {'question_id': 'phq9_9', 'score': 2}
    ]

    total_questions = 9  # PHQ-9 has 9 questions
    answered_questions = len(responses)

    print(f"  Total questions: {total_questions}")
    print(f"  Answered questions: {answered_questions}")
    print(f"  Is complete: {answered_questions >= total_questions}")
    print(f"  Should be incomplete: {answered_questions < total_questions}")

    # Test issue 2: Large numbers
    print("\nIssue 2 - Large Numbers:")
    large_score = 999999 + 1000000 + 999999
    print(f"  Expected sum: 2999997")
    print(f"  Actual calculation: {large_score}")

    # Test issue 3: Boolean handling
    print("\nIssue 3 - Boolean Handling:")
    test_values = [None, 'invalid', '', True, False]
    for val in test_values:
        is_num = isinstance(val, (int, float))
        is_finite = is_finite if isinstance(val, (int, float)) else False
        print(f"  Value: {repr(val):<10} is numeric: {is_num:<5} is finite: {is_finite}")

def test_improved_validation():
    """Test improved validation logic"""
    print("\n🔧 Testing Improved Validation...")

    def is_valid_score(score):
        """Improved score validation"""
        return (
            isinstance(score, (int, float)) and
            not isinstance(score, bool) and  # Exclude booleans
            not math.isnan(score) and
            math.isfinite(score)
        )

    def calculate_safe_total_score_improved(responses, expected_question_count=None):
        """Improved safe score calculation"""
        valid_scores = []
        missing_questions = []

        for response in responses:
            score = response.get('score')
            if is_valid_score(score):
                valid_scores.append(score)
            else:
                missing_questions.append(response['question_id'])

        if len(valid_scores) == 0:
            return {'score': 0, 'isValid': False, 'missingQuestions': missing_questions}

        total_score = sum(valid_scores)

        # Check if complete (only if expected count is provided)
        is_valid = len(missing_questions) == 0
        if expected_question_count is not None:
            is_valid = is_valid and len(responses) == expected_question_count

        return {'score': total_score, 'isValid': is_valid, 'missingQuestions': missing_questions}

    # Test the improved logic
    test_cases = [
        {
            'name': 'Boolean handling',
            'responses': [{'question_id': 'q1', 'score': True}],
            'expected_valid': False
        },
        {
            'name': 'Missing questions',
            'responses': [
                {'question_id': 'q1', 'score': 2},
                {'question_id': 'q2', 'score': 1}
            ],
            'expected_question_count': 3,
            'expected_valid': False
        },
        {
            'name': 'Complete valid responses',
            'responses': [
                {'question_id': 'q1', 'score': 1},
                {'question_id': 'q2', 'score': 2},
                {'question_id': 'q3', 'score': 0}
            ],
            'expected_question_count': 3,
            'expected_valid': True
        }
    ]

    passed = 0
    for test in test_cases:
        result = calculate_safe_total_score_improved(
            test['responses'],
            test.get('expected_question_count')
        )

        if result['isValid'] == test['expected_valid']:
            print(f"  ✅ {test['name']}: PASSED")
            passed += 1
        else:
            print(f"  ❌ {test['name']}: FAILED (valid={result['isValid']}, expected={test['expected_valid']})")

    print(f"\nImproved validation: {passed}/{len(test_cases)} passed")

if __name__ == "__main__":
    analyze_test_failures()
    test_issue_reproduction()
    test_improved_validation()
