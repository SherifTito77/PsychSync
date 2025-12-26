"""
Prediction Data Collection Service
Comprehensive service for collecting, preprocessing, and preparing data
for machine learning model training and prediction analytics.
"""

import asyncio
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.dialects.postgresql import array_agg

from app.core.database import get_db

from app.core.path_utils import sanitize_path, safe_filename
from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import Team
from app.db.models.team import TeamMember
from app.services.irt_service import IRTService, IRTModel
from app.services.nlp_service import NLPService, TextAnalysis

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of data for ML models"""
    ASSESSMENT_RESPONSES = "assessment_responses"
    USER_DEMOGRAPHICS = "user_demographics"
    TEAM_PERFORMANCE = "team_performance"
    ITEM_ANALYTICS = "item_analytics"
    RESPONSE_TIMES = "response_times"
    TEXT_ANALYTICS = "text_analytics"
    TEMPORAL_PATTERNS = "temporal_patterns"


class DataQualityLevel(Enum):
    """Data quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INSUFFICIENT = "insufficient"


@dataclass
class FeatureDefinition:
    """Definition of a feature for ML models"""
    name: str
    feature_type: str
    data_type: DataType
    description: str
    calculation_method: str
    aggregation_method: str
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    category: str = ""
    importance_weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "feature_type": self.feature_type,
            "data_type": self.data_type.value,
            "description": self.description,
            "calculation_method": self.calculation_method,
            "aggregation_method": self.aggregation_method,
            "validation_rules": self.validation_rules,
            "category": self.category,
            "importance_weight": self.importance_weight
        }


@dataclass
class DatasetStatistics:
    """Statistics for a collected dataset"""
    dataset_name: str
    record_count: int
    feature_count: int
    time_period: Tuple[datetime, datetime]
    quality_level: DataQualityLevel
    completeness_score: float
    data_range: Dict[str, Tuple[float, float]]
    correlation_matrix: Dict[str, float] = field(default_factory=dict)
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "record_count": self.record_count,
            "feature_count": self.feature_count,
            "time_period": [t.isoformat() for t in self.time_period],
            "quality_level": self.quality_level.value,
            "completeness_score": self.completeness_score,
            "data_range": self.data_range,
            "correlation_matrix": self.correlation_matrix,
            "summary_stats": self.summary_stats,
            "created_at": self.created_at.isoformat()
        }


