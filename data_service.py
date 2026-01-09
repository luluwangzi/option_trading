import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from models import MarketData
from config import STOCK_CONFIGS

def get_historical_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get historical price data for a symbol"""
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    return data

def get_current_market_data(symbols: List[str]) -> Dict[str, MarketData]:
    """Get current market data for multiple symbols"""
    results = {}
    
    # Get VIX data
    vix_data = yf.Ticker("^VIX")
    vix_info = vix_data.info
    vix_price = vix_info.get('regularMarketPrice', 20.0)
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            
            # Get options data for IV calculation
            options = ticker.options
            if options:
                # Get nearest expiration for IV calculation
                nearest_exp = options[0]
                opt_chain = ticker.option_chain(nearest_exp)
                
                # Calculate average IV from options chain
                puts_iv = opt_chain.puts.impliedVolatility.mean() if not opt_chain.puts.empty else 0.4
                calls_iv = opt_chain.calls.impliedVolatility.mean() if not opt_chain.calls.empty else 0.4
                avg_iv = (puts_iv + calls_iv) / 2
                
                # Simple IV rank calculation (0-1 scale)
                iv_rank = min(avg_iv / 0.8, 1.0)  # Assuming 0.8 as high IV threshold
            else:
                avg_iv = 0.4
                iv_rank = 0.5
            
            # Get historical data for moving averages
            hist_data = get_historical_data(symbol, (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d'), 
                                          datetime.now().strftime('%Y-%m-%d'))
            
            moving_averages = {}
            if not hist_data.empty:
                moving_averages['50_day'] = hist_data['Close'].rolling(50).mean().iloc[-1]
                moving_averages['200_day'] = hist_data['Close'].rolling(200).mean().iloc[-1]
            
            results[symbol] = MarketData(
                symbol=symbol,
                price=current_price,
                iv_30=avg_iv,
                iv_rank=iv_rank,
                moving_averages=moving_averages,
                vix=vix_price,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            # Fallback data
            results[symbol] = MarketData(
                symbol=symbol,
                price=100.0,
                iv_30=0.4,
                iv_rank=0.5,
                moving_averages={"50_day": 95.0, "200_day": 90.0},
                vix=20.0,
                timestamp=datetime.now()
            )
    
    return results

def get_options_chain(symbol: str, expiration: str) -> pd.DataFrame:
    """Get options chain for a specific expiration"""
    try:
        ticker = yf.Ticker(symbol)
        opt_chain = ticker.option_chain(expiration)
        
        # Combine puts and calls
        puts = opt_chain.puts
        calls = opt_chain.calls
        
        puts['optionType'] = 'put'
        calls['optionType'] = 'call'
        
        full_chain = pd.concat([puts, calls], ignore_index=True)
        return full_chain
        
    except Exception as e:
        print(f"Error fetching options chain for {symbol}: {e}")
        return pd.DataFrame()

def find_optimal_option(symbol: str, option_type: str, delta_range: tuple, 
                        current_price: float, dte_range: tuple) -> Optional[dict]:
    """Find optimal option contract based on criteria"""
    try:
        ticker = yf.Ticker(symbol)
        options = ticker.options
        
        if not options:
            return None
            
        optimal_contract = None
        best_score = float('inf')
        
        for exp in options:
            # Calculate days to expiration
            exp_date = datetime.strptime(exp, '%Y-%m-%d')
            dte = (exp_date - datetime.now()).days
            
            if dte_range[0] <= dte <= dte_range[1]:
                opt_chain = ticker.option_chain(exp)
                
                chain = opt_chain.puts if option_type == 'put' else opt_chain.calls
                if chain.empty:
                    continue
                    
                # Filter by delta range
                filtered = chain[(chain['impliedVolatility'] > 0) & 
                               (chain['delta'].between(delta_range[0], delta_range[1]))]
                
                if not filtered.empty:
                    # Find contract with highest premium (bid price)
                    best_contract = filtered.loc[filtered['bid'].idxmax()]
                    
                    # Simple scoring: prefer higher premium and closer to mid delta
                    delta_mid = (delta_range[0] + delta_range[1]) / 2
                    delta_diff = abs(best_contract['delta'] - delta_mid)
                    score = delta_diff - best_contract['bid']  # Lower score is better
                    
                    if score < best_score:
                        best_score = score
                        optimal_contract = best_contract.to_dict()
                        optimal_contract['expiration'] = exp_date
                        optimal_contract['dte'] = dte
                        optimal_contract['optionType'] = option_type
        
        return optimal_contract
        
    except Exception as e:
        print(f"Error finding optimal option for {symbol}: {e}")
        return None

def is_bear_market_conditions(market_data: Dict[str, MarketData]) -> bool:
    """Check if bear market conditions are met"""
    # Condition 1: VIX > 35
    vix_condition = any(data.vix > 35 for data in market_data.values())
    
    # Condition 2: QQQ below 200-day MA
    qqq_data = market_data.get('QQQ')
    qqq_condition = False
    if qqq_data and '200_day' in qqq_data.moving_averages:
        qqq_condition = qqq_data.price < qqq_data.moving_averages['200_day']
    
    return vix_condition or qqq_condition