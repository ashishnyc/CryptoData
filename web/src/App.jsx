import React from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import TradingDashboard from './TradingDashboard';
import { useThemeColors } from './hooks/useThemeColors';

const AppContent = () => {
  const { getColor } = useThemeColors();

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