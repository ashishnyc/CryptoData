import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import { marketService } from '../services/api';

const Chart = ({ symbol, timeframe }) => {
    const chartContainerRef = useRef();

    useEffect(() => {
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
        });

        const candlestickSeries = chart.addCandlestickSeries();
        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
        });
        chart.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
            alignLabels: false,
        });

        const fetchData = async () => {
            try {
                const data = await fetchSymbolData(symbol, timeframe);
                const candlestickData = data.map(item => ({
                    time: new Date(item.time).getTime(),
                    open: item.open,
                    high: item.high,
                    low: item.low,
                    close: item.close,
                }));
                const volumeData = data.map(item => ({
                    time: new Date(item.time).getTime(),
                    value: item.volume,
                    color: item.close > item.open ? '#26a69a' : '#ef5350',
                }));
                candlestickSeries.setData(candlestickData);
                volumeSeries.setData(volumeData);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();

        return () => {
            chart.remove();
        };
    }, [symbol, timeframe]);

    return <div ref={chartContainerRef} className="h-96 bg-gray-50 rounded-lg" />;
};

// Mock function to simulate fetching Kline data for a symbol and timeframe
const fetchSymbolData = async (symbol, timeframe) => {
    // Replace this with your actual data fetching logic
    const data = await marketService.getKlineData(symbol, timeframe);
    return data;
};

export default Chart;