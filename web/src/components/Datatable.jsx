import React from 'react';
import { ArrowUpDown } from 'lucide-react';

// Table Header Component
const TableHeader = ({ label, sortKey, sortConfig, onSort, textColor }) => {
    const isActive = sortConfig.key === sortKey;
    return (
        <th
            className={`py-3 px-4 text-right cursor-pointer group ${textColor} whitespace-nowrap`}
            onClick={() => onSort(sortKey)}
        >
            <div className="flex items-center justify-end gap-2">
                {label}
                <ArrowUpDown
                    className={`w-4 h-4 transition-opacity ${isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'
                        } ${isActive && sortConfig.direction === 'asc' ? 'rotate-180' : ''
                        }`}
                />
            </div>
        </th>
    );
};

const MarketDataTable = ({
    symbols,
    symbolsInfo,
    sortConfig,
    onSort,
    formatPrice,
    formatPercentage,
    getColor
}) => {
    return (
        <div className="overflow-y-auto max-h-[calc(100vh-240px)]">
            <table className="w-full relative">
                <thead className={`sticky top-0 z-10 ${getColor('background.primary')}`}>
                    <tr className={`border-b ${getColor('border.primary')}`}>
                        <TableHeader
                            label="Symbol"
                            sortKey="symbol"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="Current Price"
                            sortKey="price"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="24h Volume"
                            sortKey="volume24h"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="1h Change"
                            sortKey="change1h"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="4h Change"
                            sortKey="change4h"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="1d Change"
                            sortKey="change1d"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                        <TableHeader
                            label="Volume (5m/15m/1h)"
                            sortKey="volume"
                            sortConfig={sortConfig}
                            onSort={onSort}
                            textColor={getColor('text.primary')}
                        />
                    </tr>
                </thead>
                <tbody>
                    {symbols.map((symbol) => {
                        const data = symbolsInfo[symbol];
                        if (!data) return null;
                        return (
                            <tr
                                key={symbol}
                                className={`border-b ${getColor('border.primary')} hover:${getColor('background.secondary')}`}
                            >
                                <td className={`py-3 px-4 ${getColor('text.primary')}`}>
                                    {symbol}
                                </td>
                                <td className={`py-3 px-4 text-right ${getColor('text.primary')}`}>
                                    {formatPrice(data.current_price, data.price_scale)}
                                </td>
                                <td className={`py-3 px-4 text-right ${getColor('text.primary')}`}>
                                    ${(data.turnover_1d || 0).toLocaleString()}
                                </td>
                                <td className={`py-3 px-4 text-right ${data.change_1h_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(data.change_1h_pct)}
                                </td>
                                <td className={`py-3 px-4 text-right ${data.change_4h_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(data.change_4h_pct)}
                                </td>
                                <td className={`py-3 px-4 text-right ${data.change_1d_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {formatPercentage(data.change_1d_pct)}
                                </td>
                                <td className={`py-3 px-4 text-right ${getColor('text.primary')}`}>
                                    ${(data.turnover_5m || 0).toLocaleString()} /
                                    ${(data.turnover_15m || 0).toLocaleString()} /
                                    ${(data.turnover_1h || 0).toLocaleString()}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default MarketDataTable;