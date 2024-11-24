import React, { useState, useEffect } from 'react';
import { ArrowUpCircle, ArrowDownCircle, DollarSign, RefreshCw } from 'lucide-react';
import { marketService } from './services/api';
import ChartComponent from './components/ChartComponent';
import Symbols from './components/SymbolsComponent';

const TradingDashboard = () => {
  const [activeSymbol, setActiveSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [symbols, setSymbols] = useState([]);

  const timeframes = ['5m', '15m', '1h', '4h', '1d'];
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const fetchedSymbols = await marketService.getSymbols();
        setSymbols(Array.isArray(fetchedSymbols) ? fetchedSymbols : []);
      } catch (error) {
        console.error('Error fetching symbols:', error);
      }
    };
    fetchSymbols();
  }, []);

  const opportunities = [
    { id: 1, symbol: 'BTCUSDT', type: 'LONG', entry: 42000, target: 43000, stop: 41500 },
    { id: 2, symbol: 'ETHUSDT', type: 'SHORT', entry: 2800, target: 2700, stop: 2850 }
  ];

  const trades = [
    { id: 1, symbol: 'BTCUSDT', type: 'LONG', entry: 42000, exit: 43000, pnl: '+2.38%' },
    { id: 2, symbol: 'ETHUSDT', type: 'SHORT', entry: 2800, exit: 2750, pnl: '+1.79%' }
  ];

  return (
    <div className="bg-gray-50 p-6 content-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-8">Trading Dashboard</h1>

      {/* Chart Section */}

      <ChartComponent
        activeSymbol={activeSymbol}
        timeframes={timeframes}
        timeframe={timeframe}
        setTimeframe={setTimeframe}
      />

      {/* Opportunities Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Trading Opportunities</h2>
        <div className="space-y-4">
          {opportunities.map((opp) => (
            <div key={opp.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {opp.type === 'LONG' ? (
                    <ArrowUpCircle className="text-green-500 w-6 h-6" />
                  ) : (
                    <ArrowDownCircle className="text-red-500 w-6 h-6" />
                  )}
                  <span className="font-semibold text-gray-900">{opp.symbol}</span>
                  <span className={`px-2 py-1 rounded-full text-sm ${opp.type === 'LONG' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                    {opp.type}
                  </span>
                </div>
                <div className="flex gap-6 text-sm">
                  <span className="text-gray-600">Entry: {opp.entry}</span>
                  <span className="text-green-600">Target: {opp.target}</span>
                  <span className="text-red-600">Stop: {opp.stop}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trades Section */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Recent Trades</h2>
        <div className="space-y-4">
          {trades.map((trade) => (
            <div key={trade.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <DollarSign className="text-blue-500 w-6 h-6" />
                  <span className="font-semibold text-gray-900">{trade.symbol}</span>
                  <span className={`px-2 py-1 rounded-full text-sm ${trade.type === 'LONG' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                    {trade.type}
                  </span>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <span className="text-gray-600">Entry: {trade.entry}</span>
                  <span className="text-gray-600">Exit: {trade.exit}</span>
                  <span className={`font-semibold ${trade.pnl.startsWith('+') ? 'text-green-600' : 'text-red-600'
                    }`}>
                    {trade.pnl}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Symbols Section */}
      <Symbols
        symbols={symbols}
        activeSymbol={activeSymbol}
        setActiveSymbol={setActiveSymbol}
      />
    </div>
  );
};

export default TradingDashboard;