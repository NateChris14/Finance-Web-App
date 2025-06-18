import requests

BASE = "http://localhost:8050/api"

def test_health():
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "total_records" in data["data_info"]
    assert "total_tickers" in data["data_info"]

def test_tickers():
    r = requests.get(f"{BASE}/tickers")
    assert r.status_code == 200
    data = r.json()
    assert "tickers" in data
    assert isinstance(data["tickers"], list)
    assert data["count"] == len(data["tickers"])
    # Use a sample ticker for further tests
    global SAMPLE_TICKER
    SAMPLE_TICKER = data["tickers"][0] if data["tickers"] else None

def test_stock_summary():
    if not globals().get("SAMPLE_TICKER"):
        test_tickers()
    ticker = globals()["SAMPLE_TICKER"]
    r = requests.get(f"{BASE}/stock/{ticker}/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == ticker
    assert "metrics" in data
    assert "cluster" in data

def test_chart_data():
    if not globals().get("SAMPLE_TICKER"):
        test_tickers()
    ticker = globals()["SAMPLE_TICKER"]
    r = requests.get(f"{BASE}/stock/{ticker}/chart-data")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == ticker
    assert "data" in data
    assert "dates" in data["data"]

def test_technical_data():
    if not globals().get("SAMPLE_TICKER"):
        test_tickers()
    ticker = globals()["SAMPLE_TICKER"]
    r = requests.get(f"{BASE}/stock/{ticker}/technical")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == ticker
    assert "timeseries" in data
    assert "current" in data

def test_clusters():
    r = requests.get(f"{BASE}/clusters")
    assert r.status_code == 200
    data = r.json()
    assert "clusters" in data
    assert "total_clusters" in data

def test_clusters_pca():
    r = requests.get(f"{BASE}/clusters/pca")
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert "count" in data

def test_invalid_ticker_summary():
    r = requests.get(f"{BASE}/stock/INVALID_TICKER/summary")
    assert r.status_code == 404 or r.status_code == 200
    data = r.json()
    assert "error" in data

def test_invalid_ticker_chart_data():
    r = requests.get(f"{BASE}/stock/INVALID_TICKER/chart-data")
    assert r.status_code == 404 or r.status_code == 200
    data = r.json()
    assert "error" in data

def test_invalid_ticker_technical():
    r = requests.get(f"{BASE}/stock/INVALID_TICKER/technical")
    assert r.status_code == 404 or r.status_code == 200
    data = r.json()
    assert "error" in data 