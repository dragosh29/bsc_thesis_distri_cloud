/**
 * Capitalizes the first letter of a string and lowercases the rest.
 * @param text - The input string to capitalize.
 * @returns The capitalized string.
 */
export const capitalize = (text: string) =>
    text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();

/**
 * Formats a number with commas as thousands separators.
 * @param num - The number to format.
 * @returns The formatted number as a string.
 */
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
  
/**
 * Generates a tooltip text based on the trust value.
 * @param value  - The trust value to evaluate.
 * @returns {string} The tooltip text based on the trust value.
 */
export const trustTooltip = (value: number) =>
    value >= 8 ? 'High Trust' : value >= 5 ? 'Moderate Trust' : 'Low Trust';

/**
 *  Returns a color based on the trust value.
 *  @param value - The trust value to evaluate.
 *  @returns {string} The color associated with the trust value.
 */
export const trustBadgeColor = (value: number): string =>
    value >= 8 ? '#2ecc71' : value >= 5 ? '#f39c12' : '#e74c3c';

/**
 *  Formats a number to a string with two decimal places.
 *  @param num - The number to format.
 *  @returns {string} The formatted number as a string with two decimal places.
 */
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

/**
 * Translates a task status string into a human readable format.
 * @param status  - The status string to translate.
 * @returns {string} The translated status string.
 */
export const translateTaskStatus = (status: string) => {
    if (status === 'invalid') {
        return 'Invalid Docker Image';
    }
    return status.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };