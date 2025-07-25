import json
import logging
import os
import threading
import time
import psutil
from api_client import APIClient
from task_executor import TaskExecutor
from heartbeat import Heartbeat

CONFIG_FILE = "node_config.json"
logging.basicConfig(level=logging.INFO)

class NodeManager:
    """
    Central manager for the local node worker, handling registration, task execution, and heartbeat.
    Delegates task execution to TaskExecutor and heartbeat submissions to Heartbeat.
    Communicated with the Hub API via APIClient.
    """

    def __init__(self):
        self.api_client = APIClient()
        self.executor = TaskExecutor()
        self.heartbeat = Heartbeat(self.api_client)
        self.node_id = None
        self.running = False
        self.should_run = False
        self.last_task_id = None
        self.last_assignment_info = None
        self.heartbeat_thread = None
        self.task_loop_thread = None
        self.load_config()

    def load_config(self):
        """Load configuration from local JSON file."""

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.node_id = config.get("node_id")
                self.last_task_id = config.get("last_task_id")

    def save_config(self, node_id, last_task_id=None):
        """Save configuration to local JSON file."""

        config = {"node_id": node_id}
        if last_task_id:
            config["last_task_id"] = last_task_id
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def register(self, node_name):
        """Register the node with the Hub API. Uses api_client to communicate with the Hub."""

        print("[NODE MANAGER] Registering Node with Hub API...")
        try:
            response = self.api_client.register_node(node_name)
            self.node_id = response.get('id')
            if self.node_id:
                self.save_config(self.node_id)
                print(f"[NODE MANAGER] Registration successful. Node ID: {self.node_id}")
                return True
            else:
                print("[NODE MANAGER] Registration failed. No node ID returned.")
                return False
        except Exception as e:
            logging.error(f"Node registration failed: {e}")
            return False

    def start(self):
        """Start the Node Manager, initializing heartbeat and task execution."""

        if not self.node_id:
            raise Exception("[NODE MANAGER] Node is not registered. Please register first.")

        print("[NODE MANAGER] Starting Node tasks...")
        self.running = True
        self.should_run = True

        self.heartbeat_thread = threading.Thread(target=self.heartbeat.start, daemon=True)
        self.heartbeat_thread.start()

        self.task_loop_thread = threading.Thread(target=self._run_main_loop, daemon=True)
        self.task_loop_thread.start()

    def _run_main_loop(self):
        """Main loop for fetching and executing tasks."""

        while self.should_run:
            try:
                task = self.api_client.fetch_task()
                if task:
                    self.last_task_id = task["id"]
                    self.save_config(self.node_id, self.last_task_id)
                    self.executor.execute_task(task)
            except Exception as e:
                print("[NODE MANAGER] Error:", e)
            time.sleep(60)

    def get_resource_usage(self):
        """Get current resource usage of the node."""

        cpu = psutil.cpu_percent(interval=1)
        used_bytes = psutil.virtual_memory().used
        used_gb = used_bytes / 1024 ** 3
        return {
            "cpu": cpu,
            "ram": round(used_gb, 2)
        }

    def stop(self):
        """Stop the Node Manager and clean up resources."""

        print("[NODE MANAGER] Stopping Node Manager...")
        self.should_run = False
        self.running = False
        self.heartbeat.stop()

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        if self.task_loop_thread:
            self.task_loop_thread.join(timeout=5)
