import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.db.models.assessment import (
    Assessment,
    AssessmentCategory,
    AssessmentQuestion,
    AssessmentSection,
    AssessmentStatus,
)
from app.db.models.organization import Organization
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_data():
    async with AsyncSessionLocal() as db:
        try:
            # 0. Create or Get Organization
            org_name = "PsychSync Demo Org"
            organization = (
                await db.execute(
                    select(Organization).where(Organization.name == org_name)
                )
            ).scalar_one_or_none()

            if not organization:
                logger.info(f"Creating organization: {org_name}")
                organization = Organization(name=org_name)
                db.add(organization)
                await db.flush()
            else:
                logger.info(f"Organization found: {organization.id}")

            # 1. Create Teams
            num_teams = 10
            teams = []

            # Check for an existing user to be creator/owner
            admin_user = (await db.execute(select(User).limit(1))).scalar_one_or_none()
            if not admin_user:
                logger.info("Creating admin user for team creation...")
                admin_user = User(
                    email=f"admin_{uuid.uuid4()}@example.com",
                    password_hash=get_password_hash("StrongP@ssw0rd123!"),
                    full_name="Admin User",
                    role="admin",
                    is_active=True,
                    organization_id=organization.id,
                )
                db.add(admin_user)
                await db.flush()

            for t in range(num_teams):
                team_name = f"Predictive Team {t+1}"
                team = (
                    await db.execute(select(Team).where(Team.name == team_name))
                ).scalar_one_or_none()

                if not team:
                    logger.info(f"Creating team: {team_name}")
                    team = Team(
                        name=team_name,
                        description=f"Team {t+1} for predictive analytics",
                        created_by_id=admin_user.id,
                        organization_id=organization.id,
                    )
                    db.add(team)
                    await db.flush()
                else:
                    logger.info(f"Team found: {team.id}")
                teams.append(team)

            # 2. Create Users and Add to Teams
            # Create 5 users per team
            users = []
            for team in teams:
                for i in range(5):
                    email = f"user_{team.name.replace(' ', '_')}_{i}_{uuid.uuid4()}@example.com"
                    user = User(
                        email=email,
                        password_hash=get_password_hash("StrongP@ssw0rd123!"),
                        full_name=f"User {i} of {team.name}",
                        role="employee",
                        is_active=True,
                        organization_id=organization.id,
                    )
                    db.add(user)
                    await db.flush()
                    users.append(user)

                    # Add to team
                    member = TeamMember(
                        team_id=team.id, user_id=user.id, role=TeamRole.MEMBER
                    )
                    db.add(member)

            await db.flush()
            logger.info(f"Created {len(users)} users across {len(teams)} teams.")

            # 3. Create Assessment (One shared assessment)
            assessment_title = "Team Performance Assessment"
            assessment = Assessment(
                title=assessment_title,
                description="Assessment to measure team performance factors",
                category=AssessmentCategory.SKILLS,
                status=AssessmentStatus.PUBLISHED,
                created_by_id=admin_user.id,
                team_id=None,  # Organization-wide assessment, or loop to assign to all teams?
                # Assessment model has team_id as nullable.
                # collect_assessment_data filters by team_id via Assessment.team_id.
                # If Assessment.team_id is None, does it match?
            )
            # To ensure it works for all teams, we might need multiple assessments or one assigned to None (if supported)
            # collect_assessment_data logic:
            # if team_ids: query.append(Assessment.team_id.in_(team_ids))
            # This implies assessments must be assigned to the specific team.

            # Let's create an assessment for each team to be safe.

            assessments = []
            for team in teams:
                assessment = Assessment(
                    title=f"{assessment_title} for {team.name}",
                    description="Assessment to measure team performance factors",
                    category=AssessmentCategory.SKILLS,
                    status=AssessmentStatus.PUBLISHED,
                    created_by_id=admin_user.id,
                    team_id=team.id,
                )
                db.add(assessment)
                await db.flush()
                assessments.append(assessment)

                # 4. Create Section and Questions for this assessment
                section = AssessmentSection(
                    assessment_id=assessment.id, title="General Skills", order=1
                )
                db.add(section)
                await db.flush()

                questions = []
                for i in range(10):
                    question = AssessmentQuestion(
                        section_id=section.id,
                        question_type="scale",
                        question_text=f"Question {i+1}: Rate performance.",
                        order=i + 1,
                        is_required=True,
                    )
                    db.add(question)
                    questions.append(question)

                await db.flush()

                # 5. Generate Responses for this team's users
                team_users = (
                    (
                        await db.execute(
                            select(User)
                            .join(TeamMember)
                            .where(TeamMember.team_id == team.id)
                        )
                    )
                    .scalars()
                    .all()
                )

                for user in team_users:
                    for question in questions:
                        # Random answer with some team-based bias to make data interesting
                        # Teams 0-4 high performance, 5-9 low performance
                        team_idx = teams.index(team)
                        if team_idx < 5:
                            answer_value = random.randint(4, 5)
                        else:
                            answer_value = random.randint(1, 3)

                        response_time = random.randint(2000, 15000)

                        response = Response(
                            assessment_id=assessment.id,
                            user_id=user.id,
                            question_id=question.id,
                            answer_value=answer_value,
                            response_time_ms=response_time,
                            created_at=datetime.utcnow()
                            - timedelta(days=random.randint(0, 30)),
                        )
                        db.add(response)

            await db.commit()
            logger.info("Data generation complete.")

        except Exception as e:
            logger.error(f"Error generating data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(generate_data())
