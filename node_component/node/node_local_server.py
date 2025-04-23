import json
import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from node_manager import NodeManager

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:18080"}})

CONFIG_FILE = "node_config.json"
node_manager = NodeManager()

@app.route('/api/node', methods=['GET'])
def get_node_status():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        node_manager.node_id = config.get("node_id")
        node_manager.last_task_id = config.get("last_task_id")

        return jsonify({
            "status": "registered",
            "node_id": node_manager.node_id,
            "is_running": node_manager.running,
            "last_task_id": node_manager.last_task_id,
            "resource_usage": node_manager.get_resource_usage() if node_manager.running else None
        }), 200

    return jsonify({
        "status": "unregistered",
        "message": "Node is not registered. Please register to proceed.",
        "node_id": node_manager.node_id
    }), 200

@app.route('/api/node/register', methods=['POST'])
def register_node():
    data = request.json
    node_name = data.get('name')
    logging.info(f"Registering Node with name: {node_name}")
    if not node_name:
        return jsonify({"error": "Node name is required."}), 400

    try:
        success = node_manager.register(node_name)
        if success:
            return jsonify({"message": "Node registered successfully.", "id": node_manager.node_id}), 200
        return jsonify({"error": "Failed to register node."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/node/start', methods=['POST'])
def start_node():
    try:
        node_manager.start()
        return jsonify({"message": "Node Manager started successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/node/stop', methods=['POST'])
def stop_node():
    try:
        node_manager.stop()
        return jsonify({"message": "Node Manager stopped successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18001)
