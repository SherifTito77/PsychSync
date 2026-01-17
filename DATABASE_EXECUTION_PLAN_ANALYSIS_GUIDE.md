# Database Execution Plan Analysis Guide

## Overview

This guide provides comprehensive instructions for analyzing PostgreSQL query execution plans to identify performance bottlenecks and optimize database queries in the PsychSync application.

## 1. Understanding Query Execution Plans

### 1.1 What is an Execution Plan?

An execution plan is PostgreSQL's roadmap for executing a query. It shows:
- **How** PostgreSQL will access data (index scans vs sequential scans)
- **In what order** operations will be performed
- **How much data** will be processed at each step
- **What operations** (joins, sorts, aggregations) will be performed

### 1.2 Types of Execution Plans

#### **EXPLAIN** - Estimated Plan
```sql
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
```
- Shows estimated execution plan
- No actual query execution
- Fast but may be inaccurate for complex queries

#### **EXPLAIN ANALYZE** - Actual Execution Plan
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```
- Shows actual execution with real performance metrics
- Executes the query (use with caution on production)
- Provides timing and row count information

#### **EXPLAIN ANALYZE BUFFERS** - Detailed Buffer Information
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT * FROM users WHERE email = 'test@example.com';
```
- Includes buffer cache information
- Shows disk vs memory usage
- Best for performance tuning

## 2. Reading Execution Plans

### 2.1 Execution Plan Structure

Execution plans are tree structures read from **bottom to top**:

```
->  Nested Loop  (cost=100.00..500.00 rows=1000 width=200) (actual time=2.345..123.456 rows=1000 loops=1)
     ->  Index Scan using idx_users_org_active on users  (cost=0.42..50.00 rows=100 width=100) (actual time=0.123..45.678 rows=100 loops=1)
           Index Cond: (organization_id = 'uuid'::uuid)
     ->  Index Scan using idx_responses_assessment_user on responses  (cost=0.42..3.50 rows=10 width=100) (actual time=0.234..0.567 rows=10 loops=100)
           Index Cond: (assessment_id = users.id)
```

**Reading Order:**
1. Bottom: Index Scan on users (find users)
2. Middle: Index Scan on responses (for each user, find their responses)
3. Top: Nested Loop (combine results)

### 2.2 Key Plan Elements

#### **Cost Information**
- `Startup Cost`: Cost before producing first row
- `Total Cost`: Total cost to produce all rows
- **Lower is better**. Relative values matter more than absolute.

#### **Row Estimates**
- `Plan Rows`: Estimated number of rows
- `Actual Rows`: Actual number of rows (with ANALYZE)
- Large discrepancies indicate statistics problems.

#### **Timing Information**
- `Actual Time`: Time in milliseconds
- First value: time to first row
- Second value: time to complete operation

## 3. Common Performance Issues in Plans

### 3.1 Sequential Scans (Seq Scan)

#### **Problematic Example:**
```
Seq Scan on responses  (cost=0.00..5000.00 rows=100000 width=200) (actual time=0.123..1234.567 rows=100000 loops=1)
  Filter: (score > 0.8)
```

**Issues:**
- Table scan instead of index usage
- Expensive for large tables
- Processes all rows even with filters

**Solutions:**
1. **Add Index:**
```sql
CREATE INDEX CONCURRENTLY idx_responses_score ON responses (score) WHERE score > 0.8;
```

2. **Rewrite Query:**
```sql
-- Before (inefficient)
SELECT * FROM responses WHERE score > 0.8;

-- After (with partial index)
SELECT * FROM responses WHERE score > 0.8;  -- Now uses index
```

### 3.2 Inefficient Joins

#### **Problematic Example:**
```
Hash Join  (cost=10000.00..50000.00 rows=50000 width=300) (actual time=500.123..2000.456 rows=50000 loops=1)
  Hash Cond: (responses.user_id = users.id)
  ->  Seq Scan on responses  (cost=0.00..8000.00 rows=200000 width=150)
  ->  Hash  (cost=5000.00..5000.00 rows=100000 width=150)
        ->  Seq Scan on users  (cost=0.00..5000.00 rows=100000 width=150)
```

**Issues:**
- Sequential scans on both tables
- Expensive hash operation
- Large memory usage

