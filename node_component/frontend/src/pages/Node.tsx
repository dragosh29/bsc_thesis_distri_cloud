import React, { useEffect, useState } from 'react';
import axios from 'axios';
import dayjs from 'dayjs';

const LOCAL_API_BASE_URL = import.meta.env.VITE_LOCAL_API_BASE_URL;
const HUB_API_BASE_URL = import.meta.env.VITE_HUB_API_BASE_URL;

interface NodeConfig {
    id?: string;
    status: string;
    is_running?: boolean;
    last_task_id?: string;
    last_task?: {
        id: string;
        description?: string;
        status: string;
        started_at: string;
        completed_at?: string;
    };
    resource_usage?: {
        cpu: number;
        ram: number;
    };
}

interface FullNode {
    name: string;
    status: string;
    resourceCapacity: { cpu: number; ram: number };
    resourceAvailable: { cpu: number; ram: number };
    ipAddress: string;
    trustIndex: number;
}

const Node: React.FC = () => {
    const [nodeConfig, setNodeConfig] = useState<NodeConfig | null>(null);
    const [nodeName, setNodeName] = useState('');
    const [isRegistering, setIsRegistering] = useState(false);
    const [isStarting, setIsStarting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [fullNode, setFullNode] = useState<FullNode | null>(null);

    const fetchLastTaskDetails = async (taskId: string, nodeId: string) => {
        try {
            const response = await axios.get(`${HUB_API_BASE_URL}/tasks/${taskId}?node_id=${nodeId}`);
            const task = response.data;
            setNodeConfig(prev => {
                if (!prev) return prev;
                const status = task.assignment?.completed_at ? "completed" : "in_progress";
                return {
                    ...prev,
                    last_task: {
                        id: task.id,
                        description: task.description,
                        status,
                        started_at: task.assignment?.started_at || '',
                        completed_at: task.assignment?.completed_at || undefined,
                    }
                };
            });
        } catch (err) {
            console.error("Failed to fetch task details:", err);
        }
    };

    const fetchNodeStatus = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${LOCAL_API_BASE_URL}/node`);
            const config = response.data;
            setNodeConfig(config);
            if (config?.node_id && config?.last_task_id) {
                await fetchLastTaskDetails(config.last_task_id, config.node_id);
            }
            if (config?.node_id) {
                await fetchFullNode(config.node_id);
            }
        } catch (err) {
            console.error('Failed to fetch node status:', err);
            setError('Failed to fetch node status.');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchFullNode = async (id: string) => {
        try {
            const response = await axios.get(`${HUB_API_BASE_URL}/nodes/${id}`);
            const fullNode: FullNode = {
                name: response.data.name,
                status: response.data.status,
                resourceCapacity: {
                    cpu: response.data.resources_capacity.cpu,
                    ram: response.data.resources_capacity.ram,
                },
                resourceAvailable: {
                    cpu: response.data.free_resources.free_cpu,
                    ram: response.data.free_resources.free_ram,
                },
                ipAddress: response.data.ip_address,
                trustIndex: response.data.trust_index,
            };
            setFullNode(fullNode);
        } catch (err) {
            console.error('Failed to fetch node details:', err);
            setError('Failed to fetch node details.');
        }
    };

    const handleRegisterNode = async () => {
        if (!nodeName.trim()) {
            setError('Node name cannot be empty.');
            return;
        }

        setIsRegistering(true);
        setError(null);
        try {
            await axios.post(`${LOCAL_API_BASE_URL}/node/register`, { name: nodeName });
            await fetchNodeStatus();
        } catch (err) {
            console.error('Failed to register Node:', err);
            setError('Failed to register Node. Please try again.');
        } finally {
            setIsRegistering(false);
        }
    };

    const handleStartNode = async () => {
        setIsStarting(true);
        setError(null);
        try {
            await axios.post(`${LOCAL_API_BASE_URL}/node/start`);
            await fetchNodeStatus();
        } catch (err) {
            console.error('Failed to start Node Manager:', err);
            setError('Failed to start Node Manager. Please try again.');
        } finally {
            setIsStarting(false);
        }
    };

    useEffect(() => {
        fetchNodeStatus();
        const interval = setInterval(fetchNodeStatus, 15000);
        return () => clearInterval(interval);
    }, []);

    const translateStatus = (status: string) => {
        if (status === 'completed') return 'Completed';
        if (status === 'in_progress') return 'In Progress';
        return 'Pending';
    };

    const formatDate = (dateStr: string) =>
        dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss');

    const getTrustIndexColor = (value: number) => {
        if (value >= 8) return { backgroundColor: '#2ecc71' };
        if (value >= 5) return { backgroundColor: '#f39c12' };
        return { backgroundColor: '#e74c3c' };
    };

    const getTrustIndexTitle = (value: number) => {
        if (value >= 8) return 'High Trust';
        if (value >= 5) return 'Moderate Trust';
        return 'Low Trust';
    };

    const styles = {
        container: {
            maxWidth: '800px',
            margin: '50px auto',
            padding: '30px',
            backgroundColor: '#ffffff',
            borderRadius: '15px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)',
            fontFamily: 'Arial, sans-serif',
            color: '#333',
        },
        header: {
            fontSize: '36px',
            fontWeight: 'bold',
            color: '#2c3e50',
            marginBottom: '30px',
        },
        input: {
            padding: '10px',
            width: '100%',
            marginBottom: '20px',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontSize: '16px',
        },
        button: {
            padding: '12px 20px',
            fontSize: '16px',
            fontWeight: 'bold',
            color: '#ffffff',
            backgroundColor: '#3498db',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'background-color 0.3s ease',
            marginBottom: '8px',
        },
        buttonDisabled: {
            backgroundColor: '#a5d6a7',
            cursor: 'not-allowed',
        },
        errorContainer: {
            backgroundColor: '#fdecea',
            border: '1px solid #e74c3c',
            borderRadius: '8px',
            color: '#e74c3c',
            padding: '15px',
            marginBottom: '20px',
        },
        nodeDetails: {
            textAlign: 'left' as const,
            margin: '20px 0',
            padding: '15px',
            backgroundColor: '#ecf0f1',
            borderRadius: '10px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        },
        detailItem: {
            marginBottom: '10px',
            fontSize: '18px',
        },
        label: {
            fontWeight: 'bold',
        },
        badge: {
            display: 'inline-block',
            padding: '4px 10px',
            borderRadius: '999px',
            fontWeight: 'bold',
            fontSize: '14px',
            color: '#fff',
            marginTop: '5px',
            marginBottom: '10px',
        },
        statusCompleted: { backgroundColor: '#27ae60' },
        statusInProgress: { backgroundColor: '#e67e22' },
        statusPending: { backgroundColor: '#95a5a6' },
    };

    return (
        <div id="node" style={styles.container}>
            <h1 style={styles.header}>Node Management</h1>
            {error && (
                <div style={styles.errorContainer}>
                    <p>{error}</p>
                    <button style={styles.button} onClick={fetchNodeStatus}>
                        Retry
                    </button>
                </div>
            )}
            {nodeConfig?.status === 'registered' && fullNode ? (
                <div style={styles.nodeDetails}>
                    <p style={styles.detailItem}><span style={styles.label}>Node Name:</span> {fullNode.name}</p>
                    <p style={styles.detailItem}><span style={styles.label}>Status:</span> {nodeConfig.status}</p>
                    <p style={styles.detailItem}><span style={styles.label}>IP Address:</span> {fullNode.ipAddress}</p>
                    <p style={styles.detailItem}>
                        <span style={styles.label}>Trust Index:</span>{" "}
                        <span
                            style={{ ...styles.badge, ...getTrustIndexColor(fullNode.trustIndex) }}
                            title={getTrustIndexTitle(fullNode.trustIndex)}
                        >
                            {fullNode.trustIndex.toFixed(1)}
                        </span>
                    </p>
                    {nodeConfig.is_running && (
                        <>
                            <p style={styles.detailItem}><span style={styles.label}>Node Runtime Status:</span> Running</p>
                            {nodeConfig.resource_usage && (
                                <p style={styles.detailItem}>
                                    <span style={styles.label}>CPU Usage:</span> {nodeConfig.resource_usage.cpu}%<br />
                                    <span style={styles.label}>RAM Usage:</span> {nodeConfig.resource_usage.ram} MB
                                </p>
                            )}
                        </>
                    )}
                    {!nodeConfig.is_running && (
                        <button
                            style={isStarting ? { ...styles.button, ...styles.buttonDisabled } : styles.button}
                            onClick={handleStartNode}
                            disabled={isStarting}
                        >
                            {isStarting ? 'Starting...' : 'Start Node'}
                        </button>
                    )}
                    <div style={{ ...styles.detailItem, paddingTop: '10px', borderTop: '1px solid #ccc' }}>
                        <span style={{ ...styles.label, fontSize: '20px' }}>Last/Active Task</span>
                        <div style={{ marginTop: '8px', paddingLeft: '10px' }}>
                            {nodeConfig.last_task ? (
                                <>
                                    <div><span style={styles.label}>Task Name:</span> {nodeConfig.last_task.description || "Unnamed Task"}</div>
                                    <div><span style={styles.label}>Task ID:</span> {nodeConfig.last_task.id}</div>
                                    <div>
                                        <span style={styles.label}>Status:</span>{" "}
                                        <span style={{
                                            ...styles.badge,
                                            ...(nodeConfig.last_task.status === "completed"
                                                ? styles.statusCompleted
                                                : nodeConfig.last_task.status === "in_progress"
                                                    ? styles.statusInProgress
                                                    : styles.statusPending)
                                        }}>
                                            {translateStatus(nodeConfig.last_task.status)}
                                        </span>
                                    </div>
                                    <div><span style={styles.label}>Started:</span> {formatDate(nodeConfig.last_task.started_at)}</div>
                                    {nodeConfig.last_task.completed_at && (
                                        <div><span style={styles.label}>Completed:</span> {formatDate(nodeConfig.last_task.completed_at)}</div>
                                    )}
                                </>
                            ) : (
                                <i>No task has been executed yet.</i>
                            )}
                        </div>
                    </div>
                </div>
            ) : (
                <div>
                    <p>Node is not registered. Please enter a name to register.</p>
                    <input
                        style={styles.input}
                        type="text"
                        placeholder="Enter Node Name"
                        value={nodeName}
                        onChange={(e) => setNodeName(e.target.value)}
                    />
                    <button
                        style={isRegistering || !nodeName ? { ...styles.button, ...styles.buttonDisabled } : styles.button}
                        onClick={handleRegisterNode}
                        disabled={isRegistering || !nodeName}
                    >
                        {isRegistering ? 'Registering...' : 'Register Node'}
                    </button>
                </div>
            )}
        </div>
    );
};

export default Node;
