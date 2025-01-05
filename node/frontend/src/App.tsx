import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Nodes from './pages/Nodes';
import Tasks from './pages/Tasks';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/login" element={<Login />} />
      <Route path="/nodes" element={<Nodes />} />
      <Route path="/tasks" element={<Tasks />} />
    </Routes>
  );
};

export default App;
