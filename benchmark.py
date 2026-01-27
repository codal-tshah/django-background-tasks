import os
import django
import time
import argparse
from concurrent.futures import ThreadPoolExecutor

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'demo_project.settings')
django.setup()

from tasks_demo.tasks import (
    celery_send_email, celery_io_bound, celery_cpu_bound, celery_batch_process,
    celery_db_contention, celery_http_fanout,
    django_send_email, django_io_bound, django_cpu_bound, django_batch_process,
    django_db_contention, django_http_fanout
)
from tasks_demo.models import TaskMetric, WorkerMetric

def trigger_celery_tasks(count):
    print(f"Triggering {count} Celery tasks...")
    for _ in range(count):
        now = time.time()
        celery_send_email.delay("user@example.com", enqueued_at=now)
        celery_io_bound.delay(0.2, enqueued_at=now)
        celery_cpu_bound.delay(10**5, enqueued_at=now)
        celery_batch_process.delay([i for i in range(10)], enqueued_at=now)
        celery_db_contention.delay(50, enqueued_at=now)
        celery_http_fanout.delay(fanout=5, enqueued_at=now)

def trigger_django_tasks(count):
    print(f"Triggering {count} Django tasks...")
    for _ in range(count):
        now = time.time()
        django_send_email.enqueue("user@example.com", enqueued_at=now)
        django_io_bound.enqueue(0.2, enqueued_at=now)
        django_cpu_bound.enqueue(10**5, enqueued_at=now)
        django_batch_process.enqueue([i for i in range(10)], enqueued_at=now)
        django_db_contention.enqueue(50, enqueued_at=now)
        django_http_fanout.enqueue(fanout=5, enqueued_at=now)

def run_benchmark(batch_size=10, iterations=5):
    # Clear previous metrics
    TaskMetric.objects.all().delete()
    
    print(f"Starting benchmark: {iterations} iterations of {batch_size} batches...")
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        # Trigger both systems
        trigger_celery_tasks(batch_size)
        trigger_django_tasks(batch_size)
        
        # Wait for some processing
        time.sleep(5)

    print("Waiting for all tasks to complete (cooling down)...")
    time.sleep(20) 

def analyze_results():
    systems = ['celery', 'django']
    task_types = ['email', 'io', 'cpu', 'batch', 'db_contention', 'http_fanout']
    
    print("\n" + "="*70)
    print(f"{'System':<10} | {'Task':<10} | {'Count':<6} | {'Exec Avg':<8} | {'Lat Avg':<8} | {'Lat P95':<8} | {'Success'}")
    print("-" * 70)
    
    for system in systems:
        for t_type in task_types:
            metrics = TaskMetric.objects.filter(system=system, task_type=t_type, success=True)
            count = metrics.count()
            if count > 0:
                durations = sorted([m.duration for m in metrics if m.duration is not None])
                latencies = sorted([m.latency for m in metrics if m.latency is not None])
                
                avg_exec = sum(durations) / len(durations)
                avg_lat = sum(latencies) / len(latencies) if latencies else 0
                p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0
                
                success_rate = (metrics.count() / max(TaskMetric.objects.filter(system=system, task_type=t_type).count(), 1)) * 100
                print(f"{system:<10} | {t_type:<10} | {count:<6} | {avg_exec:<8.3f} | {avg_lat:<8.3f} | {p95_lat:<8.3f} | {success_rate:>6.1f}%")
            else:
                print(f"{system:<10} | {t_type:<10} | {'0':<6} | {'N/A':<8} | {'N/A':<8} | {'N/A':<8} | {'0.0':>6}%")
    print("="*70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=10)
    parser.add_argument("--iter", type=int, default=3)
    args = parser.parse_args()
    
    run_benchmark(batch_size=args.batch, iterations=args.iter)
    analyze_results()
