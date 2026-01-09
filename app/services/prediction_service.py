"""
Predictive Analytics Service - Machine Learning Prediction Models

This service provides comprehensive ML prediction capabilities for psychological assessment data,
including team performance predictions, user outcome predictions, and assessment analytics.

Key Features:
- Multiple ML algorithms (Random Forest, Gradient Boosting, SVM, Neural Networks)
- Automated model selection and hyperparameter tuning
- Cross-validation and model evaluation
- Feature importance analysis
- Model persistence and loading
- Prediction confidence intervals
- Model interpretability and explainability
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
from typing import Any
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    explained_variance_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

warnings.filterwarnings("ignore")

from sqlalchemy.orm import Session

from app.services.irt_service import IRTService
from app.services.prediction_data_service import PredictionDataCollectionService

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions supported by the service."""

    TEAM_PERFORMANCE = "team_performance"
    USER_OUTCOME = "user_outcome"
    ASSESSMENT_COMPLETION = "assessment_completion"
    TEAM_DYNAMICS = "team_dynamics"
    PERFORMANCE_TREND = "performance_trend"
    RETENTION_RISK = "retention_risk"
    LEADERSHIP_POTENTIAL = "leadership_potential"
    TEAM_COHESION = "team_cohesion"


class ModelType(Enum):
    """ML model types supported."""

    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVM = "svm"
    NEURAL_NETWORK = "neural_network"
    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    GAUSSIAN_PROCESS = "gaussian_process"
    DECISION_TREE = "decision_tree"
    NAIVE_BAYES = "naive_bayes"
    KNN = "knn"
    ENSEMBLE = "ensemble"


class TargetType(Enum):
    """Target variable types."""

    CONTINUOUS = "continuous"
    BINARY = "binary"
    MULTICLASS = "multiclass"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class ModelPerformance:
    """Model performance metrics."""

    def __init__(
        self,
        mse: float | None = None,
        mae: float | None = None,
        rmse: float | None = None,
        r2: float | None = None,
        accuracy: float | None = None,
        precision: float | None = None,
        recall: float | None = None,
        f1: float | None = None,
        auc: float | None = None,
        mape: float | None = None,
        explained_variance: float | None = None,
        cv_scores: list[float] | None = None,
        feature_importance: dict[str, float] | None = None,
    ):
        self.mse = mse
        self.mae = mae
        self.rmse = rmse
        self.r2 = r2
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.auc = auc
        self.mape = mape
        self.explained_variance = explained_variance
        self.cv_scores = cv_scores or []
        self.feature_importance = feature_importance or {}


class PredictionModel:
    """Trained ML model with metadata."""

    def __init__(
        self,
        model_id: str,
        model_type: ModelType,
        prediction_type: PredictionType,
        target_type: TargetType,
        model: Any,
        feature_names: list[str],
        target_name: str,
        performance: ModelPerformance,
        scaler: Any | None = None,
        feature_selector: Any | None = None,
        hyperparameters: dict[str, Any] | None = None,
        training_date: datetime = None,
        cross_val_score: float | None = None,
    ):
        self.model_id = model_id
        self.model_type = model_type
        self.prediction_type = prediction_type
        self.target_type = target_type
        self.model = model
        self.feature_names = feature_names
        self.target_name = target_name
        self.performance = performance
        self.scaler = scaler
        self.feature_selector = feature_selector
        self.hyperparameters = hyperparameters or {}
        self.training_date = training_date or datetime.now()
        self.cross_val_score = cross_val_score


class PredictionResult:
    """Single prediction result with confidence."""

    def __init__(
        self,
        prediction: float | int | str,
        confidence: float,
        prediction_interval: tuple[float, float] | None = None,
        probabilities: dict[str, float] | None = None,
        feature_contributions: dict[str, float] | None = None,
        model_id: str = None,
        prediction_type: PredictionType = None,
        timestamp: datetime = None,
    ):
        self.prediction = prediction
        self.confidence = confidence
        self.prediction_interval = prediction_interval
        self.probabilities = probabilities or {}
        self.feature_contributions = feature_contributions or {}
        self.model_id = model_id
        self.prediction_type = prediction_type
        self.timestamp = timestamp or datetime.now()