class PredictionDataCollectionService:
    """Service for collecting and preparing data for ML models"""

    def __init__(self):
        self.irt_service = IRTService()
        self.nlp_service = NLPService()

        # Feature definitions
        self.feature_definitions = self._initialize_feature_definitions()

        # Data collection configuration
        self.config = {
            "min_responses_per_assessment": 5,
            "min_persons_for_training": 100,
            "min_items_per_assessment": 10,
            "quality_check_enabled": True,
            "outlier_detection_enabled": True,
            "data_retention_days": 365
        }

        logger.info("Prediction Data Collection Service initialized")

    def _initialize_feature_definitions(self) -> List[FeatureDefinition]:
        """Initialize default feature definitions"""
        return [
            # Assessment response features
            FeatureDefinition(
                name="total_correct_responses",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="Total number of correct responses",
                calculation_method="sum",
                aggregation_method="sum",
                validation_rules={"min": 0, "max": None},
                category="performance",
                importance_weight=1.0
            ),
            FeatureDefinition(
                name="total_responses",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="Total number of responses",
                calculation_method="count",
                aggregation_method="sum",
                validation_rules={"min": 5, "max": None},
                category="engagement",
                importance_weight=0.8
            ),
            FeatureDefinition(
                name="accuracy_rate",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="Response accuracy rate",
                calculation_method="ratio",
                aggregation_method="mean",
                validation_rules={"min": 0.0, "max": 1.0},
                category="performance",
                importance_weight=1.2
            ),
            FeatureDefinition(
                name="difficulty_adjusted_score",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="IRT difficulty-adjusted score",
                calculation_method="irt_weighted",
                aggregation_method="sum",
                validation_rules={"min": 0.0, "max": 100.0},
                category="performance",
                importance_weight=1.5
            ),

            # IRT model features
            FeatureDefinition(
                name="estimated_ability",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="Estimated ability from IRT model",
                calculation_method="irt_ability",
                aggregation_method="mean",
                validation_rules={"min": -4.0, "max": 4.0},
                category="psychometric",
                importance_weight=1.0
            ),
            FeatureDefinition(
                name="measurement_error",
                feature_type="numeric",
                data_type=DataType.ASSESSMENT_RESPONSES,
                description="Standard error of ability estimate",
                calculation_method="irt_se",
                aggregation_method="mean",
                validation_rules={"min": 0.0, "max": 2.0},
                category="psychometric",
                importance_weight=0.8
            ),

            # Response time features
            FeatureDefinition(
                name="mean_response_time",
                feature_type="numeric",
                data_type=DataType.RESPONSE_TIMES,
                description="Average response time per item",
                calculation_method="mean",
                aggregation_method="mean",
                validation_rules={"min": 0.1, "max": 300.0},
                category="behavioral",
                importance_weight=0.6
            ),
            FeatureDefinition(
                name="response_time_variance",
                feature_type="numeric",
                data_type=DataType.RESPONSE_TIMES,
                description="Variance in response times",
                calculation_method="variance",
                aggregation_method="mean",
                validation_rules={"min": 0.01, "max": 10000.0},
                category="behavioral",
                importance_weight=0.4
            ),

            # Text analytics features
            FeatureDefinition(
                name="text_complexity",
                feature_type="numeric",
                data_type=DataType.TEXT_ANALYTICS,
                description="Average text complexity score",
                calculation_method="mean",
                aggregation_method="mean",
                validation_rules={"min": 10, "max": 50},
                category="linguistic",
                importance_weight=0.7
            ),
            FeatureDefinition(
                name="response_length",
                feature_type="numeric",
                data_type=DataType.TEXT_ANALYTICS,
                description="Average response text length",
                calculation_method="mean",
                aggregation_method="mean",
                validation_rules={"min": 5, "max": 500},
                category="linguistic",
                importance_weight=0.5
            ),
            FeatureDefinition(
                name="sentiment_score",
                feature_type="numeric",
                data_type=DataType.TEXT_ANALYTICS,
                description="Average sentiment polarity score",
                calculation_method="mean",
                aggregation_method="mean",
                validation_rules={"min": -1.0, "max": 1.0},
                category="affective",
                importance_weight=0.8
            ),

            # Team performance features
            FeatureDefinition(
                name="team_avg_performance",
                feature_type="numeric",
                data_type=DataType.TEAM_PERFORMANCE,
                description="Team average performance score",
                calculation_method="mean",
                aggregation_method="team_level",
                validation_rules={"min": 0.0, "max": 100.0},
                category="team",
                importance_weight=1.2
            ),
            FeatureDefinition(
                name="team_performance_variance",
                feature_type="numeric",
                data_type=DataType.TEAM_PERFORMANCE,
                description="Variance in team performance",
                calculation_method="variance",
                aggregation_method="team_level",
                validation_rules={"min": 0.0, "max": 100.0},
                category="team",
                importance_weight=0.8
            ),
        ]

    async def collect_assessment_data(
        self,
        db: Session,
        assessment_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
        user_ids: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        min_responses: Optional[int] = None
    ) -> Dict[str, Any]:
        """Collect assessment response data for ML training"""
        try:
            # Build query filters
            query = []

            if assessment_ids:
                query.append(Response.assessment_id.in_(assessment_ids))
            if team_ids:
                query.append(Assessment.team_id.in_(team_ids))
            if user_ids:
                query.append(Response.user_id.in_(user_ids))
            if date_range:
                query.append(Response.created_at.between(date_range[0], date_range[1]))

            # Execute query
            if query:
                responses = db.query(Response).filter(and_(*query)).all()
            else:
                responses = db.query(Response).all()

            if not responses:
                logger.warning("No responses found matching criteria")
                return {"data": [], "statistics": self._create_empty_statistics()}

            # Convert to pandas DataFrame
            data_list = []
            for response in responses:
                data_list.append({
                    "response_id": response.id,
                    "user_id": response.user_id,
                    "assessment_id": response.assessment_id,
                    "team_id": response.assessment.team_id,
                    "item_id": response.item_id,
                    "response": response.response,
                    "response_time": response.response_time,
                    "created_at": response.created_at,
                    "updated_at": response.updated_at
                })

            df = pd.DataFrame(data_list)

            # Apply quality filters
            if min_responses:
                # Filter assessments with minimum responses
                assessment_counts = df.groupby('assessment_id')['response_id'].count()
                valid_assessments = assessment_counts[assessment_counts >= min_responses].index.tolist()
                df = df[df['assessment_id'].isin(valid_assessments)]

            if df.empty:
                return {"data": [], "statistics": self._create_empty_statistics()}

            # Calculate initial statistics
            statistics = self._calculate_basic_statistics(df, DataType.ASSESSMENT_RESPONSES)

            # Apply data cleaning and validation
            df_cleaned = self._clean_response_data(df)

            # Calculate quality score
            quality_score = self._calculate_data_quality_score(df_cleaned)

            return {
                "data": df_cleaned.to_dict('records'),
                "statistics": statistics.to_dict(),
                "quality_score": quality_score
            }

        except Exception as e:
            logger.error(f"Error collecting assessment data: {str(e)}")
            return {"data": [], "statistics": self._create_empty_statistics()}

    async def collect_user_demographics(
        self,
        db: Session,
        user_ids: Optional[List[str]] = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Collect user demographic data"""
        try:
            # Build query
            query = []

            if user_ids:
                query.append(User.id.in_(user_ids))
            if not include_inactive:
                query.append(User.is_active == True)

            # Execute query
            if query:
                users = db.query(User).filter(and_(*query)).all()
            else:
                users = db.query(User).filter(User.is_active == True).all()

            # Convert to DataFrame
            data_list = []
            for user in users:
                data_list.append({
                    "user_id": user.id,
                    "email": user.email,
                    "age": user.age,
                    "gender": user.gender,
                    "education_level": user.education_level,
                    "department": user.department,
                    "location": user.location,
                    "years_experience": user.years_experience,
                    "created_at": user.created_at,
                    "last_login": user.last_login
                })

            df = pd.DataFrame(data_list)

            # Handle missing values
            df_cleaned = self._clean_demographic_data(df)

            return {
                "data": df_cleaned.to_dict('records'),
                "statistics": self._calculate_basic_statistics(df_cleaned, DataType.USER_DEMOGRAPHICS)
            }

        except Exception as e:
            logger.error(f"Error collecting user demographics: {str(e)}")
            return {"data": [], "statistics": self._create_empty_statistics()}

    async def collect_team_performance_data(
        self,
        db: Session,
        team_ids: Optional[List[int]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Collect team performance data"""
        try:
            # This would typically aggregate from assessment results
            # For now, we'll simulate team performance from assessment data

            # First collect assessment data with team information
            assessment_data = await self.collect_assessment_data(db, team_ids=team_ids, date_range=date_range)

            if not assessment_data["data"]:
                return {"data": [], "statistics": self._create_empty_statistics()}

            df_assessments = pd.DataFrame(assessment_data["data"])

            # Aggregate by team
            team_performance = df_assessessments.groupby(['team_id', 'user_id']).agg({
                'total_correct': ('response', 'sum'),
                'total_responses': ('response', 'count'),
                'mean_response_time': ('response_time', 'mean'),
                'assessment_count': ('assessment_id', 'nunique')
            }).reset_index()

            # Calculate team-level metrics
            team_level_stats = team_performance.groupby('team_id').agg({
                'team_avg_correct': ('total_correct', 'sum'),
                'team_total_responses': ('total_responses', 'sum'),
                'team_performance': ('total_correct', 'sum') / ('total_responses', 'sum'),
                'team_response_time': ('mean_response_time', 'mean'),
                'team_member_count': ('user_id', 'nunique'),
                'assessment_count': ('assessment_count', 'sum')
            }).reset_index()

            return {
                "data": team_level_stats.to_dict('records'),
                "statistics": self._calculate_basic_statistics(
                    team_level_stats, DataType.TEAM_PERFORMANCE
                )
            }

        except Exception as e:
            logger.error(f"Error collecting team performance data: {str(e)}")
            return {"data": [], "statistics": self._create_empty_statistics()}

    async def collect_item_analytics(
        self,
        db: Session,
        item_ids: Optional[List[int]] = None,
        assessment_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Collect item-level analytics"""
        try:
            # This would analyze item difficulty, discrimination, etc.
            # For now, we'll collect basic item statistics from assessment data

            assessment_data = await self.collect_assessment_data(db, assessment_ids=assessment_ids)

            if not assessment_data["data"]:
                return {"data": [], "statistics": self._create_empty_statistics()}

            df_assessments = pd.DataFrame(assessment_data["data"])

            # Item-level statistics
            item_stats = df_assessments.groupby('item_id').agg({
                'total_correct': ('response', 'sum'),
                'total_attempts': ('response', 'count'),
                'accuracy_rate': ('response', 'mean'),
                'mean_response_time': ('response_time', 'mean'),
                'response_time_variance': ('response_time', 'variance')
            }).reset_index()

            return {
                "data": item_stats.to_dict('records'),
                "statistics": self._calculate_basic_statistics(item_stats, DataType.ITEM_ANALYTICS)
            }

        except Exception as e:
            logger.error(f"Error collecting item analytics: {str(e)}")
            return {"data": [], "statistics": self._create_empty_statistics()}

    async def prepare_training_dataset(
        self,
        data_config: Dict[str, Any],
        include_irt_features: bool = True,
        include_text_features: bool = True,
        include_demographic_features: bool = True,
        include_team_features: bool = False
    ) -> Dict[str, Any]:
        """Prepare comprehensive training dataset for ML models"""
        try:
            db = get_db()

            dataset_parts = {}
            feature_matrices = {}

            # Collect different types of data
            if data_config.get("include_assessment_responses", True):
                assessment_data = await self.collect_assessment_data(
                    db,
                    assessment_ids=data_config.get("assessment_ids"),
                    team_ids=data_config.get("team_ids"),
                    user_ids=data_config.get("user_ids"),
                    date_range=data_config.get("date_range")
                )
                dataset_parts["assessment_responses"] = assessment_data["data"]

                # Calculate IRT features if requested
                if include_irt_features:
                    irt_features = await self._extract_irt_features(
                        assessment_data["data"]
                    )
                    feature_matrices["irt_features"] = irt_features

            if data_config.get("include_demographic_features", True) and include_demographic_features:
                demographics_data = await self.collect_user_demographics(db)
                dataset_parts["user_demographics"] = demographics_data["data"]

            if data_config.get("include_team_features", True) and include_team_features:
                team_data = await self.collect_team_performance_data(
                    db,
                    team_ids=data_config.get("team_ids"),
                    date_range=data_config.get("date_range")
                )
                dataset_parts["team_performance"] = team_data["data"]

            if data_config.get("include_item_analytics", True):
                item_data = await self.collect_item_analytics(
                    db,
                    item_ids=data_config.get("item_ids"),
                    assessment_ids=data_config.get("assessment_ids")
                )
                dataset_parts["item_analytics"] = item_data["data"]

            # Calculate text features if requested
            if include_text_features and data_config.get("include_text_features", True):
                text_features = await self._extract_text_features(
                    dataset_parts.get("assessment_responses", [])
                )
                feature_matrices["text_features"] = text_features

            # Combine all data into final dataset
            final_dataset = self._combine_datasets(dataset_parts, feature_matrices)

            # Final quality assessment
            quality_score = self._assess_dataset_quality(final_dataset)

            return {
                "dataset": final_dataset,
                "feature_matrices": feature_matrices,
                "data_parts": dataset_parts,
                "quality_score": quality_score,
                "metadata": {
                    "data_types": list(dataset_parts.keys()),
                    "feature_count": len(final_dataset.columns) if hasattr(final_dataset, 'columns') else 0,
                    "record_count": len(final_dataset),
                    "created_at": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error preparing training dataset: {str(e)}")
            return {"dataset": None, "feature_matrices": {}, "metadata": {}}

    async def _extract_irt_features(
        self,
        response_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract IRT-based features from response data"""
        try:
            # This would use the calibrated IRT model
            # For now, we'll return simple IRT-like features

            # Convert to DataFrame
            df = pd.DataFrame(response_data)

            if df.empty:
                return []

            # Group by user and assessment for IRT estimation
            user_assessments = df.groupby(['user_id', 'assessment_id']).agg({
                'correct_responses': ('response', 'sum'),
                'total_responses': ('response', 'count'),
                'difficulty_estimate': ('response', 'mean')  # Simplified difficulty estimate
            }).reset_index()

            # Calculate IRT-like features
            irt_features = []
            for _, row in user_assessments.iterrows():
                if row['total_responses'] > 0:
                    accuracy = row['correct_responses'] / row['total_responses']
                    # Use logit transformation
                    difficulty_estimate = row['difficulty_estimate']
                    if difficulty_estimate == 0:
                        difficulty_estimate = 0.01  # Avoid log(0)

                    if difficulty_estimate > 0 and difficulty_estimate < 1:
                        ability_estimate = math.log(difficulty_estimate / (1 - difficulty_estimate))
                    elif difficulty_estimate == 1:
                        ability_estimate = 3.0
                    elif difficulty_estimate == 0:
                        ability_estimate = -3.0
                    else:
                        ability_estimate = math.log(difficulty_estimate / (1 - difficulty_estimate))

                    irt_features.append({
                        "user_id": row['user_id'],
                        "assessment_id": row['assessment_id'],
                        "estimated_ability": ability_estimate,
                        "accuracy_rate": accuracy,
                        "item_count": row['total_responses'],
                        "logit_difficulty": math.log(row['difficulty_estimate'] / (1 - row['difficulty_estimate'])) if 0 < row['difficulty_estimate'] < 1 else 3.0
                    })

            return irt_features

        except Exception as e:
            logger.error(f"Error extracting IRT features: {str(e)}")
            return []

    async def _extract_text_features(
        self,
        response_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract text analytics features from response data"""
        try:
            # Collect text responses
            text_responses = []

            for response in response_data:
                if response.get('text_response'):
                    text_responses.append({
                        "user_id": response['user_id'],
                        "assessment_id": response['assessment_id'],
                        "text": response['text_response']
                    })

            if not text_responses:
                return []

            # Process text features using NLP service
            text_analyses = []
            for text_response in text_responses:
                try:
                    analysis = await self.nlp_service.analyze_text(
                        text_response["text"],
                        include_sentiment=True,
                        include_themes=True,
                        include_phrases=True
                    )

                    text_analyses.append({
                        "user_id": text_response["user_id"],
                        "assessment_id": text_response["assessment_id"],
                        "text_length": analysis.word_count,
                        "readability_score": analysis.readability_score,
                        "complexity": analysis.complexity.value,
                        "sentiment_score": analysis.sentiment.polarity,
                        "sentiment_confidence": analysis.sentiment.confidence,
                        "theme_count": len(analysis.themes),
                        "key_phrase_count": len(analysis.key_phrases)
                    })
                except Exception as e:
                    logger.warning(f"Error analyzing text: {str(e)}")
                    continue

            return text_analyses

        except Exception as e:
            logger.error(f"Error extracting text features: {str(e)}")
            return []

    def _combine_datasets(
        self,
        dataset_parts: Dict[str, List[Dict[str, Any]]],
        feature_matrices: Dict[str, List[Dict[str, Any]]]
    ) -> pd.DataFrame:
        """Combine different data parts into final training dataset"""
        try:
            # Start with assessment responses
            if "assessment_responses" in dataset_parts:
                df = pd.DataFrame(dataset_parts["assessment_responses"])
            else:
                return pd.DataFrame()

            # Add user demographic features
            if "user_demographics" in dataset_parts:
                demo_df = pd.DataFrame(dataset_parts["user_demographics"])
                df = pd.merge(
                    df, demo_df,
                    left_on='user_id',
                    how='left'
                )

            # Add IRT features
            if "irt_features" in feature_matrices and feature_matrices["irt_features"]:
                irt_df = pd.DataFrame(feature_matrices["irt_features"])
                df = pd.merge(
                    df, irt_df,
                    left_on=['user_id', 'assessment_id'],
                    how='left'
                )

            # Add text features
            if "text_features" in feature_matrices and feature_matrices["text_features"]:
                text_df = pd.DataFrame(feature_matrices["text_features"])
                df = pd.merge(
                    df, text_df,
                    left_on=['user_id', 'assessment_id'],
                    how='left'
                )

            # Add team features
            if "team_performance" in dataset_parts:
                team_df = pd.DataFrame(dataset_parts["team_performance"])
                df = pd.merge(
                    df, team_df,
                    left_on='team_id',
                    how='left'
                )

            # Add item features
            if "item_analytics" in dataset_parts:
                item_df = pd.DataFrame(dataset_parts["item_analytics"])
                df = pd.merge(
                    df, item_df,
                    left_on='item_id',
                    how='left'
                )

            return df

        except Exception as e:
            logger.error(f"Error combining datasets: {str(e)}")
            return pd.DataFrame()

    def _clean_response_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate response data"""
        try:
            # Remove completely empty rows
            df = df.dropna(subset=['user_id', 'item_id', 'response'])

            # Validate response values
            df = df[(df['response'].isin([0, 1]))]

            # Filter responses with valid timing
            if 'response_time' in df.columns:
                df = df[(df['response_time'] > 0) & (df['response_time'] < 300)]  # 5 minutes max

            # Remove duplicate responses (same user, item, assessment)
            df = df.drop_duplicates(subset=['user_id', 'item_id', 'assessment_id'])

            return df

        except Exception as e:
            logger.error(f"Error cleaning response data: {str(e)}")
            return df

    def _clean_demographic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean demographic data"""
        try:
            # Handle missing values
            if 'age' in df.columns:
                df['age'] = df['age'].fillna(df['age'].median())

            if 'years_experience' in df.columns:
                df['years_experience'] = df['years_experience'].fillna(df['years_experience'].median())

            # Validate ranges
            if 'age' in df.columns:
                df = df[(df['age'] >= 18) & (df['age'] <= 80)]  # Reasonable working age range

            return df

        except Exception as e:
            logger.error(f"Error cleaning demographic data: {str(e)}")
            return df

    def _calculate_basic_statistics(
        self,
        df: pd.DataFrame,
        data_type: DataType
    ) -> DatasetStatistics:
        """Calculate basic statistics for a dataset"""
        try:
            if df.empty:
                return self._create_empty_statistics()

            # Calculate time range
            if 'created_at' in df.columns:
                min_date = df['created_at'].min()
                max_date = df['created_at'].max()
            else:
                min_date = datetime.utcnow()
                max_date = datetime.utcnow()

            # Calculate data ranges
            data_range = {}
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
            for col in numeric_columns:
                if col in df.columns and not df[col].empty():
                    data_range[col] = (float(df[col].min()), float(df[col].max()))

            # Calculate summary statistics
            summary_stats = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "missing_values": df.isnull().sum().sum()
            }

            return DatasetStatistics(
                dataset_name=data_type.value,
                record_count=len(df),
                feature_count=len(df.columns),
                time_range=(min_date, max_date),
                quality_level=DataQualityStatus.GOOD,  # Default assumption
                completeness_score=self._calculate_completeness_score(df),
                data_range=data_range,
                correlation_matrix={},
                summary_stats=summary_stats
            )

        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return self._create_empty_statistics()

    def _calculate_data_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score"""
        try:
            if df.empty:
                return 0.0

            # Factors affecting quality
            completeness_score = self._calculate_completeness_score(df)

            # Calculate duplicate rows
            duplicate_ratio = df.duplicated().sum() / len(df) if len(df) > 0 else 0
            duplicate_score = max(0, 1 - duplicate_ratio)

            # Calculate outlier ratio (simplified)
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
            outlier_count = 0
            total_numeric_values = 0

            for col in numeric_columns:
                if col in df.columns:
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    outliers = ((df[col] < (q1 - 1.5 * iqr)) | (df[col] > (q3 + 1.5 * iqr))).sum()
                    total_numeric_values += len(df[col].dropna())

            outlier_score = 1 - (outlier_count / total_numeric_values) if total_numeric_values > 0 else 1

            # Calculate missing data ratio
            missing_ratio = df.isnull().sum().sum() / (df.size * len(df.columns))
            missing_score = 1 - missing_ratio

            # Combine scores with weights
            quality_score = (
                completeness_score * 0.4 +
                duplicate_score * 0.3 +
                outlier_score * 0.2 +
                missing_score * 0.1
            )

            return quality_score

        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0.0

    def _calculate_completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        try:
            if df.empty:
                return 0.0

            total_cells = df.size * len(df.columns)
            missing_cells = df.isnull().sum().sum()

            completeness_score = 1.0 - (missing_cells / total_cells)
            return completeness_score

        except Exception as e:
            logger.error(f"Error calculating completeness score: {str(e)}")
            return 0.0

    def _create_empty_statistics(self) -> DatasetStatistics:
        """Create empty statistics object"""
        return DatasetStatistics(
            dataset_name="empty",
            record_count=0,
            feature_count=0,
            time_range=(datetime.utcnow(), datetime.utcnow()),
            quality_level=DataQualityLevel.INSUFFICIENT,
            completeness_score=0.0,
            data_range={},
            correlation_matrix={},
            summary_stats={}
        )

    async def get_feature_importance(
        self,
        feature_name: str
    ) -> float:
        """Get importance weight for a feature"""
        for feature_def in self.feature_definitions:
            if feature_def.name == feature_name:
                return feature_def.importance_weight
        return 1.0  # Default weight

    async def validate_dataset(
        self,
        dataset: pd.DataFrame,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate dataset against provided rules"""
        try:
            if dataset.empty:
                    return {
                        "valid": False,
                        "issues": ["Dataset is empty"],
                        "quality_score": 0.0
                    }

            issues = []

            # Validate record count
            min_records = validation_rules.get("min_records", 100) if validation_rules else 100
            if len(dataset) < min_records:
                issues.append(f"Insufficient records: {len(dataset)} < {min_records}")

            # Validate feature completeness
            completeness_score = self._calculate_completeness_score(dataset)
            min_completeness = validation_rules.get("min_completeness", 0.9) if validation_rules else 0.9
            if completeness_score < min_completeness:
                issues.append(f"Low completeness: {completeness_score:.3f} < {min_completeness}")

            # Validate data types
            for col in dataset.columns:
                if col not in ['id', 'user_id', 'assessment_id', 'team_id', 'item_id']:
                    if dataset[col].dtype not in ['int64', 'float64', 'object', 'bool']:
                        issues.append(f"Invalid data type for column: {col}")

            # Validate ranges
            for feature_def in self.feature_definitions:
                if feature_def.name in dataset.columns:
                    validation_rules = feature_def.validation_rules
                    min_val = validation_rules.get("min")
                    max_val = validation_rules.get("max")

                    if min_val is not None:
                        if dataset[feature_def.name].min() < min_val:
                            issues.append(f"{feature_def.name} below minimum: {min_val}")
                    if max_val is not None:
                        if dataset[feature_def.name].max() > max_val:
                            issues.append(f"{feature_def.name} above maximum: {max_val}")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "quality_score": self._calculate_data_quality_score(dataset)
            }

        except Exception as e:
            logger.error(f"Error validating dataset: {str(e)}")
            return {"valid": False, "issues": [str(e)]}

    async def export_dataset(
        self,
        dataset: pd.DataFrame,
        export_format: str = "json",
        filename: Optional[str] = None
    ) -> str:
        """Export dataset to specified format"""
        try:
            if export_format == "json":
                json_data = dataset.to_dict('records')
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

                if filename:
                    with open(filename, 'w') as f:
                        f.write(json_str)

                return json_str
            else:
                raise ValueError(f"Unsupported export format: {export_format}")

        except Exception as e:
            logger.error(f"Error exporting dataset: {str(e)}")
            return ""

    async def create_feature_importance_report(
        self,
        dataset: pd.DataFrame,
        target_variable: Optional[str] = None,
        feature_correlation_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """Create report on feature importance and correlation"""
        try:
            if dataset.empty:
                return {"error": "Empty dataset"}

            # Calculate correlation matrix for numeric features
            numeric_features = dataset.select_dtypes(include=['int64', 'float64']).columns
            correlation_matrix = dataset[numeric_features].corr()

            # Calculate feature importance based on correlation with target
            importance_scores = {}

            if target_variable and target_variable in correlation_matrix.columns:
                correlations = correlation_matrix[target_variable].abs()
                for feature, correlation in correlations.items():
                    importance_scores[feature] = correlation

            # Apply feature definitions importance weights
            weighted_scores = {}
            for feature_def in self.feature_definitions:
                if feature_def.name in importance_scores:
                    weight = feature_def.importance_weight
                    correlation = importance_scores.get(feature_def.name, 0)
                    weighted_scores[feature_def.name] = correlation * weight

            # Sort features by importance
            sorted_features = sorted(
                sorted_features.items(),
                key=lambda x: x[1],
                reverse=True
            )

            return {
                "feature_correlation": correlation_matrix.to_dict(),
                "target_correlations": importance_scores,
                "weighted_importance": weighted_scores,
                "top_features": sorted_features[:20],
                "feature_categories": self._categorize_features(sorted_features),
                "quality_score": self._calculate_data_quality_score(dataset)
            }

        except Exception as e:
            logger.error(f"Error creating feature report: {str(e)}")
            return {"error": str(e)}

    def _categorize_features(self, sorted_features: List[Tuple[str, float]]) -> Dict[str, List[str]]:
        """Categorize features by type and importance level"""
        categories = {
            "high_importance": [],
            "medium_importance": [],
            "low_importance": []
        }

        for feature, score in sorted_features:
            if score >= 0.7:
                categories["high_importance"].append(feature)
            elif score >= 0.3:
                categories["medium_importance"].append(feature)
            else:
                categories["low_importance"].append(feature)

        return categories

    async def get_data_collection_summary(
        self,
        db: Session,
        time_period: int = 30  # days
    ) -> Dict[str, Any]:
        """Get summary of data collection activity"""
        try:
            # Get counts for different data types
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period)

            assessment_count = db.query(Assessment).filter(
                Assessment.created_at >= start_date
            ).count()

            response_count = db.query(Response).filter(
                Response.created_at >= start_date
            ).count()

            user_count = db.query(User).filter(
                User.created_at >= start_date
            ).count()

            team_count = db.query(Team).count()

            return {
                "time_period_days": time_period,
                "assessment_count": assessment_count,
                "response_count": response_count,
                "user_count": user_count,
                "team_count": team_count,
                "data_types": [
                    "assessment_responses",
                    "user_demographics",
                    "team_performance",
                    "item_analytics",
                    "text_analytics"
                ],
                "collection_date": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting collection summary: {str(e)}")
            return {}

    def export_feature_definitions(self) -> List[Dict[str, Any]]:
        """Export feature definitions for documentation"""
        return [feature_def.to_dict() for feature_def in self.feature_definitions]

    def get_model_status(self) -> Dict[str, Any]:
        """Get model service status"""
        return {
            "service": "Prediction Data Collection Service",
            "initialized": True,
            "feature_count": len(self.feature_definitions),
            "config": self.config,
            "available_data_types": [dt.value for dt in DataType]
        }

    async def collect_team_prediction_data(self,
                                          db: Session,
                                          team_id: int) -> Dict[str, Any]:
        """
        Collect team-specific data for prediction.

        Args:
            db: Database session
            team_id: Team ID to collect data for

        Returns:
            Dictionary with prediction features and metadata
        """
        try:
            # Get team information
            team = db.query(Team).filter(Team.id == team_id).first()
            if not team:
                return {"success": False, "error": f"Team {team_id} not found"}

            # Get team members
            team_members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
            user_ids = [member.user_id for member in team_members]

            if not user_ids:
                return {"success": False, "error": f"No members found for team {team_id}"}

            # Collect team performance data
            performance_data = await self.collect_team_performance_data(
                db, team_ids=[team_id]
            )

            # Collect assessment response data for team members
            assessment_data = await self.collect_assessment_data(
                db, user_ids=user_ids
            )

            # Extract features for prediction
            features = {}

            # Team performance features
            if performance_data["success"]:
                team_df = performance_data["data"]
                if not team_df.empty:
                    team_row = team_df.iloc[0] if len(team_df) == 1 else team_df.mean()
                    for col in team_df.columns:
                        if col != "team_id":
                            features[f"team_{col}"] = team_row.get(col, 0.0)

            # Assessment response features
            if assessment_data["success"]:
                response_df = assessment_data["data"]
                if not response_df.empty:
                    # Aggregate by user and then compute team-level features
                    user_features = response_df.groupby('user_id').agg({
                        'response_score': ['mean', 'std', 'min', 'max'],
                        'IRT_ability': ['mean', 'std'],
                        'IRT_se': ['mean'],
                        'difficulty_match_score': ['mean'],
                        'discrimination_score': ['mean'],
                        'point_biserial': ['mean']
                    }).fillna(0)

                    # Flatten column names
                    user_features.columns = [f"user_{col[0]}_{col[1]}" for col in user_features.columns]

                    # Aggregate to team level
                    team_assessment_features = user_features.mean()
                    for feature_name, value in team_assessment_features.items():
                        features[feature_name] = value

                    # Add team size
                    features["team_size"] = len(user_ids)
                    features["team_assessment_variability"] = user_features.std().mean()

            # Add team-level demographic features
            team_demo_data = await self.collect_demographics_data(
                db, user_ids=user_ids
            )

            if team_demo_data["success"]:
                demo_df = team_demo_data["data"]
                if not demo_df.empty:
                    # Calculate demographic diversity metrics
                    for col in demo_df.columns:
                        if col != "user_id" and demo_df[col].dtype in ['object', 'category']:
                            # Diversity as proportion of unique categories
                            diversity = len(demo_df[col].unique()) / len(demo_df)
                            features[f"demo_{col}_diversity"] = diversity

            return {
                "success": True,
                "team_id": team_id,
                "features": features,
                "feature_count": len(features),
                "data_collection_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error collecting team prediction data for team {team_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def collect_training_data(self,
                                  db: Session,
                                  include_assessment_responses: bool = True,
                                  include_team_performance: bool = True,
                                  include_demographics: bool = False,
                                  include_response_patterns: bool = True,
                                  team_ids: Optional[List[int]] = None,
                                  user_ids: Optional[List[str]] = None,
                                  min_data_quality: float = 0.5,
                                  date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Collect comprehensive training data for ML models.

        Args:
            db: Database session
            include_assessment_responses: Include assessment response features
            include_team_performance: Include team performance data
            include_demographics: Include demographic features
            include_response_patterns: Include response pattern analytics
            team_ids: Specific teams to include
            user_ids: Specific users to include
            min_data_quality: Minimum data quality score
            date_range: Date range for data collection

        Returns:
            Dictionary with collected training data and metadata
        """
        try:
            all_dataframes = []

            # Collect assessment response data
            if include_assessment_responses:
                assessment_data = await self.collect_assessment_data(
                    db=db,
                    team_ids=team_ids,
                    user_ids=user_ids,
                    date_range=date_range
                )
                if assessment_data["success"]:
                    df_assessment = assessment_data["data"]
                    if not df_assessment.empty:
                        all_dataframes.append(df_assessment)

            # Collect team performance data
            if include_team_performance:
                performance_data = await self.collect_team_performance_data(
                    db=db,
                    team_ids=team_ids
                )
                if performance_data["success"]:
                    df_performance = performance_data["data"]
                    if not df_performance.empty:
                        all_dataframes.append(df_performance)

            # Collect demographics data
            if include_demographics:
                demographics_data = await self.collect_demographics_data(
                    db=db,
                    user_ids=user_ids
                )
                if demographics_data["success"]:
                    df_demographics = demographics_data["data"]
                    if not df_demographics.empty:
                        all_dataframes.append(df_demographics)

            # Collect response pattern data
            if include_response_patterns:
                patterns_data = await self.collect_response_patterns(
                    db=db,
                    team_ids=team_ids,
                    user_ids=user_ids,
                    date_range=date_range
                )
                if patterns_data["success"]:
                    df_patterns = patterns_data["data"]
                    if not df_patterns.empty:
                        all_dataframes.append(df_patterns)

            # Merge all dataframes
            if not all_dataframes:
                return {
                    "success": False,
                    "error": "No data collected for training"
                }

            # Start with the first dataframe
            merged_df = all_dataframes[0]

            # Merge with remaining dataframes
            for df in all_dataframes[1:]:
                # Try different merge strategies
                if 'user_id' in merged_df.columns and 'user_id' in df.columns:
                    merged_df = pd.merge(merged_df, df, on='user_id', how='outer')
                elif 'team_id' in merged_df.columns and 'team_id' in df.columns:
                    merged_df = pd.merge(merged_df, df, on='team_id', how='outer')
                else:
                    # Concatenate if no common keys
                    merged_df = pd.concat([merged_df, df], axis=1)

            # Remove rows with too many missing values
            threshold = int(len(merged_df.columns) * (1 - min_data_quality))
            merged_df = merged_df.dropna(thresh=threshold)

            # Fill remaining missing values
            numeric_columns = merged_df.select_dtypes(include=[np.number]).columns
            merged_df[numeric_columns] = merged_df[numeric_columns].fillna(0)

            categorical_columns = merged_df.select_dtypes(include=['object', 'category']).columns
            merged_df[categorical_columns] = merged_df[categorical_columns].fillna('unknown')

            return {
                "success": True,
                "data": merged_df,
                "rows": len(merged_df),
                "columns": len(merged_df.columns),
                "data_sources": [
                    source for source, included in [
                        ("assessment_responses", include_assessment_responses),
                        ("team_performance", include_team_performance),
                        ("demographics", include_demographics),
                        ("response_patterns", include_response_patterns)
                    ] if included
                ],
                "collection_time": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error collecting training data: {str(e)}")
            return {"success": False, "error": str(e)}


# Export the main service class
__all__ = [
    "PredictionDataCollectionService",
    "DatasetStatistics",
    "FeatureDefinition",
    "DataType",
    "DataQualityLevel",
    "ModelStatus"
]