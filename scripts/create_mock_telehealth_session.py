import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.db.session import get_async_db


async def create_mock_session():
    print("🚀 Starting Mock Telehealth Session Creation...")

    async for db in get_async_db():
        try:
            # 1. Ensure we have a patient and a clinician
            result = await db.execute(
                text("SELECT id, email FROM users WHERE role = 'patient' LIMIT 1")
            )
            patient = result.fetchone()

            result = await db.execute(
                text("SELECT id, email FROM users WHERE role = 'clinician' LIMIT 1")
            )
            clinician = result.fetchone()

            if not patient:
                print("📝 Creating mock patient...")
                p_id = uuid.uuid4()
                await db.execute(
                    text(
                        """
                    INSERT INTO users (id, email, password_hash, full_name, role, is_active)
                    VALUES (:id, 'demo_patient@psychsync.com', 'hashed', 'Demo Patient', 'patient', true)
                """
                    ),
                    {"id": p_id},
                )
                patient_id = p_id
            else:
                patient_id = patient[0]

            if not clinician:
                print("📝 Creating mock clinician...")
                c_id = uuid.uuid4()
                await db.execute(
                    text(
                        """
                    INSERT INTO users (id, email, password_hash, full_name, role, is_active)
                    VALUES (:id, 'demo_clinician@psychsync.com', 'hashed', 'Dr. Demo Clinician', 'clinician', true)
                """
                    ),
                    {"id": c_id},
                )
                clinician_id = c_id
            else:
                clinician_id = clinician[0]

            await db.commit()  # Commit users first

            # 2. Define session details
            session_id = uuid.uuid4()
            scheduled_time = datetime.now(timezone.utc) + timedelta(hours=2)

            # 3. Insert mock session
            insert_sql = text(
                """
                INSERT INTO telehealth_sessions (
                    id, user_id, clinician_id, session_type, consultation_reason,
                    scheduled_time, duration_minutes, status, recording_enabled,
                    room_name, room_sid, created_at
                ) VALUES (
                    :id, :user_id, :clinician_id, :type, :reason,
                    :time, :duration, :status, :recording,
                    :room_name, :room_sid, :created_at
                )
            """
            )

            await db.execute(
                insert_sql,
                {
                    "id": session_id,
                    "user_id": patient_id,
                    "clinician_id": clinician_id,
                    "type": "initial",
                    "reason": "Introductory Consultation & Clinical Strategy",
                    "time": scheduled_time,
                    "duration": 60,
                    "status": "scheduled",
                    "recording": True,
                    "room_name": f"demo-session-{session_id}",
                    "room_sid": f"RM{uuid.uuid4().hex[:30]}",
                    "created_at": datetime.now(timezone.utc),
                },
            )

            await db.commit()
            print(
                f"🎉 SUCCESS! Mock session created for {scheduled_time.strftime('%Y-%m-%d %H:%M')} UTC"
            )
            print(f"🔗 Session ID: {session_id}")

        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(create_mock_session())
