import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from models import BacktestResult
from trading_engine import TradingEngine, run_backtest
from data_service import get_historical_data

def calculate_performance_metrics(equity_curve: List[Tuple[datetime, float]], 
                                 initial_capital: float) -> Dict:
    """Calculate performance metrics from equity curve"""
    dates = [x[0] for x in equity_curve]
    values = [x[1] for x in equity_curve]
    
    # Calculate returns
    returns = pd.Series(values).pct_change().dropna()
    
    # Basic metrics
    total_return = (values[-1] / initial_capital) - 1
    
    # Annualized return
    days_in_period = (dates[-1] - dates[0]).days
    annualized_return = (1 + total_return) ** (365.25 / days_in_period) - 1
    
    # Max drawdown
    peak = np.maximum.accumulate(values)
    drawdown = (values - peak) / peak
    max_drawdown = np.min(drawdown)
    
    # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
    sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 else 0
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'final_value': values[-1]
    }

def run_comprehensive_backtest(start_date: str, end_date: str, 
                              initial_capital: float = 100000.0) -> BacktestResult:
    """Run comprehensive backtest with full analysis"""
    
    # Convert string dates to datetime
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Run the backtest
    results = run_backtest(start_dt, end_dt, initial_capital)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(results['equity_curve'], initial_capital)
    
    # Create final result object
    return BacktestResult(
        initial_capital=initial_capital,
        final_portfolio_value=metrics['final_value'],
        total_return=metrics['total_return'],
        annualized_return=metrics['annualized_return'],
        max_drawdown=metrics['max_drawdown'],
        sharpe_ratio=metrics['sharpe_ratio'],
        trades_executed=len(results['trades_executed']),
        start_date=start_dt,
        end_date=end_dt,
        equity_curve=results['equity_curve'],
        portfolio_snapshots=results['portfolio_snapshots']
    )

def plot_equity_curve(backtest_result: BacktestResult, benchmark_symbol: str = "QQQ"):
    """Plot equity curve compared to benchmark"""
    
    # Extract equity curve data
    dates = [x[0] for x in backtest_result.equity_curve]
    portfolio_values = [x[1] for x in backtest_result.equity_curve]
    
    # Get benchmark data
    benchmark_data = get_historical_data(
        benchmark_symbol, 
        dates[0].strftime('%Y-%m-%d'), 
        dates[-1].strftime('%Y-%m-%d')
    )
    
    # Normalize benchmark to same scale
    benchmark_normalized = benchmark_data['Close'] / benchmark_data['Close'].iloc[0] * backtest_result.initial_capital
    
    # Create plot
    plt.figure(figsize=(12, 8))
    
    # Plot portfolio equity curve
    plt.plot(dates, portfolio_values, label='Portfolio', linewidth=2, color='blue')
    
    # Plot benchmark
    plt.plot(benchmark_data.index, benchmark_normalized, label=benchmark_symbol, linewidth=2, color='gray', alpha=0.7)
    
    # Formatting
    plt.title('Portfolio Performance vs Benchmark')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # Add performance metrics text
    metrics_text = f"""Annualized Return: {backtest_result.annualized_return:.2%}
Total Return: {backtest_result.total_return:.2%}
Max Drawdown: {backtest_result.max_drawdown:.2%}
Sharpe Ratio: {backtest_result.sharpe_ratio:.2f}
Trades: {backtest_result.trades_executed}"""
    
    plt.annotate(metrics_text, xy=(0.02, 0.98), xycoords='axes fraction', 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    return plt

def generate_trade_summary(backtest_result: BacktestResult) -> pd.DataFrame:
    """Generate summary of all trades executed"""
    trades_data = []
    
    for trade in backtest_result.trades_executed:
        trades_data.append({
            'Date': trade.timestamp,
            'Symbol': trade.symbol,
            'Type': trade.option_type.value,
            'Action': trade.action,
            'Strike': trade.strike,
            'Premium': trade.premium,
            'Quantity': trade.quantity,
            'Expiration': trade.expiration
        })
    
    return pd.DataFrame(trades_data)

def analyze_strategy_performance(start_date: str, end_date: str, initial_capital: float = 100000.0):
    """Complete analysis of strategy performance"""
    
    print(f"Running backtest from {start_date} to {end_date}...")
    
    # Run backtest
    result = run_comprehensive_backtest(start_date, end_date, initial_capital)
    
    # Display results
    print("\n" + "="*60)
    print("STRATEGY PERFORMANCE SUMMARY")
    print("="*60)
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${result.initial_capital:,.2f}")
    print(f"Final Portfolio Value: ${result.final_portfolio_value:,.2f}")
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Annualized Return: {result.annualized_return:.2%}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Trades Executed: {result.trades_executed}")
    
    # Generate trade summary
    trade_df = generate_trade_summary(result)
    if not trade_df.empty:
        print("\nTRADE SUMMARY:")
        print("-" * 40)
        print(f"Total Trades: {len(trade_df)}")
        print(f"Put Trades: {len(trade_df[trade_df['Type'] == 'put'])}")
        print(f"Call Trades: {len(trade_df[trade_df['Type'] == 'call'])}")
        print(f"Total Premium Collected: ${trade_df['Premium'].sum():,.2f}")
    
    # Plot equity curve
    plot = plot_equity_curve(result)
    plot.show()
    
    return result

# Example usage
def main():
    """Example main function to run backtest"""
    # Test with a recent 1-year period
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    result = analyze_strategy_performance(start_date, end_date)
    
    return result

if __name__ == "__main__":
    main()