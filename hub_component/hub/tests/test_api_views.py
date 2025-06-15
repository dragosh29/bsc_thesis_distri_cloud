import http

import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from hub.tests.factories import NodeFactory, TaskFactory
from hub.models import Node, TaskAssignment


@pytest.mark.django_db
class TestNodeAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_register_node_success(self):
        payload = {
            "name": "NodeAlpha",
            "ip_address": "10.0.0.1",
            "resources_capacity": {"cpu": 4, "ram": 8},
            "free_resources": {"cpu": 2, "ram": 4}
        }
        response = self.client.post(reverse("register_node"), data=payload, format="json")
        assert response.status_code == 201
        assert Node.objects.count() == 1

    def test_register_node_invalid(self):
        response = self.client.post(reverse("register_node"), data={}, format="json")
        assert response.status_code == 400

    def test_list_nodes(self):
        NodeFactory.create_batch(3)
        response = self.client.get(reverse("list_nodes"))
        assert response.status_code == 200
        assert len(response.data) == 3

    def test_fetch_node_by_id(self):
        node = NodeFactory()
        response = self.client.get(reverse("fetch_node", kwargs={"node_id": node.id}))
        assert response.status_code == 200
        assert response.data["id"] == str(node.id)

    def test_fetch_node_invalid(self):
        response = self.client.get(reverse("fetch_node", kwargs={"node_id": "00000000-0000-0000-0000-000000000000"}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestHeartbeatAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_heartbeat_updates_node(self):
        node = NodeFactory(status="inactive", free_resources={"cpu": 1})
        response = self.client.post(reverse("node_heartbeat"), data={
            "node_id": str(node.id),
            "free_resources": {"cpu": 3, "ram": 5}
        }, format="json")
        node.refresh_from_db()
        assert response.status_code == 200
        assert node.status == "active"
        assert node.free_resources["cpu"] == 3

    def test_heartbeat_missing_node_id(self):
        response = self.client.post(reverse("node_heartbeat"), data={}, format="json")
        assert response.status_code == 400

    def test_heartbeat_node_not_found(self):
        response = self.client.post(reverse("node_heartbeat"), data={
            "node_id": "00000000-0000-0000-0000-000000000000"
        }, format="json")
        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_submit_task_success(self):
        node = NodeFactory()
        payload = {
            "submitted_by": str(node.id),
            "description": "Sim test",
            "container_spec": {"image": "python:3.9", "command": "run.py"},
            "resource_requirements": {"cpu": 2, "ram": 4},
            "trust_index_required": 5.0,
            "overlap_count": 2
        }
        response = self.client.post(reverse("submit_task"), data=payload, format="json")
        assert response.status_code == 201
        assert "task_id" in response.data

    def test_submit_task_invalid_node(self):
        payload = {
            "submitted_by": "00000000-0000-0000-0000-000000000000",
            "description": "bad node",
            "container_spec": {"image": "img", "command": "cmd"}
        }
        response = self.client.post(reverse("submit_task"), data=payload, format="json")
        assert response.status_code == 404

    def test_submit_task_missing_fields(self):
        response = self.client.post(reverse("submit_task"), data={}, format="json")
        assert response.status_code == 400

    def test_list_tasks(self):
        TaskFactory.create_batch(2)
        response = self.client.get(reverse("list_tasks"))
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_get_task_with_assignment(self):
        node = NodeFactory()
        task = TaskFactory()
        TaskAssignment.objects.create(task=task, node=node)
        url = reverse("get_task", kwargs={"task_id": task.id})
        response = self.client.get(f"{url}?node_id={node.id}")
        assert response.status_code == 200
        assert response.data["assignment"]["node_id"] == str(node.id)

    def test_get_task_no_assignment(self):
        task = TaskFactory()
        node = NodeFactory()
        url = reverse("get_task", kwargs={"task_id": task.id})
        response = self.client.get(f"{url}?node_id={node.id}")
        assert response.status_code == 200
        assert "assignment" in response.data

    def test_get_task_invalid_id(self):
        response = self.client.get(reverse("get_task", kwargs={"task_id": "00000000-0000-0000-0000-000000000000"}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskAssignmentAPI:

    def setup_method(self):
        self.client = APIClient()

    def test_fetch_task_missing_node_id(self):
        response = self.client.get(reverse("fetch_task"))
        assert response.status_code == 400

    def test_fetch_task_node_not_found(self):
        response = self.client.get(reverse("fetch_task"), {"node_id": "00000000-0000-0000-0000-000000000000"})
        assert response.status_code == 404

    def test_fetch_task_none_assigned(self):
        node = NodeFactory()
        response = self.client.get(reverse("fetch_task"), {"node_id": str(node.id)})
        assert response.status_code == 404

    def test_fetch_task_assigned(self):
        node = NodeFactory()
        task = TaskFactory()
        TaskAssignment.objects.create(task=task, node=node)
        response = self.client.get(reverse("fetch_task"), {"node_id": str(node.id)})
        assert response.status_code == 200
        assert response.data["id"] == str(task.id)

    def test_submit_task_result_success(self):
        node = NodeFactory()
        task = TaskFactory(status="in_progress")
        TaskAssignment.objects.create(task=task, node=node)
        payload = {
            "task_id": str(task.id),
            "node_id": str(node.id),
            "result": {"output": "42"}
        }
        response = self.client.post(reverse("submit_task_result"), data=payload, format="json")
        assert response.status_code == 200

    def test_submit_task_result_twice(self):
        node = NodeFactory()
        task = TaskFactory(status="in_progress")
        TaskAssignment.objects.create(task=task, node=node, completed_at=timezone.now(), result={"output": "X"})
        payload = {
            "task_id": str(task.id),
            "node_id": str(node.id),
            "result": {"output": "Y"}
        }
        response = self.client.post(reverse("submit_task_result"), data=payload, format="json")
        assert response.status_code == 400

    def test_submit_task_result_missing_fields(self):
        response = self.client.post(reverse("submit_task_result"), data={}, format="json")
        assert response.status_code == 400

    def test_submit_task_result_invalid_assignment(self):
        node = NodeFactory()
        task = TaskFactory()
        payload = {
            "task_id": str(task.id),
            "node_id": str(node.id),
            "result": {"output": "fail"}
        }
        response = self.client.post(reverse("submit_task_result"), data=payload, format="json")
        assert response.status_code == 404


@pytest.mark.django_db
class TestTaskQueries:

    def setup_method(self):
        self.client = APIClient()

    def test_get_submitted_tasks_success(self):
        node = NodeFactory()
        TaskFactory.create_batch(2, submitted_by=node)
        response = self.client.get(reverse("get_submitted_tasks"), {"node_id": node.id})
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_get_submitted_tasks_invalid_node(self):
        response = self.client.get(reverse("get_submitted_tasks"), {"node_id": "00000000-0000-0000-0000-000000000000"})
        assert response.status_code == 404

    def test_get_submitted_tasks_missing_param(self):
        response = self.client.get(reverse("get_submitted_tasks"))
        assert response.status_code == 400


@pytest.mark.django_db
class TestNetworkActivity:

    def setup_method(self):
        self.client = APIClient()

    def test_network_activity_returns_valid_payload(self):
        response = self.client.get(reverse("network_activity"))
        assert response.status_code == 200
        assert "timestamp" in response.data
        assert "data" in response.data


@pytest.mark.django_db
class TestSSEViews:

    def setup_method(self):
        self.client = APIClient()

    def test_sse_network_activity_stream_response(self):
        response = self.client.get(reverse("sse_network_activity"))
        assert response.status_code == 200
        assert response.get("Content-Type") == "text/event-stream"

    def test_sse_task_updates_missing_node_id(self):
        response = self.client.get(reverse("sse_task_updates"), follow=True)
        assert response.status_code == 400
        assert response.reason_phrase == http.HTTPStatus.BAD_REQUEST.phrase

    def test_sse_task_updates_valid_node_id(self):
        response = self.client.get(reverse("sse_task_updates") + "?node_id=abc")
        assert response.status_code == 200
        assert response.get("Content-Type") == "text/event-stream"
