"""
Step 1: Keyword Extraction
Goal: Automatically identify the most important concepts and keywords per reflection
"""
from typing import List, Dict, Any
import pandas as pd
import json
from rich.progress import track


class KeywordExtractor:
    """Extract keywords from reflections using LLM"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.num_keywords = config['analysis'].get('keywords_per_reflection', 5)
        
    def extract_keywords(
        self, 
        reflections: List[Dict[str, Any]], 
        use_context: bool = False
    ) -> pd.DataFrame:
        """
        Extract keywords from all reflections
        
        Args:
            reflections: List of reflection dicts
            use_context: If True, maintain context between reflections (stateful)
            
        Returns:
            DataFrame with columns: id, text, keywords, keywords_list
        """
        results = []
        conversation_context = [] if use_context else None
        
        system_prompt = self._get_system_prompt()
        
        for reflection in track(reflections, description="Keyword extraction..."):
            try:
                keywords = self._extract_single(
                    reflection, 
                    system_prompt, 
                    conversation_context
                )
                
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',  # Preview
                    'keywords': ', '.join(keywords),
                    'keywords_list': keywords,
                    'num_keywords': len(keywords)
                })
                
            except Exception as e:
                print(f"⚠️  Error at {reflection['id']}: {e}")
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',
                    'keywords': 'ERROR',
                    'keywords_list': [],
                    'num_keywords': 0
                })
        
        df = pd.DataFrame(results)
        print(f"\n✓ Keywords extracted for {len(df)} reflections")
        return df
    
    def _extract_single(
        self, 
        reflection: Dict[str, Any], 
        system_prompt: str,
        context: List[Dict] = None
    ) -> List[str]:
        """Extract keywords from a single reflection"""
        prompt = self._build_prompt(reflection['text'])
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower for more consistency
            context=context
        )
        
        # Update context if stateful
        if context is not None:
            context.append({'role': 'user', 'content': prompt})
            context.append({'role': 'assistant', 'content': response['response']})
        
        # Parse keywords from response
        keywords = self._parse_keywords(response['response'])
        return keywords
    
    def _get_system_prompt(self) -> str:
        """System prompt for keyword extraction"""
        return f"""You are an expert in qualitative analysis. Extract the {self.num_keywords} most important keywords from student reflections about GenAI.

RULES:
- Exactly {self.num_keywords} keywords (no more, no less)
- Use 1-3 words per keyword
- Focus on concrete concepts and experiences
- Prefer English terms
- Avoid generic words like "AI" or "student"

FORMAT (use exactly this format):
1. keyword one
2. keyword two
3. keyword three
4. keyword four
5. keyword five

No extra text, only the numbered list."""
    
    def _build_prompt(self, text: str) -> str:
        """Build prompt for single reflection"""
        return f"""Analyze the following student reflection and identify the {self.num_keywords} most important keywords or concepts:

REFLECTION:
{text}

Provide a numbered list of exactly {self.num_keywords} keywords:"""
    
    def _parse_keywords(self, response: str) -> List[str]:
        """Parse keywords from LLM response"""
        keywords = []
        
        # Split on newlines
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 1), -, *, etc)
            for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.',
                          '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)', '10)',
                          '-', '*', '•']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            
            if line:
                keywords.append(line)
        
        # Take first N keywords
        return keywords[:self.num_keywords]
    
    def save_results(self, df: pd.DataFrame, output_path: str):
        """Save results to CSV"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Results saved: {output_path}")
    
    def get_keyword_frequency(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get frequency of all keywords across reflections"""
        all_keywords = []
        for keywords_list in df['keywords_list']:
            if isinstance(keywords_list, list):
                all_keywords.extend(keywords_list)
        
        # Count frequencies
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        freq_df = pd.DataFrame([
            {'keyword': kw, 'frequency': count}
            for kw, count in keyword_counts.most_common()
        ])
        
        return freq_df

