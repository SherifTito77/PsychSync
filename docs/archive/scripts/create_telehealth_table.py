"""
Create telehealth_sessions table directly
This bypasses the broken migration chain
"""

import asyncio

from sqlalchemy import text

from app.db.session import get_async_db


async def create_telehealth_table():
    async for db in get_async_db():
        try:
            # Check if table exists first
            result = await db.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'telehealth_sessions'
                )
            """
                )
            )
            exists = result.scalar()

            if exists:
                print("✅ telehealth_sessions table already exists")
                return

            # Create the table
            create_sql = """
            CREATE TABLE telehealth_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                clinician_id UUID REFERENCES users(id) ON DELETE SET NULL,

                -- Session details
                session_type VARCHAR(50) NOT NULL,
                consultation_reason TEXT,
                related_assessment_id UUID,

                -- Twilio Video details
                room_sid VARCHAR(100) UNIQUE,
                room_name VARCHAR(200) UNIQUE,
                user_token TEXT,
                clinician_token TEXT,

                -- Scheduling
                scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
                duration_minutes INTEGER DEFAULT 50,
                timezone VARCHAR(50) DEFAULT 'UTC',

                -- Session tracking
                started_at TIMESTAMP WITH TIME ZONE,
                ended_at TIMESTAMP WITH TIME ZONE,
                actual_duration_minutes INTEGER,
                user_joined_at TIMESTAMP WITH TIME ZONE,
                clinician_joined_at TIMESTAMP WITH TIME ZONE,

                -- Recording
                recording_enabled BOOLEAN DEFAULT true,
                recording_sid VARCHAR(100),
                recording_url TEXT,
                recording_duration_seconds INTEGER,

                -- Session notes
                session_notes TEXT,
                clinician_notes TEXT,
                prescriptions_issued JSONB,
                diagnoses_discussed TEXT[],

                -- Status
                status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,
                cancellation_reason VARCHAR(200),
                cancelled_by VARCHAR(50),
                cancelled_at TIMESTAMP WITH TIME ZONE,

                -- Quality metrics
                connection_quality VARCHAR(20),
                technical_issues JSONB,
                user_satisfaction_rating INTEGER,
                feedback_comment TEXT,

                -- Timestamps
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );

            -- Create indexes for common queries
            CREATE INDEX idx_telehealth_user ON telehealth_sessions(user_id);
            CREATE INDEX idx_telehealth_clinician ON telehealth_sessions(clinician_id);
            CREATE INDEX idx_telehealth_upcoming ON telehealth_sessions(scheduled_time, status)
                WHERE status IN ('scheduled', 'in_progress');
            CREATE INDEX idx_telehealth_status ON telehealth_sessions(status);
            """

            print("Creating telehealth_sessions table...")
            for statement in create_sql.split(";"):
                statement = statement.strip()
                if statement:
                    await db.execute(text(statement))

            await db.commit()
            print("✅ telehealth_sessions table created successfully!")

        except Exception as e:
            print(f"❌ Error creating table: {e}")
            await db.rollback()
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(create_telehealth_table())
