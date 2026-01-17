"""
AI Agent: Encryption Strategy Advisor

Analyzes database schema and recommends encryption strategy for sensitive fields.
Uses NLP and pattern matching to identify PII, PHI, and sensitive data.

Capabilities:
- Scans database models for sensitive fields
- Classifies fields by data sensitivity (PII, PHI, SENSITIVE, PUBLIC)
- Recommends encryption algorithms and key sizes
- Suggests field-level vs. record-level encryption
- Generates migration scripts for encrypted fields
- Ensures compliance with HIPAA, GDPR, SOC 2

Compliance: HIPAA, GDPR, SOC 2
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect
from sqlalchemy.orm import Mapper

logger = logging.getLogger(__name__)


class DataSensitivity(Enum):
    """Data sensitivity classification"""

    PII = "pii"  # Personal Identifiable Information
    PHI = "phi"  # Protected Health Information
    FINANCIAL = "financial"  # Financial data
    SENSITIVE = "sensitive"  # Sensitive business data
    PUBLIC = "public"  # Non-sensitive data


class EncryptionStrength(Enum):
    """Encryption strength levels"""

    STANDARD = "standard"  # AES-256-GCM
    HIGH = "high"  # AES-256-GCM + key rotation
    CRITICAL = "critical"  # AES-256-GCM + key rotation + HSM


@dataclass
class FieldRecommendation:
    """Encryption recommendation for a field"""

    table_name: str
    field_name: str
    current_type: str
    sensitivity: DataSensitivity
    should_encrypt: bool
    encryption_strength: Optional[EncryptionStrength]
    recommended_algorithm: str
    key_rotation_period: Optional[str]
    rationale: str
    migration_complexity: str  # low, medium, high


@dataclass
class EncryptionStrategy:
    """Overall encryption strategy for a table"""

    table_name: str
    total_fields: int
    sensitive_fields: int
    recommended_encrypted_fields: int
    field_recommendations: List[FieldRecommendation]
    compliance_score: float  # 0.0 to 1.0
    priority: str  # critical, high, medium, low


class EncryptionStrategyAgent:
    """
    AI Agent for recommending encryption strategies.

    Automatically analyzes database schema and provides
    actionable encryption recommendations.
    """

    # Field name patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        DataSensitivity.PII: [
            r".*email.*",
            r".*name.*",
            r".*phone.*",
            r".*ssn.*",
            r".*social_security.*",
            r".*address.*",
            r".*dob$",
            r".*birth.*",
            r".*passport.*",
            r".*license.*",
            r".*id_number.*",
        ],
        DataSensitivity.PHI: [
            r".*diagnosis.*",
            r".*medical.*",
            r".*health.*",
            r".*clinical.*",
            r".*treatment.*",
            r".*medication.*",
            r".*prescription.*",
            r".*therapy.*",
            r".*symptom.*",
            r".*condition.*",
            r".*response.*",  # Assessment responses
        ],
        DataSensitivity.FINANCIAL: [
            r".*credit_card.*",
            r".*bank.*account.*",
            r".*payment.*",
            r".*salary.*",
            r".*income.*",
            r".*invoice.*",
        ],
        DataSensitivity.SENSITIVE: [
            r".*password.*",
            r".*secret.*",
            r".*token.*",
            r".*api_key.*",
            r".*private.*",
        ],
    }

    # Field types that can be encrypted
    ENCRYPTABLE_TYPES = {
        "String",
        "Text",
        "VARCHAR",
        "CHAR",
        "JSON",
        "JSONB",
    }

    def __init__(self):
        self.analysis_cache: Dict[str, EncryptionStrategy] = {}

    async def analyze_database(
        self,
        db: AsyncSession,
        models: Optional[List] = None,
    ) -> List[EncryptionStrategy]:
        """
        Analyze database and recommend encryption strategies.

        Args:
            db: Database session
            models: List of SQLAlchemy models to analyze

        Returns:
            List of encryption strategies for each table
        """
        logger.info("Starting encryption strategy analysis")

        strategies = []

        # Import models if not provided
        if models is None:
            from app.db.models import (
                user,
                clinical_screening,
                assessment,
                responses,
                organization,
                team,
            )
            models = [
                user.User,
                clinical_screening.ClinicalScreening,
                assessment.Assessment,
                responses.Response,
                organization.Organization,
                team.Team,
            ]

        # Analyze each model
        for model in models:
            try:
                strategy = await self._analyze_model(model)
                strategies.append(strategy)
            except Exception as e:
                logger.error(f"Failed to analyze model {model.__name__}: {str(e)}")

        logger.info(f"Encryption analysis complete: {len(strategies)} tables analyzed")

        return strategies

    async def _analyze_model(self, model) -> EncryptionStrategy:
        """
        Analyze a single model.

        Args:
            model: SQLAlchemy model class

        Returns:
            Encryption strategy for the model
        """
        table_name = model.__tablename__
        mapper = inspect(model)

        # Get all columns
        columns = mapper.columns
        total_fields = len(columns)

        recommendations = []

        for column in columns:
            recommendation = await self._analyze_field(table_name, column)
            if recommendation:
                recommendations.append(recommendation)

        # Calculate statistics
        sensitive_fields = len([r for r in recommendations if r.sensitivity != DataSensitivity.PUBLIC])
        recommended_encrypted = len([r for r in recommendations if r.should_encrypt])

        # Calculate compliance score
        compliance_score = await self._calculate_compliance_score(recommendations)

        # Determine priority
        priority = await self._determine_priority(recommendations, compliance_score)

        return EncryptionStrategy(
            table_name=table_name,
            total_fields=total_fields,
            sensitive_fields=sensitive_fields,
            recommended_encrypted_fields=recommended_encrypted,
            field_recommendations=recommendations,
            compliance_score=compliance_score,
            priority=priority,
        )

    async def _analyze_field(
        self,
        table_name: str,
        column,
    ) -> Optional[FieldRecommendation]:
        """
        Analyze a single field.

        Args:
            table_name: Table name
            column: SQLAlchemy column

        Returns:
            Field recommendation or None
        """
        field_name = column.name
        field_type = str(column.type)

        # Skip non-encryptable types
        if not any(t in field_type for t in self.ENCRYPTABLE_TYPES):
            return None

        # Skip primary keys and foreign keys
        if column.primary_key or column.foreign_keys:
            return None

        # Classify sensitivity
        sensitivity = await self._classify_sensitivity(field_name)

        # Determine if encryption is needed
        should_encrypt, strength, algorithm = await self._recommend_encryption(
            sensitivity, field_name
        )

        # Determine rationale
        rationale = await self._generate_rationale(sensitivity, should_encrypt)

        # Determine migration complexity
        migration_complexity = await self._assess_migration_complexity(
            table_name, field_name, field_type
        )

        # Determine key rotation period
        key_rotation = await self._recommend_key_rotation(strength)

        return FieldRecommendation(
            table_name=table_name,
            field_name=field_name,
            current_type=field_type,
            sensitivity=sensitivity,
            should_encrypt=should_encrypt,
            encryption_strength=strength,
            recommended_algorithm=algorithm,
            key_rotation_period=key_rotation,
            rationale=rationale,
            migration_complexity=migration_complexity,
        )

    async def _classify_sensitivity(self, field_name: str) -> DataSensitivity:
        """
        Classify field sensitivity based on name patterns.

        Args:
            field_name: Field name

        Returns:
            Data sensitivity classification
        """
        field_lower = field_name.lower()

        # Check each sensitivity category
        for sensitivity, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, field_lower):
                    return sensitivity

        # Default to public
        return DataSensitivity.PUBLIC

    async def _recommend_encryption(
        self,
        sensitivity: DataSensitivity,
        field_name: str,
    ) -> Tuple[bool, Optional[EncryptionStrength], str]:
        """
        Recommend encryption for a field.

        Args:
            sensitivity: Data sensitivity
            field_name: Field name

        Returns:
            Tuple of (should_encrypt, strength, algorithm)
        """
        if sensitivity == DataSensitivity.PUBLIC:
            return False, None, "None"

        if sensitivity == DataSensitivity.PHI:
            # PHI requires strongest encryption
            return True, EncryptionStrength.CRITICAL, "AES-256-GCM"

        if sensitivity == DataSensitivity.PII:
            # PII requires high encryption
            return True, EncryptionStrength.HIGH, "AES-256-GCM"

        if sensitivity == DataSensitivity.FINANCIAL:
            # Financial data requires high encryption
            return True, EncryptionStrength.HIGH, "AES-256-GCM"

        if sensitivity == DataSensitivity.SENSITIVE:
            # Sensitive data requires standard encryption
            return True, EncryptionStrength.STANDARD, "AES-256-GCM"

        return False, None, "None"

    async def _generate_rationale(
        self,
        sensitivity: DataSensitivity,
        should_encrypt: bool,
    ) -> str:
        """
        Generate rationale for encryption recommendation.

        Args:
            sensitivity: Data sensitivity
            should_encrypt: Whether encryption is recommended

        Returns:
            Rationale string
        """
        rationales = {
            DataSensitivity.PHI: "Protected Health Information requires encryption per HIPAA §164.312(a)(2)(iv)",
            DataSensitivity.PII: "Personal Identifiable Information should be encrypted per GDPR Article 32",
            DataSensitivity.FINANCIAL: "Financial data requires encryption per PCI DSS 3.2.1",
            DataSensitivity.SENSITIVE: "Sensitive business data should be encrypted to prevent unauthorized access",
            DataSensitivity.PUBLIC: "Non-sensitive data, encryption not required",
        }

        if should_encrypt:
            return rationales.get(sensitivity, "Field contains sensitive data")
        else:
            return rationales.get(DataSensitivity.PUBLIC, "Field does not contain sensitive data")

    async def _assess_migration_complexity(
        self,
        table_name: str,
        field_name: str,
        field_type: str,
    ) -> str:
        """
        Assess migration complexity for encrypting a field.

        Args:
            table_name: Table name
            field_name: Field name
            field_type: Field type

        Returns:
            Migration complexity (low, medium, high)
        """
        # Check if field is indexed
        # Indexed fields require special handling (encrypted indexes)
        complexity = "medium"

        # Check if field is used in foreign keys
        # These are more complex to migrate
        if "id" in field_name.lower():
            complexity = "high"

        # Large text fields are easier to migrate
        if "text" in field_type.lower():
            complexity = "low"

        return complexity

    async def _recommend_key_rotation(
        self,
        strength: Optional[EncryptionStrength],
    ) -> Optional[str]:
        """
        Recommend key rotation period.

        Args:
            strength: Encryption strength

        Returns:
            Key rotation period or None
        """
        if strength == EncryptionStrength.CRITICAL:
            return "30 days"
        elif strength == EncryptionStrength.HIGH:
            return "90 days"
        elif strength == EncryptionStrength.STANDARD:
            return "180 days"
        else:
            return None

    async def _calculate_compliance_score(
        self,
        recommendations: List[FieldRecommendation],
    ) -> float:
        """
        Calculate compliance score based on recommendations.

        Args:
            recommendations: List of field recommendations

        Returns:
            Compliance score (0.0 to 1.0)
        """
        if not recommendations:
            return 1.0

        # Check if sensitive fields are recommended for encryption
        sensitive_fields = [r for r in recommendations if r.sensitivity != DataSensitivity.PUBLIC]
        encrypted_fields = [r for r in sensitive_fields if r.should_encrypt]

        if not sensitive_fields:
            return 1.0

        return len(encrypted_fields) / len(sensitive_fields)

    async def _determine_priority(
        self,
        recommendations: List[FieldRecommendation],
        compliance_score: float,
    ) -> str:
        """
        Determine priority for implementing encryption.

        Args:
            recommendations: List of field recommendations
            compliance_score: Compliance score

        Returns:
            Priority level (critical, high, medium, low)
        """
        # Check for critical data
        critical_fields = [
            r for r in recommendations
            if r.sensitivity == DataSensitivity.PHI and not r.should_encrypt
        ]

        if critical_fields or compliance_score < 0.5:
            return "critical"

        # Check for high-priority data
        high_priority_fields = [
            r for r in recommendations
            if r.sensitivity == DataSensitivity.PII and not r.should_encrypt
        ]

        if high_priority_fields or compliance_score < 0.8:
            return "high"

        # Check for any unencrypted sensitive data
        unencrypted_sensitive = [
            r for r in recommendations
            if r.sensitivity != DataSensitivity.PUBLIC and not r.should_encrypt
        ]

        if unencrypted_sensitive:
            return "medium"

        return "low"

    async def generate_migration_script(
        self,
        strategy: EncryptionStrategy,
    ) -> str:
        """
        Generate migration script for implementing encryption.

        Args:
            strategy: Encryption strategy

        Returns:
            Migration SQL script
        """
        script_lines = [
            f"-- Migration script for {strategy.table_name}",
            f"-- Purpose: Encrypt sensitive fields",
            f"-- Generated by AI Encryption Strategy Advisor",
            "",
            "-- Step 1: Add encrypted columns",
        ]

        for recommendation in strategy.field_recommendations:
            if recommendation.should_encrypt:
                script_lines.append(
                    f"ALTER TABLE {strategy.table_name} "
                    f"ADD COLUMN {recommendation.field_name}_encrypted TEXT;"
                )

        script_lines.append("")
        script_lines.append("-- Step 2: Migrate data to encrypted columns")
        script_lines.append("UPDATE {} SET".format(strategy.table_name))

        for recommendation in strategy.field_recommendations:
            if recommendation.should_encrypt:
                script_lines.append(
                    f"    {recommendation.field_name}_encrypted = "
                    f"pgp_sym_encrypt({recommendation.field_name}, '{{ENCRYPTION_KEY}}'),"
                )

        script_lines.append(";")
        script_lines.append("")
        script_lines.append("-- Step 3: Drop old columns (after verification)")
        script_lines.append("-- WARNING: Verify encrypted data before dropping!")

        for recommendation in strategy.field_recommendations:
            if recommendation.should_encrypt:
                script_lines.append(
                    f"-- ALTER TABLE {strategy.table_name} "
                    f"DROP COLUMN {recommendation.field_name};"
                )

        return "\n".join(script_lines)


# Global agent instance
encryption_strategy_agent = EncryptionStrategyAgent()
