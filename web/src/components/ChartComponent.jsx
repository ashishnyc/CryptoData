import React, { useState, useEffect } from 'react';
import Chart from './Chart';
import Select from 'react-select';
import { marketService } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';

const ChartComponent = () => {
    const { isDark } = useTheme();
    const [activeSymbolId, setActiveSymbolId] = useState(1);
    const [timeframe, setTimeframe] = useState('1d');
    const [symbolOptions, setSymbolOptions] = useState([]);

    // Convert timeframes to React Select options format
    const timeframeOptions = [
        { value: '5m', label: '5m' },
        { value: '15m', label: '15m' },
        { value: '1h', label: '1h' },
        { value: '4h', label: '4h' },
        { value: '1d', label: '1d' }
    ];

    const fetchSymbols = async () => {
        try {
            const symbols = await marketService.getSymbols();
            const options = Object.entries(symbols).map(([id, data]) => ({
                value: id,
                label: data.symbol,
                priceScale: data.priceScale
            }));

            setSymbolOptions(options);

            if (options.length && !options.find(opt => opt.value === activeSymbolId)) {
                setActiveSymbolId(options[0].value);
            }
        } catch (error) {
            console.error('Error fetching symbols:', error);
        }
    };

    useEffect(() => {
        fetchSymbols();
    }, []);

    const customStyles = {
        control: (base) => ({
            ...base,
            width: '300px',
            backgroundColor: isDark ? '#1C2127' : 'white',
            borderColor: isDark ? '#2D3748' : '#e2e8f0',
            '&:hover': {
                borderColor: isDark ? '#4A5568' : '#cbd5e1'
            }
        }),
        menu: (base) => ({
            ...base,
            backgroundColor: isDark ? '#1C2127' : 'white',
            zIndex: 9999
        }),
        option: (base, state) => ({
            ...base,
            backgroundColor: isDark
                ? state.isSelected
                    ? '#2D3748'
                    : state.isFocused
                        ? '#2D3748'
                        : '#1C2127'
                : state.isSelected
                    ? '#3b82f6'
                    : state.isFocused
                        ? '#f1f5f9'
                        : 'white',
            color: isDark ? '#d1d5db' : state.isSelected ? 'white' : '#1f2937',
            '&:active': {
                backgroundColor: isDark ? '#2D3748' : '#3b82f6'
            }
        }),
        singleValue: (base) => ({
            ...base,
            color: isDark ? '#d1d5db' : '#1f2937'
        }),
        input: (base) => ({
            ...base,
            color: isDark ? '#d1d5db' : '#1f2937'
        }),
        placeholder: (base) => ({
            ...base,
            color: isDark ? '#6B7280' : '#9CA3AF'
        })
    };

    const timeframeStyles = {
        ...customStyles,
        control: (base) => ({
            ...base,
            width: '100px',  // Smaller width for timeframe dropdown
            backgroundColor: isDark ? '#1C2127' : 'white',
            borderColor: isDark ? '#2D3748' : '#e2e8f0',
            '&:hover': {
                borderColor: isDark ? '#4A5568' : '#cbd5e1'
            }
        })
    };

    const handleSymbolChange = (selectedOption) => {
        setActiveSymbolId(selectedOption.value);
    };

    const handleTimeframeChange = (selectedOption) => {
        setTimeframe(selectedOption.value);
    };

    const activeSymbol = symbolOptions.find(opt => opt.value === activeSymbolId);
    const activeTimeframe = timeframeOptions.find(opt => opt.value === timeframe);

    return (
        <div className={`${isDark ? 'bg-[#1C2127]' : 'bg-white'} rounded-lg shadow-sm p-3 mb-2`}>
            <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                    <Select
                        options={symbolOptions}
                        value={activeSymbol}
                        onChange={handleSymbolChange}
                        isSearchable={true}
                        placeholder="Search symbol..."
                        styles={customStyles}
                    />
                </div>
                <div>
                    <Select
                        options={timeframeOptions}
                        value={activeTimeframe}
                        onChange={handleTimeframeChange}
                        isSearchable={false}
                        styles={timeframeStyles}
                    />
                </div>
            </div>
            <div className={`${isDark ? 'bg-[#1C2127]' : 'bg-white'} rounded-lg`}>
                <Chart
                    symbol={activeSymbol?.label}
                    timeframe={timeframe}
                    priceScale={activeSymbol?.priceScale}
                />
            </div>
        </div>
    );
};

export default ChartComponent;