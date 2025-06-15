import pytest
from unittest.mock import patch

@pytest.fixture
def mock_api_response():
    with patch("api_client.requests.post") as mock_post, \
         patch("api_client.requests.get") as mock_get:
        yield mock_post, mock_get

@pytest.fixture
def dummy_task():
    return {
        "id": "dummy-task-id",
        "container_spec": {"image": "alpine", "command": "echo hello"},
        "resource_requirements": {"cpu": 1, "ram": 1}
    }
