#!/usr/bin/env python3
"""
Real-time monitoring script for crypto trading signals.
"""

import json
import time
import os
from datetime import datetime


def load_signals():
    """Load latest signals from file."""
    try:
        with open('data/signals.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def load_prices():
    """Load latest price data."""
    try:
        with open('data/prices.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def print_header():
    """Print header."""
    print("\n" + "="*70)
    print("🔍 CRYPTO AI ANALYZER - LIVE MONITORING")
    print("="*70)


def print_prices(price_data):
    """Print current prices."""
    if not price_data or 'data' not in price_data:
        print("❌ No price data available")
        return
        
    print("\n💰 CURRENT PRICES:")
    data = price_data['data']
    
    for symbol, info in data.items():
        price = info.get('price', 0)
        change = info.get('change_24h', 0)
        volume = info.get('volume', 0)
        source = info.get('source', 'unknown')
        
        change_icon = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
        
        print(f"{change_icon} {symbol}: ${price:,.2f} ({change:+.2%}) "
              f"Vol: ${volume:,.0f} [{source}]")


def print_latest_signals(signals, limit=3):
    """Print latest trading signals."""
    if not signals:
        print("\n📊 No signals available")
        return
        
    print(f"\n🎯 LATEST SIGNALS (last {limit}):")
    
    # Get the last few signals
    recent_signals = signals[-limit:] if len(signals) >= limit else signals
    
    for i, signal in enumerate(reversed(recent_signals), 1):
        symbol = signal.get('symbol', 'Unknown')
        action = signal.get('action', 'WAIT')
        confidence = signal.get('confidence', 0)
        reasoning = signal.get('reasoning', 'No reason provided')
        timestamp = signal.get('timestamp', '')
        
        # Format timestamp
        try:
            ts = datetime.fromisoformat(timestamp)
            time_str = ts.strftime("%H:%M:%S")
        except:
            time_str = timestamp[:8] if timestamp else "Unknown"
            
        action_icon = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
        
        print(f"{action_icon} {symbol}: {action} (conf: {confidence:.2f}) [{time_str}]")
        print(f"   💬 {reasoning[:60]}{'...' if len(reasoning) > 60 else ''}")


def print_stats(signals):
    """Print trading statistics."""
    if not signals:
        return
        
    total = len(signals)
    buy_signals = sum(1 for s in signals if s.get('action') == 'BUY')
    sell_signals = sum(1 for s in signals if s.get('action') == 'SELL')
    wait_signals = sum(1 for s in signals if s.get('action') == 'WAIT')
    
    avg_confidence = sum(s.get('confidence', 0) for s in signals) / total if total > 0 else 0
    
    print(f"\n📈 STATISTICS:")
    print(f"Total Signals: {total} | BUY: {buy_signals} | SELL: {sell_signals} | WAIT: {wait_signals}")
    print(f"Average Confidence: {avg_confidence:.2f}")


def monitor_loop():
    """Main monitoring loop."""
    print_header()
    
    last_signal_count = 0
    
    while True:
        try:
            # Clear screen (works on most terminals)
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print_header()
            print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Load and display data
            price_data = load_prices()
            signals = load_signals()
            
            print_prices(price_data)
            print_latest_signals(signals)
            print_stats(signals)
            
            # Check for new signals
            current_signal_count = len(signals)
            if current_signal_count > last_signal_count:
                new_signals = current_signal_count - last_signal_count
                print(f"\n🔔 {new_signals} new signal(s) detected!")
                last_signal_count = current_signal_count
            
            print(f"\n⏱️  Refreshing in 30 seconds... (Ctrl+C to exit)")
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    monitor_loop() 