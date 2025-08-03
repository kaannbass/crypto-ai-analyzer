#!/usr/bin/env python3
"""
Enhanced real-time monitoring script for crypto trading signals with WebSocket integration.
"""

import json
import time
import os
import threading
from datetime import datetime
from binance_websocket_client import BinanceWebSocketClient


class EnhancedCryptoMonitor:
    def __init__(self):
        self.websocket_client = None
        self.monitoring = False
        self.latest_live_prices = {}
        
    def load_signals(self):
        """Load latest signals from file."""
        try:
            with open('data/signals.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def load_prices(self):
        """Load latest price data."""
        try:
            with open('data/prices.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_live_feed(self, limit=10):
        """Load latest live feed data from WebSocket logs."""
        try:
            with open('crypto_feed.jsonl', 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-limit:] if len(lines) >= limit else lines
                
                feed_data = []
                for line in recent_lines:
                    try:
                        feed_data.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
                        
                return feed_data
        except FileNotFoundError:
            return []

    def start_websocket_client(self):
        """Start WebSocket client for live data."""
        symbols = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "adausdt"]
        self.websocket_client = BinanceWebSocketClient(
            symbols=symbols,
            log_file="crypto_feed.jsonl"
        )
        self.websocket_client.start()
        print("🔗 WebSocket client started for live data...")

    def stop_websocket_client(self):
        """Stop WebSocket client."""
        if self.websocket_client:
            self.websocket_client.stop()
            print("🔌 WebSocket client stopped")

    def get_live_prices(self):
        """Get current live prices from WebSocket client."""
        if self.websocket_client:
            return self.websocket_client.get_latest_prices()
        return {}

    def print_header(self):
        """Print header."""
        print("\n" + "="*80)
        print("🔍 CRYPTO AI ANALYZER - ENHANCED LIVE MONITORING")
        print("="*80)

    def print_live_prices(self):
        """Print real-time prices from WebSocket."""
        live_prices = self.get_live_prices()
        
        if live_prices:
            print("\n💹 LIVE PRICES (WebSocket):")
            for symbol, price in live_prices.items():
                # Get previous price for change calculation
                prev_price = self.latest_live_prices.get(symbol, price)
                change = ((price - prev_price) / prev_price * 100) if prev_price != price else 0
                
                change_icon = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
                
                print(f"{change_icon} {symbol}: ${price:,.4f} ({change:+.3f}%)")
                
                # Update latest prices
                self.latest_live_prices[symbol] = price
        else:
            print("\n💹 LIVE PRICES: Connecting to WebSocket...")

    def print_api_prices(self, price_data):
        """Print API-based prices."""
        if not price_data or 'data' not in price_data:
            print("❌ No API price data available")
            return
            
        print("\n💰 API PRICES:")
        data = price_data['data']
        
        for symbol, info in data.items():
            price = info.get('price', 0)
            change = info.get('change_24h', 0)
            volume = info.get('volume', 0)
            source = info.get('source', 'unknown')
            
            change_icon = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
            
            print(f"{change_icon} {symbol}: ${price:,.2f} ({change:+.2%}) "
                  f"Vol: ${volume:,.0f} [{source}]")

    def print_live_feed_summary(self):
        """Print summary of recent live feed activity."""
        feed_data = self.load_live_feed(20)
        
        if not feed_data:
            print("\n📡 LIVE FEED: No data available")
            return
            
        print(f"\n📡 LIVE FEED ACTIVITY (last {len(feed_data)} ticks):")
        
        # Group by symbol
        symbol_activity = {}
        for record in feed_data:
            symbol = record.get('symbol')
            if symbol not in symbol_activity:
                symbol_activity[symbol] = []
            symbol_activity[symbol].append(record)
        
        for symbol, records in symbol_activity.items():
            latest = records[-1]
            count = len(records)
            latest_price = latest.get('price', 0)
            latest_time = datetime.fromtimestamp(latest.get('timestamp', 0)).strftime('%H:%M:%S')
            
            print(f"📊 {symbol}: {count} ticks, Latest: ${latest_price:,.4f} at {latest_time}")

    def print_latest_signals(self, signals, limit=3):
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

    def print_stats(self, signals):
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

    def print_websocket_status(self):
        """Print WebSocket connection status."""
        if self.websocket_client and self.websocket_client.is_running():
            print("🟢 WebSocket Status: CONNECTED")
        else:
            print("🔴 WebSocket Status: DISCONNECTED")

    def monitor_loop(self):
        """Main monitoring loop."""
        self.print_header()
        
        # Start WebSocket client
        self.start_websocket_client()
        time.sleep(2)  # Give it time to connect
        
        last_signal_count = 0
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                # Clear screen (works on most terminals)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                self.print_header()
                print(f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Print WebSocket status
                self.print_websocket_status()
                
                # Load and display data
                price_data = self.load_prices()
                signals = self.load_signals()
                
                # Display real-time prices first
                self.print_live_prices()
                
                # Display API prices
                self.print_api_prices(price_data)
                
                # Display live feed summary
                self.print_live_feed_summary()
                
                # Display signals
                self.print_latest_signals(signals)
                self.print_stats(signals)
                
                # Check for new signals
                current_signal_count = len(signals)
                if current_signal_count > last_signal_count:
                    new_signals = current_signal_count - last_signal_count
                    print(f"\n🔔 {new_signals} new signal(s) detected!")
                    last_signal_count = current_signal_count
                
                print(f"\n⏱️  Refreshing in 10 seconds... (Ctrl+C to exit)")
                print("📡 Real-time WebSocket data updating continuously...")
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped. Goodbye!")
            self.monitoring = False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)
        finally:
            self.stop_websocket_client()

    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.monitoring = False
        self.stop_websocket_client()


def main():
    """Main function to run the enhanced monitor."""
    monitor = EnhancedCryptoMonitor()
    
    try:
        monitor.monitor_loop()
    except Exception as e:
        print(f"Monitor error: {e}")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main() 