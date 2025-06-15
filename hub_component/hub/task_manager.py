import logging
import docker
from docker.errors import ImageNotFound, DockerException
from collections import defaultdict

from django.utils import timezone
from django.conf import settings
from django.db.models import Q, Count
from hub.models import Task, Node, TaskAssignment
from licenta.settings import VALIDATION_THRESHOLD, TRUST_INCREMENT, TRUST_DECREMENT, STALE_PENALTY_MULTIPLIER, \
    IN_PROGRESS_BOOST, MAX_STALE_COUNT, TRUST_INDEX_MAX, TRUST_INDEX_MIN

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Manages task distribution among nodes using an active queue + backlog strategy,
    resource-aware assignment, trust index filtering, and staleness logic.
    """

    def __init__(self):
        self.active_queue_size = getattr(settings, 'ACTIVE_QUEUE_SIZE', 10)
        self.max_stale_count = MAX_STALE_COUNT

    def select_tasks_to_activate(self, backlog_tasks, available_slots):
        """Selects tasks from the backlog to activate based on priority / use FiFo."""
        mechanism = getattr(settings, "ORCHESTRATION_MECHANISM", "custom")
        if mechanism == "fifo":
            return list(backlog_tasks.order_by("created_at")[:available_slots])
        else:
            sorted_backlog = sorted(backlog_tasks, key=self.calculate_task_priority, reverse=True)
            return sorted_backlog[:available_slots]

    def calculate_task_priority(self, task: Task) -> float:
        """
        Calculates a numeric priority score for a given task using heuristic.
        Higher -> higher priority to schedule.
        """
        # Age factor: the longer it has waited, the more urgent
        time_waiting = (timezone.now() - task.created_at).total_seconds()
        # If no resource requirements, use 1 so we don't divide by zero
        resource_weight = task.resource_requirements.get("cpu", 0.5) + task.resource_requirements.get("ram",
                                                                                                            0.5) / 2
        # Give a penalty for tasks that have gone stale multiple times
        stale_penalty = task.stale_count * STALE_PENALTY_MULTIPLIER

        # Status weight: in_progress tasks get a slight boost
        status_weight = IN_PROGRESS_BOOST if task.status == 'in_progress' else 1.0

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
        tasks_to_activate = self.select_tasks_to_activate(backlog_tasks, available_slots)

        for task in tasks_to_activate:
            task.status = 'in_queue'
            task.last_attempted = timezone.now()
            task.save()
            logger.info(f"Moved task {task.id} to queue for assignment.")

    def reorder_active_queue(self):
        """
        Swap tasks from the active queue with backlog tasks if the latter have higher priority,
        but only if the active tasks are unassigned. (We do not swap tasks that already started.)
        Don't swap tasks if impact is minimal (30% threshold).
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

        if self.calculate_task_priority(highest_backlog) > self.calculate_task_priority(lowest_active) * 1.3: # 30% threshold to prevent minimal impact swapping
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
        mechanism = getattr(settings, "ORCHESTRATION_MECHANISM", "custom")
        active_tasks = Task.objects.filter(Q(status='in_progress') | Q(status='in_queue'))

        for task in active_tasks:
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

            if mechanism == "fifo":
                # Assign nodes just in DB-order (FIFO, no ranking)
                ranked_nodes = list(candidate_nodes.order_by("last_heartbeat"))
            else:
                def calculate_suitability(node):
                    """Compute suitability score based on resource availability and match with task requirements."""
                    node_free_cpu = node.free_resources.get('cpu', 0)
                    node_free_ram = node.free_resources.get('ram', 0)

                    task_cpu = task.resource_requirements.get('cpu', 1)
                    task_ram = task.resource_requirements.get('ram', 1)

                    cpu_score = abs(node_free_cpu - task_cpu) / max(task_cpu, 1)
                    ram_score = abs(node_free_ram - task_ram) / max(task_ram, 1)

                    return cpu_score + ram_score  # lower is better

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

    def validate_task(self, task_id):
        """
        Validates task results using trust-weighted majority voting and adjusts node trust indexes.
        """
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            logger.error(f"[VALIDATION] Task {task_id} does not exist.")
            return False

        if task.status != 'completed':
            logger.warning(f"[VALIDATION] Task {task_id} is not completed yet.")
            return False

        # aggregate results from task assignments
        assignments = TaskAssignment.objects.filter(task=task, completed_at__isnull=False)
        if assignments.count() < task.overlap_count:
            logger.warning("Not all assignments are completed yet.")
            return False

        result_weights = defaultdict(float)
        node_results = {}

        for assignment in assignments:
            node = assignment.node
            result = assignment.result.get('output') if assignment.result else None
            if result:
                result_weights[result] += node.trust_index
                node_results[node.id] = result

        if not result_weights:
            logger.warning(f"[VALIDATION] No valid results found for Task {task_id}.")
            task.status = 'failed'
            task.save()
            return False

        # Find the result with the maximum trust weight
        validated_result, max_weight = max(result_weights.items(), key=lambda x: x[1])
        total_weight = sum(result_weights.values())

        # Determine if the result passes the validation threshold
        validation_threshold = VALIDATION_THRESHOLD
        if max_weight / total_weight >= validation_threshold:
            task.result = {"validated_output": validated_result, "trust_score": max_weight / total_weight * 10}
            task.status = 'validated'
            task.save()
            logger.info(f"[VALIDATION] Task {task_id} validated successfully with result: {validated_result}")

            # Adjust trust indexes based on validation
            for assignment in assignments:
                node = assignment.node
                if node_results.get(node.id) == validated_result:
                    node.trust_index = min(node.trust_index + TRUST_INCREMENT, TRUST_INDEX_MAX)  # Cap at 10.0
                    logger.info(f"[TRUST] Node {node.name} trust index increased to {node.trust_index}")
                else:
                    node.trust_index = max(node.trust_index - TRUST_DECREMENT, TRUST_INDEX_MIN)  # Floor at 1.0
                    logger.info(f"[TRUST] Node {node.name} trust index decreased to {node.trust_index}")
                node.save()

            return True
        else:
            task.status = 'failed'
            task.save()
            logger.warning(f"[VALIDATION] Task {task_id} failed validation. Insufficient trust weight.")

            return False

    def retry_failed_tasks(self):
        """
        Retry tasks marked as 'failed' by resetting their status and stale counters,
        allowing them to be redistributed.
        """
        # Fetch tasks that are marked as 'failed' and haven't exceeded retry limits
        retryable_tasks = Task.objects.filter(
            status='failed',
            stale_count__lt=self.max_stale_count  # ensure we dont retry tasks indefinitely
        )

        if not retryable_tasks.exists():
            logger.info("[retry_failed_tasks] No retryable failed tasks found.")
            return

        retried_count = 0
        for task in retryable_tasks:
            TaskAssignment.objects.filter(task=task).delete()
            task.status = 'pending'
            task.last_attempted = timezone.now()
            task.save()
            retried_count += 1
            logger.info(f"[retry_failed_tasks] Task {task.id} reset and moved back to 'pending', assignments cleared.")

    def handle_persistently_failing_tasks(self):
        """
        Delete tasks that have exceeded the maximum retry threshold or are invalid.
        """

        persistently_failing_tasks = Task.objects.filter(
            stale_count__gte=self.max_stale_count,
            status='failed'
        )

        if not persistently_failing_tasks.exists():
            logger.info("[handle_persistently_failing_tasks] No tasks exceeded max retry limit.")
            return

        task_ids = [str(task.id) for task in persistently_failing_tasks]
        deleted_count, _ = persistently_failing_tasks.delete()

        logger.warning(
            f"[handle_persistently_failing_tasks] Deleted {deleted_count} persistently failing task(s): {', '.join(task_ids)}"
        )

    def validate_docker_image(self, task_id):
        """
        Validate Docker image before allowing the task to proceed.
        """
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return {"status": "invalid", "error": f"Task {task_id} does not exist."}

        image = task.container_spec.get('image')
        credentials = task.container_spec.get('docker_credentials', {})

        try:
            client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            # Handle private registry login
            if credentials:
                client.login(
                    username=credentials.get('username'),
                    password=credentials.get('password'),
                    registry=credentials.get('registry', 'https://index.docker.io/v1/')
                )

            client.images.pull(image)
            task.status = 'pending'
            task.save()
            return {"status": "valid"}
        except docker.errors.APIError as e:
            task.status = 'invalid'
            task.save()
            return {"status": "invalid", "error": f"API Error: {str(e)}"}
        except docker.errors.ImageNotFound:
            task.status = 'invalid'
            task.save()
            return {"status": "invalid", "error": f"Image '{image}' not found."}
        except DockerException as e:
            task.status = 'invalid'
            task.save()
            return {"status": "invalid", "error": f"Docker exception: {str(e)}"}
        except Exception as e:
            task.status = 'invalid'
            task.save()
            return {"status": "invalid", "error": f"Unexpected error: {str(e)}"}
        finally:
            if credentials:
                client.logout()
