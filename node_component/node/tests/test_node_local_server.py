import json
import pytest
from unittest.mock import patch, MagicMock

from node_local_server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@patch("node_local_server.node_manager")
def test_get_node_status_registered(mock_manager, client):
    mock_manager.node_id = "abc-123"
    mock_manager.running = True
    mock_manager.get_resource_usage.return_value = {"cpu": 10, "ram": 2}

    with patch("builtins.open", create=True):
        with patch("os.path.exists", return_value=True), \
             patch("json.load", return_value={"node_id": "abc-123", "last_task_id": "xyz"}):
            response = client.get("/api/node")
            assert response.status_code == 200
            assert response.json["status"] == "registered"
            assert response.json["node_id"] == "abc-123"


def test_get_node_status_unregistered(client):
    with patch("os.path.exists", return_value=False):
        response = client.get("/api/node")
        assert response.status_code == 200
        assert response.json["status"] == "unregistered"


@patch("node_local_server.node_manager.register", return_value=True)
def test_register_node_success(mock_register, client):
    response = client.post("/api/node/register", json={"name": "test-node"})
    assert response.status_code == 200
    assert response.json["message"] == "Node registered successfully."


def test_register_node_missing_name(client):
    response = client.post("/api/node/register", json={})
    assert response.status_code == 400
    assert "error" in response.json


@patch("node_local_server.node_manager.start")
def test_start_node_success(mock_start, client):
    response = client.post("/api/node/start")
    assert response.status_code == 200
    assert "Node Manager started" in response.json["message"]


@patch("node_local_server.node_manager.start", side_effect=Exception("boom"))
def test_start_node_failure(mock_start, client):
    response = client.post("/api/node/start")
    assert response.status_code == 500
    assert "boom" in response.json["error"]


@patch("node_local_server.node_manager.stop")
def test_stop_node_success(mock_stop, client):
    response = client.post("/api/node/stop")
    assert response.status_code == 200
    assert "Node Manager stopped" in response.json["message"]


@patch("node_local_server.node_manager.stop", side_effect=Exception("halt"))
def test_stop_node_failure(mock_stop, client):
    response = client.post("/api/node/stop")
    assert response.status_code == 500
    assert "halt" in response.json["error"]
