import React from 'react';

interface BadgeProps {
  label: string;
  backgroundColor: string;
  style?: React.CSSProperties;
  title?: string;
}

const Badge: React.FC<BadgeProps> = ({ label, backgroundColor, style = {}, title }) => (
  <span
    title={title}
    style={{
      display: 'inline-block',
      padding: '4px 10px',
      borderRadius: '999px',
      fontWeight: 'bold',
      fontSize: '14px',
      color: '#fff',
      backgroundColor,
      ...style
    }}
  >
    {label}
  </span>
);

export default Badge;
