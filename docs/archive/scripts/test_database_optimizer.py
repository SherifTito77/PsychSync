#!/usr/bin/env python3
"""
Test database excellence optimizer with current setup
"""

import asyncio
import os
import sys

sys.path.append(".")

from scripts.database_excellence_optimizer import DatabaseExcellenceOptimizer


async def test_database_optimizer():
    """Test the database excellence optimizer"""
    print("🚀 Testing Database Excellence Optimizer")
    print("=" * 50)

    try:
        optimizer = DatabaseExcellenceOptimizer()

        # Initialize connection
        success = await optimizer.initialize_connection()
        if not success:
            print("❌ Failed to initialize database connection")
            return False

        print("✅ Database connection initialized")

        # Collect basic metrics
        print("📊 Collecting database metrics...")
        metrics = await optimizer.analyze_database_metrics()

        print(f"   Total Connections: {metrics.total_connections}")
        print(f"   Cache Hit Ratio: {metrics.cache_hit_ratio:.2%}")
        print(f"   Database Size: {metrics.database_size_gb:.2f}GB")
        print(f"   Index Size: {metrics.index_size_gb:.2f}GB")

        # Apply safe optimizations
        print("\n🔧 Applying safe optimizations...")
        optimization_result = await optimizer.apply_automatic_optimizations()

        print("✅ Optimizations Applied:")
        for opt in optimization_result["optimizations_applied"]:
            print(f"   • {opt}")

        if optimization_result["warnings"]:
            print("⚠️ Warnings:")
            for warning in optimization_result["warnings"]:
                print(f"   • {warning}")

        # Calculate improvement score
        if metrics.cache_hit_ratio == 0:
            print("\n📈 Improvement Potential:")
            print("   • Configure pg_stat_statements in shared_preload_libraries")
            print("   • Enable query performance monitoring")
            print("   • Expected improvement: 40-60% query performance")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_database_optimizer())
    if success:
        print("\n🎉 Database Excellence Optimizer test completed successfully!")
    else:
        print("\n💥 Database Excellence Optimizer test failed!")
    sys.exit(0 if success else 1)
