"""
LLM Client - Abstraction for Ollama and Azure OpenAI
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

try:
    import ollama
except ImportError:
    ollama = None

try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None


class LLMClient:
    """Unified interface for Ollama and Azure OpenAI"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config['llm']['provider']
        self.audit_log = []
        
        if self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "azure":
            self._init_azure()
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _init_ollama(self):
        """Initialize Ollama client"""
        if ollama is None:
            raise ImportError("Ollama package not installed. Run: pip install ollama")
        
        self.model = self.config['llm']['ollama']['model']
        self.base_url = self.config['llm']['ollama'].get('base_url', 'http://localhost:11434')
        self.temperature = self.config['llm']['ollama'].get('temperature', 0.7)
        
        print(f"✓ Ollama client initialized (model: {self.model})")
    
    def _init_azure(self):
        """Initialize Azure OpenAI client"""
        if AzureOpenAI is None:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        api_key = os.getenv('AZURE_OPENAI_API_KEY') or self.config['llm']['azure'].get('api_key')
        if not api_key:
            raise ValueError("Azure API key not found. Set AZURE_OPENAI_API_KEY env variable.")
        
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=self.config['llm']['azure']['api_version'],
            azure_endpoint=self.config['llm']['azure']['endpoint']
        )
        self.deployment_name = self.config['llm']['azure']['deployment_name']
        self.temperature = self.config['llm']['azure'].get('temperature', 0.7)
        
        print(f"✓ Azure OpenAI client initialized (deployment: {self.deployment_name})")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Max tokens to generate
            context: Previous messages for stateful conversation
            
        Returns:
            Dict with 'response', 'prompt', 'timestamp', 'model'
        """
        temp = temperature if temperature is not None else self.temperature
        
        # Log request
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider,
            'prompt': prompt,
            'system_prompt': system_prompt,
            'temperature': temp,
            'max_tokens': max_tokens
        }
        
        try:
            if self.provider == "ollama":
                response = self._generate_ollama(prompt, system_prompt, temp, max_tokens, context)
            else:
                response = self._generate_azure(prompt, system_prompt, temp, max_tokens, context)
            
            log_entry['response'] = response['response']
            log_entry['model'] = response['model']
            log_entry['success'] = True
            
        except Exception as e:
            log_entry['error'] = str(e)
            log_entry['success'] = False
            raise
        
        finally:
            self.audit_log.append(log_entry)
        
        return response
    
    def _generate_ollama(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        context: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Generate using Ollama"""
        messages = []
        
        # Add context if provided (for stateful conversation)
        if context:
            messages.extend(context)
        
        # Add system prompt
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        # Add user prompt
        messages.append({'role': 'user', 'content': prompt})
        
        # Generate
        options = {
            'temperature': temperature
        }
        # Only include num_predict if max_tokens is explicitly set
        # Some models don't accept -1 (unlimited), so omit it if None
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        
        response = ollama.chat(
            model=self.model,
            messages=messages,
            options=options
        )
        
        return {
            'response': response['message']['content'],
            'model': self.model,
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'system_prompt': system_prompt
        }
    
    def _generate_azure(
        self, 
        prompt: str, 
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
        context: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Generate using Azure OpenAI"""
        messages = []
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        # Add system prompt
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        
        # Add user prompt
        messages.append({'role': 'user', 'content': prompt})
        
        # Generate
        create_params = {
            'model': self.deployment_name,
            'messages': messages,
            'temperature': temperature
        }
        # Only include max_tokens if explicitly set
        if max_tokens is not None:
            create_params['max_tokens'] = max_tokens
        
        response = self.client.chat.completions.create(**create_params)
        
        return {
            'response': response.choices[0].message.content,
            'model': self.deployment_name,
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'system_prompt': system_prompt
        }
    
    def save_audit_log(self, filepath: str):
        """Save audit log to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.audit_log, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Audit log saved: {filepath}")
    
    def get_model_info(self) -> Dict[str, str]:
        """Get current model information"""
        if self.provider == "ollama":
            return {
                'provider': 'Ollama',
                'model': self.model,
                'base_url': self.base_url,
                'temperature': str(self.temperature)
            }
        else:
            return {
                'provider': 'Azure OpenAI',
                'deployment': self.deployment_name,
                'temperature': str(self.temperature)
            }

