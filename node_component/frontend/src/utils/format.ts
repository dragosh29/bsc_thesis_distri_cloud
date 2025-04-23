export const capitalize = (text: string) =>
    text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  
  export const statusColorMap: Record<string, string> = {
    registered: '#3498db',
    active: '#2ecc71',
    busy: '#e67e22',
    inactive: '#95a5a6',
    unknown: '#bdc3c7',
  };
  
  export const trustTooltip = (value: number) =>
    value >= 8 ? 'High Trust' : value >= 5 ? 'Moderate Trust' : 'Low Trust';
  
  export const trustBadgeColor = (value: number): string =>
    value >= 8 ? '#2ecc71' : value >= 5 ? '#f39c12' : '#e74c3c';
  