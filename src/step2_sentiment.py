"""
Step 2: Sentiment Analysis
Goal: Analyze student attitudes toward AI and toward the assignment
"""
from typing import List, Dict, Any
import pandas as pd
from rich.progress import track


class SentimentAnalyzer:
    """Analyze two-dimensional sentiment in reflections using LLM"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        # Get dimensions from config, with fallback to single dimension
        self.dimensions = config['analysis'].get('sentiment_dimensions', [
            {'name': 'ai_technology', 'label': 'Attitude toward AI', 'categories': ['positive', 'negative', 'neutral']},
            {'name': 'assignment', 'label': 'Attitude toward Assignment', 'categories': ['positive', 'negative', 'neutral']}
        ])
        # Legacy support
        self.categories = config['analysis'].get('sentiment_categories', 
                                                  ['positive', 'negative', 'neutral'])
    
    def analyze_sentiment(
        self, 
        reflections: List[Dict[str, Any]],
        use_context: bool = False
    ) -> pd.DataFrame:
        """
        Analyze sentiment for all reflections across two dimensions:
        1. Attitude toward AI technology
        2. Attitude toward the assignment
        
        Args:
            reflections: List of reflection dicts
            use_context: If True, maintain context between reflections
            
        Returns:
            DataFrame with columns: id, text, ai_sentiment, ai_explanation, 
                                   assignment_sentiment, assignment_explanation
        """
        results = []
        conversation_context = [] if use_context else None
        
        system_prompt = self._get_system_prompt()
        
        for reflection in track(reflections, description="Sentiment analysis (two dimensions)..."):
            try:
                sentiment_result = self._analyze_single(
                    reflection,
                    system_prompt,
                    conversation_context
                )
                
                result_row = {
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...'
                }
                
                # Add results for each dimension
                for dim in self.dimensions:
                    dim_name = dim['name']
                    result_row[f'{dim_name}_sentiment'] = sentiment_result.get(f'{dim_name}_sentiment', 'neutral')
                    result_row[f'{dim_name}_explanation'] = sentiment_result.get(f'{dim_name}_explanation', '')
                
                results.append(result_row)
                
            except Exception as e:
                print(f"⚠️  Error at {reflection['id']}: {e}")
                error_row = {
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...'
                }
                for dim in self.dimensions:
                    error_row[f"{dim['name']}_sentiment"] = 'ERROR'
                    error_row[f"{dim['name']}_explanation"] = str(e)
                results.append(error_row)
        
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
        """System prompt for two-dimensional sentiment analysis"""
        return """You are an expert in sentiment analysis. Analyze student reflections about generative AI from TWO different perspectives.

IMPORTANT: Use this exact format without extra text or markdown:

AI_SENTIMENT: [positive/negative/neutral]
AI_EXPLANATION: [one clear sentence explaining the student's attitude toward AI technology]

ASSIGNMENT_SENTIMENT: [positive/negative/neutral]
ASSIGNMENT_EXPLANATION: [one clear sentence explaining the student's attitude toward the assignment/task]

Category definitions:

1. ATTITUDE TOWARD AI TECHNOLOGY (AI_SENTIMENT):
   - positive: sees AI as valuable, helpful, promising; emphasizes benefits and opportunities
   - negative: concerned about AI, critical, emphasizes risks, drawbacks, fears, or limitations
   - neutral: balanced view with both benefits and concerns equally weighted, or purely descriptive

2. ATTITUDE TOWARD THE ASSIGNMENT (ASSIGNMENT_SENTIMENT):
   - positive: found assignment valuable, educational, worthwhile, insightful
   - negative: frustrated with assignment, critical of the task itself, questions its value
   - neutral: descriptive about assignment without clear positive or negative evaluation

IMPORTANT: These are TWO SEPARATE dimensions. A student can be positive about AI but neutral about the assignment, or vice versa."""
    
    def _build_prompt(self, text: str) -> str:
        """Build prompt for single reflection"""
        return f"""Analyze this student reflection about generative AI and determine TWO separate attitudes:

1. The student's attitude toward AI TECHNOLOGY itself (helpful vs problematic)
2. The student's attitude toward THIS ASSIGNMENT/TASK (valuable learning experience vs not)

REFLECTION:
{text}

Provide your analysis:"""
    
    def _parse_sentiment(self, response: str) -> Dict[str, Any]:
        """Parse two-dimensional sentiment from LLM response"""
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
        
        result = {
            'ai_technology_sentiment': 'neutral',
            'ai_technology_explanation': '',
            'assignment_sentiment': 'neutral',
            'assignment_explanation': ''
        }
        
        for line in lines:
            line = line.strip()
            # Remove markdown formatting (**, *, etc)
            line = line.replace('**', '').replace('*', '')
            
            # Parse AI sentiment
            if 'AI_SENTIMENT:' in line.upper():
                sentiment = line.split(':', 1)[1].strip().lower() if ':' in line else ''
                sentiment_normalized = translation_map.get(sentiment, sentiment)
                if sentiment_normalized in ['positive', 'negative', 'neutral']:
                    result['ai_technology_sentiment'] = sentiment_normalized
            
            # Parse AI explanation
            elif 'AI_EXPLANATION:' in line.upper():
                expl_text = line.split(':', 1)[1].strip() if ':' in line else ''
                result['ai_technology_explanation'] = expl_text
            
            # Parse assignment sentiment
            elif 'ASSIGNMENT_SENTIMENT:' in line.upper():
                sentiment = line.split(':', 1)[1].strip().lower() if ':' in line else ''
                sentiment_normalized = translation_map.get(sentiment, sentiment)
                if sentiment_normalized in ['positive', 'negative', 'neutral']:
                    result['assignment_sentiment'] = sentiment_normalized
            
            # Parse assignment explanation
            elif 'ASSIGNMENT_EXPLANATION:' in line.upper():
                expl_text = line.split(':', 1)[1].strip() if ':' in line else ''
                result['assignment_explanation'] = expl_text
        
        return result
    
    def _print_summary(self, df: pd.DataFrame):
        """Print sentiment summary statistics for both dimensions"""
        print("\n📊 Sentiment Summary:")
        print("=" * 60)
        
        for dim in self.dimensions:
            dim_name = dim['name']
            dim_label = dim['label']
            sentiment_col = f'{dim_name}_sentiment'
            
            print(f"\n{dim_label}:")
            print("-" * 40)
            
            if sentiment_col in df.columns:
                for category in ['positive', 'negative', 'neutral']:
                    count = len(df[df[sentiment_col] == category])
                    percentage = (count / len(df)) * 100 if len(df) > 0 else 0
                    print(f"  {category.capitalize():12s}: {count:3d} ({percentage:5.1f}%)")
        
        print("=" * 60)
    
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

