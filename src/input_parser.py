"""
Input Parser - Flexible parsing for txt, csv, json formats
"""
import json
from typing import List, Dict, Any
from pathlib import Path
import pandas as pd


class ReflectionParser:
    """Parse reflections from various input formats"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.input_config = config['input']
        self.format = self.input_config['format']
        self.path = Path(self.input_config['path'])
    
    def parse(self) -> List[Dict[str, Any]]:
        """
        Parse reflections from configured input source
        
        Returns:
            List of dicts with 'id', 'text', and optional metadata
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Input file not found: {self.path}")
        
        if self.format == "txt":
            return self._parse_txt()
        elif self.format == "csv":
            return self._parse_csv()
        elif self.format == "json":
            return self._parse_json()
        else:
            raise ValueError(f"Unknown input format: {self.format}")
    
    def _parse_txt(self) -> List[Dict[str, Any]]:
        """Parse text file with separator"""
        separator = self.input_config.get('txt_separator', '\n\n---\n\n')
        
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split on separator
        reflections = content.split(separator)
        
        # Filter empty reflections
        reflections = [r.strip() for r in reflections if r.strip()]
        
        # Convert to dict format
        parsed = []
        for idx, text in enumerate(reflections, 1):
            parsed.append({
                'id': f"R{idx:03d}",
                'text': text,
                'source': 'txt',
                'index': idx
            })
        
        print(f"✓ {len(parsed)} reflections read from text file")
        return parsed
    
    def _parse_csv(self) -> List[Dict[str, Any]]:
        """Parse CSV file"""
        text_column = self.input_config.get('csv_column', 'reflection')
        id_column = self.input_config.get('csv_id_column')
        
        df = pd.read_csv(self.path)
        
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in CSV. "
                           f"Available columns: {list(df.columns)}")
        
        parsed = []
        for idx, row in df.iterrows():
            reflection_id = row[id_column] if id_column and id_column in df.columns else f"R{idx+1:03d}"
            
            parsed.append({
                'id': str(reflection_id),
                'text': str(row[text_column]),
                'source': 'csv',
                'index': idx + 1,
                'metadata': {k: v for k, v in row.items() if k != text_column}
            })
        
        print(f"✓ {len(parsed)} reflections read from CSV")
        return parsed
    
    def _parse_json(self) -> List[Dict[str, Any]]:
        """Parse JSON file"""
        text_field = self.input_config.get('json_text_field', 'text')
        id_field = self.input_config.get('json_id_field', 'id')
        
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both array and single object
        if isinstance(data, dict):
            data = [data]
        
        parsed = []
        for idx, item in enumerate(data, 1):
            if text_field not in item:
                raise ValueError(f"Field '{text_field}' not found in JSON item {idx}")
            
            reflection_id = item.get(id_field, f"R{idx:03d}")
            
            parsed.append({
                'id': str(reflection_id),
                'text': item[text_field],
                'source': 'json',
                'index': idx,
                'metadata': {k: v for k, v in item.items() if k not in [text_field, id_field]}
            })
        
        print(f"✓ {len(parsed)} reflections read from JSON")
        return parsed
    
    @staticmethod
    def validate_reflections(reflections: List[Dict[str, Any]]) -> bool:
        """Validate that reflections are correctly parsed"""
        if not reflections:
            raise ValueError("No reflections found")
        
        for r in reflections:
            if 'id' not in r or 'text' not in r:
                raise ValueError(f"Invalid reflection: {r}")
            if not r['text'].strip():
                raise ValueError(f"Empty reflection found: {r['id']}")
        
        print(f"✓ Validation passed: {len(reflections)} reflections")
        return True

