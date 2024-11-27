import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { marketService } from '../services/api';

const Chart = ({ symbol, timeframe }) => {
    const chartContainerRef = useRef();

    useEffect(() => {
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            layout: {
                background: { color: '#fafafa' },
                textColor: '#333',
            },
            grid: {
                vertLines: { color: '#f0f0f0' },
                horzLines: { color: '#f0f0f0' },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                tickMarkFormatter: (time) => {
                    const date = new Date(time * 1000);
                    // Basic formatting based on timeframe
                    switch (timeframe) {
                        case '1m':
                        case '5m':
                        case '15m':
                        case '30m':
                            return date.toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit'
                            });
                        case '1h':
                        case '4h':
                            return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
                        case '1d':
                            return date.toLocaleDateString([], {
                                month: 'short',
                                day: 'numeric'
                            });
                        default:
                            return date.toLocaleDateString();
                    }
                },
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceFormat: {
                type: 'custom',
                formatter: price => {
                    // Check if the price has more than 2 decimal places
                    const decimalPlaces = (price.toString().split('.')[1] || '').length;
                    if (decimalPlaces > 2) {
                        // For small numbers (e.g., 0.00012345), show up to 8 decimal places
                        if (Math.abs(price) < 0.01) {
                            return price.toFixed(8);
                        }
                        // For medium numbers (e.g., 0.12345), show up to 6 decimal places
                        else if (Math.abs(price) < 1) {
                            return price.toFixed(6);
                        }
                        // For larger numbers, show up to 4 decimal places
                        else {
                            return price.toFixed(4);
                        }
                    }
                    // For regular numbers, show 2 decimal places
                    return price.toFixed(2);
                },
            },
        });

        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: 'volume',
        });

        chart.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });

        const fetchData = async () => {
            try {
                const data = await fetchSymbolData(symbol, timeframe);
                console.log('Fetched data:', data); // Debug log

                if (!data || data.length === 0) {
                    console.error('No data received');
                    return;
                }

                const candlestickData = data.map(item => ({
                    time: Math.floor(item.time), // Ensure we have integer timestamps
                    open: parseFloat(item.open),
                    high: parseFloat(item.high),
                    low: parseFloat(item.low),
                    close: parseFloat(item.close),
                }));

                const volumeData = data.map(item => ({
                    time: Math.floor(item.time), // Ensure we have integer timestamps
                    value: parseFloat(item.volume),
                    color: parseFloat(item.close) > parseFloat(item.open) ? '#26a69a' : '#ef5350',
                }));

                console.log('Processed candlestick data:', candlestickData[0]); // Debug log
                candlestickSeries.setData(candlestickData);
                volumeSeries.setData(volumeData);

                // Fit content after setting data
                chart.timeScale().fitContent();
            } catch (error) {
                console.error('Error fetching or processing data:', error);
            }
        };

        // Handle window resize
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        window.addEventListener('resize', handleResize);
        fetchData();

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [symbol, timeframe]);

    return (
        <div
            ref={chartContainerRef}
            className="h-96 bg-gray-50 rounded-lg shadow-sm"
            style={{ minHeight: '400px' }}
        />
    );
};
const fetchSymbolData = async (symbol, timeframe) => {
    const data = await marketService.getKlineData(symbol, timeframe);
    return data;
};

export default Chart;