"""
News processing utilities for crypto analysis.
"""

try:
    from data_sources.news_api import CryptoNewsAPI
    NEWS_API_AVAILABLE = True
except ImportError:
    NEWS_API_AVAILABLE = False


class NewsProcessor:
    """News processor for crypto sentiment analysis."""
    
    def __init__(self):
        self.available = NEWS_API_AVAILABLE
    
    async def get_crypto_news(self, limit=20):
        """Get crypto news from API."""
        if not self.available:
            return None
        
        async with CryptoNewsAPI() as news_api:
            return await news_api.get_crypto_news(limit)
    
    def process_news_for_ai(self, news_data):
        """Process news data for AI analysis."""
        if not news_data:
            return {
                "sentiment_summary": "neutral", 
                "impact_level": "low", 
                "key_themes": [], 
                "total_articles": 0
            }
        
        # Simple sentiment analysis based on keywords
        positive_keywords = ["surge", "rally", "bull", "gain", "rise", "up", "positive", "adoption"]
        negative_keywords = ["drop", "fall", "crash", "bear", "down", "negative", "ban", "hack"]
        
        positive_count = 0
        negative_count = 0
        
        for article in news_data:
            title = article.get('title', '').lower()
            content = article.get('description', '').lower()
            text = f"{title} {content}"
            
            positive_count += sum(1 for keyword in positive_keywords if keyword in text)
            negative_count += sum(1 for keyword in negative_keywords if keyword in text)
        
        total_articles = len(news_data)
        
        # Determine sentiment
        if positive_count > negative_count * 1.2:
            sentiment = "bullish"
            impact = "high" if positive_count > 10 else "medium"
        elif negative_count > positive_count * 1.2:
            sentiment = "bearish" 
            impact = "high" if negative_count > 10 else "medium"
        else:
            sentiment = "neutral"
            impact = "low"
        
        # Extract key themes (simplified)
        themes = []
        if positive_count > 5:
            themes.append("positive_sentiment")
        if negative_count > 5:
            themes.append("negative_sentiment")
        
        return {
            "sentiment_summary": sentiment,
            "impact_level": impact,
            "key_themes": themes,
            "total_articles": total_articles,
            "positive_signals": positive_count,
            "negative_signals": negative_count
        } 