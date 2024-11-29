import React, { useState, useEffect, useCallback } from 'react';
import Chart from './Chart';
import Select from 'react-select';
import { marketService } from '../services/api';

const ChartComponent = ({ }) => {
    const [activeSymbolId, setActiveSymbolId] = useState(1);
    const [timeframe, setTimeframe] = useState('1d');
    const [symbolsMap, setSymbolsMap] = useState({});
    const timeframes = ['5m', '15m', '1h', '4h', '1d'];
    const fetchSymbols = async () => {
        try {
            const symbols = await marketService.getSymbols();
            setSymbolsMap(symbols);

            const symbolIds = Object.keys(symbols);
            if (symbolIds.length && !symbols[activeSymbolId]) {
                setActiveSymbolId(symbolIds[0]);
            }
        } catch (error) {
            console.error('Error fetching symbols:', error);
        }
    };
    useEffect(() => {
        fetchSymbols();
    }, []);
    const selectOptions = Object.entries(symbolsMap).map(([id, data]) => ({
        value: id,
        label: data.symbol
    }));

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
        setActiveSymbolId(selectedOption.value);
    };

    return (
        <div className="bg-white rounded-lg shadow-sm p-3 mb-2">
            <div className="flex justify-between items-center mb-2">
                <div className="flex items-center gap-2">
                    <Select
                        options={selectOptions}
                        value={selectOptions.find(option => option.value === activeSymbolId)}
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
                <Chart symbol={symbolsMap[activeSymbolId]?.symbol} timeframe={timeframe} priceScale={symbolsMap[activeSymbolId]?.priceScale} />
            </div>
        </div >
    );
};

export default ChartComponent;