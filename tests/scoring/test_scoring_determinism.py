import pytest

from app.ai.clinical.scoring.strategies.gad7_scorer import GAD7Scorer
from app.ai.clinical.scoring.strategies.phq9_scorer import PHQ9Scorer


@pytest.mark.scoring
def test_phq9_determinism():
    scorer = PHQ9Scorer()
    responses = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 0}
    result1 = scorer.score(responses)
    result2 = scorer.score(responses)
    assert result1.total_score == result2.total_score
    assert result1.interpretation == result2.interpretation


@pytest.mark.scoring
def test_gad7_determinism():
    scorer = GAD7Scorer()
    responses = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
    result1 = scorer.score(responses)
    result2 = scorer.score(responses)
    assert result1.total_score == result2.total_score
