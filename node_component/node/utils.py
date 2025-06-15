import os
import psutil

def get_node_resources():
    """
    Automatically detect the node's resource capacity.
    """
    cpu_cores = os.cpu_count()
    ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)  # RAM in GB

    return {
        "cpu": cpu_cores,
        "ram": ram_gb
    }

def get_node_availability(interval=2):
    """
    Returns the current resource usage/availability in terms of CPU cores and available RAM (GB).
    Usage is measured over the time interval specified in param: interval (in seconds).
    """
    # CPU usage per core
    usage_per_core_percent = psutil.cpu_percent(interval=interval, percpu=True)
    total_cores = len(usage_per_core_percent)

    # Convert each core's usage from percent to fraction of a core
    used_cores = sum((usage / 100.0) for usage in usage_per_core_percent)
    available_cores = total_cores - used_cores

    mem_info = psutil.virtual_memory()
    ram_available_gb = round(mem_info.available / (1024 ** 3), 2)

    return {
        "free_cpu": round(available_cores, 2),
        "free_ram": ram_available_gb
    }

def get_ip_address():
    """Returns the IP address of the node."""
    import socket
    return socket.gethostbyname(socket.gethostname())