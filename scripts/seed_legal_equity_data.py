"""
Seed script for Legal Rights and Discrimination Analysis systems

Populates the database with sample labor laws, legal aid resources,
and other reference data for testing and demonstration.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.db.models.discrimination_analysis import DemographicProfile
from app.db.models.legal_rights import LaborLaw, LegalAidResource
from app.db.models.organization import Organization
from app.db.models.user import User


async def seed_labor_laws(db: AsyncSession) -> int:
    """Seed labor laws for major countries"""
    print("Seeding labor laws...")

    labor_laws_data = [
        # United States
        {
            "country_code": "US",
            "country_name": "United States",
            "state_region": None,
            "continent": "NA",
            "law_name": "Fair Labor Standards Act (FLSA)",
            "law_code": "29 U.S.C. § 201",
            "category": "working_hours",
            "description": "Establishes minimum wage, overtime pay, recordkeeping, and youth employment standards.",
            "min_wage": 7.25,
            "max_weekly_hours": 40,
            "overtime_threshold": 40,
            "overtime_rate": 1.5,
            "mandatory_break_minutes": None,
            "min_vacation_days": 0,
            "discrimination_protection_level": 8,
            "safety_protection_level": 7,
            "privacy_protection_level": 6,
            "termination_protection_level": 5,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.dol.gov/agencies/whd/flsa",
        },
        {
            "country_code": "US",
            "country_name": "United States",
            "state_region": None,
            "continent": "NA",
            "law_name": "Title VII of the Civil Rights Act",
            "law_code": "42 U.S.C. § 2000e",
            "category": "discrimination_protection",
            "description": "Prohibits employment discrimination based on race, color, religion, sex, or national origin.",
            "discrimination_protection_level": 9,
            "safety_protection_level": 8,
            "privacy_protection_level": 7,
            "termination_protection_level": 7,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.eeoc.gov/laws/guidance/title-vii-civil-rights-act-1964",
        },
        # United Kingdom
        {
            "country_code": "UK",
            "country_name": "United Kingdom",
            "state_region": None,
            "continent": "EU",
            "law_name": "National Minimum Wage Act 1998",
            "law_code": "NMWA 1998",
            "category": "wages_compensation",
            "description": "Establishes the national minimum wage for workers in the UK.",
            "min_wage": 10.42,
            "max_weekly_hours": 48,
            "overtime_threshold": 48,
            "overtime_rate": 1.25,
            "mandatory_break_minutes": 20,
            "min_vacation_days": 28,
            "discrimination_protection_level": 9,
            "safety_protection_level": 8,
            "privacy_protection_level": 8,
            "termination_protection_level": 7,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.legislation.gov.uk/ukpga/1998/8/contents",
        },
        {
            "country_code": "UK",
            "country_name": "United Kingdom",
            "state_region": None,
            "continent": "EU",
            "law_name": "Equality Act 2010",
            "law_code": "EqA 2010",
            "category": "discrimination_protection",
            "description": "Protects people from discrimination based on protected characteristics.",
            "discrimination_protection_level": 10,
            "safety_protection_level": 8,
            "privacy_protection_level": 8,
            "termination_protection_level": 8,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.legislation.gov.uk/ukpga/2010/15/contents",
        },
        # Canada
        {
            "country_code": "CA",
            "country_name": "Canada",
            "state_region": None,
            "continent": "NA",
            "law_name": "Canadian Labour Code",
            "law_code": "R.S.C., 1985, c. L-2",
            "category": "working_hours",
            "description": "Sets standards for wages, hours of work, and other working conditions.",
            "min_wage": None,  # Varies by province
            "max_weekly_hours": 48,
            "overtime_threshold": 40,
            "overtime_rate": 1.5,
            "mandatory_break_minutes": None,
            "min_vacation_days": 14,
            "discrimination_protection_level": 9,
            "safety_protection_level": 8,
            "privacy_protection_level": 7,
            "termination_protection_level": 6,
            "is_active": True,
            "verified": True,
            "source_url": "https://laws-lois.justice.gc.ca/eng/acts/L-2/",
        },
        # Australia
        {
            "country_code": "AU",
            "country_name": "Australia",
            "state_region": None,
            "continent": "OC",
            "law_name": "Fair Work Act 2009",
            "law_code": "FWA 2009",
            "category": "working_hours",
            "description": "Provides workplace relations framework including minimum wages and conditions.",
            "min_wage": 23.23,
            "max_weekly_hours": 38,
            "overtime_threshold": 38,
            "overtime_rate": 1.5,
            "mandatory_break_minutes": None,
            "min_vacation_days": 20,
            "discrimination_protection_level": 9,
            "safety_protection_level": 8,
            "privacy_protection_level": 7,
            "termination_protection_level": 7,
            "is_active": True,
            "verified": True,
            "source_url": "https://legislation.gov.au/Details/C2019C00162",
        },
        # Germany
        {
            "country_code": "DE",
            "country_name": "Germany",
            "state_region": None,
            "continent": "EU",
            "law_name": "General Act on Equal Treatment",
            "law_code": "AGG",
            "category": "discrimination_protection",
            "description": "Prohibits discrimination on grounds of race, ethnic origin, gender, religion, etc.",
            "discrimination_protection_level": 10,
            "safety_protection_level": 9,
            "privacy_protection_level": 9,
            "termination_protection_level": 8,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.gesetze-im-internet.de/english_bgb/agg__2018-08-08.html",
        },
        # France
        {
            "country_code": "FR",
            "country_name": "France",
            "state_region": None,
            "continent": "EU",
            "law_name": "French Labour Code",
            "law_code": "Code du travail",
            "category": "working_hours",
            "description": "Regulates employment, working conditions, and employee rights in France.",
            "min_wage": 11.27,  # SMIC
            "max_weekly_hours": 35,
            "overtime_threshold": 35,
            "overtime_rate": 1.25,
            "mandatory_break_minutes": 20,
            "min_vacation_days": 30,
            "discrimination_protection_level": 10,
            "safety_protection_level": 9,
            "privacy_protection_level": 8,
            "termination_protection_level": 8,
            "is_active": True,
            "verified": True,
            "source_url": "https://www.legifrance.gouv.fr/",
        },
    ]

    created_count = 0
    for law_data in labor_laws_data:
        from sqlalchemy import select

        result = await db.execute(
            select(LaborLaw).where(
                LaborLaw.country_code == law_data["country_code"],
                LaborLaw.law_code == law_data["law_code"],
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            law = LaborLaw(**law_data)
            db.add(law)
            created_count += 1

    await db.commit()
    print(f"✅ Created {created_count} labor laws")
    return created_count


async def seed_legal_aid_resources(db: AsyncSession) -> int:
    """Seed legal aid resources for major US cities"""
    print("Seeding legal aid resources...")

    legal_aid_data = [
        {
            "country_code": "US",
            "state_region": "CA",
            "city": "San Francisco",
            "resource_type": "legal_aid_org",
            "name": "Legal Aid Society of San Francisco",
            "description": "Provides free legal services to low-income residents in employment law cases.",
            "phone": "(415) 863-9761",
            "email": "info@lasf.org",
            "website": "https://www.lasf.org",
            "address": "575 Market Street, Suite 400, San Francisco, CA 94105",
            "specializations": [
                "employment",
                "discrimination",
                "wrongful_termination",
                "wages",
            ],
            "languages_spoken": ["en", "es", "zh", "tl"],
            "free_consultation": True,
            "sliding_scale": True,
            "emergency_services": False,
            "verified": True,
            "rating": 4.5,
            "response_time_hours": 48,
        },
        {
            "country_code": "US",
            "state_region": "NY",
            "city": "New York",
            "resource_type": "legal_aid_org",
            "name": "New York Legal Assistance Group",
            "description": "Nonprofit providing free legal services in employment discrimination cases.",
            "phone": "(212) 431-7200",
            "email": "help@nylag.org",
            "website": "https://www.nylag.org",
            "address": "50 Broadway, Suite 1100, New York, NY 10004",
            "specializations": ["employment", "discrimination", "harassment"],
            "languages_spoken": ["en", "es"],
            "free_consultation": True,
            "sliding_scale": True,
            "emergency_services": False,
            "verified": True,
            "rating": 4.7,
            "response_time_hours": 24,
        },
        {
            "country_code": "US",
            "state_region": None,
            "city": None,
            "resource_type": "hotline",
            "name": "EEOC Toll-Free Hotline",
            "description": "Equal Employment Opportunity Commission hotline for discrimination charges.",
            "phone": "1-800-669-4000",
            "website": "https://www.eeoc.gov",
            "specializations": ["discrimination", "harassment", "retaliation"],
            "languages_spoken": ["en", "es"],
            "free_consultation": True,
            "emergency_services": False,
            "verified": True,
            "rating": 4.8,
            "response_time_hours": 1,
        },
        {
            "country_code": "US",
            "state_region": "CA",
            "city": "Los Angeles",
            "resource_type": "lawyer",
            "name": "Employment Rights Law Group APC",
            "description": "Employment law firm specializing in discrimination and wrongful termination cases.",
            "phone": "(310) 553-3100",
            "email": "info@employeerightslawgroup.com",
            "website": "https://www.employeerightslawgroup.com",
            "address": "10866 Wilshire Blvd, Suite 800, Los Angeles, CA 90024",
            "specializations": [
                "employment",
                "discrimination",
                "wrongful_termination",
                "overtime",
            ],
            "languages_spoken": ["en", "es", "ko"],
            "free_consultation": True,
            "sliding_scale": False,
            "emergency_services": False,
            "verified": True,
            "rating": 4.6,
            "consultation_fee": 0.0,
            "hourly_rate": 350.0,
        },
        {
            "country_code": "UK",
            "state_region": "England",
            "city": "London",
            "resource_type": "legal_aid_org",
            "name": "Citizens Advice Bureau",
            "description": "Provides free, confidential, and impartial advice on employment rights.",
            "phone": "03444 111 444",
            "website": "https://www.citizensadvice.org.uk",
            "address": "4th Floor, 200 Aldersgate, London, EC1A 4HD",
            "specializations": ["employment", "discrimination", "unfair_dismissal"],
            "languages_spoken": ["en"],
            "free_consultation": True,
            "sliding_scale": False,
            "emergency_services": False,
            "verified": True,
            "rating": 4.4,
            "response_time_hours": 72,
        },
    ]

    created_count = 0
    for aid_data in legal_aid_data:
        from sqlalchemy import select

        result = await db.execute(
            select(LegalAidResource).where(
                LegalAidResource.name == aid_data["name"],
                LegalAidResource.city == aid_data["city"],
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            aid = LegalAidResource(**aid_data)
            db.add(aid)
            created_count += 1

    await db.commit()
    print(f"✅ Created {created_count} legal aid resources")
    return created_count


async def seed_sample_demographics(db: AsyncSession) -> int:
    """Seed sample demographic profiles for testing"""
    print("Seeding sample demographic profiles...")

    # Get first organization and its users
    from sqlalchemy import select

    org_result = await db.execute(select(Organization).limit(1))
    org = org_result.scalar_one_or_none()

    if not org:
        print("⚠️  No organizations found. Skipping demographic seeding.")
        return 0

    users_result = await db.execute(
        select(User)
        .where(User.organization_id == org.id, User.is_active == True)
        .limit(20)
    )
    users = users_result.scalars().all()

    if not users:
        print("⚠️  No users found. Skipping demographic seeding.")
        return 0

    # Sample demographic data
    demographic_samples = [
        {
            "gender": "female",
            "race": "white",
            "age_range": "30-39",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "male",
            "race": "white",
            "age_range": "30-39",
            "veteran_status": "veteran",
        },
        {
            "gender": "male",
            "race": "asian",
            "age_range": "20-29",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "female",
            "race": "black",
            "age_range": "40-49",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "non-binary",
            "race": "white",
            "age_range": "25-34",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "male",
            "race": "hispanic",
            "age_range": "35-44",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "female",
            "race": "asian",
            "age_range": "28-37",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "male",
            "race": "black",
            "age_range": "45-54",
            "veteran_status": "veteran",
        },
        {
            "gender": "female",
            "race": "white",
            "age_range": "50-59",
            "veteran_status": "non-veteran",
        },
        {
            "gender": "male",
            "race": "white",
            "age_range": "25-34",
            "veteran_status": "non-veteran",
        },
    ]

    created_count = 0
    for i, user in enumerate(users):
        # Check if profile already exists
        profile_result = await db.execute(
            select(DemographicProfile).where(DemographicProfile.user_id == user.id)
        )
        existing = profile_result.scalar_one_or_none()

        if not existing and i < len(demographic_samples):
            profile = DemographicProfile(
                user_id=user.id,
                organization_id=org.id,
                **demographic_samples[i],
                consent_given=True,
                verified=False,
            )
            db.add(profile)
            created_count += 1

    await db.commit()
    print(f"✅ Created {created_count} sample demographic profiles")
    return created_count


async def main():
    """Main seeding function"""
    print("🌱 Starting Legal Rights and Discrimination Analysis data seeding...\n")

    async with AsyncSessionLocal() as db:
        try:
            total_created = 0

            # Seed labor laws
            total_created += await seed_labor_laws(db)

            # Seed legal aid resources
            total_created += await seed_legal_aid_resources(db)

            # Seed sample demographics
            total_created += await seed_sample_demographics(db)

            await db.commit()
            print(f"\n✅ Seeding completed! Total records created: {total_created}")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
