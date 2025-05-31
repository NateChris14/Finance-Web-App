import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
from src.utils import load_data,FeatureEngineer
from src.components.clustering.pipeline.predict_pipeline import PredictPipeline

# Load and preprocess data
columns = [
    "sd.ticker", "sd.date", "sd.open", "sd.high", "sd.low", "sd.close", "sd.volume",
    "ti.ticker", "ti.date", "ti.rsi", "ti.macd", "ti.sma", "ti.ema", "ti.atr", "ti.bb_upper", "ti.bb_middle", "ti.bb_lower"
]
df = pd.concat(load_data(join=True, chunksize=10000, columns=columns), ignore_index=True)
df = df.loc[:, ~df.columns.duplicated()]
df['date'] = pd.to_datetime(df['date'])
tickers = df['ticker'].unique()

#Performing feature engineering only to get the df with all features
df_copy = df.copy()
fe = FeatureEngineer()
df_new = fe.fit_transform(df_copy)

# Predict Clusters
PCA_df = PredictPipeline().predict_clusters(df)
df_new['clusters'] = PCA_df['clusters']

# Summarize clusters
summary = df_new.groupby('clusters').agg({
    'rsi': 'median',
    'macd': 'median',
    'atr': 'median',
    'volume': 'median',
    'rolling_volatility': 'median'  # Ensure this column exists in df
}).round(2).reset_index()

# Bubble chart figure
bubble_fig = px.scatter(
    summary,
    x='atr',
    y='macd',
    size='volume',
    color='clusters',
    hover_data=['rsi', 'rolling_volatility'],
    title='📊 Cluster Summary: Volatility vs Momentum',
    labels={
        'atr': 'ATR (Volatility Range)',
        'macd': 'MACD (Momentum)',
        'volume': 'Volume (Bubble Size)'
    },
    template='plotly_dark'
)

# Dash app
app = dash.Dash(__name__)
app.title = "Stock Dashboard"

# Layout
app.layout = html.Div(style={'backgroundColor': '#111111', 'color': '#ffffff', 'padding': '20px'}, children=[
    html.H1("Stock Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Select Ticker:", style={'fontSize': '20px'}),
        dcc.Dropdown(
            id='ticker-dropdown',
            options=[{'label': t, 'value': t} for t in tickers],
            value=tickers[0],
            style={'color': '#000'}
        )
    ], style={'width': '50%', 'margin': 'auto'}),

    dcc.Graph(id='candlestick-chart'),
    html.Hr(),

    dcc.Graph(id='rsi-macd-chart'),
    html.Hr(),

    html.H2("3D PCA Projection of Stock Data by Cluster", style={'textAlign': 'center'}),
    dcc.Graph(
        id='pca-cluster-chart',
        figure=px.scatter_3d(
            PCA_df,
            x='col1', y='col2', z='col3',
            color='clusters',
            hover_data=['clusters'],
            title='3D PCA Projection of Stock Data by Cluster',
            template='plotly_dark'
        )
    ),
    html.Hr(),

    html.H2("📊 Cluster Summary: Volatility vs Momentum", style={'textAlign': 'center'}),
    dcc.Graph(id='cluster-bubble-chart', figure=bubble_fig)
])

# Callbacks
@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_candlestick_chart(ticker):
    df_t = df[df['ticker'] == ticker].sort_values('date')

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_t['date'], open=df_t['open'], high=df_t['high'],
        low=df_t['low'], close=df_t['close'], name='OHLC'
    ))

    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['sma'], name='SMA', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['ema'], name='EMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')))
    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['bb_lower'], name='BB Lower',
                             line=dict(color='gray', dash='dot'), fill='tonexty', fillcolor='rgba(173,216,230,0.2)'))

    fig.update_layout(
        title=f"{ticker} Candlestick Chart with Indicators",
        template='plotly_dark',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

@app.callback(
    Output('rsi-macd-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_rsi_macd_chart(ticker):
    df_t = df[df['ticker'] == ticker].sort_values('date')

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
        subplot_titles=("RSI Timeline", "MACD Timeline")
    )

    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['rsi'], name="RSI", line=dict(color='royalblue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_t['date'], y=df_t['macd'], name="MACD", line=dict(color='purple')), row=2, col=1)

    fig.add_shape(type='line', x0=df_t['date'].min(), x1=df_t['date'].max(), y0=70, y1=70,
                  line=dict(color='gray', dash='dash'), row=1, col=1)
    fig.add_shape(type='line', x0=df_t['date'].min(), x1=df_t['date'].max(), y0=30, y1=30,
                  line=dict(color='gray', dash='dash'), row=1, col=1)

    fig.update_layout(
        height=600,
        template='plotly_dark',
        title=f"RSI and MACD for {ticker}",
        hovermode='x unified',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

# Run app
if __name__ == '__main__':
    app.run(debug=True)