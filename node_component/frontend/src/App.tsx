import React from 'react';
import { Routes, Route } from 'react-router-dom';
// import Login from './pages/Login';
import Node from './pages/Node';
// import Nodes from './pages/Nodes';
// import Tasks from './pages/Tasks';
import SubmitTask from './components/SubmitTask';
import SubmittedTasks from './pages/SubmittedTasks';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Node />} />
      {/* <Route path="/login" element={<Login />} /> */}
      <Route path="/node" element={<Node />} />
      {/* <Route path="/nodes" element={<Nodes />} /> */}
      <Route path="/submitted-tasks" element={<SubmittedTasks />} />
      <Route path="/submit-task" element={<SubmitTask />} />
      
    </Routes>
  );
};

export default App;