**Solutions:**
1. **Add Composite Indexes:**
```sql
CREATE INDEX CONCURRENTLY idx_responses_user_assessment ON responses (user_id, assessment_id);
CREATE INDEX CONCURRENTLY idx_users_org_active ON users (organization_id, is_active);
```

2. **Use Nested Loop with Indexes:**
```sql
-- Query that uses efficient nested loop
SELECT u.*, r.*
FROM users u
JOIN responses r ON u.id = r.user_id
WHERE u.organization_id = 'uuid'
  AND r.assessment_id = 'assessment_uuid';
```

### 3.3 Expensive Sort Operations

#### **Problematic Example:**
```
Sort  (cost=10000.00..15000.00 rows=100000 width=200) (actual time=1000.123..2500.456 rows=100000 loops=1)
  Sort Key: created_at DESC
  ->  Seq Scan on assessments  (cost=0.00..8000.00 rows=100000 width=200)
```

**Issues:**
- Sorting large result sets
- No index covering ORDER BY
- Memory-intensive operation

**Solutions:**
1. **Add Index with ORDER BY:**
```sql
CREATE INDEX CONCURRENTLY idx_assessments_user_created_desc
ON assessments (user_id, created_at DESC);
```

2. **Use Keyset Pagination:**
```sql
-- Instead of OFFSET/LIMIT
SELECT * FROM assessments
WHERE user_id = 'uuid' AND created_at < '2023-12-01T00:00:00Z'
ORDER BY created_at DESC
LIMIT 50;
```

### 3.4 N+1 Query Problems

#### **Problematic Pattern:**
```python
# This generates N+1 queries
for user in users:
    responses = get_user_responses(user.id)  # Separate query for each user
```

**In Execution Plans:**
Multiple similar plans showing repeated access patterns:
```
Index Scan using idx_responses_user ON responses (cost=0.42..3.50 rows=10 width=100)
  Index Cond: (user_id = 'user_1_uuid')

Index Scan using idx_responses_user ON responses (cost=0.42..3.50 rows=10 width=100)
  Index Cond: (user_id = 'user_2_uuid')

... (repeated N times)
```

**Solutions:**
```python
# Single query with join
query = select(User, Response).join(Response, User.id == Response.user_id)
```

## 4. Advanced Analysis Techniques

### 4.1 Using JSON Format Analysis

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT u.*, COUNT(r.id) as response_count
FROM users u
LEFT JOIN responses r ON u.id = r.user_id
WHERE u.organization_id = 'uuid'
GROUP BY u.id;
```

**Python Analysis Function:**
```python
import json
import matplotlib.pyplot as plt

def analyze_execution_plan_json(plan_data):
    """Analyze JSON execution plan with detailed metrics"""

    def analyze_node(node, depth=0):
        metrics = {
            'node_type': node.get('Node Type'),
            'cost': node.get('Total Cost', 0),
            'actual_time': node.get('Actual Total Time', 0),
            'rows': node.get('Actual Rows', 0),
            'depth': depth,
            'buffers': node.get('Buffers', {}),
            'issues': []
        }

        # Check for common issues
        if node.get('Node Type') == 'Seq Scan':
            if metrics['rows'] > 10000:
                metrics['issues'].append('Large sequential scan')

        if node.get('Node Type') == 'Sort':
            if metrics['actual_time'] > 1000:
                metrics['issues'].append('Expensive sort operation')

        if node.get('Node Type') == 'Hash Join':
            if metrics['actual_time'] > 2000:
                metrics['issues'].append('Expensive hash join')

        # Recursively analyze child nodes
        child_metrics = []
        for plan in node.get('Plans', []):
            child_metrics.extend(analyze_node(plan, depth + 1))

        return [metrics] + child_metrics

    # Analyze all nodes
    all_metrics = analyze_node(plan_data[0]['Plan'])

    # Find most expensive operations
    expensive_ops = sorted(
        [m for m in all_metrics if m['actual_time'] > 100],
        key=lambda x: x['actual_time'],
        reverse=True
    )

    return {
        'total_nodes': len(all_metrics),
        'max_depth': max(m['depth'] for m in all_metrics),
        'most_expensive': expensive_ops[:5],
        'total_time': sum(m['actual_time'] for m in all_metrics),
        'issues': [issue for m in all_metrics for issue in m['issues']]
    }

