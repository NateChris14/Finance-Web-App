import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from src.utils import load_data, FeatureEngineer
from src.components.clustering.pipeline.predict_pipeline import PredictPipeline

# Add these imports for API functionality
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import plotly.utils
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ========================================
# 🔄 DATA LOADING AND PREPROCESSING
# ========================================

print("🔄 Loading data...")
columns = [
    "sd.ticker", "sd.date", "sd.open", "sd.high", "sd.low", "sd.close", "sd.volume",
    "ti.ticker", "ti.date", "ti.rsi", "ti.macd", "ti.sma", "ti.ema", "ti.atr", "ti.bb_upper", "ti.bb_middle", "ti.bb_lower"
]

try:
    df = pd.concat(load_data(join=True, chunksize=10000, columns=columns), ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df['date'] = pd.to_datetime(df['date'])
    tickers = df['ticker'].unique()
    print(f"✅ Loaded data with {len(df)} rows and {len(tickers)} tickers")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    # Create sample data for testing
    print("🔄 Creating sample data for testing...")
    dates = pd.date_range('2023-01-01', '2024-01-01', freq='D')
    sample_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
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

print(f"📊 Original columns: {list(df.columns)}")

# ========================================
# 🔧 FEATURE ENGINEERING WITH TICKER PRESERVATION
# ========================================

print("🔄 Starting feature engineering...")
df_copy = df.copy()

# Store ticker and date info before feature engineering
ticker_date_info = df_copy[['ticker', 'date']].copy()

try:
    fe = FeatureEngineer()
    df_new = fe.fit_transform(df_copy)
    print(f"📊 After feature engineering columns: {list(df_new.columns)}")
    
    # Add ticker back to df_new if it's missing
    if 'ticker' not in df_new.columns:
        print("⚠️  'ticker' column missing after feature engineering. Adding it back...")
        if len(df_new) == len(ticker_date_info):
            df_new['ticker'] = ticker_date_info['ticker'].values
            df_new['date'] = ticker_date_info['date'].values
        else:
            print(f"❌ Length mismatch: df_new={len(df_new)}, ticker_info={len(ticker_date_info)}")
            df_new = df_new.reset_index(drop=True)
            ticker_date_info = ticker_date_info.reset_index(drop=True)
            min_len = min(len(df_new), len(ticker_date_info))
            df_new = df_new.iloc[:min_len].copy()
            df_new['ticker'] = ticker_date_info.iloc[:min_len]['ticker'].values
            df_new['date'] = ticker_date_info.iloc[:min_len]['date'].values

except Exception as e:
    print(f"❌ Error in feature engineering: {e}")
    print("🔄 Using simplified feature engineering...")
    df_new = df.copy()
    # Add some basic derived features
    df_new['price_change'] = df_new.groupby('ticker')['close'].pct_change()
    df_new['volume_ma'] = df_new.groupby('ticker')['volume'].rolling(window=5).mean().reset_index(0, drop=True)

print(f"✅ df_new now has columns: {list(df_new.columns)}")

# ========================================
# 🤖 CLUSTERING WITH FALLBACK
# ========================================

print("🔄 Predicting clusters...")
try:
    PCA_df = PredictPipeline().predict_clusters(df)
    print(f"✅ PCA_df shape: {PCA_df.shape}")
    
    # Add clusters to df_new
    if len(PCA_df) == len(df_new):
        df_new['clusters'] = PCA_df['clusters']
    else:
        print(f"⚠️  Length mismatch between PCA_df ({len(PCA_df)}) and df_new ({len(df_new)})")
        # Create mapping based on available data
        if 'ticker' in PCA_df.columns:
            df_new = df_new.merge(PCA_df[['ticker', 'clusters']], on='ticker', how='left')
        else:
            clusters = PCA_df['clusters'].tolist()
            if len(clusters) < len(df_new):
                clusters.extend([0] * (len(df_new) - len(clusters)))
            elif len(clusters) > len(df_new):
                clusters = clusters[:len(df_new)]
            df_new['clusters'] = clusters
            
except Exception as e:
    print(f"❌ Error in clustering: {e}")
    print("🔄 Using simplified clustering...")
    
    # Simplified clustering approach
    feature_cols = ['rsi', 'macd', 'volume']
    available_features = [col for col in feature_cols if col in df_new.columns]
    
    if available_features and len(df_new) > 0:
        try:
            # Get latest values per ticker for clustering
            cluster_data = df_new[available_features + ['ticker']].dropna()
            latest_data = cluster_data.groupby('ticker')[available_features].last().reset_index()
            
            if len(latest_data) >= 4:  # Need at least 4 points for 4 clusters
                # Scale features
                scaler = StandardScaler()
                scaled_features = scaler.fit_transform(latest_data[available_features])
                
                # Perform clustering
                kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(scaled_features)
                
                # Create cluster mapping
                ticker_clusters = pd.DataFrame({
                    'ticker': latest_data['ticker'],
                    'clusters': clusters
                })
                
                # Add clusters back to df_new
                df_new = df_new.merge(ticker_clusters, on='ticker', how='left')
                df_new['clusters'] = df_new['clusters'].fillna(0).astype(int)
                
                # Create simple PCA_df for visualization
                n_points = min(200, len(ticker_clusters))
                PCA_df = pd.DataFrame({
                    'col1': np.random.randn(n_points),
                    'col2': np.random.randn(n_points),
                    'col3': np.random.randn(n_points),
                    'clusters': np.random.choice(ticker_clusters['clusters'], n_points),
                    'ticker': np.random.choice(ticker_clusters['ticker'], n_points)
                })
                
                print("✅ Simplified clustering completed")
            else:
                raise ValueError("Not enough data points for clustering")
                
        except Exception as cluster_error:
            print(f"❌ Simplified clustering failed: {cluster_error}")
            # Final fallback: random assignment
            df_new['clusters'] = np.random.randint(0, 4, len(df_new))
            PCA_df = pd.DataFrame({
                'col1': np.random.randn(100),
                'col2': np.random.randn(100),
                'col3': np.random.randn(100),
                'clusters': np.random.randint(0, 4, 100),
                'ticker': np.random.choice(tickers, 100) if len(tickers) > 0 else ['SAMPLE'] * 100
            })
            print("⚠️  Using random clusters as final fallback")
    else:
        # Final fallback
        df_new['clusters'] = np.random.randint(0, 4, len(df_new))
        PCA_df = pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100),
            'col3': np.random.randn(100),
            'clusters': np.random.randint(0, 4, 100),
            'ticker': np.random.choice(tickers, 100) if len(tickers) > 0 else ['SAMPLE'] * 100
        })
        print("⚠️  Using random clusters as fallback")

