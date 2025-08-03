"""
Test script for crypto news API functionality
"""

import asyncio
import json
import logging
from data_sources.news_api import get_crypto_news, NewsProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_news_api():
    """Test the crypto news API."""
    print("🚀 Testing Crypto News API...")
    print("=" * 50)
    
    try:
        # Get crypto news
        print("📰 Fetching crypto news...")
        news_articles = await get_crypto_news(limit=5)
        
        print(f"✅ Successfully fetched {len(news_articles)} news articles!")
        print()
        
        if news_articles:
            print("📋 Latest Crypto News:")
            print("-" * 40)
            
            for i, article in enumerate(news_articles[:3], 1):
                print(f"{i}. 📰 {article['title']}")
                print(f"   🏷️  Source: {article['source']}")
                print(f"   📊 Sentiment: {article['sentiment']} | Impact: {article['impact']}")
                print(f"   🔗 {article['url']}")
                if article.get('keywords'):
                    print(f"   🏷️  Keywords: {', '.join(article['keywords'][:3])}")
                print()
            
            # Test news processing
            print("🧠 Processing news for AI analysis...")
            processor = NewsProcessor()
            processed = processor.process_news_for_ai(news_articles)
            
            print("📊 News Analysis Results:")
            print(f"   📈 Overall Sentiment: {processed['sentiment_summary']}")
            print(f"   ⚡ Impact Level: {processed['impact_level']}")
            print(f"   🎯 Key Themes: {', '.join(processed['key_themes'][:5])}")
            print(f"   📰 Total Articles: {processed['total_articles']}")
            print(f"   📡 Sources: {', '.join(processed['sources'])}")
            
        else:
            print("❌ No news articles fetched")
            
    except Exception as e:
        print(f"❌ Error testing news API: {e}")
        
    print("\n" + "=" * 50)
    print("🎯 News API test completed!")

if __name__ == "__main__":
    asyncio.run(test_news_api()) 