# Usage example:
async def get_detailed_analysis(db: AsyncSession, query):
    plan_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
    result = await db.execute(plan_query)
    plan_data = result.scalar()

    analysis = analyze_execution_plan_json(plan_data)
    return analysis
```

### 4.2 Buffer Analysis

**Understanding Buffer Information:**
```
Buffers: shared hit=1000 read=500 written=10, temp read=200 written=50
```

- **shared hit**: Blocks found in shared cache (good)
- **shared read**: Blocks read from disk (expensive)
- **temp read/write**: Temporary disk usage (bad - indicates memory issues)

**Ideal Scenario:**
```
Buffers: shared hit=5000
```

**Problematic Scenario:**
```
Buffers: shared hit=100 read=4900 temp written=1000
```

### 4.3 Timing Analysis

**Identifying Bottlenecks by Time:**

```sql
EXPLAIN (ANALYZE, TIMING OFF)  -- Disable timing for faster execution
```

**Time-based Analysis Script:**
```python
def identify_timing_bottlenecks(plan_data):
    """Identify operations taking the most time"""

    timing_data = []

    def extract_timing(node, path=""):
        if node.get('Actual Total Time'):
            timing_data.append({
                'path': path,
                'node_type': node.get('Node Type'),
                'time': node.get('Actual Total Time'),
                'percent_of_total': 0  # Will be calculated
            })

        for i, plan in enumerate(node.get('Plans', [])):
            extract_timing(plan, f"{path} -> Node {i}")

    extract_timing(plan_data[0]['Plan'])

    # Calculate percentages
    total_time = max(item['time'] for item in timing_data)
    for item in timing_data:
        item['percent_of_total'] = (item['time'] / total_time) * 100

    # Sort by time (descending)
    return sorted(timing_data, key=lambda x: x['time'], reverse=True)

# Usage:
timing_bottlenecks = identify_timing_bottlenecks(plan_data)
top_bottlenecks = timing_bottlenecks[:10]  # Top 10 bottlenecks
```

## 5. Performance Monitoring Implementation

### 5.1 Automated Query Analysis

```python
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, List
import time

logger = logging.getLogger(__name__)

