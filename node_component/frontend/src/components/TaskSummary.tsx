import React from 'react';
import dayjs from 'dayjs';
import Badge from './Badge';
import { badgeBaseStyle } from '../styles/shared';

interface Task {
  id: string;
  description?: string;
  status: string;
  started_at: string;
  completed_at?: string;
}

interface TaskSummaryProps {
  task?: Task;
  statusColorMap: Record<string, string>;
  translateStatus: (status: string) => string;
}

const TaskSummary: React.FC<TaskSummaryProps> = ({
  task,
  statusColorMap,
  translateStatus,
}) => {
  if (!task) return <i>No task has been executed yet.</i>;

  const statusColor = statusColorMap[task.status] || '#ccc';
  const itemStyle: React.CSSProperties = { marginBottom: '6px' };

  return (
    <div style={{ paddingTop: '10px', borderTop: '1px solid #ccc' }}>
      <div style={{ fontWeight: 'bold', fontSize: '20px', marginBottom: '8px' }}>
        Last/Active Task
      </div>
      <div style={{ marginTop: '8px', paddingLeft: '10px', lineHeight: '1.6', fontSize: '16px' }}>
        <div style={itemStyle}>
          <strong>Task Name:</strong> {task.description || 'Unnamed Task'}
        </div>
        <div style={itemStyle}>
          <strong>Status:</strong>{' '}
          <Badge
            label={translateStatus(task.status)}
            backgroundColor={statusColor}
            style={badgeBaseStyle}
          />
        </div>
        <div style={itemStyle}>
          <strong>Started:</strong> {dayjs(task.started_at).format('YYYY-MM-DD HH:mm:ss')}
        </div>
        {task.completed_at && (
          <div style={itemStyle}>
            <strong>Completed:</strong> {dayjs(task.completed_at).format('YYYY-MM-DD HH:mm:ss')}
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskSummary;
