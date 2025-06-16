import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Node from './pages/Node';
import SubmitTask from './components/SubmitTask';
import SubmittedTasks from './pages/SubmittedTasks';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Node />} />
      <Route path="/node" element={<Node />} />
      <Route path="/submitted-tasks" element={<SubmittedTasks />} />
      <Route path="/submit-task" element={<SubmitTask />} />
    </Routes>
  );
};

export default App;
