import yfinance as yf
from datetime import datetime

def check_qqq():
    print("Fetching QQQ data...")
    try:
        # Fetch data from late 2025 to present
        qqq = yf.Ticker("QQQ")
        hist = qqq.history(start="2025-10-01", end="2026-01-09")
        
        if not hist.empty:
            high_price = hist['High'].max()
            last_price = hist['Close'].iloc[-1]
            last_date = hist.index[-1]
            
            print(f"✅ Data fetched successfully!")
            print(f"Latest Date: {last_date.date()}")
            print(f"Latest Price: {last_price:.2f}")
            print(f"Period High: {high_price:.2f}")
            return True
        else:
            print("❌ No data returned")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return False

if __name__ == "__main__":
    check_qqq()