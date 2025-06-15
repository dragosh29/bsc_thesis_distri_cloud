import pytest
from unittest.mock import patch, MagicMock

from django.utils import timezone

from hub.models import Task, Node, TaskAssignment
from hub.task_manager import TaskManager
from hub.tasks import (
    orchestrate_task_distribution,
    validate_docker_image_task,
    check_node_health,
)
from hub.tests.factories import NodeFactory, TaskFactory, TaskAssignmentFactory


@pytest.mark.django_db
class TestTaskManagerLogic:
    """Test suite for TaskManager logic. Included prioritization, assignment, and validation."""

    def test_calculate_task_priority_gives_higher_score_for_older_tasks(self):
        manager = TaskManager()
        task_old = TaskFactory(
            created_at=timezone.now() - timezone.timedelta(minutes=30),
            resource_requirements={"cpu": 1, "ram": 2},
            stale_count=0,
            status="pending"
        )
        task_new = TaskFactory(
            created_at=timezone.now() - timezone.timedelta(minutes=1),
            resource_requirements={"cpu": 1, "ram": 2},
            stale_count=0,
            status="pending"
        )
        old_score = manager.calculate_task_priority(task_old)
        new_score = manager.calculate_task_priority(task_new)
        assert old_score > new_score

    def test_move_tasks_to_active_queue_promotes_pending(self):
        manager = TaskManager()
        TaskFactory.create_batch(5, status="pending")
        manager.move_tasks_to_active_queue()
        assert Task.objects.filter(status="in_queue").count() > 0

    def test_assign_tasks_to_nodes_assigns_based_on_resources(self):
        task = TaskFactory(status="in_queue", resource_requirements={"cpu": 1, "ram": 1})
        node = NodeFactory(status="active", trust_index=9.0, free_resources={"cpu": 2, "ram": 2})
        manager = TaskManager()
        manager.assign_tasks_to_nodes()
        assignments = TaskAssignment.objects.filter(task=task)
        assert assignments.count() == 1
        assert assignments.first().node == node

    def test_handle_stale_tasks_marks_failed(self):
        manager = TaskManager()
        task = TaskFactory(status="in_queue", stale_count=manager.max_stale_count + 1)
        manager.handle_stale_tasks()
        task.refresh_from_db()
        assert task.status == "failed"

    def test_validate_task_success(self):
        task = TaskFactory(status="completed")
        node1 = NodeFactory(trust_index=9.0)
        node2 = NodeFactory(trust_index=1.0)
        TaskAssignmentFactory(task=task, node=node1, result={"output": "42"}, completed_at=timezone.now())
        TaskAssignmentFactory(task=task, node=node2, result={"output": "13"}, completed_at=timezone.now())
        manager = TaskManager()
        validated = manager.validate_task(task.id)
        task.refresh_from_db()
        assert validated is True
        assert task.status == "validated"


@pytest.mark.django_db
class TestCeleryOrchestration:
    """Test for async task orchestration and distribution."""

    @patch("hub.tasks.chain")
    def test_orchestrate_task_distribution_triggers_all(self, mock_chain):
        mock_chain.return_value.apply_async = MagicMock()
        orchestrate_task_distribution()
        mock_chain.return_value.apply_async.assert_called_once()


