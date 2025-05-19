import React, { useState } from 'react';
import NodeOverview from '../components/NodeOverview';
import TaskSummary from '../components/TaskSummary';
import NodeRuntimeToggle from '../components/NodeRuntimeToggle';
import LoadingButton from '../components/LoadingButton';
import ErrorPopup from '../components/ErrorPopup';
import { useNodeData } from '../hooks/useNodeData';
import { buttonStyle, containerStyle } from '../styles/shared';
import { trustTooltip, trustBadgeColor } from '../utils/format';
import NetworkActivityCard from '../components/NetworkActivityCard';
import { Link } from 'react-router-dom';

const Node: React.FC = () => {
  const [nodeName, setNodeName] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  const safeHandleStartNode = async () => {
    try {
      await handleStartNode();
      setErrorMessage(null);
    } catch (error) {
      console.error(error);
      setErrorMessage('Failed to start node. Please try refreshing.');
    }
  };

  const safeHandleStopNode = async () => {
    try {
      await handleStopNode();
      setErrorMessage(null);
    } catch (error) {
      console.error(error);
      setErrorMessage('Failed to stop node. Please try refreshing.');
    }
  };

  const safeHandleRegisterNode = async (name: string) => {
    try {
      await handleRegisterNode(name);
      setErrorMessage(null);
    } catch (error) {
      console.error(error);
      setErrorMessage('Failed to register node. Please try refreshing.');
    }
  };

  return (
    <div id="node" style={containerStyle}>
      <Link
          to="/submitted-tasks"
          className='card-hover'
          style={{
            ...buttonStyle,
            backgroundColor: '#3498db',
            position: 'absolute',
            right: '5%',
            top: '5%',
            transform: 'translateY(-50%)',
          }}
        >
          Tasks Overview
        </Link>
      {errorMessage && (
        <ErrorPopup
          message={errorMessage}
          onRefresh={() => window.location.reload()}
          onClose={() => setErrorMessage(null)}
        />
      )}

      <h1 style={{ fontSize: '36px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '50px', textAlign: 'center' }}>
        Node Management
      </h1>
      
      {nodeConfig?.status === 'registered' && fullNode ? (
        <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '40px',
          flexWrap: 'wrap',

        }}
      >
        <div style={{ flex: 1, minWidth: '300px' }}>
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
            onStart={safeHandleStartNode}
            onStop={safeHandleStopNode}
          />
        </div>
      
        <div style={{ flex: 1, minWidth: '300px' }}>
          <TaskSummary
            task={nodeConfig.last_task}
            statusColorMap={{
              completed: '#27ae60',
              in_progress: '#e67e22',
              pending: '#95a5a6',
            }}
            title={nodeConfig.last_task?.status === 'completed' ? 'Last Task Executed' : 'Current Task Running'}
          />
        </div>
      </div>
      
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
            onClick={() => safeHandleRegisterNode(nodeName)}
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
      <div style={{ marginTop: '50px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', color: '#2c3e50', marginBottom: '20px' }}>
          Network Activity
        </h2>
          <NetworkActivityCard />
      </div>
    </div>
  );
};

export default Node;
