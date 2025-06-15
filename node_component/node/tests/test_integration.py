import time
import threading
import pytest
from unittest.mock import patch, MagicMock, mock_open
import json

from node_manager import NodeManager
from node_local_server import app, node_manager

def test_node_manager_start_runs_heartbeat_and_task_loop():
    with patch("heartbeat.Heartbeat.start") as mock_heartbeat_start, \
         patch("api_client.APIClient.fetch_task") as mock_fetch_task, \
         patch("task_executor.TaskExecutor.execute_task") as mock_execute:

        mock_fetch_task.side_effect = [{"id": "task1", "container_spec": {"image": "alpine", "command": "echo hi"}}] * 2

        manager = NodeManager()
        manager.node_id = "node-abc"  # simulate already registered

        # Start node manager in a thread to test async behavior
        thread = threading.Thread(target=manager.start)
        thread.start()

        # Let the loop run a bit
        time.sleep(2)

        # Stop manager
        manager.stop()
        thread.join(timeout=3)

        assert mock_heartbeat_start.called
        assert mock_fetch_task.call_count >= 1
        assert mock_execute.call_count >= 1


def test_flask_register_and_start_flow():
    client = app.test_client()

    # Mock the internal registration and start logic
    with patch.object(node_manager, "register") as mock_register, \
         patch.object(node_manager, "start") as mock_start:

        mock_register.return_value = True
        mock_start.return_value = None

        # Call register
        response = client.post("/api/node/register", json={"name": "integration-node"})
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        mock_register.assert_called_once_with("integration-node")

        # Call start
        response = client.post("/api/node/start")
        assert response.status_code == 200
        assert "message" in response.get_json()
        assert mock_start.called


def test_flask_stop_node():
    client = app.test_client()

    with patch.object(node_manager, "stop") as mock_stop:
        mock_stop.return_value = None

        response = client.post("/api/node/stop")
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        mock_stop.assert_called_once()


def test_get_node_status_registered():
    mock_config = json.dumps({
        "node_id": "abc-123",
        "last_task_id": "task-789"
    })

    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_config)):

        client = app.test_client()
        response = client.get("/api/node")
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "registered"
        assert data["node_id"] == "abc-123"
        assert "resource_usage" in data or data["resource_usage"] is None


def test_get_node_status_unregistered():
    with patch("os.path.exists", return_value=False):
        client = app.test_client()
        response = client.get("/api/node")
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "unregistered"
        assert "node_id" in data