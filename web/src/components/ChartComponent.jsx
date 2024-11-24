import React, { useState } from 'react';
import Chart from './Chart';
import Select from 'react-select';

const ChartComponent = ({ activeSymbol, timeframes, timeframe, setTimeframe }) => {
    const [selectedOption, setSelectedOption] = useState(null);

    const handleChange = (selectedOption) => {
        setSelectedOption(selectedOption);
        // Handle the change in selected option if needed
    };

    const options = [
        { value: 'AAPL', label: 'Apple' },
        { value: 'GOOGL', label: 'Google' },
        // Add more options as needed
    ];

    return (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold text-gray-800">{activeSymbol} Chart</h2>
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
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                <Chart symbol={activeSymbol} timeframe={timeframe} />
            </div>
        </div>
    );
};

export default ChartComponent;