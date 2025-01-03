import React, { useEffect, useState } from 'react';
import apiClient from '../services/apiClient';

const Nodes: React.FC = () => {
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    apiClient.get('/nodes/list')
      .then(response => setNodes(response.data))
      .catch(error => console.error('Error fetching nodes:', error));
  }, []);

  return (
    <div>
      <h2>Nodes</h2>
      <ul>
        {nodes.map((node: any) => (
          <li key={node.id}>{node.name} - {node.status}</li>
        ))}
      </ul>
    </div>
  );
};

export default Nodes;
