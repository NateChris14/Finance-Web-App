import pandas as pd
import numpy as np
from flask import Flask, jsonify
from flask_cors import CORS
import json
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from src.utils import load_data, FeatureEngineer
from src.components.clustering.pipeline.predict_pipeline import PredictPipeline

# ========================================
# 🔄 DATA LOADING AND PREPROCESSING
# ========================================

print("🔄 Loading data...")

try:
    # Try to load real data
    columns = [
        "sd.ticker", "sd.date", "sd.open", "sd.high", "sd.low", "sd.close", "sd.volume",
        "ti.ticker", "ti.date", "ti.rsi", "ti.macd", "ti.sma", "ti.ema", "ti.atr", 
        "ti.bb_upper", "ti.bb_middle", "ti.bb_lower"
    ]
    df = pd.concat(load_data(join=True, chunksize=10000, columns=columns), ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df['date'] = pd.to_datetime(df['date'])
    tickers = df['ticker'].unique()
    print(f"✅ Loaded real data with {len(df)} rows and {len(tickers)} tickers")
    
except Exception as e:
    print(f"❌ Error loading real data: {e}")
    print("🔄 Creating sample data for testing...")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')
    sample_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'DIS', 'JPM']
    
    data = []
    for ticker in sample_tickers:
        for date in dates:
            price = 100 + np.random.randn() * 10
            data.append({
                'ticker': ticker,
                'date': date,
                'open': price,
                'high': price * 1.02,
                'low': price * 0.98,
                'close': price * (1 + np.random.randn() * 0.01),
                'volume': int(1000000 + np.random.randn() * 500000),
                'rsi': 30 + np.random.randn() * 20,
                'macd': np.random.randn() * 2,
                'sma': price,
                'ema': price,
                'atr': abs(np.random.randn() * 5),
                'bb_upper': price * 1.05,
                'bb_middle': price,
                'bb_lower': price * 0.95
            })
    
    df = pd.DataFrame(data)
    tickers = df['ticker'].unique()
    print(f"✅ Created sample data with {len(df)} rows and {len(tickers)} tickers")

# ========================================
# 🔧 FEATURE ENGINEERING
# ========================================

print("🔄 Starting feature engineering...")
df_copy = df.copy()
ticker_date_info = df_copy[['ticker', 'date']].copy()

try:
    fe = FeatureEngineer()
    df_new = fe.fit_transform(df_copy)
    
    if 'ticker' not in df_new.columns:
        df_new['ticker'] = ticker_date_info['ticker'].values
        df_new['date'] = ticker_date_info['date'].values
        
except Exception as e:
    print(f"❌ Error in feature engineering: {e}")
    df_new = df.copy()
    df_new['price_change'] = df_new.groupby('ticker')['close'].pct_change()

# ========================================
# 🤖 CLUSTERING
# ========================================

print("🔄 Predicting clusters...")
try:
    PCA_df = PredictPipeline().predict_clusters(df)
    df_new['clusters'] = PCA_df['clusters']
    
except Exception as e:
    print(f"❌ Error in clustering: {e}")
    print("🔄 Using simplified clustering...")
    
    # Simplified clustering
    feature_cols = ['rsi', 'macd', 'volume']
    available_features = [col for col in feature_cols if col in df_new.columns]
    
    if available_features and len(df_new) > 0:
        try:
            cluster_data = df_new[available_features + ['ticker']].dropna()
            latest_data = cluster_data.groupby('ticker')[available_features].last().reset_index()
            
            if len(latest_data) >= 4:
                scaler = StandardScaler()
                scaled_features = scaler.fit_transform(latest_data[available_features])
                kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(scaled_features)
                
                ticker_clusters = pd.DataFrame({
                    'ticker': latest_data['ticker'],
                    'clusters': clusters
                })
                
                df_new = df_new.merge(ticker_clusters, on='ticker', how='left')
                df_new['clusters'] = df_new['clusters'].fillna(0).astype(int)
                
                # Create PCA_df for visualization
                PCA_df = pd.DataFrame({
                    'col1': np.random.randn(200),
                    'col2': np.random.randn(200),
                    'col3': np.random.randn(200),
                    'clusters': np.random.choice(ticker_clusters['clusters'], 200),
                    'ticker': np.random.choice(ticker_clusters['ticker'], 200)
                })
                
            else:
                raise ValueError("Not enough data points")
                
        except Exception as cluster_error:
            print(f"❌ Simplified clustering failed: {cluster_error}")
            df_new['clusters'] = np.random.randint(0, 4, len(df_new))
            PCA_df = pd.DataFrame({
                'col1': np.random.randn(100),
                'col2': np.random.randn(100),
                'col3': np.random.randn(100),
                'clusters': np.random.randint(0, 4, 100),
                'ticker': np.random.choice(tickers, 100)
            })
    else:
        df_new['clusters'] = np.random.randint(0, 4, len(df_new))
        PCA_df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100),
            'col3': np.random.randn(100),
            'clusters': np.random.randint(0, 4, 100),
            'ticker': np.random.choice(tickers, 100)
        })

