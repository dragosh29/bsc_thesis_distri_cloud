# node_manager.py

import time
from api_client import APIClient
from task_executor import TaskExecutor
from heartbeat import Heartbeat

class NodeManager:
    def __init__(self):
        self.api_client = APIClient()
        self.executor = TaskExecutor()
        self.heartbeat = Heartbeat()

    def start(self):
        print("[NODE MANAGER] Starting Node...")
        try:
            self.api_client.register_node()
            print("[NODE MANAGER] Node registered with the hub.")
        except Exception as e:
            print("[ERROR] Node registration failed:", e)
            return

        # Start Heartbeat in a separate thread
        import threading
        heartbeat_thread = threading.Thread(target=self.heartbeat.start, daemon=True)
        heartbeat_thread.start()

        # Start Task Fetching and Execution
        while True:
            try:
                task = self.api_client.fetch_task()
                if task and 'id' in task:
                    self.executor.execute_task(task)
                else:
                    print("[NODE MANAGER] No task assigned. Retrying in 60 seconds...")
            except Exception as e:
                print("[ERROR] Failed to fetch or execute task:", e)
            time.sleep(60)
