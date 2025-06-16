import React from 'react';

interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading: boolean;
  children: React.ReactNode;
}

/**
 *  LoadingButton component that displays a button with a loading spinner when `isLoading` is true.
 *  @param {boolean} isLoading - Indicates whether the button is in a loading state.
 *   @param {React.ReactNode} children - The content to display inside the button.
 *  @param {React.ButtonHTMLAttributes<HTMLButtonElement>} rest - Additional props for the button.
 *  @returns {JSX.Element} A button element that shows a spinner when loading.
*/
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
