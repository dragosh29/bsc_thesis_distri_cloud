import React, { useEffect, useState } from 'react';
import axios from 'axios';

// Environment Variable
const LOCAL_API_BASE_URL = import.meta.env.VITE_LOCAL_API_BASE_URL;

// Node Configuration Interface
interface NodeConfig {
    name?: string;
    status: string; // Either 'registered' or 'unregistered'
}

const Nodes: React.FC = () => {
    const [nodeConfig, setNodeConfig] = useState<NodeConfig | null>(null);
    const [nodeName, setNodeName] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    /**
     * Fetch Node Configuration on Component Mount
     */
    const fetchNodeStatus = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${LOCAL_API_BASE_URL}/node`);
            setNodeConfig(response.data); // Handle status: "registered" or "unregistered"
        } catch (err) {
            console.error('Failed to fetch node status:', err);
            setError('Failed to fetch node status.');
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * Register Node with the Node API
     */
    const handleRegisterNode = async () => {
        if (!nodeName.trim()) {
            setError('Node name cannot be empty.');
            return;
        }

        setIsRegistering(true);
        setError(null);
        try {
            await axios.post(`${LOCAL_API_BASE_URL}/node/register`, {
                name: nodeName,
            });
            await fetchNodeStatus(); // Refresh Node Status
        } catch (err) {
            console.error('Failed to register Node:', err);
            setError('Failed to register Node. Please try again.');
        } finally {
            setIsRegistering(false);
        }
    };

    /**
     * Start Node Manager
     */
    const handleStartNode = async () => {
        setIsStarting(true);
        setError(null);
        try {
            await axios.post(`${LOCAL_API_BASE_URL}/node/start`);
            await fetchNodeStatus(); // Refresh Node Status
        } catch (err) {
            console.error('Failed to start Node Manager:', err);
            setError('Failed to start Node Manager. Please try again.');
        } finally {
            setIsStarting(false);
        }
    };

    /**
     * Fetch Node Status on Mount
     */
    useEffect(() => {
        fetchNodeStatus();
    }, []);

    /**
     * Render Loading State
     */
    if (isLoading) {
        return <p>Loading Node Status...</p>;
    }

    /**
     * Render Error State
     */
    if (error) {
        return (
            <div>
                <h1>Node Management</h1>
                <p style={{ color: 'red' }}>{error}</p>
                <button onClick={fetchNodeStatus}>Retry</button>
            </div>
        );
    }

    /**
     * Render Node Status
     */
    return (
        <div>
            <h1>Node Management</h1>
            {nodeConfig?.status === 'registered' ? (
                <>
                    <p><strong>Node Name:</strong> {nodeConfig.name}</p>
                    <p><strong>Status:</strong> {nodeConfig.status}</p>
                    <button onClick={handleStartNode} disabled={isStarting}>
                        {isStarting ? 'Starting...' : 'Start Node'}
                    </button>
                </>
            ) : (
                <>
                    <p>Node is not registered. Please enter a name and register.</p>
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
