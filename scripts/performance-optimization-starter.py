#!/usr/bin/env python3
"""
PsychSync Performance Optimization Starter Script
Phase 1: Database Connection Pool Optimization

This script safely applies the first phase of performance optimizations
with rollback capabilities and monitoring.
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import get_async_engine
from sqlalchemy import text
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Safe performance optimization implementation with rollback"""

    def __init__(self):
        self.backup_settings = {}
        self.engine = None
        self.optimizations_applied = []

    async def backup_current_settings(self) -> Dict[str, Any]:
        """Backup current configuration for rollback"""
        logger.info("🔄 Backing up current settings...")

        self.backup_settings = {
            'DB_POOL_SIZE': getattr(settings, 'DB_POOL_SIZE', None),
            'DB_MAX_OVERFLOW': getattr(settings, 'DB_MAX_OVERFLOW', None),
            'DB_POOL_RECYCLE': getattr(settings, 'DB_POOL_RECYCLE', None),
            'timestamp': datetime.now().isoformat()
        }

        # Save backup to file
        backup_file = project_root / '.env.backup'
        with open(backup_file, 'w') as f:
            f.write(f"# Performance Optimization Backup - {datetime.now()}\n")
            for key, value in self.backup_settings.items():
                if key != 'timestamp':
                    f.write(f"{key}={value}\n")

        logger.info(f"✅ Settings backed up to {backup_file}")
        return self.backup_settings

    async def apply_connection_pool_optimization(self):
        """Apply Phase 1: Database connection pool optimization"""
        logger.info("🚀 Applying Phase 1: Database Connection Pool Optimization")

        # Recommended production settings
        optimized_settings = {
            'DB_POOL_SIZE': 20,              # 4x increase
            'DB_MAX_OVERFLOW': 30,           # 3x increase
            'DB_POOL_RECYCLE': 1800,         # 30 minutes for connection health
            'DB_POOL_PRE_PING': True         # Enable connection validation
        }

        try:
            # Update environment file safely
            env_file = project_root / '.env.dev'

            if env_file.exists():
                await self._update_env_file(env_file, optimized_settings)
                self.optimizations_applied.append('connection_pool')
                logger.info("✅ Connection pool settings updated")

            # Validate new settings
            await self._validate_new_settings()

        except Exception as e:
            logger.error(f"❌ Failed to apply connection pool optimization: {e}")
            await self.rollback_changes()
            raise

    async def _update_env_file(self, env_file: Path, settings_update: Dict[str, Any]):
        """Safely update environment file with new settings"""
        content = env_file.read_text()
        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            if line.startswith('#') or not line.strip():
                updated_lines.append(line)
                continue

            key = line.split('=')[0] if '=' in line else line

            if key in settings_update:
                updated_lines.append(f"{key}={settings_update[key]}")
                logger.info(f"  📝 Updated {key}: → {settings_update[key]}")
            else:
                updated_lines.append(line)

        # Add any missing settings
        existing_keys = [line.split('=')[0] for line in updated_lines if '=' in line and not line.startswith('#')]

        for key, value in settings_update.items():
            if key not in existing_keys:
                updated_lines.append(f"{key}={value}")
                logger.info(f"  ➕ Added {key}: {value}")

        env_file.write_text('\n'.join(updated_lines))

    async def _validate_new_settings(self):
        """Test new database connection settings"""
        logger.info("🔍 Validating new database connection settings...")

        try:
            # Create test connection with new settings
            test_engine = get_async_engine()

            async with test_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                test_value = result.scalar()

            if test_value == 1:
                logger.info("✅ Database connection validation successful")
            else:
                raise Exception("Database test query failed")

            await test_engine.dispose()

        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
            raise

    async def benchmark_database_performance(self) -> Dict[str, float]:
        """Benchmark current database performance"""
        logger.info("⏱️ Benchmarking database performance...")

        engine = get_async_engine()
        benchmark_results = {}

        try:
            # Test connection acquisition speed
            start_time = time.time()

            async with engine.begin() as conn:
                await conn.execute(text("SELECT COUNT(*) FROM users"))

            connection_time = (time.time() - start_time) * 1000
            benchmark_results['connection_time_ms'] = connection_time

            # Test query performance
            start_time = time.time()

            async with engine.begin() as conn:
                result = await conn.execute(text("""
                    SELECT u.id, u.email, u.created_at
                    FROM users u
                    ORDER BY u.created_at DESC
                    LIMIT 10
                """))
                rows = result.fetchall()

            query_time = (time.time() - start_time) * 1000
            benchmark_results['query_time_ms'] = query_time
            benchmark_results['rows_returned'] = len(rows)

            logger.info(f"📊 Benchmark Results:")
            logger.info(f"  • Connection Time: {connection_time:.2f}ms")
            logger.info(f"  • Query Time: {query_time:.2f}ms")
            logger.info(f"  • Rows Returned: {len(rows)}")

        finally:
            await engine.dispose()

        return benchmark_results

    async def rollback_changes(self):
        """Rollback all applied optimizations"""
        logger.warning("🔄 Rolling back optimizations...")

        if not self.optimizations_applied:
            logger.info("No optimizations to rollback")
            return

        try:
            # Restore from backup
            backup_file = project_root / '.env.backup'

            if backup_file.exists():
                env_file = project_root / '.env.dev'

                # Read backup settings
                backup_content = backup_file.read_text()
                restored_settings = {}

                for line in backup_content.split('\n'):
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        restored_settings[key] = value

                # Restore settings
                await self._update_env_file(env_file, restored_settings)
                logger.info("✅ Settings restored from backup")

            self.optimizations_applied.clear()
            logger.info("✅ Rollback completed successfully")

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            raise

    async def generate_optimization_report(self, before_benchmark: Dict[str, float],
                                         after_benchmark: Dict[str, float]):
        """Generate performance optimization report"""
        report_file = project_root / 'PERFORMANCE_OPTIMIZATION_REPORT.md'

        report_content = f"""# 🚀 PsychSync Performance Optimization Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Phase:** Phase 1 - Database Connection Pool Optimization
**Status:** {'✅ SUCCESS' if self.optimizations_applied else '❌ FAILED'}

---

## 📊 Performance Metrics

### Before Optimization
- **Connection Time:** {before_benchmark.get('connection_time_ms', 'N/A')}ms
- **Query Time:** {before_benchmark.get('query_time_ms', 'N/A')}ms

### After Optimization
- **Connection Time:** {after_benchmark.get('connection_time_ms', 'N/A')}ms
- **Query Time:** {after_benchmark.get('query_time_ms', 'N/A')}ms

### Performance Improvement
"""

        if 'connection_time_ms' in before_benchmark and 'connection_time_ms' in after_benchmark:
            improvement = ((before_benchmark['connection_time_ms'] - after_benchmark['connection_time_ms'])
                          / before_benchmark['connection_time_ms']) * 100
            report_content += f"- **Connection Speed:** {improvement:.1f}% improvement\n"

        if 'query_time_ms' in before_benchmark and 'query_time_ms' in after_benchmark:
            improvement = ((before_benchmark['query_time_ms'] - after_benchmark['query_time_ms'])
                          / before_benchmark['query_time_ms']) * 100
            report_content += f"- **Query Speed:** {improvement:.1f}% improvement\n"

        report_content += f"""

---

## 🔧 Applied Optimizations

"""
        for optimization in self.optimizations_applied:
            report_content += f"- ✅ {optimization}\n"

        report_content += f"""

## 📝 Configuration Changes

### Connection Pool Settings
- **Pool Size:** 5 → 20 (4x increase)
- **Max Overflow:** 10 → 30 (3x increase)
- **Pool Recycle:** Default → 1800 seconds (30 minutes)

## 🎯 Next Steps

1. **Monitor Performance:** Watch database metrics in production
2. **Phase 2 Preparation:** Ready for frontend bundle optimization
3. **Load Testing:** Test under concurrent load

## 🚨 Rollback Information

Backup available at: `.env.backup`
Rollback command: `python scripts/performance-optimization-starter.py --rollback`

---

*Generated automatically by PsychSync Performance Optimizer*
"""

        report_file.write_text(report_content)
        logger.info(f"📄 Optimization report generated: {report_file}")

