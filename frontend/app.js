// Main Application Class
class StockDashboard {
  constructor() {
      this.currentTicker = null;
      this.isLoading = false;
      this.clusters = null;
      
      // DOM elements
      this.elements = {
          tickerSelect: document.getElementById('ticker-select'),
          loadingOverlay: document.getElementById('loading-overlay'),
          errorMessage: document.getElementById('error-message'),
          errorText: document.getElementById('error-text'),
          retryBtn: document.getElementById('retry-btn'),
          dashboardContent: document.getElementById('dashboard-content'),
          statusIndicator: document.getElementById('status-indicator'),
          statusText: document.getElementById('status-text'),
          
          // Summary elements
          summaryTicker: document.getElementById('summary-ticker'),
          recommendationBadge: document.getElementById('recommendation-badge'),
          confidenceText: document.getElementById('confidence-text'),
          currentPrice: document.getElementById('current-price'),
          targetPrice: document.getElementById('target-price'),
          potentialUpside: document.getElementById('potential-upside'),
          rsiValue: document.getElementById('rsi-value'),
          macdValue: document.getElementById('macd-value'),
          
          // Cluster elements
          clusterInfo: document.getElementById('cluster-info'),
          clusterBadge: document.getElementById('cluster-badge'),
          clusterDescription: document.getElementById('cluster-description'),
          clusterStrategy: document.getElementById('cluster-strategy'),
          clusterRisk: document.getElementById('cluster-risk'),
          clusterCards: document.getElementById('cluster-cards')
      };

      this.init();
  }

  async init() {
      console.log('Initializing Stock Dashboard...');
      
      // Check API health
      await this.checkAPIHealth();
      
      // Load initial data
      await this.loadTickers();
      
      // Setup event listeners
      this.setupEventListeners();
      
      // Load clusters
      await this.loadClusters();
      
      console.log('Dashboard initialized successfully');
  }

  async checkAPIHealth() {
      try {
          const result = await api.checkHealth();
          
          if (result.success) {
              this.updateStatus('connected', 'API Connected');
              console.log('API Health Check:', result.data);
          } else {
              this.updateStatus('error', 'API Error');
              this.showError(`API Health Check Failed: ${result.error}`);
          }
      } catch (error) {
          this.updateStatus('error', 'Connection Failed');
          this.showError(`Failed to connect to API: ${error.message}`);
      }
  }

  async loadTickers() {
      try {
          this.showLoading(true);
          
          const result = await api.getTickers();
          
          if (result.success && result.data.tickers) {
              this.populateTickerSelect(result.data.tickers);
              
              // Load first ticker by default
              if (result.data.tickers.length > 0) {
                  this.currentTicker = result.data.tickers[0];
                  this.elements.tickerSelect.value = this.currentTicker;
                  await this.loadStockData(this.currentTicker);
              }
          } else {
              this.showError(`Failed to load tickers: ${result.error}`);
          }
      } catch (error) {
          this.showError(`Error loading tickers: ${error.message}`);
      } finally {
          this.showLoading(false);
      }
  }

  populateTickerSelect(tickers) {
      this.elements.tickerSelect.innerHTML = '';
      
      tickers.forEach(ticker => {
          const option = document.createElement('option');
          option.value = ticker;
          option.textContent = ticker;
          this.elements.tickerSelect.appendChild(option);
      });
      
      console.log(`Loaded ${tickers.length} tickers`);
  }

  async loadStockData(ticker) {
      if (!ticker || this.isLoading) return;
      
      try {
          this.isLoading = true;
          this.showLoading(true);
          this.hideError();
          
          console.log(`Loading data for ${ticker}...`);
          
          // Get all stock data
          const result = await api.getAllStockData(ticker);
          
          if (result.success) {
              const { summary, chart, technical } = result.data;
              
              // Update summary
              if (summary?.success) {
                  this.updateSummary(summary.data);
              }
              
              // Update charts
              if (chart?.success) {
                  charts.createCandlestickChart('price-chart', chart.data);
              }
              
              if (technical?.success) {
                  charts.createTechnicalChart('technical-chart', technical.data);
              }
              
              // Show dashboard
              this.showDashboard();
              
              console.log(`Successfully loaded data for ${ticker}`);
          } else {
              this.showError(`Failed to load data for ${ticker}: ${result.error}`);
          }
      } catch (error) {
          this.showError(`Error loading stock data: ${error.message}`);
      } finally {
          this.isLoading = false;
          this.showLoading(false);
      }
  }

  async loadClusters() {
      try {
          const result = await api.getClusters();
          
          if (result.success && result.data.clusters) {
              this.clusters = result.data.clusters;
              this.renderClusterCards();
              
              // Load PCA data for 3D chart
              const pcaResult = await api.getPCAData();
              if (pcaResult.success) {
                  charts.create3DChart('pca-chart', pcaResult.data);
              }
              
              // Create bubble chart
              charts.createBubbleChart('bubble-chart', result.data);
              
              console.log('Clusters loaded successfully');
          } else {
              console.warn('Failed to load clusters:', result.error);
          }
      } catch (error) {
          console.error('Error loading clusters:', error);
      }
  }

  renderClusterCards() {
      if (!this.clusters || !this.elements.clusterCards) return;
      
      this.elements.clusterCards.innerHTML = '';
      
      this.clusters.forEach(cluster => {
          const card = document.createElement('div');
          card.className = 'cluster-card';
          card.style.setProperty('--cluster-color', cluster.color);
          
          const stockTags = cluster.stocks.slice(0, 8).map(stock => 
              `<span class="stock-tag" style="background: ${cluster.color}">${stock}</span>`
          ).join('');
          
          const moreStocks = cluster.stocks.length > 8 ? 
              `<span class="stock-tag" style="background: #6b7280">+${cluster.stocks.length - 8} more</span>` : '';
          
          card.innerHTML = `
              <h3>${cluster.label}</h3>
              <p>${cluster.description}</p>
              <div class="cluster-details">
                  <span class="cluster-strategy">Strategy: ${cluster.strategy}</span>
                  <span class="cluster-risk">Risk: ${cluster.risk}</span>
              </div>
              <div class="cluster-stocks">
                  ${stockTags}
                  ${moreStocks}
              </div>
          `;
          
          this.elements.clusterCards.appendChild(card);
      });
  }

