import React, { useState } from 'react';
import NodeOverview from '../components/NodeOverview';
import TaskSummary from '../components/TaskSummary';
import NodeRuntimeToggle from '../components/NodeRuntimeToggle';
import LoadingButton from '../components/LoadingButton';
import { useNodeData } from '../hooks/useNodeData';
import { containerStyle } from '../styles/shared';
import { trustTooltip, trustBadgeColor } from '../utils/format';

const Node: React.FC = () => {
  const [nodeName, setNodeName] = useState<string>('');
  const {
    nodeConfig,
    fullNode,
    isRegistering,
    isStarting,
    isStopping,
    handleRegisterNode,
    handleStartNode,
    handleStopNode,
  } = useNodeData();

  const getTrustBadgeColor = (value: number): string => trustBadgeColor(value);
  const getTrustTooltip = (value: number): string => trustTooltip(value);

  const translateStatus = (status: string) => {
    if (status === 'completed') return 'Completed';
    if (status === 'in_progress') return 'In Progress';
    return 'Pending';
  };

  return (
    <div id="node" style={containerStyle}>
      <h1 style={{ fontSize: '36px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '30px' }}>
        Node Management
      </h1>

      {nodeConfig?.status === 'registered' && fullNode ? (
        <>
          <NodeOverview
            name={fullNode.name}
            status={nodeConfig.status}
            ipAddress={fullNode.ipAddress}
            trustIndex={fullNode.trustIndex}
            badgeColor={{ backgroundColor: getTrustBadgeColor(fullNode.trustIndex) }}
            badgeTooltip={getTrustTooltip(fullNode.trustIndex)}
          />

          <NodeRuntimeToggle
            isRunning={nodeConfig.is_running ?? false}
            usage={nodeConfig.resource_usage}
            isStarting={isStarting}
            isStopping={isStopping}
            onStart={handleStartNode}
            onStop={handleStopNode}
          />

          <TaskSummary
            task={nodeConfig.last_task}
            statusColorMap={{
              completed: '#27ae60',
              in_progress: '#e67e22',
              pending: '#95a5a6',
            }}
            translateStatus={translateStatus}
          />
        </>
      ) : (
        <div>
          <p>Node is not registered. Please enter a name to register.</p>
          <input
            style={{
              padding: '10px',
              width: '100%',
              marginBottom: '20px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              fontSize: '16px',
            }}
            type="text"
            placeholder="Enter Node Name"
            value={nodeName}
            onChange={(e) => setNodeName(e.target.value)}
          />
          <LoadingButton
            isLoading={isRegistering}
            onClick={() => handleRegisterNode(nodeName)}
            disabled={!nodeName.trim()}
            style={{
              backgroundColor: isRegistering || !nodeName.trim() ? '#a5d6a7' : '#3498db',
              cursor: isRegistering || !nodeName.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {isRegistering ? 'Registering...' : 'Register Node'}
          </LoadingButton>
        </div>
      )}
    </div>
  );
};

export default Node;
