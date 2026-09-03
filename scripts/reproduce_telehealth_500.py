import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import and_, select

from app.db.models.clinical_extended import TelehealthSession
from app.db.models.user import User
from app.db.session import get_async_db


# Mock the request schema
class ScheduleSessionRequest(BaseModel):
    session_type: str
    consultation_reason: Optional[str] = None
    scheduled_time: datetime
    duration_minutes: int = 60
    related_assessment_id: Optional[str] = None
    timezone: str = "UTC"
    clinician_id: Optional[str] = None
    recording_enabled: bool = False


async def reproduce():
    print("🧪 Reproducing Telehealth 500 error...")

    async for db in get_async_db():
        try:
            # 1. Get a test user
            result = await db.execute(
                select(User).where(User.role == "patient").limit(1)
            )
            current_user = result.scalar_one_or_none()
            if not current_user:
                print(
                    "❌ No patient found. Please run scripts/create_mock_telehealth_session.py first."
                )
                return

            # 2. Mock request
            request = ScheduleSessionRequest(
                session_type="initial",
                scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
                duration_minutes=60,
                clinician_id="00000000-0000-0000-0000-000000000001",
            )

            print(f"👤 Using User: {current_user.email}")
            print(f"👨‍⚕️ Requested Clinician ID: {request.clinician_id}")

            # 3. Simulate logic in schedule_telehealth_session
            # Validate scheduled_time is in the future
            print("🕒 Validating scheduled time...")
            if request.scheduled_time < datetime.now(timezone.utc) + timedelta(
                minutes=15
            ):
                print("❌ Validation failed: too soon.")
                return
            print("✅ Time validation passed!")

            # Assign clinician
            if request.clinician_id:
                # Use specified clinician
                clinician_query = select(User).where(
                    and_(User.id == request.clinician_id, User.is_active == True)
                )
                clinician_result = await db.execute(clinician_query)
                clinician = clinician_result.scalar_one_or_none()

                if not clinician:
                    print(
                        "⚠️ Clinician not found (as expected). Falling back to auto-assign for this test."
                    )
                    # Auto-assign first available clinician
                    clinician_query = (
                        select(User)
                        .where(and_(User.role == "clinician", User.is_active == True))
                        .limit(1)
                    )
                    clinician_result = await db.execute(clinician_query)
                    clinician = clinician_result.scalar_one_or_none()

            if not clinician:
                print("❌ No clinician found even for auto-assign.")
                return

            print(f"✅ Using Clinician: {clinician.email} ({clinician.id})")

            # Create session record
            session = TelehealthSession(
                user_id=current_user.id,
                clinician_id=clinician.id,
                session_type="group",  # Test 'group' type specifically
                consultation_reason=request.consultation_reason
                or f"Group Therapy Session",
                related_assessment_id=request.related_assessment_id,
                scheduled_time=request.scheduled_time,
                duration_minutes=request.duration_minutes,
                timezone=request.timezone,
                status="scheduled",
            )

            # Set recording_enabled
            if hasattr(session, "recording_enabled"):
                session.recording_enabled = request.recording_enabled

            print("💾 Attempting to add and commit session...")
            db.add(session)
            await db.commit()
            print("✅ Commit successful!")

            await db.refresh(session)
            print(f"🎉 Session created with ID: {session.id}")

        except Exception as e:
            print(f"🔥 CAUGHT ERROR: {type(e).__name__}: {str(e)}")
            import traceback

            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(reproduce())