class QueryPerformanceMonitor:
    """Monitor and analyze query performance automatically"""

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold = slow_query_threshold_ms
        self.query_stats: Dict[str, List[float]] = {}

    @asynccontextmanager
    async def monitor_query(self, db: AsyncSession, query_name: str):
        """Context manager to monitor query performance"""

        start_time = time.time()

        try:
            yield
        finally:
            execution_time = (time.time() - start_time) * 1000

            # Record execution time
            if query_name not in self.query_stats:
                self.query_stats[query_name] = []

            self.query_stats[query_name].append(execution_time)

            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(
                    f"Slow query detected: {query_name}",
                    extra={
                        "execution_time_ms": execution_time,
                        "threshold_ms": self.slow_query_threshold,
                        "query_name": query_name
                    }
                )

    async def analyze_slow_query(
        self,
        db: AsyncSession,
        query,
        query_name: str
    ) -> Dict[str, any]:
        """Analyze a specific slow query in detail"""

        # Get execution plan
        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))

        explain_query = text(f"""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            {query_str}
        """)

        result = await db.execute(explain_query)
        plan_data = result.scalar()

        # Analyze the plan
        analysis = analyze_execution_plan_json(plan_data)

        return {
            'query_name': query_name,
            'query': query_str,
            'execution_plan': plan_data,
            'analysis': analysis,
            'recommendations': self._generate_recommendations(analysis)
        }

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate optimization recommendations based on analysis"""

        recommendations = []

        # Check for sequential scans
        if any('sequential scan' in issue.lower() for issue in analysis['issues']):
            recommendations.append(
                "Consider adding indexes for tables with sequential scans"
            )

        # Check for expensive sorts
        if any('sort' in issue.lower() for issue in analysis['issues']):
            recommendations.append(
                "Consider adding indexes to cover ORDER BY clauses or using keyset pagination"
            )

        # Check for expensive joins
        if any('hash join' in issue.lower() for issue in analysis['issues']):
            recommendations.append(
                "Consider optimizing join conditions or adding composite indexes"
            )

        # Check total execution time
        if analysis['total_time'] > 5000:  # 5 seconds
            recommendations.append(
                "Query execution time is very high. Consider query rewriting or data partitioning"
            )

        return recommendations

    def get_performance_stats(self) -> Dict[str, any]:
        """Get performance statistics for all monitored queries"""

        stats = {}

        for query_name, times in self.query_stats.items():
            if times:
                stats[query_name] = {
                    'count': len(times),
                    'avg_time_ms': sum(times) / len(times),
                    'min_time_ms': min(times),
                    'max_time_ms': max(times),
                    'p95_time_ms': sorted(times)[int(len(times) * 0.95)],
                    'slow_queries': sum(1 for t in times if t > self.slow_query_threshold)
                }

        return stats

# Usage example:
monitor = QueryPerformanceMonitor(slow_query_threshold_ms=100.0)

# In your service functions:
async def get_users_with_monitoring(db: AsyncSession, organization_id: UUID):
    async with monitor.monitor_query(db, "get_users_by_organization"):
        # Your existing query logic
        query = select(User).where(User.organization_id == organization_id)
        result = await db.execute(query)
        return result.scalars().all()

# Periodic analysis:
async def periodic_performance_check(db: AsyncSession):
    # Get all slow queries from monitoring data
    stats = monitor.get_performance_stats()

    for query_name, stat in stats.items():
        if stat['avg_time_ms'] > 200:  # Average > 200ms
            # Get the actual query and analyze it
            query = get_query_by_name(query_name)  # You need to implement this

            detailed_analysis = await monitor.analyze_slow_query(
                db, query, query_name
            )

            logger.error(
                f"Performance issue detected in {query_name}",
                extra=detailed_analysis
            )
```

### 5.2 Integration with Service Layer

```python
# In your service base class
class OptimizedService:
    """Base service class with built-in performance monitoring"""

    def __init__(self):
        self.monitor = QueryPerformanceMonitor()

    async def execute_query_with_analysis(
        self,
        db: AsyncSession,
        query,
        query_name: str,
        analyze_if_slow: bool = True
    ):
        """Execute query with automatic performance analysis"""

        async with self.monitor.monitor_query(db, query_name):
            start_time = time.time()
            result = await db.execute(query)
            execution_time = (time.time() - start_time) * 1000

        # Analyze slow queries
        if analyze_if_slow and execution_time > self.monitor.slow_query_threshold:
            try:
                analysis = await self.monitor.analyze_slow_query(db, query, query_name)
                logger.warning(
                    f"Query optimization needed: {query_name}",
                    extra=analysis
                )
            except Exception as e:
                logger.error(f"Failed to analyze query {query_name}: {e}")

        return result

# Usage in user service:
class OptimizedUserService(OptimizedService):

    async def get_users_by_organization(
        self,
        db: AsyncSession,
        organization_id: UUID,
        limit: int = 100
    ) -> List[User]:
        """Get users with automatic performance monitoring"""

        query = select(User).where(User.organization_id == organization_id).limit(limit)

        result = await self.execute_query_with_analysis(
            db, query, "get_users_by_organization"
        )

        return result.scalars().all()
```

## 6. Best Practices and Common Patterns

### 6.1 When to Use EXPLAIN ANALYZE

#### **Use Cases:**
1. **Slow Queries**: Identify bottlenecks in slow-performing queries
2. **Query Optimization**: Before and after optimization comparisons
3. **Index Planning**: Determine which indexes would be most beneficial
4. **Development**: During development to catch performance issues early

#### **Avoid in Production:**
```sql
-- DON'T DO THIS IN PRODUCTION
EXPLAIN ANALYZE SELECT * FROM large_table WHERE complex_conditions;

-- Instead, use EXPLAIN only for quick checks
EXPLAIN SELECT * FROM large_table WHERE complex_conditions;
```

### 6.2 Common Optimization Patterns

#### **Pattern 1: Replace Seq Scan with Index Scan**

**Before:**
```
Seq Scan on users  (cost=0.00..5000.00 rows=100000 width=200)
  Filter: (organization_id = 'uuid')
```

**Solution:**
```sql
CREATE INDEX CONCURRENTLY idx_users_org_created
ON users (organization_id, created_at DESC);
```

**After:**
```
Index Scan using idx_users_org_created on users  (cost=0.42..100.00 rows=1000 width=200)
  Index Cond: (organization_id = 'uuid')
```

#### **Pattern 2: Replace Nested Loop with Hash Join**

**Before:**
```
Nested Loop  (cost=100.00..10000.00 rows=50000 width=300)
  ->  Seq Scan on responses  (cost=0.00..5000.00 rows=100000 width=150)
  ->  Index Scan using idx_users_id on users  (cost=0.42..0.50 rows=1 width=150)
```

**Solution:**
```sql
-- Use appropriate join conditions
SELECT u.*, COUNT(r.id)
FROM users u
JOIN responses r ON u.id = r.user_id
WHERE u.organization_id = 'uuid'
GROUP BY u.id;
```

**After:**
```
Hash Join  (cost=1000.00..2000.00 rows=50000 width=300)
  Hash Cond: (u.id = r.user_id)
  ->  Seq Scan on users  (cost=0.00..500.00 rows=10000 width=150)
        Filter: (organization_id = 'uuid')
  ->  Hash  (cost=800.00..800.00 rows=100000 width=150)
        ->  Seq Scan on responses  (cost=0.00..800.00 rows=100000 width=150)
```

### 6.3 Monitoring and Alerting

#### **Set Up Automated Monitoring:**
```sql
-- Create a function to log slow queries
CREATE OR REPLACE FUNCTION log_slow_queries()
RETURNS void AS $$
BEGIN
  -- Log queries that take longer than 1 second
  -- This would be implemented in your application layer
END;
$$ LANGUAGE plpgsql;

-- Set log_min_duration_statement in postgresql.conf
-- log_min_duration_statement = 1000  # Log queries > 1 second
```

#### **Regular Performance Reviews:**
```python
# Weekly performance report generation
async def generate_weekly_performance_report():
    stats = monitor.get_performance_stats()

    report = {
        'period': 'last_7_days',
        'total_queries': sum(stat['count'] for stat in stats.values()),
        'avg_response_time': sum(stat['avg_time_ms'] for stat in stats.values()) / len(stats),
        'slowest_queries': sorted(
            [(name, stat['avg_time_ms']) for name, stat in stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10],
        'recommendations': []
    }

    return report
```

## 7. Troubleshooting Guide

### 7.1 Common Issues and Solutions

#### **Issue: Sequential Scans on Large Tables**
```sql
-- Check if index exists
SELECT indexname, tablename FROM pg_indexes WHERE tablename = 'users';

-- If no index exists, create one
CREATE INDEX CONCURRENTLY idx_users_org_created ON users (organization_id, created_at DESC);
```

#### **Issue: Inaccurate Row Estimates**
```sql
-- Update table statistics
ANALYZE users;
ANALYZE responses;

-- Check statistics
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('users', 'responses');
```

#### **Issue: High Memory Usage**
```sql
-- Check work_mem setting
SHOW work_mem;

-- Increase for complex queries (per session)
SET work_mem = '256MB';

-- Or globally (requires restart)
-- SET work_mem = '256MB';  -- In postgresql.conf
```

### 7.2 Performance Testing

#### **Load Testing Script:**
```python
async def load_test_query_performance(db: AsyncSession, query_func, iterations=100):
    """Load test a specific query function"""

    times = []
    errors = 0

    for i in range(iterations):
        start_time = time.time()

        try:
            await query_func(db)
            execution_time = (time.time() - start_time) * 1000
            times.append(execution_time)
        except Exception as e:
            errors += 1
            logger.error(f"Query failed on iteration {i}: {e}")

    return {
        'iterations': iterations,
        'errors': errors,
        'avg_time_ms': sum(times) / len(times) if times else 0,
        'min_time_ms': min(times) if times else 0,
        'max_time_ms': max(times) if times else 0,
        'p95_time_ms': sorted(times)[int(len(times) * 0.95)] if times else 0
    }
```

This comprehensive execution plan analysis guide provides the tools and techniques needed to identify, analyze, and resolve database performance issues in the PsychSync application.
