import React from 'react';

interface LoadingIndicatorProps {
  message?: string;
}

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ message = 'Loading...' }) => {
  return (
    <div style={{ textAlign: 'center', marginTop: '60px' }}>
      <div style={{ display: 'inline-block' }}>
        <div
          style={{
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            animation: 'spin 1s linear infinite',
            margin: '0 auto',
          }}
        />
        <div
          style={{
            marginTop: '12px',
            fontSize: '18px',
            color: '#555',
            fontFamily: 'Arial, sans-serif',
          }}
        >
          {message}
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;
