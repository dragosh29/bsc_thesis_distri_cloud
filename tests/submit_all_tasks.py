import json
import requests
import time

# Configuration
API_ENDPOINT = "http://localhost:18000/api/tasks/submit_task/"
HEADERS = {"Content-Type": "application/json"}
TASK_FILE = "test_tasks.json"

def main():
    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    except Exception as e:
        print(f"Failed to load {TASK_FILE}: {e}")
        return

    for i, task in enumerate(tasks, 1):
        print(f"\nSubmitting Task {i}: {task['description']}")
        try:
            response = requests.post(API_ENDPOINT, headers=HEADERS, json=task)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error submitting task {i}: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
