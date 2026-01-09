#!/usr/bin/env python3
"""
Options Trading Strategy Backtester
Automated implementation of the NVDA/GOOGL/TSLA/QQQ options strategy
"""

import argparse
from datetime import datetime, timedelta
from backtester import analyze_strategy_performance
from trading_engine import TradingEngine

def run_strategy():
    """Main function to run the options trading strategy"""
    
    parser = argparse.ArgumentParser(description='Options Trading Strategy Backtester')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000.0, help='Initial capital')
    parser.add_argument('--symbols', nargs='+', default=['NVDA', 'GOOGL', 'TSLA', 'QQQ'], 
                       help='Stock symbols to trade')
    
    args = parser.parse_args()
    
    # Set default dates if not provided
    if not args.end_date:
        args.end_date = datetime.now().strftime('%Y-%m-%d')
    if not args.start_date:
        args.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    print("=" * 70)
    print("AUTOMATED OPTIONS TRADING STRATEGY BACKTESTER")
    print("=" * 70)
    print(f"Strategy: Cash-Secured Puts + Covered Calls")
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print("=" * 70)
    
    # Run the backtest
    try:
        result = analyze_strategy_performance(args.start_date, args.end_date, args.capital)
        
        # Display strategy details
        print("\nSTRATEGY CONFIGURATION:")
        print("-" * 40)
        print("• Cash-Secured Puts: 60% allocation")
        print("• Covered Calls: 40% allocation")
        print("• DTE Range: 30-45 days")
        print("• Roll at: 7-10 DTE")
        print("• Profit Take: 70% of premium")
        print("• IV Rank Threshold: < 80%")
        print("• Bear Market Rules: VIX > 35 or QQQ < 200D MA")
        
        return result
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        return None

def interactive_mode():
    """Interactive mode for running multiple backtests"""
    
    print("\nInteractive Backtesting Mode")
    print("-" * 30)
    
    while True:
        print("\nOptions:")
        print("1. Run 1-year backtest")
        print("2. Run 2-year backtest") 
        print("3. Custom date range")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            analyze_strategy_performance(start_date, end_date)
            
        elif choice == '2':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            analyze_strategy_performance(start_date, end_date)
            
        elif choice == '3':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            analyze_strategy_performance(start_date, end_date)
            
        elif choice == '4':
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # Run with command line arguments or interactive mode
    import sys
    
    if len(sys.argv) > 1:
        run_strategy()
    else:
        interactive_mode()