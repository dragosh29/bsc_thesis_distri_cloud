import redis
import json
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone

from hub.models import Node, Task

redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

def get_network_activity_data():
    """
    Collect and return network activity data as a dictionary.
    """
    active_nodes = Node.objects.filter(status='active')
    active_nodes_count = active_nodes.count()
    total_cpu = sum(node.free_resources.get('free_cpu', 0) for node in active_nodes)
    total_ram = sum(node.free_resources.get('free_ram', 0) for node in active_nodes)
    average_trust_index = active_nodes.aggregate(Avg('trust_index'))['trust_index__avg'] or 0

    return {
        "active_nodes": active_nodes_count,
        "total_cpu": total_cpu,
        "total_ram": total_ram,
        "pending_tasks": Task.objects.filter(status='pending').count(),
        "in_progress_tasks": Task.objects.filter(status='in_progress').count(),
        "completed_tasks": Task.objects.filter(status='completed').count(),
        "validated_tasks": Task.objects.filter(status='validated').count(),
        "failed_tasks": Task.objects.filter(status='failed').count(),
        "in_queue_tasks": Task.objects.filter(status='in_queue').count(),
        "average_trust_index": average_trust_index,
    }

def publish_task_update(node_id, emit=False):
    """
    Publish a task update event to the Redis channel.
    Args: node_id (UUID): The ID of the node that is being updated.
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
    Publish aggregated network activity data to the Redis channel.
    """
    data = get_network_activity_data()
    channel = settings.REDIS_NETWORK_ACTIVITY_CHANNEL
    message = {
        "type": "network_activity",
        "timestamp": timezone.now().isoformat(),
        "data": data
    }
    redis_client.publish(channel, json.dumps(message))
