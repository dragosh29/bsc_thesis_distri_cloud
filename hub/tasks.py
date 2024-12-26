from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from hub.models import Node

@shared_task
def check_node_health():
    """
    Periodically checks node heartbeats and updates their status.
    """
    threshold = timezone.now() - timedelta(minutes=5)  # 5-minute threshold

    inactive_nodes = Node.objects.filter(
        last_heartbeat__lt=threshold,
        status='active'
    )

    for node in inactive_nodes:
        node.status = 'inactive'
        node.save()

    failed_nodes = Node.objects.filter(
        last_heartbeat__lt=threshold - timedelta(minutes=10),
        status='inactive'
    )

    for node in failed_nodes:
        node.status = 'failed'
        node.save()

    print(f"Checked node health: {inactive_nodes.count()} marked inactive, {failed_nodes.count()} marked failed.")
