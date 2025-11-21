"""
Step 2: Sentiment Analysis
Goal: Detect general tone (positive, negative, neutral)
"""
from typing import List, Dict, Any
import pandas as pd
from rich.progress import track


class SentimentAnalyzer:
    """Analyze sentiment in reflections using LLM"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.categories = config['analysis'].get('sentiment_categories', 
                                                  ['positive', 'negative', 'neutral'])
    
    def analyze_sentiment(
        self, 
        reflections: List[Dict[str, Any]],
        use_context: bool = False
    ) -> pd.DataFrame:
        """
        Analyze sentiment for all reflections
        
        Args:
            reflections: List of reflection dicts
            use_context: If True, maintain context between reflections
            
        Returns:
            DataFrame with columns: id, text, sentiment, confidence, explanation
        """
        results = []
        conversation_context = [] if use_context else None
        
        system_prompt = self._get_system_prompt()
        
        for reflection in track(reflections, description="Sentiment analysis..."):
            try:
                sentiment_result = self._analyze_single(
                    reflection,
                    system_prompt,
                    conversation_context
                )
                
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',
                    'sentiment': sentiment_result['sentiment'],
                    'confidence': sentiment_result['confidence'],
                    'explanation': sentiment_result['explanation']
                })
                
            except Exception as e:
                print(f"⚠️  Error at {reflection['id']}: {e}")
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',
                    'sentiment': 'ERROR',
                    'confidence': 0,
                    'explanation': str(e)
                })
        
        df = pd.DataFrame(results)
        print(f"\n✓ Sentiment analyzed for {len(df)} reflections")
        
        # Print summary
        self._print_summary(df)
        
        return df
    
    def _analyze_single(
        self,
        reflection: Dict[str, Any],
        system_prompt: str,
        context: List[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment for single reflection"""
        prompt = self._build_prompt(reflection['text'])
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            context=context
        )
        
        # Update context if stateful
        if context is not None:
            context.append({'role': 'user', 'content': prompt})
            context.append({'role': 'assistant', 'content': response['response']})
        
        # Parse sentiment
        return self._parse_sentiment(response['response'])
    
    def _get_system_prompt(self) -> str:
        """System prompt for sentiment analysis"""
        categories_str = ', '.join(self.categories)
        
        # Build category definitions dynamically based on config
        category_definitions = []
        category_meaning = {
            'positive': 'enthusiasm, appreciation, optimism, emphasizing benefits',
            'positief': 'enthusiasme, waardering, optimisme, nadruk op voordelen',
            'negative': 'concerns, frustration, criticism, emphasizing drawbacks, fear',
            'negatief': 'zorgen, frustratie, kritiek, nadruk op nadelen, angst',
            'neutral': 'balanced, descriptive, both pros and cons, informative',
            'neutraal': 'gebalanceerd, beschrijvend, zowel voor- als nadelen, informatief'
        }
        
        for cat in self.categories:
            meaning = category_meaning.get(cat.lower(), 'balanced perspective')
            category_definitions.append(f"- {cat} = {meaning}")
        
        definitions_text = '\n'.join(category_definitions)
        
        return f"""You are an expert in sentiment analysis. Analyze the tone of student reflections about generative AI.

IMPORTANT: Use this exact format without extra text or markdown:

SENTIMENT: [choose from: {categories_str}]
CONFIDENCE: [choose from: low, medium, high]
EXPLANATION: [1 short sentence]

Category definitions:
{definitions_text}

NOTE: If there are clearly positive or negative emotions, do NOT use neutral!"""
    
    def _build_prompt(self, text: str) -> str:
        """Build prompt for single reflection"""
        return f"""Analyze the general tone/sentiment of this student reflection about generative AI:

REFLECTION:
{text}

Determine the sentiment:"""
    
    def _parse_sentiment(self, response: str) -> Dict[str, Any]:
        """Parse sentiment from LLM response"""
        lines = response.strip().split('\n')
        
        # Translation mapping for English <-> Dutch
        translation_map = {
            'positive': 'positive',
            'positief': 'positive',
            'negative': 'negative',
            'negatief': 'negative',
            'neutral': 'neutral',
            'neutraal': 'neutral'
        }
        
        # Default to first category from config
        default_sentiment = self.categories[0] if self.categories else 'neutral'
        
        result = {
            'sentiment': default_sentiment,
            'confidence': 'medium',
            'explanation': ''
        }
        
        for line in lines:
            line = line.strip()
            # Remove markdown formatting (**, *, etc)
            line = line.replace('**', '').replace('*', '')
            
            if 'SENTIMENT:' in line.upper():
                sentiment = line.split(':', 1)[1].strip().lower() if ':' in line else line.lower()
                # Translate to English first if needed
                sentiment_normalized = translation_map.get(sentiment, sentiment)
                # Validate against categories (check both original and normalized)
                for cat in self.categories:
                    if cat.lower() in sentiment or cat.lower() in sentiment_normalized:
                        result['sentiment'] = cat
                        break
                # If no match found, try direct translation
                if result['sentiment'] == default_sentiment and sentiment_normalized in translation_map.values():
                    # Find matching category
                    for cat in self.categories:
                        if translation_map.get(cat.lower(), cat.lower()) == sentiment_normalized:
                            result['sentiment'] = cat
                            break
            
            elif 'CONFIDENCE:' in line.upper():
                conf_text = line.split(':', 1)[1].strip().lower() if ':' in line else ''
                result['confidence'] = conf_text
            
            elif 'EXPLANATION:' in line.upper() or 'UITLEG:' in line.upper():
                expl_text = line.split(':', 1)[1].strip() if ':' in line else ''
                result['explanation'] = expl_text
            
            # Also handle cases without labels
            elif not result['explanation'] and len(line) > 20:
                result['explanation'] = line
        
        return result
    
    def _print_summary(self, df: pd.DataFrame):
        """Print sentiment summary statistics"""
        print("\n📊 Sentiment Summary:")
        print("-" * 40)
        
        for category in self.categories:
            count = len(df[df['sentiment'] == category])
            percentage = (count / len(df)) * 100 if len(df) > 0 else 0
            print(f"  {category.capitalize():12s}: {count:3d} ({percentage:5.1f}%)")
        
        print("-" * 40)
    
    def save_results(self, df: pd.DataFrame, output_path: str):
        """Save results to CSV"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Results saved: {output_path}")
    
    def get_sentiment_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get sentiment distribution"""
        dist = df['sentiment'].value_counts().reset_index()
        dist.columns = ['sentiment', 'count']
        dist['percentage'] = (dist['count'] / len(df)) * 100
        return dist

