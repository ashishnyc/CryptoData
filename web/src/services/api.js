import axios from 'axios';

const api = axios.create({
    baseURL: '/api'
});

export const marketService = {
    getKlineData: async (symbol, timeframe) => {
        const response = await api.get(`/klines/${symbol}`, {
            params: { timeframe }
        });
        return response.data;
    },

    getOpportunities: async () => {
        const response = await api.get('/opportunities');
        return response.data;
    },

    getTrades: async () => {
        const response = await api.get('/trades');
        return response.data;
    },

    getSymbols: async () => {
        try {
            const response = await api.get('/symbols');
            const symbolsMap = response.data.reduce((acc, [id, symbol, priceScale]) => {
                acc[id] = {
                    symbol: symbol,
                    priceScale: priceScale
                };
                return acc;
            }, {});
            return symbolsMap;
        } catch (error) {
            console.error('Error in getSymbols:', error);
            return {};
        }
    }
};