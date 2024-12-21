import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import TradingDashboard from './TradingDashboard';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Markets from './components/Markets';
import Symbol from './components/Symbol';

const Backtest = () => <div>Backtest Page</div>;
const Files = () => <div>Files Page</div>;
const Profile = () => <div>Profile Page</div>;

const AppContent = () => {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<TradingDashboard />} />
            <Route path="/markets" element={<Markets />} />
            <Route path="/symbol" element={<Symbol />} />
            <Route path="/symbol/:symbolId" element={<Symbol />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/live" element={<Files />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
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