#!/usr/bin/env python3
"""
Test script for alternative APIs.
"""

import asyncio
import sys
sys.path.append('.')

from data_sources.alternative_apis import AlternativeAPIs

async def test_alternative_apis():
    print("🚀 Testing Alternative APIs...")
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    try:
        async with AlternativeAPIs() as alt_apis:
            print("🔄 Testing all alternative sources...")
            
            # Test individual APIs
            coincap_data = await alt_apis.get_coincap_data(symbols)
            print(f"CoinCap: {len(coincap_data)} symbols")
            
            kraken_data = await alt_apis.get_kraken_data(symbols)
            print(f"Kraken: {len(kraken_data)} symbols")
            
            kucoin_data = await alt_apis.get_kucoin_data(symbols)
            print(f"KuCoin: {len(kucoin_data)} symbols")
            
            bybit_data = await alt_apis.get_bybit_data(symbols)
            print(f"Bybit: {len(bybit_data)} symbols")
            
            # Test combined
            all_data = await alt_apis.get_all_alternative_data(symbols)
            print(f"\n✅ Combined result: {len(all_data)} symbols")
            
            for symbol, info in all_data.items():
                price = info.get('price', 0)
                source = info.get('source', 'unknown')
                print(f"  {symbol}: ${price:.2f} from {source}")
                
            return len(all_data) > 0
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_alternative_apis())
    if success:
        print("\n🎉 Alternative APIs are working!")
    else:
        print("\n❌ Alternative APIs failed")
    sys.exit(0 if success else 1) 