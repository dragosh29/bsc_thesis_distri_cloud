import requests
import threading
import time
import random
import numpy as np
import pandas as pd
from datetime import datetime
from queue import Queue

# ============ CONFIGURABLE PARAMETERS ============

API_BASE = 'http://localhost:18000/api'
NODES = [10, 20]       # Try with multiple node counts
TASKS = [50, 100]      # Try with multiple task counts
EXPERIMENTS = ['fifo', 'custom']  # Orchestration strategies

# Resource/trust distributions
CPU_RANGE = (1, 4)
RAM_RANGE = (1, 8)
TRUST_RANGE = (1.0, 10.0)
CPU_REQ_RANGE = (1, 6)
RAM_REQ_RANGE = (1, 10)

# Task execution time simulation (in seconds)
TASK_DURATION_MEAN = 1.0
TASK_DURATION_STD = 0.1

# Overlap distribution setup
OVERLAP_DIST = [1, 2, 3, 4, 5]
OVERLAP_WEIGHTS = [0.10, 0.35, 0.35, 0.15, 0.05]  # 2/3 common, 5 rare

def random_overlap():
    """Generate a random overlap count based on predefined distribution."""
    return random.choices(OVERLAP_DIST, weights=OVERLAP_WEIGHTS, k=1)[0]

def random_trust_required():
    """Generate a random trust index required for task submission."""
    # You can tune this as desired (e.g., bias towards more realistic scenarios)
    return round(random.uniform(1.0, 10.0), 2)

# ============ API HELPERS ============

def set_algorithm(alg):
    """Reminder to set the orchestration algorithm in Django settings."""
    print(f"\n*** Please ensure ORCHESTRATION_MECHANISM is set to '{alg}' and restart Django if needed! ***\n")
    input("Press Enter to continue once Django is running with the correct mode...")

def register_node(name, cpu, ram, trust):
    """Register a new node with the given resources and trust index."""
    payload = {
        "name": name,
        "ip_address": "127.0.0.1",
        "resources_capacity": {"cpu": cpu, "ram": ram},
        "free_resources": {"cpu": cpu, "ram": ram},
        "trust_index": trust
    }
    res = requests.post(f"{API_BASE}/experiment/distribution/create_node/", json=payload)
    res.raise_for_status()
    data = res.json()
    return data

def submit_task(desc, cpu, ram, overlap, submitter_id, trust_required):
    """Submit a new task with the specified requirements and metadata."""
    payload = {
        "description": desc,
        "container_spec": {"image": "python:3.9", "command": "python main.py"},
        "resource_requirements": {"cpu": cpu, "ram": ram},
        "overlap_count": overlap,
        "submitted_by": submitter_id,
        "trust_index_required": trust_required
    }
    res = requests.post(f"{API_BASE}/tasks/submit_task/", json=payload)
    res.raise_for_status()
    return res.json()["task_id"]

def send_heartbeat(nid, free_resources):
    """Send a heartbeat to the API to update node's free resources."""
    requests.post(f"{API_BASE}/nodes/heartbeat/", json={
        "node_id": nid,
        "free_resources": free_resources
    })

def fetch_task(nid):
    """Fetch a task for the given node ID."""
    res = requests.get(f"{API_BASE}/tasks/fetch", params={"node_id": nid})
    if res.status_code == 200:
        return res.json()
    return None

def submit_result(tid, nid, output="ok"):
    """Submit the result of a task execution."""
    payload = {
        "task_id": tid,
        "node_id": nid,
        "result": {"output": output}
    }
    res = requests.post(f"{API_BASE}/tasks/submit_result/", json=payload)
    return res.status_code == 200

def get_task_status(tid):
    """Get the status of a specific task by its ID."""
    res = requests.get(f"{API_BASE}/tasks/{tid}/")
    return res.json() if res.status_code == 200 else None

def get_all_tasks():
    """Fetch all tasks from the API."""
    res = requests.get(f"{API_BASE}/tasks")
    res.raise_for_status()
    return res.json()

