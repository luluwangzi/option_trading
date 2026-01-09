from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid
from models import Portfolio, PortfolioPosition, PositionState, OptionContract, Trade, OptionType
from config import STOCK_CONFIGS, STRATEGY_CONFIG, is_first_trading_day
from data_service import get_current_market_data, find_optimal_option, is_bear_market_conditions

class TradingEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.portfolio = self._initialize_portfolio()
        self.trade_history: List[Trade] = []
    
    def _initialize_portfolio(self) -> Portfolio:
        """Initialize portfolio with cash only"""
        positions = {}
        for symbol in STOCK_CONFIGS.keys():
            positions[symbol] = PortfolioPosition(
                symbol=symbol,
                state=PositionState.CASH,
                quantity=0,
                average_cost=0.0
            )
        
        return Portfolio(
            cash=self.initial_capital,
            positions=positions,
            total_value=self.initial_capital,
            timestamp=datetime.now()
        )
    
    def execute_strategy(self, current_date: datetime) -> List[Trade]:
        """Execute the complete strategy for a given date"""
        executed_trades = []
        
        # Get current market data
        market_data = get_current_market_data(list(STOCK_CONFIGS.keys()))
        
        # Check for extreme market conditions
        bear_market = is_bear_market_conditions(market_data)
        
        # Process each stock according to its state machine
        for symbol, position in self.portfolio.positions.items():
            stock_trades = self._process_stock_position(
                symbol, position, market_data[symbol], bear_market, current_date
            )
            executed_trades.extend(stock_trades)
        
        # Update portfolio value
        self._update_portfolio_value(market_data)
        
        return executed_trades
    
    def _process_stock_position(self, symbol: str, position: PortfolioPosition, 
                               market_data, bear_market: bool, current_date: datetime) -> List[Trade]:
        """Process a single stock position according to state machine"""
        trades = []
        stock_config = STOCK_CONFIGS[symbol]
        
        if position.state == PositionState.CASH:
            # Cash state: Sell cash-secured put on first trading day
            if is_first_trading_day(current_date):
                put_trade = self._sell_cash_secured_put(symbol, market_data, bear_market)
                if put_trade:
                    trades.append(put_trade)
                    position.state = PositionState.PUT_SOLD
                    position.current_option = self._create_option_contract(put_trade, market_data)
        
        elif position.state == PositionState.PUT_SOLD:
            # Put sold state: Check for profit take, roll, or exercise
            if position.current_option:
                # Check profit take condition
                current_premium = self._get_current_option_premium(position.current_option)
                initial_premium = position.current_option.premium
                
                if current_premium <= initial_premium * (1 - STRATEGY_CONFIG.profit_take_percent):
                    # Profit take: Buy back put
                    buyback_trade = self._buy_back_option(position.current_option, market_data.price)
                    trades.append(buyback_trade)
                    position.state = PositionState.CASH
                    position.current_option = None
                
                # Check roll condition (low DTE)
                elif position.current_option.dte <= STRATEGY_CONFIG.roll_dte_threshold:
                    # Roll to next month
                    roll_trade = self._roll_option(position.current_option, market_data, bear_market)
                    if roll_trade:
                        trades.append(roll_trade)
                        position.current_option = self._create_option_contract(roll_trade, market_data)
                
                # Check exercise condition (if option is in the money)
                elif market_data.price <= position.current_option.strike:
                    # Option exercised, transition to stock owned
                    exercise_trade = self._exercise_option(position.current_option, market_data.price)
                    trades.append(exercise_trade)
                    position.state = PositionState.STOCK_OWNED
                    position.quantity = 100  # Standard option contract size
                    position.average_cost = position.current_option.strike
                    position.current_option = None
        
        elif position.state == PositionState.STOCK_OWNED:
            # Stock owned state: Sell covered call
            if not position.current_option:
                call_trade = self._sell_covered_call(symbol, position.average_cost, market_data)
                if call_trade:
                    trades.append(call_trade)
                    position.state = PositionState.CALL_SOLD
                    position.current_option = self._create_option_contract(call_trade, market_data)
            else:
                # Check call position for profit take, roll, or exercise
                current_premium = self._get_current_option_premium(position.current_option)
                initial_premium = position.current_option.premium
                
                if current_premium <= initial_premium * (1 - STRATEGY_CONFIG.profit_take_percent):
                    # Profit take: Buy back call
                    buyback_trade = self._buy_back_option(position.current_option, market_data.price)
                    trades.append(buyback_trade)
                    position.state = PositionState.STOCK_OWNED
                    position.current_option = None
                
                # Check roll condition for calls (if stock price rises significantly)
                elif market_data.price > position.current_option.strike * 1.1:  # 10% above strike
                    roll_trade = self._roll_option(position.current_option, market_data, bear_market)
                    if roll_trade:
                        trades.append(roll_trade)
                        position.current_option = self._create_option_contract(roll_trade, market_data)
                
                # Check exercise condition
                elif market_data.price >= position.current_option.strike:
                    # Call exercised, sell stock
                    exercise_trade = self._exercise_call_option(position.current_option, market_data.price)
                    trades.append(exercise_trade)
                    position.state = PositionState.CASH
                    position.quantity = 0
                    position.average_cost = 0.0
                    position.current_option = None
        
        elif position.state == PositionState.CALL_SOLD:
            # Similar logic to PUT_SOLD state for call management
            pass
        
        return trades
    
    def _sell_cash_secured_put(self, symbol: str, market_data, bear_market: bool) -> Optional[Trade]:
        """Sell cash-secured put according to strategy rules"""
        stock_config = STOCK_CONFIGS[symbol]
        
        # Adjust delta range for bear market
        delta_range = stock_config.put_delta_range
        if bear_market and symbol in ["NVDA", "TSLA"]:
            # In bear market, only trade QQQ and GOOGL with lower delta
            if symbol in ["QQQ", "GOOGL"]:
                delta_range = STRATEGY_CONFIG.bear_market_put_delta
            else:
                return None  # Skip NVDA and TSLA in bear market
        
        # Find optimal put option
        option_data = find_optimal_option(
            symbol, 'put', delta_range, market_data.price, STRATEGY_CONFIG.dte_range
        )
        
        if option_data and option_data.get('iv_rank', 1.0) < STRATEGY_CONFIG.iv_rank_threshold:
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                symbol=symbol,
                option_type=OptionType.PUT,
                action="open",
                quantity=1,
                price=option_data['bid'],
                strike=option_data['strike'],
                expiration=option_data['expiration'],
                timestamp=datetime.now(),
                premium=option_data['bid'] * 100,  # Premium per contract
                delta=option_data.get('delta'),
                iv_rank=option_data.get('iv_rank')
            )
            
            # Update portfolio cash (receive premium)
            self.portfolio.cash += trade.premium
            
            return trade
        
        return None
    
    def _sell_covered_call(self, symbol: str, cost_basis: float, market_data) -> Optional[Trade]:
        """Sell covered call according to strategy rules"""
        stock_config = STOCK_CONFIGS[symbol]
        
        # Find optimal call option with strike above cost basis + 10%
        min_strike = max(market_data.price * 1.10, cost_basis * 1.10)
        
        # Get options chain to find suitable call
        option_data = find_optimal_option(
            symbol, 'call', stock_config.call_delta_range, market_data.price, STRATEGY_CONFIG.dte_range
        )
        
        if option_data and option_data['strike'] >= min_strike:
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                symbol=symbol,
                option_type=OptionType.CALL,
                action="open",
                quantity=1,
                price=option_data['bid'],
                strike=option_data['strike'],
                expiration=option_data['expiration'],
                timestamp=datetime.now(),
                premium=option_data['bid'] * 100,
                delta=option_data.get('delta'),
                iv_rank=option_data.get('iv_rank')
            )
            
            self.portfolio.cash += trade.premium
            return trade
        
        return None
    
    def _create_option_contract(self, trade: Trade, market_data) -> OptionContract:
        """Create OptionContract from Trade"""
        return OptionContract(
            symbol=trade.symbol,
            option_type=trade.option_type,
            strike=trade.strike,
            expiration=trade.expiration,
            premium=trade.premium,
            delta=trade.delta or 0.0,
            iv_rank=trade.iv_rank or 0.5,
            dte=(trade.expiration - datetime.now()).days,
            contract_id=f"{trade.symbol}_{trade.expiration.strftime('%Y%m%d')}_{trade.strike}"
        )
    
    def _update_portfolio_value(self, market_data):
        """Update total portfolio value based on current market prices"""
        stock_value = 0.0
        option_value = 0.0
        
        for symbol, position in self.portfolio.positions.items():
            current_price = market_data[symbol].price
            
            # Stock value
            stock_value += position.quantity * current_price
            
            # Option value (mark to market)
            if position.current_option:
                # Simple approximation: use initial premium for now
                # In real implementation, would get current market price
                option_value += position.current_option.premium
        
        self.portfolio.total_value = self.portfolio.cash + stock_value + option_value
        self.portfolio.timestamp = datetime.now()
    
    # Additional helper methods would be implemented here for:
    # _buy_back_option, _roll_option, _exercise_option, _exercise_call_option
    # These would handle the specific trade execution logic

def run_backtest(start_date: datetime, end_date: datetime, initial_capital: float) -> dict:
    """Run backtest for the given date range"""
    engine = TradingEngine(initial_capital)
    
    # Generate trading dates (business days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')
    
    results = {
        'equity_curve': [],
        'portfolio_snapshots': [],
        'trades_executed': []
    }
    
    for current_date in date_range:
        # Execute strategy for this date
        trades = engine.execute_strategy(current_date)
        
        # Record results
        results['equity_curve'].append((current_date, engine.portfolio.total_value))
        results['portfolio_snapshots'].append(engine.portfolio)
        results['trades_executed'].extend(trades)
    
    return results