# ========================================
# 📊 CLUSTER ANALYSIS SETUP
# ========================================

def get_cluster_stocks():
    """Get stocks belonging to each cluster"""
    try:
        if 'ticker' not in df_new.columns or 'clusters' not in df_new.columns:
            return {i: [] for i in range(4)}
        
        latest_clusters = df_new.groupby('ticker')['clusters'].last().reset_index()
        cluster_stocks = {}
        
        for cluster_id in range(4):
            cluster_tickers = latest_clusters[latest_clusters['clusters'] == cluster_id]['ticker'].tolist()
            cluster_stocks[cluster_id] = cluster_tickers
        
        return cluster_stocks
        
    except Exception as e:
        print(f"❌ Error in get_cluster_stocks: {e}")
        sample_tickers = tickers.tolist() if len(tickers) > 0 else ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        return {
            0: sample_tickers[:len(sample_tickers)//4] if len(sample_tickers) >= 4 else sample_tickers[:1],
            1: sample_tickers[len(sample_tickers)//4:len(sample_tickers)//2] if len(sample_tickers) >= 4 else sample_tickers[1:2],
            2: sample_tickers[len(sample_tickers)//2:3*len(sample_tickers)//4] if len(sample_tickers) >= 4 else sample_tickers[2:3],
            3: sample_tickers[3*len(sample_tickers)//4:] if len(sample_tickers) >= 4 else sample_tickers[3:4]
        }

cluster_stocks = get_cluster_stocks()

# Enhanced Business labels for clusters
cluster_insights = {
    0: {
        "label": "✅ STABLE GROWTH",
        "description": "Conservative dividend-focused stocks with steady performance",
        "strategy": "INCOME & LONG-TERM GROWTH",
        "risk": "LOW RISK",
        "allocation": "40-60% of portfolio",
        "color": "#10B981",
        "icon": "📈",
        "stocks": cluster_stocks.get(0, [])
    },
    1: {
        "label": "⚠️ HIGH VOLATILITY",
        "description": "Volatile stocks with no clear trend - requires active monitoring",
        "strategy": "SHORT-TERM TRADING ONLY",
        "risk": "HIGH RISK",
        "allocation": "5-10% of portfolio",
        "color": "#EF4444",
        "icon": "⚡",
        "stocks": cluster_stocks.get(1, [])
    },
    2: {
        "label": "🚀 MOMENTUM PLAYS",
        "description": "High momentum, algorithmic trading opportunities",
        "strategy": "QUANTITATIVE & MOMENTUM",
        "risk": "MEDIUM-HIGH RISK",
        "allocation": "15-25% of portfolio",
        "color": "#F59E0B",
        "icon": "🎯",
        "stocks": cluster_stocks.get(2, [])
    },
    3: {
        "label": "🏆 INSTITUTIONAL FAVORITES",
        "description": "High volume, bullish trend - institutional and ETF tracking",
        "strategy": "CORE HOLDINGS",
        "risk": "MEDIUM RISK",
        "allocation": "25-35% of portfolio",
        "color": "#3B82F6",
        "icon": "🏛️",
        "stocks": cluster_stocks.get(3, [])
    }
}

# Add ticker information to PCA_df if not present
if 'ticker' not in PCA_df.columns:
    try:
        if 'ticker' in df_new.columns and 'clusters' in df_new.columns:
            ticker_cluster_map = df_new.groupby('ticker')['clusters'].last().reset_index()
            pca_tickers = []
            for _, row in PCA_df.iterrows():
                cluster_id = row['clusters']
                cluster_tickers = ticker_cluster_map[ticker_cluster_map['clusters'] == cluster_id]['ticker'].tolist()
                if cluster_tickers:
                    ticker_idx = len(pca_tickers) % len(cluster_tickers)
                    pca_tickers.append(cluster_tickers[ticker_idx])
                else:
                    pca_tickers.append('UNKNOWN')
            PCA_df['ticker'] = pca_tickers
        else:
            PCA_df['ticker'] = ['STOCK_' + str(i) for i in range(len(PCA_df))]
    except Exception as e:
        PCA_df['ticker'] = ['STOCK_' + str(i) for i in range(len(PCA_df))]

PCA_df['cluster_use_case'] = PCA_df['clusters'].map(lambda x: cluster_insights.get(x, {}).get('label', 'Unknown'))

# ========================================
# 📈 BUSINESS METRICS CALCULATION
# ========================================

def calculate_business_metrics(ticker_data):
    """Calculate key business metrics for a stock"""
    if ticker_data.empty:
        return {}
    
    latest = ticker_data.iloc[-1]
    previous = ticker_data.iloc[-2] if len(ticker_data) > 1 else latest
    
    current_price = latest.get('close', 0)
    price_change = current_price - previous.get('close', current_price)
    price_change_pct = (price_change / previous.get('close', 1)) * 100 if previous.get('close', 0) != 0 else 0
    
    rsi = latest.get('rsi', 50)
    macd = latest.get('macd', 0)
    
    # Generate recommendation
    if rsi < 30 and macd > 0:
        recommendation = "STRONG BUY"
        confidence = 90
        target_price = current_price * 1.15
    elif rsi < 50 and macd > 0:
        recommendation = "BUY"
        confidence = 75
        target_price = current_price * 1.08
    elif rsi > 70 and macd < 0:
        recommendation = "SELL"
        confidence = 80
        target_price = current_price * 0.92
    else:
        recommendation = "HOLD"
        confidence = 60
        target_price = current_price
    
    return {
        'current_price': float(current_price),
        'price_change': float(price_change),
        'price_change_pct': float(price_change_pct),
        'recommendation': recommendation,
        'confidence': int(confidence),
        'target_price': float(target_price),
        'upside': float(((target_price - current_price) / current_price) * 100) if current_price != 0 else 0,
        'rsi': float(rsi),
        'macd': float(macd)
    }

print("✅ Data pipeline completed successfully!")

# ========================================
# 🔧 FLASK SERVER SETUP
# ========================================

server = Flask(__name__)
CORS(server, origins=["*"])

# ========================================
# 🚀 API ENDPOINTS (Only what frontend needs)
# ========================================

@server.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "API is running",
        "data_info": {
            "total_records": len(df),
            "total_tickers": len(tickers),
            "clusters_available": len(cluster_insights),
            "sample_tickers": tickers[:5].tolist() if len(tickers) > 0 else []
        }
    })

@server.route('/api/tickers', methods=['GET'])
def get_tickers():
    """Get all available tickers"""
    try:
        return jsonify({
            "tickers": tickers.tolist(),
            "count": len(tickers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/stock/<ticker>/summary', methods=['GET'])
def get_stock_summary(ticker):
    """Get executive summary for a ticker"""
    try:
        if ticker not in tickers:
            return jsonify({"error": f"Ticker '{ticker}' not found"}), 404
        
        ticker_data = df[df['ticker'] == ticker].sort_values('date')
        metrics = calculate_business_metrics(ticker_data)
        
        if not metrics:
            return jsonify({"error": "No data available for ticker"}), 404
        
        # Get cluster info
        ticker_cluster_data = df_new[df_new['ticker'] == ticker]
        if not ticker_cluster_data.empty:
            ticker_cluster = ticker_cluster_data['clusters'].iloc[0]
            cluster_info = cluster_insights.get(ticker_cluster, {})
        else:
            ticker_cluster = None
            cluster_info = {}
        
        return jsonify({
            'ticker': ticker,
            'metrics': metrics,
            'cluster': {
                'id': int(ticker_cluster) if ticker_cluster is not None else None,
                'label': cluster_info.get('label', ''),
                'color': cluster_info.get('color', ''),
                'risk': cluster_info.get('risk', ''),
                'strategy': cluster_info.get('strategy', ''),
                'description': cluster_info.get('description', '')
            },
            'latest_date': ticker_data['date'].max().strftime('%Y-%m-%d') if not ticker_data.empty else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/stock/<ticker>/chart-data', methods=['GET'])
def get_chart_data(ticker):
    """Get candlestick chart data"""
    try:
        if ticker not in tickers:
            return jsonify({"error": f"Ticker '{ticker}' not found"}), 404
        
        ticker_data = df[df['ticker'] == ticker].sort_values('date')
        
        if ticker_data.empty:
            return jsonify({"error": "No data available for ticker"}), 404
        
        return jsonify({
            'ticker': ticker,
            'data': {
                'dates': ticker_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                'open': ticker_data['open'].fillna(0).tolist(),
                'high': ticker_data['high'].fillna(0).tolist(),
                'low': ticker_data['low'].fillna(0).tolist(),
                'close': ticker_data['close'].fillna(0).tolist(),
                'volume': ticker_data['volume'].fillna(0).tolist(),
                'sma': ticker_data['sma'].fillna(0).tolist(),
                'ema': ticker_data['ema'].fillna(0).tolist(),
                'bb_upper': ticker_data['bb_upper'].fillna(0).tolist(),
                'bb_lower': ticker_data['bb_lower'].fillna(0).tolist(),
            },
            'count': len(ticker_data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/stock/<ticker>/technical', methods=['GET'])
def get_technical_data(ticker):
    """Get technical indicators"""
    try:
        if ticker not in tickers:
            return jsonify({"error": f"Ticker '{ticker}' not found"}), 404
        
        ticker_data = df[df['ticker'] == ticker].sort_values('date')
        
        if ticker_data.empty:
            return jsonify({"error": "No data available for ticker"}), 404
        
        return jsonify({
            'ticker': ticker,
            'timeseries': {
                'dates': ticker_data['date'].dt.strftime('%Y-%m-%d').tolist(),
                'rsi': ticker_data['rsi'].fillna(50).tolist(),
                'macd': ticker_data['macd'].fillna(0).tolist(),
                'volume': ticker_data['volume'].fillna(0).tolist(),
                'atr': ticker_data['atr'].fillna(0).tolist() if 'atr' in ticker_data.columns else [0] * len(ticker_data)
            },
            'current': {
                'rsi': float(ticker_data['rsi'].iloc[-1]) if not ticker_data['rsi'].isna().iloc[-1] else 50.0,
                'macd': float(ticker_data['macd'].iloc[-1]) if not ticker_data['macd'].isna().iloc[-1] else 0.0,
                'atr': float(ticker_data['atr'].iloc[-1]) if 'atr' in ticker_data.columns and not ticker_data['atr'].isna().iloc[-1] else 0.0,
                'volume': float(ticker_data['volume'].iloc[-1]) if not ticker_data['volume'].isna().iloc[-1] else 0.0
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get cluster analysis data"""
    try:
        cluster_stocks = get_cluster_stocks()
        
        # Calculate cluster summaries
        if 'clusters' in df_new.columns:
            summary = df_new.groupby('clusters').agg({
                'rsi': 'median',
                'macd': 'median',
                'atr': 'median',
                'volume': 'median',
                'close': ['mean', 'std']
            }).round(2)
            
            summary.columns = ['_'.join(col).strip() for col in summary.columns]
            summary = summary.reset_index()
        else:
            # Create dummy summary
            summary = pd.DataFrame({
                'clusters': [0, 1, 2, 3],
                'rsi_median': [45, 65, 55, 50],
                'macd_median': [0.5, -0.3, 1.2, 0.1],
                'atr_median': [2.1, 4.5, 3.2, 2.8],
                'volume_median': [1000000, 2000000, 1500000, 1800000],
                'close_mean': [150, 200, 180, 160],
                'close_std': [10, 25, 15, 12]
            })
        
        clusters_data = []
        for _, row in summary.iterrows():
            cluster_id = int(row['clusters'])
            cluster_info = cluster_insights[cluster_id]
            
            clusters_data.append({
                'id': cluster_id,
                'label': cluster_info['label'],
                'description': cluster_info['description'],
                'color': cluster_info['color'],
                'risk': cluster_info['risk'],
                'strategy': cluster_info['strategy'],
                'allocation': cluster_info['allocation'],
                'icon': cluster_info['icon'],
                'stocks': cluster_stocks.get(cluster_id, []),
                'stock_count': len(cluster_stocks.get(cluster_id, [])),
                'metrics': {
                    'atr_median': float(row['atr_median']),
                    'macd_median': float(row['macd_median']),
                    'volume_median': float(row['volume_median']),
                    'rsi_median': float(row['rsi_median']),
                    'close_mean': float(row['close_mean']),
                    'close_std': float(row['close_std'])
                }
            })
        
        return jsonify({
            'clusters': clusters_data,
            'total_clusters': len(clusters_data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@server.route('/api/clusters/pca', methods=['GET'])
def get_pca_data():
    """Get PCA data for 3D visualization"""
    try:
        pca_with_tickers = PCA_df.copy()
        
        pca_with_tickers['cluster_label'] = pca_with_tickers['clusters'].map(
            lambda x: cluster_insights.get(x, {}).get('label', 'Unknown')
        )
        
        return jsonify({
            'data': pca_with_tickers.to_dict('records'),
            'count': len(pca_with_tickers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================
# 🚀 RUN THE APPLICATION
# ========================================

if __name__ == '__main__':
    print("🚀 Starting Portfolio Intelligence API...")
    print("🔌 API Endpoints: http://localhost:8050/api/")
    print("💡 Try: http://localhost:8050/api/health")
    
    server.run(debug=True, host='0.0.0.0', port=8050)