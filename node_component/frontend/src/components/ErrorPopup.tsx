import React from 'react';
import { buttonStyle } from '../styles/shared';

interface ErrorPopupProps {
  message: string;
  onRefresh?: () => void;
  onClose?: () => void;
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 9999,
};

const popupStyle: React.CSSProperties = {
  backgroundColor: '#fff',
  padding: '30px',
  borderRadius: '12px',
  width: '90%',
  maxWidth: '400px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
  textAlign: 'center',
  fontFamily: 'Arial, sans-serif',
};

/**
  * ErrorPopup component to display an error message with options to refresh or close.
  * @param {string} message - The error message to display.
  * @param {function} [onRefresh] - Optional callback function to execute on refresh.
  * @param {function} [onClose] - Optional callback function to execute on close.
  * @returns {JSX.Element} A styled popup with the error message and action buttons.
  */
const ErrorPopup: React.FC<ErrorPopupProps> = ({ message, onRefresh, onClose }) => {
  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      window.location.reload(); // default: reload page
    }
  };

  return (
    <div style={overlayStyle}>
      <div style={popupStyle}>
        <h2 style={{ color: '#e74c3c', marginBottom: '20px' }}>Error</h2>
        <p style={{ fontSize: '16px' }}>{message}</p>
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
          <button style={buttonStyle} onClick={handleRefresh}>
            Refresh Page
          </button>
          {onClose && (
            <button
              style={{
                ...buttonStyle,
                backgroundColor: '#3498db',
              }}
              onClick={onClose}
            >
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorPopup;
