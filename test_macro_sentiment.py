"""
Test script for the new macro sentiment analysis functionality.
Demonstrates how the enhanced AI prompting system works.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List

from llm.aggregator import AIAggregator


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sample_market_data() -> Dict:
    """Generate sample market data for testing."""
    return {
        'BTCUSDT': {
            'price': 114282.00,
            'change_24h': 0.0192,  # +1.92%
            'volume': 26433805632,
            'volume_change_24h': 0.15  # +15% volume
        },
        'ETHUSDT': {
            'price': 3493.22,
            'change_24h': 0.0302,  # +3.02%
            'volume': 20030973494,
            'volume_change_24h': 0.08  # +8% volume
        },
        'BNBUSDT': {
            'price': 751.78,
            'change_24h': -0.001,  # -0.1%
            'volume': 1831227672,
            'volume_change_24h': -0.05  # -5% volume
        },
        'ADAUSDT': {
            'price': 0.723775,
            'change_24h': 0.012,  # +1.2%
            'volume': 759099914,
            'volume_change_24h': 0.03  # +3% volume
        },
        'SOLUSDT': {
            'price': 245.67,
            'change_24h': -0.025,  # -2.5%
            'volume': 1245678901,
            'volume_change_24h': 0.22  # +22% volume (unusual)
        }
    }


def get_sample_news_data() -> List[Dict]:
    """Generate sample news data for testing."""
    return [
        {
            'headline': 'Federal Reserve hints at potential rate cuts in Q2 2025',
            'sentiment': 'bullish',
            'impact': 'high',
            'timestamp': '2025-08-03T20:00:00Z'
        },
        {
            'headline': 'Major crypto exchange announces new institutional custody services',
            'sentiment': 'bullish',
            'impact': 'medium',
            'timestamp': '2025-08-03T18:30:00Z'
        },
        {
            'headline': 'SEC delays decision on spot Bitcoin ETF applications',
            'sentiment': 'bearish',
            'impact': 'medium',
            'timestamp': '2025-08-03T16:15:00Z'
        },
        {
            'headline': 'Ethereum layer 2 adoption reaches new all-time high',
            'sentiment': 'bullish',
            'impact': 'low',
            'timestamp': '2025-08-03T14:00:00Z'
        }
    ]


def get_sample_events_data() -> List[Dict]:
    """Generate sample crypto events data for testing."""
    return [
        {
            'event': 'Bitcoin halving countdown',
            'days_remaining': 190,
            'impact': 'high',
            'type': 'protocol'
        },
        {
            'event': 'Ethereum Dencun upgrade',
            'days_remaining': 30,
            'impact': 'medium',
            'type': 'upgrade'
        },
        {
            'event': 'Major altcoin exchange listing',
            'days_remaining': 7,
            'impact': 'low',
            'type': 'listing'
        }
    ]


async def test_basic_analysis():
    """Test basic AI aggregator functionality."""
    logger.info("=== Testing Basic Daily Analysis ===")
    
    aggregator = AIAggregator()
    market_data = get_sample_market_data()
    
    try:
        result = await aggregator.get_daily_analysis(market_data)
        
        if result:
            logger.info("✅ Basic analysis completed successfully")
            logger.info(f"Participating models: {result.get('participating_models', [])}")
            logger.info(f"Number of signals: {len(result.get('signals', []))}")
            
            # Show sample signals
            signals = result.get('signals', [])
            for signal in signals[:3]:  # Show first 3 signals
                logger.info(f"  {signal.get('symbol')}: {signal.get('action')} (conf: {signal.get('confidence', 0):.2f})")
                
        else:
            logger.warning("❌ No basic analysis results (expected - API keys not configured)")
            
    except Exception as e:
        logger.error(f"❌ Basic analysis failed: {e}")


async def test_macro_sentiment_analysis():
    """Test the new macro sentiment analysis functionality."""
    logger.info("\n=== Testing Macro Sentiment Analysis ===")
    
    aggregator = AIAggregator()
    market_data = get_sample_market_data()
    news_data = get_sample_news_data()
    events_data = get_sample_events_data()
    
    try:
        result = await aggregator.get_macro_sentiment_analysis(
            market_data, news_data, events_data
        )
        
        if result:
            logger.info("✅ Macro sentiment analysis completed successfully")
            
            # Display results
            sentiment = result.get('market_sentiment', {})
            logger.info(f"Market Sentiment:")
            logger.info(f"  Short-term: {sentiment.get('short_term', 'Unknown')}")
            logger.info(f"  Medium-term: {sentiment.get('medium_term', 'Unknown')}")
            logger.info(f"  Confidence: {sentiment.get('confidence', 'Unknown')}")
            
            logger.info(f"Volatility: {result.get('volatility', 'Unknown')}")
            
            # Show signals
            signals = result.get('signals', [])
            logger.info(f"\nSignals Generated ({len(signals)}):")
            for signal in signals:
                symbol = signal.get('symbol')
                action = signal.get('action')
                conf = signal.get('confidence', 0)
                level = signal.get('confidence_level', 'Unknown')
                reason = signal.get('reason', '')[:50] + '...' if signal.get('reason', '') else ''
                
                logger.info(f"  {symbol}: {action} (conf: {conf:.2f}, {level}) - {reason}")
            
            # Show abnormal movements
            abnormal = result.get('abnormal_coins', [])
            if abnormal:
                logger.info(f"\nAbnormal Movements:")
                for coin in abnormal:
                    logger.info(f"  {coin.get('symbol')}: {coin.get('movement')} {coin.get('magnitude')}")
            
            # Show macro factors
            macro = result.get('macro_factors', {})
            if macro:
                logger.info(f"\nMacro Factors:")
                logger.info(f"  Primary Risk: {macro.get('primary_risk', 'Unknown')}")
                opportunities = macro.get('opportunities', [])
                if opportunities:
                    logger.info(f"  Opportunities: {', '.join(opportunities[:3])}")
            
            # Show risk assessment
            risk = result.get('risk_assessment', {})
            if risk:
                logger.info(f"\nRisk Assessment:")
                logger.info(f"  Market Risk: {risk.get('market_risk', 'Unknown')}")
                logger.info(f"  Overall Risk: {risk.get('overall_risk', 'Unknown')}")
                
        else:
            logger.warning("❌ No macro sentiment analysis results")
            
    except Exception as e:
        logger.error(f"❌ Macro sentiment analysis failed: {e}")


async def test_prompt_loading():
    """Test prompt template loading."""
    logger.info("\n=== Testing Prompt Template Loading ===")
    
    aggregator = AIAggregator()
    
    try:
        # Test daily prompt loading
        daily_prompt = aggregator.load_daily_prompt()
        logger.info(f"✅ Daily prompt loaded ({len(daily_prompt)} characters)")
        
        # Test macro sentiment prompt loading
        macro_prompt = aggregator.load_macro_sentiment_prompt()
        logger.info(f"✅ Macro sentiment prompt loaded ({len(macro_prompt)} characters)")
        
        # Show snippet of macro prompt
        lines = macro_prompt.split('\n')
        logger.info(f"Macro prompt preview: {lines[0] if lines else 'Empty'}")
        
    except Exception as e:
        logger.error(f"❌ Prompt loading failed: {e}")


async def test_aggregation_logic():
    """Test the aggregation logic with mock data."""
    logger.info("\n=== Testing Aggregation Logic ===")
    
    aggregator = AIAggregator()
    
    # Mock results from different models
    mock_results = {
        'openai': {
            'model': 'gpt-4-mock',
            'market_sentiment': {
                'short_term': 'Bullish',
                'medium_term': 'Neutral',
                'confidence': 'High'
            },
            'signals': [
                {
                    'symbol': 'BTCUSDT',
                    'action': 'BUY',
                    'confidence': 0.8,
                    'reason': 'Strong momentum with volume confirmation'
                }
            ],
            'macro_factors': {
                'primary_risk': 'Fed policy uncertainty',
                'opportunities': ['DeFi adoption', 'Institutional inflows']
            },
            'risk_assessment': {
                'market_risk': 'Medium',
                'liquidity_risk': 'Low'
            }
        },
        'claude': {
            'model': 'claude-3-mock',
            'market_sentiment': {
                'short_term': 'Bullish',
                'medium_term': 'Bullish',
                'confidence': 'Medium'
            },
            'signals': [
                {
                    'symbol': 'BTCUSDT',
                    'action': 'BUY',
                    'confidence': 0.7,
                    'reason': 'Technical breakout with macro support'
                }
            ],
            'macro_factors': {
                'primary_risk': 'Regulatory overhang',
                'opportunities': ['Layer 2 growth', 'ETF speculation']
            },
            'risk_assessment': {
                'market_risk': 'Low',
                'liquidity_risk': 'Low'
            }
        }
    }
    
    try:
        aggregated = aggregator.aggregate_macro_analyses(mock_results)
        
        logger.info("✅ Aggregation logic test completed")
        logger.info(f"Analysis type: {aggregated.get('analysis_type')}")
        logger.info(f"Participating models: {aggregated.get('participating_models')}")
        
        # Test sentiment aggregation
        sentiment = aggregated.get('market_sentiment', {})
        logger.info(f"Aggregated sentiment: {sentiment.get('short_term')} (confidence: {sentiment.get('confidence')})")
        
        # Test signal aggregation
        signals = aggregated.get('signals', [])
        logger.info(f"Aggregated signals: {len(signals)}")
        
        # Test macro factor aggregation
        macro = aggregated.get('macro_factors', {})
        logger.info(f"Consensus risk: {macro.get('consensus_risk', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"❌ Aggregation logic test failed: {e}")


def save_sample_output(analysis_result: Dict):
    """Save a sample analysis result for reference."""
    if analysis_result:
        try:
            with open('sample_macro_analysis.json', 'w') as f:
                json.dump(analysis_result, f, indent=2)
            logger.info("✅ Sample output saved to 'sample_macro_analysis.json'")
        except Exception as e:
            logger.error(f"❌ Failed to save sample output: {e}")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting Macro Sentiment Analysis Tests")
    logger.info("=" * 60)
    
    # Test prompt loading first
    await test_prompt_loading()
    
    # Test aggregation logic
    await test_aggregation_logic()
    
    # Test basic functionality
    await test_basic_analysis()
    
    # Test main macro sentiment functionality
    result = None
    try:
        aggregator = AIAggregator()
        market_data = get_sample_market_data()
        news_data = get_sample_news_data()
        events_data = get_sample_events_data()
        
        result = await aggregator.get_macro_sentiment_analysis(
            market_data, news_data, events_data
        )
        
        if result:
            save_sample_output(result)
            
    except Exception as e:
        logger.error(f"Main test failed: {e}")
    
    # Test the full macro sentiment analysis
    await test_macro_sentiment_analysis()
    
    logger.info("=" * 60)
    logger.info("🎯 Tests completed!")
    logger.info("\nTo enable real AI analysis:")
    logger.info("1. Set OPENAI_API_KEY environment variable")
    logger.info("2. Set CLAUDE_API_KEY environment variable")
    logger.info("3. Uncomment the actual API calls in openai_client.py and claude_client.py")


if __name__ == "__main__":
    asyncio.run(main()) 