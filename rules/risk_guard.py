"""
Risk management system for protecting capital and managing trade limits.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import config


class RiskGuard:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.daily_trades = []
        self.daily_pnl = 0.0
        self.open_positions = {}
        
    def can_trade_today(self) -> bool:
        """Check if we can trade today based on limits."""
        today = datetime.utcnow().date()
        
        # Count today's trades
        today_trades = [
            trade for trade in self.daily_trades 
            if datetime.fromisoformat(trade['timestamp']).date() == today
        ]
        
        # Check max trades per day
        if len(today_trades) >= config.MAX_DAILY_TRADES:
            self.logger.warning(f"Max daily trades ({config.MAX_DAILY_TRADES}) reached")
            return False
            
        # Check daily loss limit
        today_pnl = sum(trade.get('pnl', 0) for trade in today_trades)
        if today_pnl <= config.MAX_DAILY_LOSS:
            self.logger.warning(f"Daily loss limit reached: {today_pnl:.2%}")
            return False
            
        return True
        
    def validate_signal(self, signal: Dict) -> bool:
        """Validate a trading signal against risk management rules."""
        try:
            symbol = signal.get('symbol')
            action = signal.get('action')
            confidence = signal.get('confidence', 0)
            
            if not symbol or not action:
                return False
                
            # Skip WAIT signals
            if action == 'WAIT':
                return True
                
            # Check if we can trade today
            if not self.can_trade_today():
                return False
                
            # Check minimum confidence
            if confidence < 0.5:
                self.logger.info(f"Signal confidence too low: {confidence:.2f}")
                return False
                
            # Check if we already have a position in this symbol
            if symbol in self.open_positions:
                existing_action = self.open_positions[symbol].get('action')
                if existing_action == action:
                    self.logger.info(f"Already have {action} position in {symbol}")
                    return False
                    
            # Check risk/reward ratio
            if not self.check_risk_reward_ratio(signal):
                return False
                
            # Check position sizing
            if not self.check_position_size(signal):
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating signal: {e}")
            return False
            
    def check_risk_reward_ratio(self, signal: Dict) -> bool:
        """Check if the signal meets minimum risk/reward ratio."""
        confidence = signal.get('confidence', 0)
        
        # Risk/reward estimation based on confidence and volatility
        # Higher confidence signals assumed to have better risk/reward
        estimated_rr = confidence * 3  # Simplified calculation
        
        if estimated_rr < config.MIN_RISK_REWARD_RATIO:
            self.logger.info(f"Risk/reward ratio too low: {estimated_rr:.2f}")
            return False
            
        return True
        
    def check_position_size(self, signal: Dict) -> bool:
        """Check if position size is appropriate."""
        # Portfolio value should be configurable or fetched from account data
        # For now, using a base portfolio value that should be set in config
        portfolio_value = getattr(config, 'PORTFOLIO_VALUE', 10000)  # Default $10k
        
        position_value = portfolio_value * config.POSITION_SIZE
        
        # Check if position size is reasonable
        max_position_pct = getattr(config, 'MAX_POSITION_PCT', 0.2)  # Default 20%
        if position_value > portfolio_value * max_position_pct:
            self.logger.warning(f"Position size too large: {position_value}")
            return False
            
        return True
        
    def calculate_stop_loss(self, entry_price: float, action: str) -> float:
        """Calculate stop loss price."""
        if action == 'BUY':
            return entry_price * (1 - config.STOP_LOSS_PCT)
        elif action == 'SELL':
            return entry_price * (1 + config.STOP_LOSS_PCT)
        return entry_price
        
    def calculate_take_profit(self, entry_price: float, action: str) -> float:
        """Calculate take profit price."""
        if action == 'BUY':
            return entry_price * (1 + config.TAKE_PROFIT_PCT)
        elif action == 'SELL':
            return entry_price * (1 - config.TAKE_PROFIT_PCT)
        return entry_price
        
    def open_position(self, signal: Dict, entry_price: float) -> Dict:
        """Open a new position based on signal."""
        symbol = signal['symbol']
        action = signal['action']
        
        stop_loss = self.calculate_stop_loss(entry_price, action)
        take_profit = self.calculate_take_profit(entry_price, action)
        
        position = {
            'symbol': symbol,
            'action': action,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'quantity': self.calculate_quantity(entry_price),
            'timestamp': datetime.utcnow().isoformat(),
            'signal_confidence': signal.get('confidence', 0),
            'signal_reasoning': signal.get('reasoning', ''),
            'status': 'open'
        }
        
        self.open_positions[symbol] = position
        self.logger.info(f"Opened {action} position for {symbol} at {entry_price}")
        
        return position
        
    def calculate_quantity(self, entry_price: float) -> float:
        """Calculate position quantity based on position sizing rules."""
        # Portfolio value should be fetched from account or configuration
        portfolio_value = getattr(config, 'PORTFOLIO_VALUE', 10000)  # Default $10k
        position_value = portfolio_value * config.POSITION_SIZE
        
        return position_value / entry_price
        
    def check_stop_loss_take_profit(self, current_prices: Dict) -> List[Dict]:
        """Check if any positions hit stop loss or take profit."""
        closed_positions = []
        
        for symbol, position in list(self.open_positions.items()):
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            action = position['action']
            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            take_profit = position['take_profit']
            
            should_close = False
            close_reason = ''
            
            if action == 'BUY':
                if current_price <= stop_loss:
                    should_close = True
                    close_reason = 'stop_loss'
                elif current_price >= take_profit:
                    should_close = True
                    close_reason = 'take_profit'
            elif action == 'SELL':
                if current_price >= stop_loss:
                    should_close = True
                    close_reason = 'stop_loss'
                elif current_price <= take_profit:
                    should_close = True
                    close_reason = 'take_profit'
                    
            if should_close:
                closed_position = self.close_position(symbol, current_price, close_reason)
                closed_positions.append(closed_position)
                
        return closed_positions
        
    def close_position(self, symbol: str, exit_price: float, reason: str) -> Dict:
        """Close a position and calculate P&L."""
        if symbol not in self.open_positions:
            return {}
            
        position = self.open_positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']
        action = position['action']
        
        # Calculate P&L
        if action == 'BUY':
            pnl = (exit_price - entry_price) * quantity
            pnl_pct = (exit_price - entry_price) / entry_price
        else:  # SELL
            pnl = (entry_price - exit_price) * quantity
            pnl_pct = (entry_price - exit_price) / entry_price
            
        closed_position = {
            **position,
            'exit_price': exit_price,
            'exit_timestamp': datetime.utcnow().isoformat(),
            'close_reason': reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'status': 'closed'
        }
        
        # Update tracking
        self.daily_trades.append(closed_position)
        self.daily_pnl += pnl
        del self.open_positions[symbol]
        
        self.logger.info(f"Closed {action} position for {symbol}: P&L {pnl:.2f} ({pnl_pct:.2%})")
        
        return closed_position
        
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics."""
        today = datetime.utcnow().date()
        today_trades = [
            trade for trade in self.daily_trades 
            if datetime.fromisoformat(trade['timestamp']).date() == today
        ]
        
        total_pnl = sum(trade.get('pnl', 0) for trade in today_trades)
        total_pnl_pct = sum(trade.get('pnl_pct', 0) for trade in today_trades)
        
        winning_trades = [t for t in today_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in today_trades if t.get('pnl', 0) < 0]
        
        return {
            'date': today.isoformat(),
            'total_trades': len(today_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(today_trades) if today_trades else 0,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'remaining_trades': config.MAX_DAILY_TRADES - len(today_trades),
            'open_positions': len(self.open_positions)
        }
        
    def reset_daily_data(self):
        """Reset daily data at start of new day."""
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        # Keep only recent trades for historical analysis
        self.daily_trades = [
            trade for trade in self.daily_trades 
            if datetime.fromisoformat(trade['timestamp']).date() >= yesterday
        ]
        
        self.daily_pnl = 0.0 