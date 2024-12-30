# api_client.py

import requests
from config import HUB_API_BASE_URL, NODE_NAME, RESOURCE_CAPACITY, IP_ADDRESS

class APIClient:
    node_id = None

    def __init__(self):
        self.base_url = HUB_API_BASE_URL

    def register_node(self):
        payload = {
            "name": NODE_NAME,
            "resources_capacity": RESOURCE_CAPACITY,
            'ip_address': IP_ADDRESS
        }
        response = requests.post(f"{self.base_url}/nodes/register/", json=payload)
        if 'id' in response.json():
            APIClient.node_id = response.json()['id']
        return response.json()

    def fetch_task(self):
        response = requests.get(f"{self.base_url}/tasks/fetch", params={"node_id": APIClient.node_id})
        return response.json()

    def send_heartbeat(self):
        payload = {"node_id": APIClient.node_id}
        response = requests.post(f"{self.base_url}/nodes/heartbeat/", json=payload)
        return response.json()

    def submit_result(self, task_id, result):
        payload = {
            "node_id": APIClient.node_id,
            "task_id": task_id,
            "result": result
        }
        response = requests.post(f"{self.base_url}/tasks/submit_result/", json=payload)
        return response.json()
