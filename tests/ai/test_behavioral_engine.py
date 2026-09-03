import pytest

from app.ai.engine.behavioral_engine import BehavioralEngine


def test_synthesis_method_is_heuristic():
    engine = BehavioralEngine()
    assert engine.synthesis_method == "heuristic"


def test_no_neural_network_in_engine():
    engine = BehavioralEngine()
    # Ensure no attribute exists that would indicate neural network usage
    assert not hasattr(engine, "models")
    assert not hasattr(engine, "create_synthesis_model")
