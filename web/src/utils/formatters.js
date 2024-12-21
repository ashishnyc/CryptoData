// src/utils/formatters.js

/**
 * Format price with given price scale
 * @param {number} price - The price to format
 * @param {number} priceScale - Number of decimal places
 * @returns {string} Formatted price string
 */
export const formatPrice = (price, priceScale = 2) => {
    if (price === undefined || price === null || typeof price !== 'number') {
        return '0.00';
    }
    return price.toLocaleString(undefined, {
        minimumFractionDigits: priceScale,
        maximumFractionDigits: priceScale
    });
};

/**
 * Format percentage with +/- sign
 * @param {number} value - Percentage value (e.g., 0.156 for 15.6%)
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimals = 2) => {
    if (value === undefined || value === null || typeof value !== 'number') {
        return '0.00%';
    }
    var pct_value = Number(value);
    const formatted = Number(pct_value * 100).toFixed(decimals);
    return `${value >= 0 ? '+' : ''}${formatted}%`;
};

/**
 * Format volume/turnover with appropriate units (K, M, B)
 * @param {number} value - The volume/turnover value
 * @returns {string} Formatted volume string
 */
export const formatVolume = (value) => {
    if (value === undefined || value === null || typeof value !== 'number') {
        return '$0';
    }

    if (value >= 1000000000) {
        return `$${(value / 1000000000).toFixed(2)}B`;
    }
    if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(2)}M`;
    }
    if (value >= 1000) {
        return `$${(value / 1000).toFixed(2)}K`;
    }
    return `$${value.toFixed(2)}`;
};

/**
 * Format date/time
 * @param {number|string|Date} timestamp - Timestamp or date string
 * @param {boolean} includeTime - Whether to include time in the output
 * @returns {string} Formatted date string
 */
export const formatDateTime = (timestamp, includeTime = true) => {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        ...(includeTime && {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        })
    };

    return new Intl.DateTimeFormat('en-US', options).format(date);
};

/**
 * Format number with thousand separators
 * @param {number} value - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number string
 */
export const formatNumber = (value, decimals = 0) => {
    if (value === undefined || value === null || typeof value !== 'number') {
        return '0';
    }
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
};