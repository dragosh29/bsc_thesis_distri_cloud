import time

class Heartbeat:
    def __init__(self, api_client):
        self.api_client = api_client
        self.should_run = False

    def start(self):
        """Start the heartbeat process to periodically notify the API that the node is active."""
        self.should_run = True
        while self.should_run:
            try:
                response = self.api_client.send_heartbeat()
                print("[HEARTBEAT] Node is active:", response)
            except Exception as e:
                print("[ERROR] Heartbeat failed:", e)
            time.sleep(30)

    def stop(self):
        """Stop the heartbeat process."""
        print("[HEARTBEAT] Stopping heartbeat...")
        self.should_run = False
