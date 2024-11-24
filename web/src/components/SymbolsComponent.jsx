import React from 'react';
import { RefreshCw } from 'lucide-react';

const Symbols = ({ symbols, activeSymbol, setActiveSymbol }) => {
    return (
        <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-semibold text-gray-800">Symbols</h2>
                <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                    <RefreshCw className="w-5 h-5 text-gray-600" />
                </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {symbols.map((symbol) => (
                    <button
                        key={symbol}
                        onClick={() => setActiveSymbol(symbol)}
                        className={`p-4 rounded-lg border transition-all ${activeSymbol === symbol
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-200 hover:border-blue-200 hover:bg-blue-50'
                            }`}
                    >
                        {symbol}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default Symbols;