class ModelComparisonResult:
    """Model comparison results."""

    def __init__(
        self,
        model_performances: dict[str, ModelPerformance],
        best_model_name: str,
        comparison_metrics: dict[str, float],
        recommendation: str,
    ):
        self.model_performances = model_performances
        self.best_model_name = best_model_name
        self.comparison_metrics = comparison_metrics
        self.recommendation = recommendation


class PredictionService:
    """
    Comprehensive machine learning prediction service for psychological assessment data.
    """

    def __init__(self, model_save_path: str = "models/"):
        self.data_service = PredictionDataCollectionService()
        self.irt_service = IRTService()
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(exist_ok=True)
        self.trained_models: dict[str, PredictionModel] = {}
        self.model_registry = self._initialize_model_registry()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _initialize_model_registry(self) -> dict[ModelType, dict]:
        """Initialize model registry with configuration."""
        return {
            ModelType.RANDOM_FOREST: {
                "regressor": RandomForestRegressor,
                "classifier": RandomForestClassifier,
                "params": {
                    "n_estimators": [50, 100, 200],
                    "max_depth": [5, 10, 15, None],
                    "min_samples_split": [2, 5, 10],
                    "min_samples_leaf": [1, 2, 4],
                },
            },
            ModelType.GRADIENT_BOOSTING: {
                "regressor": GradientBoostingRegressor,
                "classifier": GradientBoostingClassifier,
                "params": {
                    "n_estimators": [50, 100, 200],
                    "learning_rate": [0.01, 0.1, 0.2],
                    "max_depth": [3, 5, 7],
                    "subsample": [0.8, 0.9, 1.0],
                },
            },
            ModelType.SVM: {
                "regressor": SVR,
                "classifier": SVC,
                "params": {
                    "C": [0.1, 1, 10, 100],
                    "kernel": ["rbf", "linear", "poly"],
                    "gamma": ["scale", "auto"],
                },
            },
            ModelType.NEURAL_NETWORK: {
                "regressor": MLPRegressor,
                "classifier": MLPClassifier,
                "params": {
                    "hidden_layer_sizes": [(50,), (100,), (50, 25), (100, 50)],
                    "activation": ["relu", "tanh"],
                    "alpha": [0.0001, 0.001, 0.01],
                    "learning_rate": ["constant", "adaptive"],
                    "max_iter": [500, 1000],
                },
            },
            ModelType.LINEAR_REGRESSION: {
                "regressor": LinearRegression,
                "classifier": LogisticRegression,
                "params": {
                    "fit_intercept": [True, False],
                    "normalize": [False],  # Deprecated in newer versions
                },
            },
            ModelType.DECISION_TREE: {
                "regressor": DecisionTreeRegressor,
                "classifier": DecisionTreeClassifier,
                "params": {
                    "max_depth": [3, 5, 7, 10, None],
                    "min_samples_split": [2, 5, 10],
                    "min_samples_leaf": [1, 2, 4],
                    "criterion": ["mse", "friedman_mse", "mae"],  # For regression
                },
            },
            ModelType.KNN: {
                "regressor": KNeighborsRegressor,
                "classifier": KNeighborsClassifier,
                "params": {
                    "n_neighbors": [3, 5, 7, 9],
                    "weights": ["uniform", "distance"],
                    "algorithm": ["auto", "ball_tree", "kd_tree"],
                },
            },
        }

    async def train_team_performance_model(
        self,
        db: Session,
        team_ids: list[int] | None = None,
        target_variable: str = "team_performance_score",
        model_types: list[ModelType] | None = None,
        test_size: float = 0.2,
        cv_folds: int = 5,
        hyperparameter_tuning: bool = True,
        feature_selection: bool = True,
    ) -> ModelComparisonResult:
        """
        Train ML models to predict team performance based on assessment data.

        Args:
            db: Database session
            team_ids: Specific teams to include in training
            target_variable: Target variable to predict
            model_types: List of model types to train
            test_size: Proportion of data for testing
            cv_folds: Number of cross-validation folds
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            feature_selection: Whether to perform feature selection

        Returns:
            ModelComparisonResult with performance comparison
        """
        logger.info(f"Training team performance models for target: {target_variable}")

        if model_types is None:
            model_types = [
                ModelType.RANDOM_FOREST,
                ModelType.GRADIENT_BOOSTING,
                ModelType.LINEAR_REGRESSION,
                ModelType.NEURAL_NETWORK,
            ]

        # Collect training data
        data_result = await self.data_service.collect_training_data(
            db=db,
            include_assessment_responses=True,
            include_team_performance=True,
            include_demographics=True,
            include_response_patterns=True,
            team_ids=team_ids,
            min_data_quality=0.7,
        )

        if not data_result["success"]:
            raise ValueError(f"Data collection failed: {data_result.get('error', 'Unknown error')}")

        df = data_result["data"]

        # Prepare features and target
        feature_cols = [col for col in df.columns if col != target_variable and col != "team_id"]

        if target_variable not in df.columns:
            raise ValueError(f"Target variable '{target_variable}' not found in data")

        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df[target_variable].fillna(df[target_variable].median())

        # Determine target type
        target_type = self._determine_target_type(y)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=42,
            stratify=y if target_type == TargetType.CLASSIFICATION else None,
        )

        model_performances = {}
        trained_models = {}

        # Train each model type
        for model_type in model_types:
            try:
                logger.info(f"Training {model_type.value} model...")

                # Create preprocessing pipeline
                pipeline = self._create_preprocessing_pipeline(
                    X_train, feature_selection, target_type
                )

                # Get model class and params
                model_config = self.model_registry[model_type]
                model_class = (
                    model_config["regressor"]
                    if target_type == TargetType.REGRESSION
                    else model_config["classifier"]
                )

                # Base model
                base_model = model_class(random_state=42)

                # Hyperparameter tuning
                if hyperparameter_tuning and model_config["params"]:
                    search = RandomizedSearchCV(
                        base_model,
                        model_config["params"],
                        n_iter=20,
                        cv=cv_folds,
                        scoring="neg_mean_squared_error"
                        if target_type == TargetType.REGRESSION
                        else "accuracy",
                        random_state=42,
                        n_jobs=-1,
                    )
                    best_model = search.fit(X_train, y_train)
                    best_params = best_model.best_params_
                else:
                    best_model = base_model.fit(X_train, y_train)
                    best_params = {}

                # Create full pipeline
                full_pipeline = Pipeline([("preprocessor", pipeline), ("model", best_model)])

                # Fit pipeline
                full_pipeline.fit(X_train, y_train)

                # Evaluate model
                performance = await self._evaluate_model(
                    full_pipeline, X_test, y_test, target_type, cv_folds
                )

                # Store model
                model_id = f"{model_type.value}_team_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                prediction_model = PredictionModel(
                    model_id=model_id,
                    model_type=model_type,
                    prediction_type=PredictionType.TEAM_PERFORMANCE,
                    target_type=target_type,
                    model=full_pipeline,
                    feature_names=feature_cols,
                    target_name=target_variable,
                    performance=performance,
                    hyperparameters=best_params,
                    cross_val_score=np.mean(performance.cv_scores)
                    if performance.cv_scores
                    else None,
                )

                trained_models[model_type.value] = prediction_model
                model_performances[model_type.value] = performance

                # Save model
                await self._save_model(prediction_model)

                logger.info(
                    f"{model_type.value} model trained successfully. R²: {performance.r2:.3f}"
                    if target_type == TargetType.REGRESSION
                    else f"Accuracy: {performance.accuracy:.3f}"
                )

            except Exception as e:
                logger.error(f"Error training {model_type.value} model: {e!s}")
                continue

        # Compare models and select best
        best_model_name, comparison_metrics, recommendation = self._compare_models(
            model_performances, target_type
        )

        # Register best model in memory
        if best_model_name in trained_models:
            self.trained_models[f"team_performance_{best_model_name}"] = trained_models[
                best_model_name
            ]

        return ModelComparisonResult(
            model_performances=model_performances,
            best_model_name=best_model_name,
            comparison_metrics=comparison_metrics,
            recommendation=recommendation,
        )

    async def predict_team_performance(
        self,
        db: Session,
        team_id: int,
        model_id: str | None = None,
        include_confidence: bool = True,
        include_feature_importance: bool = True,
    ) -> PredictionResult:
        """
        Predict team performance for a specific team.

        Args:
            db: Database session
            team_id: Team ID to predict for
            model_id: Specific model to use (if None, uses best available)
            include_confidence: Whether to include confidence intervals
            include_feature_importance: Whether to include feature contributions

        Returns:
            PredictionResult with prediction and metadata
        """
        # Select model
        if model_id and model_id in self.trained_models:
            model = self.trained_models[model_id]
        else:
            # Find best team performance model
            team_models = {
                k: v
                for k, v in self.trained_models.items()
                if v.prediction_type == PredictionType.TEAM_PERFORMANCE
            }

            if not team_models:
                raise ValueError("No trained team performance models available")

            # Select model with best cross-validation score
            model = max(team_models.values(), key=lambda m: m.cross_val_score or 0)

        # Collect prediction data
        data_result = await self.data_service.collect_team_prediction_data(db, team_id)

        if not data_result["success"]:
            raise ValueError(f"Prediction data collection failed: {data_result.get('error')}")

        # Extract features in correct order
        feature_data = []
        for feature_name in model.feature_names:
            if feature_name in data_result["features"]:
                feature_data.append(data_result["features"][feature_name])
            else:
                feature_data.append(0.0)  # Default value

        X_pred = np.array(feature_data).reshape(1, -1)

        # Make prediction
        if hasattr(model.model, "predict_proba"):
            # Classification
            prediction = model.model.predict(X_pred)[0]
            probabilities = model.model.predict_proba(X_pred)[0]

            if include_confidence:
                confidence = np.max(probabilities)
            else:
                confidence = 0.0

            prob_dict = {}
            if hasattr(model.model, "classes_"):
                for i, cls in enumerate(model.model.classes_):
                    prob_dict[str(cls)] = probabilities[i]

        else:
            # Regression
            prediction = model.model.predict(X_pred)[0]
            confidence = 0.0
            prob_dict = {}

            # Calculate prediction interval for regression
            if include_confidence and hasattr(model.performance, "rmse"):
                interval = 1.96 * model.performance.rmse  # 95% confidence interval
                confidence_interval = (prediction - interval, prediction + interval)
            else:
                confidence_interval = None

        # Feature contributions (simplified SHAP-like approach)
        feature_contributions = {}
        if include_feature_importance and model.performance.feature_importance:
            for feature_name in model.feature_names:
                if feature_name in model.performance.feature_importance:
                    feature_contributions[feature_name] = model.performance.feature_importance[
                        feature_name
                    ] * data_result["features"].get(feature_name, 0.0)

        return PredictionResult(
            prediction=prediction,
            confidence=confidence,
            prediction_interval=confidence_interval
            if model.target_type == TargetType.REGRESSION
            else None,
            probabilities=prob_dict if model.target_type == TargetType.CLASSIFICATION else None,
            feature_contributions=feature_contributions,
            model_id=model.model_id,
            prediction_type=PredictionType.TEAM_PERFORMANCE,
        )

    async def train_user_outcome_model(
        self,
        db: Session,
        outcome_variable: str,
        user_ids: list[str] | None = None,
        model_types: list[ModelType] | None = None,
    ) -> ModelComparisonResult:
        """
        Train models to predict individual user outcomes.
        """
        # Similar implementation to team performance model but for individual users
        # This would use user-level data instead of team-level aggregation

        logger.info(f"Training user outcome model for: {outcome_variable}")

        # Implementation would follow similar pattern to train_team_performance_model
        # but focus on individual user features and outcomes

        raise NotImplementedError("User outcome model training not yet implemented")

    async def batch_predict(
        self,
        db: Session,
        prediction_type: PredictionType,
        entity_ids: list[int | str],
        model_id: str | None = None,
    ) -> list[PredictionResult]:
        """
        Make batch predictions for multiple entities.

        Args:
            db: Database session
            prediction_type: Type of prediction to make
            entity_ids: List of team IDs or user IDs
            model_id: Specific model to use

        Returns:
            List of prediction results
        """
        results = []

        # Use ThreadPoolExecutor for parallel predictions
        loop = asyncio.get_event_loop()

        if prediction_type == PredictionType.TEAM_PERFORMANCE:
            tasks = [
                loop.run_in_executor(
                    self.executor,
                    self.predict_team_performance,
                    db,
                    entity_id,
                    model_id,
                    True,
                    True,
                )
                for entity_id in entity_ids
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            valid_results = [r for r in results if not isinstance(r, Exception)]

            return valid_results

        # Add other prediction types as needed
        raise NotImplementedError(f"Batch prediction not implemented for {prediction_type}")

    async def evaluate_model_performance(
        self, model_id: str, test_data: dict[str, Any] | None = None, cv_folds: int = 5
    ) -> ModelPerformance:
        """
        Evaluate trained model performance.
        """
        if model_id not in self.trained_models:
            model = await self._load_model(model_id)
            if model:
                self.trained_models[model_id] = model
            else:
                raise ValueError(f"Model {model_id} not found")

        model = self.trained_models[model_id]

        if test_data is None:
            # Would need to collect fresh test data
            raise NotImplementedError("Test data collection not implemented")

        # Evaluate model on test data
        X_test = test_data["X"]
        y_test = test_data["y"]

        return await self._evaluate_model(model.model, X_test, y_test, model.target_type, cv_folds)

    def _determine_target_type(self, y: pd.Series) -> TargetType:
        """Determine if target is regression or classification."""
        if y.dtype in ["object", "category", "bool"]:
            unique_values = y.nunique()
            if unique_values == 2:
                return TargetType.BINARY
            if unique_values <= 10:
                return TargetType.MULTICLASS
            return TargetType.CLASSIFICATION
        return TargetType.REGRESSION

    def _create_preprocessing_pipeline(
        self, X_train: pd.DataFrame, feature_selection: bool, target_type: TargetType
    ) -> Any:
        """Create preprocessing pipeline for features."""

        # Identify numeric and categorical columns
        numeric_features = X_train.select_dtypes(include=["int64", "float64"]).columns
        categorical_features = X_train.select_dtypes(include=["object", "category"]).columns

        # Create preprocessing steps
        numeric_transformer = Pipeline(
            steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
        )

        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("onehot", pd.get_dummies),  # Simplified
            ]
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, numeric_features),
                ("cat", categorical_transformer, categorical_features),
            ]
        )

        # Add feature selection if requested
        if feature_selection:
            if target_type == TargetType.REGRESSION:
                selector = SelectKBest(score_func=f_regression, k=20)
            else:
                selector = SelectKBest(score_func=f_classif, k=20)

            pipeline = Pipeline([("preprocessor", preprocessor), ("feature_selection", selector)])
        else:
            pipeline = preprocessor

        return pipeline

    async def _evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        target_type: TargetType,
        cv_folds: int,
    ) -> ModelPerformance:
        """Evaluate model performance."""

        # Make predictions
        y_pred = model.predict(X_test)

        # Initialize performance metrics
        performance = ModelPerformance()

        if target_type == TargetType.REGRESSION:
            # Regression metrics
            performance.mse = mean_squared_error(y_test, y_pred)
            performance.mae = mean_absolute_error(y_test, y_pred)
            performance.rmse = np.sqrt(performance.mse)
            performance.r2 = r2_score(y_test, y_pred)
            performance.mape = mean_absolute_percentage_error(y_test, y_pred)
            performance.explained_variance = explained_variance_score(y_test, y_pred)

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_test, y_test, cv=cv_folds, scoring="neg_mean_squared_error"
            )
            performance.cv_scores = (-cv_scores).tolist()

        else:
            # Classification metrics
            performance.accuracy = accuracy_score(y_test, y_pred)
            performance.precision = precision_score(y_test, y_pred, average="weighted")
            performance.recall = recall_score(y_test, y_pred, average="weighted")
            performance.f1 = f1_score(y_test, y_pred, average="weighted")

            # For binary classification
            if len(np.unique(y_test)) == 2:
                if hasattr(model, "predict_proba"):
                    y_proba = model.predict_proba(X_test)[:, 1]
                    performance.auc = roc_auc_score(y_test, y_proba)

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_test, y_test, cv=StratifiedKFold(cv_folds), scoring="accuracy"
            )
            performance.cv_scores = cv_scores.tolist()

        # Feature importance (if available)
        if hasattr(model, "feature_importances_"):
            # Get feature names from preprocessing pipeline
            feature_names = [f"feature_{i}" for i in range(len(model.feature_importances_))]
            performance.feature_importance = dict(zip(feature_names, model.feature_importances_))

        return performance

    def _compare_models(
        self, model_performances: dict[str, ModelPerformance], target_type: TargetType
    ) -> tuple[str, dict[str, float], str]:
        """Compare models and select the best one."""

        comparison_metrics = {}

        if target_type == TargetType.REGRESSION:
            # Use R² score for regression (higher is better)
            scores = {}
            for name, perf in model_performances.items():
                if perf.r2 is not None:
                    scores[name] = perf.r2
                    comparison_metrics[name] = perf.r2

            best_model = (
                max(scores, key=scores.get) if scores else list(model_performances.keys())[0]
            )

            if scores[best_model] > 0.8:
                recommendation = f"Excellent model: {best_model} with R² = {scores[best_model]:.3f}"
            elif scores[best_model] > 0.6:
                recommendation = f"Good model: {best_model} with R² = {scores[best_model]:.3f}"
            else:
                recommendation = f"Fair model: {best_model} with R² = {scores[best_model]:.3f}. Consider feature engineering."

        else:
            # Use accuracy for classification
            scores = {}
            for name, perf in model_performances.items():
                if perf.accuracy is not None:
                    scores[name] = perf.accuracy
                    comparison_metrics[name] = perf.accuracy

            best_model = (
                max(scores, key=scores.get) if scores else list(model_performances.keys())[0]
            )

            if scores[best_model] > 0.9:
                recommendation = (
                    f"Excellent model: {best_model} with accuracy = {scores[best_model]:.3f}"
                )
            elif scores[best_model] > 0.8:
                recommendation = (
                    f"Good model: {best_model} with accuracy = {scores[best_model]:.3f}"
                )
            else:
                recommendation = f"Fair model: {best_model} with accuracy = {scores[best_model]:.3f}. Consider more data or feature engineering."

        return best_model, comparison_metrics, recommendation

    async def _save_model(self, model: PredictionModel) -> None:
        """Save trained model to disk."""
        model_path = self.model_save_path / f"{model.model_id}.joblib"

        # Prepare model data for saving
        model_data = {
            "model": model.model,
            "model_type": model.model_type.value,
            "prediction_type": model.prediction_type.value,
            "target_type": model.target_type.value,
            "feature_names": model.feature_names,
            "target_name": model.target_name,
            "performance": {
                "mse": model.performance.mse,
                "mae": model.performance.mae,
                "rmse": model.performance.rmse,
                "r2": model.performance.r2,
                "accuracy": model.performance.accuracy,
                "precision": model.performance.precision,
                "recall": model.performance.recall,
                "f1": model.performance.f1,
                "auc": model.performance.auc,
                "cv_scores": model.performance.cv_scores,
                "feature_importance": model.performance.feature_importance,
            },
            "hyperparameters": model.hyperparameters,
            "training_date": model.training_date.isoformat(),
            "cross_val_score": model.cross_val_score,
        }

        joblib.dump(model_data, model_path)
        logger.info(f"Model saved to {model_path}")

    async def _load_model(self, model_id: str) -> PredictionModel | None:
        """Load trained model from disk."""
        model_path = self.model_save_path / f"{model_id}.joblib"

        if not model_path.exists():
            return None

        try:
            model_data = joblib.load(model_path)

            # Reconstruct ModelPerformance object
            performance = ModelPerformance(
                mse=model_data["performance"].get("mse"),
                mae=model_data["performance"].get("mae"),
                rmse=model_data["performance"].get("rmse"),
                r2=model_data["performance"].get("r2"),
                accuracy=model_data["performance"].get("accuracy"),
                precision=model_data["performance"].get("precision"),
                recall=model_data["performance"].get("recall"),
                f1=model_data["performance"].get("f1"),
                auc=model_data["performance"].get("auc"),
                cv_scores=model_data["performance"].get("cv_scores", []),
                feature_importance=model_data["performance"].get("feature_importance", {}),
            )

            # Reconstruct PredictionModel
            model = PredictionModel(
                model_id=model_id,
                model_type=ModelType(model_data["model_type"]),
                prediction_type=PredictionType(model_data["prediction_type"]),
                target_type=TargetType(model_data["target_type"]),
                model=model_data["model"],
                feature_names=model_data["feature_names"],
                target_name=model_data["target_name"],
                performance=performance,
                hyperparameters=model_data["hyperparameters"],
                training_date=datetime.fromisoformat(model_data["training_date"]),
                cross_val_score=model_data["cross_val_score"],
            )

            return model

        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e!s}")
            return None

    async def get_model_info(self, model_id: str) -> dict[str, Any] | None:
        """Get model information and metadata."""
        if model_id in self.trained_models:
            model = self.trained_models[model_id]
        else:
            model = await self._load_model(model_id)
            if model:
                self.trained_models[model_id] = model
            else:
                return None

        return {
            "model_id": model.model_id,
            "model_type": model.model_type.value,
            "prediction_type": model.prediction_type.value,
            "target_type": model.target_type.value,
            "feature_names": model.feature_names,
            "target_name": model.target_name,
            "performance": {
                "mse": model.performance.mse,
                "mae": model.performance.mae,
                "rmse": model.performance.rmse,
                "r2": model.performance.r2,
                "accuracy": model.performance.accuracy,
                "precision": model.performance.precision,
                "recall": model.performance.recall,
                "f1": model.performance.f1,
                "auc": model.performance.auc,
                "cv_scores": model.performance.cv_scores,
                "feature_importance": model.performance.feature_importance,
            },
            "hyperparameters": model.hyperparameters,
            "training_date": model.training_date.isoformat(),
            "cross_val_score": model.cross_val_score,
        }

    async def list_trained_models(
        self, prediction_type: PredictionType | None = None
    ) -> list[dict[str, Any]]:
        """List all trained models."""
        models = []

        # Get model files
        model_files = list(self.model_save_path.glob("*.joblib"))

        for model_file in model_files:
            model_id = model_file.stem
            model_info = await self.get_model_info(model_id)

            if model_info:
                if (
                    prediction_type is None
                    or model_info["prediction_type"] == prediction_type.value
                ):
                    models.append(model_info)

        return models

    async def delete_model(self, model_id: str) -> bool:
        """Delete a trained model."""
        # Remove from memory
        if model_id in self.trained_models:
            del self.trained_models[model_id]

        # Remove from disk
        model_path = self.model_save_path / f"{model_id}.joblib"
        if model_path.exists():
            model_path.unlink()
            return True

        return False
