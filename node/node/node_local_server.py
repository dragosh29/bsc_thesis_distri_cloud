# node_local_server.py
import json

from flask import Flask, jsonify, request
import subprocess
import os

app = Flask(__name__)

NODE_PROCESS = None

@app.route('/api/node/config', methods=['GET'])
def get_node_config():
    config_file = 'node_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"message": "No node configuration found."}), 404

@app.route('/api/node/start', methods=['POST'])
def start_node():
    global NODE_PROCESS
    if NODE_PROCESS:
        return jsonify({"message": "Node Manager is already running."}), 400

    try:
        NODE_PROCESS = subprocess.Popen(["python", "node/main.py"])
        return jsonify({"message": "Node Manager started successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/node/register', methods=['POST'])
def register_node():
    data = request.json
    node_name = data.get('name')
    node_id = data.get('node_id')
    if not node_name:
        return jsonify({"error": "Node name is required."}), 400
    if not node_id:
        return jsonify({"error": "Node ID is required."}), 400

    config = {
        "node_id": node_id,
        "name": node_name,
        "status": "registered"
    }
    with open('node_config.json', 'w') as f:
        json.dump(config, f)

    return jsonify(config), 201

@app.route('api/node', methods=['GET'])
def fetch_node():
    config = {}
    if os.path.exists('node_config.json'):
        with open('node_config.json', 'r') as f:
            config = json.load(f)
    else:
        return jsonify({"error": "Node not registered."}), 404
    node_id = config.get('node_id')
    node_name = config.get('name')
    if not node_id:
        return jsonify({"error": "Node not registered."}), 404
    if not node_name:
        return jsonify({"error": "Node name not found."}), 404
    return jsonify({"node_id": node_id, "name": node_name}, 200)

@app.route('/api/node/stop', methods=['POST'])
def stop_node():
    global NODE_PROCESS
    if NODE_PROCESS:
        NODE_PROCESS.terminate()
        NODE_PROCESS = None
        return jsonify({"message": "Node Manager stopped successfully."})
    return jsonify({"error": "Node Manager is not running."}), 400

if __name__ == '__main__':
    app.run(port=18001)
