export const capitalize = (text: string) =>
    text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
  
export const statusColorMap: Record<string, string> = {
    registered: '#3498db',
    active: '#2ecc71',
    busy: '#e67e22',
    inactive: '#95a5a6',
    unknown: '#bdc3c7',
    completed: '#27ae60',
    in_progress: '#e67e22',
    validating: '#f39c12',
    validated: '#2ecc71',
    failed: '#e74c3c',
    in_queue: '#3498db',
    pending: '#95a5a6',
    invalid: '#e74c3c',
};
  
export const trustTooltip = (value: number) =>
    value >= 8 ? 'High Trust' : value >= 5 ? 'Moderate Trust' : 'Low Trust';
  
export const trustBadgeColor = (value: number): string =>
    value >= 8 ? '#2ecc71' : value >= 5 ? '#f39c12' : '#e74c3c';
  
export const getUpdatedTimestampLabel = (status: string): string => {
    switch (status) {
      case 'validated':
        return 'Result validated at:';
      case 'completed':
        return "All results submitted and awaiting validation since:";
      case 'validating':
        return 'Docker image submitted and awaiting validation since:';
      default:
        return 'Last update at:';
    }
  };

export const translateTaskStatus = (status: string) => {
    if (status === 'invalid') {
        return 'Invalid Docker Image';
    }
    return status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };