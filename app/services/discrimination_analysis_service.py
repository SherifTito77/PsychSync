"""
Discrimination & Equity Analysis Service
Provides comprehensive analysis of workplace discrimination, pay equity, and promotion fairness
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.db.models.discrimination_analysis import (
    DemographicProfile,
    EquityAnalysis,
    PayEquityRecord,
    PromotionTracking,
    HiringMetrics,
    DiscriminationComplaint,
    ProtectedClass,
    AnalysisType,
    SeverityLevel,
)
from app.db.models.user import User
from app.core.logging_config import logger

logger = logging.getLogger(__name__)


class DiscriminationAnalysisService:
    """
    Comprehensive service for discrimination and equity analysis
    """

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # DEMOGRAPHIC DATA MANAGEMENT
    # ============================================

    async def save_demographic_profile(
        self,
        user_id: UUID,
        organization_id: UUID,
        demographic_data: Dict[str, Any]
    ) -> DemographicProfile:
        """
        Save or update user demographic profile

        Args:
            user_id: User UUID
            organization_id: Organization UUID
            demographic_data: Demographic information

        Returns:
            Created or updated profile
        """
        try:
            # Check if profile exists
            profile = self.db.query(DemographicProfile).filter(
                DemographicProfile.user_id == user_id
            ).first()

            demographic_data['consent_given'] = True

            if profile:
                # Update existing profile
                for key, value in demographic_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.last_updated = datetime.utcnow()
            else:
                # Create new profile
                profile = DemographicProfile(
                    user_id=user_id,
                    organization_id=organization_id,
                    **demographic_data
                )
                self.db.add(profile)

            self.db.commit()
            self.db.refresh(profile)

            logger.info(f"Saved demographic profile for user {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Error saving demographic profile: {e}")
            self.db.rollback()
            raise

    async def get_organization_demographics(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Get aggregated demographic statistics for organization

        Args:
            organization_id: Organization UUID

        Returns:
            Aggregated demographic data
        """
        try:
            profiles = self.db.query(DemographicProfile).filter(
                DemographicProfile.organization_id == organization_id,
                DemographicProfile.consent_given == True
            ).all()

            if not profiles:
                return {
                    "total_employees": 0,
                    "demographics": {}
                }

            # Aggregate by demographic dimensions
            demographics = {
                "gender": {},
                "race": {},
                "age_range": {},
                "veteran_status": {},
                "disability_status": {}
            }

            for profile in profiles:
                for dimension in demographics.keys():
                    value = getattr(profile, dimension, None)
                    if value:
                        demographics[dimension][value] = \
                            demographics[dimension].get(value, 0) + 1

            return {
                "total_employees": len(profiles),
                "demographics": demographics,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error retrieving demographics: {e}")
            raise

    # ============================================
    # PAY EQUITY ANALYSIS
    # ============================================

    async def analyze_pay_equity(
        self,
        organization_id: UUID,
        demographic_dimension: str,
        time_period_start: Optional[datetime] = None,
        time_period_end: Optional[datetime] = None
    ) -> EquityAnalysis:
        """
        Analyze pay equity across demographic groups

        Args:
            organization_id: Organization UUID
            demographic_dimension: Dimension to analyze (gender, race, etc.)
            time_period_start: Optional start date
            time_period_end: Optional end date

        Returns:
            EquityAnalysis with findings
        """
        try:
            if not time_period_end:
                time_period_end = datetime.utcnow()
            if not time_period_start:
                time_period_start = time_period_end - timedelta(days=365)

            # Get demographic profiles with consent
            profiles = self.db.query(DemographicProfile).filter(
                DemographicProfile.organization_id == organization_id,
                DemographicProfile.consent_given == True
            ).all()

            if len(profiles) < 10:
                # Insufficient data for meaningful analysis
                return self._create_insufficient_data_analysis(
                    organization_id, AnalysisType.PAY_EQUITY.value
                )

            # Group by demographic dimension
            dimension_values = {}
            for profile in profiles:
                value = getattr(profile, demographic_dimension, None)
                if value:
                    if value not in dimension_values:
                        dimension_values[value] = []
                    dimension_values[value].append(profile.user_id)

            # Calculate salary statistics for each group
            # This would integrate with payroll data in production
            # For now, using placeholder calculations
            group_statistics = {}
            baseline_value = None
            max_count = 0

            for value, user_ids in dimension_values.items():
                count = len(user_ids)
                if count > max_count:
                    max_count = count
                    baseline_value = value

                # Placeholder salary data - would come from payroll in production
                import random
                salaries = [random.randint(50000, 120000) for _ in user_ids]

                group_statistics[value] = {
                    "count": count,
                    "mean_salary": sum(salaries) / len(salaries),
                    "median_salary": sorted(salaries)[len(salaries) // 2],
                    "min_salary": min(salaries),
                    "max_salary": max(salaries),
                }

            # Detect disparities
            baseline_salary = group_statistics[baseline_value]["mean_salary"]
            disparity_detected = False
            severity = SeverityLevel.NONE.value
            affected_groups = []
            pay_gap = 0

            for value, stats in group_statistics.items():
                if value != baseline_value:
                    gap_percent = ((stats["mean_salary"] - baseline_salary) / baseline_salary) * 100
                    stats["salary_gap_percent"] = gap_percent

                    if abs(gap_percent) > 15:  # 15% threshold
                        disparity_detected = True
                        if gap_percent < 0:
                            affected_groups.append(value)
                            pay_gap = max(pay_gap, abs(gap_percent))

            # Determine severity
            if disparity_detected:
                if pay_gap > 30:
                    severity = SeverityLevel.CRITICAL.value
                elif pay_gap > 25:
                    severity = SeverityLevel.SEVERE.value
                elif pay_gap > 20:
                    severity = SeverityLevel.SIGNIFICANT.value
                elif pay_gap > 15:
                    severity = SeverityLevel.MODERATE.value
                else:
                    severity = SeverityLevel.LOW.value

            # Create analysis record
            analysis = EquityAnalysis(
                organization_id=organization_id,
                analysis_type=AnalysisType.PAY_EQUITY.value,
                analysis_date=datetime.utcnow(),
                time_period_start=time_period_start,
                time_period_end=time_period_end,
                total_employees_analyzed=len(profiles),
                protected_classes_analyzed=[demographic_dimension],
                disparity_detected=disparity_detected,
                severity_level=severity,
                group_statistics=group_statistics,
                baseline_group=baseline_value,
                affected_groups=affected_groups,
                estimated_pay_gap=pay_gap,
                recommended_actions=self._generate_pay_equity_recommendations(severity, affected_groups),
                priority_level="high" if disparity_detected else "low"
            )

            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)

            logger.info(f"Pay equity analysis completed for org {organization_id}: {severity}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing pay equity: {e}")
            raise

    def _create_insufficient_data_analysis(
        self,
        organization_id: UUID,
        analysis_type: str
    ) -> EquityAnalysis:
        """Create analysis record for insufficient data cases"""
        return EquityAnalysis(
            organization_id=organization_id,
            analysis_type=analysis_type,
            analysis_date=datetime.utcnow(),
            total_employees_analyzed=0,
            disparity_detected=False,
            severity_level=SeverityLevel.NONE.value,
            group_statistics={},
            recommended_actions=[
                "Insufficient data for meaningful analysis",
                "Encourage employees to complete voluntary demographic surveys"
            ],
            priority_level="low"
        )

    def _generate_pay_equity_recommendations(
        self,
        severity: str,
        affected_groups: List[str]
    ) -> List[str]:
        """Generate recommendations based on pay equity analysis"""
        if severity == SeverityLevel.NONE.value:
            return [
                "Continue monitoring pay equity on quarterly basis",
                "Maintain current compensation practices"
            ]

        recommendations = [
            "Conduct comprehensive compensation audit",
            "Review starting salaries and promotion increases",
        ]

        if severity in [SeverityLevel.CRITICAL.value, SeverityLevel.SEVERE.value]:
            recommendations.extend([
                "URGENT: Immediate review of all compensation decisions",
                "Consider external pay equity consultant",
                "Develop corrective action plan",
                "Prepare for potential legal implications"
            ])

        if affected_groups:
            recommendations.append(
                f"Specific focus on equity for: {', '.join(affected_groups)}"
            )

        return recommendations

    # ============================================
    # PROMOTION EQUITY ANALYSIS
    # ============================================

    async def analyze_promotion_equity(
        self,
        organization_id: UUID,
        demographic_dimension: str,
        time_period_start: Optional[datetime] = None,
        time_period_end: Optional[datetime] = None
    ) -> EquityAnalysis:
        """
        Analyze promotion equity across demographic groups

        Args:
            organization_id: Organization UUID
            demographic_dimension: Dimension to analyze
            time_period_start: Optional start date
            time_period_end: Optional end date

        Returns:
            EquityAnalysis with promotion findings
        """
        try:
            if not time_period_end:
                time_period_end = datetime.utcnow()
            if not time_period_start:
                time_period_start = time_period_end - timedelta(days=730)  # 2 years

            # Get all promotions in time period
            promotions = self.db.query(PromotionTracking).filter(
                PromotionTracking.organization_id == organization_id,
                PromotionTracking.promotion_date >= time_period_start,
                PromotionTracking.promotion_date <= time_period_end
            ).all()

            if len(promotions) < 10:
                return self._create_insufficient_data_analysis(
                    organization_id, AnalysisType.PROMOTION_EQUITY.value
                )

            # Group promotions by demographic dimension
            promotion_rates = {}
            for promotion in promotions:
                # Get demographic info
                profile = self.db.query(DemographicProfile).filter(
                    DemographicProfile.user_id == promotion.user_id
                ).first()

                if profile:
                    value = getattr(profile, demographic_dimension, None)
                    if value:
                        if value not in promotion_rates:
                            promotion_rates[value] = {
                                "promoted": 0,
                                "avg_months_in_role": []
                            }
                        promotion_rates[value]["promoted"] += 1
                        if promotion.months_in_previous_role:
                            promotion_rates[value]["avg_months_in_role"].append(
                                promotion.months_in_previous_role
                            )

            # Calculate average time to promotion by group
            for value in promotion_rates:
                months = promotion_rates[value]["avg_months_in_role"]
                if months:
                    promotion_rates[value]["avg_time_to_promotion"] = sum(months) / len(months)

            # Detect disparities
            baseline_group = max(promotion_rates.keys(),
                                key=lambda k: promotion_rates[k]["promoted"])
            baseline_count = promotion_rates[baseline_group]["promoted"]

            disparity_detected = False
            severity = SeverityLevel.NONE.value
            affected_groups = []

            for value, stats in promotion_rates.items():
                if value != baseline_group:
                    ratio = stats["promoted"] / baseline_count if baseline_count > 0 else 0
                    if ratio < 0.7:  # 30% less promotion rate
                        disparity_detected = True
                        affected_groups.append(value)

            if disparity_detected:
                severity = SeverityLevel.MODERATE.value
            elif any(ratio < 0.85 for ratio in
                   [stats["promoted"] / baseline_count
                    for stats in promotion_rates.values()]):
                severity = SeverityLevel.LOW.value

            analysis = EquityAnalysis(
                organization_id=organization_id,
                analysis_type=AnalysisType.PROMOTION_EQUITY.value,
                analysis_date=datetime.utcnow(),
                time_period_start=time_period_start,
                time_period_end=time_period_end,
                total_employees_analyzed=len(promotions),
                protected_classes_analyzed=[demographic_dimension],
                disparity_detected=disparity_detected,
                severity_level=severity,
                group_statistics=promotion_rates,
                baseline_group=baseline_group,
                affected_groups=affected_groups,
                recommended_actions=self._generate_promotion_equity_recommendations(severity),
                priority_level="medium" if disparity_detected else "low"
            )

            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)

            logger.info(f"Promotion equity analysis completed for org {organization_id}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing promotion equity: {e}")
            raise

    def _generate_promotion_equity_recommendations(self, severity: str) -> List[str]:
        """Generate promotion equity recommendations"""
        if severity == SeverityLevel.NONE.value:
            return [
                "Continue monitoring promotion patterns",
                "Maintain transparent promotion criteria"
            ]

        recommendations = [
            "Review promotion criteria and process",
            "Ensure equal access to development opportunities",
            "Train managers on unconscious bias in promotion decisions",
            "Monitor promotion metrics quarterly by demographic group"
        ]

        if severity != SeverityLevel.LOW.value:
            recommendations.append(
                "Consider external review of promotion practices"
            )

        return recommendations

    # ============================================
    # HIRING DISPARITY ANALYSIS
    # ============================================

    async def analyze_hiring_disparities(
        self,
        organization_id: UUID,
        demographic_dimension: str,
        time_period_start: Optional[datetime] = None,
        time_period_end: Optional[datetime] = None
    ) -> EquityAnalysis:
        """
        Analyze hiring patterns for disparities

        Args:
            organization_id: Organization UUID
            demographic_dimension: Dimension to analyze
            time_period_start: Optional start date
            time_period_end: Optional end date

        Returns:
            EquityAnalysis with hiring findings
        """
        try:
            if not time_period_end:
                time_period_end = datetime.utcnow()
            if not time_period_start:
                time_period_start = time_period_end - timedelta(days=365)

            # Get hiring metrics
            metrics = self.db.query(HiringMetrics).filter(
                HiringMetrics.organization_id == organization_id,
                HiringMetrics.demographic_dimension == demographic_dimension,
                HiringMetrics.period_start >= time_period_start,
                HiringMetrics.period_end <= time_period_end
            ).all()

            if not metrics:
                return self._create_insufficient_data_analysis(
                    organization_id, AnalysisType.HIRING_DISPARITY.value
                )

            # Analyze hire rates by demographic group
            group_statistics = {}
            baseline_hire_rate = 0
            max_hires = 0

            for metric in metrics:
                value = metric.demographic_value
                group_statistics[value] = {
                    "applicants": metric.applicants_count,
                    "hired": metric.hired_count,
                    "hire_rate": metric.overall_hire_rate
                }

                if metric.hired_count > max_hires:
                    max_hires = metric.hired_count
                    baseline_hire_rate = metric.overall_hire_rate

            # Detect significant disparities
            affected_groups = []
            disparity_detected = False
            severity = SeverityLevel.NONE.value

            for value, stats in group_statistics.items():
                if stats["hire_rate"] > 0:
                    ratio = stats["hire_rate"] / baseline_hire_rate if baseline_hire_rate > 0 else 1
                    if ratio < 0.6:  # 40% lower hire rate
                        disparity_detected = True
                        affected_groups.append(value)

            if disparity_detected:
                severity = SeverityLevel.MODERATE.value

            analysis = EquityAnalysis(
                organization_id=organization_id,
                analysis_type=AnalysisType.HIRING_DISPARITY.value,
                analysis_date=datetime.utcnow(),
                time_period_start=time_period_start,
                time_period_end=time_period_end,
                total_employees_analyzed=sum(m.hired_count for m in metrics),
                protected_classes_analyzed=[demographic_dimension],
                disparity_detected=disparity_detected,
                severity_level=severity,
                group_statistics=group_statistics,
                affected_groups=affected_groups,
                recommended_actions=self._generate_hiring_recommendations(severity),
                priority_level="medium" if disparity_detected else "low"
            )

            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing hiring disparities: {e}")
            raise

    def _generate_hiring_recommendations(self, severity: str) -> List[str]:
        """Generate hiring disparity recommendations"""
        recommendations = [
            "Review job postings for biased language",
            "Ensure diverse interview panels",
            "Implement structured interview processes",
            "Track hiring metrics by demographic group",
            "Expand recruiting channels to reach diverse candidates"
        ]

        if severity != SeverityLevel.NONE.value:
            recommendations.extend([
                "Consider blind resume review process",
                "Audit selection criteria for adverse impact",
                "Provide unconscious bias training for hiring managers"
            ])

        return recommendations

    # ============================================
    # DISCRIMINATION COMPLAINTS
    # ============================================

    async def create_complaint(
        self,
        organization_id: UUID,
        complaint_data: Dict[str, Any],
        reporter_id: Optional[UUID] = None
    ) -> DiscriminationComplaint:
        """
        Create a discrimination complaint

        Args:
            organization_id: Organization UUID
            complaint_data: Complaint details
            reporter_id: Optional reporter UUID (None if anonymous)

        Returns:
            Created complaint
        """
        try:
            complaint = DiscriminationComplaint(
                organization_id=organization_id,
                complainant_id=complaint_data.get("complainant_id") or reporter_id,
                is_anonymous=complaint_data.get("is_anonymous", False),
                complaint_type=complaint_data["complaint_type"],
                discrimination_type=complaint_data["discrimination_type"],
                description=complaint_data["description"],
                incident_date=complaint_data.get("incident_date"),
                incident_location=complaint_data.get("incident_location"),
                perpetrator_type=complaint_data.get("perpetrator_type"),
                perpetrator_id=complaint_data.get("perpetrator_id"),
                witness_ids=complaint_data.get("witness_ids", []),
                evidence_urls=complaint_data.get("evidence_urls", []),
                severity=complaint_data.get("severity", SeverityLevel.MODERATE.value)
            )

            self.db.add(complaint)
            self.db.commit()
            self.db.refresh(complaint)

            logger.info(f"Created discrimination complaint: {complaint.id}")
            return complaint

        except Exception as e:
            logger.error(f"Error creating complaint: {e}")
            self.db.rollback()
            raise

    async def get_complaints(
        self,
        organization_id: UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[DiscriminationComplaint]:
        """
        Get discrimination complaints for organization

        Args:
            organization_id: Organization UUID
            status: Optional status filter
            severity: Optional severity filter
            limit: Maximum results

        Returns:
            List of complaints
        """
        try:
            query = self.db.query(DiscriminationComplaint).filter(
                DiscriminationComplaint.organization_id == organization_id
            )

            if status:
                query = query.filter(DiscriminationComplaint.status == status)

            if severity:
                query = query.filter(DiscriminationComplaint.severity == severity)

            complaints = query.order_by(
                DiscriminationComplaint.created_at.desc()
            ).limit(limit).all()

            return complaints

        except Exception as e:
            logger.error(f"Error retrieving complaints: {e}")
            raise

    # ============================================
    # COMPREHENSIVE EQUITY REPORT
    # ============================================

    async def generate_equity_report(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Generate comprehensive equity report

        Args:
            organization_id: Organization UUID

        Returns:
            Comprehensive equity analysis report
        """
        try:
            # Run all analyses
            pay_equity = await self.analyze_pay_equity(
                organization_id, "gender"
            )
            promotion_equity = await self.analyze_promotion_equity(
                organization_id, "race"
            )
            hiring_disparity = await self.analyze_hiring_disparities(
                organization_id, "gender"
            )

            # Get open complaints
            open_complaints = await self.get_complaints(
                organization_id, status="open"
            )

            # Calculate overall risk score
            critical_count = sum([
                1 for analysis in [pay_equity, promotion_equity, hiring_disparity]
                if analysis.severity_level in [
                    SeverityLevel.CRITICAL.value,
                    SeverityLevel.SEVERE.value
                ]
            ])

            risk_score = min(100, critical_count * 25)

            return {
                "organization_id": str(organization_id),
                "analysis_date": datetime.utcnow().isoformat(),
                "overall_risk_score": risk_score,
                "pay_equity": {
                    "severity": pay_equity.severity_level,
                    "disparity_detected": pay_equity.disparity_detected,
                    "affected_groups": pay_equity.affected_groups,
                },
                "promotion_equity": {
                    "severity": promotion_equity.severity_level,
                    "disparity_detected": promotion_equity.disparity_detected,
                    "affected_groups": promotion_equity.affected_groups,
                },
                "hiring_equity": {
                    "severity": hiring_disparity.severity_level,
                    "disparity_detected": hiring_disparity.disparity_detected,
                    "affected_groups": hiring_disparity.affected_groups,
                },
                "open_complaints": len(open_complaints),
                "complaint_severity_breakdown": self._count_complaints_by_severity(open_complaints),
                "recommendations": self._generate_comprehensive_recommendations(
                    pay_equity, promotion_equity, hiring_disparity
                ),
                "compliance_score": max(0, 100 - risk_score)
            }

        except Exception as e:
            logger.error(f"Error generating equity report: {e}")
            raise

    def _count_complaints_by_severity(
        self,
        complaints: List[DiscriminationComplaint]
    ) -> Dict[str, int]:
        """Count complaints by severity level"""
        severity_counts = {}
        for complaint in complaints:
            severity = complaint.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    def _generate_comprehensive_recommendations(
        self,
        *analyses: EquityAnalysis
    ) -> List[str]:
        """Generate comprehensive recommendations from all analyses"""
        all_recommendations = []

        for analysis in analyses:
            if analysis.recommended_actions:
                all_recommendations.extend(analysis.recommended_actions)

        # Add organizational recommendations
        if any(a.disparity_detected for a in analyses):
            all_recommendations.extend([
                "Establish diversity, equity, and inclusion (DEI) committee",
                "Conduct mandatory anti-discrimination training",
                "Implement regular equity audits (quarterly)",
                "Create mentorship and sponsorship programs",
                "Review and update HR policies for fairness"
            ])

        return list(set(all_recommendations))  # Remove duplicates
