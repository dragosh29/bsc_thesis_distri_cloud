import json
import pytest
import threading
from unittest.mock import patch, mock_open, MagicMock
from node_manager import NodeManager


@pytest.fixture
def manager():
    return NodeManager()


def test_load_config_reads_file_and_sets_ids():
    data = {"node_id": "abc", "last_task_id": "task123"}
    with patch("builtins.open", mock_open(read_data=json.dumps(data))), \
         patch("os.path.exists", return_value=True):
        nm = NodeManager()
        assert nm.node_id == "abc"
        assert nm.last_task_id == "task123"


def test_save_config_writes_expected_content():
    valid_json = json.dumps({"node_id": "existing"})

    with patch("builtins.open", mock_open(read_data=valid_json)) as m_read, \
         patch("os.path.exists", return_value=True):
        nm = NodeManager()

    with patch("builtins.open", mock_open()) as m_write:
        nm.save_config("abc-123", "task999")
        handle = m_write()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        parsed = json.loads(written)
        assert parsed["node_id"] == "abc-123"
        assert parsed["last_task_id"] == "task999"


@patch("node_manager.APIClient.register_node", return_value={"id": "abc-123"})
def test_register_success(mock_register):
    nm = NodeManager()
    result = nm.register("my-node")
    assert result is True
    assert nm.node_id == "abc-123"


@patch("node_manager.APIClient.register_node", return_value={})
def test_register_failure_no_id(mock_register):
    nm = NodeManager()
    result = nm.register("test-node")
    assert result is False


@patch("node_manager.APIClient.register_node", side_effect=Exception("fail"))
def test_register_raises_gracefully(mock_register):
    nm = NodeManager()
    result = nm.register("test-node")
    assert result is False


def test_start_sets_flags_and_starts_threads(manager):
    manager.node_id = "abc"
    with patch.object(threading.Thread, "start"):
        manager.start()
        assert manager.running is True
        assert manager.should_run is True


def test_stop_joins_threads_safely():
    nm = NodeManager()
    nm.heartbeat_thread = MagicMock()
    nm.task_loop_thread = MagicMock()
    nm.should_run = True
    nm.running = True

    with patch.object(nm.heartbeat, "stop"):
        nm.stop()
        assert nm.should_run is False
        assert nm.running is False
        nm.heartbeat_thread.join.assert_called()
        nm.task_loop_thread.join.assert_called()


@patch("node_manager.psutil.cpu_percent", return_value=42.5)
@patch("node_manager.psutil.virtual_memory")
def test_get_resource_usage_returns_expected_values(mock_mem, mock_cpu):
    mock_mem.return_value.used = 4 * 1024 ** 3  # 4 GB
    nm = NodeManager()
    result = nm.get_resource_usage()
    assert result["cpu"] == 42.5
    assert result["ram"] == 4.0


def test_run_main_loop_handles_fetch_and_exec_once():
    nm = NodeManager()
    nm.should_run = True
    fake_task = {"id": "task-1"}
    nm.node_id = "abc"

    with patch.object(nm.api_client, "fetch_task", return_value=fake_task), \
         patch.object(nm, "save_config") as mock_save, \
         patch.object(nm.executor, "execute_task") as mock_exec, \
         patch("time.sleep", side_effect=lambda x: setattr(nm, "should_run", False)):
        nm._run_main_loop()
        mock_save.assert_called_once()
        mock_exec.assert_called_once_with(fake_task)


def test_run_main_loop_handles_exception_gracefully():
    nm = NodeManager()
    nm.should_run = True
    nm.node_id = "abc"

    with patch.object(nm.api_client, "fetch_task", side_effect=Exception("fail")), \
         patch("time.sleep", side_effect=lambda x: setattr(nm, "should_run", False)):
        nm._run_main_loop()
