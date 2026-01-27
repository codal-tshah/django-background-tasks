from django.db import models

class TaskMetric(models.Model):
    SYSTEM_CHOICES = [
        ('celery', 'Celery'),
        ('django', 'Django Tasks'),
    ]
    TASK_TYPE_CHOICES = [
        ('email', 'Email'),
        ('io', 'I/O Bound'),
        ('cpu', 'CPU Bound'),
        ('batch', 'Batch'),
        ('db_contention', 'DB Contention'),
        ('http_fanout', 'HTTP Fanout'),
        ('throughput_burst', 'Throughput Burst'),
    ]
    
    system = models.CharField(max_length=20, choices=SYSTEM_CHOICES)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    enqueued_at = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True) # execution time in seconds
    latency = models.FloatField(null=True, blank=True) # queue wait time in seconds
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['system', 'task_type']),
        ]

class WorkerMetric(models.Model):
    system = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_percent = models.FloatField()
    memory_usage_mb = models.FloatField()
    active_tasks = models.IntegerField(default=0)

class ContentionModel(models.Model):
    data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
