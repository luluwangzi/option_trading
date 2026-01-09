import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtester import run_comprehensive_backtest
from quick_test import generate_simulation_results

st.set_page_config(page_title="Options Trading Backtester", layout="wide")

st.title("📈 Automated Options Trading Strategy")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Date inputs
start_date = st.sidebar.date_input(
    "Start Date",
    datetime.now() - timedelta(days=365)
)
end_date = st.sidebar.date_input(
    "End Date",
    datetime.now()
)

initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=1000,
    value=100000,
    step=1000
)

# Simulation mode toggle (due to API limits)
use_simulation = st.sidebar.checkbox("Use Simulation Mode (No API Calls)", value=True)

if st.sidebar.button("Run Backtest", type="primary"):
    with st.spinner("Running backtest..."):
        try:
            if use_simulation:
                st.warning("⚠️ SIMULATION MODE ACTIVE: The chart below uses generated RANDOM data for demonstration purposes. It does NOT reflect real historical market prices (e.g., QQQ price).")
                # Use simulation data
                dates, strategy_values, benchmark_values, _ = generate_simulation_results(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    initial_capital=initial_capital
                )
                
                # Filter by selected dates
                df = pd.DataFrame({
                    'Date': dates,
                    'Portfolio': strategy_values,
                    'Benchmark': benchmark_values
                })
                mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
                df = df.loc[mask]
                
                # Calculate metrics
                total_return = (df['Portfolio'].iloc[-1] / initial_capital - 1)
                days = (end_date - start_date).days
                annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Return", f"{total_return:.2%}")
                col2.metric("Annualized Return", f"{annualized_return:.2%}")
                col3.metric("Final Value", f"${df['Portfolio'].iloc[-1]:,.2f}")
                
                # Plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['Date'], y=df['Portfolio'], name='Portfolio', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=df['Date'], y=df['Benchmark'], name='Benchmark (QQQ)', line=dict(color='gray', dash='dash')))
                
                fig.update_layout(title="Portfolio Performance vs Benchmark",
                                xaxis_title="Date",
                                yaxis_title="Portfolio Value ($)",
                                hovermode="x unified")
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("Simulation completed successfully!")
                
            else:
                # Run real backtest
                result = run_comprehensive_backtest(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    initial_capital
                )
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Return", f"{result.total_return:.2%}")
                col2.metric("Annualized Return", f"{result.annualized_return:.2%}")
                col3.metric("Max Drawdown", f"{result.max_drawdown:.2%}")
                col4.metric("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
                
                # Prepare data for plotting
                dates = [x[0] for x in result.equity_curve]
                values = [x[1] for x in result.equity_curve]
                
                # Plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=values, name='Portfolio', line=dict(color='blue')))
                
                fig.update_layout(title="Portfolio Performance",
                                xaxis_title="Date",
                                yaxis_title="Portfolio Value ($)",
                                hovermode="x unified")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show trades
                if result.trades_executed:
                    st.subheader("Trade History")
                    trades_data = []
                    for trade in result.portfolio_snapshots[-1].open_trades + result.trades_executed: # Note: trades_executed might need better access
                         # In backtester.py, we have a helper generate_trade_summary
                         pass
                    
                    from backtester import generate_trade_summary
                    trade_df = generate_trade_summary(result)
                    st.dataframe(trade_df)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.warning("If you are hitting API rate limits, please try enabling 'Simulation Mode' in the sidebar.")

# Strategy Description
with st.expander("ℹ️ Strategy Details"):
    st.markdown("""
    ### Strategy Overview
    *   **Underlyings**: NVDA (25%), GOOGL (25%), TSLA (20%), QQQ (30%)
    *   **Core Logic**: Sell Cash-Secured Puts (60%) + Covered Calls (40%)
    *   **Rules**:
        *   Sell Puts on 1st trading day of month
        *   Take profit at 70%
        *   Roll at 7-10 DTE
        *   Bear Market Protection (VIX > 35)
    """)
