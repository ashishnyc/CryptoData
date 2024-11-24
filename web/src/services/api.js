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
        const response = await api.get('/symbols');
        const symbolsArray = Object.values(response.data);
        return symbolsArray;
    }
};