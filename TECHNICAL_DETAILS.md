# Technical Deep Dive: Django Tasks vs. Celery Benchmark Project

## 1. Project Introduction
This project is a high-fidelity performance evaluation suite designed to compare the execution characteristics of **Django 6.0's native Task framework** against **Celery 5.4**. The goal is to provide measurable evidence of where each system excels, specifically focusing on latency, throughput, and database contention.

---

## 2. Architectural Comparison

### A. Celery (The Distributed Architecture)
*   **Infrastructure**: Uses **Redis** as a Message Broker. Task definitions are serialized via JSON and pushed into a Redis List.
*   **Worker Lifecycle**: Celery workers run in a separate process space, using a `ForkPool` by default. They "long-poll" Redis with extremely low overhead.
*   **State Management**: Task results are stored in a separate Redis database (Result Backend).

### B. Django Tasks (The Integrated Architecture)
*   **Infrastructure**: Uses the **Application Database** (PostgreSQL/SQLite) as the broker.
*   **Worker Lifecycle**: Workers are managed via `python manage.py db_worker`. They use an ORM-based polling mechanism to find pending tasks in the `django_tasks_database_dbtaskresult` table.
*   **Atomicity**: Tasks are only written to the database when the current Django database transaction is committed. This ensures that if a record creation fails, the associated background task is never enqueued.

---

## 3. Workload Implementation Details

We implemented seven distinct workload types to cover all common production scenarios:

1.  **Transactional Email**: Simulates SMTP latency (0.5s network wait).
2.  **I/O Bound**: Pure `time.sleep` to test worker concurrency.
3.  **CPU Bound**: Intense SHA-256 hashing to test multi-core utilization and process isolation.
4.  **Batch Processing**: Running multiple small CPU tasks inside a single job.
5.  **Database Contention**: Performs 50 bulk creates and 50 updates on a shared table (`ContentionModel`). This tests how background tasks impact application DB performance.
6.  **HTTP Fan-out**: Uses `httpx` and `ThreadPoolExecutor` to trigger 5 concurrent outbound requests. This tests asynchronous I/O within a synchronous worker process.
7.  **Throughput Burst**: Enqueues 1,000 tasks with 100KB payloads to measure the "Enqueue Throughput" of the broker (Redis vs DB).

---

## 4. Metrics Collection System

### The Decorator Pattern (`@record_metric`)
Every task in `tasks_demo/tasks.py` is wrapped in a custom decorator. This pattern ensures zero boilerplate inside the task logic itself.

**What it captures:**
*   **Enqueue Timestamp**: Passed as an argument when the task is called (`enqueued_at`).
*   **Start/End Timestamp**: Captured using `time.time()` for wall-clock tracking.
*   **Execution Time**: Captured using `time.perf_counter()` for high-precision duration (independent of system clock shifts).
*   **Latency**: Calculated as `Start Time - Enqueue Time`. This is the single most important metric for scalability as it shows the "backlog" pressure.

### Database Schema
*   **TaskMetric Model**: Stores the system, task type, duration, latency, and success/failure logs.
*   **Indexes**: Crucial indexes on `(system, task_type)` allow the `/metrics/` API to aggregate thousands of records in milliseconds.

---

## 5. Benchmarking Engine (`benchmark.py`)

The benchmark script operates in three phases:
1.  **Trigger Phase**: Simultaneously enqueues tasks to both Celery and Django. It generates a "burst" of 200 high-volume tasks per iteration.
2.  **Cooling Phase**: Waits 20 seconds after the final enqueue to ensure all background processes complete before the database is queried for stats.
3.  **Analysis Phase**: Pulls metrics from the DB and calculates:
    *   **Exec Avg**: The raw speed of the code.
    *   **Lat Avg**: The health of the queue.
    *   **Lat P95**: The "tail" experience (worst-case scenario for a user).

---

## 6. Observability
*   **Metrics API**: The endpoint `/metrics/` calculates these stats in real-time. It provides a JSON summary that can be scraped by Prometheus or viewed in a dashboard.
*   **Worker Logs**: We redirect worker output to `celery.log` and `django_worker.log` for structured error tracking.

---

## 7. Operational Summary
To reproduce these findings, the project requires:
1.  **RabbitMQ/Redis** for the Celery transport layer.
2.  **Django 6.0** for the native `django_tasks` module.
3.  **Concurrency tuning**: Workers are set to `--concurrency=4` to match physical CPU cores for a fair trial.
