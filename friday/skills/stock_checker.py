import requests
from langchain.tools import tool

@tool("stock_market_checker")
def stock_market_checker(symbol: str) -> str:
    """
    Fetches real-time stock price and market data for a given ticker symbol (e.g. 'AAPL', 'MSFT', 'TSLA').
    Input: stock ticker symbol.
    """
    clean_symbol = symbol.strip().upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_symbol}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code != 200:
            return f"Could not find stock data for ticker '{clean_symbol}'."
            
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return f"No results returned for ticker '{clean_symbol}'."
            
        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("previousClose")
        currency = meta.get("currency", "USD")
        
        if price is None:
            return f"Data for '{clean_symbol}' is currently unavailable."
            
        change_str = ""
        if prev_close:
            change = price - prev_close
            change_percent = (change / prev_close) * 100
            sign = "+" if change >= 0 else ""
            change_str = f" ({sign}{change:.2f}, {sign}{change_percent:.2f}%)"
            
        return f"{clean_symbol}: {price:.2f} {currency}{change_str}."
        
    except Exception as e:
        return f"Stock lookup failed: {e}"
