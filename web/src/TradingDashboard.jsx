import React, { useState } from 'react';
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

    return (
        <div className={`flex h-screen n  ${getColor('background.primary')}`}>
            <main className={`flex-1 transition-all duration-300 ease-in-out transform`}>
                <div className="p-6">
                    <div className="flex justify-between items-center mb-8">
                        <h1 className={`text-2xl font-bold ${getColor('text.primary')}`}>
                            Trading Dashboard
                        </h1>
                        <ThemeToggle />
                    </div>
                    <div className="rounded-lg p-4 mb-6">
                        <ChartComponent />
                    </div>
                    <TradingOpportunities opportunities={opportunities} />
                </div>
            </main>
        </div>
    );
};

export default TradingDashboard;