"""
Train Bayesian Burnout Predictor on Historical Data

This script loads historical assessment and wellness data to train
the Bayesian burnout prediction model.

Usage:
    python scripts/train_burnout_predictor.py [--samples N] [--chains N]

Author: PsychSync Engineering Team
Version: 2.0
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.db.models.response import Response
from app.db.models.user import User
from app.db.models.wellness_burnout import WellnessMetrics
from app.services.burnout.bayesian_burnout_predictor import BayesianBurnoutPredictor

logger = logging.getLogger(__name__)


async def load_historical_data(db: AsyncSession, lookback_days: int = 365) -> tuple:
    """
    Load historical data for model training

    Returns:
        X: Feature matrix (n_samples, n_features)
        y: BRS scores (n_samples,)
        org_ids: Organization IDs (n_samples,)
    """
    logger.info(f"Loading historical data from last {lookback_days} days")

    cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

    # Query wellness metrics that have BRS scores
    # In production, you would query actual historical assessment data
    # For now, we'll create synthetic data for demonstration

    # Get organizations
    org_result = await db.execute(select(User.organization_id).distinct().limit(100))
    org_ids = [row[0] for row in org_result if row[0] is not None]

    if not org_ids:
        logger.warning(
            "No organizations found. Creating synthetic data for demonstration."
        )
        return create_synthetic_training_data(n_samples=500, n_organizations=50)

    logger.info(f"Found {len(org_ids)} organizations")

    # Query wellness metrics
    # In production, this would join with assessment tables
    query = (
        select(WellnessMetrics)
        .where(WellnessMetrics.measurement_date >= cutoff_date)
        .order_by(WellnessMetrics.measurement_date)
        .limit(1000)
    )

    result = await db.execute(query)
    wellness_records = result.scalars().all()

    logger.info(f"Found {len(wellness_records)} wellness records")

    # Extract features and calculate BRS
    X_list = []
    y_list = []
    org_id_list = []

    for record in wellness_records:
        # Extract features from wellness record
        # In production, these would come from actual assessments
        features = extract_features_from_wellness(record)
        brs = calculate_brs_from_wellness(record)

        if features is not None and brs is not None:
            X_list.append(features)
            y_list.append(brs)
            # Get organization ID for this user
            org_id_list.append(record.user_id % 100)  # Modulo for demo

    if len(X_list) < 50:
        logger.warning(
            f"Insufficient real data ({len(X_list)} samples). Augmenting with synthetic data."
        )
        X_synthetic, y_synthetic, org_synthetic = create_synthetic_training_data(
            n_samples=500 - len(X_list), n_organizations=len(org_ids)
        )
        X_list.extend(X_synthetic.tolist())
        y_list.extend(y_synthetic.tolist())
        org_id_list.extend(org_synthetic.tolist())

    X = np.array(X_list)
    y = np.array(y_list)
    org_ids = np.array(org_id_list)

    logger.info(f"Loaded {len(X)} samples from {len(set(org_ids))} organizations")

    return X, y, org_ids


def extract_features_from_wellness(wellness_record) -> np.ndarray:
    """Extract feature vector from wellness metrics"""
    try:
        # Extract features (12 features total)
        features = np.array(
            [
                wellness_record.workload_stress or 50,  # weekly_hours proxy
                min(wellness_record.consecutive_work_days or 0, 30),  # continuous_days
                wellness_record.after_hours_work_pct or 0.1,  # after_hours_percentage
                0,  # pto_days_used (not in wellness)
                wellness_record.sleep_quality or 0.7,  # sleep_hours_avg proxy
                abs(wellness_record.sentiment_avg or 0),  # negative_sentiment_avg proxy
                wellness_record.sentiment_volatility or 0.3,
                wellness_record.conflict_score or 0,
                wellness_record.communication_decline or 0,
                wellness_record.meeting_decline or 0,
                min(
                    wellness_record.social_withdrawal or 0, 1.0
                ),  # social_interaction_score proxy
                0.5,  # response_time proxy (hours)
            ]
        )
        return features
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return None


def calculate_brs_from_wellness(wellness_record) -> float:
    """Calculate BRS from wellness metrics"""
    try:
        # Use the stress_level as a proxy for BRS
        # stress_level is 0-10, convert to 0-100
        brs = (wellness_record.stress_level or 5) * 10
        return min(max(brs, 0), 100)
    except Exception as e:
        logger.error(f"Error calculating BRS: {e}")
        return None


def create_synthetic_training_data(
    n_samples: int = 500, n_organizations: int = 50
) -> tuple:
    """
    Create synthetic training data for demonstration

    This generates realistic synthetic data based on the patterns
    observed in actual burnout cases.
    """
    logger.info(
        f"Creating {n_samples} synthetic samples for {n_organizations} organizations"
    )

    np.random.seed(42)

    # Generate features
    X = np.random.randn(n_samples, 12)

    # Normalize features to realistic ranges
    X[:, 0] = 40 + X[:, 0] * 15  # weekly_hours: mean 50, std 15
    X[:, 0] = np.clip(X[:, 0], 20, 80)

    X[:, 1] = np.random.exponential(3, n_samples)  # continuous_days
    X[:, 1] = np.clip(X[:, 1], 0, 30)

    X[:, 2] = np.random.beta(2, 5, n_samples)  # after_hours_pct

    X[:, 4] = 5 + X[:, 4] * 2  # sleep_hours_avg: mean 7, std 2
    X[:, 4] = np.clip(X[:, 4], 4, 10)

    X[:, 6] = np.abs(np.random.randn(n_samples)) * 0.5  # sentiment_volatility
    X[:, 6] = np.clip(X[:, 6], 0, 1.5)

    # Generate BRS scores based on features
    y = (
        0.25 * X[:, 0] * 1.5
        + 0.20 * X[:, 1] * 2.0  # workload
        + 0.18 * X[:, 6] * 50  # recovery (inverted)
        + 0.15 * X[:, 7] * 10  # sentiment
        + 0.12 * X[:, 8] * 30  # withdrawal  # pattern
    )

    # Add noise
    y += np.random.randn(n_samples) * 5
    y = np.clip(y, 0, 100)

    # Generate organization IDs
    org_ids = np.random.randint(0, n_organizations, n_samples)

    return X, y, org_ids


async def train_model(
    samples: int = 2000,
    chains: int = 4,
    tune: int = 1000,
    target_accept: float = 0.95,
    cores: int = 4,
):
    """Train the Bayesian predictor"""
    logger.info("Starting Bayesian predictor training...")

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        pass  # Connection test

    # Load historical data
    async with AsyncSession(engine) as db:
        X, y, org_ids = await load_historical_data(db, lookback_days=365)

    logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
    logger.info(f"Organizations: {len(set(org_ids))}")

    # Create predictor
    n_features = X.shape[1]
    n_organizations = len(set(org_ids))

    logger.info(
        f"Creating Bayesian predictor: {n_features} features, {n_organizations} orgs"
    )

    predictor = BayesianBurnoutPredictor(
        n_features=n_features, n_organizations=n_organizations
    )

    # Build model
    logger.info("Building Bayesian hierarchical model...")
    predictor.build_model(X, y, org_ids)

    # Train model
    logger.info(
        f"Training with {samples} samples, {chains} chains, {tune} tuning steps..."
    )
    logger.info("This may take 15-30 minutes...")

    trace = predictor.fit(
        X,
        y,
        org_ids,
        samples=samples,
        tune=tune,
        chains=chains,
        target_accept=target_accept,
        cores=cores,
    )

    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / "bayesian_burnout_predictor.nc"
    import arviz as az

    az.to_netcdf(trace, str(model_path))

    logger.info(f"✅ Model saved to {model_path}")

    # Print summary
    summary = az.summary(trace, hdi_prob=0.94)
    logger.info("\n=== Model Summary ===")
    logger.info(summary.to_string())

    # Print feature importance
    logger.info("\n=== Feature Importance ===")
    importance = predictor.get_feature_importance()
    for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {feature}: {score:.3f}")

    return predictor


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Train Bayesian burnout predictor")
    parser.add_argument(
        "--samples",
        type=int,
        default=2000,
        help="Number of MCMC samples (default: 2000)",
    )
    parser.add_argument(
        "--chains", type=int, default=4, help="Number of MCMC chains (default: 4)"
    )
    parser.add_argument(
        "--tune", type=int, default=1000, help="Number of tuning steps (default: 1000)"
    )
    parser.add_argument(
        "--target-accept",
        type=float,
        default=0.95,
        help="Target acceptance rate (default: 0.95)",
    )
    parser.add_argument(
        "--cores", type=int, default=4, help="Number of CPU cores to use (default: 4)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 80)
    logger.info("BAYESIAN BURNOUT PREDICTOR - TRAINING")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  Samples: {args.samples}")
    logger.info(f"  Chains: {args.chains}")
    logger.info(f"  Tune: {args.tune}")
    logger.info(f"  Target Accept: {args.target_accept}")
    logger.info(f"  Cores: {args.cores}")
    logger.info("")

    # Run training
    asyncio.run(
        train_model(
            samples=args.samples,
            chains=args.chains,
            tune=args.tune,
            target_accept=args.target_accept,
            cores=args.cores,
        )
    )

    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Model saved to: models/bayesian_burnout_predictor.nc")
    logger.info("  2. Start backend server: uvicorn app.main:app --reload")
    logger.info("  3. Test prediction endpoints")
    logger.info("  4. View CEO dashboard: http://localhost:5173/executive/burnout")
    logger.info("")


if __name__ == "__main__":
    main()
