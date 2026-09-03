import pytest

from ai.processors.big_five import BigFiveProcessor
from ai.processors.enneagram_processor import EnneagramProcessor
from ai.processors.mbti_processor import MBTIProcessor
from ai.processors.processors_base import PersonalityFrameworkProcessor


class MockProcessor(PersonalityFrameworkProcessor):
    def process(self, data):
        return data


@pytest.fixture
def base_processor():
    return MockProcessor()


def test_big_five_processor():
    processor = BigFiveProcessor()
    data = {
        "openness": 0.5,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.5,
        "neuroticism": 0.5,
    }
    result = processor.process(data)
    assert "dimensions" in result
    assert "interpretations" in result


def test_mbti_processor():
    processor = MBTIProcessor()
    data = {"type": "INTJ", "confidence": 0.8}
    result = processor.process(data)
    assert "type" in result
    assert "dimensions" in result
    assert "description" in result


def test_enneagram_processor():
    processor = EnneagramProcessor()
    data = {"type": 1, "confidence": 0.9}
    result = processor.process(data)
    assert "type" in result
    assert "interpretation" in result


def test_clamp_value_upper(base_processor):
    assert base_processor._clamp_value(1.5) == 1.0


def test_clamp_value_lower(base_processor):
    assert base_processor._clamp_value(-0.5) == 0.0


def test_safe_get_existing(base_processor):
    assert base_processor._safe_get({"a": 1}, "a", 0) == 1


def test_safe_get_missing(base_processor):
    assert base_processor._safe_get({}, "missing", "default") == "default"
