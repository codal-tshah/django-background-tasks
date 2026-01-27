# Django vs Celery Tasks Comparison Demo

This project provides a production-quality comparison between Django's built-in Tasks and Celery.

## Prerequisites
- Python 3.12+
- Redis (installed and running on port 6379)
- Dependencies: `pip install django celery redis psutil django-tasks`

## Project Structure
- `tasks_demo/tasks.py`: Implementation of workloads (Email, I/O, CPU, Batch, DB Contention, HTTP Fan-out, Throughput Burst).
- `benchmark.py`: Load testing script.
- `demo_project/settings.py`: Integrated configuration for both systems.
- `SPIKE_REPORT.md`: Comprehensive engineering analysis and final recommendation (Main Doc).
- `Spike_Report_Django_Background_Tasks.docx`: Professional documentation for stakeholders.

## How to Run the Demo

### 1. Start Infrastructure
Start Redis (for Celery):
```bash
redis-server --port 6379
```

### 2. Start Workers
Run each in a separate terminal:
```bash
# Celery (4 concurrent workers)
celery -A demo_project worker --loglevel=info --concurrency=4

# Django Tasks (Start 2-4 workers for concurrency)
python manage.py db_worker --worker-id w1
python manage.py db_worker --worker-id w2
```

### 3. Run Scalability Benchmarks
Execute the benchmark script with different load parameters:
```bash
# Standard Load
python benchmark.py --batch 10 --iter 2

# High Volume Throughput Test (Tests Redis vs DB Enqueue speed)
python benchmark.py --batch 50 --iter 5
```

### 4. Metrics & Observation
To view real-time metrics, start the Django dev server:
```bash
python manage.py runserver
```
Then visit:
- **Metrics API**: `http://localhost:8000/metrics/` (Aggregated JSON)
- **DB Inspection**: `python manage.py dbshell` -> `select * from tasks_demo_taskmetric;`

## Metrics Collected
- **Exec Avg**: Execution time inside the worker.
- **Lat Avg**: Queue latency (time spent waiting for a worker).
- **Lat P95**: Tail latency (helps identify "stuck" tasks or broker bottlenecks).

## Metrics Observation
- **Latency**: Time from enqueue to execution start.
- **Execution Time**: Real-time taken by the worker.
- **Success Rate**: Count of tasks finishing without error.
- **Queue Depth**: Check `django_tasks_database_dbtaskresult` table for Django or Redis `LLEN` for Celery.
