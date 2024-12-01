export const chartTheme = {
    getChartOptions: (getColor) => ({
        layout: {
            background: { type: 'solid', color: getColor('chart.background') },
            textColor: getColor('chart.text')
        },
        timeScale: {
            timeVisible: true,
            secondsVisible: true,
            borderColor: getColor('chart.border')
        },
        rightPriceScale: {
            borderColor: getColor('chart.border')
        }
    })
};