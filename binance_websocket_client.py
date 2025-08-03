import json
import time
import threading
import websocket
from collections import deque, defaultdict
from datetime import datetime
import logging
from typing import Dict, Optional, List


class BinanceWebSocketClient:
    def __init__(self, symbols=None, log_file="crypto_feed.jsonl"):
        self.symbols = symbols or ["btcusdt", "ethusdt", "solusdt"]
        self.log_file = log_file
        self.ws = None
        self.running = False
        self.thread = None
        
        # Price tracking for pump detection
        self.price_history = defaultdict(lambda: deque(maxlen=5))
        
        # Reconnection settings
        self.reconnect_delay = 1
        self.max_reconnect_delay = 60
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def get_stream_url(self):
        """Build WebSocket URL for multiple streams"""
        streams = [f"{symbol}@trade" for symbol in self.symbols]
        stream_names = "/".join(streams)
        return f"wss://stream.binance.com:9443/ws/{stream_names}"
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Extract trade data
            symbol = data.get('s', '').upper()
            price = float(data.get('p', 0))
            timestamp = int(time.time())
            event_type = data.get('e', 'trade')
            
            # Log to file
            self.log_trade_data(symbol, price, timestamp, event_type)
            
            # Update price history and check for pumps
            self.update_price_history(symbol, price)
            self.check_pump(symbol)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def log_trade_data(self, symbol, price, timestamp, event_type):
        """Append trade data to JSONL file"""
        try:
            trade_record = {
                "symbol": symbol,
                "price": price,
                "timestamp": timestamp,
                "event_type": event_type
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(trade_record) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error logging trade data: {e}")
    
    def update_price_history(self, symbol, price):
        """Update price history for pump detection"""
        self.price_history[symbol].append(price)
    
    def check_pump(self, symbol):
        """Check for pump based on last 5 prices"""
        prices = self.price_history[symbol]
        
        if len(prices) >= 5:
            oldest_price = prices[0]
            newest_price = prices[-1]
            
            if oldest_price > 0:
                percentage_change = ((newest_price - oldest_price) / oldest_price) * 100
                
                if percentage_change > 3.0:
                    print(f"🚀 PUMP ALERT: {symbol} +{percentage_change:.2f}% in last 5 ticks")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        self.logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.logger.warning("WebSocket connection closed")
        if self.running:
            self.reconnect()
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        self.logger.info("WebSocket connection opened")
        self.reconnect_delay = 1  # Reset reconnect delay on successful connection
    
    def reconnect(self):
        """Reconnect with exponential backoff"""
        if not self.running:
            return
            
        self.logger.info(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
        time.sleep(self.reconnect_delay)
        
        # Exponential backoff
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
        if self.running:
            self.connect()
    
    def connect(self):
        """Establish WebSocket connection"""
        try:
            websocket.enableTrace(False)
            self.ws = websocket.WebSocketApp(
                self.get_stream_url(),
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            self.ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            if self.running:
                self.reconnect()
    
    def start(self):
        """Start WebSocket client in a separate thread"""
        if self.running:
            self.logger.warning("Client is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self.connect, daemon=True)
        self.thread.start()
        self.logger.info("WebSocket client started")
    
    def stop(self):
        """Stop WebSocket client"""
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        self.logger.info("WebSocket client stopped")
    
    def is_running(self):
        """Check if client is running"""
        return self.running and self.thread and self.thread.is_alive()
    
    def get_latest_prices(self):
        """Get latest prices for all symbols"""
        latest_prices = {}
        for symbol, prices in self.price_history.items():
            if prices:
                latest_prices[symbol] = prices[-1]
        return latest_prices


# Usage example
if __name__ == "__main__":
    # Initialize client
    client = BinanceWebSocketClient(
        symbols=["btcusdt", "ethusdt", "solusdt"],
        log_file="crypto_live_feed.jsonl"
    )
    
    try:
        # Start the client
        client.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.stop() 