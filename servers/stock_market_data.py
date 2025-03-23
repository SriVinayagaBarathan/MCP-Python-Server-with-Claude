from typing import Any, List, Dict, Optional
import httpx
from mcp.server.fastmcp import FastMCP
import json
from datetime import datetime, timedelta

# Initialize FastMCP server
mcp = FastMCP("stock_market")

# Constants
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
USER_AGENT = "stock-app/1.0"

# You would need to replace this with a real API key in production
ALPHA_VANTAGE_API_KEY = "E6DGI4VIHP8A25RY"  # Using demo key for this example

async def make_alpha_vantage_request(function: str, symbol: str, **kwargs) -> dict[str, Any] | None:
    """Make a request to the Alpha Vantage API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT
    }
    
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        **kwargs
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ALPHA_VANTAGE_BASE_URL, 
                                        headers=headers, 
                                        params=params, 
                                        timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def format_quote(data: dict) -> str:
    """Format stock quote data into a readable string."""
    if "Global Quote" not in data or not data["Global Quote"]:
        return "No quote data available."
    
    quote = data["Global Quote"]
    return f"""
Symbol: {quote.get('01. symbol', 'Unknown')}
Price: ${quote.get('05. price', 'Unknown')}
Change: {quote.get('09. change', 'Unknown')} ({quote.get('10. change percent', 'Unknown')})
Volume: {quote.get('06. volume', 'Unknown')}
Last Trading Day: {quote.get('07. latest trading day', 'Unknown')}
"""

@mcp.tool()
async def get_stock_quote(symbol: str) -> str:
    """Get the latest stock quote for a symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
    """
    data = await make_alpha_vantage_request("GLOBAL_QUOTE", symbol)
    
    if "error" in data:
        return f"Error fetching stock quote: {data['error']}"
    
    return format_quote(data)

@mcp.tool()
async def get_stock_history(symbol: str, days: int = 7) -> str:
    """Get historical stock data for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        days: Number of days of history to retrieve (default: 7, max: 100)
    """
    # Limit days to a reasonable maximum
    days = min(days, 100)
    
    data = await make_alpha_vantage_request("TIME_SERIES_DAILY", 
                                           symbol, 
                                           outputsize="compact")
    
    if "error" in data:
        return f"Error fetching stock history: {data['error']}"
    
    if "Time Series (Daily)" not in data:
        return "No historical data available."
    
    time_series = data["Time Series (Daily)"]
    
    # Sort dates in descending order and limit to requested days
    sorted_dates = sorted(time_series.keys(), reverse=True)[:days]
    
    result = f"Historical data for {symbol} (last {len(sorted_dates)} days):\n\n"
    
    for date in sorted_dates:
        daily_data = time_series[date]
        result += f"""
Date: {date}
Open: ${daily_data.get('1. open', 'Unknown')}
High: ${daily_data.get('2. high', 'Unknown')}
Low: ${daily_data.get('3. low', 'Unknown')}
Close: ${daily_data.get('4. close', 'Unknown')}
Volume: {daily_data.get('5. volume', 'Unknown')}
"""
        result += "\n---\n"
    
    return result

@mcp.tool()
async def search_stocks(keywords: str) -> str:
    """Search for stocks matching the provided keywords.
    
    Args:
        keywords: Search terms to find matching stocks
    """
    data = await make_alpha_vantage_request("SYMBOL_SEARCH", 
                                           "NONE", 
                                           keywords=keywords)
    
    if "error" in data:
        return f"Error searching stocks: {data['error']}"
    
    if "bestMatches" not in data or not data["bestMatches"]:
        return "No matching stocks found."
    
    matches = data["bestMatches"]
    result = f"Found {len(matches)} stocks matching '{keywords}':\n\n"
    
    for stock in matches:
        result += f"""
Symbol: {stock.get('1. symbol', 'Unknown')}
Name: {stock.get('2. name', 'Unknown')}
Type: {stock.get('3. type', 'Unknown')}
Region: {stock.get('4. region', 'Unknown')}
Currency: {stock.get('8. currency', 'Unknown')}
"""
        result += "\n---\n"
    
    return result

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')