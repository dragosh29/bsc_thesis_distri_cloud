import json
import os
import socket
import time
from api_client import APIClient
from task_executor import TaskExecutor
from heartbeat import Heartbeat
from utils import get_node_resources, get_node_availability

CONFIG_FILE = "node_config.json"


class NodeManager:
    def __init__(self):
        self.api_client = APIClient()
        self.executor = TaskExecutor()
        self.heartbeat = Heartbeat()
        self.node_id = None

    def load_config(self):
        """Load node configuration from file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.node_id = config.get("node_id")

    def save_config(self, node_id):
        """Save node ID to file."""
        config = {"node_id": node_id}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def register(self, node_name):
        """
        Register the Node with the Hub.
        """
        print("[NODE MANAGER] Registering Node with Hub API...")

        ip_address = socket.gethostbyname(socket.gethostname())
        resources = get_node_resources()
        free_resources = get_node_availability()

        payload = {
            "name": node_name,  # Node name is passed directly
            "ip_address": ip_address,
            "resource_capacity": resources,
            "free_resources": free_resources,
        }

        try:
            response = self.api_client.register_node(payload)
            node_id = response.get('id')
            if node_id:
                self.save_config(node_id)
                self.node_id = node_id
                print(f"[NODE MANAGER] Registration successful. Node ID: {self.node_id}")
                return True
            else:
                print("[NODE MANAGER] Registration failed. No node ID returned.")
                return False
        except Exception as e:
            print(f"[NODE MANAGER] Registration failed: {e}")
            return False

    def start(self):
        """
        Start task execution and heartbeat.
        """
        self.load_config()
        if not self.node_id:
            raise Exception("[NODE MANAGER] Node is not registered. Please register first.")

        print("[NODE MANAGER] Starting Node tasks...")

        import threading
        heartbeat_thread = threading.Thread(target=self.heartbeat.start, daemon=True)
        heartbeat_thread.start()

        while True:
            try:
                task = self.api_client.fetch_task()
                if task and 'id' in task:
                    self.executor.execute_task(task)
                else:
                    print("[NODE MANAGER] No tasks. Retrying in 60 seconds...")
            except Exception as e:
                print("[NODE MANAGER] Failed to fetch or execute task:", e)
            time.sleep(60)

    def stop(self):
        """
        Stop Node Manager tasks.
        """
        print("[NODE MANAGER] Stopping Node Manager...")
