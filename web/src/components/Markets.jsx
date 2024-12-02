import React, { useState } from 'react';
import { useThemeColors } from '../hooks/useThemeColors';
import { ArrowUpDown, ChevronDown, Filter } from 'lucide-react';
import Select from 'react-select';

const Markets = () => {
    const { getColor } = useThemeColors();
    const [filters, setFilters] = useState({
        symbol: '',
        minVolume: '',
        sortBy: null
    });

    // Sample data - replace with your actual data
    const marketData = [
        {
            symbol: 'BTC/USDT',
            price: 45000,
            volume24h: 1000000,
            change1h: 2.5,
            change4h: -1.2,
            change1d: 5.3,
            volume1h: 50000,
            volume4h: 200000,
            volume1d: 800000
        },
        // Add more market data...
    ];

    const sortOptions = [
        { value: 'volume24h', label: '24h Volume' },
        { value: 'change1h', label: '1h Change' },
        { value: 'change4h', label: '4h Change' },
        { value: 'change1d', label: '1d Change' }
    ];

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
    };

    const applyFilters = () => {
        // Implement filter logic here
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
                            className={`w-full p-2 rounded-md border ${getColor('border.primary')} ${getColor('background.primary')}`}
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
                            className={`w-full p-2 rounded-md border ${getColor('border.primary')} ${getColor('background.primary')}`}
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
                            className="react-select"
                        />
                    </div>

                    <button
                        onClick={applyFilters}
                        className={`px-4 py-2 rounded-md flex items-center gap-2 ${getColor('background.primary')} text-white`}
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
                            <th className="py-3 text-left">Symbol</th>
                            <th className="py-3 text-right">Price</th>
                            <th className="py-3 text-right">24h Volume</th>
                            <th className="py-3 text-right">1h Change</th>
                            <th className="py-3 text-right">4h Change</th>
                            <th className="py-3 text-right">1d Change</th>
                            <th className="py-3 text-right">Volume (1h/4h/1d)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {marketData.map((item, index) => (
                            <tr
                                key={item.symbol}
                                className={`border-b ${getColor('border.primary')} hover:${getColor('background.secondary')}`}
                            >
                                <td className="py-3">{item.symbol}</td>
                                <td className="text-right">${item.price.toLocaleString()}</td>
                                <td className="text-right">${item.volume24h.toLocaleString()}</td>
                                <td className={`text-right ${item.change1h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {item.change1h}%
                                </td>
                                <td className={`text-right ${item.change4h >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {item.change4h}%
                                </td>
                                <td className={`text-right ${item.change1d >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {item.change1d}%
                                </td>
                                <td className="text-right">
                                    ${item.volume1h.toLocaleString()} /
                                    ${item.volume4h.toLocaleString()} /
                                    ${item.volume1d.toLocaleString()}
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