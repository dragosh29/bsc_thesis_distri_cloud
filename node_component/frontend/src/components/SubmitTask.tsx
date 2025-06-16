import React, { useState } from 'react';
import { buttonStyle, containerStyle } from '../styles/shared';
import TaskForm from '../components/TaskForm';
import ErrorPopup from '../components/ErrorPopup';
import SuccessPopup from '../components/SuccessPopup'; 
import { submitTask } from '../services/api';
import { Link } from 'react-router-dom';

/**
 * SubmitTask component allows users to submit new tasks.
 * @returns  {JSX.Element} A component for submitting new tasks.
 */
const SubmitTask: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (payload: any) => {
    try {
      setIsSubmitting(true);
      await submitTask(payload);
      setSuccessMessage('Task submitted successfully!');
      setErrorMessage(null);
    } catch (error) {
      console.error(error);
      setErrorMessage('Failed to submit task. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div id="submit-task" style={containerStyle}>
      <Link
          to="/submitted-tasks"
          className='card-hover'
          style={{
            ...buttonStyle,
            backgroundColor: '#3498db',
            position: 'absolute',
            left: '5%',
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

      {successMessage && (
        <SuccessPopup
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      <h1 style={{ fontSize: '32px', marginBottom: '24px' }}>Submit New Task</h1>
      <TaskForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
    </div>
  );
};

export default SubmitTask;
