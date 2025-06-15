import pytest
from unittest.mock import MagicMock, patch
from heartbeat import Heartbeat


@pytest.fixture
def mock_api_client():
    client = MagicMock()
    client.send_heartbeat.return_value = {"status": "ok"}
    return client


@patch("time.sleep", return_value=None)
def test_heartbeat_runs_once_and_calls_send(mock_sleep, mock_api_client):
    heartbeat = Heartbeat(mock_api_client)

    def stop_after_one(*args, **kwargs):
        heartbeat.should_run = False  # stop loop after first call
        return None

    with patch.object(mock_api_client, "send_heartbeat") as mock_send:
        with patch("time.sleep", side_effect=stop_after_one):
            heartbeat.start()
            mock_send.assert_called_once()


def test_stop_sets_flag(mock_api_client):
    heartbeat = Heartbeat(mock_api_client)
    heartbeat.should_run = True
    heartbeat.stop()
    assert heartbeat.should_run is False
