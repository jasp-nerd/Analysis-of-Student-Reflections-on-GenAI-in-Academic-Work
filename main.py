#!/usr/bin/env python3
"""
Qualitative Analysis Pipeline - Main Application
Interactive CLI for analyzing student reflections
"""
import sys
import yaml
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from dotenv import load_dotenv

from src.llm_client import LLMClient
from src.input_parser import ReflectionParser
from src.step1_keywords import KeywordExtractor
from src.step2_sentiment import SentimentAnalyzer
from src.step3_memos import MemoGenerator
from src.step4_clustering import ThematicClusterer
from src.step5_audit import AuditTrail


# Load environment variables
load_dotenv()

console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def display_welcome():
    """Display welcome message"""
    console.print(Panel.fit(
        "[bold cyan]Qualitative Analysis Pipeline[/bold cyan]\n"
        "Analysis of GenAI Reflections with Local LLM",
        border_style="cyan"
    ))


def display_config_info(config: dict):
    """Display current configuration"""
    table = Table(title="Configuration", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("LLM Provider", config['llm']['provider'])
    
    if config['llm']['provider'] == 'ollama':
        table.add_row("Model", config['llm']['ollama']['model'])
    else:
        table.add_row("Deployment", config['llm']['azure']['deployment_name'])
    
    table.add_row("Input Format", config['input']['format'])
    table.add_row("Input Path", config['input']['path'])
    table.add_row("Target Themes", str(config['analysis']['target_themes']))
    
    console.print(table)


@click.group()
def cli():
    """Qualitative Analysis Pipeline for GenAI Reflections"""
    pass


@cli.command()
@click.option('--config', default='config.yaml', help='Path to config file')
@click.option('--skip-memory-test', is_flag=True, help='Skip memory test')
def analyze(config: str, skip_memory_test: bool):
    """Run complete analysis pipeline (all 5 steps)"""
    display_welcome()
    
    # Load config
    cfg = load_config(config)
    display_config_info(cfg)
    
    console.print("\n[bold]Starting complete analysis...[/bold]\n")
    
    # Confirm before proceeding
    if not Confirm.ask("Proceed with analysis?"):
        console.print("❌ Analysis cancelled")
        return
    
    try:
        # Initialize components
        console.print("\n[cyan]Initializing...[/cyan]")
        llm_client = LLMClient(cfg)
        parser = ReflectionParser(cfg)
        
        # Setup output directories
        output_base = Path(cfg['output']['base_path'])
        results_dir = output_base / cfg['output']['results_dir']
        audit_dir = output_base / cfg['output']['audit_dir']
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize audit trail
        audit = AuditTrail(cfg, str(audit_dir))
        
        # Parse input
        console.print("\n[cyan]Loading reflections...[/cyan]")
        reflections = parser.parse()
        parser.validate_reflections(reflections)
        
        console.print(f"✓ {len(reflections)} reflections loaded\n")
        
        # Step 1: Keyword Extraction
        audit.log_step_start("Keyword Extraction", 1, 
                            "Extracting keywords from reflections")
        console.print("[bold cyan]Step 1: Keyword Extraction[/bold cyan]")
        
        keyword_extractor = KeywordExtractor(llm_client, cfg)
        keywords_df = keyword_extractor.extract_keywords(reflections)
        
        keywords_path = results_dir / "step1_keywords.csv"
        keyword_extractor.save_results(keywords_df, str(keywords_path))
        
        # Save keyword frequency
        freq_df = keyword_extractor.get_keyword_frequency(keywords_df)
        freq_df.to_csv(results_dir / "step1_keyword_frequency.csv", 
                      index=False, encoding='utf-8')
        
        audit.log_step_complete(1, str(keywords_path), len(keywords_df))
        
        # Step 2: Sentiment Analysis
        audit.log_step_start("Sentiment Analysis", 2,
                            "Analyzing sentiment of reflections")
        console.print("\n[bold cyan]Step 2: Sentiment Analysis[/bold cyan]")
        
        sentiment_analyzer = SentimentAnalyzer(llm_client, cfg)
        sentiment_df = sentiment_analyzer.analyze_sentiment(reflections)
        
        sentiment_path = results_dir / "step2_sentiment.csv"
        sentiment_analyzer.save_results(sentiment_df, str(sentiment_path))
        
        # Save distribution
        dist_df = sentiment_analyzer.get_sentiment_distribution(sentiment_df)
        dist_df.to_csv(results_dir / "step2_sentiment_distribution.csv",
                      index=False, encoding='utf-8')
        
        audit.log_step_complete(2, str(sentiment_path), len(sentiment_df))
        
        # Step 3: Analytic Memos
        audit.log_step_start("Analytic Memos", 3,
                            "Generating analytic memos")
        console.print("\n[bold cyan]Step 3: Analytic Memos[/bold cyan]")
        
        memo_generator = MemoGenerator(llm_client, cfg)
        memos_df = memo_generator.generate_memos(reflections)
        
        memos_path = results_dir / "step3_memos.csv"
        memo_generator.save_results(memos_df, str(memos_path))
        
        # Save learning patterns
        patterns_df = memo_generator.get_common_learning_patterns(memos_df)
        patterns_df.to_csv(results_dir / "step3_learning_patterns.csv",
                          index=False, encoding='utf-8')
        
        audit.log_step_complete(3, str(memos_path), len(memos_df))
        
        # Step 4: Thematic Clustering
        audit.log_step_start("Thematic Clustering", 4,
                            "Clustering reflections into themes")
        console.print("\n[bold cyan]Step 4: Thematic Clustering[/bold cyan]")
        
        clusterer = ThematicClusterer(llm_client, cfg)
        clustering_result = clusterer.cluster_themes(reflections, keywords_df)
        
        clustering_dir = results_dir / "step4_clustering"
        clusterer.save_results(clustering_result, str(clustering_dir))
        
        # Display themes
        console.print("\n[bold green]Identified Themes:[/bold green]")
        for i, theme in enumerate(clustering_result['themes'], 1):
            console.print(f"{i}. [cyan]{theme['name']}[/cyan]")
            console.print(f"   {theme['definition'][:100]}...")
        
        audit.log_step_complete(4, str(clustering_dir), len(reflections))
        
        # Step 5: Finalize Audit Trail
        console.print("\n[bold cyan]Step 5: Finalizing Audit Trail[/bold cyan]")
        audit.finalize(llm_client)
        
        # Memory Test (optional)
        if not skip_memory_test and cfg['memory_test'].get('enabled', True):
            console.print("\n[bold yellow]Running Memory Test...[/bold yellow]")
            
            memory_test = MemoryTest(llm_client, cfg)
            test_results = memory_test.run_comparison(
                reflections,
                sample_size=cfg['memory_test'].get('sample_size', 10)
            )
            
            memory_test_dir = results_dir / "memory_test"
            memory_test.save_results(test_results, str(memory_test_dir))
        
        # Success summary
        console.print("\n" + "="*80)
        console.print("[bold green]✅ Analysis Completed![/bold green]")
        console.print("="*80)
        console.print(f"\n📁 Results: {results_dir}/")
        console.print(f"📋 Audit logs: {audit_dir}/")
        console.print(f"📊 Number of reflections: {len(reflections)}")
        console.print(f"🎯 Themes: {len(clustering_result['themes'])}")
        console.print()
        
    except FileNotFoundError as e:
        console.print(f"\n❌ [red]Error: {e}[/red]")
        console.print("\n💡 Tip: Make sure your reflections are in the correct path:")
        console.print(f"   {cfg['input']['path']}")
        sys.exit(1)
    
    except Exception as e:
        console.print(f"\n❌ [red]Error during analysis: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option('--config', default='config.yaml', help='Path to config file')
@click.option('--sample-size', type=int, help='Number of reflections to test')
def memory_test(config: str, sample_size: Optional[int]):
    """Run memory test (stateless vs stateful comparison)"""
    display_welcome()
    
    cfg = load_config(config)
    console.print("\n[bold yellow]Memory Test Mode[/bold yellow]")
    console.print("Comparing: Stateless vs Stateful (with context)\n")
    
    try:
        # Initialize
        llm_client = LLMClient(cfg)
        parser = ReflectionParser(cfg)
        
        # Load reflections
        reflections = parser.parse()
        parser.validate_reflections(reflections)
        
        # Run test
        test = MemoryTest(llm_client, cfg)
        results = test.run_comparison(reflections, sample_size)
        
        # Save results
        output_base = Path(cfg['output']['base_path'])
        test_dir = output_base / "memory_test"
        test.save_results(results, str(test_dir))
        
        console.print(f"\n✅ Memory test completed!")
        console.print(f"📁 Results: {test_dir}/")
        
    except Exception as e:
        console.print(f"\n❌ [red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('step_number', type=int)
@click.option('--config', default='config.yaml', help='Path to config file')
def step(step_number: int, config: str):
    """Run individual analysis step (1-5)"""
    if step_number not in [1, 2, 3, 4, 5]:
        console.print("❌ Invalid step number. Choose 1-5.")
        sys.exit(1)
    
    cfg = load_config(config)
    
    try:
        llm_client = LLMClient(cfg)
        parser = ReflectionParser(cfg)
        reflections = parser.parse()
        
        output_base = Path(cfg['output']['base_path'])
        results_dir = output_base / cfg['output']['results_dir']
        results_dir.mkdir(parents=True, exist_ok=True)
        
        if step_number == 1:
            console.print("[bold cyan]Step 1: Keyword Extraction[/bold cyan]")
            extractor = KeywordExtractor(llm_client, cfg)
            df = extractor.extract_keywords(reflections)
            extractor.save_results(df, str(results_dir / "step1_keywords.csv"))
        
        elif step_number == 2:
            console.print("[bold cyan]Step 2: Sentiment Analysis[/bold cyan]")
            analyzer = SentimentAnalyzer(llm_client, cfg)
            df = analyzer.analyze_sentiment(reflections)
            analyzer.save_results(df, str(results_dir / "step2_sentiment.csv"))
        
        elif step_number == 3:
            console.print("[bold cyan]Step 3: Analytic Memos[/bold cyan]")
            generator = MemoGenerator(llm_client, cfg)
            df = generator.generate_memos(reflections)
            generator.save_results(df, str(results_dir / "step3_memos.csv"))
        
        elif step_number == 4:
            console.print("[bold cyan]Step 4: Thematic Clustering[/bold cyan]")
            # Check if keywords exist
            keywords_path = results_dir / "step1_keywords.csv"
            if keywords_path.exists():
                import pandas as pd
                keywords_df = pd.read_csv(keywords_path)
            else:
                keywords_df = None
            
            clusterer = ThematicClusterer(llm_client, cfg)
            result = clusterer.cluster_themes(reflections, keywords_df)
            clusterer.save_results(result, str(results_dir / "step4_clustering"))
        
        elif step_number == 5:
            console.print("[bold cyan]Step 5: Generate Audit Trail[/bold cyan]")
            audit_dir = output_base / cfg['output']['audit_dir']
            audit = AuditTrail(cfg, str(audit_dir))
            audit.finalize(llm_client)
        
        console.print(f"\n✅ Step {step_number} completed!")
        
    except Exception as e:
        console.print(f"\n❌ [red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def info():
    """Display configuration and system information"""
    display_welcome()
    
    try:
        cfg = load_config()
        display_config_info(cfg)
        
        console.print("\n[bold]Available Commands:[/bold]")
        console.print("  analyze         - Run complete analysis (all 5 steps)")
        console.print("  memory-test     - Run memory test comparison")
        console.print("  step <1-5>      - Run individual step")
        console.print("  info            - Show this information")
        
        console.print("\n[bold]Examples:[/bold]")
        console.print("  python main.py analyze")
        console.print("  python main.py memory-test")
        console.print("  python main.py step 1")
        
    except FileNotFoundError:
        console.print("❌ config.yaml not found")
        sys.exit(1)


if __name__ == "__main__":
    cli()

