"""
Test script to verify Celery setup
Run this after starting your Celery worker
"""
import sys
import time
from datetime import datetime

def test_redis_connection():
    """Test Redis connection"""
    print("=" * 60)
    print("1. Testing Redis Connection")
    print("=" * 60)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        result = r.ping()
        
        if result:
            print("✅ Redis connection: SUCCESS")
            print(f"   Redis version: {r.info()['redis_version']}")
            return True
        else:
            print("❌ Redis connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Redis connection: ERROR - {str(e)}")
        print("\nTo fix:")
        print("  macOS: brew install redis && brew services start redis")
        print("  Linux: sudo apt install redis-server && sudo systemctl start redis")
        return False


def test_celery_import():
    """Test Celery import"""
    print("\n" + "=" * 60)
    print("2. Testing Celery Import")
    print("=" * 60)
    
    try:
        from app.core.celery_worker import celery_app
        print("✅ Celery app import: SUCCESS")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        print(f"❌ Celery app import: ERROR - {str(e)}")
        return False


def test_celery_worker():
    """Test if Celery worker is running"""
    print("\n" + "=" * 60)
    print("3. Testing Celery Worker Status")
    print("=" * 60)
    
    try:
        from app.core.celery_worker import celery_app
        
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery worker: RUNNING")
            for worker_name, worker_stats in stats.items():
                print(f"   Worker: {worker_name}")
                print(f"   Pool: {worker_stats.get('pool', {}).get('implementation', 'N/A')}")
            return True
        else:
            print("❌ Celery worker: NOT RUNNING")
            print("\nTo start worker:")
            print("  celery -A app.core.celery_worker.celery_app worker --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Celery worker check: ERROR - {str(e)}")
        return False


def test_simple_task():
    """Test executing a simple task"""
    print("\n" + "=" * 60)
    print("4. Testing Simple Task Execution")
    print("=" * 60)
    
    try:
        from app.core.celery_worker import debug_task
        
        print("   Sending task to worker...")
        result = debug_task.delay()
        
        print(f"   Task ID: {result.id}")
        print(f"   Task State: {result.state}")
        
        print("   Waiting for result (max 10 seconds)...")
        task_result = result.get(timeout=10)
        
        print("✅ Task execution: SUCCESS")
        print(f"   Result: {task_result}")
        return True
        
    except Exception as e:
        print(f"❌ Task execution: ERROR - {str(e)}")
        return False


def test_scheduled_tasks():
    """Test scheduled tasks configuration"""
    print("\n" + "=" * 60)
    print("5. Testing Scheduled Tasks (Beat)")
    print("=" * 60)
    
    try:
        from app.core.celery_worker import celery_app
        
        schedule = celery_app.conf.beat_schedule
        
        if schedule:
            print("✅ Beat schedule: CONFIGURED")
            print(f"   Number of scheduled tasks: {len(schedule)}")
            for task_name in schedule.keys():
                print(f"   - {task_name}")
            
            # Check if beat is running
            inspect = celery_app.control.inspect()
            scheduled = inspect.scheduled()
            
            if scheduled:
                print("\n✅ Celery Beat: RUNNING")
            else:
                print("\n⚠️  Celery Beat: NOT RUNNING")
                print("   To start beat:")
                print("   celery -A app.core.celery_worker.celery_app beat --loglevel=info")
            
            return True
        else:
            print("❌ Beat schedule: NOT CONFIGURED")
            return False
            
    except Exception as e:
        print(f"❌ Beat schedule check: ERROR - {str(e)}")
        return False


def test_task_queues():
    """Test task queues"""
    print("\n" + "=" * 60)
    print("6. Testing Task Queues")
    print("=" * 60)
    
    try:
        from app.core.celery_worker import celery_app
        
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues()
        
        if active_queues:
            print("✅ Task queues: CONFIGURED")
            for worker_name, queues in active_queues.items():
                print(f"   Worker: {worker_name}")
                for queue in queues:
                    print(f"     - {queue['name']}")
            return True
        else:
            print("⚠️  Task queues: Worker not running or no queues active")
            return False
            
    except Exception as e:
        print(f"❌ Queue check: ERROR - {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 16 + "CELERY SETUP TEST" + " " * 25 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = []
    
    # Run all tests
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Celery Import", test_celery_import()))
    results.append(("Celery Worker", test_celery_worker()))
    results.append(("Task Execution", test_simple_task()))
    results.append(("Scheduled Tasks", test_scheduled_tasks()))
    results.append(("Task Queues", test_task_queues()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print("\n" + "-" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print("-" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Celery is properly configured.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
        