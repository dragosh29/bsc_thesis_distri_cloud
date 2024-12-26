from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Node(models.Model):
    """
    Represents a connected peer in the network. Nodes periodically
    report their resource usage so the hub can make informed scheduling decisions.
    """
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()

    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive'),
                 ('busy', 'Busy'), ('failed', 'Failed')],
        default='inactive'
    )

    trust_index = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )  # 0 (untrusted) to 10 (fully trusted)

    # Resource capacity (static or semi-static info)
    resources_capacity = models.JSONField(
        default=dict
        # Example structure: {
        #   "cpu_cores": 4,
        #   "ram_gb": 16,
        #   "gpu": false
        # }
    )

    # Current usage (dynamic) - Node reports usage periodically
    resources_usage = models.JSONField(
        default=dict
        # Example structure: {
        #   "cpu_cores_in_use": 2,
        #   "ram_gb_in_use": 8
        # }
    )

    # Last heartbeat or status update
    last_heartbeat = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def is_available_for_task(self, task_requirements: dict) -> bool:
        """
        Example helper method:
        Check if this Node has enough free resources for `task_requirements`.
        """
        capacity = self.resources_capacity
        usage = self.resources_usage
        # Very simplified logic below (pseudo-code):
        #   free_cpu = capacity["cpu_cores"] - usage["cpu_cores_in_use"]
        #   free_ram = capacity["ram_gb"] - usage["ram_gb_in_use"]
        #   needed_cpu = task_requirements.get("cpu_cores", 1)
        #   needed_ram = task_requirements.get("ram_gb", 1)
        #   return (free_cpu >= needed_cpu) and (free_ram >= needed_ram)

        # You'd parse and compare carefully. For now, we'll just stub it out:
        return True


class Task(models.Model):
    """
    A task to be executed by one or more Nodes. Contains a container spec
    for Docker-based execution and resource requirements so we can
    schedule properly. We also keep track of overlap_count for
    majority-based validation if needed.
    """
    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('in_progress', 'In Progress'),
                 ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )

    # If you want ONLY one node assigned, keep a single FK:
    assigned_node = models.ForeignKey(Node, null=True, blank=True, on_delete=models.SET_NULL)

    # If you want multiple nodes to run the same task for cross-validation,
    # you could use a ManyToMany (see "TaskAssignment" model below).
    # But let's keep assigned_node for "primary" assignment.

    trust_index_required = models.FloatField(
        default=5.0,  # e.g., requires trust_index >= 5
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )

    container_spec = models.JSONField(
        default=dict
        # e.g., {"image": "python:3.9", "command": "python main.py", "env": {...}}
    )

    # Resource requirements for scheduling
    resource_requirements = models.JSONField(
        default=dict
        # e.g., {"cpu_cores": 2, "ram_gb": 4}
    )

    # Overlap or majority-based validations:
    # e.g., how many nodes to run the same task for cross-check
    overlap_count = models.PositiveSmallIntegerField(default=1)

    result = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task {self.id}: {self.status}"


class TaskAssignment(models.Model):
    """
    If you want multiple Nodes to run the same Task simultaneously
    for cross-validation, you can track each assignment here.
    - 'node' runs the task
    - 'task' is the job to execute
    - 'result' is what that node computed
    - 'validated' if the node's result was accepted
    """
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    result = models.JSONField(null=True, blank=True)
    validated = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TaskAssignment (Task {self.task.id}, Node {self.node.id})"


class Heartbeat(models.Model):
    """
    Track health pings from Nodes. The Node can send
    additional info about resource usage or status in the future.
    """
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[('healthy', 'Healthy'), ('unhealthy', 'Unhealthy')],
        default='healthy'
    )

    def __str__(self):
        return f"Heartbeat from {self.node.name} at {self.timestamp}"
