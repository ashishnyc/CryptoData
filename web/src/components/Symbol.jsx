import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useThemeColors } from '../hooks/useThemeColors';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import Chart from './Chart';

const DEFAULT_SYMBOL = 'BTCUSDT';

const Symbol = () => {
    const { symbolId } = useParams();
    const navigate = useNavigate();
    const { getColor } = useThemeColors();
    const { isDark } = useTheme();
    const [currentSymbol, setCurrentSymbol] = useState(symbolId || DEFAULT_SYMBOL);
    const [symbolData, setSymbolData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSymbolData = async () => {
            setLoading(true);
            try {
                // Replace this with your actual API call
                const response = await fetch(`/api/symbols/${currentSymbol}`);
                const data = await response.json();
                setSymbolData(data);
            } catch (error) {
                console.error('Error fetching symbol data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchSymbolData();
    }, [currentSymbol]);

    useEffect(() => {
        if (symbolId && symbolId !== currentSymbol) {
            setCurrentSymbol(symbolId);
        }
    }, [symbolId]);

    const handleSymbolChange = (newSymbol) => {
        navigate(`/symbol/${newSymbol}`);
        setCurrentSymbol(newSymbol);
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className={`${getColor('background.primary')} border-b ${getColor('border.primary')} p-4`}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h1 className={`text-2xl font-semibold ${getColor('text.primary')}`}>
                            {currentSymbol}
                        </h1>
                        <div className="flex items-center space-x-2">
                            <button
                                className={`p-2 rounded-full ${getColor('hover.background')}`}
                                onClick={() => handleSymbolChange('BTCUSDT')}
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <button
                                className={`p-2 rounded-full ${getColor('hover.background')}`}
                                onClick={() => handleSymbolChange('ETHUSDT')}
                            >
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Price Information */}
                    {symbolData && (
                        <div className={`flex items-center space-x-6 ${getColor('text.primary')}`}>
                            <div>
                                <span className="text-2xl font-bold">
                                    ${symbolData?.price || '0.00'}
                                </span>
                                <span className={`ml-2 ${(symbolData?.priceChange || 0) >= 0
                                    ? 'text-green-500'
                                    : 'text-red-500'
                                    }`}>
                                    {(symbolData?.priceChange || 0) >= 0 ? '+' : ''}
                                    {symbolData?.priceChangePercent || '0.00'}%
                                </span>
                            </div>
                            <div className="grid grid-cols-3 gap-6">
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h High</div>
                                    <div>${symbolData?.highPrice || '0.00'}</div>
                                </div>
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h Low</div>
                                    <div>${symbolData?.lowPrice || '0.00'}</div>
                                </div>
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h Volume</div>
                                    <div>{symbolData?.volume || '0.00'}</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Chart Container */}
            <Chart
                symbol={currentSymbol}
                timeframe={"1d"}
                priceScale={2}
            />
        </div>
    );
};

export default Symbol;