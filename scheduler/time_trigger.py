"""
Time-aware logic for handling different trading sessions and market hours.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import config


class TimeTrigger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_daily_run = None
        self.last_hourly_run = None

    def should_run_daily(self, current_time: datetime) -> bool:
        """Check if daily analysis should run at 08:00 UTC."""
        try:
            # Check if it's 08:00 UTC and we haven't run today
            if current_time.hour == config.DAILY_ANALYSIS_HOUR:
                if self.last_daily_run is None:
                    self.last_daily_run = current_time
                    return True
                
                # Check if it's a new day
                if current_time.date() > self.last_daily_run.date():
                    self.last_daily_run = current_time
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking daily run condition: {e}")
            return False

    def should_run_hourly(self, current_time: datetime) -> bool:
        """Check if hourly scan should run (at the top of each hour)."""
        try:
            # Run at the top of each hour (first 5 minutes)
            if current_time.minute < 5:
                if self.last_hourly_run is None:
                    self.last_hourly_run = current_time
                    return True
                
                # Check if it's a new hour
                if current_time.hour != self.last_hourly_run.hour:
                    self.last_hourly_run = current_time
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking hourly run condition: {e}")
            return False
        
    def get_current_session(self) -> str:
        """Determine current trading session based on UTC time."""
        current_time = datetime.utcnow()
        hour = current_time.hour
        
        # Weekend detection
        if current_time.weekday() >= 5:  # Saturday=5, Sunday=6
            return 'weekend'
            
        # Asia session: 00:00 - 08:00 UTC
        if config.ASIA_SESSION_START <= hour < config.ASIA_SESSION_END:
            return 'asia'
            
        # US-EU overlap: 13:00 - 16:00 UTC
        elif config.OVERLAP_SESSION_START <= hour < config.OVERLAP_SESSION_END:
            return 'overlap'
            
        # European session: 08:00 - 17:00 UTC (outside overlap)
        elif 8 <= hour < 17:
            return 'europe'
            
        # US session: 17:00 - 00:00 UTC
        elif hour >= 17 or hour < config.ASIA_SESSION_START:
            return 'us'
            
        else:
            return 'unknown'
            
    def get_session_characteristics(self, session: str) -> Dict:
        """Get trading characteristics for each session."""
        characteristics = {
            'asia': {
                'volatility': 'medium',
                'volume': 'moderate',
                'major_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD'],
                'crypto_activity': 'moderate',
                'recommended_strategy': 'range_trading',
                'risk_multiplier': 1.0
            },
            'europe': {
                'volatility': 'high',
                'volume': 'high',
                'major_pairs': ['EURUSD', 'GBPUSD', 'USDCHF'],
                'crypto_activity': 'high',
                'recommended_strategy': 'trend_following',
                'risk_multiplier': 1.2
            },
            'overlap': {
                'volatility': 'very_high',
                'volume': 'very_high',
                'major_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
                'crypto_activity': 'very_high',
                'recommended_strategy': 'breakout_trading',
                'risk_multiplier': 1.5
            },
            'us': {
                'volatility': 'high',
                'volume': 'high',
                'major_pairs': ['EURUSD', 'GBPUSD', 'USDCAD'],
                'crypto_activity': 'high',
                'recommended_strategy': 'momentum_trading',
                'risk_multiplier': 1.3
            },
            'weekend': {
                'volatility': 'low',
                'volume': 'very_low',
                'major_pairs': [],
                'crypto_activity': 'low',
                'recommended_strategy': 'conservative',
                'risk_multiplier': 0.5
            }
        }
        
        return characteristics.get(session, {
            'volatility': 'unknown',
            'volume': 'unknown',
            'major_pairs': [],
            'crypto_activity': 'unknown',
            'recommended_strategy': 'wait',
            'risk_multiplier': 0.8
        })
        
    def should_trade_now(self) -> Tuple[bool, str]:
        """Determine if trading should be active now."""
        session = self.get_current_session()
        characteristics = self.get_session_characteristics(session)
        
        if session == 'weekend':
            return False, "Weekend - crypto markets continue but reduced activity"
            
        if session == 'overlap':
            return True, "US-EU overlap - highest activity period"
            
        if session in ['europe', 'us']:
            return True, f"{session.title()} session - high activity"
            
        if session == 'asia':
            return True, "Asia session - moderate activity"
            
        return False, "Unknown session or low activity period"
        
    def get_risk_adjustment(self) -> float:
        """Get risk adjustment multiplier based on current session."""
        session = self.get_current_session()
        characteristics = self.get_session_characteristics(session)
        return characteristics.get('risk_multiplier', 1.0)
        
    def is_major_news_time(self) -> bool:
        """Check if current time is during major news releases."""
        current_time = datetime.utcnow()
        hour = current_time.hour
        minute = current_time.minute
        
        # Major news times (simplified)
        news_times = [
            (8, 30),   # EU economic data
            (12, 30),  # EU central bank decisions
            (13, 30),  # US economic data
            (14, 0),   # US Fed announcements
            (18, 0),   # US close
        ]
        
        for news_hour, news_minute in news_times:
            if (hour == news_hour and 
                abs(minute - news_minute) <= 15):  # 15 minutes before/after
                return True
                
        return False
        
    def get_next_session_change(self) -> Tuple[datetime, str]:
        """Get the next session change time and session name."""
        current_time = datetime.utcnow()
        current_session = self.get_current_session()
        
        # Define session start times
        session_times = [
            (0, 'asia'),      # 00:00 UTC
            (8, 'europe'),    # 08:00 UTC
            (13, 'overlap'),  # 13:00 UTC
            (16, 'us'),       # 16:00 UTC (end of overlap, start pure US)
            (17, 'us_peak'),  # 17:00 UTC (US market open)
        ]
        
        # Find next session
        for hour, session in session_times:
            next_time = current_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            if next_time <= current_time:
                next_time += timedelta(days=1)
                
            if next_time > current_time:
                return next_time, session
                
        # Default to next day asia session
        next_asia = (current_time + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return next_asia, 'asia'
        
    def get_hourly_priority_symbols(self) -> List[str]:
        """Get priority symbols to scan based on current session."""
        session = self.get_current_session()
        
        priority_maps = {
            'asia': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            'europe': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
            'overlap': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'],
            'us': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            'weekend': ['BTCUSDT', 'ETHUSDT']
        }
        
        return priority_maps.get(session, config.SYMBOLS)
        
    def adjust_confidence_by_time(self, confidence: float) -> float:
        """Adjust signal confidence based on time factors."""
        session = self.get_current_session()
        characteristics = self.get_session_characteristics(session)
        
        # Base adjustment by session
        if session == 'overlap':
            time_multiplier = 1.1  # Higher confidence during high-activity overlap
        elif session in ['europe', 'us']:
            time_multiplier = 1.05  # Slightly higher during main sessions
        elif session == 'asia':
            time_multiplier = 1.0   # Normal confidence
        elif session == 'weekend':
            time_multiplier = 0.8   # Lower confidence on weekends
        else:
            time_multiplier = 0.9   # Conservative for unknown periods
            
        # Reduce confidence during major news times
        if self.is_major_news_time():
            time_multiplier *= 0.85  # 15% reduction during news
            
        adjusted_confidence = confidence * time_multiplier
        return min(adjusted_confidence, 1.0)
        
    def get_optimal_scan_frequency(self) -> int:
        """Get optimal scanning frequency in minutes based on session."""
        session = self.get_current_session()
        
        frequencies = {
            'overlap': 15,     # Every 15 minutes during high activity
            'europe': 20,      # Every 20 minutes
            'us': 20,          # Every 20 minutes
            'asia': 30,        # Every 30 minutes
            'weekend': 60      # Every hour on weekends
        }
        
        return frequencies.get(session, 30)
        
    def should_increase_position_size(self) -> bool:
        """Determine if position size should be increased based on session."""
        session = self.get_current_session()
        
        # Increase position size during high-activity sessions
        return session in ['overlap', 'europe', 'us']
        
    def get_session_trading_hours_remaining(self) -> float:
        """Get hours remaining in current trading session."""
        current_time = datetime.utcnow()
        session = self.get_current_session()
        
        session_ends = {
            'asia': 8,
            'europe': 13,  # When overlap starts
            'overlap': 16,
            'us': 24,  # Continuous, but traditionally ends at midnight
            'weekend': 24  # Continuous
        }
        
        end_hour = session_ends.get(session, 24)
        
        if session == 'us' and current_time.hour >= 17:
            # US session from 17:00 to 24:00
            hours_remaining = 24 - current_time.hour + (60 - current_time.minute) / 60
        else:
            hours_remaining = end_hour - current_time.hour - current_time.minute / 60
            
        return max(hours_remaining, 0)
        
    def get_session_summary(self) -> Dict:
        """Get comprehensive summary of current session."""
        session = self.get_current_session()
        characteristics = self.get_session_characteristics(session)
        should_trade, reason = self.should_trade_now()
        next_change, next_session = self.get_next_session_change()
        
        return {
            'current_session': session,
            'characteristics': characteristics,
            'should_trade': should_trade,
            'trade_reason': reason,
            'hours_remaining': self.get_session_trading_hours_remaining(),
            'next_session_change': next_change.isoformat(),
            'next_session': next_session,
            'is_news_time': self.is_major_news_time(),
            'risk_adjustment': self.get_risk_adjustment(),
            'optimal_scan_frequency': self.get_optimal_scan_frequency(),
            'priority_symbols': self.get_hourly_priority_symbols()
        } 