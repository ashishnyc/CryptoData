import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import TradingDashboard from './TradingDashboard';
import Sidebar from './components/Sidebar';
import Markets from './components/Markets';

// Import or create other page components
const Backtest = () => <div>Backtest Page</div>;
const Files = () => <div>Files Page</div>;
const Profile = () => <div>Profile Page</div>;

const AppContent = () => {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<TradingDashboard />} />
          <Route path="/markets" element={<Markets />} />
          <Route path="/backtest" element={<Backtest />} />
          <Route path="/files" element={<Files />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AppContent />
      </ThemeProvider>
    </BrowserRouter>
  );
};

export default App;