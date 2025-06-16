import React from 'react';
import { ResourceUsage } from '../types/api';
import LoadingButton from './LoadingButton';

interface NodeRuntimeToggleProps {
  isRunning: boolean;
  usage?: ResourceUsage;
  isStarting: boolean;
  isStopping: boolean;
  onStart: () => void;
  onStop: () => void;
}

/**
 * NodeRuntimeToggle component displays the current status of a node runtime
 * and provides buttons to start or stop the node.
 * @param {boolean} props.isRunning - Indicates if the node is currently running.
 * @param {ResourceUsage} [props.usage] - The resource usage of the node, including CPU and RAM.
 * @param {boolean} props.isStarting - Indicates if the node is currently starting.
 * @param {boolean} props.isStopping - Indicates if the node is currently stopping.
 * @param {function} props.onStart - Callback function to start the node when it is stopped.
 * @param {function} props.onStop - Callback function to stop the node when it is running.
 * @returns The rendered component.
*/
const NodeRuntimeToggle: React.FC<NodeRuntimeToggleProps> = ({
  isRunning,
  usage,
  isStarting,
  isStopping,
  onStart,
  onStop,
}) => {
  const runtimeLabel = isRunning ? 'Running' : 'Stopped';
  const runtimeColor = isRunning ? '#2ecc71' : '#e74c3c';
  const buttonColor = isRunning ? '#e74c3c' : '#3498db';

  return (
    <div style={{ marginBottom: '16px', lineHeight: 1.6, fontSize: '16px' }}>
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

      <LoadingButton
        isLoading={isStarting || isStopping}
        onClick={isRunning ? onStop : onStart}
        style={{ backgroundColor: buttonColor }}
      >
        {isStarting
          ? 'Starting...'
          : isStopping
          ? 'Stopping...'
          : isRunning
          ? 'Stop Node'
          : 'Start Node'}
      </LoadingButton>
    </div>
  );
};

export default NodeRuntimeToggle;
