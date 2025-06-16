import React from 'react';

interface SuccessPopupProps {
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

const buttonStyle: React.CSSProperties = {
  marginTop: '20px',
  padding: '10px 20px',
  borderRadius: '8px',
  border: 'none',
  backgroundColor: '#3498db',
  color: 'white',
  fontSize: '16px',
  cursor: 'pointer',
};

/**
 * SuccessPopup component displays a success message with optional actions.
 * @param  {string} message - The success message to display.
 * @param {function} [onClose] - Optional callback function to execute when the popup is closed.
 * @returns {JSX.Element} The rendered component.
 */
const SuccessPopup: React.FC<SuccessPopupProps> = ({ message, onClose }) => {
  return (
    <div style={overlayStyle}>
      <div style={popupStyle}>
        <h2 style={{ color: '#2ecc71', marginBottom: '20px' }}>Success</h2>
        <p style={{ fontSize: '16px' }}>{message}</p>
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '10px' }}>
          {onClose && (<button style={buttonStyle} onClick={onClose}> Ok </button> )}
        </div>
      </div>
    </div>
  );
};

export default SuccessPopup;
