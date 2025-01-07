import React, { useEffect, useState } from 'react';
import apiClient from '../services/apiClient';

const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    apiClient.get('/tasks')
      .then(response => setTasks(response.data))
      .catch(error => console.error('Error fetching tasks:', error));
  }, []);

  return (
    <div>
      <h2>Tasks</h2>
      <ul>
        {tasks.map((task: any) => (
          <li key={task.id}>{task.description} - {task.status}</li>
        ))}
      </ul>
    </div>
  );
};

export default Tasks;
