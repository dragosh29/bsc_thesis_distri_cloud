import pytest
from django.utils import timezone
from datetime import timedelta
from freezegun import freeze_time

from hub.tests.factories import NodeFactory, TaskFactory, TaskAssignmentFactory, HeartbeatFactory


@pytest.mark.django_db
class TestNodeModel:

    def test_is_available_for_task_true(self):
        node = NodeFactory(free_resources={"cpu": 4, "ram": 8})
        task_req = {"cpu": 2, "ram": 4}
        assert node.is_available_for_task(task_req) is True

    def test_is_available_for_task_false_due_to_cpu(self):
        node = NodeFactory(free_resources={"cpu": 1, "ram": 8})
        task_req = {"cpu": 2, "ram": 4}
        assert node.is_available_for_task(task_req) is False

    @freeze_time("2025-06-01 12:00:00")
    def test_mark_inactive_if_stale_marks_inactive(self):
        with freeze_time("2025-06-01 11:58:30"):
            node = NodeFactory(status="active")

        node.mark_inactive_if_stale(threshold_seconds=60)
        node.refresh_from_db()
        assert node.status == "inactive"

    @freeze_time("2025-06-01 12:00:00")
    def test_mark_inactive_if_stale_does_nothing_if_fresh(self):
        node = NodeFactory(
            status="active",
            last_heartbeat=timezone.now() - timedelta(seconds=30)
        )
        node.mark_inactive_if_stale(threshold_seconds=60)
        node.refresh_from_db()
        assert node.status == "active"


@pytest.mark.django_db
class TestTaskModel:

    def test_mark_stale_increments_counter(self):
        task = TaskFactory(stale_count=0)
        task.mark_stale()
        task.refresh_from_db()
        assert task.stale_count == 1

    def test_reset_stale_sets_zero(self):
        task = TaskFactory(stale_count=5)
        task.reset_stale()
        task.refresh_from_db()
        assert task.stale_count == 0

    def test_get_assigned_nodes_returns_names(self):
        node1 = NodeFactory(name="Alpha")
        node2 = NodeFactory(name="Beta")
        task = TaskFactory()
        TaskAssignmentFactory(task=task, node=node1)
        TaskAssignmentFactory(task=task, node=node2)

        names = task.get_assigned_nodes()
        assert "Alpha" in names and "Beta" in names


@pytest.mark.django_db
class TestTaskAssignmentModel:

    def test_str_representation(self):
        assignment = TaskAssignmentFactory()
        s = str(assignment)
        assert f"Task {assignment.task.id}" in s
        assert f"Node {assignment.node.id}" in s


@pytest.mark.django_db
class TestHeartbeatModel:

    def test_update_node_status_healthy(self):
        node = NodeFactory(status="inactive")
        heartbeat = HeartbeatFactory(node=node, status="healthy")
        heartbeat.update_node_status()
        node.refresh_from_db()
        assert node.status == "active"

    def test_update_node_status_unhealthy(self):
        node = NodeFactory(status="active")
        heartbeat = HeartbeatFactory(node=node, status="unhealthy")
        heartbeat.update_node_status()
        node.refresh_from_db()
        assert node.status == "inactive"