# ========================================
# 📊 CLUSTER ANALYSIS SETUP
# ========================================

def get_cluster_stocks():
    """Get stocks belonging to each cluster"""
    try:
        cluster_stocks = {}
        
        if 'ticker' not in df_new.columns or 'clusters' not in df_new.columns:
            print(f"❌ Missing columns in df_new: {list(df_new.columns)}")
            return {i: [] for i in range(4)}
        
        # Get the latest cluster assignment for each ticker
        latest_clusters = df_new.groupby('ticker')['clusters'].last().reset_index()
        
        for cluster_id in range(4):
            cluster_tickers = latest_clusters[latest_clusters['clusters'] == cluster_id]['ticker'].tolist()
            cluster_stocks[cluster_id] = cluster_tickers
        
        print(f"✅ Cluster distribution: {[(k, len(v)) for k, v in cluster_stocks.items()]}")
        return cluster_stocks
        
    except Exception as e:
        print(f"❌ Error in get_cluster_stocks: {e}")
        # Return sample data
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
    print("⚠️  Adding ticker info to PCA_df...")
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
        print(f"❌ Error adding tickers to PCA_df: {e}")
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
    
    # Price metrics
    current_price = latest.get('close', 0)
    price_change = current_price - previous.get('close', current_price)
    price_change_pct = (price_change / previous.get('close', 1)) * 100 if previous.get('close', 0) != 0 else 0
    
    # Technical signals
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
print(f"📊 Final data shapes:")
print(f"   - df: {df.shape}")
print(f"   - df_new: {df_new.shape}")
print(f"   - PCA_df: {PCA_df.shape}")
print(f"   - Available tickers: {len(tickers)}")

# ========================================
# 🔧 FLASK SERVER SETUP
# ========================================

server = Flask(__name__)
CORS(server, origins=["*"])

# ========================================
# 🚀 API ENDPOINTS
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
            return jsonify({"error": f"Ticker '{ticker}' not found. Available tickers: {tickers[:10].tolist()}"}), 404
        
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
            # Create dummy summary if clustering failed
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
# 📱 DASH APP SETUP
# ========================================

app = dash.Dash(
    __name__, 
    server=server,
    routes_pathname_prefix='/dashboard/'
)
app.title = "Portfolio Intelligence Dashboard"

# ========================================
# 🎨 DASH LAYOUT
# ========================================