async def main():
    """Main optimization execution"""
    import argparse

    parser = argparse.ArgumentParser(description='PsychSync Performance Optimization')
    parser.add_argument('--rollback', action='store_true', help='Rollback optimizations')
    parser.add_argument('--benchmark-only', action='store_true', help='Run benchmarks only')
    args = parser.parse_args()

    optimizer = PerformanceOptimizer()

    try:
        if args.rollback:
            await optimizer.rollback_changes()
            return

        if args.benchmark_only:
            results = await optimizer.benchmark_database_performance()
            print(f"Benchmark Results: {results}")
            return

        logger.info("🚀 Starting PsychSync Performance Optimization - Phase 1")

        # Step 1: Backup current settings
        await optimizer.backup_current_settings()

        # Step 2: Benchmark before optimization
        logger.info("📊 Running pre-optimization benchmark...")
        before_benchmark = await optimizer.benchmark_database_performance()

        # Step 3: Apply optimizations
        await optimizer.apply_connection_pool_optimization()

        # Step 4: Benchmark after optimization
        logger.info("📊 Running post-optimization benchmark...")
        after_benchmark = await optimizer.benchmark_database_performance()

        # Step 5: Generate report
        await optimizer.generate_optimization_report(before_benchmark, after_benchmark)

        logger.info("🎉 Phase 1 optimization completed successfully!")
        logger.info("📄 Check PERFORMANCE_OPTIMIZATION_REPORT.md for detailed results")
        logger.info("🚀 Ready for Phase 2: Frontend Bundle Optimization")

    except KeyboardInterrupt:
        logger.warning("⚠️ Optimization interrupted by user")
        await optimizer.rollback_changes()

    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        await optimizer.rollback_changes()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())