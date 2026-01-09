from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal
from enum import Enum

class OptionType(Enum):
    PUT = "put"
    CALL = "call"

class PositionState(Enum):
    CASH = "cash"
    PUT_SOLD = "put_sold"
    STOCK_OWNED = "stock_owned"
    CALL_SOLD = "call_sold"

@dataclass
class OptionContract:
    symbol: str
    option_type: OptionType
    strike: float
    expiration: datetime
    premium: float
    delta: float
    iv_rank: float
    dte: int
    contract_id: str
    
@dataclass
class Trade:
    trade_id: str
    symbol: str
    option_type: OptionType
    action: Literal["open", "close", "roll", "exercise"]
    quantity: int
    price: float
    strike: float
    expiration: datetime
    timestamp: datetime
    premium: float
    delta: Optional[float] = None
    iv_rank: Optional[float] = None

@dataclass
class PortfolioPosition:
    symbol: str
    state: PositionState
    quantity: int
    average_cost: float
    current_option: Optional[OptionContract] = None
    open_trades: list[Trade] = None
    
    def __post_init__(self):
        if self.open_trades is None:
            self.open_trades = []

@dataclass
class Portfolio:
    cash: float
    positions: dict[str, PortfolioPosition]
    total_value: float
    timestamp: datetime

@dataclass
class MarketData:
    symbol: str
    price: float
    iv_30: float  # 30-day implied volatility
    iv_rank: float  # IV rank (0-1)
    moving_averages: dict[str, float]  # e.g., {"50_day": 150.0, "200_day": 140.0}
    vix: float  # VIX index value
    timestamp: datetime

@dataclass
class BacktestResult:
    initial_capital: float
    final_portfolio_value: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades_executed: int
    start_date: datetime
    end_date: datetime
    equity_curve: list[tuple[datetime, float]]
    portfolio_snapshots: list[Portfolio]