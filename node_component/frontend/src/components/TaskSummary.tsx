import React from 'react';
import dayjs from 'dayjs';
import Badge from './Badge';
import { badgeBaseStyle, cardStyle } from '../styles/shared';
import { Task, TaskAssignment } from '../types/api';
import { getUpdatedTimestampLabel, translateTaskStatus } from '../utils/format';

interface TaskSummaryProps {
  task?: Task | TaskAssignment;
  statusColorMap: Record<string, string>;
  noTaskMessage?: string;
  title?: string;
}

const TaskSummary: React.FC<TaskSummaryProps> = ({
  task,
  statusColorMap,
  noTaskMessage = 'No task has been executed yet.',
  title = ''
}) => {
  if (!task) return <i>{noTaskMessage}</i>;

  const statusColor = statusColorMap[task.status] || '#ccc';
  const isAssignment = 'started_at' in task && 'status' in task && !('created_at' in task);

  const renderTimestamps = () => {
    if (isAssignment) {
      return (
        <>
          <div style={{ marginBottom: '8px' }}>
            <strong>Started:</strong> {dayjs((task as TaskAssignment).started_at).format('YYYY-MM-DD HH:mm:ss')}
          </div>
          {(task as TaskAssignment).completed_at && (
            <div style={{ marginBottom: '8px' }}>
              <strong>Completed:</strong> {dayjs((task as TaskAssignment).completed_at!).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          )}
        </>
      );
    } else {
      const t = task as Task;
      const updatedLabel = getUpdatedTimestampLabel(t.status);
  
      return (
        <>
          <div style={{ marginBottom: '8px' }}>
            <strong>Submitted at:</strong> {dayjs(t.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </div>
          {t.updated_at && (
            <div style={{ marginBottom: '8px' }}>
              <strong>{updatedLabel}</strong> {dayjs(t.updated_at).format('YYYY-MM-DD HH:mm:ss')}
            </div>
          )}
        </>
      );
    }
  };
  

  return (
    <div style={cardStyle}>
      {title && (
        <div style={{ fontSize: '20px', fontWeight: 600, marginBottom: '25px', textAlign: 'center' }}>
          {title}
        </div>
      )}
      <div style={{ fontSize: '18px', marginBottom: '15px', fontWeight: 700 }}>
        {task.description || 'Unnamed Task'}
      </div>

      <div style={{ lineHeight: '1.8', fontSize: '15px' }}>
        <div style={{ marginBottom: '8px' }}>
          <strong>Status:</strong>{' '}
          <Badge
            label={translateTaskStatus(task.status)}
            backgroundColor={statusColor}
            style={badgeBaseStyle}
          />
        </div>

        {renderTimestamps()}
      </div>
    </div>
  );
};

export default TaskSummary;
