import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { marketService } from '../services/api';
import { useTheme } from '../ThemeContext';

const Chart = ({ symbol, timeframe, priceScale }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);
    const { isDark } = useTheme();

    useEffect(() => {
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            layout: {
                background: { type: 'solid', color: isDark ? '#1C2127' : '#ffffff' },
                textColor: isDark ? '#9ca3af' : '#333333',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false }
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: true,
                borderColor: isDark ? '#2D3748' : '#e2e8f0',
            },
            rightPriceScale: {
                borderColor: isDark ? '#2D3748' : '#e2e8f0',
            }
        });

        chartRef.current = chart;  // Store chart instance

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceFormat: {
                type: 'custom',
                formatter: price => price.toFixed(priceScale)
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
                if (!data || data.length === 0) {
                    console.error('No data received');
                    return;
                }

                const candlestickData = data.map(item => ({
                    time: Math.floor(item.time),
                    open: parseFloat(item.open),
                    high: parseFloat(item.high),
                    low: parseFloat(item.low),
                    close: parseFloat(item.close),
                }));

                const volumeData = data.map(item => ({
                    time: Math.floor(item.time),
                    value: parseFloat(item.volume),
                    color: parseFloat(item.close) > parseFloat(item.open) ? '#26a69a' : '#ef5350',
                }));

                candlestickSeries.setData(candlestickData);
                volumeSeries.setData(volumeData);
                chart.timeScale().setVisibleLogicalRange({
                    from: candlestickData.length - 100,
                    to: candlestickData.length - 1
                });
            } catch (error) {
                console.error('Error fetching or processing data:', error);
            }
        };

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
            chartRef.current = null;
        };
    }, [symbol, timeframe, priceScale, isDark]);  // Add isDark to dependencies

    // Update chart theme when isDark changes
    useEffect(() => {
        if (chartRef.current) {
            chartRef.current.applyOptions({
                layout: {
                    background: { type: 'solid', color: isDark ? '#1C2127' : '#ffffff' },
                    textColor: isDark ? '#9ca3af' : '#333333',
                },
                timeScale: {
                    borderColor: isDark ? '#2D3748' : '#e2e8f0',
                },
                rightPriceScale: {
                    borderColor: isDark ? '#2D3748' : '#e2e8f0',
                }
            });
        }
    }, [isDark]);

    return (
        <div
            ref={chartContainerRef}
            className={`h-96 ${isDark ? 'bg-[#1C2127]' : 'bg-white'} rounded-lg shadow-sm`}
            style={{ minHeight: '400px' }}
        />
    );
};

const fetchSymbolData = async (symbol, timeframe) => {
    const data = await marketService.getKlineData(symbol, timeframe);
    return data;
};

export default Chart;