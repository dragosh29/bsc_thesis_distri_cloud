import React, { useState } from 'react';
import dayjs from 'dayjs';
import { Task } from '../types/api';
import copy from 'copy-to-clipboard';

import { getUpdatedTimestampLabel, trustBadgeColor, statusColorMap, translateTaskStatus } from '../utils/format';
import { badgeBaseStyle } from '../styles/shared';
import Badge from './Badge';

const FullTask: React.FC<{ task: Task }> = ({ task }) => {
  const { result } = task;
  const trustScore = result?.trust_score;
  const validatedOutput = result?.validated_output;
  const error = result?.error;
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    copy(JSON.stringify(validatedOutput));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    columnGap: '30px',
    rowGap: '12px',
    fontSize: '15px',
  };

  const labelStyle: React.CSSProperties = {
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: '4px',
  };

  const valueStyle: React.CSSProperties = {
    wordBreak: 'break-word',
  };

  const resultBoxStyle: React.CSSProperties = {
    backgroundColor: '#f8f9fa',
    padding: '8px',
    borderRadius: '8px',
    fontFamily: 'Courier, monospace',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    fontSize: '14px',
    color: '#2d3436',
    border: '1px solid #dfe6e9',
    marginTop: '10px',
    display: 'flex',
    flexDirection: 'column',
  };

  const sectionTitleStyle: React.CSSProperties = {
    fontWeight: 600,
    fontSize: '16px',
    marginTop: '30px',
    marginBottom: '10px',
  };

  return (
    <div style={{ padding: '30px', maxWidth: '720px', backgroundColor: '#fff', borderRadius: '16px', fontFamily: 'Arial, sans-serif', color: '#333' }}>
      <h2 style={{ fontSize: '24px', marginBottom: '30px', fontWeight: 600 }}>
        {task.description || 'Unnamed Task'}
      </h2>

      <div style={gridStyle}>
        {/* Status with badge */}
        <div>
          <div style={labelStyle}>Status:</div>
          <Badge
            label={translateTaskStatus(task.status)}
            backgroundColor={statusColorMap[task.status] || '#ccc'}
            style={badgeBaseStyle}
          />
        </div>

        {/* Trust Score */}
        {trustScore !== undefined && (
          <div>
            <div style={labelStyle}>Trust Score:</div>
            <div style={{
              backgroundColor: trustBadgeColor(trustScore),
              color: '#fff',
              borderRadius: '999px',
              padding: '4px 10px',
              fontWeight: 'bold',
              fontSize: '14px',
              display: 'inline-block',
            }}>
              {trustScore.toFixed(1)}
            </div>
          </div>
        )}

        {/* Submitted */}
        <div>
          <div style={labelStyle}>Submitted at:</div>
          <div style={valueStyle}>{dayjs(task.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
        </div>

        {/* Updated */}
        {task.updated_at && (
          <div>
            <div style={labelStyle}>{getUpdatedTimestampLabel(task.status)}</div>
            <div style={valueStyle}>{dayjs(task.updated_at).format('YYYY-MM-DD HH:mm:ss')}</div>
          </div>
        )}
      </div>

      {/* Validated Output */}
      {validatedOutput && (
        <div style={{ marginTop: '30px' }}>
          <div style={sectionTitleStyle}>Validated Output:</div>

          <div
            style={{
              ...resultBoxStyle,
              maxHeight: isExpanded ? 'none' : '100px',
              overflowY: isExpanded ? 'visible' : 'auto',
              position: 'relative',
            }}
          >
            <button
              onClick={handleCopy}
              style={{
                position: 'sticky',
                top: '0',
                right: '0',
                marginBottom: '5px',
                marginLeft: 'auto',
                fontSize: '13px',
                padding: '4px 8px',
                borderRadius: '6px',
                backgroundColor: copied ? '#2ecc71' : '#3498db',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
                transition: 'background-color 0.2s ease',
                zIndex: 10,
              }}
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {validatedOutput}
          </div>

          {validatedOutput.length > 100 && (
            <div style={{ marginTop: '8px' }}>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                style={{
                  fontSize: '13px',
                  color: '#3498db',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                {isExpanded ? 'Show Less ▲' : 'Show More ▼'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Execution Error */}
      {error && (
        <div style={{ marginTop: '30px' }}>
          <div style={{ ...sectionTitleStyle, color: '#e74c3c' }}>Execution Error:</div>
          <div style={{ ...resultBoxStyle, border: '1px solid #e74c3c', backgroundColor: '#fdecea' }}>
            {error}
          </div>
        </div>
      )}

      {/* Container Spec */}
      <div style={sectionTitleStyle}>Container Spec:</div>
      <div style={gridStyle}>
        <div>
          <div style={labelStyle}>Image:</div>
          <div style={valueStyle}>{task.container_spec.image}</div>
        </div>
        <div>
          <div style={labelStyle}>Command:</div>
          <div style={valueStyle}>{task.container_spec.command}</div>
        </div>
      </div>

      {/* Resources */}
      <div style={sectionTitleStyle}>Resource Requirements:</div>
      <div style={gridStyle}>
        <div>
          <div style={labelStyle}>CPU:</div>
          <div style={valueStyle}>{task.resource_requirements.cpu}</div>
        </div>
        <div>
          <div style={labelStyle}>RAM:</div>
          <div style={valueStyle}>{task.resource_requirements.ram} GB</div>
        </div>
      </div>

      {/* Constraints */}
      {(task.trust_index_required !== undefined || task.overlap_count !== undefined) && (
        <>
          <div style={sectionTitleStyle}>Execution Constraints:</div>
          <div style={gridStyle}>
            {task.trust_index_required !== undefined && (
              <div>
                <div style={labelStyle}>Trust Index Required:</div>
                <div style={valueStyle}>{task.trust_index_required}</div>
              </div>
            )}
            {task.overlap_count !== undefined && (
              <div>
                <div style={labelStyle}>Overlap Count:</div>
                <div style={valueStyle}>{task.overlap_count}</div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default FullTask;
