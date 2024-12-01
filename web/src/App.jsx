import React from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import TradingDashboard from './TradingDashboard';

const AppContent = () => {
  return (
    <div className={`min-h-screen`}>
      <TradingDashboard />
    </div>
  );
};

const App = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
};

export default App;