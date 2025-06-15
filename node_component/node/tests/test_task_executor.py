import pytest
from unittest.mock import patch, MagicMock
from task_executor import TaskExecutor
import subprocess

from api_client import APIClient


@pytest.fixture
def task_executor():
    return TaskExecutor()


@pytest.mark.parametrize("status_code,stdout,stderr", [
    (0, "Task ran", ""), # success case
    (1, "", "Some error" # failure case
])
def test_execute_task_basic_flow(task_executor, status_code, stdout, stderr):
    task = {
        "id": "task123",
        "container_spec": {
            "image": "python:3.9",
            "command": "run.py",
            "env": {"VAR": "value"},
            "docker_credentials": {
                "registry": "ghcr.io",
                "username": "user",
                "password": "pass"
            }
        }
    }

    # control subprocess behavior
    mock_completed = MagicMock()
    mock_completed.returncode = status_code
    mock_completed.stdout = stdout
    mock_completed.stderr = stderr

    with patch("task_executor.subprocess.run") as mock_run, \
        patch.object(APIClient, "submit_result") as mock_submit:

        task_executor.execute_task(task)

        # validate subprocess command calls
        assert mock_run.call_count >= 3  # login, pull, run, logout

        mock_submit.assert_called_once()
        args = mock_submit.call_args[0]
        assert args[0] == "task123"
        assert "status" in args[1]


def test_execute_task_handles_docker_failure(task_executor):
    task = {
        "id": "task456",
        "container_spec": {
            "image": "bad:image",
            "command": "fail.py"
        }
    }

    with patch("task_executor.subprocess.run") as mock_run, \
         patch.object(task_executor.api_client, "submit_result") as mock_submit:

        mock_run.side_effect = Exception("Boom!")

        task_executor.execute_task(task)
        mock_submit.assert_called_once()
        result = mock_submit.call_args[0][1]
        assert result["status"] == "failed"
        assert "Boom!" in result["error"]


def test_ensure_docker_installed_success():
    with patch("task_executor.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        executor = TaskExecutor()
        executor.ensure_docker_installed()
        mock_run.assert_called_once_with(
            "docker --version",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )


def test_ensure_docker_installed_triggers_install():
    with patch("task_executor.subprocess.run") as mock_run:
        # first call fails → triggers install
        mock_run.side_effect = [subprocess.CalledProcessError(1, "docker --version"), MagicMock()]
        executor = TaskExecutor()
        executor.ensure_docker_installed()
        assert mock_run.call_count == 2
        install_cmd = mock_run.call_args_list[1][0][0]
        assert "get.docker.com" in install_cmd


def test_execute_task_triggers_logout():
    task = {
        "id": "logout-task",
        "container_spec": {
            "image": "python:3.9",
            "command": "echo done",
            "docker_credentials": {
                "registry": "ghcr.io",
                "username": "user",
                "password": "pass"
            }
        }
    }

    with patch("task_executor.subprocess.run") as mock_run, \
        patch.object(APIClient, "submit_result") as mock_submit:

        mock_run.return_value = MagicMock(returncode=0, stdout="out", stderr="")

        executor = TaskExecutor()
        executor.execute_task(task)

        logout_cmds = [c[0][0] for c in mock_run.call_args_list if "logout" in c[0][0]]
        assert any("docker logout" in cmd for cmd in logout_cmds)
