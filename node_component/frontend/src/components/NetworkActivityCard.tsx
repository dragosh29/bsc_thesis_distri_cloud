import React, { useEffect, useState } from 'react';
import { cardStyle, badgeBaseStyle } from '../styles/shared';
import LoadingIndicator from './LoadingIndicator';
import { NetworkActivityData } from '../types/api';
import { subscribeToNetworkActivity } from '../services/api';
import { trustBadgeColor, trustTooltip, statusColorMap, translateTaskStatus } from '../utils/format';

const defaultData: NetworkActivityData = {
  active_nodes: 0,
  total_cpu: 0,
  total_ram: 0,
  pending_tasks: 0,
  in_queue_tasks: 0,
  in_progress_tasks: 0,
  completed_tasks: 0,
  validated_tasks: 0,
  failed_tasks: 0,
  average_trust_index: 0,
};

const NetworkActivityCard: React.FC = () => {
  const [data, setData] = useState<NetworkActivityData>(defaultData);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = subscribeToNetworkActivity(
      (newData) => {
        setData(newData);
        setIsLoading(false);
      },
      (error) => {
        console.error('SSE error:', error);
      }
    );
    return () => unsubscribe();
  }, []);

  const trustBadgeStyle = {
    ...badgeBaseStyle,
    backgroundColor: trustBadgeColor(data.average_trust_index),
  };

  const renderTaskStatus = (label: string, key: keyof NetworkActivityData) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ ...badgeBaseStyle, backgroundColor: statusColorMap[label] || '#7f8c8d' }}>
        {translateTaskStatus(label)}
      </span>
      <span style={{ fontWeight: 600 }}>{data[key]}</span>
    </div>
  );

  return (
    <div style={{ ...cardStyle, padding: '24px', width:'100%', maxWidth: '700px', animation: 'scaleIn 0.3s ease-in-out' }}>
  {isLoading ? (
    <LoadingIndicator message="Loading network data..." />
  ) : (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
      <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'flex'}}>
        <h3 style={{ fontSize: '24px', margin: 0 }}>Network Activity</h3>
        <h3 style={{ fontSize: '24px', margin: 0 }}>Global Task Status Summary</h3>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', width: '100%', gap: '60px' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>Active Nodes: {data.active_nodes}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            Average Trust Index:
            <span style={trustBadgeStyle} title={trustTooltip(data.average_trust_index)}>
              {data.average_trust_index.toFixed(1)}
            </span>
          </div>
          <div>Total CPU: {data.total_cpu.toFixed(2)} Cores</div>
          <div>Total RAM: {data.total_ram.toFixed(2)} GB</div>
        </div>

        <div style={{ flex: 1.4, display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '300px' }}>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {renderTaskStatus('pending', 'pending_tasks')}
              {renderTaskStatus('in_queue', 'in_queue_tasks')}
              {renderTaskStatus('in_progress', 'in_progress_tasks')}
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px', marginLeft: '20px' }}>
              {renderTaskStatus('completed', 'completed_tasks')}
              {renderTaskStatus('validated', 'validated_tasks')}
              {renderTaskStatus('failed', 'failed_tasks')}
            </div>
          </div>
        </div>
      </div>
    </div>
  )}
</div>

  );
};

export default NetworkActivityCard;
