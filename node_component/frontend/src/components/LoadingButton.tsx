import React from 'react';

interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading: boolean;
  children: React.ReactNode;
}

const LoadingButton: React.FC<LoadingButtonProps> = ({ isLoading, children, ...rest }) => {
  return (
    <button
      {...rest}
      style={{
        padding: '12px 20px',
        fontSize: '16px',
        fontWeight: 'bold',
        color: '#ffffff',
        border: 'none',
        borderRadius: '8px',
        transition: 'background-color 0.3s ease',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '10px',
        opacity: isLoading ? 0.8 : 1,
        ...rest.style,
      }}
      disabled={isLoading || rest.disabled}
    >
      {isLoading && (
        <span
          className="spinner"
          style={{
            width: '18px',
            height: '18px',
            border: '2px solid #fff',
            borderTop: '2px solid transparent',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
      )}
      {children}
    </button>
  );
};

export default LoadingButton;
