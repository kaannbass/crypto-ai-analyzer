"""
AI Aggregator for combining multiple AI model outputs into unified decisions.
Enhanced with real AI integration, consensus building, and risk management.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

import config
from llm.openai_client import OpenAIClient
from llm.claude_client import ClaudeClient


class AIAggregator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.openai_client = OpenAIClient()
        self.claude_client = ClaudeClient()
        self.confidence_threshold = 0.6  # Minimum confidence for signals
        
    async def get_daily_analysis(self, market_data: Dict) -> Optional[Dict]:
        """Get aggregated daily analysis from all available AI models."""
        try:
            # Load daily prompt template
            prompt_template = self.load_daily_prompt()
            
            # Run AI analyses in parallel for better performance
            tasks = []
            
            if self.openai_client.is_available():
                tasks.append(('openai', self.openai_client.analyze_market_data(market_data, prompt_template)))
                self.logger.info("Queued OpenAI for daily analysis")
                
            if self.claude_client.is_available():
                tasks.append(('claude', self.claude_client.analyze_market_data(market_data, prompt_template)))
                self.logger.info("Queued Claude for daily analysis")
                
            if not tasks:
                self.logger.warning("No AI models available for analysis")
                return self.generate_fallback_analysis(market_data)
                
            # Execute analyses with extended timeout for complex analysis
            results = {}
            for model_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT * 2)
                    if result and isinstance(result, dict):
                        result['analysis_timestamp'] = datetime.utcnow().isoformat()
                        result['model_source'] = model_name
                        results[model_name] = result
                        self.logger.info(f"{model_name} daily analysis completed with {len(result.get('signals', []))} signals")
                    else:
                        self.logger.warning(f"{model_name} returned invalid analysis result")
                except asyncio.TimeoutError:
                    self.logger.warning(f"{model_name} daily analysis timed out after {config.AI_TIMEOUT * 2}s")
                except Exception as e:
                    self.logger.error(f"{model_name} daily analysis failed: {e}")
                    
            if not results:
                self.logger.warning("All AI analyses failed, using fallback")
                return self.generate_fallback_analysis(market_data)
                
            # Aggregate and enhance results
            aggregated = self.aggregate_daily_analyses(results, market_data)
            
            # Add metadata
            aggregated['aggregation_timestamp'] = datetime.utcnow().isoformat()
            aggregated['models_used'] = list(results.keys())
            aggregated['market_data_timestamp'] = datetime.utcnow().isoformat()
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Daily analysis aggregation failed: {e}")
            return self.generate_fallback_analysis(market_data)

    async def get_macro_sentiment_analysis(self, market_data: Dict, news_data: List = None, events_data: List = None) -> Optional[Dict]:
        """Get comprehensive macro and sentiment analysis from AI models."""
        try:
            # Load macro sentiment prompt template
            prompt_template = self.load_macro_sentiment_prompt()
            
            # Prepare enhanced context with news and events
            enhanced_context = {
                'market_data': market_data,
                'news_headlines': news_data or [],
                'crypto_events': events_data or [],
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'market_context': {
                    'total_symbols': len(market_data) if market_data else 0,
                    'positive_movers': len([s for s, d in (market_data or {}).items() if d.get('change_24h', 0) > 0]),
                    'negative_movers': len([s for s, d in (market_data or {}).items() if d.get('change_24h', 0) < 0]),
                },
                'risk_parameters': {
                    'daily_target': config.DAILY_PROFIT_TARGET,
                    'max_daily_loss': config.MAX_DAILY_LOSS,
                    'max_position': config.MAX_POSITION_PCT,
                    'risk_tolerance': 'medium'
                }
            }
            
            # Run macro analyses in parallel
            tasks = []
            
            if self.openai_client.is_available():
                tasks.append(('openai', self.openai_client.analyze_macro_sentiment(enhanced_context, prompt_template)))
                
            if self.claude_client.is_available():
                tasks.append(('claude', self.claude_client.analyze_macro_sentiment(enhanced_context, prompt_template)))
                
            if not tasks:
                self.logger.warning("No AI models available for macro analysis")
                return None
                
            # Execute analyses
            results = {}
            for model_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT * 3)  # Longer timeout for macro
                    if result and isinstance(result, dict):
                        result['analysis_timestamp'] = datetime.utcnow().isoformat()
                        result['model_source'] = model_name
                        results[model_name] = result
                        self.logger.info(f"{model_name} macro analysis completed")
                    else:
                        self.logger.warning(f"{model_name} returned invalid macro result")
                except asyncio.TimeoutError:
                    self.logger.warning(f"{model_name} macro analysis timed out")
                except Exception as e:
                    self.logger.error(f"{model_name} macro analysis failed: {e}")
                    
            if not results:
                return None
                
            # Aggregate macro results with enhanced logic
            aggregated = self.aggregate_macro_analyses(results, enhanced_context)
            
            return aggregated
            
        except Exception as e:
            self.logger.error(f"Macro analysis aggregation failed: {e}")
            return None

    async def get_news_sentiment_analysis(self, news_data: List[Dict]) -> Optional[Dict]:
        """Get news sentiment analysis from AI models."""
        try:
            if not news_data:
                return None
                
            # Run news sentiment analysis in parallel
            tasks = []
            
            if self.openai_client.is_available():
                tasks.append(('openai', self.openai_client.evaluate_news_sentiment(news_data)))
                
            if self.claude_client.is_available():
                # Claude doesn't have news sentiment method in current impl, could add it
                pass
                
            if not tasks:
                return None
                
            # Execute analyses
            results = {}
            for model_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT)
                    if result:
                        results[model_name] = result
                        self.logger.info(f"{model_name} news sentiment analysis completed")
                except Exception as e:
                    self.logger.error(f"{model_name} news sentiment failed: {e}")
                    
            return results.get('openai')  # Return OpenAI result for now
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed: {e}")
            return None

    async def analyze_pump_event(self, pump_data: Dict) -> Optional[Dict]:
        """Analyze pump events for sustainability and trading opportunities."""
        try:
            # Run pump analysis in parallel
            tasks = []
            
            if self.openai_client.is_available():
                tasks.append(('openai', self.openai_client.analyze_pump_sustainability(pump_data)))
                
            if not tasks:
                return None
                
            # Execute analyses
            for model_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT)
                    if result:
                        self.logger.info(f"{model_name} pump analysis completed")
                        return result
                except Exception as e:
                    self.logger.error(f"{model_name} pump analysis failed: {e}")
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Pump analysis failed: {e}")
            return None

    def load_daily_prompt(self) -> str:
        """Load daily analysis prompt template."""
        try:
            with open('llm/prompt_templates/daily_prompt.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return self.get_default_daily_prompt()

    def load_single_crypto_prompt(self) -> str:
        """Load single cryptocurrency analysis prompt template."""
        try:
            with open('llm/prompt_templates/single_crypto_prompt.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning("Single crypto prompt not found, using default")
            return self.get_default_single_crypto_prompt()

    def get_default_daily_prompt(self) -> str:
        """Default daily analysis prompt."""
        return """
        Analyze the provided crypto market data and generate trading signals for the next 24 hours.
        
        Consider:
        - Technical indicators and price action
        - Volume patterns and market breadth
        - Risk/reward ratios for potential trades
        - Market sentiment and momentum
        
        Provide:
        - BUY/SELL/WAIT signals for each symbol
        - Confidence scores (0-1)
        - Clear reasoning for each recommendation
        - Overall market assessment
        """

    def get_default_single_crypto_prompt(self) -> str:
        """Default single crypto analysis prompt with professional structure."""
        return """
