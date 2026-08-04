import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.db.models.assessment import (
    Assessment,
    AssessmentCategory,
    AssessmentQuestion,
    AssessmentSection,
    AssessmentStatus,
)
from app.db.models.organization import Organization
from app.db.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_engagement_survey():
    async with AsyncSessionLocal() as db:
        # Get an organization
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalar_one_or_none()
        if not org:
            logger.error("No organization found. Please seed organizations first.")
            return

        # Get an admin user
        user_result = await db.execute(select(User).limit(1))
        user = user_result.scalar_one_or_none()
        if not user:
            logger.error("No user found. Please seed users first.")
            return

        # Check if engagement survey already exists
        existing_result = await db.execute(
            select(Assessment).where(Assessment.framework_code == "ENGAGEMENT")
        )
        if existing_result.scalar_one_or_none():
            logger.info("Engagement survey already seeded.")
            return

        # Create Engagement Assessment
        assessment = Assessment(
            id=uuid4(),
            title="Employee Engagement Survey 2024",
            description="Measure workplace satisfaction and employee sentiment.",
            category=AssessmentCategory.BEHAVIORAL,
            status=AssessmentStatus.PUBLISHED,
            created_by_id=user.id,
            organization_id=org.id,
            framework_code="ENGAGEMENT",
        )
        db.add(assessment)
        await db.flush()

        # Create Section
        section = AssessmentSection(
            id=uuid4(),
            assessment_id=assessment.id,
            title="General Engagement",
            description="Please rate your agreement with the following statements.",
            order=1,
        )
        db.add(section)
        await db.flush()

        # Define questions for each dimension
        questions_data = [
            # Job Satisfaction
            {
                "text": "I find my work meaningful and fulfilling.",
                "dim": "job_satisfaction",
            },
            {
                "text": "I am proud to work for this organization.",
                "dim": "job_satisfaction",
            },
            # Work-Life Balance
            {
                "text": "My workload allows me to maintain a healthy work-life balance.",
                "dim": "work_life_balance",
            },
            {
                "text": "I can disconnect from work during my personal time.",
                "dim": "work_life_balance",
            },
            # Management Support
            {
                "text": "My manager provides clear goals and expectations.",
                "dim": "management_support",
            },
            {
                "text": "I receive regular and constructive feedback from my manager.",
                "dim": "management_support",
            },
            # Career Growth
            {
                "text": "I see clear opportunities for career progression here.",
                "dim": "career_growth",
            },
            {
                "text": "The organization invests in my professional development.",
                "dim": "career_growth",
            },
            # Compensation Satisfaction
            {
                "text": "I am fairly compensated for the work I do.",
                "dim": "compensation_satisfaction",
            },
            {
                "text": "Our benefits package meets my needs.",
                "dim": "compensation_satisfaction",
            },
            # Team Collaboration
            {
                "text": "There is a strong sense of teamwork and collaboration in my department.",
                "dim": "team_collaboration",
            },
            {"text": "I feel supported by my colleagues.", "dim": "team_collaboration"},
        ]

        for i, q_data in enumerate(questions_data):
            question = AssessmentQuestion(
                id=uuid4(),
                section_id=section.id,
                question_type="rating_scale",  # 1-5
                question_text=q_data["text"],
                order=i,
                config={"dimension": q_data["dim"], "min": 1, "max": 5},
            )
            db.add(question)

        await db.commit()
        logger.info(
            f"Successfully seeded Engagement Survey with {len(questions_data)} questions."
        )


if __name__ == "__main__":
    asyncio.run(seed_engagement_survey())
