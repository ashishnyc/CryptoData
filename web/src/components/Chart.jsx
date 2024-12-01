import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { marketService } from '../services/api';
import { useThemeColors } from '../hooks/useThemeColors';
import { chartTheme } from '../theme/chartTheme';

const Chart = ({ symbol, timeframe, priceScale }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);
    const candlestickSeriesRef = useRef(null);
    const volumeSeriesRef = useRef(null);
    const isMounted = useRef(true);
    const { getColor } = useThemeColors();

    // Initialize chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Set mounted flag
        isMounted.current = true;

        // Create chart instance
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            ...chartTheme.getChartOptions(getColor),
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false }
            }
        });

        chartRef.current = chart;

        // Create series
        candlestickSeriesRef.current = chart.addCandlestickSeries({
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

        volumeSeriesRef.current = chart.addHistogramSeries({
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

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        // Cleanup function
        return () => {
            isMounted.current = false;
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
                candlestickSeriesRef.current = null;
                volumeSeriesRef.current = null;
            }
        };
    }, [getColor, priceScale]); // Only recreate chart when these change

    // Fetch and update data
    useEffect(() => {
        const fetchAndUpdateData = async () => {
            if (!chartRef.current || !isMounted.current) return;

            try {
                const data = await fetchSymbolData(symbol, timeframe);

                if (!data || data.length === 0 || !isMounted.current) {
                    console.warn('No data received or component unmounted');
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
                    color: parseFloat(item.close) > parseFloat(item.open)
                        ? '#26a69a'
                        : '#ef5350',
                }));

                if (candlestickSeriesRef.current && volumeSeriesRef.current && isMounted.current) {
                    candlestickSeriesRef.current.setData(candlestickData);
                    volumeSeriesRef.current.setData(volumeData);

                    // Set visible range to last 100 candles
                    chartRef.current.timeScale().setVisibleLogicalRange({
                        from: candlestickData.length - 100,
                        to: candlestickData.length - 1
                    });
                }
            } catch (error) {
                console.error('Error fetching or processing data:', error);
            }
        };

        fetchAndUpdateData();
    }, [symbol, timeframe]);

    // Update chart theme
    useEffect(() => {
        if (chartRef.current) {
            chartRef.current.applyOptions(chartTheme.getChartOptions(getColor));
        }
    }, [getColor]);

    return (
        <div
            ref={chartContainerRef}
            className={`h-96 ${getColor('background.primary')}`}
            style={{ minHeight: '400px' }}
        />
    );
};

const fetchSymbolData = async (symbol, timeframe) => {
    const data = await marketService.getKlineData(symbol, timeframe);
    return data;
};

export default Chart;