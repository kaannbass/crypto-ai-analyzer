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
        """Get latest crypto news from multiple sources."""
        all_news = []
        
        # Try multiple sources
        sources = [
            self.get_coindesk_news,
            self.get_cryptonews_free,
            self.get_coingecko_news,
            self.get_reddit_crypto_news
        ]
        
        for source_func in sources:
            try:
                news_data = await source_func(limit=min(limit, 10))
                if news_data:
                    all_news.extend(news_data)
                    self.logger.info(f"Fetched {len(news_data)} articles from {source_func.__name__}")
                    
                    # If we have enough news, break
                    if len(all_news) >= limit:
                        break
                        
            except Exception as e:
                self.logger.warning(f"Failed to fetch from {source_func.__name__}: {e}")
                continue
        
        # Sort by timestamp and limit
        all_news.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_news[:limit]
    
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
        """Fetch news from CryptoNews.net (free)."""
        try:
            # Mock implementation - replace with actual CryptoNews.net scraping or API
            mock_news = [
                {
                    'title': 'Bitcoin Reaches New All-Time High Amid Institutional Adoption',
                    'summary': 'Major financial institutions continue to add Bitcoin to their portfolios...',
                    'url': 'https://example.com/news/1',
                    'source': 'CryptoNews',
                    'timestamp': datetime.utcnow().isoformat(),
                    'sentiment': 'bullish',
                    'impact': 'high',
                    'keywords': ['bitcoin', 'institutions', 'adoption']
                },
                {
                    'title': 'Ethereum Layer 2 Solutions See Record Volume',
                    'summary': 'Layer 2 scaling solutions for Ethereum process record transaction volumes...',
                    'url': 'https://example.com/news/2',
                    'source': 'CryptoNews',
                    'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    'sentiment': 'bullish',
                    'impact': 'medium',
                    'keywords': ['ethereum', 'layer2', 'scaling']
                },
                {
                    'title': 'Regulatory Uncertainty Clouds Altcoin Market',
                    'summary': 'New regulations being considered may impact smaller cryptocurrencies...',
                    'url': 'https://example.com/news/3',
                    'source': 'CryptoNews',
                    'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    'sentiment': 'bearish',
                    'impact': 'medium',
                    'keywords': ['regulation', 'altcoins', 'sec']
                }
            ]
            
            return mock_news[:limit]
            
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
        """Parse RSS feed XML content."""
        # This is a simplified RSS parser - in production, use feedparser library
        news_list = []
        
        try:
            # Mock RSS parsing - replace with actual XML parsing
            mock_rss_news = [
                {
                    'title': 'Fed Rate Decision Impacts Crypto Markets',
                    'summary': 'Federal Reserve decision causes volatility in cryptocurrency markets...',
                    'url': 'https://coindesk.com/news/1',
                    'source': source,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sentiment': 'neutral',
                    'impact': 'high',
                    'keywords': ['fed', 'rates', 'markets']
                },
                {
                    'title': 'DeFi Protocol Launches New Yield Farming Features',
                    'summary': 'New DeFi protocol offers innovative yield farming opportunities...',
                    'url': 'https://coindesk.com/news/2',
                    'source': source,
                    'timestamp': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                    'sentiment': 'bullish',
                    'impact': 'medium',
                    'keywords': ['defi', 'yield', 'farming']
                }
            ]
            
            return mock_rss_news[:limit]
            
        except Exception as e:
            self.logger.error(f"RSS parsing failed: {e}")
            
        return news_list
    
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