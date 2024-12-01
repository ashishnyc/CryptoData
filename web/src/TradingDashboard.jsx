import React from 'react';
import { DollarSign } from 'lucide-react';
import ChartComponent from './components/ChartComponent';
import ThemeToggle from './components/ThemeToggle';
import TradingOpportunities from './components/TradingOpportunities';
import { useThemeColors } from './hooks/useThemeColors';

const TradingDashboard = () => {
    const { getColor } = useThemeColors();

    const opportunities = [
        { id: 1, symbol: 'BTCUSDT', type: 'LONG', entry: 42000, target: 43000, stop: 41500 },
        { id: 2, symbol: 'ETHUSDT', type: 'SHORT', entry: 2800, target: 2700, stop: 2850 }
    ];

    const trades = [
        { id: 1, symbol: 'BTCUSDT', type: 'LONG', entry: 42000, exit: 43000, pnl: '+2.38%' },
        { id: 2, symbol: 'ETHUSDT', type: 'SHORT', entry: 2800, exit: 2750, pnl: '+1.79%' }
    ];

    return (
        <div className={`min-h-screen ${getColor('background.primary')}`}>
            <div className="p-6">
                <div className="flex justify-between items-center mb-8">
                    <h1 className={`text-4xl font-bold ${getColor('text.primary')}`}>
                        Trading Dashboard
                    </h1>
                    <ThemeToggle />
                </div>

                <ChartComponent />

                <TradingOpportunities opportunities={opportunities} />

                {/* Recent Trades Section */}
                <div className={`rounded-lg shadow-sm p-6 mb-6`}>
                    <h2 className={`text-2xl font-semibold ${getColor('text.secondary')} mb-4`}>
                        Recent Trades
                    </h2>
                    <div className="space-y-4">
                        {trades.map((trade) => (
                            <div
                                key={trade.id}
                                className={`border ${getColor('border.primary')} ${getColor('hover.background')} 
                                    rounded-lg p-4 transition-colors`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <DollarSign className="text-blue-500 w-6 h-6" />
                                        <span className={`font-semibold ${getColor('text.primary')}`}>
                                            {trade.symbol}
                                        </span>
                                        <span className={`px-2 py-1 rounded-full text-sm ${trade.type === 'LONG'
                                            ? 'bg-green-500/20 text-green-500'
                                            : 'bg-red-500/20 text-red-500'
                                            }`}>
                                            {trade.type}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-6 text-sm">
                                        <span className={getColor('text.tertiary')}>
                                            Entry: {trade.entry}
                                        </span>
                                        <span className={getColor('text.tertiary')}>
                                            Exit: {trade.exit}
                                        </span>
                                        <span className={`font-semibold ${trade.pnl.startsWith('+')
                                            ? 'text-green-500'
                                            : 'text-red-500'
                                            }`}>
                                            {trade.pnl}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TradingDashboard;