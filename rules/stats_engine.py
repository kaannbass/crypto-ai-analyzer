"""
Statistics engine for tracking performance and generating trading reports.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import config


class StatsEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_performance_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics."""
        if not trades:
            return self.get_empty_metrics()
            
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        total_pnl = sum(trade.get('pnl', 0) for trade in trades)
        total_pnl_pct = sum(trade.get('pnl_pct', 0) for trade in trades)
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Drawdown calculation
        cumulative_pnl = []
        running_total = 0
        for trade in trades:
            running_total += trade.get('pnl', 0)
            cumulative_pnl.append(running_total)
            
        max_drawdown = self.calculate_max_drawdown(cumulative_pnl)
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
        
    def calculate_max_drawdown(self, cumulative_pnl: List[float]) -> float:
        """Calculate maximum drawdown from cumulative P&L."""
        if not cumulative_pnl:
            return 0.0
            
        peak = cumulative_pnl[0]
        max_dd = 0.0
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_dd:
                max_dd = drawdown
                
        return max_dd
        
    def get_empty_metrics(self) -> Dict:
        """Return empty metrics structure."""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'total_pnl_pct': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'gross_profit': 0.0,
            'gross_loss': 0.0
        }
        
    def generate_daily_report(self, trades: List[Dict], signals: List[Dict]) -> Dict:
        """Generate comprehensive daily trading report."""
        today = datetime.utcnow().date()
        
        # Filter today's data
        today_trades = [
            t for t in trades 
            if datetime.fromisoformat(t['timestamp']).date() == today
        ]
        
        today_signals = [
            s for s in signals 
            if datetime.fromisoformat(s['timestamp']).date() == today
        ]
        
        # Calculate metrics
        performance = self.calculate_performance_metrics(today_trades)
        
        # Signal analysis
        signal_analysis = self.analyze_signals(today_signals)
        
        # Risk analysis
        risk_analysis = self.analyze_risk(today_trades)
        
        report = {
            'date': today.isoformat(),
            'generated_at': datetime.utcnow().isoformat(),
            'performance': performance,
            'signal_analysis': signal_analysis,
            'risk_analysis': risk_analysis,
            'summary': self.generate_summary(performance, signal_analysis, risk_analysis)
        }
        
        return report
        
    def analyze_signals(self, signals: List[Dict]) -> Dict:
        """Analyze signal generation patterns."""
        if not signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'wait_signals': 0,
                'avg_confidence': 0.0,
                'signal_types': {},
                'symbols_analyzed': []
            }
            
        buy_signals = [s for s in signals if s.get('action') == 'BUY']
        sell_signals = [s for s in signals if s.get('action') == 'SELL']
        wait_signals = [s for s in signals if s.get('action') == 'WAIT']
        
        # Average confidence
        confidences = [s.get('confidence', 0) for s in signals if s.get('confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Signal types
        signal_types = {}
        for signal in signals:
            signal_type = signal.get('type', 'daily')
            signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
        # Symbols analyzed
        symbols = list(set(s.get('symbol') for s in signals if s.get('symbol')))
        
        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'wait_signals': len(wait_signals),
            'avg_confidence': avg_confidence,
            'signal_types': signal_types,
            'symbols_analyzed': symbols
        }
        
    def analyze_risk(self, trades: List[Dict]) -> Dict:
        """Analyze risk metrics from trades."""
        if not trades:
            return {
                'trades_executed': 0,
                'avg_risk_per_trade': 0.0,
                'max_loss_trade': 0.0,
                'max_win_trade': 0.0,
                'risk_reward_ratio': 0.0,
                'stop_loss_hits': 0,
                'take_profit_hits': 0
            }
            
        pnls = [t.get('pnl', 0) for t in trades]
        
        stop_loss_hits = len([t for t in trades if t.get('close_reason') == 'stop_loss'])
        take_profit_hits = len([t for t in trades if t.get('close_reason') == 'take_profit'])
        
        # Risk per trade (assuming 2% stop loss)
        avg_risk = config.STOP_LOSS_PCT * 100  # Convert to percentage
        
        return {
            'trades_executed': len(trades),
            'avg_risk_per_trade': avg_risk,
            'max_loss_trade': min(pnls) if pnls else 0,
            'max_win_trade': max(pnls) if pnls else 0,
            'risk_reward_ratio': max(pnls) / abs(min(pnls)) if pnls and min(pnls) < 0 else 0,
            'stop_loss_hits': stop_loss_hits,
            'take_profit_hits': take_profit_hits
        }
        
    def generate_summary(self, performance: Dict, signal_analysis: Dict, risk_analysis: Dict) -> str:
        """Generate human-readable summary."""
        summary_parts = []
        
        # Performance summary
        total_trades = performance.get('total_trades', 0)
        win_rate = performance.get('win_rate', 0)
        total_pnl_pct = performance.get('total_pnl_pct', 0)
        
        if total_trades > 0:
            summary_parts.append(f"Executed {total_trades} trades with {win_rate:.1%} win rate")
            summary_parts.append(f"Daily P&L: {total_pnl_pct:.2%}")
        else:
            summary_parts.append("No trades executed today")
            
        # Signal summary
        total_signals = signal_analysis.get('total_signals', 0)
        avg_confidence = signal_analysis.get('avg_confidence', 0)
        
        if total_signals > 0:
            summary_parts.append(f"Generated {total_signals} signals with avg confidence {avg_confidence:.2f}")
        else:
            summary_parts.append("No signals generated today")
            
        # Risk summary
        if risk_analysis.get('trades_executed', 0) > 0:
            stop_losses = risk_analysis.get('stop_loss_hits', 0)
            take_profits = risk_analysis.get('take_profit_hits', 0)
            summary_parts.append(f"Risk management: {stop_losses} stop losses, {take_profits} take profits")
            
        return ". ".join(summary_parts) + "."
        
    def get_weekly_performance(self, trades: List[Dict]) -> Dict:
        """Calculate weekly performance metrics."""
        week_ago = datetime.utcnow().date() - timedelta(days=7)
        
        weekly_trades = [
            t for t in trades 
            if datetime.fromisoformat(t['timestamp']).date() >= week_ago
        ]
        
        # Group by day
        daily_performance = {}
        
        for trade in weekly_trades:
            trade_date = datetime.fromisoformat(trade['timestamp']).date()
            
            if trade_date not in daily_performance:
                daily_performance[trade_date] = []
                
            daily_performance[trade_date].append(trade)
            
        # Calculate daily metrics
        weekly_summary = {}
        for date, day_trades in daily_performance.items():
            metrics = self.calculate_performance_metrics(day_trades)
            weekly_summary[date.isoformat()] = metrics
            
        return {
            'period': f"{week_ago.isoformat()} to {datetime.utcnow().date().isoformat()}",
            'daily_breakdown': weekly_summary,
            'weekly_totals': self.calculate_performance_metrics(weekly_trades)
        }
        
    def get_symbol_performance(self, trades: List[Dict]) -> Dict:
        """Analyze performance by symbol."""
        symbol_trades = {}
        
        for trade in trades:
            symbol = trade.get('symbol')
            if symbol:
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(trade)
                
        symbol_performance = {}
        for symbol, symbol_trade_list in symbol_trades.items():
            symbol_performance[symbol] = self.calculate_performance_metrics(symbol_trade_list)
            
        return symbol_performance
        
    def save_daily_report(self, report: Dict):
        """Save daily report to file."""
        date_str = report['date']
        filename = f"{config.DATA_DIR}/report_{date_str}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Daily report saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save daily report: {e}")
            
    def load_historical_trades(self) -> List[Dict]:
        """Load historical trades from signals file."""
        try:
            with open(config.SIGNALS_FILE, 'r') as f:
                signals = json.load(f)
                
            # Filter for completed trades (those with exit data)
            trades = [s for s in signals if s.get('status') == 'closed']
            return trades
            
        except (FileNotFoundError, json.JSONDecodeError):
            return [] 