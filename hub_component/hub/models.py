# models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Node(models.Model):
    """
    Represents a connected peer in the network. Nodes periodically
    report their resource usage so the hub can make informed scheduling decisions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()

    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('busy', 'Busy'),
        ],
        default='inactive'
    )

    trust_index = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )  # 0 (untrusted) to 10 (fully trusted)

    # Resource capacity (static or semi-static info)
    resources_capacity = models.JSONField(
        default=dict
        # Example: {
        #   "cpu": 4,
        #   "ram": 16,
        #   "gpu": false
        # }
    )

    # Current usage (dynamic) - Node reports usage periodically
    free_resources = models.JSONField(
        default=dict
        # Example: {
        #   "cpu": 2,
        #   "ram": 8
        # }
    )

    last_heartbeat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def is_available_for_task(self, task_requirements: dict) -> bool:
        """
        Check if this Node has enough free resources for `task_requirements`.
        """
        free = self.free_resources or {}
        free_cpu = free.get("cpu", 0)
        free_ram = free.get("ram", 0)

        needed_cpu = task_requirements.get("cpu", 1)
        needed_ram = task_requirements.get("ram", 1)

        return (free_cpu >= needed_cpu) and (free_ram >= needed_ram)

    def mark_inactive_if_stale(self, threshold_seconds=60):
        """
        Mark this node as inactive if no heartbeat in `threshold_seconds`.
        """
        time_since_heartbeat = (timezone.now() - self.last_heartbeat).total_seconds()
        if time_since_heartbeat > threshold_seconds:
            if self.status != 'inactive':
                self.status = 'inactive'
                self.save()


class Task(models.Model):
    """
    A task to be executed by one or more Nodes. Contains a container spec
    for Docker-based execution and resource requirements so we can
    schedule properly.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_queue', 'In Queue'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('validating', 'Validating'),
            ('validated', 'Validated'),
            ('invalid', 'Invalid')
        ],
        default='pending'
    )

    assigned_nodes = models.ManyToManyField(
        'Node',
        through='TaskAssignment',
        related_name='assigned_tasks'
    )

    trust_index_required = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )

    container_spec = models.JSONField(
        default=dict
        # e.g., {"image": "python:3.9", "command": "python main.py", "env": {...}}
    )

    resource_requirements = models.JSONField(
        default=dict
        # e.g., {"cpu": 2, "ram": 4}
    )

    overlap_count = models.PositiveSmallIntegerField(default=1)

    result = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    submitted_by = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        related_name='submitted_tasks',
        null=True,
        blank=True
    )

    stale_count = models.PositiveIntegerField(default=0)
    last_attempted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Task {self.id}: {self.status}"

    def mark_stale(self):
        """
        Increment the stale counter when a task can't be assigned or fails repeatedly.
        """
        self.stale_count = models.F('stale_count') + 1
        self.save(update_fields=['stale_count'])
        self.refresh_from_db()

    def reset_stale(self):
        """
        Reset the stale count if/when the task is successfully assigned.
        """
        self.stale_count = 0
        self.save(update_fields=['stale_count'])

    def get_assigned_nodes(self):
        """
        Get the list of nodes assigned to this task.
        """
        res = ''
        for node in self.assigned_nodes.all():
            res = res + node.name + ' '
        return res


class TaskAssignment(models.Model):
    """
    Multiple Nodes can run the same Task simultaneously
    for cross-validation or redundancy. This model records:
    - Which node runs the task
    - Timestamps for assignment and completion
    - The node's result
    - Whether that result was validated/accepted
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    result = models.JSONField(null=True, blank=True)
    validated = models.BooleanField(default=False)

    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TaskAssignment (Task {self.task.id}, Node {self.node.id})"


class Heartbeat(models.Model):
    """
    Track health pings from Nodes. The Node can send
    additional info about resource usage or status in the future.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('unhealthy', 'Unhealthy')
        ],
        default='healthy'
    )

    def __str__(self):
        return f"Heartbeat from {self.node.name} at {self.timestamp}"

    def update_node_status(self):
        """
        If this heartbeat is 'healthy', mark the node 'active';
        if 'unhealthy', mark it 'inactive'.
        """
        if self.status == 'healthy' and self.node.status != 'active':
            self.node.status = 'active'
            self.node.save()
        elif self.status == 'unhealthy':
            if self.node.status != 'inactive':
                self.node.status = 'inactive'
                self.node.save()
