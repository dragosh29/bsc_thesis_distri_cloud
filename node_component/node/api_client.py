import requests
from config import HUB_API_BASE_URL, IP_ADDRESS, get_node_id, save_node_id
from utils import get_node_resources, get_node_availability

class APIClient:
    def __init__(self):
        self.base_url = HUB_API_BASE_URL
        self.node_id = get_node_id()

    def register_node(self, node_name):
        """
        Register the node if no node_id exists.
        """
        if self.node_id:
            print(f"[API CLIENT] Node already registered with ID: {self.node_id}")
            return {"id": self.node_id}

        resources = get_node_resources()
        free_resources = get_node_availability()
        payload = {
            "name": node_name,
            "resource_capacity": resources,
            "free_resources": free_resources,
            'ip_address': IP_ADDRESS
        }
        response = requests.post(f"{self.base_url}/nodes/register/", json=payload)
        response_data = response.json()
        if 'id' in response_data:
            self.node_id = response_data['id']
            save_node_id(self.node_id)
        return response_data

    def fetch_task(self):
        """
        Fetch tasks for the node using its node_id.
        """
        if not self.node_id:
            raise Exception("[API CLIENT] Node ID is missing. Register the node first.")
        response = requests.get(f"{self.base_url}/tasks/fetch", params={"node_id": self.node_id})
        return response.json()

    def send_heartbeat(self):
        """
        Send a periodic heartbeat with free resource information.
        """
        if not self.node_id:
            raise Exception("[API CLIENT] Node ID is missing. Register the node first.")
        resources = get_node_availability()
        payload = {"node_id": self.node_id, "free_resources": resources}
        response = requests.post(f"{self.base_url}/nodes/heartbeat/", json=payload)
        return response.json()

    def submit_result(self, task_id, result):
        """
        Submit the result of a completed task.
        """
        if not self.node_id:
            raise Exception("[API CLIENT] Node ID is missing. Register the node first.")
        payload = {
            "node_id": self.node_id,
            "task_id": task_id,
            "result": result
        }
        response = requests.post(f"{self.base_url}/tasks/submit_result/", json=payload)
        return response.json()
