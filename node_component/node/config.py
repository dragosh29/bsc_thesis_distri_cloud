# config.py
import json
import os

from utils import get_ip_address

HUB_API_BASE_URL = "http://localhost:18000/api"
NODE_NAME = "NODE_A"
HEARTBEAT_INTERVAL = 30  # in seconds
IP_ADDRESS = get_ip_address()

CONFIG_FILE = "node_config.json"

def get_node_id():
    """
    Retrieve the node_id from the JSON config file.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            node_id = config.get('node_id')
            if node_id:
                print("[CONFIG] Loaded NODE_ID from node_config.json.")
                return node_id
    print("[CONFIG] No NODE_ID found. Node will need to register.")
    return None

def save_node_id(node_id):
    """
    Save the node_id to the JSON config file.
    """
    with open(CONFIG_FILE, 'w') as file:
        json.dump({"node_id": node_id}, file)
    print(f"[CONFIG] NODE_ID saved to {CONFIG_FILE}.")