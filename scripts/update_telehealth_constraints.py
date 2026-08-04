import asyncio

from sqlalchemy import text

from app.db.session import get_async_db


async def update_database_constraints():
    print("🚀 Updating database constraints for telehealth_sessions...")

    async for db in get_async_db():
        try:
            # 1. Update session_type constraint
            print("📝 Updating valid_session_type constraint...")
            await db.execute(
                text(
                    "ALTER TABLE telehealth_sessions DROP CONSTRAINT IF EXISTS valid_session_type"
                )
            )
            await db.execute(
                text(
                    """
                ALTER TABLE telehealth_sessions
                ADD CONSTRAINT valid_session_type
                CHECK (session_type IN ('initial', 'follow_up', 'crisis', 'routine', 'group'))
            """
                )
            )

            # 2. Update status constraint (just in case)
            print("📝 Updating valid_session_status constraint...")
            await db.execute(
                text(
                    "ALTER TABLE telehealth_sessions DROP CONSTRAINT IF EXISTS valid_session_status"
                )
            )
            await db.execute(
                text(
                    """
                ALTER TABLE telehealth_sessions
                ADD CONSTRAINT valid_session_status
                CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show'))
            """
                )
            )

            await db.commit()
            print("✅ Database constraints updated successfully!")

        except Exception as e:
            print(f"❌ Error updating constraints: {e}")
            await db.rollback()
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(update_database_constraints())
