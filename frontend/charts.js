// Charts Service Class
class ChartsService {
    constructor() {
        this.charts = {};
        this.defaultColors = {
            primary: '#3b82f6',
            secondary: '#8b5cf6',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#06b6d4',
            light: '#f8fafc',
            dark: '#1e293b'
        };
    }

    // Create candlestick chart using Plotly
    createCandlestickChart(containerId, data) {
        if (!data || !data.data) {
            console.error('Invalid data for candlestick chart');
            return;
        }

        const { dates, open, high, low, close, volume, sma, ema } = data.data;

        // Candlestick trace
        const candlestick = {
            x: dates,
            open: open,
            high: high,
            low: low,
            close: close,
            type: 'candlestick',
            name: 'OHLC',
            yaxis: 'y',
            increasing: { line: { color: this.defaultColors.success } },
            decreasing: { line: { color: this.defaultColors.danger } }
        };

        // SMA trace
        const smaTrace = {
            x: dates,
            y: sma,
            type: 'scatter',
            mode: 'lines',
            name: 'SMA (20)',
            line: { color: this.defaultColors.primary, width: 2 },
            yaxis: 'y'
        };

        // EMA trace
        const emaTrace = {
            x: dates,
            y: ema,
            type: 'scatter',
            mode: 'lines',
            name: 'EMA (20)',
            line: { color: this.defaultColors.warning, width: 2 },
            yaxis: 'y'
        };

        // Volume trace
        const volumeTrace = {
            x: dates,
            y: volume,
            type: 'bar',
            name: 'Volume',
            marker: { color: 'rgba(156, 163, 175, 0.6)' },
            yaxis: 'y2'
        };

        const layout = {
            title: {
                text: `${data.ticker} - Price Action & Volume Analysis`,
                font: { size: 18, color: this.defaultColors.light }
            },
            xaxis: {
                title: 'Date',
                rangeslider: { visible: false },
                type: 'date',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            yaxis: {
                title: 'Price ($)',
                domain: [0.3, 1],
                side: 'left',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            yaxis2: {
                title: 'Volume',
                domain: [0, 0.25],
                side: 'right',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: this.defaultColors.light },
            showlegend: true,
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(51, 65, 85, 0.8)',
                bordercolor: '#475569',
                borderwidth: 1
            },
            margin: { l: 50, r: 50, t: 50, b: 50 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
            displaylogo: false
        };

        Plotly.newPlot(containerId, [candlestick, smaTrace, emaTrace, volumeTrace], layout, config);
        
        // Store chart reference
        this.charts[containerId] = { type: 'candlestick', data, layout, config };
    }

    // Create technical indicators chart
    createTechnicalChart(containerId, data) {
        if (!data || !data.timeseries) {
            console.error('Invalid data for technical chart');
            return;
        }

        const { dates, rsi, macd } = data.timeseries;

        // RSI trace
        const rsiTrace = {
            x: dates,
            y: rsi,
            type: 'scatter',
            mode: 'lines',
            name: 'RSI',
            line: { color: this.defaultColors.primary, width: 2 },
            yaxis: 'y'
        };

        // MACD trace
        const macdTrace = {
            x: dates,
            y: macd,
            type: 'scatter',
            mode: 'lines',
            name: 'MACD',
            line: { color: this.defaultColors.secondary, width: 2 },
            yaxis: 'y2'
        };

        // RSI reference lines
        const rsiOverbought = {
            x: dates,
            y: Array(dates.length).fill(70),
            type: 'scatter',
            mode: 'lines',
            name: 'Overbought (70)',
            line: { color: this.defaultColors.danger, width: 1, dash: 'dash' },
            yaxis: 'y',
            showlegend: false
        };

        const rsiOversold = {
            x: dates,
            y: Array(dates.length).fill(30),
            type: 'scatter',
            mode: 'lines',
            name: 'Oversold (30)',
            line: { color: this.defaultColors.success, width: 1, dash: 'dash' },
            yaxis: 'y',
            showlegend: false
        };

        // MACD zero line
        const macdZero = {
            x: dates,
            y: Array(dates.length).fill(0),
            type: 'scatter',
            mode: 'lines',
            name: 'Zero Line',
            line: { color: '#94a3b8', width: 1, dash: 'dot' },
            yaxis: 'y2',
            showlegend: false
        };

        const layout = {
            title: {
                text: `${data.ticker} - Technical Indicators`,
                font: { size: 18, color: this.defaultColors.light }
            },
            xaxis: {
                title: 'Date',
                type: 'date',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            yaxis: {
                title: 'RSI',
                domain: [0.55, 1],
                range: [0, 100],
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            yaxis2: {
                title: 'MACD',
                domain: [0, 0.45],
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: this.defaultColors.light },
            showlegend: true,
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(51, 65, 85, 0.8)',
                bordercolor: '#475569',
                borderwidth: 1
            },
            margin: { l: 50, r: 50, t: 50, b: 50 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };

        Plotly.newPlot(containerId, [rsiTrace, rsiOverbought, rsiOversold, macdTrace, macdZero], layout, config);
        
        // Store chart reference
        this.charts[containerId] = { type: 'technical', data, layout, config };
    }

    // Create 3D PCA chart
    create3DChart(containerId, data) {
        if (!data || !data.data) {
            console.error('Invalid data for 3D chart');
            return;
        }

        const clusters = [...new Set(data.data.map(d => d.clusters))];
        const colors = [this.defaultColors.success, this.defaultColors.danger, this.defaultColors.warning, this.defaultColors.primary];

        const traces = clusters.map((cluster, index) => {
            const clusterData = data.data.filter(d => d.clusters === cluster);
            
            return {
                x: clusterData.map(d => d.col1),
                y: clusterData.map(d => d.col2),
                z: clusterData.map(d => d.col3),
                mode: 'markers',
                type: 'scatter3d',
                name: clusterData[0]?.cluster_label || `Cluster ${cluster}`,
                marker: {
                    size: 5,
                    color: colors[index % colors.length],
                    opacity: 0.8
                },
                text: clusterData.map(d => d.ticker),
                hovertemplate: '<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>PC3: %{z:.2f}<extra></extra>'
            };
        });

        const layout = {
            title: {
                text: '3D Portfolio Clustering Analysis',
                font: { size: 18, color: this.defaultColors.light }
            },
            scene: {
                xaxis: { 
                    title: 'Principal Component 1',
                    gridcolor: '#475569',
                    color: this.defaultColors.light
                },
                yaxis: { 
                    title: 'Principal Component 2',
                    gridcolor: '#475569',
                    color: this.defaultColors.light
                },
                zaxis: { 
                    title: 'Principal Component 3',
                    gridcolor: '#475569',
                    color: this.defaultColors.light
                },
                camera: {
                    eye: { x: 1.5, y: 1.5, z: 1.5 }
                },
                bgcolor: 'rgba(0,0,0,0)'
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: this.defaultColors.light },
            showlegend: true,
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(51, 65, 85, 0.8)',
                bordercolor: '#475569',
                borderwidth: 1
            },
            margin: { l: 0, r: 0, t: 50, b: 0 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };

        Plotly.newPlot(containerId, traces, layout, config);
        
        // Store chart reference
        this.charts[containerId] = { type: '3d', data, layout, config };
    }

    // Create bubble chart
    createBubbleChart(containerId, clusterData) {
        if (!clusterData || !clusterData.clusters) {
            console.error('Invalid data for bubble chart');
            return;
        }

        const clusters = clusterData.clusters;
        const colors = [this.defaultColors.success, this.defaultColors.danger, this.defaultColors.warning, this.defaultColors.primary];

        const trace = {
            x: clusters.map(c => c.metrics.atr_median),
            y: clusters.map(c => c.metrics.macd_median),
            mode: 'markers',
            type: 'scatter',
            marker: {
                size: clusters.map(c => Math.sqrt(c.metrics.volume_median) / 1000),
                color: clusters.map(c => colors[c.id % colors.length]),
                opacity: 0.7,
                line: { width: 2, color: '#ffffff' },
                sizemode: 'diameter',
                sizeref: 2
            },
            text: clusters.map(c => c.label),
            customdata: clusters.map(c => ({
                rsi: c.metrics.rsi_median,
                stocks: c.stocks.slice(0, 5).join(', '),
                stockCount: c.stock_count
            })),
            hovertemplate: '<b>%{text}</b><br>' +
                          'ATR: %{x:.2f}<br>' +
                          'MACD: %{y:.2f}<br>' +
                          'RSI: %{customdata.rsi:.1f}<br>' +
                          'Stocks (%{customdata.stockCount}): %{customdata.stocks}<extra></extra>'
        };

        const layout = {
            title: {
                text: 'Risk vs Momentum Analysis',
                font: { size: 18, color: this.defaultColors.light }
            },
            xaxis: {
                title: 'ATR (Volatility Risk)',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            yaxis: {
                title: 'MACD (Momentum)',
                gridcolor: '#475569',
                color: this.defaultColors.light
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: this.defaultColors.light },
            showlegend: false,
            margin: { l: 60, r: 60, t: 60, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };

        Plotly.newPlot(containerId, [trace], layout, config);
        
        // Store chart reference
        this.charts[containerId] = { type: 'bubble', data: clusterData, layout, config };
    }

    // Resize all charts
    resizeCharts() {
        Object.keys(this.charts).forEach(containerId => {
            if (document.getElementById(containerId)) {
                Plotly.Plots.resize(containerId);
            }
        });
    }

    // Clear all charts
    clearCharts() {
        Object.keys(this.charts).forEach(containerId => {
            if (document.getElementById(containerId)) {
                Plotly.purge(containerId);
            }
        });
        this.charts = {};
    }

    // Update chart theme
    updateTheme(isDark = true) {
        const theme = isDark ? {
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { color: this.defaultColors.light },
            gridcolor: '#475569'
        } : {
            plot_bgcolor: 'rgba(255,255,255,1)',
            paper_bgcolor: 'rgba(255,255,255,1)',
            font: { color: '#1e293b' },
            gridcolor: '#e2e8f0'
        };

        Object.keys(this.charts).forEach(containerId => {
            if (document.getElementById(containerId)) {
                const chart = this.charts[containerId];
                const updatedLayout = { ...chart.layout, ...theme };
                Plotly.relayout(containerId, updatedLayout);
            }
        });
    }
}

// Create global charts instance
const charts = new ChartsService();

// Handle window resize
window.addEventListener('resize', () => {
    charts.resizeCharts();
});

// Export for use in other files
window.charts = charts;