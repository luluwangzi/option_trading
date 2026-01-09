from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

@dataclass
class StockConfig:
    symbol: str
    weight: float
    put_delta_range: Tuple[float, float]
    call_delta_range: Tuple[float, float]
    max_puts: int = 2

@dataclass
class StrategyConfig:
    dte_range: Tuple[int, int] = (30, 45)
    roll_dte_threshold: int = 10
    profit_take_percent: float = 0.7
    iv_rank_threshold: float = 0.8
    
    # Extreme market conditions
    vix_threshold: float = 35.0
    bear_market_put_delta: Tuple[float, float] = (0.10, 0.15)
    
    # Strategy allocation
    put_allocation: float = 0.6
    call_allocation: float = 0.4

# Stock-specific configurations
STOCK_CONFIGS: Dict[str, StockConfig] = {
    "NVDA": StockConfig(
        symbol="NVDA",
        weight=0.25,
        put_delta_range=(0.15, 0.20),
        call_delta_range=(0.15, 0.20)
    ),
    "GOOGL": StockConfig(
        symbol="GOOGL", 
        weight=0.25,
        put_delta_range=(0.20, 0.25),
        call_delta_range=(0.15, 0.20)
    ),
    "TSLA": StockConfig(
        symbol="TSLA",
        weight=0.20,
        put_delta_range=(0.15, 0.20),
        call_delta_range=(0.15, 0.20)
    ),
    "QQQ": StockConfig(
        symbol="QQQ",
        weight=0.30,
        put_delta_range=(0.20, 0.25),
        call_delta_range=(0.15, 0.20)
    )
}

# Global strategy configuration
STRATEGY_CONFIG = StrategyConfig()

# Trading calendar (first trading day of each month)
TRADING_CALENDAR = [
    "2024-01-02", "2024-02-01", "2024-03-01", "2024-04-01",
    "2024-05-01", "2024-06-03", "2024-07-01", "2024-08-01",
    "2024-09-03", "2024-10-01", "2024-11-01", "2024-12-02"
]

def is_first_trading_day(date: datetime) -> bool:
    """Check if date is the first trading day of the month"""
    date_str = date.strftime("%Y-%m-%d")
    return date_str in TRADING_CALENDAR