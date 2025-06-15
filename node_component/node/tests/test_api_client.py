import pytest
import requests
from unittest.mock import patch, MagicMock, mock_open
from api_client import APIClient
import builtins


@pytest.fixture
def api_client():
    return APIClient()


@patch("api_client.get_node_id", return_value=None)
@patch("api_client.save_node_id")
@patch("requests.post")
def test_register_node_success(mock_post, mock_save_node_id, mock_get_node_id):
    expected_id = "abc-123"
    mock_post.return_value.json.return_value = {"id": expected_id}

    client = APIClient()
    response = client.register_node("TestNode")

    assert response["id"] == expected_id
    mock_post.assert_called_once()
    mock_save_node_id.assert_called_once_with(expected_id)


@patch("api_client.get_node_id", return_value="abc-123")
def test_register_node_skips_if_registered(mock_get_id):
    client = APIClient()
    result = client.register_node("Any")
    assert result == {"id": "abc-123"}


@patch("api_client.requests.get")
def test_fetch_task_success(mock_get, api_client):
    api_client.node_id = "node-1"
    mock_get.return_value.json.return_value = {"id": "task-1"}
    result = api_client.fetch_task()
    assert result["id"] == "task-1"


def test_fetch_task_missing_node_id():
    client = APIClient()
    client.node_id = None
    with pytest.raises(Exception, match="Node ID is missing"):
        client.fetch_task()


@patch("api_client.requests.get")
def test_fetch_task_details(mock_get, api_client):
    api_client.node_id = "node-1"
    mock_get.return_value.json.return_value = {"id": "task-xyz"}
    result = api_client.fetch_task_details("task-xyz")
    assert result["id"] == "task-xyz"


def test_fetch_task_details_missing_node():
    client = APIClient()
    client.node_id = None
    with pytest.raises(Exception):
        client.fetch_task_details("some-task")


@patch("api_client.get_node_availability", return_value={"free_cpu": 1, "free_ram": 2})
@patch("api_client.requests.post")
def test_send_heartbeat(mock_post, mock_avail, api_client):
    api_client.node_id = "node-xyz"
    mock_post.return_value.json.return_value = {"message": "ok"}
    result = api_client.send_heartbeat()
    assert result["message"] == "ok"


def test_send_heartbeat_missing():
    client = APIClient()
    client.node_id = None
    with pytest.raises(Exception):
        client.send_heartbeat()


@patch("api_client.requests.post")
def test_submit_result_success(mock_post, api_client):
    api_client.node_id = "node-xyz"
    mock_post.return_value.json.return_value = {"status": "submitted"}
    result = api_client.submit_result("task-xyz", {"output": "42"})
    assert result["status"] == "submitted"


def test_submit_result_missing():
    client = APIClient()
    client.node_id = None
    with pytest.raises(Exception):
        client.submit_result("some-task", {"output": "test"})
