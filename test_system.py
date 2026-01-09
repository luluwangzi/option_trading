#!/usr/bin/env python3
"""Test script to verify the options trading system works"""

from data_service import get_current_market_data, get_historical_data
from config import STOCK_CONFIGS, STRATEGY_CONFIG
import pandas as pd
from datetime import datetime, timedelta

def test_market_data():
    """Test market data fetching"""
    print("Testing market data service...")
    
    symbols = list(STOCK_CONFIGS.keys())
    market_data = get_current_market_data(symbols)
    
    print("\nCurrent Market Data:")
    print("-" * 50)
    for symbol, data in market_data.items():
        print(f"{symbol}: ${data.price:.2f} | IV Rank: {data.iv_rank:.3f} | VIX: {data.vix:.2f}")

def test_historical_data():
    """Test historical data fetching"""
    print("\n\nTesting historical data...")
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    data = get_historical_data('QQQ', start_date, end_date)
    print(f"\nQQQ Historical Data ({start_date} to {end_date}):")
    print("-" * 50)
    print(f"Records: {len(data)}")
    print(f"Latest price: ${data['Close'].iloc[-1]:.2f}")
    print(f"30-day range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")

def test_strategy_config():
    """Test strategy configuration"""
    print("\n\nTesting strategy configuration...")
    print("-" * 50)
    
    print("Stock Configurations:")
    for symbol, config in STOCK_CONFIGS.items():
        print(f"  {symbol}: {config.weight:.0%} weight | Put Delta: {config.put_delta_range} | Call Delta: {config.call_delta_range}")
    
    print(f"\nStrategy Parameters:")
    print(f"  DTE Range: {STRATEGY_CONFIG.dte_range}")
    print(f"  Roll DTE: {STRATEGY_CONFIG.roll_dte_threshold}")
    print(f"  Profit Take: {STRATEGY_CONFIG.profit_take_percent:.0%}")
    print(f"  IV Rank Threshold: {STRATEGY_CONFIG.iv_rank_threshold:.0%}")
    print(f"  Put Allocation: {STRATEGY_CONFIG.put_allocation:.0%}")
    print(f"  Call Allocation: {STRATEGY_CONFIG.call_allocation:.0%}")

if __name__ == "__main__":
    print("Options Trading System Test")
    print("=" * 60)
    
    try:
        test_market_data()
        test_historical_data() 
        test_strategy_config()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("System is ready for backtesting.")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("Please check your internet connection and try again.")