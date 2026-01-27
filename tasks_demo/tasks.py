import time
import hashlib
import functools
import httpx
from concurrent.futures import ThreadPoolExecutor
from celery import shared_task
from django.tasks import task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import TaskMetric, ContentionModel

def record_metric(system, task_type):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            enqueued_at_ts = kwargs.pop('enqueued_at', None)
            start_ts = time.time()
            start_perf = time.perf_counter()
            
            metric = TaskMetric.objects.create(
                system=system, 
                task_type=task_type,
                enqueued_at=timezone.datetime.fromtimestamp(enqueued_at_ts, tz=timezone.get_current_timezone()) if enqueued_at_ts else None,
                start_time=timezone.now()
            )
            
            if enqueued_at_ts:
                metric.latency = start_ts - enqueued_at_ts
            
            try:
                result = func(*args, **kwargs)
                metric.success = True
                return result
            except Exception as e:
                metric.error_message = str(e)
                metric.success = False
                raise
            finally:
                end_perf = time.perf_counter()
                metric.duration = end_perf - start_perf
                metric.end_time = timezone.now()
                metric.save()
        return wrapper
    return decorator

# --- Shared Logic ---

def heavy_computation(n=10**6):
    """Simulates a CPU-bound task."""
    result = 0
    for i in range(n):
        result += hashlib.sha256(str(i).encode()).digest()[0]
    return result

def io_simulation(seconds=1):
    """Simulates an I/O-bound task."""
    time.sleep(seconds)
    return f"Slept for {seconds}s"

# --- Celery Tasks ---

@shared_task(name='celery_send_email')
@record_metric('celery', 'email')
def celery_send_email(recipient, enqueued_at=None):
    io_simulation(0.5)  # Simulate SMTP latency
    return f"Email sent to {recipient}"

@shared_task(name='celery_io_bound')
@record_metric('celery', 'io')
def celery_io_bound(seconds, enqueued_at=None):
    return io_simulation(seconds)

@shared_task(name='celery_cpu_bound')
@record_metric('celery', 'cpu')
def celery_cpu_bound(n, enqueued_at=None):
    return heavy_computation(n)

@shared_task(name='celery_batch_process')
@record_metric('celery', 'batch')
def celery_batch_process(items, enqueued_at=None):
    results = []
    for item in items:
        results.append(heavy_computation(10**4))
    return f"Processed {len(items)} items"

@shared_task(name='celery_db_contention')
@record_metric('celery', 'db_contention')
def celery_db_contention(count=50, enqueued_at=None):
    # Bulk create
    objs = [ContentionModel(data=f"Data {i}") for i in range(count)]
    ContentionModel.objects.bulk_create(objs)
    # Bulk update
    ContentionModel.objects.all().update(data="Updated")
    return f"DB Contention task completed for {count} records"

@shared_task(name='celery_http_fanout')
@record_metric('celery', 'http_fanout')
def celery_http_fanout(url="https://httpbin.org/get", fanout=10, enqueued_at=None):
    def fetch(u):
        with httpx.Client() as client:
            return client.get(u).status_code

    with ThreadPoolExecutor(max_workers=fanout) as executor:
        results = list(executor.map(fetch, [url] * fanout))
    return f"HTTP Fanout completed: {len(results)} requests"

# --- Django Tasks ---

@task
@record_metric('django', 'email')
def django_send_email(recipient, enqueued_at=None):
    io_simulation(0.5)
    return f"Email sent to {recipient}"

@task
@record_metric('django', 'io')
def django_io_bound(seconds, enqueued_at=None):
    return io_simulation(seconds)

@task
@record_metric('django', 'cpu')
def django_cpu_bound(n, enqueued_at=None):
    return heavy_computation(n)

@task
@record_metric('django', 'batch')
def django_batch_process(items, enqueued_at=None):
    results = []
    for item in items:
        results.append(heavy_computation(10**4))
    return f"Processed {len(items)} items"

@task
@record_metric('django', 'db_contention')
def django_db_contention(count=50, enqueued_at=None):
    # Bulk create
    objs = [ContentionModel(data=f"Data {i}") for i in range(count)]
    ContentionModel.objects.bulk_create(objs)
    # Bulk update
    ContentionModel.objects.all().update(data="Updated")
    return f"DB Contention task completed for {count} records"

@task
@record_metric('django', 'http_fanout')
def django_http_fanout(url="https://httpbin.org/get", fanout=10, enqueued_at=None):
    def fetch(u):
        with httpx.Client() as client:
            return client.get(u).status_code

    with ThreadPoolExecutor(max_workers=fanout) as executor:
        results = list(executor.map(fetch, [url] * fanout))
    return f"HTTP Fanout completed: {len(results)} requests"
