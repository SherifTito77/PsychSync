import numpy as np
import pandas as pd
import pytest

from app.services.prediction_service import (
    ModelPerformance,
    ModelType,
    PredictionService,
    TargetType,
)


def test_compare_models_empty():
    service = PredictionService()
    best_model, metrics, rec = service._compare_models({}, TargetType.REGRESSION)
    assert best_model == "none"
    assert metrics == {}
    assert "No models were trained" in rec


def test_compare_models_no_scores_regression():
    service = PredictionService()
    perf = ModelPerformance()
    best_model, metrics, rec = service._compare_models(
        {"test_model": perf}, TargetType.REGRESSION
    )
    assert best_model == "test_model"
    assert metrics == {}
    assert "No valid regression metrics" in rec


def test_compare_models_no_scores_classification():
    service = PredictionService()
    perf = ModelPerformance()
    best_model, metrics, rec = service._compare_models(
        {"test_model": perf}, TargetType.CLASSIFICATION
    )
    assert best_model == "test_model"
    assert metrics == {}
    assert "No valid classification metrics" in rec


def test_compare_models_valid_regression():
    service = PredictionService()
    perf1 = ModelPerformance(r2=0.5)
    perf2 = ModelPerformance(r2=0.9)
    best_model, metrics, rec = service._compare_models(
        {"model1": perf1, "model2": perf2}, TargetType.REGRESSION
    )
    assert best_model == "model2"
    assert metrics["model1"] == 0.5
    assert metrics["model2"] == 0.9
    assert "Excellent model" in rec


def test_compare_models_valid_classification():
    service = PredictionService()
    perf1 = ModelPerformance(accuracy=0.7)
    perf2 = ModelPerformance(accuracy=0.85)
    best_model, metrics, rec = service._compare_models(
        {"model1": perf1, "model2": perf2}, TargetType.CLASSIFICATION
    )
    assert best_model == "model2"
    assert metrics["model1"] == 0.7
    assert metrics["model2"] == 0.85
    assert "Good model" in rec


def test_preprocessing_pipeline_import():
    # This verifies OneHotEncoder is available and the pipeline can be created
    service = PredictionService()
    df = pd.DataFrame({"numeric": [1.0, 2.0, 3.0], "categorical": ["A", "B", "A"]})
    pipeline = service._create_preprocessing_pipeline(df, False, TargetType.REGRESSION)
    assert pipeline is not None

    # Test fitting (with dummy target)
    y = np.array([10, 20, 30])
    pipeline.fit(df, y)
    transformed = pipeline.transform(df)
    # 1 numeric col + OneHot encoded 'categorical' (2 unique values) = 3 columns
    assert transformed.shape[1] == 3
