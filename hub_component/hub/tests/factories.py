import factory
import uuid
from django.utils import timezone
from hub.models import Node, Task, TaskAssignment, Heartbeat


class NodeFactory(factory.django.DjangoModelFactory):
    """Factory for creating Node instances for testing."""
    class Meta:
        model = Node

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Node-{n}")
    ip_address = factory.Faker("ipv4")
    status = "active"
    trust_index = 7.5
    resources_capacity = {"cpu": 4, "ram": 16}
    free_resources = {"cpu": 2, "ram": 8}
    last_heartbeat = factory.LazyFunction(timezone.now)


class TaskFactory(factory.django.DjangoModelFactory):
    """Factory for creating Task instances for testing."""
    class Meta:
        model = Task

    id = factory.LazyFunction(uuid.uuid4)
    description = "Run test workload"
    status = "pending"
    container_spec = {"image": "python:3.9", "command": "python main.py"}
    resource_requirements = {"cpu": 1, "ram": 2}
    trust_index_required = 5.0
    overlap_count = 1


class TaskAssignmentFactory(factory.django.DjangoModelFactory):
    """Factory for creating TaskAssignment instances for testing."""
    class Meta:
        model = TaskAssignment

    id = factory.LazyFunction(uuid.uuid4)
    node = factory.SubFactory(NodeFactory)
    task = factory.SubFactory(TaskFactory)


class HeartbeatFactory(factory.django.DjangoModelFactory):
    """Factory for creating Heartbeat instances for testing."""
    class Meta:
        model = Heartbeat

    node = factory.SubFactory(NodeFactory)
    timestamp = factory.LazyFunction(timezone.now)
    status = "healthy"