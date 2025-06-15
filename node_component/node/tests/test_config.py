import pytest
from unittest.mock import mock_open, patch
import json

from config import get_node_id, save_node_id, CONFIG_FILE


def test_get_node_id_found():
    mock_data = json.dumps({"node_id": "abc-123"})
    with patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("os.path.exists", return_value=True):
        result = get_node_id()
        assert result == "abc-123"


def test_get_node_id_not_found_in_file():
    mock_data = json.dumps({})
    with patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("os.path.exists", return_value=True):
        result = get_node_id()
        assert result is None


def test_get_node_id_file_missing():
    with patch("os.path.exists", return_value=False):
        result = get_node_id()
        assert result is None


def test_save_node_id_writes_correctly():
    with patch("builtins.open", mock_open()) as m:
        save_node_id("xyz-456")
        m.assert_called_once_with(CONFIG_FILE, 'w')
        handle = m()

        # Collect all write calls into a single string
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        expected = json.dumps({"node_id": "xyz-456"})
        assert written == expected
