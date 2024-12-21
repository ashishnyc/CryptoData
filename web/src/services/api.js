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
    },

    getSymbolsInfo: async (symbol) => {
        try {
            const response = await api.get(`/symbols/${symbol}`);
            const symbolsInfoMap = response.data.reduce((acc, {
                symbol,
                time,
                current_price,
                change_5m_pct,
                change_15m_pct,
                change_1h_pct,
                change_4h_pct,
                change_1d_pct,
                turnover_5m,
                turnover_15m,
                turnover_1h,
                turnover_4h,
                turnover_1d,
                price_scale: priceScale,
                max_price_24h,
                min_price_24h
            }) => {
                acc[symbol] = {
                    time,
                    current_price,
                    change_5m_pct,
                    change_15m_pct,
                    change_1h_pct,
                    change_4h_pct,
                    change_1d_pct,
                    turnover_5m,
                    turnover_15m,
                    turnover_1h,
                    turnover_4h,
                    turnover_1d,
                    priceScale,
                    max_price_24h,
                    min_price_24h
                };
                return acc;
            }, {});
            return symbolsInfoMap;
        } catch (error) {
            console.error('Error in getSymbolsInfo:', error);
            return {};
        }
    }
};