def trigger_orchestration():
    """Trigger orchestration manually to process tasks."""
    resp = requests.post(f"{API_BASE}/experiment/distribution/trigger_orchestration/", timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Failed to trigger orchestration: {resp.text}")

def reset_all_data():
    """Reset the database to a clean state for the experiment."""
    resp = requests.post(f"{API_BASE}/experiment/distribution/reset_db/")
    if resp.status_code != 200:
        raise Exception("Failed to reset DB: " + resp.text)
    print("[DB RESET] Success.")

# ============ NODE THREAD ============

class NodeThread(threading.Thread):
    def __init__(self, node_info, experiment_queue, result_log, stop_flag):
        """Initialize the node thread with its info and queues."""
        super().__init__()
        self.node = node_info
        self.nid = self.node["id"]
        self.cpu = self.node["resources_capacity"]["cpu"]
        self.ram = self.node["resources_capacity"]["ram"]
        self.trust = self.node.get("trust_index", 5.0)
        self.queue = experiment_queue
        self.log = result_log
        self.stop_flag = stop_flag

    def run(self):
        """Run the node thread to fetch and process tasks."""
        while not self.stop_flag.is_set():
            send_heartbeat(self.nid, {"cpu": self.cpu, "ram": self.ram})
            task = fetch_task(self.nid)
            if task:
                tid = task["id"]
                start_time = datetime.utcnow()
                duration = max(0.1, np.random.normal(TASK_DURATION_MEAN, TASK_DURATION_STD))
                time.sleep(duration)
                # Always submit the same result
                submit_result(tid, self.nid, output="42")
                end_time = datetime.utcnow()
                self.log.put({
                    "task_id": tid,
                    "node_id": self.nid,
                    "assigned_at": start_time,
                    "completed_at": end_time,
                    "work_duration": duration,
                })
            time.sleep(2)

# ============ EXPERIMENT RUNNER ============

def run_experiment(algorithm, N, M):
    """Run a single experiment with the specified algorithm, N nodes, and M tasks."""
    print(f"\n=== Running experiment: {algorithm.upper()}, N={N}, M={M} ===")

    set_algorithm(algorithm)
    reset_all_data()

    # 1. Register N nodes with random resources/trust
    nodes = []
    for i in range(N):
        cpu = random.randint(*CPU_RANGE)
        ram = random.randint(*RAM_RANGE)
        trust = round(random.uniform(*TRUST_RANGE), 2)
        node_info = register_node(f"Node-{i}", cpu, ram, trust)
        node_info["trust_index"] = trust
        nodes.append(node_info)

    # 2. Submit M tasks with random requirements and valid overlap/trust
    task_ids = []
    task_overlaps = {}
    task_trusts = {}
    # --- Compute maximum node trust index up front ---
    max_trust = max(n["trust_index"] for n in nodes)
    for i in range(M):
        cpu_req = random.randint(*CPU_REQ_RANGE)
        ram_req = random.randint(*RAM_REQ_RANGE)
        # --- Guarantee: overlap/trust_required is always possible with the given nodes
        while True:
            overlap = random_overlap()
            trust_required = min(random_trust_required(), max_trust)  # <=== HARD CAP
            trust_required = round(trust_required, 2)
            eligible = [n for n in nodes if n["trust_index"] >= trust_required + 0.5]
            if len(eligible) >= overlap:
                break
        assert trust_required <= max_trust, f"BUG: trust_required {trust_required} > max node trust {max_trust}"
        submitter = random.choice(nodes)
        tid = submit_task(f"Task-{i}", cpu_req, ram_req, overlap, submitter["id"], trust_required)
        task_ids.append(tid)
        task_overlaps[tid] = overlap
        task_trusts[tid] = trust_required

    # 3. Start node threads
    stop_flag = threading.Event()
    log_queue = Queue()
    threads = [NodeThread(n, None, log_queue, stop_flag) for n in nodes]
    for t in threads:
        t.start()

    # 4. Poll until all tasks are validated or failed and retrigger orchestration at each poll ("manual beat")
    task_status = {tid: {"validated": False, "failed": False} for tid in task_ids}
    start_time = time.time()
    stale_counts = {}
    while True:
        finished = 0
        for tid in task_ids:
            tstat = get_task_status(tid)
            if not tstat:
                continue
            stale_counts[tid] = tstat.get("stale_count", 0)
            if tstat["status"] in ("validated", "failed"):
                finished += 1
                task_status[tid]["validated"] = tstat["status"] == "validated"
                task_status[tid]["failed"] = tstat["status"] == "failed"
        trigger_orchestration() # manual beat
        if finished == M:
            break
        time.sleep(3)

    # 5. Stop threads
    stop_flag.set()
    for t in threads:
        t.join()

    end_time = time.time()
    total_duration = end_time - start_time

    # 6. Collect logs
    result_rows = []
    while not log_queue.empty():
        result_rows.append(log_queue.get())

    # 7. Augment with stale/validation/failure info, and overlap/trust
    for row in result_rows:
        tid = row["task_id"]
        row["overlap"] = task_overlaps.get(tid, None)
        row["trust_index_required"] = task_trusts.get(tid, None)
        row["stale_count"] = stale_counts.get(tid, 0)
        row["validated"] = task_status[tid]["validated"]
        row["failed"] = task_status[tid]["failed"]
        row["algorithm"] = algorithm
        row["N"] = N
        row["M"] = M
        row["total_duration"] = total_duration

    print(f"Experiment finished in {total_duration:.2f}s")

    return result_rows

# ============ MAIN MULTI-RUNNER ============

if __name__ == "__main__":
    all_results = []

    for alg in EXPERIMENTS:
        for N in NODES:
            for M in TASKS:
                results = run_experiment(alg, N, M)
                all_results.extend(results)

    df = pd.DataFrame(all_results)
    df.to_csv("node_distribution_experiment_results.csv", index=False)
    print("\nAll experiments done. Results saved to node_distribution_experiment_results.csv.")
