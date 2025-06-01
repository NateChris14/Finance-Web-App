// Mock API service to simulate backend responses
const mockAPI = {
    // Simulate API delay
    delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  
    // Get available tickers
    getTickers: async () => {
      await mockAPI.delay(500);
      return {
        success: true,
        tickers: ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX", "JPM", "JNJ"]
      };
    },
  
    // Get clusters data
    getClusters: async () => {
      await mockAPI.delay(300);
      return {
        success: true,
        clusters: [
          {
            id: 0,
            label: "✅ Stable Growth",
            description: "Conservative dividend-focused stocks with steady performance",
            strategy: "Income & Long-term Growth",
            risk: "Low Risk",
            color: "#10b981",
            icon: "shield",
            stocks: ["AAPL", "MSFT", "JNJ", "PG", "KO", "WMT"],
            avgReturn: "8.2%",
            volatility: "12.5%",
            riskLevel: "Low"
          },
          {
            id: 1,
            label: "⚠️ High Volatility",
            description: "Volatile stocks with no clear trend - requires active monitoring",
            strategy: "Short-term Trading Only",
            risk: "High Risk",
            color: "#ef4444",
            icon: "zap",
            stocks: ["TSLA", "GME", "AMC", "PLTR", "COIN"],
            avgReturn: "15.8%",
            volatility: "45.2%",
            riskLevel: "High"
          },
          {
            id: 2,
            label: "🚀 Momentum Growth",
            description: "High momentum, algorithmic trading opportunities",
            strategy: "Quantitative & Momentum",
            risk: "Medium-High Risk",
            color: "#f59e0b",
            icon: "trending-up",
            stocks: ["NVDA", "AMD", "CRM", "SNOW", "ZM"],
            avgReturn: "22.4%",
            volatility: "28.7%",
            riskLevel: "Medium-High"
          },
          {
            id: 3,
            label: "🏆 Institutional Favorites",
            description: "High volume, bullish trend - institutional and ETF tracking",
            strategy: "Core Holdings",
            risk: "Medium Risk",
            color: "#3b82f6",
            icon: "target",
            stocks: ["GOOGL", "AMZN", "META", "NFLX", "DIS"],
            avgReturn: "18.6%",
            volatility: "22.1%",
            riskLevel: "Medium"
          }
        ]
      };
    },
  
    // Get comprehensive stock data
    getStockData: async (ticker) => {
      await mockAPI.delay(800);
  
      // Generate mock data based on ticker
      const basePrice = 150 + Math.random() * 100;
      const rsi = 30 + Math.random() * 40;
      const macd = (Math.random() - 0.5) * 4;
  
      // Generate time series data
      const generateTimeSeries = (days) => {
        const data = [];
        let price = basePrice;
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
  
        for (let i = 0; i < days; i++) {
          const date = new Date(startDate);
          date.setDate(date.getDate() + i);
  
          const change = (Math.random() - 0.5) * 0.05;
          price = price * (1 + change);
  
          const volume = 30000000 + Math.random() * 40000000;
          const sma = price * (1 + Math.sin(i / 10) * 0.02);
          const ema = price * (1 + Math.sin(i / 8) * 0.015);
  
          data.push({
            date: date.toISOString().split('T')[0],
            close: Number(price.toFixed(2)),
            volume: Math.round(volume),
            sma: Number(sma.toFixed(2)),
            ema: Number(ema.toFixed(2)),
            rsi: Math.max(0, Math.min(100, rsi + (Math.random() - 0.5) * 10)),
            macd: macd + (Math.random() - 0.5) * 2,
            macdSignal: macd * 0.8 + (Math.random() - 0.5) * 1.5,
            macdHistogram: (Math.random() - 0.5) * 1
          });
        }
  
        return data;
      };
  
      const chartData = generateTimeSeries(60);
      const currentPrice = chartData[chartData.length - 1].close;
      const targetPrice = currentPrice * (1.05 + Math.random() * 0.1);
  
      // Determine cluster based on ticker
      let clusterId = 0;
      if (["TSLA", "GME", "AMC"].includes(ticker)) clusterId = 1;
      else if (["NVDA", "AMD", "CRM"].includes(ticker)) clusterId = 2;
      else if (["GOOGL", "AMZN", "META"].includes(ticker)) clusterId = 3;
  
      const clusters = await mockAPI.getClusters();
      const cluster = clusters.clusters[clusterId];
  
      // Generate recommendation
      let recommendation = "HOLD";
      let confidence = 60;
      if (rsi < 40 && macd > 0) {
        recommendation = "BUY";
        confidence = 80;
      } else if (rsi > 60 && macd < 0) {
        recommendation = "SELL";
        confidence = 75;
      }
  
      // Generate PCA data
      const pcaData = Array.from({ length: 200 }, (_, i) => ({
        pc1: (Math.random() - 0.5) * 10,
        pc2: (Math.random() - 0.5) * 10,
        pc3: (Math.random() - 0.5) * 10,
        cluster: Math.floor(i / 50),
        ticker: i % 20 === 0 ? ticker : `STOCK${i}`
      }));
  
      return {
        success: true,
        ticker,
        recommendation: {
          action: recommendation,
          confidence
        },
        metrics: {
          currentPrice: Number(currentPrice.toFixed(2)),
          targetPrice: Number(targetPrice.toFixed(2)),
          upside: Number((((targetPrice - currentPrice) / currentPrice) * 100).toFixed(2)),
          rsi: Number(rsi.toFixed(2)),
          macd: Number(macd.toFixed(3))
        },
        cluster,
        chartData,
        technicalData: chartData,
        pcaData
      };
    }
  };
  
  // Make it globally available
  window.mockAPI = mockAPI;