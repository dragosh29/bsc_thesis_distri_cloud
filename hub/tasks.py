from celery import shared_task
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from hub.models import Node
from hub.task_manager import TaskManager, logger


@shared_task
def check_node_health():
    """
    Periodically checks node heartbeats and updates their status based on inactivity.
    - Any 'active' node that hasn't had a heartbeat in the last 5 minutes becomes 'inactive'.
    - Delegates task handling logic to TaskManager.
    """
    threshold_inactive = timezone.now() - timedelta(minutes=5)

    # Mark active nodes as inactive if they haven't sent a heartbeat in 5+ minutes
    inactive_nodes = Node.objects.filter(
        Q(
        last_heartbeat__lt=threshold_inactive,
        status='active'
    ) | Q(
            status='inactive')
    )
    if inactive_nodes.exists():
        node_ids = list(inactive_nodes.values_list('id', flat=True))
        count_inactive = inactive_nodes.update(status='inactive')
        logger.info(f"[check_node_health] {count_inactive} node(s) marked inactive.")

        # Delegate task handling to TaskManager
        manager = TaskManager()
        manager.handle_tasks_for_inactive_nodes(node_ids)

    logger.info("[check_node_health] Node health check complete.")


@shared_task
def distribute_tasks():
    """
    Periodically invokes the TaskManager to manage
    - Reordering active queue
    - Moving tasks from backlog to active
    - Assigning tasks to nodes
    - Handling stale tasks
    """
    manager = TaskManager()
    manager.manage_distributions()
    logger.info("[distribute_tasks] Task distribution cycle complete.")
