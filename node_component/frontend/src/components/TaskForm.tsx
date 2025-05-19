import React, { useState } from 'react';
import { SubmitTaskPayload } from '../types/api';
import LoadingButton from './LoadingButton';
import { useNodeData } from '../hooks/useNodeData';

interface TaskFormProps {
  onSubmit: (payload: SubmitTaskPayload) => Promise<void>;
  isSubmitting: boolean;
}

const labelStyle: React.CSSProperties = {
  fontWeight: 'bold',
  marginBottom: '6px',
  fontSize: '16px',
};

const inputStyle: React.CSSProperties = {
  padding: '12px',
  fontSize: '16px',
  border: '1px solid #ccc',
  borderRadius: '6px',
  width: '100%',
  boxSizing: 'border-box',
};

const fullWidthFieldStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  marginBottom: '20px',
};

const halfWidthFieldStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  marginBottom: '20px',
  flex: '1 1 45%',
  minWidth: '250px',
  maxWidth: '300px',
};

const rowStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'row',
  justifyContent: 'space-between',
  gap: '20px',
  flexWrap: 'wrap',
};

const tooltipStyle: React.CSSProperties = {
  fontSize: '12px',
  color: '#888',
  marginTop: '4px',
};

const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, isSubmitting }) => {
  const [description, setDescription] = useState('');
  const { nodeConfig, isLoading } = useNodeData();
  const [image, setImage] = useState('');
  const [command, setCommand] = useState('');
  const [cpu, setCpu] = useState<number>(0.5);
  const [ram, setRam] = useState<number>(1);
  const [trustIndexRequired, setTrustIndexRequired] = useState<number>(5);
  const [overlapCount, setOverlapCount] = useState<number>(1);

  const handleSubmit = async (e: React.FormEvent) => {
    if (isLoading) return; 
    e.preventDefault();
    await onSubmit({
      description,
      container_spec: {
        image,
        command,
      },
      resource_requirements: {
        cpu,
        ram,
      },
      trust_index_required: trustIndexRequired,
      overlap_count: overlapCount,
      submitted_by: nodeConfig?.node_id as string,
    });
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        padding: '30px',
        backgroundColor: '#fdfdfd',
        borderRadius: '16px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
        maxWidth: '700px',
        margin: '0 auto',
        fontFamily: 'Arial, sans-serif',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      <div style={fullWidthFieldStyle}>
        <label style={labelStyle}>Task Description</label>
        <input
          style={inputStyle}
          type="text"
          placeholder="Enter a short task description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
      </div>

      <div style={fullWidthFieldStyle}>
        <label style={labelStyle}>Docker Image</label>
        <input
          style={inputStyle}
          type="text"
          placeholder="e.g., ubuntu:latest"
          value={image}
          onChange={(e) => setImage(e.target.value)}
          required
        />
      </div>

      <div style={fullWidthFieldStyle}>
        <label style={labelStyle}>Command (space-separated)</label>
        <input
          style={inputStyle}
          type="text"
          placeholder="e.g., echo hello world"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          required
        />
          <div style={tooltipStyle}>Command to run the container built from the image</div>
      </div>

      <div style={rowStyle}>
        <div style={halfWidthFieldStyle}>
          <label style={labelStyle}>CPU Cores</label>
          <input
            style={inputStyle}
            type="number"
            value={cpu}
            min={0.1}
            step={0.1}
            onChange={(e) => setCpu(parseFloat(e.target.value))}
            required
          />
          <div style={tooltipStyle}>Minimum CPU cores needed (default 1 core)</div>
        </div>

        <div style={halfWidthFieldStyle}>
          <label style={labelStyle}>RAM (GB)</label>
          <input
            style={inputStyle}
            type="number"
            value={ram}
            min={0.5}
            step={0.1}
            onChange={(e) => setRam(parseFloat(e.target.value))}
            required
          />
          <div style={tooltipStyle}>Minimum RAM needed in gigabytes (default 1GB)</div>
        </div>
      </div>

      <div style={rowStyle}>
        <div style={halfWidthFieldStyle}>
          <label style={labelStyle}>Trust Index Required</label>
          <input
            style={inputStyle}
            type="number"
            value={trustIndexRequired}
            min={1}
            max={10}
            step={0.1}
            onChange={(e) => setTrustIndexRequired(parseFloat(e.target.value))}
          />
          <div style={tooltipStyle}>Minimum trust level nodes must have to execute (default 5)</div>
        </div>

        <div style={halfWidthFieldStyle}>
          <label style={labelStyle}>Overlap Count</label>
          <input
            style={inputStyle}
            type="number"
            value={overlapCount}
            min={1}
            onChange={(e) => setOverlapCount(parseInt(e.target.value))}
          />
          <div style={tooltipStyle}>Number of nodes assigned for redundancy (default 1)</div>
        </div>
      </div>

      <LoadingButton
        isLoading={isSubmitting}
        type="submit"
        style={{
          backgroundColor: '#3498db',
          color: 'white',
          fontSize: '20px',
          padding: '14px 0',
          borderRadius: '10px',
          fontWeight: 'bold',
        }}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Task'}
      </LoadingButton>
    </form>
  );
};

export default TaskForm;
