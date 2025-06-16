import React, { useEffect, useState, useCallback } from 'react';
import { fetchSubmittedTasks, subscribeToSubmittedTaskUpdates } from '../services/api';
import { Task } from '../types/api';
import TaskSummary from '../components/TaskSummary';
import FullTask from '../components/FullTask';
import ErrorPopup from '../components/ErrorPopup';
import { statusColorMap } from '../utils/format';
import { buttonStyle, cardStyle } from '../styles/shared';
import LoadingIndicator from '../components/LoadingIndicator';
import { useNodeConfigOnly } from '../hooks/useNodeConfigOnly';
import { Link } from 'react-router-dom';

const SubmittedTasks: React.FC = () => {
  const { nodeConfig } = useNodeConfigOnly();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoadingTasks, setIsLoadingTasks] = useState<boolean>(true);

  /**
    * Loads the submitted tasks for the current node.
    * If the node ID is not available, it sets an error message.
    * If fetching tasks fails, it sets an error message.
    * Otherwise, it updates the tasks state with the fetched tasks.
  */
  const loadTasks = useCallback(async () => {
    setErrorMessage(null);
    setIsLoadingTasks(true);
    if (nodeConfig?.node_id) {
      try {
        const fetchedTasks = await fetchSubmittedTasks(nodeConfig.node_id);
        setTasks(fetchedTasks);
      } catch {
        setErrorMessage('Failed to fetch tasks.');
      }
    } else {
      setErrorMessage('Node ID is not available. Cannot fetch tasks. Register a node first.');
    }
    setIsLoadingTasks(false);
  }, [nodeConfig?.node_id]);

  useEffect(() => {
    if (!nodeConfig?.node_id) return;

    loadTasks();
    const unsubscribe = subscribeToSubmittedTaskUpdates(
      nodeConfig.node_id,
      () => {
        console.log('[SSE] Triggering task refresh for node:', nodeConfig.node_id);
        loadTasks();
      },
      (error) => {
        console.error('[SSE] Task update stream error:', error);
      }
    );

    return () => unsubscribe();
  }, [nodeConfig?.node_id, loadTasks]);

  return (
    <div style={{ padding: '40px', position: 'relative' }}>
      <div style={{ position: 'relative', marginBottom: '30px', textAlign: 'center' }}>
        <Link
          to="/node"
          className='card-hover'
          style={{
            ...buttonStyle,
            backgroundColor: '#3498db',
            position: 'absolute',
            left: 0,
            top: '0%',
            transform: 'translateY(-50%)',
          }}
        >
          Node Overview
        </Link>

        <h1
          style={{
            fontSize: '32px',
            fontFamily: 'Arial, sans-serif',
            margin: 0,
          }}
        >
          Submitted Tasks
        </h1>

        <Link
          to="/submit-task"
          className='card-hover'
          style={{
            ...buttonStyle,
            backgroundColor: '#3498db',
            position: 'absolute',
            right: 0,
            top: '0%',
            transform: 'translateY(-50%)',
          }}
        >
          Submit New Task
        </Link>
      </div>

      {isLoadingTasks && <LoadingIndicator message="Fetching task submissions" />}

      {!isLoadingTasks && errorMessage && (
        <ErrorPopup
          message={errorMessage}
          onRefresh={() => window.location.reload()}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {!isLoadingTasks && tasks.length === 0 && !errorMessage && (
        <div
          style={{
            textAlign: 'center',
            fontSize: '18px',
            color: '#7f8c8d',
            fontFamily: 'Arial, sans-serif',
          }}
        >
          No tasks submitted by this node yet. Please submit a task to see it here.
        </div>
      )}

      {!isLoadingTasks && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '20px',
            justifyContent: 'center',
          }}
        >
          {tasks.map((task) => (
            <div
              key={task.id}
              className="card-hover"
              onClick={() => setSelectedTask(task)}
              style={cardStyle}
            >
              <TaskSummary task={task} statusColorMap={statusColorMap} />
            </div>
          ))}
        </div>
      )}

      {selectedTask && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000,
            animation: 'fadeIn 0.3s ease-in-out',
          }}
          onClick={() => setSelectedTask(null)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'relative',
              backgroundColor: '#fff',
              borderRadius: '12px',
              padding: '30px',
              maxHeight: '90vh',
              overflowY: 'auto',
              animation: 'scaleIn 0.3s ease-in-out',
            }}
          >
            <button
              onClick={() => setSelectedTask(null)}
              style={{
                position: 'absolute',
                top: '10px',
                right: '15px',
                background: 'none',
                border: 'none',
                fontSize: '22px',
                cursor: 'pointer',
              }}
            >
              &times;
            </button>
            <FullTask task={selectedTask} />
          </div>
        </div>
      )}
    </div>
  );
};

export default SubmittedTasks;
