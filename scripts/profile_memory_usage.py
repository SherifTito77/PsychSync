#!/usr/bin/env python3
"""
Memory Profiling Script for Performance Analysis
Profiles memory usage patterns and identifies memory leaks
"""

import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
from datetime import datetime
from typing import Any, Dict, List

import psutil


class MemoryProfiler:
    """Advanced memory profiling utility"""

    def __init__(self, output_file: str = "memory-profile.json"):
        self.output_file = output_file
        self.snapshots = []
        self.baseline_memory = None

    def start_profiling(self):
        """Start memory profiling"""
        print("🔍 Starting memory profiling...")

        # Enable tracemalloc
        tracemalloc.start()

        # Record baseline memory
        self.baseline_memory = self._get_memory_info()
        self.snapshots.append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": "baseline",
                "memory": self.baseline_memory,
            }
        )

        print(
            f"✅ Memory profiling started. Baseline: {self.baseline_memory['rss_mb']:.1f} MB"
        )

    def take_snapshot(self, label: str = None):
        """Take a memory snapshot"""
        if not self.baseline_memory:
            raise RuntimeError("Profiling not started. Call start_profiling() first.")

        current_memory = self._get_memory_info()
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "type": "snapshot",
            "label": label,
            "memory": current_memory,
        }

        # Add memory delta
        snapshot["memory"]["delta_rss_mb"] = (
            current_memory["rss_mb"] - self.baseline_memory["rss_mb"]
        )
        snapshot["memory"]["delta_vms_mb"] = (
            current_memory["vms_mb"] - self.baseline_memory["vms_mb"]
        )

        self.snapshots.append(snapshot)

        print(
            f"📸 Memory snapshot '{label}': {current_memory['rss_mb']:.1f} MB "
            f"(Δ{snapshot['memory']['delta_rss_mb']:+.1f} MB)"
        )

    def get_tracemalloc_stats(self) -> Dict[str, Any]:
        """Get tracemalloc statistics"""
        if not tracemalloc.is_tracing():
            return {}

        current, peak = tracemalloc.get_traced_memory()

        # Get top memory allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        top_allocations = []
        for stat in top_stats[:10]:  # Top 10 allocations
            top_allocations.append(
                {
                    "filename": stat.traceback[0].filename,
                    "line": stat.traceback[0].lineno,
                    "function": stat.traceback[0].name,
                    "size": stat.size,
                    "size_mb": stat.size / (1024 * 1024),
                    "count": stat.count,
                }
            )

        return {
            "current_allocated_mb": current / (1024 * 1024),
            "peak_allocated_mb": peak / (1024 * 1024),
            "top_allocations": top_allocations,
        }

    def _get_memory_info(self) -> Dict[str, float]:
        """Get current memory information"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / (1024 * 1024),  # Resident Set Size
            "vms_mb": memory_info.vms / (1024 * 1024),  # Virtual Memory Size
            "shared_mb": memory_info.shared / (1024 * 1024),  # Shared memory
            "text_mb": memory_info.text / (1024 * 1024),  # Executable code
            "lib_mb": memory_info.lib / (1024 * 1024),  # Shared libraries
            "data_mb": memory_info.data / (1024 * 1024),  # Data + stack
            "dirty_mb": memory_info.dirty / (1024 * 1024),  # Dirty pages
            "percent": process.memory_percent(),
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory profiling report"""
        if not self.snapshots:
            return {"error": "No profiling data available"}

        tracemalloc_stats = self.get_tracemalloc_stats()

        report = {
            "profiling_session": {
                "start_time": self.snapshots[0]["timestamp"],
                "end_time": datetime.now().isoformat(),
                "total_snapshots": len(self.snapshots),
            },
            "baseline_memory": self.baseline_memory,
            "peak_memory": max(s["memory"]["rss_mb"] for s in self.snapshots),
            "memory_growth": {
                "total_growth_mb": self.snapshots[-1]["memory"]["rss_mb"]
                - self.baseline_memory["rss_mb"],
                "peak_growth_mb": max(
                    s["memory"].get("delta_rss_mb", 0) for s in self.snapshots
                ),
            },
            "tracemalloc_stats": tracemalloc_stats,
            "snapshots": self.snapshots,
        }

        # Add memory analysis
        report["analysis"] = {
            "has_memory_leak": report["memory_growth"]["total_growth_mb"]
            > 100,  # >100MB growth
            "peak_usage_excessive": report["peak_memory"] > 500,  # >500MB usage
            "growth_rate_per_minute": self._calculate_growth_rate(),
        }

        return report

    def _calculate_growth_rate(self) -> float:
        """Calculate memory growth rate per minute"""
        if len(self.snapshots) < 2:
            return 0.0

        start_time = datetime.fromisoformat(self.snapshots[0]["timestamp"])
        end_time = datetime.fromisoformat(self.snapshots[-1]["timestamp"])
        duration_minutes = (end_time - start_time).total_seconds() / 60

        if duration_minutes == 0:
            return 0.0

        growth = (
            self.snapshots[-1]["memory"]["rss_mb"]
            - self.snapshots[0]["memory"]["rss_mb"]
        )
        return growth / duration_minutes

    def save_report(self):
        """Save profiling report to file"""
        report = self.generate_report()

        with open(self.output_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Memory profiling report saved to: {self.output_file}")

        # Print summary
        print("\n📊 Memory Profiling Summary:")
        print(f"  Peak Memory: {report['peak_memory']:.1f} MB")
        print(f"  Total Growth: {report['memory_growth']['total_growth_mb']:.1f} MB")
        print(
            f"  Growth Rate: {report['analysis']['growth_rate_per_minute']:.1f} MB/min"
        )
        print(
            f"  Potential Memory Leak: {'⚠️ YES' if report['analysis']['has_memory_leak'] else '✅ NO'}"
        )

        if report["tracemalloc_stats"].get("top_allocations"):
            print("\n🔝 Top Memory Allocations:")
            for i, alloc in enumerate(
                report["tracemalloc_stats"]["top_allocations"][:3], 1
            ):
                print(
                    f"  {i}. {alloc['filename']}:{alloc['line']} - {alloc['size_mb']:.1f} MB ({alloc['count']} objects)"
                )


def profile_fastapi_app():
    """Profile FastAPI application memory usage"""
    profiler = MemoryProfiler("fastapi-memory-profile.json")

    try:
        profiler.start_profiling()

        # Simulate application load
        print("\n🚀 Simulating FastAPI application load...")

        # Initial startup
        profiler.take_snapshot("app_startup")

        # Import and initialize FastAPI components
        import time

        time.sleep(2)  # Simulate startup time

        profiler.take_snapshot("dependencies_loaded")

        # Simulate processing requests
        print("\n📈 Simulating request processing...")
        for i in range(10):
            # Simulate request processing
            dummy_data = []
            for j in range(1000):
                dummy_data.append(
                    {
                        "id": j,
                        "data": "x" * 100,  # 100 bytes per record
                        "timestamp": time.time(),
                    }
                )

            if i % 3 == 0:
                profiler.take_snapshot(f"request_batch_{i}")

            # Clear some data to simulate cleanup
            if i % 5 == 0:
                dummy_data = dummy_data[:100]
                gc.collect()

            time.sleep(0.1)

        profiler.take_snapshot("after_request_simulation")

        # Simulate memory stress test
        print("\n💪 Running memory stress test...")
        large_objects = []
        for i in range(100):
            # Create large objects to stress test
            large_obj = {
                "data": "x" * (1024 * 1024),  # 1MB
                "metadata": {f"field_{j}": "value" * 100 for j in range(10)},
            }
            large_objects.append(large_obj)

            if i % 20 == 0:
                profiler.take_snapshot(f"stress_test_{i}")

        profiler.take_snapshot("after_stress_test")

        # Clean up large objects
        large_objects.clear()
        gc.collect()
        profiler.take_snapshot("after_cleanup")

    except Exception as e:
        print(f"❌ Error during profiling: {e}")
        return

    finally:
        profiler.save_report()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Memory profiling for PsychSync application"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="memory-profile.json",
        help="Output file for profiling report",
    )
    parser.add_argument(
        "--duration", "-d", type=int, default=60, help="Profiling duration in seconds"
    )
    parser.add_argument(
        "--fastapi",
        action="store_true",
        help="Profile FastAPI application specifically",
    )

    args = parser.parse_args()

    print("🧠 Memory Profiling Tool")
    print("=" * 50)

    if args.fastjson:
        profile_fastapi_app()
    else:
        # Generic memory profiling
        profiler = MemoryProfiler(args.output)
        profiler.start_profiling()

        try:
            # Run profiling for specified duration
            start_time = time.time()
            snapshot_interval = 10  # seconds

            while time.time() - start_time < args.duration:
                time.sleep(snapshot_interval)
                elapsed = time.time() - start_time
                profiler.take_snapshot(f"t{elapsed:.0f}s")

        except KeyboardInterrupt:
            print("\n⏹️ Profiling interrupted by user")

        finally:
            profiler.save_report()


if __name__ == "__main__":
    main()
