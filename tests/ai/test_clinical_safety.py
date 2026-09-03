import pytest

from app.ai.clinical.scoring.strategies.phq9_scorer import PHQ9Scorer


def test_phq9_crisis_flag_and_disclaimer():
    scorer = PHQ9Scorer()
    # PHQ-9 item 9 score 3 (suicidal ideation)
    responses = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 3}
    result = scorer.score(responses)

    assert result.crisis_alert is True
    assert "CRISIS ALERT" in "\n".join(result.recommendations)
    assert "screening purposes only" in result.interpretation


def test_phq9_no_crisis_no_alarm():
    scorer = PHQ9Scorer()
    # Low score
    responses = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
    result = scorer.score(responses)

    assert result.crisis_alert is False
    assert "CRISIS ALERT" not in "\n".join(result.recommendations)
    assert "screening purposes only" in result.interpretation
