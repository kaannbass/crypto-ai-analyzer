"""
Crypto news API client for fetching latest cryptocurrency news and sentiment.
Supports multiple news sources with fallback mechanisms.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import config


class CryptoNewsAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_crypto_news(self, limit: int = 20) -> List[Dict]:
        """Get crypto news from multiple sources - REAL DATA ONLY."""
        try:
            self.logger.info(f"🔄 Fetching REAL crypto news from live sources only...")
            all_news = []
            
            # Try CryptoNews.net first (if available)
            try:
                cryptonews_data = await self._get_cryptonews_net(limit)
                if cryptonews_data:
                    all_news.extend(cryptonews_data)
                    self.logger.info(f"✅ Got {len(cryptonews_data)} articles from CryptoNews.net")
            except Exception as e:
                self.logger.warning(f"CryptoNews.net failed: {e}")
            
            # Try RSS feeds
            try:
                rss_data = await self._get_rss_news(limit)
                if rss_data:
                    all_news.extend(rss_data)
                    self.logger.info(f"✅ Got {len(rss_data)} articles from RSS feeds")
            except Exception as e:
                self.logger.warning(f"RSS feeds failed: {e}")
            
            # If no real news data available, return empty list
            if not all_news:
                self.logger.error("🚫 NO REAL NEWS DATA AVAILABLE - returning empty list")
                return []
            
            # Remove duplicates and sort by date
            seen_titles = set()
            unique_news = []
            for article in all_news:
                title = article.get('title', '').lower()
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_news.append(article)
            
            # Sort by date (newest first)
            unique_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            self.logger.info(f"✅ Returning {len(unique_news[:limit])} real news articles")
            return unique_news[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching crypto news: {e}")
            return []  # Return empty list instead of mock data

    async def _get_cryptonews_net(self, limit: int) -> List[Dict]:
        """Get news from CryptoNews.net - REAL API ONLY."""
        try:
            # This would need actual CryptoNews.net API implementation
            # For now, return empty list since no real API is implemented
            self.logger.warning("CryptoNews.net API not implemented - no mock data returned")
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching from CryptoNews.net: {e}")
            return []
    
    async def get_coindesk_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from CoinDesk (free RSS feed)."""
        try:
            url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    return self.parse_rss_feed(content, source="CoinDesk", limit=limit)
                    
        except Exception as e:
            self.logger.error(f"CoinDesk news fetch failed: {e}")
            
        return []
    
    async def get_cryptonews_free(self, limit: int = 10) -> List[Dict]:
        """Fetch news from CryptoNews.net (free) - REAL DATA ONLY."""
        try:
            # No real API implementation available - return empty list
            self.logger.warning("CryptoNews free API not implemented - no mock data returned")
            return []
            
        except Exception as e:
            self.logger.error(f"CryptoNews fetch failed: {e}")
            return []
    
    async def get_coingecko_news(self, limit: int = 10) -> List[Dict]:
        """Fetch news from CoinGecko API (free tier)."""
        try:
            url = "https://api.coingecko.com/api/v3/news"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    news_list = []
                    
                    for article in data.get('data', [])[:limit]:
                        news_item = {
                            'title': article.get('title', ''),
                            'summary': article.get('description', '')[:200] + '...' if article.get('description') else '',
                            'url': article.get('url', ''),
                            'source': 'CoinGecko',
                            'timestamp': article.get('created_at', datetime.utcnow().isoformat()),
                            'sentiment': self.analyze_basic_sentiment(article.get('title', '')),
                            'impact': 'medium',
                            'keywords': self.extract_keywords(article.get('title', ''))
                        }
                        news_list.append(news_item)
                    
                    return news_list
                    
        except Exception as e:
            self.logger.error(f"CoinGecko news fetch failed: {e}")
            
        return []
    
    async def get_reddit_crypto_news(self, limit: int = 5) -> List[Dict]:
        """Fetch top posts from r/cryptocurrency (free Reddit API)."""
        try:
            url = "https://www.reddit.com/r/cryptocurrency/hot.json?limit=10"
            headers = {'User-Agent': 'CryptoAnalyzer/1.0'}
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    news_list = []
                    
                    for post in data.get('data', {}).get('children', [])[:limit]:
                        post_data = post.get('data', {})
                        
                        # Filter out low-quality posts
                        if post_data.get('score', 0) < 10:
                            continue
                            
                        news_item = {
                            'title': post_data.get('title', ''),
                            'summary': post_data.get('selftext', '')[:200] + '...' if post_data.get('selftext') else '',
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'source': 'Reddit r/cryptocurrency',
                            'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                            'sentiment': self.analyze_basic_sentiment(post_data.get('title', '')),
                            'impact': 'low',
                            'keywords': self.extract_keywords(post_data.get('title', '')),
                            'score': post_data.get('score', 0)
                        }
                        news_list.append(news_item)
                    
                    return news_list
                    
        except Exception as e:
            self.logger.error(f"Reddit crypto news fetch failed: {e}")
            
        return []
    
    def parse_rss_feed(self, xml_content: str, source: str, limit: int = 10) -> List[Dict]:
        """Parse RSS feed XML content - REAL DATA ONLY."""
        news_list = []
        
        try:
            # No real RSS parsing implementation - return empty list
            self.logger.warning("RSS parsing not implemented - no mock data returned")
            return []
            
        except Exception as e:
            self.logger.error(f"RSS parsing failed: {e}")
            return []
    
    def analyze_basic_sentiment(self, text: str) -> str:
        """Basic sentiment analysis based on keywords."""
        text = text.lower()
        
        bullish_words = ['bullish', 'moon', 'pump', 'surge', 'rally', 'breakout', 'adoption', 'buy', 'green', 'up', 'rise', 'positive', 'bull']
        bearish_words = ['bearish', 'crash', 'dump', 'fall', 'drop', 'bear', 'red', 'down', 'sell', 'negative', 'decline']
        
        bullish_count = sum(1 for word in bullish_words if word in text)
        bearish_count = sum(1 for word in bearish_words if word in text)
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract crypto-related keywords from text."""
        text = text.lower()
        
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'bnb', 'ada', 'sol', 'solana',
            'defi', 'nft', 'dao', 'web3', 'blockchain', 'crypto', 'cryptocurrency',
            'altcoin', 'stablecoin', 'trading', 'exchange', 'wallet', 'mining',
            'halving', 'fork', 'consensus', 'smart contract', 'dapp', 'yield',
            'staking', 'liquidity', 'market', 'volume', 'regulation', 'sec'
        ]
        
        found_keywords = [keyword for keyword in crypto_keywords if keyword in text]
        return found_keywords[:5]  # Return max 5 keywords


async def get_crypto_news(limit: int = 20) -> List[Dict]:
    """Main function to get crypto news."""
    async with CryptoNewsAPI() as news_api:
        return await news_api.get_crypto_news(limit=limit)


# Enhanced news analysis for AI integration
class NewsProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_news_for_ai(self, news_list: List[Dict]) -> Dict:
        """Process news data for AI analysis."""
        if not news_list:
            return {
                'headlines': [],
                'sentiment_summary': 'neutral',
                'impact_level': 'low',
                'key_themes': []
            }
        
        # Analyze overall sentiment
        sentiments = [news.get('sentiment', 'neutral') for news in news_list]
        bullish_count = sentiments.count('bullish')
        bearish_count = sentiments.count('bearish')
        
        if bullish_count > bearish_count:
            overall_sentiment = 'bullish'
        elif bearish_count > bullish_count:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        # Extract key themes
        all_keywords = []
        for news in news_list:
            all_keywords.extend(news.get('keywords', []))
        
        # Count keyword frequency
        keyword_count = {}
        for keyword in all_keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
        
        # Get top themes
        key_themes = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:5]
        key_themes = [theme[0] for theme in key_themes]
        
        # Determine impact level
        high_impact_count = sum(1 for news in news_list if news.get('impact') == 'high')
        impact_level = 'high' if high_impact_count > 0 else 'medium' if len(news_list) > 5 else 'low'
        
        return {
            'headlines': [news.get('title', '') for news in news_list[:10]],
            'sentiment_summary': overall_sentiment,
            'impact_level': impact_level,
            'key_themes': key_themes,
            'total_articles': len(news_list),
            'sources': list(set(news.get('source', '') for news in news_list))
        }


if __name__ == "__main__":
    # Test the news API
    async def test_news():
        news = await get_crypto_news(limit=10)
        print(f"Fetched {len(news)} news articles:")
        for article in news[:3]:
            print(f"- {article['title']} ({article['source']})")
            print(f"  Sentiment: {article['sentiment']}, Impact: {article['impact']}")
        
        # Test news processing
        processor = NewsProcessor()
        processed = processor.process_news_for_ai(news)
        print(f"\nProcessed Summary:")
        print(f"Overall Sentiment: {processed['sentiment_summary']}")
        print(f"Key Themes: {', '.join(processed['key_themes'])}")
    
    asyncio.run(test_news()) 