"""
Step 4: Thematic Clustering
Goal: Group reflections into 5-10 overarching themes using LLM-based analysis
"""
from typing import List, Dict, Any
import pandas as pd
from collections import Counter
import json


class ThematicClusterer:
    """Cluster reflections into themes using LLM with two-pass approach"""
    
    def __init__(self, llm_client, config: Dict[str, Any]):
        self.llm = llm_client
        self.config = config
        self.target_themes = config['analysis'].get('target_themes', 8)
    
    def cluster_themes(
        self,
        reflections: List[Dict[str, Any]],
        keywords_df: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        Cluster reflections into themes using two-pass LLM approach:
        1. First pass: LLM analyzes all reflections and creates themes
        2. Second pass: LLM assigns each reflection to one of the themes
        
        Args:
            reflections: List of reflection dicts
            keywords_df: Optional DataFrame from step 1 with keywords
            
        Returns:
            Dict with 'themes', 'assignments', 'frequency_table'
        """
        print(f"\n🔍 Clustering {len(reflections)} reflections into ~{self.target_themes} themes...")
        
        # PASS 1: Let LLM analyze all reflections and create themes
        print("\n📊 PASS 1: Analyzing all reflections to identify themes...")
        themes = self._generate_themes_from_reflections(reflections)
        print(f"✓ {len(themes)} themes identified by LLM")
        
        # PASS 2: Assign each reflection to one of the themes
        print(f"\n🎯 PASS 2: Assigning {len(reflections)} reflections to themes...")
        assignments = self._assign_reflections_to_themes(reflections, themes)
        print(f"✓ All reflections assigned to themes")
        
        # Generate frequency table
        frequency_table = self._generate_frequency_table(assignments, themes)
        
        # Create summary
        result = {
            'themes': themes,
            'assignments': assignments,
            'frequency_table': frequency_table,
            'summary': self._generate_summary(themes, frequency_table, reflections, assignments)
        }
        
        return result
    
    def _generate_themes_from_reflections(self, reflections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        PASS 1: Let LLM analyze all reflections and create themes
        """
        # Prepare all reflection texts
        all_reflections_text = "\n\n".join([
            f"Reflection {i+1}: {r['text'][:500]}"  # Limit each to 500 chars to fit in context
            for i, r in enumerate(reflections[:100])  # Use first 100 reflections for theme generation
        ])
        
        prompt = f"""You are analyzing student reflections about their experiences with generative AI.

Please read through ALL the reflections below and identify {self.target_themes} main themes or topics that emerge across these reflections.

REFLECTIONS:
{all_reflections_text}

Based on these reflections, identify {self.target_themes} themes. For each theme, provide:
1. A clear, concise theme name (2-5 words)
2. A definition explaining what the theme is about (2-3 sentences)
3. Key concepts or keywords associated with this theme (5-10 words)

Format your response EXACTLY like this (no extra text, no markdown):

THEME 1: [name]
DEFINITION: [explanation]
KEYWORDS: [keyword1, keyword2, keyword3, ...]

THEME 2: [name]
DEFINITION: [explanation]
KEYWORDS: [keyword1, keyword2, keyword3, ...]

Continue for all {self.target_themes} themes.

IMPORTANT:
- Choose themes that are actually present in the reflections above
- Make theme names descriptive and distinct from each other
- Write in English
- No markdown formatting (no ** or *)"""
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt="You are an expert qualitative researcher specializing in thematic analysis of student reflections."
        )
        
        # Parse the themes from LLM response
        themes = self._parse_themes(response['response'])
        
        # If parsing failed, create basic fallback themes
        if not themes or len(themes) < 3:
            print("⚠️  Theme generation failed, creating themes from reflection content...")
            themes = self._create_emergency_themes(reflections)
        
        return themes
    
    def _parse_themes(self, response: str) -> List[Dict[str, Any]]:
        """Parse themes from LLM response"""
        themes = []
        current_theme = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Remove markdown formatting
            line = line.replace('**', '').replace('*', '')
            
            if not line:
                # Save current theme
                if current_theme and 'name' in current_theme:
                    themes.append(current_theme)
                    current_theme = {}
                continue
            
            # Detect theme line
            if ('THEME' in line.upper() or 'THEMA' in line.upper()) and ':' in line:
                if current_theme and 'name' in current_theme:
                    themes.append(current_theme)
                
                # Extract theme name
                parts = line.split(':', 1)
                if len(parts) == 2:
                    theme_name = parts[1].strip()
                    # Remove leading numbers if present
                    theme_name = theme_name.lstrip('0123456789. ')
                    current_theme = {
                        'name': theme_name,
                        'definition': '',
                        'keywords': []
                    }
            
            elif 'DEFINITION:' in line.upper() or 'DEFINITIE:' in line.upper():
                if current_theme:
                    def_text = line.split(':', 1)[1].strip() if ':' in line else ''
                    current_theme['definition'] = def_text
            
            elif 'KEYWORDS:' in line.upper() or 'KERNWOORDEN:' in line.upper():
                if current_theme:
                    kw_text = line.split(':', 1)[1].strip() if ':' in line else ''
                    current_theme['keywords'] = [kw.strip().lower() for kw in kw_text.split(',') if kw.strip()]
            
            # Handle continuation lines for definition
            elif current_theme and 'definition' in current_theme and len(line) > 20:
                if 'THEME' not in line.upper() and 'KEYWORD' not in line.upper():
                    current_theme['definition'] += ' ' + line
        
        # Don't forget last theme
        if current_theme and 'name' in current_theme:
            themes.append(current_theme)
        
        return themes
    
    def _create_emergency_themes(self, reflections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Emergency fallback: create simple themes if LLM generation completely fails"""
        return [
            {
                'name': 'Learning and Education',
                'definition': 'Reflections about learning, understanding, and educational experiences with AI.',
                'keywords': ['learning', 'education', 'understanding', 'knowledge', 'study']
            },
            {
                'name': 'Ethics and Responsibility',
                'definition': 'Ethical considerations and responsible use of AI technology.',
                'keywords': ['ethics', 'responsibility', 'moral', 'integrity', 'trust']
            },
            {
                'name': 'Efficiency and Productivity',
                'definition': 'Impact on work efficiency, time management, and productivity.',
                'keywords': ['efficiency', 'productivity', 'time', 'faster', 'speed']
            },
            {
                'name': 'Critical Thinking',
                'definition': 'Critical evaluation, verification, and questioning of AI outputs.',
                'keywords': ['critical', 'thinking', 'verification', 'check', 'evaluate']
            },
            {
                'name': 'Creativity and Innovation',
                'definition': 'Creative applications and innovative uses of AI.',
                'keywords': ['creativity', 'creative', 'innovation', 'ideas', 'brainstorm']
            }
        ]
    
    def _assign_reflections_to_themes(
        self,
        reflections: List[Dict[str, Any]],
        themes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        PASS 2: Assign each reflection to one of the themes using LLM
        Goes through reflections one by one
        """
        assignments = []
        
        # Create theme list for prompt
        theme_list = "\n".join([
            f"{i+1}. {theme['name']}: {theme['definition']}"
            for i, theme in enumerate(themes)
        ])
        
        # Process each reflection
        for idx, reflection in enumerate(reflections):
            if (idx + 1) % 10 == 0:
                print(f"   Processing reflection {idx + 1}/{len(reflections)}...")
            
            # Ask LLM to assign this specific reflection to a theme
            prompt = f"""You have identified the following themes from student reflections about generative AI:

{theme_list}

Now, read this specific reflection and assign it to the MOST APPROPRIATE theme from the list above:

REFLECTION:
{reflection['text']}

Which theme does this reflection belong to? Respond with ONLY the theme number (1-{len(themes)}) and the theme name.

Format: [number]. [Theme Name]

For example: "1. Critical Thinking & Verification" or "3. Efficiency & Productivity"

Your answer:"""
            
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="You are an expert at categorizing student reflections into themes. Be concise and only respond with the theme number and name."
            )
            
            # Parse the response to extract theme
            assigned_theme = self._parse_theme_assignment(response['response'], themes)
            
            assignments.append({
                'id': reflection['id'],
                'text_preview': reflection['text'][:100] + "...",
                'assigned_theme': assigned_theme,
                'llm_response': response['response'].strip()
            })
        
        print(f"   ✓ Completed processing all {len(reflections)} reflections")
        return assignments
    
    def _parse_theme_assignment(self, llm_response: str, themes: List[Dict[str, Any]]) -> str:
        """Parse the LLM's theme assignment response"""
        response = llm_response.strip()
        
        # Try to extract theme number
        import re
        
        # Look for pattern like "1." or "1:" or just "1"
        number_match = re.search(r'^(\d+)[\.\:\)]?\s*', response)
        if number_match:
            theme_num = int(number_match.group(1))
            if 1 <= theme_num <= len(themes):
                return themes[theme_num - 1]['name']
        
        # Try to match theme name directly
        for theme in themes:
            if theme['name'].lower() in response.lower():
                return theme['name']
        
        # Fallback: assign to first theme
        print(f"   ⚠️  Could not parse theme assignment: '{response}', defaulting to first theme")
        return themes[0]['name'] if themes else "Unknown"
    
    def _generate_frequency_table(
        self,
        assignments: List[Dict[str, Any]],
        themes: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Generate frequency table of themes"""
        theme_counts = Counter([a['assigned_theme'] for a in assignments])
        
        freq_data = []
        for theme in themes:
            count = theme_counts.get(theme['name'], 0)
            percentage = (count / len(assignments)) * 100 if assignments else 0
            
            freq_data.append({
                'theme': theme['name'],
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        df = pd.DataFrame(freq_data)
        df = df.sort_values('count', ascending=False)
        
        return df
    
    def _generate_summary(
        self, 
        themes: List[Dict[str, Any]], 
        freq_table: pd.DataFrame,
        reflections: List[Dict[str, Any]],
        assignments: List[Dict[str, Any]]
    ) -> str:
        """Generate text summary of clustering results"""
        summary = f"Thematic Clustering Results\n"
        summary += "=" * 70 + "\n\n"
        summary += f"Total reflections analyzed: {len(reflections)}\n"
        summary += f"Number of themes identified: {len(themes)}\n"
        summary += f"Method: Two-pass LLM clustering\n\n"
        summary += "=" * 70 + "\n\n"
        
        for i, theme in enumerate(themes, 1):
            freq_row = freq_table[freq_table['theme'] == theme['name']]
            count = freq_row.iloc[0]['count'] if not freq_row.empty else 0
            percentage = freq_row.iloc[0]['percentage'] if not freq_row.empty else 0
            
            summary += f"THEME {i}: {theme['name']}\n"
            summary += f"Definition: {theme['definition']}\n"
            summary += f"Reflections assigned: {count} ({percentage}%)\n"
            summary += f"Keywords: {', '.join(theme['keywords'][:10])}\n"
            
            # Add example reflection for this theme
            theme_examples = [a for a in assignments if a['assigned_theme'] == theme['name']]
            if theme_examples:
                example = theme_examples[0]
                summary += f"Example: \"{example['text_preview']}\"\n"
            
            summary += "-" * 70 + "\n\n"
        
        return summary
    
    def save_results(self, result: Dict[str, Any], output_dir: str):
        """Save clustering results to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save themes with keywords
        themes_data = []
        for theme in result['themes']:
            themes_data.append({
                'theme_name': theme['name'],
                'definition': theme['definition'],
                'keywords': ', '.join(theme['keywords'])
            })
        themes_df = pd.DataFrame(themes_data)
        themes_df.to_csv(f"{output_dir}/themes.csv", index=False, encoding='utf-8')
        
        # Save assignments
        assignments_df = pd.DataFrame(result['assignments'])
        assignments_df.to_csv(f"{output_dir}/theme_assignments.csv", index=False, encoding='utf-8')
        
        # Save frequency table
        result['frequency_table'].to_csv(f"{output_dir}/theme_frequency.csv", index=False, encoding='utf-8')
        
        # Save summary
        with open(f"{output_dir}/clustering_summary.txt", 'w', encoding='utf-8') as f:
            f.write(result['summary'])
        
        # Save full result as JSON
        json_result = {
            'themes': result['themes'],
            'assignments': result['assignments'],
            'frequency_table': result['frequency_table'].to_dict(orient='records')
        }
        with open(f"{output_dir}/clustering_full.json", 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Clustering results saved in {output_dir}/")