  updateSummary(data) {
      if (!data) return;
      
      // Update ticker
      this.elements.summaryTicker.textContent = data.ticker;
      
      // Update recommendation
      const recommendation = data.metrics.recommendation;
      this.elements.recommendationBadge.textContent = recommendation;
      this.elements.recommendationBadge.className = 'recommendation-badge';
      
      if (recommendation === 'STRONG BUY' || recommendation === 'BUY') {
          this.elements.recommendationBadge.classList.add('buy');
      } else if (recommendation === 'HOLD') {
          this.elements.recommendationBadge.classList.add('hold');
      } else {
          this.elements.recommendationBadge.classList.add('sell');
      }
      
      // Update confidence
      this.elements.confidenceText.textContent = `${data.metrics.confidence}% Confidence`;
      
      // Update metrics
      this.elements.currentPrice.textContent = `$${data.metrics.current_price.toFixed(2)}`;
      this.elements.targetPrice.textContent = `$${data.metrics.target_price.toFixed(2)}`;
      this.elements.potentialUpside.textContent = `${data.metrics.upside.toFixed(2)}%`;
      this.elements.rsiValue.textContent = data.metrics.rsi.toFixed(2);
      this.elements.macdValue.textContent = data.metrics.macd.toFixed(3);
      
      // Update cluster info
      if (data.cluster && data.cluster.label) {
          this.elements.clusterInfo.classList.remove('hidden');
          this.elements.clusterBadge.textContent = data.cluster.label;
          this.elements.clusterBadge.style.backgroundColor = data.cluster.color;
          this.elements.clusterDescription.textContent = data.cluster.description;
          this.elements.clusterStrategy.textContent = `Strategy: ${data.cluster.strategy}`;
          this.elements.clusterRisk.textContent = `Risk: ${data.cluster.risk}`;
      } else {
          this.elements.clusterInfo.classList.add('hidden');
      }
  }

  setupEventListeners() {
      // Ticker selection
      this.elements.tickerSelect.addEventListener('change', (e) => {
          const ticker = e.target.value;
          if (ticker && ticker !== this.currentTicker) {
              this.currentTicker = ticker;
              this.loadStockData(ticker);
          }
      });
      
      // Retry button
      this.elements.retryBtn.addEventListener('click', () => {
          if (this.currentTicker) {
              this.loadStockData(this.currentTicker);
          } else {
              this.loadTickers();
          }
      });
      
      // Chart period buttons
      document.querySelectorAll('.chart-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
              // Remove active class from all buttons
              document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
              // Add active class to clicked button
              e.target.classList.add('active');
              
              // Here you could implement different time periods
              // For now, we'll just reload the current data
              if (this.currentTicker) {
                  this.loadStockData(this.currentTicker);
              }
          });
      });
  }

  updateStatus(status, text) {
      this.elements.statusIndicator.className = `status-indicator ${status}`;
      this.elements.statusText.textContent = text;
  }

  showLoading(show = true) {
      if (show) {
          this.elements.loadingOverlay.classList.remove('hidden');
      } else {
          this.elements.loadingOverlay.classList.add('hidden');
      }
  }

  showError(message) {
      this.elements.errorText.textContent = message;
      this.elements.errorMessage.classList.remove('hidden');
      this.elements.dashboardContent.classList.add('hidden');
      console.error('Dashboard Error:', message);
  }

  hideError() {
      this.elements.errorMessage.classList.add('hidden');
  }

  showDashboard() {
      this.elements.dashboardContent.classList.remove('hidden');
      this.elements.dashboardContent.classList.add('fade-in');
      this.hideError();
  }

  // Utility method to format numbers
  formatNumber(num, decimals = 2) {
      if (typeof num !== 'number') return '0.00';
      return num.toLocaleString('en-US', {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals
      });
  }

  // Utility method to format currency
  formatCurrency(num) {
      if (typeof num !== 'number') return '$0.00';
      return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD'
      }).format(num);
  }

  // Utility method to format percentage
  formatPercentage(num) {
      if (typeof num !== 'number') return '0.00%';
      return `${num.toFixed(2)}%`;
  }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing dashboard...');
  
  // Create dashboard instance
  window.dashboard = new StockDashboard();
  
  // Add some global error handling
  window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
  });
  
  window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
  });
});

// Add some utility functions for the dashboard
window.utils = {
  // Debounce function for performance
  debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
          const later = () => {
              clearTimeout(timeout);
              func(...args);
          };
          clearTimeout(timeout);
          timeout = setTimeout(later, wait);
      };
  },
  
  // Throttle function for performance
  throttle(func, limit) {
      let inThrottle;
      return function() {
          const args = arguments;
          const context = this;
          if (!inThrottle) {
              func.apply(context, args);
              inThrottle = true;
              setTimeout(() => inThrottle = false, limit);
          }
      };
  },
  
  // Format large numbers
  formatLargeNumber(num) {
      if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
      if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
      if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
      return num.toString();
  },
  
  // Get color based on value (for positive/negative indicators)
  getValueColor(value, isPercentage = false) {
      if (value > 0) return '#10b981'; // green
      if (value < 0) return '#ef4444'; // red
      return '#6b7280'; // gray
  }
};