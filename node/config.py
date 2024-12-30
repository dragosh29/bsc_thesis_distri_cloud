# config.py

HUB_API_BASE_URL = "http://localhost:18000/api"
NODE_NAME = "NODE_C"
HEARTBEAT_INTERVAL = 30  # in seconds

RESOURCE_CAPACITY = {
    "cpu": 4,
    "ram": 16
}

def get_ip_address():
    import socket
    return socket.gethostbyname(socket.gethostname())

IP_ADDRESS = get_ip_address()
