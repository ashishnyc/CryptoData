import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { useThemeColors } from '../hooks/useThemeColors';
import Chart from './Chart';
import { marketService } from '../services/api';
import { formatPrice, formatPercentage, formatVolume } from '../utils/formatters';

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
                const data = await marketService.getSymbolsInfo(currentSymbol);
                const symbolInfo = data[currentSymbol];
                if (symbolInfo) {
                    setSymbolData(symbolInfo);
                }
            } catch (error) {
                console.error('Error fetching symbol data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchSymbolData();
    }, [currentSymbol]);

    useEffect(() => {
        if (!symbolId) {
            navigate(`/symbol/${DEFAULT_SYMBOL}`, { replace: true });
        }
    }, [symbolId, navigate]);

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
                    </div>

                    {/* Price Information */}
                    {symbolData && (
                        <div className={`flex items-center space-x-6 ${getColor('text.primary')}`}>
                            <div>
                                <span className="text-2xl font-bold">
                                    ${formatPrice(symbolData.current_price, symbolData.priceScale)}
                                </span>
                                <span className={`ml-2 ${(symbolData?.priceChange || 0) >= 0
                                    ? 'text-green-500'
                                    : 'text-red-500'
                                    }`}>
                                    {formatPercentage(symbolData.change_1d_pct)}
                                </span>
                            </div>
                            <div className="grid grid-cols-3 gap-6">
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h High</div>
                                    <div>${formatPrice(symbolData.max_price_24h, symbolData.priceScale)}</div>
                                </div>
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h Low</div>
                                    <div>${formatPrice(symbolData.min_price_24h, symbolData.priceScale)}</div>
                                </div>
                                <div>
                                    <div className={`text-sm ${getColor('text.secondary')}`}>24h Volume</div>
                                    <div>{formatVolume(symbolData.turnover_1d)}</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Chart Container */}
            {!loading && symbolData && (
                <Chart
                    key={`${currentSymbol}-${symbolData.priceScale}`}
                    symbol={currentSymbol}
                    timeframe="1d"
                    priceScale={symbolData.priceScale || 2}
                />
            )}
        </div>
    );
};

export default Symbol;
