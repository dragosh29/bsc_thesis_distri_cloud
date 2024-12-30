# heartbeat.py

import time
from api_client import APIClient

class Heartbeat:
    def __init__(self):
        self.api_client = APIClient()

    def start(self):
        while True:
            try:
                response = self.api_client.send_heartbeat()
                print("[HEARTBEAT] Node is active:", response)
            except Exception as e:
                print("[ERROR] Heartbeat failed:", e)
            time.sleep(30)
