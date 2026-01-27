# Django vs Celery Tasks Comparison Demo

This project provides a production-quality comparison between Django's built-in Tasks and Celery.

## Prerequisites
- Python 3.12+
- Redis (installed and running on port 6379)
- Dependencies: `pip install django celery redis psutil django-tasks`

## Project Structure
- `tasks_demo/tasks.py`: Implementation of workloads (Email, I/O, CPU, Batch).
- `benchmark.py`: Load testing script.
- `demo_project/settings.py`: Integrated configuration for both systems.
- `Django_Tasks_vs_Celery_Evaluation.md`: Final analysis and recommendation.

## How to Run the Demo

1. **Start Redis**:
   ```bash
   redis-server
   ```

2. **Start Workers** (Run each in a separate terminal or background):
   ```bash
   # Celery
   celery -A demo_project worker --loglevel=info --concurrency=4
   
   # Django Tasks (Start multiple for concurrency)
   python manage.py db_worker --worker-id w1
   python manage.py db_worker --worker-id w2
   ```

3. **Run Benchmark**:
   ```bash
   python benchmark.py --batch 50 --iter 2
   ```

4. **View Metrics**:
   Start the dev server:
   ```bash
   python manage.py runserver
   ```
   Visit `http://localhost:8000/metrics/` to see the JSON output of performance stats.

## Metrics Observation
- **Latency**: Time from enqueue to execution start.
- **Execution Time**: Real-time taken by the worker.
- **Success Rate**: Count of tasks finishing without error.
- **Queue Depth**: Check `django_tasks_database_dbtaskresult` table for Django or Redis `LLEN` for Celery.
