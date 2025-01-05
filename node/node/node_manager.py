import time
from api_client import APIClient
from task_executor import TaskExecutor
from heartbeat import Heartbeat

class NodeManager:
    def __init__(self):
        self.api_client = APIClient()
        self.executor = TaskExecutor()
        self.heartbeat = Heartbeat()
        self.node_id = self.api_client.node_id

    def start(self):
        """
        Start the Node Manager with node registration or resumption.
        """
        if self.node_id:
            print("[NODE MANAGER] Starting as an existing node...")
        else:
            print("[NODE MANAGER] Registering node with the hub...")
            try:
                response = self.api_client.register_node()
                self.node_id = response.get('id')
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
