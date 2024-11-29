import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { marketService } from '../services/api';

const Chart = ({ symbol, timeframe, priceScale }) => {
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
                secondsVisible: true,
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