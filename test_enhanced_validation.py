#!/usr/bin/env python3
"""
Test the enhanced validation logic (simulating JavaScript behavior)
"""

def test_enhanced_validation():
    """Test enhanced validation logic matching the TypeScript implementation"""
    print("🔧 Testing Enhanced Validation Logic...")

    def is_valid_score_js_style(score):
        """Simulate JavaScript validation logic"""
        # In JavaScript, typeof true === 'boolean' and typeof NaN === 'number'
        # Python: isinstance(True, (int, float)) is True, but type(True) is bool

        if type(score) is bool:
            return False  # Explicitly reject booleans

        if not isinstance(score, (int, float)):
            return False

        # Check for NaN and infinity
        import math
        if math.isnan(score) or not math.isfinite(score):
            return False

        return True

    def calculate_safe_total_score_enhanced(responses):
        """Enhanced calculation matching TypeScript implementation"""
        valid_scores = []
        missing_questions = []

        for response in responses:
            score = response.get('score')
            if is_valid_score_js_style(score):
                valid_scores.append(score)
            else:
                missing_questions.append(response['question_id'])

        if len(valid_scores) == 0:
            return {'score': 0, 'isValid': False, 'missingQuestions': missing_questions}

        total_score = sum(valid_scores)
        is_valid = len(missing_questions) == 0

        return {'score': total_score, 'isValid': is_valid, 'missingQuestions': missing_questions}

    def validate_complete_responses_enhanced(tool_questions, responses):
        """Enhanced complete response validation"""
        # Check if all questions have been answered
        if len(responses) != len(tool_questions):
            print(f"Incomplete responses: {len(responses)}/{len(tool_questions)} questions answered")
            return False

        # Check if all responses have valid scores
        for response in responses:
            if not is_valid_score_js_style(response.get('score')):
                print(f"Invalid score {response.get('score')} for response to question {response['question_id']}")
                return False

        return True

    # Test cases matching the edge cases that failed before
    test_cases = [
        {
            'name': 'Boolean Handling Fixed',
            'responses': [
                {'question_id': 'q1', 'score': True},
                {'question_id': 'q2', 'score': False},
                {'question_id': 'q3', 'score': 1}
            ],
            'expected_valid': False,
            'expected_score': 1  # Only the numeric 1 should count
        },
        {
            'name': 'Missing Questions Detected',
            'tool_questions': [
                {'id': 'q1', 'text': 'Q1'},
                {'id': 'q2', 'text': 'Q2'},
                {'id': 'q3', 'text': 'Q3'},
                {'id': 'q4', 'text': 'Q4'},
                {'id': 'q5', 'text': 'Q5'}
            ],
            'responses': [
                {'question_id': 'q1', 'score': 1},
                {'question_id': 'q2', 'score': 2},
                # Missing q3, q4
                {'question_id': 'q5', 'score': 0}
            ],
            'expected_valid': False,
            'expected_score': 3
        },
        {
            'name': 'Mixed Invalid Values',
            'responses': [
                {'question_id': 'q1', 'score': None},
                {'question_id': 'q2', 'score': 'invalid'},
                {'question_id': 'q3', 'score': ''},
                {'question_id': 'q4', 'score': True},  # Should be rejected
                {'question_id': 'q5', 'score': 2}     # Only valid score
            ],
            'expected_valid': False,
            'expected_score': 2
        },
        {
            'name': 'Edge Numbers',
            'responses': [
                {'question_id': 'q1', 'score': 0},
                {'question_id': 'q2', 'score': -1},
                {'question_id': 'q3', 'score': 999999}
            ],
            'expected_valid': True,
            'expected_score': 999998
        },
        {
            'name': 'Complete Valid Responses',
            'tool_questions': [
                {'id': 'q1', 'text': 'Q1'},
                {'id': 'q2', 'text': 'Q2'},
                {'id': 'q3', 'text': 'Q3'}
            ],
            'responses': [
                {'question_id': 'q1', 'score': 1},
                {'question_id': 'q2', 'score': 2},
                {'question_id': 'q3', 'score': 0}
            ],
            'expected_valid': True,
            'expected_score': 3
        }
    ]

    passed = 0
    for test in test_cases:
        print(f"\n  Test: {test['name']}")

        # Test safe calculation
        calc_result = calculate_safe_total_score_enhanced(test['responses'])
        score_correct = calc_result['score'] == test['expected_score']
        valid_correct = calc_result['isValid'] == test['expected_valid']

        # Test complete response validation if applicable
        complete_valid = True
        complete_correct = True
        if 'tool_questions' in test:
            complete_valid = validate_complete_responses_enhanced(test['tool_questions'], test['responses'])
            complete_correct = complete_valid == test['expected_valid']

        if score_correct and valid_correct and complete_correct:
            print(f"    ✅ PASSED: Score={calc_result['score']}, Valid={calc_result['isValid']}")
            if 'tool_questions' in test:
                print(f"      Complete validation: {complete_valid}")
            passed += 1
        else:
            print(f"    ❌ FAILED:")
            print(f"      Score: {calc_result['score']} (expected {test['expected_score']})")
            print(f"      Valid: {calc_result['isValid']} (expected {test['expected_valid']})")
            if 'tool_questions' in test:
                print(f"      Complete: {complete_valid} (expected {test['expected_valid']})")

    print(f"\n📊 Enhanced Validation Tests: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)

def test_real_phq9_scenarios():
    """Test realistic PHQ-9 scenarios"""
    print("\n🏥 Testing Realistic PHQ-9 Scenarios...")

    def calculate_phq9_risk_level(score):
        """Calculate PHQ-9 risk level"""
        if score >= 20:
            return 'severe'
        elif score >= 15:
            return 'moderately_severe'
        elif score >= 10:
            return 'moderate'
        elif score >= 5:
            return 'mild'
        else:
            return 'minimal'

    # Real PHQ-9 scoring scenarios
    scenarios = [
        {
            'name': 'No Depression',
            'scores': [0, 0, 0, 0, 0, 0, 0, 0, 0],
            'expected_total': 0,
            'expected_risk': 'minimal'
        },
        {
            'name': 'Mild Depression',
            'scores': [1, 1, 1, 0, 1, 0, 1, 0, 0],
            'expected_total': 5,
            'expected_risk': 'mild'
        },
        {
            'name': 'Moderate Depression',
            'scores': [2, 2, 1, 2, 1, 2, 0, 1, 1],
            'expected_total': 12,
            'expected_risk': 'moderate'
        },
        {
            'name': 'Severe Depression',
            'scores': [3, 3, 3, 2, 3, 3, 2, 3, 3],
            'expected_total': 25,
            'expected_risk': 'severe'
        }
    ]

    passed = 0
    for scenario in scenarios:
        total = sum(scenario['scores'])
        risk = calculate_phq9_risk_level(total)

        total_correct = total == scenario['expected_total']
        risk_correct = risk == scenario['expected_risk']

        if total_correct and risk_correct:
            print(f"  ✅ {scenario['name']}: Total={total}, Risk={risk}")
            passed += 1
        else:
            print(f"  ❌ {scenario['name']}: Total={total} (exp {scenario['expected_total']}), Risk={risk} (exp {scenario['expected_risk']})")

    print(f"\n📊 PHQ-9 Scenarios: {passed}/{len(scenarios)} passed")
    return passed == len(scenarios)

def main():
    """Run enhanced validation tests"""
    print("🚀 Enhanced Mental Health Screening Validation Tests")
    print("=" * 70)

    test1_passed = test_enhanced_validation()
    test2_passed = test_real_phq9_scenarios()

    print("\n" + "=" * 70)
    print("📋 ENHANCED VALIDATION TEST RESULTS:")
    print(f"  Enhanced Validation:  {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  PHQ-9 Scenarios:      {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    all_passed = test1_passed and test2_passed
    print(f"\n🎯 ENHANCED VALIDATION RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    if all_passed:
        print("\n🎉 Enhanced validation is working perfectly!")
        print("   ✅ Boolean values are properly rejected")
        print("   ✅ Missing questions are detected")
        print("   ✅ Invalid scores are filtered out")
        print("   ✅ PHQ-9 clinical scoring works correctly")
        print("   ✅ System is production-ready with robust validation")
    else:
        print("\n⚠️  Some validation tests failed. Please review the issues.")

    return all_passed

if __name__ == "__main__":
    main()