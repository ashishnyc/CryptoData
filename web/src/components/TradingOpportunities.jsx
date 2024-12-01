import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useThemeColors } from '../hooks/useThemeColors';

const TradingOpportunities = ({ opportunities }) => {
    const { getColor } = useThemeColors();
    const { isDark } = useTheme();

    return (
        <div className={`${getColor('background.secondary')} rounded-lg shadow-sm p-6 mb-6`}>
            <h2 className={`text-2xl font-semibold ${isDark ? 'text-white' : 'text-gray-800'} mb-4`}>
                Trading Opportunities
            </h2>
            <div className="space-y-3">
                {opportunities.map((opp) => (
                    <div
                        key={opp.symbol}
                        className={`${getColor('text.primary')}'} 
                            border rounded-lg p-4 transition-colors`}
                    >
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                {opp.type === 'LONG' ? (
                                    <div className={`w-6 h-6 rounded-full ${isDark ? 'bg-green-500/20' : 'bg-green-50'} 
                                        flex items-center justify-center`}>
                                        <span className="text-green-500">↑</span>
                                    </div>
                                ) : (
                                    <div className={`w-6 h-6 rounded-full ${isDark ? 'bg-red-500/20' : 'bg-red-50'} 
                                        flex items-center justify-center`}>
                                        <span className="text-red-500">↓</span>
                                    </div>
                                )}
                                <span className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                    {opp.symbol}
                                </span>
                                <span className={`px-2 py-0.5 text-xs font-medium rounded ${opp.type === 'LONG'
                                    ? isDark ? 'bg-green-500/20 text-green-500' : 'bg-green-50 text-green-600'
                                    : isDark ? 'bg-red-500/20 text-red-500' : 'bg-red-50 text-red-600'
                                    }`}>
                                    {opp.type}
                                </span>
                            </div>
                            <div className="flex items-center gap-6 text-sm">
                                <div>
                                    <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>Entry: </span>
                                    <span className={`font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                        {opp.entry}
                                    </span>
                                </div>
                                <div>
                                    <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>Target: </span>
                                    <span className="font-medium text-green-500">
                                        {opp.target}
                                    </span>
                                </div>
                                <div>
                                    <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>Stop: </span>
                                    <span className="font-medium text-red-500">
                                        {opp.stop}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TradingOpportunities;