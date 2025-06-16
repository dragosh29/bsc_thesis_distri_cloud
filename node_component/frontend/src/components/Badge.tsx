import React from 'react';

interface BadgeProps {
  label: string;
  backgroundColor: string;
  style?: React.CSSProperties;
  title?: string;
}

/**
 *  Badge component to display a label with a customizable background color.
 * @param {string} label - The text to display inside the badge.
 * @param {string} backgroundColor - The background color of the badge.
 * @param {React.CSSProperties} [style] - Optional additional styles to apply to the badge.
 * @param {string} [title] - Optional title attribute for the badge, displayed as a tooltip on hover.
 * @returns {JSX.Element} A styled span element representing the badge.
 */
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
