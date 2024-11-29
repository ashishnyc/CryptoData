import React, { useState, useEffect, useCallback } from 'react';
import Chart from './Chart';
import Select from 'react-select';
import { marketService } from '../services/api';

const ChartComponent = ({ }) => {
    const [activeSymbol, setActiveSymbol] = useState('BTCUSDT');
    const [timeframe, setTimeframe] = useState('1d');
    const [symbols, setSymbols] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const timeframes = ['5m', '15m', '1h', '4h', '1d'];
    const fetchSymbols = useCallback(async () => {
        try {
            const fetchedSymbols = await marketService.getSymbols();

            // Validate and transform the fetched symbols
            const validSymbols = Array.isArray(fetchedSymbols)
                ? fetchedSymbols
                    .filter(symbol => symbol && typeof symbol === 'string')
                    .map(symbol => ({
                        value: symbol,
                        label: symbol
                    }))
                : [];

            setSymbols(validSymbols);

            // If we don't have the active symbol in our new list, reset to first available
            if (validSymbols.length > 0 && !validSymbols.find(s => s.value === activeSymbol)) {
                setActiveSymbol(validSymbols[0].value);
            }
        } catch (error) {
            console.error('Error fetching symbols:', error);
        }
    }, [activeSymbol]);
    // Initial fetch
    useEffect(() => {
        const initializeData = async () => {
            setIsLoading(true);
            await fetchSymbols();
            setIsLoading(false);
        };

        initializeData();
    }, [fetchSymbols]);


    const customStyles = {
        control: (provided) => ({
            ...provided,
            width: '200px',
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
        setActiveSymbol(selectedOption.value);
    };
    const handleRefresh = async () => {
        setIsRefreshing(true);
        try {
            // Add your refresh logic here
            await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate refresh
        } finally {
            setIsRefreshing(false);
        }
    };
    return (
        <div className="bg-white rounded-lg shadow-sm p-3 mb-2">
            <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                    <Select
                        options={symbols}
                        value={symbols.find(symbol => symbol.value === activeSymbol)}
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
                <Chart symbol={activeSymbol} timeframe={timeframe} />
            </div>
        </div >
    );
};

export default ChartComponent;