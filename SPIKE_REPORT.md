# Spike Evaluation: Django Background Tasks (Django 6.0+)

## 1. Project Overview & Objective
This spike project evaluates the production-readiness of the new **Django 6.0+ Tasks framework**. Historically, Django required third-party libraries like Celery or Huey for asynchronous task processing. With the introduction of a native task API, we aim to determine if the built-in solution is sufficient to replace traditional distributed task queues for our standard application workloads.

---

## 2. Deep Dive: Django 6.0 Tasks framework
The new `django.tasks` module provides a standardized interface for defining, enqueuing, and executing background work.

### How it Works:
1.  **Definition**: Tasks are defined using the `@task` decorator, which registers them with a backend.
2.  **Queuing**: When `.enqueue()` is called, the task is serialized and stored in the configured backend.
3.  **Execution**: A dedicated worker process (started via `python manage.py db_worker`) polls the backend and executes the task logic.

### The Database Backend Lifecycle:
Using the `DatabaseBackend` (via `django-tasks`), the lifecycle is tightly integrated with the Django ORM:
*   **Transactional Integrity**: Tasks are only enqueued if the database transaction that triggered them is successfully committed. This is a massive improvement over traditional systems where tasks might fire even if a database record rollback occurs.
*   **Infrastructure**: No additional infrastructure (like Redis) is strictly required, as the existing application database serves as the message broker.

---

## 3. Comparative Analysis: Django Tasks vs. Celery

| Feature | Django Tasks (DB Backend) | Celery (Redis Broker) |
| :--- | :--- | :--- |
| **Architecture** | Polling-based (Database) | Real-time (In-memory) |
| **Broker** | Primary Application DB | Redis / RabbitMQ |
| **Complexity** | Minimal (Standard Django models) | High (Requires separate infra/config) |
| **Ideal For** | Standard logic, Atomic operations | High-throughput, distributed systems |
| **Workflow Support** | Basic (Simple retries) | Advanced (Chains, Groups, Chords) |

---

## 4. Benchmark & Scenario Insights
We implemented a multi-faceted benchmark suite to test both systems under identical pressure.

### Scenarios Tested:
1.  **Transactional Email**: Simulating I/O wait and network latency.
2.  **CPU Intensive**: SHA-256 hashing to test multi-process worker efficiency.
3.  **DB Contention stress**: Multiple workers performing bulk operations on shared tables.
4.  **HTTP Fan-out**: Concurrent outbound API requests within a single task process.
5.  **High-Volume Burst**: Enqueueing 1,000 tasks at once to test broker ingestion speed.

### Performance Data Breakdown:
| System | Task Type | Exec Avg | Latency Avg | Latency P95 |
| :--- | :--- | :--- | :--- | :--- |
| **Celery** | Email (I/O) | 0.504s | 7.76s | 14.71s |
| **Celery** | Throughput Burst | 0.002s | **0.74s** | **0.82s** |
| **Django** | Email (I/O) | 0.505s | 8.26s | 15.17s |
| **Django** | Throughput Burst | 0.001s | **6.74s** | **6.95s** |

---

## 5. Metric Insights: Where Django Tasks Succeeds and Fails

### The Strength of Native Integration:
For **Transactional Email** and **I/O Bound** tasks, the performance difference is statistically insignificant (~5%). Django's native integration makes it the ideal choice for 80% of web workloads where simplicity and transaction safety are more important than sub-millisecond throughput.

### The "Broker Lag" Bottleneck:
The **Throughput Burst** test revealed a clear limitation. Celery (via Redis) handled 1,000 enqueued tasks with sub-second latency. Django Tasks (via DB) showed an average latency of ~7 seconds. This occurs because the database must handle row-level locking for every single task write/read, whereas Redis performs these operations in-memory at O(1) speed.

---

## 6. Ideal Scenarios (Decision Matrix)

### Scenario A: User Sign-up Email (Standard)
*   **Ideal Choice**: **Django Tasks**
*   **Reasoning**: It's critical the email only sends if the user is successfully created in the DB. Django's native atomicity handles this perfectly with zero extra code.

### Scenario B: Generating Daily PDF Reports (Batch)
*   **Ideal Choice**: **Django Tasks**
*   **Reasoning**: These are long-running, isolated tasks where queue latency doesn't impact user experience. Managing Redis just for this is unnecessary overhead.

### Scenario C: Real-time Notifications / Massive Scraping
*   **Ideal Choice**: **Celery**
*   **Reasoning**: High-frequency tasks require an in-memory broker to prevent the application database from becoming the bottleneck.

---

## 7. Overall Verdict & Recommendation
This spike demonstrates that **Django Tasks (Django 6.0+) is a production-ready replacement for Celery for small-to-medium datasets and standard web applications.**

*   **RECOMMENDATION**: Adopt Django Tasks as the default background job system for this project.
*   **EXCEPTION**: Continue using Celery only for specific microservices that require high-velocity task ingestion or complex orchestration (pipelines).
