import React from 'react';
import { capitalize, statusColorMap } from '../utils/format';
import { badgeBaseStyle } from '../styles/shared';
import Badge from './Badge';

interface Props {
  name: string;
  status: string;
  ipAddress: string;
  trustIndex: number;
  badgeColor: React.CSSProperties;
  badgeTooltip: string;
}

const NodeOverview: React.FC<Props> = ({
  name,
  status,
  ipAddress,
  trustIndex,
  badgeColor,
  badgeTooltip,
}) => {
  const formattedStatus = capitalize(status);
  const statusColor = statusColorMap[status.toLowerCase()] || statusColorMap.unknown;

  return (
    <div style={{ marginBottom: '16px', lineHeight: 1.6, fontSize: '16px' }}>
      <div style={{ marginBottom: '10px' }}><strong>Node Name:</strong> {name}</div>
      <div style={{ marginBottom: '10px' }}>
        <strong>Status:</strong>{' '}
        <Badge label={formattedStatus} backgroundColor={statusColor} style={badgeBaseStyle} />
      </div>
      <div style={{ marginBottom: '10px' }}><strong>IP Address:</strong> {ipAddress}</div>
      <div style={{ marginBottom: '10px' }}>
        <strong>Trust Index:</strong>{' '}
        <Badge
          label={trustIndex.toFixed(1)}
          backgroundColor={badgeColor.backgroundColor ?? '#ccc'}
          title={badgeTooltip}
          style={badgeBaseStyle}
        />
      </div>
    </div>
  );
};

export default NodeOverview;
