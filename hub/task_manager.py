# task_manager.py

import logging
from django.utils import timezone
from django.conf import settings
from django.db.models import Q, Count
from hub.models import Task, Node, TaskAssignment

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages task distribution among nodes using an active queue + backlog strategy,
    resource-aware assignment, trust index filtering, and staleness logic.

    NOTE: Tasks already assigned to nodes are not swapped out of the active queue.
    """

    def __init__(self):
        # The maximum number of tasks to keep 'in_progress' at once
        self.active_queue_size = getattr(settings, 'ACTIVE_QUEUE_SIZE', 10)
        # Stale tasks threshold
        self.max_stale_count = 20

    def calculate_task_priority(self, task: Task) -> float:
        """
        Calculates a numeric priority score for a given task.
        Higher -> higher priority to schedule.
        """
        # Age factor: the longer it has waited, the more urgent
        time_waiting = (timezone.now() - task.created_at).total_seconds()
        # If no resource requirements, use 1 so we don't divide by zero
        resource_weight = task.resource_requirements.get("cpu_cores", 0.5) + task.resource_requirements.get("ram_gb",
                                                                                                            0.5)
        # Give a penalty for tasks that have gone stale multiple times
        stale_penalty = task.stale_count * 10

        # Status weight: in_progress tasks get a slight boost
        status_weight = 1.2 if task.status == 'in_progress' else 1.0

        # Basic formula with status weight
        return ((time_waiting / resource_weight) - stale_penalty) * status_weight

    def move_tasks_to_active_queue(self):
        """
        Fill available slots in the active queue from the backlog based on priority.
        """
        active_task_count = Task.objects.filter(Q(status='in_progress') | Q(status='in_queue')).count()
        available_slots = self.active_queue_size - active_task_count
        if available_slots <= 0:
            logger.debug("No available slots in the active queue.")
            return

        backlog_tasks = Task.objects.filter(status='pending')
        sorted_backlog = sorted(backlog_tasks, key=self.calculate_task_priority, reverse=True)
        tasks_to_activate = sorted_backlog[:available_slots]

        for task in tasks_to_activate:
            task.status = 'in_queue'
            task.last_attempted = timezone.now()
            task.save()
            logger.info(f"Moved task {task.id} to queue for assignment.")

    def reorder_active_queue(self):
        """
        Swap tasks from the active queue with backlog tasks if the latter have higher priority,
        but only if the active tasks are unassigned. (We do not swap tasks that already started.)
        """
        active_tasks_unassigned = list(
            Task.objects.filter(
                status='in_queue',
            )
        )
        backlog_tasks = list(Task.objects.filter(status='pending'))
        if not active_tasks_unassigned or not backlog_tasks:
            return

        active_sorted = sorted(active_tasks_unassigned, key=self.calculate_task_priority, reverse=True)
        backlog_sorted = sorted(backlog_tasks, key=self.calculate_task_priority, reverse=True)

        lowest_active = active_sorted[-1]
        highest_backlog = backlog_sorted[0]

        if self.calculate_task_priority(highest_backlog) > self.calculate_task_priority(lowest_active):
            lowest_active.status = 'pending'
            lowest_active.save()
            highest_backlog.status = 'in_queue'
            highest_backlog.last_attempted = timezone.now()
            highest_backlog.save()

            logger.info(
                f"Swapped out unassigned active task {lowest_active.id} "
                f"with backlog task {highest_backlog.id}."
            )

    def assign_tasks_to_nodes(self):
        """
        Assign tasks in 'in_progress' and 'in_queue' state using TaskAssignment for overlap_count nodes.
        Prevents duplicate assignment of the same task to the same node.
        """
        active_tasks = Task.objects.filter(Q(status='in_progress') | Q(status='in_queue'))

        for task in active_tasks:
            # Get currently assigned node IDs
            assigned_nodes = set(
                TaskAssignment.objects.filter(task=task).values_list('node_id', flat=True)
            )

            if len(assigned_nodes) >= task.overlap_count:
                logger.info(f"Task {task.id} already fully assigned ({len(assigned_nodes)}/{task.overlap_count}).")
                if task.status == 'in_queue':
                    task.status = 'in_progress'
                    task.save()
                continue

            candidate_nodes = Node.objects.filter(
                status='active',
                trust_index__gte=task.trust_index_required
            ).exclude(id__in=assigned_nodes)  # Exclude already assigned nodes

            if not candidate_nodes.exists():
                task.mark_stale()
                logger.warning(f"No candidate nodes found for task {task.id}. Marking as stale.")
                continue

            # Calculate suitability score for each node
            def calculate_suitability(node):
                node_free_cpu = node.resources_capacity.get('cpu', 0) - node.resources_usage.get('cpu', 0)
                node_free_ram = node.resources_capacity.get('ram', 0) - node.resources_usage.get('ram', 0)

                task_cpu = task.resource_requirements.get('cpu', 1)
                task_ram = task.resource_requirements.get('ram', 1)

                cpu_score = abs(node_free_cpu - task_cpu) / max(task_cpu, 1)
                ram_score = abs(node_free_ram - task_ram) / max(task_ram, 1)

                return cpu_score + ram_score  # Lower is better

            # Rank nodes by suitability and fallback to trust index
            ranked_nodes = sorted(
                candidate_nodes,
                key=lambda node: (calculate_suitability(node), -node.trust_index)
            )

            # Assign up to the remaining overlap count
            remaining_assignments = task.overlap_count - len(assigned_nodes)
            for i in range(remaining_assignments):
                if not ranked_nodes:
                    logger.warning(
                        f"Not enough nodes available for task {task.id}. Assigned {i} additional nodes so far."
                    )
                    break

                best_node = ranked_nodes.pop(0)

                TaskAssignment.objects.create(task=task, node=best_node)
                if task.status == 'in_queue':
                    task.status = 'in_progress'
                    task.save()
                logger.info(
                    f"Assigned task {task.id} to node {best_node.name} "
                    f"(Overlap {len(assigned_nodes) + i + 1}/{task.overlap_count})."
                )

    def handle_stale_tasks(self):
        """
        If a task's stale_count exceeds max_stale_count, mark it as 'failed'.
        This does not affect nodes; we do not mark nodes as failed.
        """
        too_stale = Task.objects.filter(
            stale_count__gte=self.max_stale_count,
            status='in_queue'
        )
        for task in too_stale:
            task.status = 'failed'
            task.save()
            logger.info(f"Marked task {task.id} as failed due to exceeding stale threshold.")

    def manage_distributions(self):
        """
        Orchestrates the scheduling:
          1. Reorder the active queue if needed.
          2. Move tasks from backlog to active queue.
          3. Assign tasks to nodes.
          4. Handle stale tasks.
        """
        logger.info("Starting task distribution cycle...")
        self.reorder_active_queue()
        self.move_tasks_to_active_queue()
        self.assign_tasks_to_nodes()
        self.handle_stale_tasks()
        logger.info("Completed task distribution cycle.")

    def handle_tasks_for_inactive_nodes(self, inactive_node_ids):
        """
        Handles tasks assigned to inactive nodes:
        - Releases task assignments linked to inactive nodes.
        - Updates task statuses based on remaining assignments.
        """
        # Step 1: Remove assignments for inactive nodes
        affected_assignments = TaskAssignment.objects.filter(node_id__in=inactive_node_ids)
        affected_task_ids = set(affected_assignments.values_list('task_id', flat=True))

        removed_assignments_count = affected_assignments.delete()[0]
        logger.info(f"[handle_tasks_for_inactive_nodes] Removed {removed_assignments_count} task assignments.")

        if not affected_task_ids:
            logger.info("[handle_tasks_for_inactive_nodes] No tasks were affected by inactive nodes.")
            return

        # Step 2: Handle tasks with no active assignments
        tasks_without_assignments = Task.objects.filter(
            id__in=affected_task_ids
        ).annotate(assignment_count=Count('taskassignment')).filter(assignment_count=0)

        reset_count = tasks_without_assignments.update(status='in_queue')
        if reset_count:
            logger.info(
                f"[handle_tasks_for_inactive_nodes] {reset_count} task(s) moved to 'in_queue' (0 active assignments).")

        # Step 3: Handle tasks with remaining active assignments
        tasks_with_assignments = Task.objects.filter(
            id__in=affected_task_ids
        ).annotate(assignment_count=Count('taskassignment')).filter(assignment_count__gt=0,
                                                                    status__in=['pending', 'in_queue'])

        in_progress_count = tasks_with_assignments.update(status='in_progress')
        if in_progress_count:
            logger.info(
             f"[handle_tasks_for_inactive_nodes] {in_progress_count} task(s) updated to 'in_progress' (active assignments remain).")
