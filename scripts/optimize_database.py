#!/usr/bin/env python3
"""
Database optimization script for PsychSync
Run this script to optimize database performance and create necessary indexes
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.config import settings
from app.core.database_optimization import DatabaseOptimizer, create_database_view_optimizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main optimization function"""

    logger.info("Starting PsychSync database optimization...")

    # Create database engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False  # Set to True to see SQL statements
    )

    async with AsyncSession(engine) as db:
        try:
            # Initialize optimizer
            optimizer = DatabaseOptimizer(db)

            # Step 1: Create performance indexes
            logger.info("Creating performance indexes...")
            await optimizer.create_performance_indexes()

            # Step 2: Update table statistics
            logger.info("Updating table statistics...")
            await optimizer.update_table_statistics()

            # Step 3: Create optimized views
            logger.info("Creating optimized database views...")
            await create_database_view_optimizer(db)

            # Step 4: Check for table bloat
            logger.info("Checking for table bloat...")
            bloat_tables = await optimizer.check_table_bloat()
            if bloat_tables:
                logger.warning(f"Found {len(bloat_tables)} tables with high bloat:")
                for table in bloat_tables:
                    logger.warning(f"  - {table['tablename']}: {table['tbloat']}x bloat")
            else:
                logger.info("No significant table bloat detected")

            # Step 5: Get database statistics
            logger.info("Collecting database statistics...")
            stats = await optimizer.get_database_stats()

            # Display key statistics
            if 'database_size' in stats:
                logger.info(f"Database size: {stats['database_size'][0]['size']}")

            if 'table_sizes' in stats:
                logger.info("Top 5 largest tables:")
                for table in stats['table_sizes'][:5]:
                    logger.info(f"  - {table['tablename']}: {table['size']}")

            # Step 6: Run automated optimization
            logger.info("Running automated optimization...")
            await optimizer.auto_optimize_database()

            logger.info("✅ Database optimization completed successfully!")

            # Print optimization summary
            print("\n" + "="*60)
            print("PSYCHSYNC DATABASE OPTIMIZATION SUMMARY")
            print("="*60)
            print("✅ Performance indexes created")
            print("✅ Table statistics updated")
            print("✅ Optimized database views created")
            print("✅ Database bloat analyzed")
            print("✅ Performance statistics collected")
            print("✅ Automated optimization completed")
            print("="*60)

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Optimization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)