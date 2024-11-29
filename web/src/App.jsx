// App.jsx
import React from 'react';
import { ThemeProvider } from './ThemeContext';
import TradingDashboard from './TradingDashboard';

function App() {
  return (
    <ThemeProvider>
      <TradingDashboard />
    </ThemeProvider>
  );
}

export default App;