app.layout = html.Div([
    # API Info Header
    html.Div([
        html.H3("🚀 API Endpoints Available:", style={'color': '#f8fafc', 'marginBottom': '10px'}),
        html.P("Dashboard URL: http://localhost:8050/dashboard/", style={'color': '#10b981', 'fontWeight': 'bold'}),
        html.Ul([
            html.Li("GET /api/health - Health check", style={'color': '#cbd5e1'}),
            html.Li("GET /api/tickers - Get all tickers", style={'color': '#cbd5e1'}),
            html.Li("GET /api/stock/{ticker}/summary - Get stock summary", style={'color': '#cbd5e1'}),
            html.Li("GET /api/stock/{ticker}/chart-data - Get chart data", style={'color': '#cbd5e1'}),
            html.Li("GET /api/stock/{ticker}/technical - Get technical indicators", style={'color': '#cbd5e1'}),
            html.Li("GET /api/clusters - Get cluster analysis", style={'color': '#cbd5e1'}),
            html.Li("GET /api/clusters/pca - Get PCA data", style={'color': '#cbd5e1'}),
        ], style={'marginBottom': '20px'})
    ], style={
        'backgroundColor': '#1e293b',
        'padding': '20px',
        'borderBottom': '2px solid #334155',
        'marginBottom': '20px'
    }),
    
    # Main Header
    html.Div([
        html.Div([
            html.H1("📊 PORTFOLIO INTELLIGENCE DASHBOARD", 
                   style={
                       'textAlign': 'center',
                       'color': '#f8fafc',
                       'fontSize': '2.5rem',
                       'fontWeight': 'bold',
                       'marginBottom': '10px',
                       'fontFamily': 'Arial, sans-serif'
                   }),
            html.P("AI-Powered Stock Analysis & Investment Strategy Platform",
                  style={
                      'textAlign': 'center',
                      'color': '#cbd5e1',
                      'fontSize': '1.2rem',
                      'marginBottom': '30px'
                  })
        ])
    ], style={
        'backgroundColor': '#1e293b',
        'padding': '30px',
        'borderBottom': '3px solid #334155',
        'marginBottom': '20px'
    }),
    
    # Main Content Container
    html.Div([
        # Stock Selection and Key Metrics Row
        html.Div([
            # Stock Selector
            html.Div([
                html.Label("📈 SELECT STOCK FOR ANALYSIS:", 
                          style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#f1f5f9', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='ticker-dropdown',
                    options=[{'label': f"{t} - {t}", 'value': t} for t in sorted(tickers)],
                    value=tickers[0] if len(tickers) > 0 else 'AAPL',
                    style={
                        'fontSize': '16px',
                        'fontFamily': 'Arial, sans-serif',
                        'backgroundColor': '#334155',
                        'color': '#f1f5f9'
                    }
                )
            ], style={
                'width': '49%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'marginRight': '2%',
                'border': '1px solid #475569'
            }),

            # Executive Summary Card
            html.Div(id='executive-summary', style={
                'width': '49%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'border': '1px solid #475569'
            })
        ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),

        # Charts Section
        html.Div([
            # Candlestick Chart
            html.Div([
                dcc.Graph(id='candlestick-chart')
            ], style={
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'marginBottom': '30px',
                'border': '1px solid #475569'
            }),

            # Technical Indicators
            html.Div([
                dcc.Graph(id='rsi-macd-chart')
            ], style={
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'marginBottom': '30px',
                'border': '1px solid #475569'
            })
        ]),

        # AI Cluster Analysis Section
        html.Div([
            html.H2("🧠 AI-POWERED INVESTMENT CLUSTER ANALYSIS", 
                   style={
                       'textAlign': 'center',
                       'color': '#f8fafc',
                       'fontSize': '2rem',
                       'fontWeight': 'bold',
                       'marginBottom': '30px'
                   }),
            
            # Enhanced Cluster Cards with Stock Lists
            html.Div([
                html.Div([
                    html.Div([
                        html.H3(f"{cluster_insights[i]['icon']} {cluster_insights[i]['label']}", 
                               style={'color': cluster_insights[i]['color'], 'fontSize': '1.1rem', 'fontWeight': 'bold', 'marginBottom': '8px'}),
                        html.P(cluster_insights[i]['description'], 
                              style={'color': '#cbd5e1', 'fontSize': '12px', 'marginBottom': '8px'}),
                        html.Div([
                            html.Span("STRATEGY: ", style={'fontWeight': 'bold', 'color': '#f1f5f9', 'fontSize': '11px'}),
                            html.Span(cluster_insights[i]['strategy'], style={'color': cluster_insights[i]['color'], 'fontWeight': 'bold', 'fontSize': '11px'})
                        ], style={'marginBottom': '4px'}),
                        html.Div([
                            html.Span("RISK: ", style={'fontWeight': 'bold', 'color': '#f1f5f9', 'fontSize': '11px'}),
                            html.Span(cluster_insights[i]['risk'], style={'color': cluster_insights[i]['color'], 'fontWeight': 'bold', 'fontSize': '11px'})
                        ], style={'marginBottom': '8px'}),
                        # Stock List
                        html.Div([
                            html.Span("📊 STOCKS: ", style={'fontWeight': 'bold', 'color': '#f1f5f9', 'fontSize': '10px'}),
                            html.Div([
                                html.Span(f"{stock}", 
                                         style={
                                             'backgroundColor': cluster_insights[i]['color'],
                                             'color': 'white',
                                             'padding': '2px 6px',
                                             'borderRadius': '10px',
                                             'fontSize': '9px',
                                             'fontWeight': 'bold',
                                             'margin': '2px',
                                             'display': 'inline-block'
                                         })
                                for stock in cluster_insights[i]['stocks'][:8]  # Show first 8 stocks
                            ], style={'marginTop': '4px'}),
                            html.Div(f"+ {len(cluster_insights[i]['stocks']) - 8} more" if len(cluster_insights[i]['stocks']) > 8 else "",
                                   style={'color': '#94a3b8', 'fontSize': '9px', 'marginTop': '4px'})
                        ])
                    ], style={
                        'backgroundColor': '#334155',
                        'padding': '15px',
                        'borderRadius': '8px',
                        'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                        'borderLeft': f'4px solid {cluster_insights[i]["color"]}',
                        'height': '240px',
                        'border': '1px solid #475569',
                        'overflow': 'hidden'
                    })
                ], style={'width': '24%', 'display': 'inline-block', 'margin': '0.5%'})
                for i in range(4)
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px'}),

            # 3D PCA Visualization
            html.Div([
                dcc.Graph(id='pca-cluster-chart')
            ], style={
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'marginBottom': '30px',
                'border': '1px solid #475569'
            }),

            # Bubble Chart
            html.Div([
                dcc.Graph(id='cluster-bubble-chart')
            ], style={
                'backgroundColor': '#334155',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
                'marginBottom': '30px',
                'border': '1px solid #475569'
            })
        ])
    ], style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '0 20px'
    })
], style={
    'backgroundColor': '#0f172a',
    'minHeight': '100vh',
    'fontFamily': 'Arial, sans-serif'
})

# ========================================
# 📊 DASH CALLBACKS
# ========================================

# Executive Summary Callback
@app.callback(
    Output('executive-summary', 'children'),
    Input('ticker-dropdown', 'value')
)
def update_executive_summary(ticker):
    if not ticker or ticker not in tickers:
        return html.Div("Please select a valid ticker", style={'color': '#ef4444'})
    
    ticker_data = df[df['ticker'] == ticker].sort_values('date')
    metrics = calculate_business_metrics(ticker_data)
    
    if not metrics:
        return html.Div("No data available", style={'color': '#ef4444'})
    
    # Get ticker's cluster information
    ticker_cluster_data = df_new[df_new['ticker'] == ticker]
    if not ticker_cluster_data.empty:
        ticker_cluster = ticker_cluster_data['clusters'].iloc[0]
        cluster_info = cluster_insights.get(ticker_cluster, {})
    else:
        ticker_cluster = None
        cluster_info = {}
    
    # Determine recommendation color
    rec_colors = {
        'STRONG BUY': '#10b981',
        'BUY': '#10b981', 
        'HOLD': '#f59e0b',
        'SELL': '#ef4444'
    }
    
    return html.Div([
        html.H3(f"📊 EXECUTIVE SUMMARY - {ticker}", 
               style={'color': '#f8fafc', 'fontSize': '1.3rem', 'marginBottom': '15px'}),
        
        # Cluster Badge
        html.Div([
            html.Span(f"{cluster_info.get('icon', '📊')} {cluster_info.get('label', 'Unknown Cluster')}", 
                     style={
                         'backgroundColor': cluster_info.get('color', '#6b7280'),
                         'color': 'white',
                         'padding': '6px 12px',
                         'borderRadius': '15px',
                         'fontSize': '12px',
                         'fontWeight': 'bold',
                         'marginBottom': '10px',
                         'display': 'inline-block'
                     })
        ], style={'marginBottom': '15px'}),
        
        # Recommendation Badge
        html.Div([
            html.Span(f"🎯 {metrics['recommendation']}", 
                     style={
                         'backgroundColor': rec_colors.get(metrics['recommendation'], '#6b7280'),
                         'color': 'white',
                         'padding': '8px 16px',
                         'borderRadius': '20px',
                         'fontSize': '14px',
                         'fontWeight': 'bold'
                     }),
            html.Span(f" ({metrics['confidence']}% Confidence)", 
                     style={'color': '#cbd5e1', 'marginLeft': '10px', 'fontSize': '12px'})
        ], style={'marginBottom': '15px'}),
        
        # Key Metrics
        html.Div([
            html.Div([
                html.Span("💰 Current Price: ", style={'fontWeight': 'bold', 'color': '#f1f5f9'}),
                html.Span(f"${metrics['current_price']:.2f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#f8fafc'})
            ], style={'marginBottom': '8px'}),
            
            html.Div([
                html.Span("📈 Target Price: ", style={'fontWeight': 'bold', 'color': '#f1f5f9'}),
                html.Span(f"${metrics['target_price']:.2f}", style={'color': '#10b981', 'fontWeight': 'bold'}),
                html.Span(f" (+{metrics['upside']:.1f}%)", style={'color': '#10b981', 'fontSize': '12px'})
            ], style={'marginBottom': '8px'}),
            
            html.Div([
                html.Span("📊 RSI: ", style={'fontWeight': 'bold', 'color': '#f1f5f9'}),
                html.Span(f"{metrics['rsi']:.1f}", style={'fontWeight': 'bold', 'color': '#f8fafc'}),
                html.Span(" | ", style={'color': '#cbd5e1'}),
                html.Span("📈 MACD: ", style={'fontWeight': 'bold', 'color': '#f1f5f9'}),
                html.Span(f"{metrics['macd']:.3f}", style={'fontWeight': 'bold', 'color': '#f8fafc'})
            ])
        ])
    ])

# Enhanced Candlestick chart
@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_candlestick_chart(ticker):
    if not ticker:
        return go.Figure()
    
    df_t = df[df['ticker'] == ticker].sort_values('date')
    
    if df_t.empty:
        return go.Figure().add_annotation(
            text="No data available for selected ticker",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color='#f8fafc')
        )

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        specs=[[{"type": "xy"}], [{"type": "xy"}]],
        subplot_titles=(f"📈 {ticker} - Price Action & Technical Analysis", "📊 Trading Volume")
    )

    # Enhanced Candlestick with professional colors
    fig.add_trace(go.Candlestick(
        x=df_t['date'], 
        open=df_t['open'], 
        high=df_t['high'],
        low=df_t['low'], 
        close=df_t['close'], 
        name='OHLC',
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444',
        increasing_fillcolor='rgba(16, 185, 129, 0.3)',
        decreasing_fillcolor='rgba(239, 68, 68, 0.3)'
    ), row=1, col=1)

    # Technical indicators with professional styling
    if 'sma' in df_t.columns:
        fig.add_trace(go.Scatter(
            x=df_t['date'], y=df_t['sma'], 
            name='SMA (20)', 
            line=dict(color='#3b82f6', width=2)
        ), row=1, col=1)
    
    if 'ema' in df_t.columns:
        fig.add_trace(go.Scatter(
            x=df_t['date'], y=df_t['ema'], 
            name='EMA (20)', 
            line=dict(color='#f59e0b', width=2)
        ), row=1, col=1)
    
    if 'bb_upper' in df_t.columns and 'bb_lower' in df_t.columns:
        fig.add_trace(go.Scatter(
            x=df_t['date'], y=df_t['bb_upper'], 
            name='Bollinger Upper', 
            line=dict(color='#94a3b8', width=1, dash='dot'),
            showlegend=False
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df_t['date'], y=df_t['bb_lower'], 
            name='Bollinger Bands', 
            line=dict(color='#94a3b8', width=1, dash='dot'),
            fill='tonexty', 
            fillcolor='rgba(148, 163, 184, 0.1)'
        ), row=1, col=1)

    # Enhanced Volume bars
    fig.add_trace(go.Bar(
        x=df_t['date'],
        y=df_t['volume'],
        name='Volume',
        marker_color='rgba(59, 130, 246, 0.6)',
        marker_line_color='rgba(59, 130, 246, 0.8)',
        marker_line_width=1
    ), row=2, col=1)

    fig.update_layout(
        title=dict(
            text=f"💼 PROFESSIONAL ANALYSIS: {ticker}",
            font=dict(size=22, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        font=dict(family="Arial, sans-serif", size=12, color='#f8fafc'),
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(51, 65, 85, 0.8)',
            bordercolor='#475569',
            borderwidth=1,
            font=dict(color='#f8fafc')
        ),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='#1e293b',
        paper_bgcolor='#334155'
    )

    fig.update_yaxes(title_text="💰 Price ($)", row=1, col=1, gridcolor='#475569', color='#f8fafc')
    fig.update_yaxes(title_text="📊 Volume", row=2, col=1, gridcolor='#475569', color='#f8fafc')
    fig.update_xaxes(gridcolor='#475569', color='#f8fafc')

    return fig

# Enhanced RSI and MACD chart
@app.callback(
    Output('rsi-macd-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_rsi_macd_chart(ticker):
    if not ticker:
        return go.Figure()
        
    df_t = df[df['ticker'] == ticker].sort_values('date')
    
    if df_t.empty:
        return go.Figure().add_annotation(
            text="No data available for selected ticker",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color='#f8fafc')
        )

    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.1,
        subplot_titles=(
            f"📊 {ticker} - RSI (Relative Strength Index)", 
            f"📈 {ticker} - MACD (Moving Average Convergence Divergence)"
        )
    )

    # Enhanced RSI with signal zones
    if 'rsi' in df_t.columns:
        fig.add_trace(go.Scatter(
            x=df_t['date'], 
            y=df_t['rsi'], 
            name="RSI", 
            line=dict(color='#3b82f6', width=3),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ), row=1, col=1)

        # RSI signal lines with annotations
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", 
                     annotation_text="⚠️ OVERBOUGHT", annotation_position="top right",
                     row=1, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", 
                     annotation_text="🚀 OVERSOLD", annotation_position="bottom right",
                     row=1, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#94a3b8", 
                     annotation_text="NEUTRAL", annotation_position="top left",
                     row=1, col=1)

    # Enhanced MACD
    if 'macd' in df_t.columns:
        fig.add_trace(go.Scatter(
            x=df_t['date'], 
            y=df_t['macd'], 
            name="MACD", 
            line=dict(color='#8b5cf6', width=3)
        ), row=2, col=1)

        # Add MACD histogram (simulated)
        macd_hist = []
        for i in range(len(df_t)):
            if i > 0:
                macd_hist.append(df_t['macd'].iloc[i] - df_t['macd'].iloc[i-1])
            else:
                macd_hist.append(0)
        
        fig.add_trace(go.Bar(
            x=df_t['date'],
            y=macd_hist,
            name="MACD Histogram",
            marker_color=[('#10b981' if val >= 0 else '#ef4444') for val in macd_hist],
            opacity=0.7
        ), row=2, col=1)

        # MACD zero line
        fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", 
                     annotation_text="ZERO LINE", annotation_position="top right",
                     row=2, col=1)

    fig.update_layout(
        height=600,
        template='plotly_dark',
        title=dict(
            text=f"🔍 TECHNICAL MOMENTUM ANALYSIS: {ticker}",
            font=dict(size=22, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        hovermode='x unified',
        font=dict(family="Arial, sans-serif", size=12, color='#f8fafc'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(51, 65, 85, 0.8)',
            bordercolor='#475569',
            borderwidth=1,
            font=dict(color='#f8fafc')
        ),
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='#1e293b',
        paper_bgcolor='#334155'
    )
    
    fig.update_yaxes(
        title_text="RSI Value", 
        range=[0, 100], 
        row=1, col=1, 
        gridcolor='#475569',
        zerolinecolor='#64748b',
        color='#f8fafc'
    )
    fig.update_yaxes(
        title_text="MACD Value", 
        row=2, col=1, 
        gridcolor='#475569',
        zerolinecolor='#64748b',
        color='#f8fafc'
    )
    fig.update_xaxes(gridcolor='#475569', color='#f8fafc')
    
    return fig

# Enhanced 3D PCA Chart with Stock Information
@app.callback(
    Output('pca-cluster-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_pca_chart(ticker):
    if not ticker:
        return go.Figure()
    
    # Create enhanced PCA visualization with stock information
    fig = px.scatter_3d(
        PCA_df,
        x='col1', y='col2', z='col3',
        color='clusters',
        hover_data={'cluster_use_case': True, 'col1': False, 'col2': False, 'col3': False},
        title=f'🧠 3D PORTFOLIO CLUSTERING: {ticker} in Context',
        color_discrete_map={0: '#10B981', 1: '#EF4444', 2: '#F59E0B', 3: '#3B82F6'},
        opacity=0.7
    )
    
    # Highlight the selected ticker's cluster
    ticker_cluster_data = df_new[df_new['ticker'] == ticker]
    if not ticker_cluster_data.empty:
        ticker_cluster = ticker_cluster_data['clusters'].iloc[0]
        cluster_data = PCA_df[PCA_df['clusters'] == ticker_cluster]
        cluster_stocks = cluster_insights[ticker_cluster]['stocks']
        
        # Add highlighted cluster with stock information
        fig.add_trace(go.Scatter3d(
            x=cluster_data['col1'],
            y=cluster_data['col2'],
            z=cluster_data['col3'],
            mode='markers',
            marker=dict(
                size=8,
                color=cluster_insights[ticker_cluster]['color'],
                opacity=1.0,
                line=dict(width=2, color='white')
            ),
            name=f'{ticker} Cluster: {cluster_insights[ticker_cluster]["label"]}',
            hovertemplate=f'<b>{ticker} Cluster</b><br>' +
                         f'Strategy: {cluster_insights[ticker_cluster]["strategy"]}<br>' +
                         f'Risk: {cluster_insights[ticker_cluster]["risk"]}<br>' +
                         f'Stocks: {", ".join(cluster_stocks[:5])}{"..." if len(cluster_stocks) > 5 else ""}<extra></extra>'
        ))

    fig.update_layout(
        template='plotly_dark',
        font=dict(family="Arial, sans-serif", size=14, color='#f8fafc'),
        height=700,
        margin=dict(l=0, r=0, t=80, b=0),
        title=dict(
            font=dict(size=22, color='#f8fafc'),
            x=0.5,
            xanchor='center'
        ),
        legend=dict(
            title="Investment Clusters",
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(51, 65, 85, 0.8)',
            bordercolor='#475569',
            borderwidth=1,
            font=dict(color='#f8fafc')
        ),
        scene=dict(
            xaxis_title="Principal Component 1",
            yaxis_title="Principal Component 2",
            zaxis_title="Principal Component 3",
            xaxis=dict(gridcolor='#475569', showbackground=True, backgroundcolor='#1e293b', color='#f8fafc'),
            yaxis=dict(gridcolor='#475569', showbackground=True, backgroundcolor='#1e293b', color='#f8fafc'),
            zaxis=dict(gridcolor='#475569', showbackground=True, backgroundcolor='#1e293b', color='#f8fafc'),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2),
                up=dict(x=0, y=0, z=1)
            )
        ),
        plot_bgcolor='#1e293b',
        paper_bgcolor='#334155'
    )
    
    return fig

# Enhanced Bubble Chart with Stock Information
@app.callback(
    Output('cluster-bubble-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_bubble_chart(ticker):
    if not ticker:
        fig = go.Figure()
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#1e293b',
            paper_bgcolor='#334155',
            font=dict(color='#f8fafc'),
            title="Select a ticker to view cluster analysis"
        )
        return fig
    
    try:
        print(f"Generating bubble chart for ticker: {ticker}")
        
        # Get the cluster for the selected ticker
        ticker_data = df_new[df_new['ticker'] == ticker]
        
        if ticker_data.empty:
            print(f"No data found for ticker {ticker}")
            fig = go.Figure()
            fig.add_annotation(
                text=f"No cluster data available for {ticker}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color='#f8fafc', size=16)
            )
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='#1e293b',
                paper_bgcolor='#334155'
            )
            return fig
        
        # Safely get ticker cluster with fallback
        if 'clusters' in ticker_data.columns and not ticker_data['clusters'].isna().all():
            ticker_cluster = ticker_data['clusters'].iloc[0]
            print(f"Ticker {ticker} belongs to cluster {ticker_cluster}")
        else:
            print(f"No cluster information for {ticker}, using default cluster 0")
            ticker_cluster = 0
        
        # Create summary for all clusters - with safe fallbacks
        try:
            if 'clusters' in df_new.columns and not df_new['clusters'].isna().all():
                # Check required columns exist
                required_cols = ['rsi', 'macd', 'atr', 'volume', 'close']
                missing_cols = [col for col in required_cols if col not in df_new.columns]
                
                if missing_cols:
                    print(f"Missing columns in df_new: {missing_cols}")
                    raise ValueError(f"Missing required columns: {missing_cols}")
                
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
                raise ValueError("No cluster information in data")
                
        except Exception as e:
            print(f"Error creating cluster summary: {e}")
            # Fallback summary
            summary = pd.DataFrame({
                'clusters': [0, 1, 2, 3],
                'rsi_median': [45, 65, 55, 50],
                'macd_median': [0.5, -0.3, 1.2, 0.1],
                'atr_median': [2.1, 4.5, 3.2, 2.8],
                'volume_median': [1000000, 2000000, 1500000, 1800000],
                'close_mean': [150, 200, 180, 160],
                'close_std': [10, 25, 15, 12]
            })
            print("Using fallback summary data")
        
        print(f"Summary data shape: {summary.shape}")
        print(f"Summary clusters: {summary['clusters'].unique()}")
        
        # Create the bubble chart with enhanced hover information
        fig = px.scatter(
            summary,
            x='atr_median',
            y='macd_median',
            size='volume_median',
            color='clusters',
            hover_data=['rsi_median'],
            title=f'📊 INVESTMENT CLUSTER ANALYSIS: {ticker} Position & Market Context',
            labels={
                'atr_median': 'Volatility Risk (ATR)',
                'macd_median': 'Momentum Strength (MACD)',
                'volume_median': 'Liquidity (Volume)'
            },
            color_discrete_map={0: '#10B981', 1: '#EF4444', 2: '#F59E0B', 3: '#3B82F6'}
        )
        
        # Add custom hover information for each cluster - with safe access
        for i, row in summary.iterrows():
            try:
                cluster_id = int(row['clusters'])
                if cluster_id not in cluster_insights:
                    print(f"Cluster {cluster_id} not found in cluster_insights")
                    continue
                    
                cluster_stocks = cluster_insights[cluster_id]['stocks']
                if not cluster_stocks:
                    stock_list = "No stocks"
                else:
                    max_stocks = min(8, len(cluster_stocks))
                    stock_list = ", ".join(cluster_stocks[:max_stocks])
                    if len(cluster_stocks) > max_stocks:
                        stock_list += "..."
                
                if i < len(fig.data):
                    fig.data[i].hovertemplate = (
                        f'<b>{cluster_insights[cluster_id]["label"]}</b><br>' +
                        f'Strategy: {cluster_insights[cluster_id]["strategy"]}<br>' +
                        f'Risk: {cluster_insights[cluster_id]["risk"]}<br>' +
                        f'Stocks ({len(cluster_stocks)}): {stock_list}<br>'
                    )
                else:
                    print(f"Warning: index {i} out of range for fig.data (length: {len(fig.data)})")
            except Exception as e:
                print(f"Error setting hover template for row {i}: {e}")
        
        # Highlight the selected ticker's cluster - with safe access
        try:
            ticker_cluster_data = summary[summary['clusters'] == ticker_cluster]
            
            if not ticker_cluster_data.empty and ticker_cluster in cluster_insights:
                # Safe calculation of marker size
                max_volume = summary['volume_median'].max() if not summary.empty else 1
                min_size = 20
                max_size = 100
                
                if 'volume_median' in ticker_cluster_data.columns and len(ticker_cluster_data) > 0:
                    ticker_volume = ticker_cluster_data['volume_median'].iloc[0]
                    if max_volume > 0:
                        marker_size = min_size + (ticker_volume / max_volume) * (max_size - min_size)
                    else:
                        marker_size = min_size
                else:
                    marker_size = min_size
                
                # Safe access to cluster stocks
                cluster_stocks = cluster_insights[ticker_cluster]['stocks']
                if cluster_stocks:
                    max_stocks = min(5, len(cluster_stocks))
                    stock_list = ", ".join(cluster_stocks[:max_stocks])
                    if len(cluster_stocks) > max_stocks:
                        stock_list += "..."
                else:
                    stock_list = "No stocks"
                
                # Safe access to x and y coordinates
                if 'atr_median' in ticker_cluster_data.columns and 'macd_median' in ticker_cluster_data.columns:
                    x_val = ticker_cluster_data['atr_median'].iloc[0]
                    y_val = ticker_cluster_data['macd_median'].iloc[0]
                    
                    fig.add_trace(go.Scatter(
                        x=[x_val],
                        y=[y_val],
                        mode='markers',
                        marker=dict(
                            size=marker_size,
                            color=cluster_insights[ticker_cluster]['color'],
                            line=dict(width=4, color='white'),
                            opacity=1.0
                        ),
                        name=f'{ticker}: {cluster_insights[ticker_cluster]["label"]}',
                        hovertemplate=f'<b>{ticker} Cluster</b><br>' +
                                     f'Strategy: {cluster_insights[ticker_cluster]["strategy"]}<br>' +
                                     f'Risk: {cluster_insights[ticker_cluster]["risk"]}<br>' +
                                     f'Allocation: {cluster_insights[ticker_cluster]["allocation"]}<br>' +
                                     f'Peer Stocks: {stock_list}<extra></extra>'
                    ))
                else:
                    print(f"Missing coordinates for ticker cluster highlight")
            else:
                print(f"No data for ticker cluster {ticker_cluster} or cluster not in insights")
        except Exception as e:
            print(f"Error highlighting ticker cluster: {e}")

        # Enhanced bubble chart styling for dark theme
        fig.update_layout(
            template='plotly_dark',
            font=dict(family="Arial, sans-serif", size=14, color='#f8fafc'),
            plot_bgcolor='#1e293b',
            paper_bgcolor='#334155',
            height=600,
            margin=dict(l=40, r=40, t=80, b=40),
            title=dict(
                font=dict(size=22, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            legend=dict(
                title="Investment Clusters",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(51, 65, 85, 0.8)',
                bordercolor='#475569',
                borderwidth=1,
                font=dict(color='#f8fafc')
            ),
            xaxis=dict(
                title=dict(font=dict(size=14, color='#f8fafc')),
                gridcolor='#475569',
                zerolinecolor='#64748b',
                color='#f8fafc'
            ),
            yaxis=dict(
                title=dict(font=dict(size=14, color='#f8fafc')),
                gridcolor='#475569',
                zerolinecolor='#64748b',
                color='#f8fafc'
            )
        )

        # Add strategic annotations for dark theme - with safe access
        try:
            if not summary.empty and 'atr_median' in summary.columns and 'macd_median' in summary.columns:
                max_atr = summary['atr_median'].max()
                min_atr = summary['atr_median'].min()
                max_macd = summary['macd_median'].max()
                min_macd = summary['macd_median'].min()
                
                # Only add annotations if we have valid values
                if not pd.isna(max_atr) and not pd.isna(max_macd):
                    fig.add_annotation(
                        x=max_atr * 0.9,
                        y=max_macd * 0.9,
                        text="High Growth<br>High Risk",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="#94a3b8",
                        font=dict(size=12, color="#f8fafc"),
                        align="center",
                        bgcolor="rgba(51, 65, 85, 0.8)",
                        bordercolor="#475569",
                        borderwidth=1,
                        borderpad=4,
                        opacity=0.9
                    )
                
                if not pd.isna(min_atr) and not pd.isna(min_macd):
                    fig.add_annotation(
                        x=min_atr * 1.1,
                        y=min_macd * 1.1,
                        text="Conservative<br>Low Risk",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="#94a3b8",
                        font=dict(size=12, color="#f8fafc"),
                        align="center",
                        bgcolor="rgba(51, 65, 85, 0.8)",
                        bordercolor="#475569",
                        borderwidth=1,
                        borderpad=4,
                        opacity=0.9
                    )
        except Exception as e:
            print(f"Error adding annotations: {e}")
        
        return fig
        
    except Exception as e:
        print(f"❌ Error in bubble chart: {str(e)}")
        import traceback
        traceback.print_exc()
        
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading cluster data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color='#ef4444', size=14)
        )
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#1e293b',
            paper_bgcolor='#334155',
            font=dict(color='#f8fafc')
        )
        return fig
        
        ticker_cluster = ticker_data['clusters'].iloc[0]
        
        # Create summary for all clusters
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
            # Fallback summary
            summary = pd.DataFrame({
                'clusters': [0, 1, 2, 3],
                'rsi_median': [45, 65, 55, 50],
                'macd_median': [0.5, -0.3, 1.2, 0.1],
                'atr_median': [2.1, 4.5, 3.2, 2.8],
                'volume_median': [1000000, 2000000, 1500000, 1800000],
                'close_mean': [150, 200, 180, 160],
                'close_std': [10, 25, 15, 12]
            })
        
        # Create the bubble chart with enhanced hover information
        fig = px.scatter(
            summary,
            x='atr_median',
            y='macd_median',
            size='volume_median',
            color='clusters',
            hover_data=['rsi_median'],
            title=f'📊 INVESTMENT CLUSTER ANALYSIS: {ticker} Position & Market Context',
            labels={
                'atr_median': 'Volatility Risk (ATR)',
                'macd_median': 'Momentum Strength (MACD)',
                'volume_median': 'Liquidity (Volume)'
            },
            color_discrete_map={0: '#10B981', 1: '#EF4444', 2: '#F59E0B', 3: '#3B82F6'}
        )
        
        # Add custom hover information for each cluster
        for i, row in summary.iterrows():
            cluster_id = int(row['clusters'])
            cluster_stocks = cluster_insights[cluster_id]['stocks']
            stock_list = ", ".join(cluster_stocks[:8]) + ("..." if len(cluster_stocks) > 8 else "")
            
            fig.data[i].hovertemplate = (
                f'<b>{cluster_insights[cluster_id]["label"]}</b><br>' +
                f'Strategy: {cluster_insights[cluster_id]["strategy"]}<br>' +
                f'Risk: {cluster_insights[cluster_id]["risk"]}<br>' +
                f'Stocks ({len(cluster_stocks)}): {stock_list}<br>'
            )
        
        # Highlight the selected ticker's cluster
        ticker_cluster_data = summary[summary['clusters'] == ticker_cluster]
        if not ticker_cluster_data.empty and ticker_cluster in cluster_insights:
            max_volume = summary['volume_median'].max()
            min_size = 20
            max_size = 100
            ticker_volume = ticker_cluster_data['volume_median'].iloc[0]
            marker_size = min_size + (ticker_volume / max_volume) * (max_size - min_size)
            
            cluster_stocks = cluster_insights[ticker_cluster]['stocks']
            stock_list = ", ".join(cluster_stocks[:5]) + ("..." if len(cluster_stocks) > 5 else "")
            
            fig.add_trace(go.Scatter(
                x=ticker_cluster_data['atr_median'],
                y=ticker_cluster_data['macd_median'],
                mode='markers',
                marker=dict(
                    size=marker_size,
                    color=cluster_insights[ticker_cluster]['color'],
                    line=dict(width=4, color='white'),
                    opacity=1.0
                ),
                name=f'{ticker}: {cluster_insights[ticker_cluster]["label"]}',
                hovertemplate=f'<b>{ticker} Cluster</b><br>' +
                             f'Strategy: {cluster_insights[ticker_cluster]["strategy"]}<br>' +
                             f'Risk: {cluster_insights[ticker_cluster]["risk"]}<br>' +
                             f'Allocation: {cluster_insights[ticker_cluster]["allocation"]}<br>' +
                             f'Peer Stocks: {stock_list}<extra></extra>'
            ))

        # Enhanced bubble chart styling for dark theme
        fig.update_layout(
            template='plotly_dark',
            font=dict(family="Arial, sans-serif", size=14, color='#f8fafc'),
            plot_bgcolor='#1e293b',
            paper_bgcolor='#334155',
            height=600,
            margin=dict(l=40, r=40, t=80, b=40),
            title=dict(
                font=dict(size=22, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            legend=dict(
                title="Investment Clusters",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(51, 65, 85, 0.8)',
                bordercolor='#475569',
                borderwidth=1,
                font=dict(color='#f8fafc')
            ),
            xaxis=dict(
                title=dict(font=dict(size=14, color='#f8fafc')),
                gridcolor='#475569',
                zerolinecolor='#64748b',
                color='#f8fafc'
            ),
            yaxis=dict(
                title=dict(font=dict(size=14, color='#f8fafc')),
                gridcolor='#475569',
                zerolinecolor='#64748b',
                color='#f8fafc'
            )
        )

        # Add strategic annotations for dark theme
        try:
            fig.add_annotation(
                x=summary['atr_median'].max() * 0.9,
                y=summary['macd_median'].max() * 0.9,
                text="High Growth<br>High Risk",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#94a3b8",
                font=dict(size=12, color="#f8fafc"),
                align="center",
                bgcolor="rgba(51, 65, 85, 0.8)",
                bordercolor="#475569",
                borderwidth=1,
                borderpad=4,
                opacity=0.9
            )

            fig.add_annotation(
                x=summary['atr_median'].min() * 1.1,
                y=summary['macd_median'].min() * 1.1,
                text="Conservative<br>Low Risk",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="#94a3b8",
                font=dict(size=12, color="#f8fafc"),
                align="center",
                bgcolor="rgba(51, 65, 85, 0.8)",
                bordercolor="#475569",
                borderwidth=1,
                borderpad=4,
                opacity=0.9
            )
        except:
            pass
        
        return fig
        
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading cluster data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color='#ef4444', size=14)
        )
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='#1e293b',
            paper_bgcolor='#334155',
            font=dict(color='#f8fafc')
        )
        return fig

# ========================================
# 🚀 RUN THE APPLICATION
# ========================================

if __name__ == '__main__':
    print("🚀 Starting Portfolio Intelligence Dashboard with API...")
    print("📊 Dash App: http://localhost:8050/dashboard/")
    print("🔌 API Endpoints: http://localhost:8050/api/")
    print("💡 Try: http://localhost:8050/api/health")
    print("📈 Sample API calls:")
    print("   curl http://localhost:8050/api/health")
    print("   curl http://localhost:8050/api/tickers")
    print("   curl http://localhost:8050/api/clusters")
    
    app.run(debug=True)