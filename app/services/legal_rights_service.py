"""
Legal Rights Awareness Service
Provides employees with comprehensive knowledge about their legal rights and protections
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.logging_config import logger
from app.db.models.legal_rights import (
    ContractViolation,
    EmployeeRightsResource,
    LaborLaw,
    LegalAidResource,
    RightsCategory,
    RightsKnowledgeCheck,
    ViolationSeverity,
)
from app.db.models.organization import Organization
from app.db.models.user import User

logger = logging.getLogger(__name__)


class LegalRightsService:
    """
    Comprehensive service for employee legal rights awareness
    """

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # LABOR LAW INFORMATION
    # ============================================

    async def get_labor_laws_by_country(
        self,
        country_code: str,
        category: Optional[str] = None,
        state_region: Optional[str] = None,
    ) -> List[LaborLaw]:
        """
        Get labor laws for a specific country

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            category: Optional category filter
            state_region: Optional state/region filter for federal countries

        Returns:
            List of labor laws
        """
        try:
            query = self.db.query(LaborLaw).filter(
                LaborLaw.country_code == country_code.upper(),
                LaborLaw.is_active == True,
            )

            if category:
                query = query.filter(LaborLaw.category == category)

            if state_region:
                query = query.filter(
                    or_(
                        LaborLaw.state_region == state_region,
                        LaborLaw.state_region.is_(None),
                    )
                )

            laws = query.order_by(LaborLaw.category, LaborLaw.law_name).all()
            logger.info(f"Retrieved {len(laws)} labor laws for country {country_code}")
            return laws

        except Exception as e:
            logger.error(f"Error retrieving labor laws: {e}")
            raise

    async def get_rights_summary(
        self, country_code: str, state_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a comprehensive summary of employee rights for a country

        Args:
            country_code: ISO country code
            state_region: Optional state/region

        Returns:
            Summary of rights by category
        """
        try:
            laws = await self.get_labor_laws_by_country(
                country_code, state_region=state_region
            )

            # ✅ FIX: Proper empty check (prevent IndexError on empty list)
            summary = {
                "country_code": country_code,
                "country_name": (
                    laws[0].country_name if laws and len(laws) > 0 else country_code
                ),
                "total_laws": len(laws),
                "categories": {},
                "key_protections": {
                    "min_wage": None,
                    "max_weekly_hours": None,
                    "overtime_threshold": None,
                    "min_vacation_days": None,
                },
                "protection_levels": {
                    "discrimination": 0,
                    "safety": 0,
                    "privacy": 0,
                    "termination": 0,
                },
            }

            for law in laws:
                if law.category not in summary["categories"]:
                    summary["categories"][law.category] = []

                summary["categories"][law.category].append(
                    {
                        "law_name": law.law_name,
                        "description": law.description,
                        "law_code": law.law_code,
                    }
                )

                # Extract key protections
                if law.min_wage:
                    summary["key_protections"]["min_wage"] = max(
                        summary["key_protections"]["min_wage"] or 0, law.min_wage
                    )
                if law.max_weekly_hours:
                    summary["key_protections"]["max_weekly_hours"] = min(
                        summary["key_protections"]["max_weekly_hours"] or float("inf"),
                        law.max_weekly_hours,
                    )
                if law.min_vacation_days:
                    summary["key_protections"]["min_vacation_days"] = max(
                        summary["key_protections"]["min_vacation_days"] or 0,
                        law.min_vacation_days,
                    )

                # Average protection levels
                if law.discrimination_protection_level:
                    summary["protection_levels"][
                        "discrimination"
                    ] += law.discrimination_protection_level
                if law.safety_protection_level:
                    summary["protection_levels"][
                        "safety"
                    ] += law.safety_protection_level
                if law.privacy_protection_level:
                    summary["protection_levels"][
                        "privacy"
                    ] += law.privacy_protection_level
                if law.termination_protection_level:
                    summary["protection_levels"][
                        "termination"
                    ] += law.termination_protection_level

            # Calculate average protection levels
            for protection_type in summary["protection_levels"]:
                if summary["protection_levels"][protection_type] > 0:
                    summary["protection_levels"][protection_type] = round(
                        summary["protection_levels"][protection_type] / len(laws), 1
                    )

            return summary

        except Exception as e:
            logger.error(f"Error generating rights summary: {e}")
            raise

    # ============================================
    # EMPLOYEE RIGHTS RESOURCES
    # ============================================

    async def get_rights_resources(
        self,
        organization_id: UUID,
        category: Optional[str] = None,
        resource_type: Optional[str] = None,
        featured_only: bool = False,
        limit: int = 50,
    ) -> List[EmployeeRightsResource]:
        """
        Get educational resources about employee rights

        Args:
            organization_id: Organization UUID
            category: Optional category filter
            resource_type: Optional type filter
            featured_only: Only return featured resources
            limit: Maximum number of results

        Returns:
            List of resources
        """
        try:
            query = self.db.query(EmployeeRightsResource).filter(
                EmployeeRightsResource.organization_id == organization_id,
                EmployeeRightsResource.is_published == True,
            )

            if category:
                query = query.filter(EmployeeRightsResource.category == category)

            if resource_type:
                query = query.filter(
                    EmployeeRightsResource.resource_type == resource_type
                )

            if featured_only:
                query = query.filter(EmployeeRightsResource.is_featured == True)

            resources = (
                query.order_by(
                    EmployeeRightsResource.display_order,
                    desc(EmployeeRightsResource.view_count),
                )
                .limit(limit)
                .all()
            )

            # Increment view counts
            for resource in resources:
                resource.view_count += 1
            self.db.commit()

            return resources

        except Exception as e:
            logger.error(f"Error retrieving rights resources: {e}")
            raise

    async def mark_resource_helpful(self, resource_id: UUID, helpful: bool) -> bool:
        """
        Mark a resource as helpful or not helpful

        Args:
            resource_id: Resource UUID
            helpful: True if helpful, False if not

        Returns:
            Success status
        """
        try:
            resource = (
                self.db.query(EmployeeRightsResource)
                .filter(EmployeeRightsResource.id == resource_id)
                .first()
            )

            if not resource:
                return False

            if helpful:
                resource.helpful_count += 1
            else:
                resource.not_helpful_count += 1

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Error marking resource helpfulness: {e}")
            self.db.rollback()
            return False

    # ============================================
    # CONTRACT VIOLATION DETECTION
    # ============================================

    async def detect_contract_violations(
        self, organization_id: UUID, employee_id: Optional[UUID] = None
    ) -> List[ContractViolation]:
        """
        Automatically detect potential contract violations

        This is a simplified version. In production, this would analyze:
        - Timesheet data vs labor laws
        - Pay records vs minimum wage
        - Overtime calculations
        - Break compliance
        - Termination procedures

        Args:
            organization_id: Organization UUID
            employee_id: Optional specific employee to check

        Returns:
            List of detected violations
        """
        try:
            violations = []

            # This would integrate with your existing monitoring services
            # For now, returning empty list as placeholder
            # In production, analyze:
            # - Wellness data for working hours violations
            # - Payroll data for wage violations
            # - Communication analysis for harassment patterns
            # - Time tracking for break violations

            logger.info(f"Violation detection check for org {organization_id}")
            return violations

        except Exception as e:
            logger.error(f"Error detecting contract violations: {e}")
            raise

    async def create_violation_report(
        self, organization_id: UUID, violation_data: Dict[str, Any], reported_by: UUID
    ) -> ContractViolation:
        """
        Create a new contract violation report

        Args:
            organization_id: Organization UUID
            violation_data: Violation details
            reported_by: User UUID reporting the violation

        Returns:
            Created violation record
        """
        try:
            violation = ContractViolation(
                organization_id=organization_id,
                affected_employee_id=violation_data.get("affected_employee_id"),
                violation_type=violation_data["violation_type"],
                category=violation_data["category"],
                severity=violation_data["severity"],
                title=violation_data["title"],
                description=violation_data["description"],
                labor_law_violated=violation_data.get("labor_law_violated"),
                law_reference=violation_data.get("law_reference"),
                detection_method="manual_report",
                detected_by=reported_by,
                incident_date_range=violation_data.get("incident_date_range"),
                evidence_urls=violation_data.get("evidence_urls"),
            )

            self.db.add(violation)
            self.db.commit()
            self.db.refresh(violation)

            logger.info(f"Created violation report: {violation.id}")
            return violation

        except Exception as e:
            logger.error(f"Error creating violation report: {e}")
            self.db.rollback()
            raise

    async def get_violations(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[ContractViolation]:
        """
        Get contract violations for an organization

        Args:
            organization_id: Organization UUID
            status: Optional status filter
            severity: Optional severity filter
            limit: Maximum number of results

        Returns:
            List of violations
        """
        try:
            query = self.db.query(ContractViolation).filter(
                ContractViolation.organization_id == organization_id
            )

            if status:
                query = query.filter(ContractViolation.status == status)

            if severity:
                query = query.filter(ContractViolation.severity == severity)

            violations = (
                query.order_by(desc(ContractViolation.detected_at)).limit(limit).all()
            )

            return violations

        except Exception as e:
            logger.error(f"Error retrieving violations: {e}")
            raise

    # ============================================
    # KNOWLEDGE CHECKS
    # ============================================

    async def create_knowledge_check(
        self,
        user_id: UUID,
        organization_id: UUID,
        check_type: str,
        responses: List[Dict[str, Any]],
    ) -> RightsKnowledgeCheck:
        """
        Create and score a rights knowledge check

        Args:
            user_id: User UUID
            organization_id: Organization UUID
            check_type: Type of knowledge check
            responses: User's responses

        Returns:
            Created knowledge check with score
        """
        try:
            # Get questions and correct answers for this check type
            questions_data = await self._get_knowledge_check_questions(check_type)

            # Calculate score
            correct_count = 0
            knowledge_gaps = []

            for i, response in enumerate(responses):
                question = questions_data["questions"][i]
                is_correct = response.get("answer") == question["correct_answer"]

                if is_correct:
                    correct_count += 1
                else:
                    knowledge_gaps.append(question["topic"])

            score_percentage = int((correct_count / len(responses)) * 100)
            passed = score_percentage >= questions_data.get("passing_threshold", 70)

            knowledge_check = RightsKnowledgeCheck(
                user_id=user_id,
                organization_id=organization_id,
                check_type=check_type,
                category=questions_data["category"],
                questions=questions_data["questions"],
                responses=responses,
                correct_answers=questions_data["questions"],
                score_percentage=score_percentage,
                passed=passed,
                knowledge_gaps=list(set(knowledge_gaps)),
                recommended_resources=questions_data.get("recommended_resources", []),
            )

            self.db.add(knowledge_check)
            self.db.commit()
            self.db.refresh(knowledge_check)

            logger.info(
                f"Created knowledge check for user {user_id}: score {score_percentage}%"
            )
            return knowledge_check

        except Exception as e:
            logger.error(f"Error creating knowledge check: {e}")
            self.db.rollback()
            raise

    async def _get_knowledge_check_questions(self, check_type: str) -> Dict[str, Any]:
        """
        Get questions for a knowledge check type

        In production, this would pull from a database of questions
        For now, providing sample questions
        """
        questions = {
            "general": {
                "category": "general",
                "passing_threshold": 70,
                "questions": [
                    {
                        "question": "What is the minimum wage in your country?",
                        "options": [
                            "Varies by region",
                            "Federal minimum",
                            "No minimum wage",
                            "Set by employer",
                        ],
                        "correct_answer": "Varies by region",
                        "topic": "wages",
                    },
                    {
                        "question": "How many hours can you be required to work before overtime pay?",
                        "options": [
                            "35 hours",
                            "40 hours",
                            "48 hours",
                            "No overtime required",
                        ],
                        "correct_answer": "40 hours",
                        "topic": "working_hours",
                    },
                    {
                        "question": "Are you protected from workplace discrimination?",
                        "options": [
                            "Yes, by law",
                            "Only in large companies",
                            "No protection",
                            "Depends on state",
                        ],
                        "correct_answer": "Yes, by law",
                        "topic": "discrimination",
                    },
                    {
                        "question": "Can you be fired for reporting safety violations?",
                        "options": [
                            "Yes, at-will employment",
                            "No, protected by whistleblower laws",
                            "Only with warning",
                            "Depends on tenure",
                        ],
                        "correct_answer": "No, protected by whistleblower laws",
                        "topic": "safety",
                    },
                    {
                        "question": "Are you entitled to breaks during your work shift?",
                        "options": [
                            "No legal requirement",
                            "Yes, meal and rest breaks",
                            "Only meal breaks",
                            "Depends on employer",
                        ],
                        "correct_answer": "Yes, meal and rest breaks",
                        "topic": "breaks",
                    },
                ],
                "recommended_resources": ["resource-uuid-1", "resource-uuid-2"],
            }
        }

        return questions.get(check_type, questions["general"])

    async def get_user_knowledge_history(
        self, user_id: UUID, limit: int = 20
    ) -> List[RightsKnowledgeCheck]:
        """
        Get a user's knowledge check history

        Args:
            user_id: User UUID
            limit: Maximum number of results

        Returns:
            List of knowledge checks
        """
        try:
            checks = (
                self.db.query(RightsKnowledgeCheck)
                .filter(RightsKnowledgeCheck.user_id == user_id)
                .order_by(desc(RightsKnowledgeCheck.completed_at))
                .limit(limit)
                .all()
            )

            return checks

        except Exception as e:
            logger.error(f"Error retrieving knowledge history: {e}")
            raise

    # ============================================
    # LEGAL AID RESOURCES
    # ============================================

    async def find_legal_aid(
        self,
        country_code: str,
        state_region: Optional[str] = None,
        city: Optional[str] = None,
        specialization: Optional[str] = None,
        free_only: bool = False,
    ) -> List[LegalAidResource]:
        """
        Find legal aid resources

        Args:
            country_code: ISO country code
            state_region: Optional state/region
            city: Optional city
            specialization: Optional area of specialization
            free_only: Only return free/pro bono resources

        Returns:
            List of legal aid resources
        """
        try:
            query = self.db.query(LegalAidResource).filter(
                LegalAidResource.country_code == country_code.upper(),
                LegalAidResource.verified == True,
            )

            if state_region:
                query = query.filter(LegalAidResource.state_region == state_region)

            if city:
                query = query.filter(LegalAidResource.city == city)

            if free_only:
                query = query.filter(
                    or_(
                        LegalAidResource.free_consultation == True,
                        LegalAidResource.pro_bono == True,
                    )
                )

            resources = query.order_by(
                desc(LegalAidResource.rating), LegalAidResource.response_time_hours
            ).all()

            # Filter by specialization if provided (JSONB field)
            if specialization:
                resources = [
                    r
                    for r in resources
                    if r.specializations and specialization in r.specializations
                ]

            logger.info(f"Found {len(resources)} legal aid resources")
            return resources

        except Exception as e:
            logger.error(f"Error finding legal aid: {e}")
            raise


class LegalRightsAnalyzer:
    """
    Advanced analysis for legal rights compliance and risk assessment
    """

    def __init__(self, db: Session):
        self.db = db

    async def analyze_organization_compliance(
        self, organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze organization's compliance with labor laws

        Returns comprehensive compliance report with risk scores
        """
        try:
            # Get all open violations
            violations = (
                self.db.query(ContractViolation)
                .filter(
                    ContractViolation.organization_id == organization_id,
                    ContractViolation.status.in_(["open", "investigating"]),
                )
                .all()
            )

            # Calculate risk scores
            critical_count = len(
                [
                    v
                    for v in violations
                    if v.severity == ViolationSeverity.CRITICAL.value
                ]
            )
            high_count = len(
                [v for v in violations if v.severity == ViolationSeverity.HIGH.value]
            )

            legal_risk_score = min(100, (critical_count * 25) + (high_count * 10))

            # Categorize violations
            violations_by_category = {}
            for violation in violations:
                if violation.category not in violations_by_category:
                    violations_by_category[violation.category] = []
                violations_by_category[violation.category].append(
                    {
                        "id": str(violation.id),
                        "title": violation.title,
                        "severity": violation.severity,
                        "detected_at": violation.detected_at.isoformat(),
                    }
                )

            return {
                "organization_id": str(organization_id),
                "legal_risk_score": legal_risk_score,
                "total_open_violations": len(violations),
                "critical_violations": critical_count,
                "high_severity_violations": high_count,
                "violations_by_category": violations_by_category,
                "compliance_percentage": max(0, 100 - legal_risk_score),
                "recommendations": await self._generate_compliance_recommendations(
                    violations
                ),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error analyzing compliance: {e}")
            raise

    async def _generate_compliance_recommendations(
        self, violations: List[ContractViolation]
    ) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []

        critical_violations = [
            v for v in violations if v.severity == ViolationSeverity.CRITICAL.value
        ]
        if critical_violations:
            recommendations.append(
                "URGENT: Address critical violations immediately to avoid legal action"
            )

        if any(v.category == "working_hours" for v in violations):
            recommendations.append(
                "Review and adjust working hour tracking and overtime calculation procedures"
            )

        if any(v.category == "safety_health" for v in violations):
            recommendations.append(
                "Conduct comprehensive safety audit and implement enhanced safety protocols"
            )

        if any(v.category == "discrimination_protection" for v in violations):
            recommendations.append(
                "Schedule anti-discrimination training for all managers and HR staff"
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring compliance, no immediate actions required"
            )

        return recommendations