You are an expert cryptocurrency analyst tasked with providing detailed analysis for a single cryptocurrency.

Analyze the provided cryptocurrency data using comprehensive technical analysis framework including:
- Price action relative to 24h range
- Volume patterns and momentum sustainability  
- Support/resistance levels and breakout potential
- Short-term risk assessment and volatility analysis

## Output Format (Turkish)
Provide analysis in Turkish with the following structure:

### 1. Piyasa Yorumu (2-3 sentences)
Current price situation, dominant trend, and key technical levels.

### 2. Teknik Durum
- **Momentum Değerlendirmesi**: Current momentum and sustainability
- **Hacim Analizi**: Volume analysis and confirmation  
- **Destek/Direnç Seviyeleri**: Key support/resistance levels
- **Fiyat Pozisyonu**: Position within daily range

### 3. Kısa Vadeli Görünüm (24-48 hours)
Expected price direction, key levels to watch, potential scenarios.

### 4. Risk Değerlendirmesi  
- **Risk Seviyesi**: Düşük/Orta/Yüksek
- **Risk Faktörleri**: Specific factors to monitor
- **Pozisyon Önerisi**: Suggested approach

Use professional Turkish financial terminology. Maximum 300 words. Base analysis strictly on provided data. Emphasize risk management and capital preservation.
        """

    def load_macro_sentiment_prompt(self) -> str:
        """Load macro sentiment analysis prompt template."""
        try:
            with open('llm/prompt_templates/macro_sentiment_prompt.md', 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning("Macro sentiment prompt not found, using default")
            return self.get_default_macro_prompt()
            
    def get_default_macro_prompt(self) -> str:
        """Default macro sentiment prompt."""
        return """
        You are an expert crypto analyst. Analyze the market data and provide:
        1. Market sentiment (bullish/bearish/neutral)
        2. Key risk factors
        3. Trading signals with confidence levels
        4. Macro economic impact assessment
        
        Format your response as structured JSON with clear reasoning.
        """
        
    def aggregate_daily_analyses(self, results: Dict, market_data: Dict) -> Dict:
        """Aggregate daily analyses from multiple AI models with advanced consensus logic."""
        try:
            # Initialize aggregation structure
            aggregated_signals = {}
            market_sentiment_votes = []
            risk_assessments = []
            summaries = []
            
            # Process each model's results
            for model_name, analysis in results.items():
                summaries.append(f"[{model_name.upper()}] {analysis.get('summary', 'No summary')}")
                
                # Collect market sentiment
                sentiment = analysis.get('market_sentiment', 'Neutral')
                market_sentiment_votes.append(sentiment)
                
                # Collect risk assessment
                risk = analysis.get('risk_level', 'Medium')
                risk_assessments.append(risk)
                
                # Process signals
                signals = analysis.get('signals', [])
                for signal in signals:
                    symbol = signal.get('symbol')
                    if symbol:
                        if symbol not in aggregated_signals:
                            aggregated_signals[symbol] = {
                                'votes': [],
                                'confidences': [],
                                'reasonings': [],
                                'models': []
                            }
                        
                        aggregated_signals[symbol]['votes'].append(signal.get('action', 'WAIT'))
                        aggregated_signals[symbol]['confidences'].append(signal.get('confidence', 0))
                        aggregated_signals[symbol]['reasonings'].append(f"[{model_name}] {signal.get('reasoning', '')}")
                        aggregated_signals[symbol]['models'].append(model_name)
            
            # Build consensus signals
            final_signals = []
            for symbol, data in aggregated_signals.items():
                consensus_signal = self.build_signal_consensus(symbol, data, market_data.get(symbol, {}))
                if consensus_signal:
                    final_signals.append(consensus_signal)
            
            # Determine overall market sentiment
            sentiment_consensus = self.get_sentiment_consensus(market_sentiment_votes)
            risk_consensus = self.get_risk_consensus(risk_assessments)
            
            return {
                'signals': final_signals,
                'market_sentiment': sentiment_consensus,
                'risk_level': risk_consensus,
                'summary': f"Aggregated analysis from {len(results)} AI models. " + " | ".join(summaries),
                'model_agreement': self.calculate_model_agreement(results),
                'high_confidence_signals': [s for s in final_signals if s.get('confidence', 0) >= self.confidence_threshold],
                'analysis_quality': self.assess_analysis_quality(results)
            }
            
        except Exception as e:
            self.logger.error(f"Error aggregating daily analyses: {e}")
            return {'signals': [], 'summary': 'Aggregation failed'}

    def aggregate_macro_analyses(self, results: Dict, context: Dict) -> Dict:
        """Aggregate macro sentiment analyses with enhanced logic."""
        try:
            # Extract and combine macro insights
            combined_sentiment = {}
            combined_signals = []
            macro_factors = []
            risk_assessments = []
            
            for model_name, analysis in results.items():
                # Market sentiment
                sentiment = analysis.get('market_sentiment', {})
                if sentiment:
                    for timeframe, value in sentiment.items():
                        if timeframe not in combined_sentiment:
                            combined_sentiment[timeframe] = []
                        combined_sentiment[timeframe].append(value)
                
                # Signals
                signals = analysis.get('signals', [])
                for signal in signals:
                    signal['source_model'] = model_name
                    combined_signals.append(signal)
                
                # Macro factors
                factors = analysis.get('macro_factors', {})
                if factors:
                    macro_factors.append(factors)
                
                # Risk assessment
                risk = analysis.get('risk_assessment', {})
                if risk:
                    risk_assessments.append(risk)
            
            # Build consensus macro sentiment
            consensus_sentiment = {}
            for timeframe, values in combined_sentiment.items():
                consensus_sentiment[timeframe] = self.get_sentiment_consensus(values)
            
            # Aggregate signals with consensus
            aggregated_signals = self.aggregate_macro_signals(combined_signals)
            
            return {
                'market_sentiment': consensus_sentiment,
                'signals': aggregated_signals,
                'volatility': self.assess_market_volatility(context.get('market_data', {})),
                'macro_factors': self.combine_macro_factors(macro_factors),
                'risk_assessment': self.combine_risk_assessments(risk_assessments),
                'summary': f"Macro analysis from {len(results)} models with {len(aggregated_signals)} consensus signals",
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error aggregating macro analyses: {e}")
            return {'signals': [], 'summary': 'Macro aggregation failed'}

    def build_signal_consensus(self, symbol: str, signal_data: Dict, market_info: Dict) -> Optional[Dict]:
        """Build consensus signal from multiple AI model votes."""
        try:
            votes = signal_data['votes']
            confidences = signal_data['confidences']
            reasonings = signal_data['reasonings']
            models = signal_data['models']
            
            if not votes:
                return None
            
            # Count votes
            vote_counts = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
            for vote in votes:
                vote_counts[vote] = vote_counts.get(vote, 0) + 1
            
            # Determine consensus action
            max_votes = max(vote_counts.values())
            consensus_actions = [action for action, count in vote_counts.items() if count == max_votes]
            
            # If tie, prefer WAIT for safety
            if len(consensus_actions) > 1:
                final_action = 'WAIT'
                consensus_strength = 0.3  # Low confidence for ties
            else:
                final_action = consensus_actions[0]
                consensus_strength = max_votes / len(votes)
            
            # Calculate weighted confidence
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                # Adjust by consensus strength
                final_confidence = avg_confidence * consensus_strength
            else:
                final_confidence = consensus_strength
            
            # Enhanced reasoning
            model_summary = f"Models: {', '.join(set(models))}"
            vote_summary = f"Votes: {vote_counts}"
            reasoning_combined = " | ".join(reasonings[:2])  # Top 2 reasonings
            
            # Calculate entry/exit levels if market info available
            current_price = market_info.get('price', 0)
            if current_price > 0:
                if final_action == 'BUY':
                    stop_loss = current_price * (1 - config.STOP_LOSS_PCT)
                    take_profit = current_price * (1 + config.TAKE_PROFIT_PCT)
                elif final_action == 'SELL':
                    stop_loss = current_price * (1 + config.STOP_LOSS_PCT)
                    take_profit = current_price * (1 - config.TAKE_PROFIT_PCT)
                else:
                    stop_loss = current_price
                    take_profit = current_price
            else:
                stop_loss = 0
                take_profit = 0
            
            return {
                'symbol': symbol,
                'action': final_action,
                'confidence': round(final_confidence, 3),
                'reasoning': f"{model_summary} | {vote_summary} | {reasoning_combined}",
                'consensus_strength': round(consensus_strength, 3),
                'model_agreement': len(set(votes)) == 1,  # All models agree
                'entry_price': current_price,
                'stop_loss': round(stop_loss, 2),
                'take_profit': round(take_profit, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error building consensus for {symbol}: {e}")
            return None

    def get_sentiment_consensus(self, sentiments: List[str]) -> str:
        """Determine consensus sentiment from a list of sentiments."""
        if not sentiments:
            return 'Neutral'
            
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
        # Determine consensus
        consensus_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        # Calculate confidence
        total_count = sum(sentiment_counts.values())
        if total_count > 0:
            high_conf_count = sentiment_counts.get('Bullish', 0) + sentiment_counts.get('Bearish', 0)
            if high_conf_count >= total_count * 0.6:
                consensus_confidence = 'High'
            elif high_conf_count >= total_count * 0.3:
                consensus_confidence = 'Medium'
            else:
                consensus_confidence = 'Low'
        else:
            consensus_confidence = 'Low'
            
        return {
            'sentiment': consensus_sentiment,
            'confidence': consensus_confidence,
            'model_agreement': f"{sentiment_counts.get('Bullish', 0)}/{total_count}"
        }

    def get_risk_consensus(self, risk_levels: List[str]) -> str:
        """Determine consensus risk level from a list of risk levels."""
        if not risk_levels:
            return 'Medium'
            
        risk_counts = {}
        for risk in risk_levels:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            
        # Determine consensus
        consensus_risk = max(risk_counts, key=risk_counts.get)
        
        # Calculate confidence
        total_count = sum(risk_counts.values())
        if total_count > 0:
            high_conf_count = risk_counts.get('High', 0)
            if high_conf_count >= total_count * 0.6:
                consensus_confidence = 'High'
            elif high_conf_count >= total_count * 0.3:
                consensus_confidence = 'Medium'
            else:
                consensus_confidence = 'Low'
        else:
            consensus_confidence = 'Low'
            
        return {
            'risk_level': consensus_risk,
            'confidence': consensus_confidence,
            'model_agreement': f"{risk_counts.get('High', 0)}/{total_count}"
        }

    def calculate_model_agreement(self, results: Dict) -> Dict:
        """Calculate model agreement metrics."""
        if not results:
            return {'total_models': 0, 'agreement_ratio': 0, 'action_agreement': 0}
            
        total_models = len(results)
        if total_models == 0:
            return {'total_models': 0, 'agreement_ratio': 0, 'action_agreement': 0}
            
        # Collect all actions from all models
        all_actions = []
        for model_name, analysis in results.items():
            signals = analysis.get('signals', [])
            for signal in signals:
                all_actions.append(signal.get('action'))
                
        # Count unique actions
        unique_actions = list(set(all_actions))
        
        # Calculate agreement ratio
        if total_models > 0:
            agreement_ratio = len(unique_actions) / total_models
        else:
            agreement_ratio = 0
            
        # Calculate action agreement
        if total_models > 0:
            action_agreement = len(unique_actions) / total_models
        else:
            action_agreement = 0
            
        return {
            'total_models': total_models,
            'agreement_ratio': agreement_ratio,
            'action_agreement': action_agreement
        }

    def assess_analysis_quality(self, results: Dict) -> Dict:
        """Assess the quality of the aggregated analysis."""
        if not results:
            return {'overall_quality': 'Low', 'reason': 'No models provided'}
            
        total_models = len(results)
        if total_models == 0:
            return {'overall_quality': 'Low', 'reason': 'No models provided'}
            
        # Check for any model returning a valid analysis
        for model_name, analysis in results.items():
            if analysis and isinstance(analysis, dict) and analysis.get('signals'):
                return {'overall_quality': 'High', 'reason': 'At least one model provided a valid analysis'}
                
        return {'overall_quality': 'Low', 'reason': 'No valid analysis found from any model'}

    def aggregate_macro_signals(self, signals: List[Dict]) -> List[Dict]:
        """Aggregate macro signals with consensus."""
        aggregated_signals = []
        symbol_groups = {}
        
        for signal in signals:
            symbol = signal.get('symbol')
            if symbol:
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(signal)
        
        for symbol, signals_list in symbol_groups.items():
            aggregated_signal = self.aggregate_symbol_signals(symbol, signals_list)
            if aggregated_signal:
                aggregated_signals.append(aggregated_signal)
        
        return aggregated_signals

    def assess_market_volatility(self, market_data: Dict) -> str:
        """Assess overall market volatility based on price changes."""
        if not market_data:
            return 'Unknown'
            
        price_changes = [abs(data.get('change_24h', 0)) for data in market_data.values()]
        if not price_changes:
            return 'Low'
            
        avg_volatility = sum(price_changes) / len(price_changes)
        
        if avg_volatility > 0.1:  # 10%
            return 'High'
        elif avg_volatility > 0.05:  # 5%
            return 'Moderate'
        else:
            return 'Low'

    def combine_macro_factors(self, macro_factors: List[Dict]) -> Dict:
        """Combine macro factors from multiple models."""
        all_risks = []
        all_opportunities = []
        all_events = []
        
        for factor in macro_factors:
            all_risks.append(factor.get('primary_risk', ''))
            all_opportunities.extend(factor.get('opportunities', []))
            all_events.extend(factor.get('global_events', []))
        
        # Remove duplicates and empty values
        unique_risks = list(set(filter(None, all_risks)))
        unique_opportunities = list(set(filter(None, all_opportunities)))
        unique_events = list(set(filter(None, all_events)))
        
        return {
            'primary_risk': unique_risks[0] if unique_risks else 'No major risks identified',
            'opportunities': unique_opportunities[:5],
            'global_events': unique_events[:5]
        }

    def combine_risk_assessments(self, risk_assessments: List[Dict]) -> Dict:
        """Combine risk assessments from multiple models."""
        if not risk_assessments:
            return {'market_risk': 'Medium', 'liquidity_risk': 'Low', 'regulatory_risk': 'Medium'}
            
        market_risks = []
        liquidity_risks = []
        regulatory_risks = []
        
        for risk in risk_assessments:
            market_risks.append(risk.get('market_risk', 'Medium'))
            liquidity_risks.append(risk.get('liquidity_risk', 'Low'))
            regulatory_risks.append(risk.get('regulatory_risk', 'Medium'))
        
        # Get most common risk level for each category
        def get_consensus_risk(risks):
            risk_counts = {}
            for risk in risks:
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            return max(risk_counts, key=risk_counts.get) if risk_counts else 'Medium'
        
        return {
            'market_risk': get_consensus_risk(market_risks),
            'liquidity_risk': get_consensus_risk(liquidity_risks),
            'regulatory_risk': get_consensus_risk(regulatory_risks)
        }

    def generate_fallback_analysis(self, market_data: Dict) -> Dict:
        """Generate fallback analysis when AI models are unavailable."""
        try:
            signals = []
            
            for symbol, data in market_data.items():
                price_change = data.get('change_24h', 0)
                
                # Simple rule-based signal generation
                if price_change > 0.03:  # 3% up
                    action = 'BUY'
                    confidence = min(0.6, 0.4 + abs(price_change))
                    reasoning = f"Fallback: Positive momentum {price_change*100:.1f}%"
                elif price_change < -0.03:  # 3% down
                    action = 'SELL'
                    confidence = min(0.6, 0.4 + abs(price_change))
                    reasoning = f"Fallback: Negative momentum {price_change*100:.1f}%"
                else:
                    action = 'WAIT'
                    confidence = 0.3
                    reasoning = "Fallback: No clear direction"
                
                signals.append({
                    'symbol': symbol,
                    'action': action,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'entry_price': data.get('price', 0),
                    'stop_loss': 0,
                    'take_profit': 0
                })
            
            return {
                'signals': signals,
                'market_sentiment': 'Neutral',
                'risk_level': 'Medium',
                'summary': 'Fallback analysis generated (AI models unavailable)',
                'models_used': ['fallback'],
                'analysis_quality': {'overall_quality': 'Low', 'reason': 'Fallback mode'}
            }
            
        except Exception as e:
            self.logger.error(f"Error generating fallback analysis: {e}")
            return {'signals': [], 'summary': 'Fallback analysis failed'}

    def aggregate_symbol_signals(self, symbol: str, signals: List[Dict]) -> Optional[Dict]:
        """Aggregate signals for a single symbol from multiple models."""
        if not signals:
            return None
            
        # Collect actions and confidences
        actions = [s.get('action') for s in signals if s.get('action')]
        confidences = [s.get('confidence', 0) for s in signals if s.get('confidence')]
        reasonings = [s.get('reasoning', '') for s in signals if s.get('reasoning')]
        
        if not actions:
            return None
            
        # Weight votes by confidence
        action_scores = {'BUY': 0, 'SELL': 0, 'WAIT': 0}
        
        for i, action in enumerate(actions):
            confidence = confidences[i] if i < len(confidences) else 0.5
            action_scores[action] += confidence
            
        # Determine consensus action
        consensus_action = max(action_scores, key=action_scores.get)
        
        # Calculate consensus confidence
        total_confidence = sum(confidences) if confidences else 0
        model_count = len(signals)
        consensus_confidence = total_confidence / model_count if model_count > 0 else 0
        
        # Adjust confidence based on agreement
        agreement_bonus = 0
        if model_count > 1:
            same_action_count = sum(1 for a in actions if a == consensus_action)
            agreement_ratio = same_action_count / model_count
            agreement_bonus = agreement_ratio * 0.2  # Up to 20% bonus for full agreement
            
        final_confidence = min(consensus_confidence + agreement_bonus, 1.0)
        
        # Combine reasoning
        combined_reasoning = f"Consensus from {model_count} models: {'; '.join(reasonings[:2])}"
        if len(reasonings) > 2:
            combined_reasoning += f" and {len(reasonings) - 2} other analysis"
            
        return {
            'symbol': symbol,
            'action': consensus_action,
            'confidence': final_confidence,
            'reasoning': combined_reasoning,
            'model_agreement': {
                'participating_models': model_count,
                'agreement_ratio': same_action_count / model_count if model_count > 0 else 0,
                'action_scores': action_scores
            },
            'individual_signals': signals
        }
        
    def generate_consensus_insights(self, results: Dict) -> Dict:
        """Generate consensus market insights from all models."""
        insights = {
            'market_sentiment': 'neutral',
            'risk_assessment': 'medium',
            'key_themes': [],
            'confidence': 0.5
        }
        
        # Collect sentiment assessments
        sentiments = []
        risk_assessments = []
        
        for model_name, analysis in results.items():
            # Extract sentiment
            if 'market_sentiment' in analysis:
                sentiment_data = analysis['market_sentiment']
                sentiment = sentiment_data.get('sentiment', 'neutral')
                sentiments.append(sentiment)
                
            elif 'market_context' in analysis:
                context_data = analysis['market_context']
                # Infer sentiment from context
                if 'bullish' in str(context_data).lower():
                    sentiments.append('bullish')
                elif 'bearish' in str(context_data).lower():
                    sentiments.append('bearish')
                else:
                    sentiments.append('neutral')
                    
            # Extract risk assessment
            if 'risk_assessment' in analysis:
                risk_data = analysis['risk_assessment']
                risk_level = risk_data.get('risk_level', 'medium')
                risk_assessments.append(risk_level)
                
        # Determine consensus sentiment
        if sentiments:
            sentiment_counts = {}
            for sentiment in sentiments:
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            insights['market_sentiment'] = max(sentiment_counts, key=sentiment_counts.get)
            
        # Determine consensus risk
        if risk_assessments:
            risk_counts = {}
            for risk in risk_assessments:
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            insights['risk_assessment'] = max(risk_counts, key=risk_counts.get)
            
        # Calculate consensus confidence
        model_count = len(results)
        if model_count > 1:
            insights['confidence'] = min(0.5 + (model_count * 0.1), 0.9)
        else:
            insights['confidence'] = 0.6
            
        insights['key_themes'] = ['technical_analysis', 'market_structure', 'risk_management']
        
        return insights
        
    async def evaluate_anomalies(self, anomalies: List[Dict]) -> Dict:
        """Get AI evaluation of detected anomalies."""
        try:
            tasks = []
            
            if self.claude_client.is_available():
                tasks.append(('claude', self.claude_client.analyze_anomalies(anomalies)))
                
            if not tasks:
                return {}
                
            results = {}
            for model_name, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT)
                    if result:
                        results[model_name] = result
                except Exception as e:
                    self.logger.error(f"{model_name} anomaly evaluation failed: {e}")
                    
            # Return the first available result for now
            # In production, you might want to aggregate these too
            for result in results.values():
                return result
                
            return {}
            
        except Exception as e:
            self.logger.error(f"Anomaly evaluation failed: {e}")
            return {}
            
    async def evaluate_pumps(self, pumps: List[Dict]) -> Dict:
        """Get AI evaluation of detected pumps."""
        try:
            evaluations = {}
            
            tasks = []
            if self.openai_client.is_available():
                for pump in pumps:
                    tasks.append((pump['symbol'], self.openai_client.analyze_pump_sustainability(pump)))
                    
            if not tasks:
                return {}
                
            for symbol, task in tasks:
                try:
                    result = await asyncio.wait_for(task, timeout=config.AI_TIMEOUT)
                    if result:
                        evaluations[symbol] = result
                except Exception as e:
                    self.logger.error(f"Pump evaluation for {symbol} failed: {e}")
                    
            return evaluations
            
        except Exception as e:
            self.logger.error(f"Pump evaluation failed: {e}")
            return {}
            
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all AI services."""
        results = {}
        
        try:
            openai_test = await self.openai_client.test_connection()
            results['openai'] = openai_test
        except Exception:
            results['openai'] = False
            
        try:
            claude_test = await self.claude_client.test_connection()
            results['claude'] = claude_test
        except Exception:
            results['claude'] = False
            
        return results 

    async def get_single_crypto_analysis(self, symbol: str, coin_data: Dict) -> Optional[str]:
        """Get AI analysis for a single cryptocurrency using professional template."""
        try:
            # Load professional prompt template
            prompt_template = self.load_single_crypto_prompt()
            
            # Prepare market data summary for the coin
            market_summary = f"""
CRYPTOCURRENCY: {symbol}
CURRENT PRICE: ${coin_data.get('price', 0):,.4f}
24H CHANGE: {coin_data.get('change_24h', 0):+.2%}
24H HIGH: ${coin_data.get('high_24h', 0):,.4f}
24H LOW: ${coin_data.get('low_24h', 0):,.4f}
24H VOLUME: ${coin_data.get('volume', 0):,.0f}
VOLUME CHANGE: {coin_data.get('volume_change_24h', 0):+.1%}
DATA SOURCE: {coin_data.get('source', 'unknown')}
TIMESTAMP: {coin_data.get('timestamp', 'N/A')}

ADDITIONAL CALCULATIONS:
- Price position in 24h range: {((coin_data.get('price', 0) - coin_data.get('low_24h', 0)) / max(coin_data.get('high_24h', 0) - coin_data.get('low_24h', 0), 0.0001)) * 100:.1f}%
- Mid-range price: ${(coin_data.get('high_24h', 0) + coin_data.get('low_24h', 0)) / 2:,.4f}
- Price vs mid-range: {((coin_data.get('price', 0) / max((coin_data.get('high_24h', 0) + coin_data.get('low_24h', 0)) / 2, 0.0001)) - 1) * 100:+.1f}%
            """
            
            # Combine template with market data
            full_prompt = f"{prompt_template}\n\n## MARKET DATA TO ANALYZE:\n{market_summary}\n\nLütfen yukarıdaki {symbol} verisini analiz et ve Türkçe yanıt ver."
            
            # Try both AI models
            analyses = []
            
            if self.openai_client.is_available():
                try:
                    openai_result = await asyncio.wait_for(
                        self.openai_client.get_completion(full_prompt), 
                        timeout=15
                    )
                    if openai_result:
                        analyses.append(("GPT-4", openai_result))
                        self.logger.info(f"GPT-4 analysis completed for {symbol}")
                except Exception as e:
                    self.logger.warning(f"GPT-4 analysis failed for {symbol}: {e}")
            
            if self.claude_client.is_available():
                try:
                    claude_result = await asyncio.wait_for(
                        self.claude_client.get_completion(full_prompt), 
                        timeout=15
                    )
                    if claude_result:
                        analyses.append(("Claude", claude_result))
                        self.logger.info(f"Claude analysis completed for {symbol}")
                except Exception as e:
                    self.logger.warning(f"Claude analysis failed for {symbol}: {e}")
            
            if not analyses:
                return self._generate_fallback_crypto_analysis(symbol, coin_data)
            
            # If we have multiple analyses, combine them
            if len(analyses) > 1:
                combined_analysis = f"""
🤖 <b>AI KONSENSÜS ANALİZİ</b>

<b>📊 {analyses[0][0]} Görüşü:</b>
{analyses[0][1][:200]}...

<b>🎯 {analyses[1][0]} Görüşü:</b>
{analyses[1][1][:200]}...

<b>🔗 Genel Değerlendirme:</b>
Her iki AI modeli de {symbol} için analiz sağladı. Detaylı görüş için yukarıdaki analizleri inceleyebilirsiniz.
                """
                return combined_analysis.strip()
            else:
                # Single analysis
                model_name, analysis = analyses[0]
                return f"""
🤖 <b>{model_name.upper()} AI ANALİZİ</b>

{analysis}

<i>AI destekli analiz - yatırım tavsiyesi değildir.</i>
                """.strip()
            
        except Exception as e:
            self.logger.error(f"Error in single crypto AI analysis: {e}")
            return self._generate_fallback_crypto_analysis(symbol, coin_data)
    
    def _generate_fallback_crypto_analysis(self, symbol: str, coin_data: Dict) -> str:
        """Generate fallback analysis when AI models are not available."""
        price = coin_data.get('price', 0)
        change_24h = coin_data.get('change_24h', 0)
        volume_change = coin_data.get('volume_change_24h', 0)
        
        # Basic analysis based on data
        if change_24h > 0.05:  # +5%
            trend = "güçlü yükseliş"
            outlook = "pozitif"
        elif change_24h > 0.02:  # +2%
            trend = "ılımlı yükseliş"  
            outlook = "iyimser"
        elif change_24h < -0.05:  # -5%
            trend = "güçlü düşüş"
            outlook = "negatif"
        elif change_24h < -0.02:  # -2%
            trend = "ılımlı düşüş"
            outlook = "temkinli"
        else:
            trend = "yatay seyrediş"
            outlook = "nötr"
        
        risk_level = "Yüksek" if abs(change_24h) > 0.1 else "Orta" if abs(change_24h) > 0.05 else "Düşük"
        
        return f"""
🤖 <b>SİSTEM ANALİZİ</b>

📊 <b>Piyasa Yorumu:</b>
{symbol} ${price:,.4f} seviyesinde {trend} gösteriyor. 24 saatlik %{change_24h:+.1%} performans ile {outlook} bir tablo çiziyor.

🔍 <b>Teknik Durum:</b>
Mevcut fiyat seviyesi ve hacim analizi göz önünde bulundurulduğunda, kısa vadeli momentum {'pozitif' if change_24h > 0 else 'negatif' if change_24h < 0 else 'nötr'} görünüyor.

⏰ <b>Kısa Vadeli Görünüm:</b>
24-48 saat içinde {outlook} seyir bekleniyor. Hacim değişimi %{volume_change:+.1f} seviyesinde.

⚠️ <b>Risk Seviyesi:</b> {risk_level}

<i>Sistem analizi - yatırım tavsiyesi değildir.</i>
        """.strip() 