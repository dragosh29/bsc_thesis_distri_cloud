from datetime import timedelta

from celery import shared_task, group, chain
from django.db.models import Q
from django.utils import timezone

from hub.models import Node
from hub.task_manager import TaskManager, logger


@shared_task
def check_node_health():
    """
    Periodically checks node heartbeats and updates their status based on inactivity.
    - Any 'active' node that hasn't had a heartbeat in the last 2 minutes becomes 'inactive'.
    - Delegates task handling logic to TaskManager.
    """
    threshold_inactive = timezone.now() - timedelta(minutes=2)

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
def reorder_active_queue_task(*args, **kwargs):
    """Celery task to reorder the active task queue. Delegates to TaskManager."""
    manager = TaskManager()
    manager.reorder_active_queue()


@shared_task
def handle_stale_tasks_task(*args, **kwargs):
    """Celery task to handle stale tasks. Delegates to TaskManager."""
    manager = TaskManager()
    manager.handle_stale_tasks()


@shared_task
def move_tasks_to_active_queue_task(*args, **kwargs):
    """Celery task to move tasks from the pending queue to the active queue. Delegates to TaskManager."""
    manager = TaskManager()
    manager.move_tasks_to_active_queue()


@shared_task
def assign_tasks_to_nodes_task(*args, **kwargs):
    """Celery task to assign tasks to nodes. Delegates to TaskManager."""
    manager = TaskManager()
    manager.assign_tasks_to_nodes()


@shared_task
def retry_failed_tasks_task(*args, **kwargs):
    """Celery task to retry failed tasks. Delegates to TaskManager."""
    manager = TaskManager()
    manager.retry_failed_tasks()


@shared_task
def handle_persistently_failing_tasks_task(*args, **kwargs):
    """Celery task to handle persistently failing tasks. Delegates to TaskManager."""
    manager = TaskManager()
    manager.handle_persistently_failing_tasks()


@shared_task
def validate_docker_image_task(task_id):
    """ Celery task to validate a Docker image for a given task ID. Delegates to TaskManager."""
    manager = TaskManager()
    status = manager.validate_docker_image(task_id)
    if 'error' in status:
        logger.error(f"[validate_docker_image_task] Error validating Docker image for task {task_id}: {status['error']}")


@shared_task
def orchestrate_task_distribution():
    """
    Orchestrates the task distribution workflow using Celery's `group` and `chain`.
    """
    # Parallel tasks
    parallel_tasks = group(
        reorder_active_queue_task.s(),
        handle_stale_tasks_task.s()
    )

    # Sequential tasks
    sequential_tasks = chain(
        move_tasks_to_active_queue_task.s(),
        assign_tasks_to_nodes_task.s(),
        retry_failed_tasks_task.s(),
        handle_persistently_failing_tasks_task.s()
    )

    # Trigger the workflow
    workflow = chain(parallel_tasks, sequential_tasks)
    workflow.apply_async()
    logger.info("[orchestrate_task_distribution] Task distribution workflow initiated.")
