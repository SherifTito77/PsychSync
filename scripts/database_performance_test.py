#!/usr/bin/env python3
"""
Database Performance Testing Script
Tests database performance under various load conditions
"""

import time
import asyncio
import psycopg2
import psycopg2.extras
import statistics
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import string


class DatabasePerformanceTester:
    """Comprehensive database performance testing"""

    def __init__(self, host='localhost', port=5432, database='psychsync_test',
                 user='postgres', password='postgres'):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.test_results = []

    def create_connection(self):
        """Create database connection"""
        return psycopg2.connect(**self.connection_params)

    def setup_test_environment(self):
        """Set up test environment with sample data"""
        print("🔧 Setting up test environment...")

        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                # Create test tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_test_users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE,
                        full_name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT NOW(),
                        metadata JSONB
                    );
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_test_responses (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES performance_test_users(id),
                        assessment_data JSONB,
                        score FLOAT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)

                # Create indexes for performance testing
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email ON performance_test_users(email);
                    CREATE INDEX IF NOT EXISTS idx_responses_user_id ON performance_test_responses(user_id);
                    CREATE INDEX IF NOT EXISTS idx_responses_created_at ON performance_test_responses(created_at);
                """)

                conn.commit()

        print("✅ Test environment setup complete")

    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("🧹 Cleaning up test environment...")

        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS performance_test_responses;")
                cursor.execute("DROP TABLE IF EXISTS performance_test_users;")
                conn.commit()

        print("✅ Test environment cleanup complete")

    def generate_test_data(self, num_users=1000, responses_per_user=10):
        """Generate test data for performance testing"""
        print(f"📊 Generating test data: {num_users} users, {responses_per_user} responses per user...")

        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                # Generate users
                users_data = []
                for i in range(num_users):
                    users_data.append((
                        f"test{i}@example.com",
                        f"Test User {i}",
                        json.dumps({'department': random.choice(['HR', 'Engineering', 'Sales', 'Marketing']),
                                  'role': random.choice(['Manager', 'Employee', 'Team Lead'])})
                    ))

                # Batch insert users
                psycopg2.extras.execute_batch(
                    cursor,
                    "INSERT INTO performance_test_users (email, full_name, metadata) VALUES (%s, %s, %s)",
                    users_data
                )

                # Get user IDs
                cursor.execute("SELECT id FROM performance_test_users ORDER BY id")
                user_ids = [row[0] for row in cursor.fetchall()]

                # Generate responses
                responses_data = []
                for user_id in user_ids:
                    for _ in range(responses_per_user):
                        responses_data.append((
                            user_id,
                            json.dumps({
                                'big_five': {trait: random.uniform(1, 5) for trait in ['O', 'C', 'E', 'A', 'N']},
                                'mbti': random.choice(['INTJ', 'ENFP', 'ISTJ', 'ENTP']),
                                'questions_answered': random.randint(50, 200)
                            }),
                            random.uniform(0, 100)
                        ))

                # Batch insert responses
                psycopg2.extras.execute_batch(
                    cursor,
                    "INSERT INTO performance_test_responses (user_id, assessment_data, score) VALUES (%s, %s, %s)",
                    responses_data
                )

                conn.commit()

        print("✅ Test data generation complete")
        return user_ids

    def test_query_performance(self, query: str, description: str, iterations: int = 100) -> Dict[str, Any]:
        """Test performance of a specific query"""
        print(f"🔍 Testing query: {description}")

        execution_times = []

        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                # Warm up
                cursor.execute(query)
                cursor.fetchall()

                # Performance test
                for _ in range(iterations):
                    start_time = time.time()
                    cursor.execute(query)
                    results = cursor.fetchall()
                    end_time = time.time()

                    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    execution_times.append(execution_time)

        result_stats = {
            'description': description,
            'query': query,
            'iterations': iterations,
            'avg_time_ms': statistics.mean(execution_times),
            'median_time_ms': statistics.median(execution_times),
            'min_time_ms': min(execution_times),
            'max_time_ms': max(execution_times),
            'std_dev_ms': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'p95_time_ms': sorted(execution_times)[int(0.95 * len(execution_times))] if execution_times else 0,
            'p99_time_ms': sorted(execution_times)[int(0.99 * len(execution_times))] if execution_times else 0
        }

        print(f"  ⏱️  Avg: {result_stats['avg_time_ms']:.2f}ms, "
              f"P95: {result_stats['p95_time_ms']:.2f}ms, "
              f"Max: {result_stats['max_time_ms']:.2f}ms")

        return result_stats

    def test_concurrent_access(self, num_threads=10, queries_per_thread=20) -> Dict[str, Any]:
        """Test database performance under concurrent access"""
        print(f"🚀 Testing concurrent access: {num_threads} threads, {queries_per_thread} queries/thread")

        def worker_query():
            """Worker function for concurrent testing"""
            queries = [
                "SELECT COUNT(*) FROM performance_test_users;",
                "SELECT COUNT(*) FROM performance_test_responses;",
                "SELECT AVG(score) FROM performance_test_responses;",
                """
                SELECT u.full_name, COUNT(r.id) as response_count
                FROM performance_test_users u
                LEFT JOIN performance_test_responses r ON u.id = r.user_id
                GROUP BY u.id, u.full_name
                ORDER BY response_count DESC
                LIMIT 10;
                """
            ]

            times = []
            with self.create_connection() as conn:
                with conn.cursor() as cursor:
                    for _ in range(queries_per_thread):
                        query = random.choice(queries)
                        start_time = time.time()
                        cursor.execute(query)
                        cursor.fetchall()
                        end_time = time.time()
                        times.append((end_time - start_time) * 1000)

            return times

        # Execute concurrent queries
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_query) for _ in range(num_threads)]
            all_times = []

            for future in as_completed(futures):
                try:
                    times = future.result()
                    all_times.extend(times)
                except Exception as e:
                    print(f"❌ Error in worker: {e}")

        concurrent_stats = {
            'type': 'concurrent_access',
            'num_threads': num_threads,
            'queries_per_thread': queries_per_thread,
            'total_queries': len(all_times),
            'avg_time_ms': statistics.mean(all_times),
            'median_time_ms': statistics.median(all_times),
            'p95_time_ms': sorted(all_times)[int(0.95 * len(all_times))] if all_times else 0,
            'p99_time_ms': sorted(all_times)[int(0.99 * len(all_times))] if all_times else 0,
            'throughput_qps': len(all_times) / (max(all_times) / 1000) if all_times else 0
        }

        print(f"  📊 Concurrent: {concurrent_stats['avg_time_ms']:.2f}ms avg, "
              f"{concurrent_stats['throughput_qps']:.1f} QPS")

        return concurrent_stats

    def test_write_performance(self, batch_sizes: List[int] = [1, 10, 100, 1000]) -> List[Dict[str, Any]]:
        """Test write performance with different batch sizes"""
        print("✍️  Testing write performance...")

        write_results = []

        for batch_size in batch_sizes:
            print(f"  📝 Testing batch size: {batch_size}")

            # Generate test data
            test_data = []
            for i in range(batch_size):
                test_data.append((
                    f"write_test_{batch_size}_{i}@example.com",
                    f"Write Test User {batch_size}-{i}",
                    json.dumps({'batch_size': batch_size, 'index': i})
                ))

            # Test write performance
            times = []
            for _ in range(10):  # 10 iterations per batch size
                with self.create_connection() as conn:
                    with conn.cursor() as cursor:
                        start_time = time.time()

                        # Insert and then cleanup
                        psycopg2.extras.execute_batch(
                            cursor,
                            "INSERT INTO performance_test_users (email, full_name, metadata) VALUES (%s, %s, %s)",
                            test_data
                        )

                        # Get inserted IDs for cleanup
                        cursor.execute("""
                            SELECT id FROM performance_test_users
                            WHERE email LIKE 'write_test_%'
                        """)
                        ids = [row[0] for row in cursor.fetchall()]

                        # Cleanup
                        cursor.execute("DELETE FROM performance_test_users WHERE id = ANY(%s)", (ids,))

                        conn.commit()

                        end_time = time.time()
                        times.append((end_time - start_time) * 1000)

            write_stats = {
                'type': 'write_performance',
                'batch_size': batch_size,
                'iterations': 10,
                'avg_time_ms': statistics.mean(times),
                'throughput_records_per_second': (batch_size * 10) / (sum(times) / 1000)
            }

            write_results.append(write_stats)
            print(f"    ⏱️  {write_stats['avg_time_ms']:.2f}ms avg, "
                  f"{write_stats['throughput_records_per_second']:.1f} records/sec")

        return write_results

    def analyze_query_execution_plan(self, query: str) -> Dict[str, Any]:
        """Analyze query execution plan"""
        print(f"📈 Analyzing execution plan for: {query[:50]}...")

        with self.create_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
                result = cursor.fetchone()

                plan_data = result[0][0]  # Get the JSON plan

                # Extract key metrics
                plan_analysis = {
                    'query': query,
                    'total_cost': plan_data['Execution Time'],
                    'planning_time': plan_data.get('Planning Time', 0),
                    'execution_time': plan_data['Execution Time'],
                    'actual_rows': plan_data['Plan']['Actual Rows'],
                    'total_cost_planned': plan_data['Plan']['Total Cost'],
                    'plan_depth': self._calculate_plan_depth(plan_data['Plan']),
                    'uses_index': self._check_index_usage(plan_data['Plan'])
                }

                print(f"  💰 Cost: {plan_analysis['total_cost']:.2f}, "
                      f"⏱️  Time: {plan_analysis['execution_time']:.2f}ms, "
                      f"📊 Rows: {plan_analysis['actual_rows']}")

                return plan_analysis

    def _calculate_plan_depth(self, plan: Dict) -> int:
        """Calculate the depth of query plan"""
        if 'Plans' not in plan:
            return 1
        if not plan['Plans']:
            return 1
        return 1 + max(self._calculate_plan_depth(subplan) for subplan in plan['Plans'])

    def _check_index_usage(self, plan: Dict) -> bool:
        """Check if plan uses indexes"""
        if 'Node Type' in plan and plan['Node Type'] in ['Index Scan', 'Index Only Scan']:
            return True
        if 'Plans' in plan:
            return any(self._check_index_usage(subplan) for subplan in plan['Plans'])
        return False

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive database performance test"""
        print("🧪 Running comprehensive database performance test...")
        print("=" * 60)

        start_time = datetime.now()

        try:
            # Setup
            self.setup_test_environment()
            user_ids = self.generate_test_data(1000, 5)

            # Test various queries
            query_tests = [
                ("SELECT COUNT(*) FROM performance_test_users;", "Count users"),
                ("SELECT COUNT(*) FROM performance_test_responses;", "Count responses"),
                ("SELECT AVG(score) FROM performance_test_responses;", "Average score"),
                ("""
                SELECT u.full_name, COUNT(r.id) as response_count
                FROM performance_test_users u
                LEFT JOIN performance_test_responses r ON u.id = r.user_id
                GROUP BY u.id, u.full_name
                ORDER BY response_count DESC
                LIMIT 10;
                """, "Top users by responses"),
                ("""
                SELECT
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as responses
                FROM performance_test_responses
                GROUP BY hour
                ORDER BY hour DESC
                LIMIT 24;
                """, "Hourly response distribution"),
                ("""
                SELECT
                    metadata->>'department' as dept,
                    AVG(r.score) as avg_score,
                    COUNT(r.id) as response_count
                FROM performance_test_users u
                LEFT JOIN performance_test_responses r ON u.id = r.user_id
                GROUP BY dept;
                """, "Department performance analysis"),
                ("""
                SELECT
                    u.id,
                    u.full_name,
                    AVG(r.score) OVER (PARTITION BY u.id) as avg_user_score
                FROM performance_test_users u
                LEFT JOIN performance_test_responses r ON u.id = r.user_id
                WHERE u.id IN (SELECT id FROM performance_test_responses LIMIT 100);
                """, "Window function query")
            ]

            print("\n📊 Query Performance Tests:")
            print("-" * 40)
            query_results = []
            for query, description in query_tests:
                result = self.test_query_performance(query, description, iterations=50)
                query_results.append(result)
                self.test_results.append(result)

            # Execution plan analysis
            print("\n📈 Execution Plan Analysis:")
            print("-" * 40)
            plan_results = []
            for query, description in query_tests[:3]:  # Analyze first 3 queries
                plan_analysis = self.analyze_query_execution_plan(query)
                plan_analysis['description'] = description
                plan_results.append(plan_analysis)

            # Concurrent access test
            print("\n🚀 Concurrent Access Tests:")
            print("-" * 40)
            concurrent_results = []
            for threads in [5, 10, 20]:
                result = self.test_concurrent_access(num_threads=threads, queries_per_thread=20)
                concurrent_results.append(result)

            # Write performance test
            print("\n✍️  Write Performance Tests:")
            print("-" * 40)
            write_results = self.test_write_performance()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Generate comprehensive report
            report = {
                'test_session': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': duration,
                    'database_info': self.connection_params
                },
                'query_performance': query_results,
                'execution_plans': plan_results,
                'concurrent_access': concurrent_results,
                'write_performance': write_results,
                'summary': {
                    'avg_query_time_ms': statistics.mean([r['avg_time_ms'] for r in query_results]),
                    'slowest_query': max(query_results, key=lambda x: x['avg_time_ms'])['description'],
                    'fastest_query': min(query_results, key=lambda x: x['avg_time_ms'])['description'],
                    'max_concurrent_throughput': max([r['throughput_qps'] for r in concurrent_results]),
                    'optimal_batch_size': max(write_results, key=lambda x: x['throughput_records_per_second'])['batch_size']
                }
            }

            return report

        except Exception as e:
            print(f"❌ Error during testing: {e}")
            return {'error': str(e)}

        finally:
            self.cleanup_test_environment()

    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save performance test report"""
        if filename is None:
            filename = f"db-performance-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Database performance report saved to: {filename}")

        # Print summary
        if 'summary' in report:
            summary = report['summary']
            print(f"\n📊 Performance Test Summary:")
            print(f"  Average Query Time: {summary['avg_query_time_ms']:.2f}ms")
            print(f"  Slowest Query: {summary['slowest_query']}")
            print(f"  Fastest Query: {summary['fastest_query']}")
            print(f"  Max Concurrent Throughput: {summary['max_concurrent_throughput']:.1f} QPS")
            print(f"  Optimal Batch Size: {summary['optimal_batch_size']} records")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Database performance testing for PsychSync")
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', default='psychsync_db_perf', help='Database name')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', default='postgres', help='Database password')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--quick', action='store_true', help='Run quick performance test')

    args = parser.parse_args()

    print("🗄️  Database Performance Testing Tool")
    print("=" * 50)

    tester = DatabasePerformanceTester(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )

    try:
        if args.quick:
            print("🚀 Running quick performance test...")
            # Run a subset of tests
            tester.setup_test_environment()
            user_ids = tester.generate_test_data(100, 3)

            quick_results = []
            quick_results.append(tester.test_query_performance(
                "SELECT COUNT(*) FROM performance_test_users;", "Count users", 20))
            quick_results.append(tester.test_query_performance(
                "SELECT AVG(score) FROM performance_test_responses;", "Average score", 20))

            concurrent_result = tester.test_concurrent_access(num_threads=5, queries_per_thread=10)

            report = {
                'quick_test': True,
                'query_performance': quick_results,
                'concurrent_access': [concurrent_result],
                'timestamp': datetime.now().isoformat()
            }

            tester.cleanup_test_environment()
        else:
            report = tester.run_comprehensive_test()

        tester.save_report(report, args.output)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
