import redis
import json
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone

from hub.models import Node, Task

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

def publish_task_update(node_id, emit=False):
    """
    Publish a task update event to the Redis channel.
    """
    if not emit:
        return

    channel = settings.REDIS_TASK_UPDATES_CHANNEL
    message = {
        "type": "task_update",
        "timestamp": timezone.now().isoformat(),
        "node_id": str(node_id),
        "action": "refetch"
    }
    redis_client.publish(channel, json.dumps(message))

def publish_network_activity():
    """
    Publish aggregated network activity data to the network activity channel.
    """
    active_nodes_count = Node.objects.filter(status='active').count()
    total_cpu = sum(node.free_resources.get('free_cpu', 0) for node in Node.objects.filter(status='active'))
    total_ram = sum(node.free_resources.get('free_ram', 0) for node in Node.objects.filter(status='active'))
    average_trust_index = Node.objects.filter(status='active').aggregate(Avg('trust_index'))['trust_index__avg'] or 0

    pending_tasks = Task.objects.filter(status='pending').count()
    in_queue_tasks = Task.objects.filter(status='in_queue').count()
    in_progress_tasks = Task.objects.filter(status='in_progress').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    validated_tasks = Task.objects.filter(status='validated').count()
    failed_tasks = Task.objects.filter(status='failed').count()

    channel = settings.REDIS_NETWORK_ACTIVITY_CHANNEL

    message = {
        "type": "network_activity",
        "timestamp": timezone.now().isoformat(),
        "data": {
            "active_nodes": active_nodes_count,
            "total_cpu": total_cpu,
            "total_ram": total_ram,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "validated_tasks": validated_tasks,
            "failed_tasks": failed_tasks,
            "in_queue_tasks": in_queue_tasks,
            "average_trust_index": average_trust_index
        }
    }

    redis_client.publish(channel, json.dumps(message))
