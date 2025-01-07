import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from node_manager import NodeManager

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:18080"}})

CONFIG_FILE = "node_config.json"
node_manager = NodeManager()


@app.route('/api/node', methods=['GET'])
def get_node_status():
    """Fetch Node status."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return jsonify({"status": "registered", "node_id": json.load(f).get("node_id")})
    return jsonify({
        "status": "unregistered",
        "message": "Node is not registered. Please register to proceed."
    }), 200


@app.route('/api/node/register', methods=['POST'])
def register_node():
    """
    Step 1: Receive node name from the frontend.
    Step 2: Trigger Node Manager to complete registration with the Hub.
    """
    data = request.json
    node_name = data.get('name')

    if not node_name:
        return jsonify({"error": "Node name is required."}), 400

    try:
        success = node_manager.register(node_name)
        if success:
            return jsonify({"message": "Node registered successfully."}), 200
        else:
            return jsonify({"error": "Failed to register node."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/node/start', methods=['POST'])
def start_node():
    """
    Start the Node Manager.
    """
    try:
        node_manager.start()
        return jsonify({"message": "Node Manager started successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/node/stop', methods=['POST'])
def stop_node():
    """
    Stop the Node Manager.
    """
    try:
        node_manager.stop()
        return jsonify({"message": "Node Manager stopped successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18001)
