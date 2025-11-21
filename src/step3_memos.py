"""
Step 3: Analytic Memos (Micro-summaries)
Goal: Generate 2-3 short sentences per reflection about what the student learned or how their attitude changed
"""
from typing import List, Dict, Any
import pandas as pd
from rich.progress import track
from collections import Counter


class MemoGenerator:
    """Generate analytic memos from reflections using LLM"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.num_sentences = config['analysis'].get('memo_sentences', 3)
    
    def generate_memos(
        self,
        reflections: List[Dict[str, Any]],
        use_context: bool = False
    ) -> pd.DataFrame:
        """
        Generate analytic memos for all reflections
        
        Args:
            reflections: List of reflection dicts
            use_context: If True, maintain context between reflections
            
        Returns:
            DataFrame with columns: id, text, memo, key_insights, learning_points
        """
        results = []
        conversation_context = [] if use_context else None
        
        system_prompt = self._get_system_prompt()
        
        for reflection in track(reflections, description="Generating memos..."):
            try:
                memo_result = self._generate_single(
                    reflection,
                    system_prompt,
                    conversation_context
                )
                
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',
                    'memo': memo_result['memo'],
                    'key_insights': memo_result['key_insights'],
                    'learning_points': ', '.join(memo_result['learning_points'])
                })
                
            except Exception as e:
                print(f"⚠️  Error at {reflection['id']}: {e}")
                results.append({
                    'id': reflection['id'],
                    'text': reflection['text'][:200] + '...',
                    'memo': 'ERROR',
                    'key_insights': '',
                    'learning_points': ''
                })
        
        df = pd.DataFrame(results)
        print(f"\n✓ Memos generated for {len(df)} reflections")
        
        return df
    
    def _generate_single(
        self,
        reflection: Dict[str, Any],
        system_prompt: str,
        context: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate memo for single reflection"""
        prompt = self._build_prompt(reflection['text'])
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            context=context
        )
        
        # Update context if stateful
        if context is not None:
            context.append({'role': 'user', 'content': prompt})
            context.append({'role': 'assistant', 'content': response['response']})
        
        return self._parse_memo(response['response'])
    
    def _get_system_prompt(self) -> str:
        """System prompt for memo generation"""
        return f"""You are an expert in qualitative analysis of educational research. Your task is to write compact analytic memos for student reflections about generative AI.

An analytic memo consists of {self.num_sentences} short, informative sentences that describe:
1. What the student learned or discovered
2. How their attitude or understanding changed
3. What new insights or awareness emerged

Examples of good memo sentences:
- "Became aware of hallucination risk in AI outputs"
- "Now checks AI sources before using them in academic work"
- "Developed more critical stance toward AI reliability"
- "Learned importance of prompt engineering"

Write concretely and action-oriented. Avoid vague statements.

Output format:
MEMO:
[Sentence 1]
[Sentence 2]
[Sentence 3]"""
    
    def _build_prompt(self, text: str) -> str:
        """Build prompt for single reflection"""
        return f"""Write an analytic memo for this student reflection about generative AI.

REFLECTION:
{text}

Generate {self.num_sentences} short sentences that describe what the student learned or how their attitude changed:"""
    
    def _parse_memo(self, response: str) -> Dict[str, Any]:
        """Parse memo from LLM response"""
        lines = response.strip().split('\n')
        
        memo_lines = []
        learning_points = []
        in_memo = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header
            if line.startswith('MEMO:'):
                in_memo = True
                continue
            
            # Parse numbered/bulleted lines
            cleaned_line = line
            for prefix in ['1.', '2.', '3.', '4.', '1)', '2)', '3)', '4)', '-', '*', '•']:
                if line.startswith(prefix):
                    cleaned_line = line[len(prefix):].strip()
                    break
            
            if cleaned_line and len(cleaned_line) > 10:
                memo_lines.append(cleaned_line)
                
                # Extract key learning point (simplified version)
                if any(word in cleaned_line.lower() for word in 
                       ['learned', 'aware', 'discovered', 'realized', 'understood']):
                    learning_points.append(cleaned_line)
        
        # Combine into full memo
        full_memo = ' '.join(memo_lines[:self.num_sentences])
        
        return {
            'memo': full_memo,
            'key_insights': memo_lines[0] if memo_lines else '',
            'learning_points': learning_points[:3]
        }
    
    def save_results(self, df: pd.DataFrame, output_path: str):
        """Save results to CSV"""
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Results saved: {output_path}")
    
    def get_common_learning_patterns(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Identify common learning patterns across memos"""
        # Extract keywords from memos
        all_words = []
        
        for memo in df['memo']:
            if isinstance(memo, str) and memo != 'ERROR':
                # Simple word extraction (can be enhanced)
                words = memo.lower().split()
                # Filter meaningful words (length > 4)
                meaningful_words = [w.strip('.,!?;:') for w in words if len(w) > 4]
                all_words.extend(meaningful_words)
        
        # Count frequencies
        word_counts = Counter(all_words)
        
        patterns_df = pd.DataFrame([
            {'pattern': word, 'frequency': count}
            for word, count in word_counts.most_common(top_n)
        ])
        
        return patterns_df

