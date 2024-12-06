import React, { useState, useEffect } from 'react';
import { useThemeColors } from '../hooks/useThemeColors';
import { ArrowUpDown, ChevronDown, Filter } from 'lucide-react';
import Select from 'react-select';
import { marketService } from '../services/api';

const Markets = () => {
    const { getColor } = useThemeColors();
    const [filters, setFilters] = useState({
        symbol: '',
        minVolume: '',
        sortBy: null
    });
    const [symbolsInfo, setSymbolsInfo] = useState({});
    const [sortedSymbols, setSortedSymbols] = useState([]);

    useEffect(() => {
        const fetchSymbolsInfo = async () => {
            const data = await marketService.getSymbolsInfo();
            setSymbolsInfo(data);
            setSortedSymbols(Object.keys(data));
        };

        fetchSymbolsInfo();
    }, []);

    // Format percentage with fixed decimals and + sign for positive values
    const formatPercentage = (value) => {
        const formatted = Number(value).toFixed(2);
        return formatted > 0 ? `+${formatted}%` : `${formatted}%`;
    };

    const handleFilterChange = (e) => {
        setFilters({
            ...filters,
            [e.target.name]: e.target.value
        });
    };

    const handleSortChange = (selectedOption) => {
        setFilters({
            ...filters,
            sortBy: selectedOption
        });

        if (selectedOption) {
            const sorted = [...sortedSymbols].sort((a, b) => {
                const aValue = getValueForSort(symbolsInfo[a], selectedOption.value);
                const bValue = getValueForSort(symbolsInfo[b], selectedOption.value);
                return bValue - aValue; // Descending order
            });
            setSortedSymbols(sorted);
        }
    };

    const getValueForSort = (symbolData, sortKey) => {
        switch (sortKey) {
            case 'volume24h':
                return symbolData.turnover_1d;
            case 'change1h':
                return symbolData.change_1h_pct;
            case 'change4h':
                return symbolData.change_4h_pct;
            case 'change1d':
                return symbolData.change_1d_pct;
            default:
                return 0;
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
                symbolsInfo[symbol].turnover_1d >= Number(filters.minVolume)
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

    // Custom styles for react-select to match theme
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
        <div className={`p-6 ${getColor('background.primary')}`}>
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
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className={`border-b ${getColor('border.primary')}`}>
                            <th className={`py-3 text-left ${getColor('text.primary')}`}>Symbol</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>Current Price</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>24h Volume</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>1h Change</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>4h Change</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>1d Change</th>
                            <th className={`py-3 text-right ${getColor('text.primary')}`}>Volume (1h/4h/1d)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedSymbols.map((symbol) => (
                            <tr
                                key={symbol}
                                className={`border-b ${getColor('border.primary')} hover:${getColor('background.secondary')}`}
                            >
                                <td className={`py-3 ${getColor('text.primary')}`}>{symbol}</td>
                                <td className={`text-right ${getColor('text.primary')}`}>
                                    ${symbolsInfo[symbol].current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </td>
                                <td className={`text-right ${getColor('text.primary')}`}>
                                    ${symbolsInfo[symbol].turnover_1d.toLocaleString()}
                                </td>
                                <td className={`text-right ${symbolsInfo[symbol].change_1h_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(symbolsInfo[symbol].change_1h_pct * 100)}
                                </td>
                                <td className={`text-right ${symbolsInfo[symbol].change_4h_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(symbolsInfo[symbol].change_4h_pct * 100)}
                                </td>
                                <td className={`text-right ${symbolsInfo[symbol].change_1d_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(symbolsInfo[symbol].change_1d_pct * 100)}
                                </td>
                                <td className={`text-right ${getColor('text.primary')}`}>
                                    ${symbolsInfo[symbol].turnover_5m.toLocaleString()} /
                                    ${symbolsInfo[symbol].turnover_15m.toLocaleString()} /
                                    ${symbolsInfo[symbol].turnover_1h.toLocaleString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Markets;