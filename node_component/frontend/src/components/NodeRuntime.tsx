import React from 'react';

interface ResourceUsage {
  cpu: number;
  ram: number;
}

interface NodeRuntimeProps {
  isRunning: boolean;
  usage?: ResourceUsage;
  isStarting: boolean;
  onStart: () => void;
}

/**
 * NodeRuntime component displays the current status and resource usage of a node.
 * @param {boolean} props.isRunning - Indicates if the node is currently running.
 * @param {ResourceUsage} [props.usage] - The resource usage of the node, including CPU and RAM.
 * @param {boolean} props.isStarting - Indicates if the node is currently starting.
 * @param {function} props.onStart - Callback function to start the node when it is stopped.
 * @returns The rendered component.
 */
const NodeRuntime: React.FC<NodeRuntimeProps> = ({
  isRunning,
  usage,
  isStarting,
  onStart,
}) => {
  const runtimeColor = isRunning ? '#2ecc71' : '#e74c3c';
  const runtimeLabel = isRunning ? 'Running' : 'Stopped';

  return (
    <div style={{ marginTop: '16px', lineHeight: 1.6, fontSize: '16px' }}>
      <div style={{ marginBottom: '10px' }}>
        <strong>Node Runtime Status:</strong>{' '}
        <span
          style={{
            padding: '4px 10px',
            borderRadius: '999px',
            fontWeight: 'bold',
            fontSize: '14px',
            color: '#fff',
            backgroundColor: runtimeColor,
          }}
        >
          {runtimeLabel}
        </span>
      </div>
      {isRunning && usage && (
        <div style={{ marginBottom: '10px' }}>
          <div><strong>CPU Usage:</strong> {usage.cpu}%</div>
          <div><strong>RAM Usage:</strong> {usage.ram} GB</div>
        </div>
      )}
      {!isRunning && (
        <button
          style={{
            padding: '12px 20px',
            fontSize: '16px',
            fontWeight: 'bold',
            color: '#ffffff',
            backgroundColor: '#3498db',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'background-color 0.3s ease',
            marginBottom: '10px',
          }}
          onClick={onStart}
          disabled={isStarting}
        >
          {isStarting ? 'Starting...' : 'Start Node'}
        </button>
      )}
    </div>
  );
};

export default NodeRuntime;
