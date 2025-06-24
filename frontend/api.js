// API Configuration
const API_CONFIG = {
    baseURL: '',
    timeout: 10000,
    retryAttempts: 3,
    retryDelay: 1000
};

// API Service Class
class APIService {
    constructor() {
        this.baseURL = API_CONFIG.baseURL;
        this.timeout = API_CONFIG.timeout;
    }

    // Generic fetch with error handling and retries
    async fetchWithRetry(url, options = {}, retries = API_CONFIG.retryAttempts) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (retries > 0 && !controller.signal.aborted) {
                console.warn(`Request failed, retrying... (${retries} attempts left)`);
                await this.delay(API_CONFIG.retryDelay);
                return this.fetchWithRetry(url, options, retries - 1);
            }
            
            throw error;
        }
    }

    // Utility function for delays
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Health check
    async checkHealth() {
        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/health`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get all tickers
    async getTickers() {
        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/tickers`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get stock summary
    async getStockSummary(ticker) {
        if (!ticker) {
            return { success: false, error: 'Ticker is required' };
        }

        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/stock/${ticker}/summary`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get chart data
    async getChartData(ticker) {
        if (!ticker) {
            return { success: false, error: 'Ticker is required' };
        }

        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/stock/${ticker}/chart-data`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get technical indicators
    async getTechnicalData(ticker) {
        if (!ticker) {
            return { success: false, error: 'Ticker is required' };
        }

        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/stock/${ticker}/technical`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get clusters
    async getClusters() {
        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/clusters`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get PCA data
    async getPCAData() {
        try {
            const data = await this.fetchWithRetry(`${this.baseURL}/api/clusters/pca`);
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Get all data for a ticker (parallel requests)
    async getAllStockData(ticker) {
        if (!ticker) {
            return { success: false, error: 'Ticker is required' };
        }

        try {
            const [summaryResult, chartResult, technicalResult] = await Promise.allSettled([
                this.getStockSummary(ticker),
                this.getChartData(ticker),
                this.getTechnicalData(ticker)
            ]);

            const results = {
                summary: summaryResult.status === 'fulfilled' ? summaryResult.value : null,
                chart: chartResult.status === 'fulfilled' ? chartResult.value : null,
                technical: technicalResult.status === 'fulfilled' ? technicalResult.value : null
            };

            // Check if at least one request succeeded
            const hasSuccess = Object.values(results).some(result => result?.success);
            
            if (!hasSuccess) {
                throw new Error('All requests failed');
            }

            return { success: true, data: results };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

// Create global API instance
const api = new APIService();

// Export for use in other files
window.api = api;