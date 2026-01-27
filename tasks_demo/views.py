from django.http import JsonResponse
from django.db.models import Avg, Max, Count, Q
from .models import TaskMetric
import json

def metrics_view(request):
    results = {}
    systems = ['celery', 'django']
    
    for system in systems:
        metrics = TaskMetric.objects.filter(system=system)
        
        system_stats = {
            'total_tasks': metrics.count(),
            'success_rate': (metrics.filter(success=True).count() / max(metrics.count(), 1)) * 100,
            'tasks_by_type': {}
        }
        
        task_types = ['email', 'io', 'cpu', 'batch']
        for t_type in task_types:
            type_metrics = metrics.filter(task_type=t_type)
            if type_metrics.exists():
                durations = list(type_metrics.filter(success=True).values_list('duration', flat=True))
                durations.sort()
                
                system_stats['tasks_by_type'][t_type] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'p95_duration': durations[int(len(durations) * 0.95)] if durations else 0,
                    'max_duration': max(durations) if durations else 0,
                }
        
        results[system] = system_stats
        
    return JsonResponse(results)