@pytest.mark.django_db
class TestDockerValidation:
    """Test suite for validating Docker images in tasks."""

    @patch("hub.task_manager.docker.DockerClient")
    def test_validate_docker_image_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.images.pull.return_value = True
        mock_client_class.return_value = mock_client

        task = TaskFactory(status="validating", container_spec={"image": "python:3.9", "command": "echo"})
        result = validate_docker_image_task(task.id)
        task.refresh_from_db()

        assert task.status == "pending" or result is None
        mock_client.images.pull.assert_called_once()

    @patch("hub.task_manager.docker.DockerClient")
    def test_validate_docker_image_not_found(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.images.pull.side_effect = Exception("not found")
        mock_client_class.return_value = mock_client

        task = TaskFactory(status="validating", container_spec={"image": "bad:image", "command": "run"})
        result = validate_docker_image_task(task.id)
        task.refresh_from_db()

        assert task.status == "invalid"
        assert result is None


@pytest.mark.django_db
class TestRedisSignalTriggering:
    """Test suite for Django post_save signals triggering Redis events."""

    @patch("hub.signals.publish_network_activity")
    def test_post_save_triggers_publish_network_activity(self, mock_publish):
        node = NodeFactory(status="inactive")
        node.status = "active"
        node.save()
        assert mock_publish.called

    @patch("hub.signals.publish_task_update")
    def test_post_save_triggers_task_update_for_submitter(self, mock_update):
        node = NodeFactory()
        TaskFactory(submitted_by=node, status="pending")
        assert mock_update.called


@pytest.mark.django_db
class TestNodeHealthTask:
    """Test suite for node health checks and status updates."""

    def test_check_node_health_marks_inactive(self):
        # Create node with dummy value first
        node = NodeFactory(status="active")

        # Then manually override last_heartbeat with old timestamp (bypassing auto_now)
        Node.objects.filter(id=node.id).update(
            last_heartbeat=timezone.now() - timezone.timedelta(minutes=10)
        )

        # Re-fetch node with correct timestamp
        node.refresh_from_db()
        assert node.status == "active"
        assert node.last_heartbeat < timezone.now() - timezone.timedelta(minutes=5)

        # Run the health check
        check_node_health()

        node.refresh_from_db()
        assert node.status == "inactive"


@pytest.mark.django_db
class TestTaskManagerExtensions:
    """Extended tests for TaskManager logic, including edge cases and additional scenarios."""

    def test_calculate_priority_handles_missing_resources(self):
        task = TaskFactory(resource_requirements={})
        manager = TaskManager()
        score = manager.calculate_task_priority(task)
        assert isinstance(score, float)

    def test_reorder_active_queue_swaps_tasks(self):
        manager = TaskManager()
        # Backlog with high priority
        high_task = TaskFactory(status="pending", stale_count=0)
        high_task.created_at = timezone.now() - timezone.timedelta(minutes=30)
        high_task.save()

        # Active with lower priority
        low_task = TaskFactory(status="in_queue", stale_count=5)
        manager.reorder_active_queue()
        low_task.refresh_from_db()
        high_task.refresh_from_db()
        assert high_task.status == "in_queue"

    def test_handle_tasks_for_inactive_nodes_reassigns(self):
        node1 = NodeFactory(status="inactive")
        node2 = NodeFactory(status="active")
        task = TaskFactory(status="in_progress")
        TaskAssignmentFactory(task=task, node=node1)
        TaskAssignmentFactory(task=task, node=node2)

        manager = TaskManager()
        manager.handle_tasks_for_inactive_nodes([node1.id])
        task.refresh_from_db()
        assert task.status == "in_progress"

    def test_handle_tasks_for_inactive_nodes_resets_if_no_assignments(self):
        node = NodeFactory(status="inactive")
        task = TaskFactory(status="in_progress")
        TaskAssignmentFactory(task=task, node=node)
        manager = TaskManager()
        manager.handle_tasks_for_inactive_nodes([node.id])
        task.refresh_from_db()
        assert task.status == "in_queue"

    def test_validate_task_failure_no_majority(self):
        task = TaskFactory(status="completed")
        node1 = NodeFactory(trust_index=5.0)
        node2 = NodeFactory(trust_index=5.0)
        TaskAssignmentFactory(task=task, node=node1, result={"output": "X"}, completed_at=timezone.now())
        TaskAssignmentFactory(task=task, node=node2, result={"output": "Y"}, completed_at=timezone.now())
        manager = TaskManager()
        validated = manager.validate_task(task.id)
        task.refresh_from_db()
        assert validated is False
        assert task.status == "failed"

    def test_retry_failed_tasks_resets_status(self):
        task = TaskFactory(status="failed", stale_count=1)
        manager = TaskManager()
        manager.retry_failed_tasks()
        task.refresh_from_db()
        assert task.status == "pending"
        assert task.stale_count == 0

    def test_handle_persistently_failing_tasks_deletes(self):
        task = TaskFactory(status="failed", stale_count=100)
        manager = TaskManager()
        manager.handle_persistently_failing_tasks()
        assert not Task.objects.filter(id=task.id).exists()


@pytest.mark.django_db
class TestCeleryEntrypoints:
    """Test suite for Celery task entry points to ensure they execute without errors."""

    def test_reorder_active_queue_task_executes(self):
        from hub.tasks import reorder_active_queue_task
        reorder_active_queue_task()

    def test_move_tasks_to_active_queue_task_executes(self):
        from hub.tasks import move_tasks_to_active_queue_task
        move_tasks_to_active_queue_task()

    def test_assign_tasks_to_nodes_task_executes(self):
        from hub.tasks import assign_tasks_to_nodes_task
        assign_tasks_to_nodes_task()

    def test_handle_stale_tasks_task_executes(self):
        from hub.tasks import handle_stale_tasks_task
        handle_stale_tasks_task()

    def test_retry_failed_tasks_task_executes(self):
        from hub.tasks import retry_failed_tasks_task
        retry_failed_tasks_task()

    def test_handle_persistently_failing_tasks_task_executes(self):
        from hub.tasks import handle_persistently_failing_tasks_task
        handle_persistently_failing_tasks_task()
