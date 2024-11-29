import React, { useState, useEffect, useCallback } from 'react';
import Chart from './Chart';
import Select from 'react-select';
import { marketService } from '../services/api';

const ChartComponent = ({ }) => {
    const [activeSymbolId, setActiveSymbolId] = useState(1);
    const [timeframe, setTimeframe] = useState('1d');
    const [symbolOptions, setSymbolOptions] = useState([]);
    const timeframes = ['5m', '15m', '1h', '4h', '1d'];
    const fetchSymbols = async () => {
        try {
            const symbols = await marketService.getSymbols();
            // Transform data immediately into the format we need
            const options = Object.entries(symbols).map(([id, data]) => ({
                value: id,
                label: data.symbol,
                priceScale: data.priceScale
            }));

            setSymbolOptions(options);

            // Set default active symbol if needed
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
        control: (provided) => ({
            ...provided,
            width: '250px',
            borderColor: '#e2e8f0',
            '&:hover': {
                borderColor: '#cbd5e1'
            }
        }),
        menu: (provided) => ({
            ...provided,
            zIndex: 9999
        }),
        option: (provided, state) => ({
            ...provided,
            backgroundColor: state.isSelected ? '#3b82f6' : state.isFocused ? '#f1f5f9' : 'white',
            color: state.isSelected ? 'white' : '#1f2937',
            '&:active': {
                backgroundColor: '#3b82f6'
            }
        })
    };

    const handleSymbolChange = (selectedOption) => {
        setActiveSymbolId(selectedOption.value);
    };
    const activeSymbol = symbolOptions.find(opt => opt.value === activeSymbolId);

    return (
        <div className="bg-white rounded-lg shadow-sm p-3 mb-2">
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
                <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
                    {timeframes.map((tf) => (
                        <button
                            key={tf}
                            onClick={() => setTimeframe(tf)}
                            className={`px-4 py-2 rounded-md transition-colors ${timeframe === tf
                                ? 'bg-white text-blue-600 shadow-sm'
                                : 'text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            {tf}
                        </button>
                    ))}
                </div>
            </div>
            <div className="bg-white rounded-lg shadow-sm p-2 mb-2">
                <Chart
                    symbol={activeSymbol?.label}
                    timeframe={timeframe}
                    priceScale={activeSymbol?.priceScale}
                />
            </div>
        </div >
    );
};

export default ChartComponent;