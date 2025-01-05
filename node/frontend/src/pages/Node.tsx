import React, { useEffect, useState } from 'react';
import axios from 'axios';

// Environment Variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const LOCAL_API_BASE_URL = import.meta.env.VITE_LOCAL_API_BASE_URL;

interface NodeConfig {
    name?: string;
    status?: string;
}

const Nodes: React.FC = () => {
    const [nodeConfig, setNodeConfig] = useState<NodeConfig | null>(null);
    const [nodeName, setNodeName] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [isStarting, setIsStarting] = useState(false);

    // Fetch Node Status on Load
    useEffect(() => {
        const fetchNodeStatus = async () => {
            try {
                const response = await axios.get(`${LOCAL_API_BASE_URL}/node`);
                setNodeConfig(response.data);
            } catch (error) {
                console.warn('No existing node configuration found.');
                setNodeConfig(null);
            }
        };
        fetchNodeStatus();
    }, []);

    // Register Node with HUB API and Local Server
    const handleRegisterNode = async () => {
        setIsRegistering(true);
        try {
            // Step 1: Register with HUB API
            const hubResponse = await axios.post(`${API_BASE_URL}/nodes/register`, { name: nodeName });
            const { id: nodeId } = hubResponse.data.get('node_id');

            // Step 2: Register locally with Node ID and Name
            await axios.post(`${LOCAL_API_BASE_URL}/node/register`, {
                name: nodeName,
                node_id: nodeId,
            });

            // Update Node Config State
            setNodeConfig({ name: nodeName, status: 'registered' });
        } catch (error) {
            console.error('Node registration failed:', error);
        } finally {
            setIsRegistering(false);
        }
    };

    // Start Node Manager
    const handleStartNode = async () => {
        setIsStarting(true);
        try {
            await axios.post(`${LOCAL_API_BASE_URL}/node/start`);
            console.log('Node Manager started successfully.');
        } catch (error) {
            console.error('Failed to start Node Manager:', error);
        } finally {
            setIsStarting(false);
        }
    };

    return (
        <div>
            <h1>{import.meta.env.VITE_APP_TITLE} - Node Management</h1>
            {nodeConfig?.status === 'registered' ? (
                <>
                    <p>Node Name: {nodeConfig.name}</p>
                    <p>Status: {nodeConfig.status}</p>
                    <button onClick={handleStartNode} disabled={isStarting}>
                        {isStarting ? 'Starting...' : 'Start Node'}
                    </button>
                </>
            ) : (
                <>
                    <p>No node registered.</p>
                    <input
                        type="text"
                        placeholder="Enter Node Name"
                        value={nodeName}
                        onChange={(e) => setNodeName(e.target.value)}
                    />
                    <button onClick={handleRegisterNode} disabled={isRegistering || !nodeName}>
                        {isRegistering ? 'Registering...' : 'Register Node'}
                    </button>
                </>
            )}
        </div>
    );
};

export default Nodes;
