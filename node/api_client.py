# api_client.py

import requests
from config import HUB_API_BASE_URL, NODE_NAME, IP_ADDRESS
from utils import get_node_resources, get_node_availability

class APIClient:
    node_id = None

    def __init__(self):
        self.base_url = HUB_API_BASE_URL

    def register_node(self):
        resources = get_node_resources()
        free_resources = get_node_availability()
        payload = {
            "name": NODE_NAME,
            "resource_capacity": resources,
            "free_resources": free_resources,
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
        resources = get_node_availability()
        payload = {"node_id": APIClient.node_id, "free_resources": resources}
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
