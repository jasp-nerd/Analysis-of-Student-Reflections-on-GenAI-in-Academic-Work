"""
Step 5: Audit Trail & Transparency
Goal: Full transparency about AI processes used
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path


class AuditTrail:
    """Comprehensive audit trail for all LLM operations"""
    
    def __init__(self, config: Dict[str, Any], output_dir: str):
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.audit_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'config': config,
            'steps': [],
            'errors': [],
            'corrections': []
        }
    
    def log_step_start(self, step_name: str, step_number: int, description: str):
        """Log start of analysis step"""
        step_entry = {
            'step_number': step_number,
            'step_name': step_name,
            'description': description,
            'start_time': datetime.now().isoformat(),
            'status': 'started'
        }
        self.audit_data['steps'].append(step_entry)
        
        print(f"\n📝 Audit: Step {step_number} started - {step_name}")
    
    def log_step_complete(self, step_number: int, results_path: str, num_items: int):
        """Log completion of analysis step"""
        step = self._get_step(step_number)
        if step:
            step['end_time'] = datetime.now().isoformat()
            step['status'] = 'completed'
            step['results_path'] = results_path
            step['num_items_processed'] = num_items
            
            # Calculate duration
            start = datetime.fromisoformat(step['start_time'])
            end = datetime.fromisoformat(step['end_time'])
            step['duration_seconds'] = (end - start).total_seconds()
            
            print(f"✓ Audit: Step {step_number} completed ({num_items} items, {step['duration_seconds']:.1f}s)")
    
    def log_error(self, step_number: int, error_message: str, context: str = ""):
        """Log error during processing"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'step_number': step_number,
            'error': error_message,
            'context': context
        }
        self.audit_data['errors'].append(error_entry)
        
        step = self._get_step(step_number)
        if step:
            step['status'] = 'error'
            step['error'] = error_message
    
    def log_correction(self, step_number: int, correction_type: str, description: str):
        """Log manual correction or adjustment"""
        correction_entry = {
            'timestamp': datetime.now().isoformat(),
            'step_number': step_number,
            'type': correction_type,
            'description': description
        }
        self.audit_data['corrections'].append(correction_entry)
    
    def log_llm_calls(self, llm_client):
        """Log all LLM API calls from client"""
        self.audit_data['llm_calls'] = llm_client.audit_log
        self.audit_data['total_llm_calls'] = len(llm_client.audit_log)
        
        print(f"✓ Audit: {len(llm_client.audit_log)} LLM calls logged")
    
    def finalize(self, llm_client=None):
        """Finalize audit trail and save all files"""
        self.audit_data['end_time'] = datetime.now().isoformat()
        
        # Calculate total duration
        start = datetime.fromisoformat(self.audit_data['start_time'])
        end = datetime.fromisoformat(self.audit_data['end_time'])
        self.audit_data['total_duration_seconds'] = (end - start).total_seconds()
        
        # Log LLM calls if provided
        if llm_client:
            self.log_llm_calls(llm_client)
        
        # Save files
        self._save_audit_log()
        self._save_prompts_log()
        self._save_system_info()
        self._save_summary_report()
        
        print(f"\n✅ Audit trail completed: {self.output_dir}/")
        print(f"   Session ID: {self.session_id}")
        print(f"   Total duration: {self.audit_data['total_duration_seconds']:.1f}s")
    
    def _get_step(self, step_number: int) -> Dict:
        """Get step entry by number"""
        for step in self.audit_data['steps']:
            if step['step_number'] == step_number:
                return step
        return None
    
    def _save_audit_log(self):
        """Save complete audit log as JSON"""
        filepath = self.output_dir / f"audit_log_{self.session_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.audit_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Audit log: {filepath}")
    
    def _save_prompts_log(self):
        """Save all prompts used"""
        if 'llm_calls' not in self.audit_data:
            return
        
        filepath = self.output_dir / f"prompts_{self.session_id}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PROMPTS LOG\n")
            f.write(f"Session: {self.session_id}\n")
            f.write("="*80 + "\n\n")
            
            for i, call in enumerate(self.audit_data['llm_calls'], 1):
                f.write(f"\n{'='*80}\n")
                f.write(f"CALL #{i}\n")
                f.write(f"Timestamp: {call['timestamp']}\n")
                f.write(f"Model: {call.get('model', 'unknown')}\n")
                f.write(f"Temperature: {call['temperature']}\n")
                f.write(f"{'='*80}\n\n")
                
                if call.get('system_prompt'):
                    f.write("SYSTEM PROMPT:\n")
                    f.write("-"*80 + "\n")
                    f.write(call['system_prompt'] + "\n\n")
                
                f.write("USER PROMPT:\n")
                f.write("-"*80 + "\n")
                f.write(call['prompt'][:1000] + "...\n\n")  # Truncate long prompts
                
                if call.get('success'):
                    f.write("RESPONSE:\n")
                    f.write("-"*80 + "\n")
                    response_text = call.get('response', '')
                    f.write(response_text[:1000] + "...\n\n")  # Truncate long responses
                else:
                    f.write(f"ERROR: {call.get('error', 'Unknown error')}\n\n")
        
        print(f"✓ Prompts log: {filepath}")
    
    def _save_system_info(self):
        """Save system and configuration information"""
        filepath = self.output_dir / f"system_info_{self.session_id}.json"
        
        system_info = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'llm_provider': self.config['llm']['provider'],
            'model_info': self._get_model_info(),
            'input_format': self.config['input']['format'],
            'analysis_settings': self.config['analysis']
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(system_info, f, indent=2, ensure_ascii=False)
        
        print(f"✓ System info: {filepath}")
    
    def _get_model_info(self) -> Dict[str, str]:
        """Extract model information from config"""
        provider = self.config['llm']['provider']
        
        if provider == 'ollama':
            return {
                'provider': 'Ollama',
                'model': self.config['llm']['ollama']['model'],
                'base_url': self.config['llm']['ollama']['base_url'],
                'temperature': str(self.config['llm']['ollama']['temperature'])
            }
        else:
            return {
                'provider': 'Azure OpenAI',
                'deployment': self.config['llm']['azure']['deployment_name'],
                'api_version': self.config['llm']['azure']['api_version'],
                'temperature': str(self.config['llm']['azure']['temperature'])
            }
    
    def _save_summary_report(self):
        """Save human-readable summary report"""
        filepath = self.output_dir / f"summary_report_{self.session_id}.txt"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("QUALITATIVE ANALYSIS - AUDIT REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Session ID: {self.session_id}\n")
            f.write(f"Start: {self.audit_data['start_time']}\n")
            f.write(f"End: {self.audit_data['end_time']}\n")
            f.write(f"Total duration: {self.audit_data.get('total_duration_seconds', 0):.1f} seconds\n\n")
            
            f.write("-"*80 + "\n")
            f.write("CONFIGURATION\n")
            f.write("-"*80 + "\n")
            model_info = self._get_model_info()
            for key, value in model_info.items():
                f.write(f"{key}: {value}\n")
            f.write(f"\nInput format: {self.config['input']['format']}\n")
            f.write(f"Input path: {self.config['input']['path']}\n\n")
            
            f.write("-"*80 + "\n")
            f.write("ANALYSIS STEPS\n")
            f.write("-"*80 + "\n\n")
            
            for step in self.audit_data['steps']:
                f.write(f"Step {step['step_number']}: {step['step_name']}\n")
                f.write(f"  Status: {step['status']}\n")
                f.write(f"  Start: {step['start_time']}\n")
                
                if 'end_time' in step:
                    f.write(f"  End: {step['end_time']}\n")
                    f.write(f"  Duration: {step.get('duration_seconds', 0):.1f}s\n")
                
                if 'num_items_processed' in step:
                    f.write(f"  Items processed: {step['num_items_processed']}\n")
                
                if 'results_path' in step:
                    f.write(f"  Results: {step['results_path']}\n")
                
                if step['status'] == 'error':
                    f.write(f"  ⚠️ ERROR: {step.get('error', 'Unknown')}\n")
                
                f.write("\n")
            
            # Log errors
            if self.audit_data['errors']:
                f.write("-"*80 + "\n")
                f.write("ERRORS\n")
                f.write("-"*80 + "\n\n")
                for error in self.audit_data['errors']:
                    f.write(f"[{error['timestamp']}] Step {error['step_number']}\n")
                    f.write(f"  {error['error']}\n")
                    if error['context']:
                        f.write(f"  Context: {error['context']}\n")
                    f.write("\n")
            
            # Log corrections
            if self.audit_data['corrections']:
                f.write("-"*80 + "\n")
                f.write("CORRECTIONS\n")
                f.write("-"*80 + "\n\n")
                for correction in self.audit_data['corrections']:
                    f.write(f"[{correction['timestamp']}] Step {correction['step_number']}\n")
                    f.write(f"  Type: {correction['type']}\n")
                    f.write(f"  {correction['description']}\n\n")
            
            # Statistics
            f.write("-"*80 + "\n")
            f.write("STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total number of LLM calls: {self.audit_data.get('total_llm_calls', 0)}\n")
            f.write(f"Successful steps: {sum(1 for s in self.audit_data['steps'] if s['status'] == 'completed')}\n")
            f.write(f"Errors: {len(self.audit_data['errors'])}\n")
            f.write(f"Corrections: {len(self.audit_data['corrections'])}\n")
            f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("End of report\n")
            f.write("="*80 + "\n")
        
        print(f"✓ Summary report: {filepath}")

