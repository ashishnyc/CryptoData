import React, { useState, useEffect } from 'react';
import { useThemeColors } from '../hooks/useThemeColors';
import { Filter } from 'lucide-react';
import Select from 'react-select';
import { marketService } from '../services/api';
import MarketDataTable from './Datatable';

const Markets = () => {
    const { getColor } = useThemeColors();
    const [filters, setFilters] = useState({
        symbol: '',
        minVolume: '',
        sortBy: null
    });
    const [symbolsInfo, setSymbolsInfo] = useState({});
    const [sortedSymbols, setSortedSymbols] = useState([]);
    const [sortConfig, setSortConfig] = useState({
        key: null,
        direction: 'desc'
    });

    useEffect(() => {
        const fetchSymbolsInfo = async () => {
            try {
                const data = await marketService.getSymbolsInfo();
                if (data && typeof data === 'object' && !Array.isArray(data)) {
                    setSymbolsInfo(data);
                    setSortedSymbols(Object.keys(data));
                } else if (Array.isArray(data)) {
                    const formattedData = data.reduce((acc, item) => {
                        acc[item.symbol] = item;
                        return acc;
                    }, {});
                    setSymbolsInfo(formattedData);
                    setSortedSymbols(Object.keys(formattedData));
                }
            } catch (error) {
                console.error('Error fetching symbols info:', error);
                setSymbolsInfo({});
                setSortedSymbols([]);
            }
        };

        fetchSymbolsInfo();
    }, []);

    // Formatting utilities
    const formatPrice = (price, priceScale) => {
        if (price === undefined || price === null || typeof price !== 'number') {
            return '0.00';
        }
        const scale = typeof priceScale === 'number' && priceScale >= 0 ? priceScale : 2;
        return `${price.toLocaleString(undefined, {
            minimumFractionDigits: scale,
            maximumFractionDigits: scale
        })}`;
    };


    const formatPercentage = (value) => {
        if (value === undefined || value === null || typeof value !== 'number') {
            return '0.00%';
        }
        const formatted = Number(value * 100).toFixed(2);
        return formatted > 0 ? `+${formatted}%` : `${formatted}%`;
    };
    const handleFilterChange = (e) => {
        setFilters(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    const getValueForSort = (symbolData, sortKey) => {
        if (!symbolData) return 0;
        switch (sortKey) {
            case 'symbol':
                return symbolData.symbol;
            case 'price':
                return symbolData.current_price || 0;
            case 'volume24h':
                return symbolData.turnover_1d || 0;
            case 'change1h':
                return symbolData.change_1h_pct || 0;
            case 'change4h':
                return symbolData.change_4h_pct || 0;
            case 'change1d':
                return symbolData.change_1d_pct || 0;
            case 'volume':
                return symbolData.turnover_1h || 0;
            default:
                return 0;
        }
    };

    const handleSort = (key) => {
        let direction = 'desc';
        if (sortConfig.key === key && sortConfig.direction === 'desc') {
            direction = 'asc';
        }
        setSortConfig({ key, direction });

        const sorted = [...sortedSymbols].sort((a, b) => {
            const aValue = getValueForSort(symbolsInfo[a], key);
            const bValue = getValueForSort(symbolsInfo[b], key);
            return direction === 'asc' ? aValue - bValue : bValue - aValue;
        });
        setSortedSymbols(sorted);
    };

    const handleSortChange = (selectedOption) => {
        setFilters(prev => ({
            ...prev,
            sortBy: selectedOption
        }));

        if (selectedOption) {
            handleSort(selectedOption.value);
        }
    };

    const applyFilters = () => {
        let filtered = Object.keys(symbolsInfo);

        if (filters.symbol) {
            filtered = filtered.filter(symbol =>
                symbol.toLowerCase().includes(filters.symbol.toLowerCase())
            );
        }

        if (filters.minVolume) {
            filtered = filtered.filter(symbol =>
                (symbolsInfo[symbol]?.turnover_1d || 0) >= Number(filters.minVolume)
            );
        }

        setSortedSymbols(filtered);
    };

    const sortOptions = [
        { value: 'volume24h', label: '24h Volume' },
        { value: 'change1h', label: '1h Change' },
        { value: 'change4h', label: '4h Change' },
        { value: 'change1d', label: '1d Change' }
    ];

    const selectStyles = {
        control: (base) => ({
            ...base,
            background: getColor('background.primary').split(' ')[1],
            borderColor: getColor('border.primary').split(' ')[1],
        }),
        menu: (base) => ({
            ...base,
            background: getColor('background.primary').split(' ')[1],
        }),
        option: (base, state) => ({
            ...base,
            backgroundColor: state.isFocused ?
                getColor('background.secondary').split(' ')[1] :
                getColor('background.primary').split(' ')[1],
            color: getColor('text.primary').split(' ')[1],
        }),
        singleValue: (base) => ({
            ...base,
            color: getColor('text.primary').split(' ')[1],
        }),
    };

    return (
        <div className={`p-6 h-full flex flex-col ${getColor('background.primary')}`}>
            {/* Filters Section */}
            <div className={`mb-6 p-4 rounded-lg ${getColor('background.secondary')}`}>
                <div className="flex flex-wrap gap-4 items-end">
                    <div className="flex-1 min-w-[200px]">
                        <label className={`block mb-2 text-sm ${getColor('text.secondary')}`}>
                            Symbol
                        </label>
                        <input
                            type="text"
                            name="symbol"
                            placeholder="Search by symbol..."
                            className={`w-full p-2 rounded-md border ${getColor('border.primary')} ${getColor('background.primary')} ${getColor('text.primary')}`}
                            value={filters.symbol}
                            onChange={handleFilterChange}
                        />
                    </div>

                    <div className="flex-1 min-w-[200px]">
                        <label className={`block mb-2 text-sm ${getColor('text.secondary')}`}>
                            Min 24h Volume
                        </label>
                        <input
                            type="number"
                            name="minVolume"
                            placeholder="Minimum volume..."
                            className={`w-full p-2 rounded-md border ${getColor('border.primary')} ${getColor('background.primary')} ${getColor('text.primary')}`}
                            value={filters.minVolume}
                            onChange={handleFilterChange}
                        />
                    </div>

                    <div className="flex-1 min-w-[200px]">
                        <label className={`block mb-2 text-sm ${getColor('text.secondary')}`}>
                            Sort By
                        </label>
                        <Select
                            options={sortOptions}
                            value={filters.sortBy}
                            onChange={handleSortChange}
                            placeholder="Select sort criteria..."
                            styles={selectStyles}
                        />
                    </div>

                    <button
                        onClick={applyFilters}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white`}
                    >
                        <Filter className="w-4 h-4" />
                        Apply Filters
                    </button>
                </div>
            </div>

            {/* Table Section */}
            <div className="flex-1 flex flex-col min-h-0">
                <div className="overflow-x-auto">
                    <MarketDataTable
                        symbols={sortedSymbols}
                        symbolsInfo={symbolsInfo}
                        sortConfig={sortConfig}
                        onSort={handleSort}
                        formatPrice={formatPrice}
                        formatPercentage={formatPercentage}
                        getColor={getColor}
                    />
                </div>
            </div>
        </div>
    );
};

export default Markets;