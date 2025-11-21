#!/usr/bin/env python3
"""
Comprehensive Analysis of GenAI Reflections
Generates visualizations and statistical insights
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory for charts
output_dir = Path('output/analysis')
output_dir.mkdir(exist_ok=True, parents=True)

print("📊 Loading data...")
# Load all datasets
keywords_df = pd.read_csv('output/results/step1_keywords.csv')
sentiment_df = pd.read_csv('output/results/step2_sentiment.csv')
memos_df = pd.read_csv('output/results/step3_memos.csv')
themes_df = pd.read_csv('output/results/step4_clustering/themes.csv')
theme_freq_df = pd.read_csv('output/results/step4_clustering/theme_frequency.csv')
theme_assign_df = pd.read_csv('output/results/step4_clustering/theme_assignments.csv')

print(f"✓ Loaded {len(keywords_df)} reflections")

# ============================================================================
# 1. SENTIMENT ANALYSIS
# ============================================================================
print("\n📈 Generating sentiment visualizations...")

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Sentiment distribution pie chart
sentiment_counts = sentiment_df['sentiment'].value_counts()
colors = ['#90EE90', '#FFB6C1', '#87CEEB']
axes[0].pie(sentiment_counts.values, labels=sentiment_counts.index, autopct='%1.1f%%',
            colors=colors, startangle=90, textprops={'fontsize': 12})
axes[0].set_title('Overall Sentiment Distribution', fontsize=16, fontweight='bold', pad=20)

# Confidence by sentiment
confidence_map = {'high': 3, 'medium': 2, 'low': 1}
sentiment_df['confidence_num'] = sentiment_df['confidence'].map(confidence_map)
conf_by_sent = sentiment_df.groupby('sentiment')['confidence_num'].mean()
axes[1].bar(conf_by_sent.index, conf_by_sent.values, color=colors)
axes[1].set_title('Average Confidence by Sentiment', fontsize=16, fontweight='bold', pad=20)
axes[1].set_ylabel('Confidence Level', fontsize=12)
axes[1].set_ylim(2.5, 3.0)
axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'sentiment_analysis.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved sentiment_analysis.png")
plt.close()

# ============================================================================
# 2. THEME ANALYSIS
# ============================================================================
print("\n🎨 Generating theme visualizations...")

fig, ax = plt.subplots(figsize=(14, 8))
theme_freq_sorted = theme_freq_df.sort_values('count', ascending=True)

# Create horizontal bar chart
bars = ax.barh(range(len(theme_freq_sorted)), theme_freq_sorted['count'])
ax.set_yticks(range(len(theme_freq_sorted)))
ax.set_yticklabels(theme_freq_sorted['theme'], fontsize=11)
ax.set_xlabel('Number of Reflections', fontsize=12, fontweight='bold')
ax.set_title('Distribution of Themes Across Student Reflections', 
             fontsize=16, fontweight='bold', pad=20)

# Color bars by frequency
norm = plt.Normalize(vmin=theme_freq_sorted['count'].min(), 
                     vmax=theme_freq_sorted['count'].max())
colors = plt.cm.viridis(norm(theme_freq_sorted['count']))
for bar, color in zip(bars, colors):
    bar.set_color(color)

# Add value labels
for i, (count, pct) in enumerate(zip(theme_freq_sorted['count'], theme_freq_sorted['percentage'])):
    ax.text(count + 0.3, i, f'{count} ({pct:.1f}%)', 
            va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'theme_distribution.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved theme_distribution.png")
plt.close()

# ============================================================================
# 3. KEYWORD ANALYSIS
# ============================================================================
print("\n🔤 Generating keyword analysis...")

# Extract all keywords
import ast
all_keywords = []
for kw_list_str in keywords_df['keywords_list']:
    try:
        kw_list = ast.literal_eval(kw_list_str)
        all_keywords.extend(kw_list)
    except:
        pass

# Count keyword frequency
keyword_freq = Counter(all_keywords)
top_keywords = keyword_freq.most_common(30)

fig, ax = plt.subplots(figsize=(14, 10))
keywords, counts = zip(*top_keywords)
y_pos = range(len(keywords))

bars = ax.barh(y_pos, counts)
ax.set_yticks(y_pos)
ax.set_yticklabels(keywords, fontsize=10)
ax.set_xlabel('Frequency', fontsize=12, fontweight='bold')
ax.set_title('Top 30 Most Frequent Keywords Across All Reflections', 
             fontsize=16, fontweight='bold', pad=20)
ax.invert_yaxis()

# Color gradient
colors = plt.cm.plasma(np.linspace(0.3, 0.9, len(bars)))
for bar, color in zip(bars, colors):
    bar.set_color(color)

# Add count labels
for i, count in enumerate(counts):
    ax.text(count + 0.3, i, str(count), va='center', fontsize=9)

plt.tight_layout()
plt.savefig(output_dir / 'top_keywords.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved top_keywords.png")
plt.close()

# ============================================================================
# 4. SENTIMENT BY THEME
# ============================================================================
print("\n🎭 Generating sentiment-theme cross-analysis...")

# Merge sentiment with themes
merged_df = pd.merge(sentiment_df[['id', 'sentiment']], 
                     theme_assign_df[['id', 'assigned_theme']], 
                     on='id')

# Create crosstab
crosstab = pd.crosstab(merged_df['assigned_theme'], merged_df['sentiment'])

fig, ax = plt.subplots(figsize=(14, 8))
crosstab_pct = crosstab.div(crosstab.sum(axis=1), axis=0) * 100

# Create stacked bar chart
crosstab_pct.plot(kind='barh', stacked=True, ax=ax, 
                  color=['#FFB6C1', '#87CEEB', '#90EE90'])
ax.set_xlabel('Percentage', fontsize=12, fontweight='bold')
ax.set_ylabel('')
ax.set_title('Sentiment Distribution by Theme', fontsize=16, fontweight='bold', pad=20)
ax.legend(title='Sentiment', bbox_to_anchor=(1.05, 1), loc='upper left')

plt.tight_layout()
plt.savefig(output_dir / 'sentiment_by_theme.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved sentiment_by_theme.png")
plt.close()

# ============================================================================
# 5. KEYWORD TRENDS
# ============================================================================
print("\n📊 Generating keyword category analysis...")

# Categorize keywords
categories = {
    'Verification': ['verification', 'source verification', 'fact-checking', 'fact checking', 
                     'source validation', 'checking', 'accuracy verification'],
    'Critical Thinking': ['critical thinking', 'critical evaluation', 'critical reasoning',
                          'critical engagement', 'critical questioning'],
    'Reliability': ['reliability', 'fabricated references', 'fabricated sources', 'fake references',
                    'false citations', 'inaccurate citations', 'citation errors'],
    'Ethical Concerns': ['ethical concerns', 'ethical use', 'ethical responsibility', 
                         'ethical AI education', 'academic integrity'],
    'Environmental Impact': ['environmental impact', 'energy consumption', 'carbon footprint',
                            'sustainability concerns', 'ecological impact']
}

category_counts = {}
for category, keywords in categories.items():
    count = sum(1 for kw in all_keywords if any(k in kw.lower() for k in keywords))
    category_counts[category] = count

fig, ax = plt.subplots(figsize=(12, 7))
cats = list(category_counts.keys())
counts = list(category_counts.values())

bars = ax.bar(cats, counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8'])
ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax.set_title('Key Concern Categories in Student Reflections', 
             fontsize=16, fontweight='bold', pad=20)
ax.tick_params(axis='x', rotation=45)

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'keyword_categories.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved keyword_categories.png")
plt.close()

# ============================================================================
# 6. STATISTICS SUMMARY
# ============================================================================
print("\n📋 Generating summary statistics...")

summary = {
    'Total Reflections': len(keywords_df),
    'Unique Keywords': len(set(all_keywords)),
    'Total Keywords': len(all_keywords),
    'Avg Keywords per Reflection': len(all_keywords) / len(keywords_df),
    'Themes Identified': len(themes_df),
    'Most Common Sentiment': sentiment_df['sentiment'].mode()[0],
    'Positive Sentiment %': (sentiment_counts.get('positive', 0) / len(sentiment_df)) * 100,
    'Negative Sentiment %': (sentiment_counts.get('negative', 0) / len(sentiment_df)) * 100,
    'Neutral Sentiment %': (sentiment_counts.get('neutral', 0) / len(sentiment_df)) * 100,
    'Top Theme': theme_freq_df.iloc[0]['theme'],
    'Top Theme Count': theme_freq_df.iloc[0]['count'],
    'Most Common Keyword': top_keywords[0][0],
    'Most Common Keyword Count': top_keywords[0][1]
}

# Create summary visualization
fig, ax = plt.subplots(figsize=(12, 10))
ax.axis('off')

# Title
title_text = "📊 Research Summary: Student Reflections on GenAI in Academic Work"
ax.text(0.5, 0.95, title_text, ha='center', va='top', 
        fontsize=16, fontweight='bold', transform=ax.transAxes)

# Key statistics
y_pos = 0.85
stats_text = f"""
Dataset Overview:
• Total Reflections Analyzed: {summary['Total Reflections']}
• Unique Keywords Extracted: {summary['Unique Keywords']}
• Average Keywords per Reflection: {summary['Avg Keywords per Reflection']:.1f}
• Themes Identified: {summary['Themes Identified']}

Sentiment Distribution:
• Positive: {summary['Positive Sentiment %']:.1f}%
• Negative: {summary['Negative Sentiment %']:.1f}%
• Neutral: {summary['Neutral Sentiment %']:.1f}%

Key Findings:
• Most Prevalent Theme: {summary['Top Theme']}
  ({summary['Top Theme Count']} reflections, {(summary['Top Theme Count']/summary['Total Reflections']*100):.1f}%)

• Most Mentioned Keyword: "{summary['Most Common Keyword']}"
  (appeared {summary['Most Common Keyword Count']} times)

• Primary Student Concerns:
  1. Source verification and citation accuracy
  2. Development of critical thinking skills
  3. Reliability of AI-generated content
  4. Ethical implications of AI use
  5. Environmental impact of AI systems
"""

ax.text(0.05, y_pos, stats_text, ha='left', va='top', 
        fontsize=12, family='monospace', transform=ax.transAxes,
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig(output_dir / 'summary_statistics.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved summary_statistics.png")
plt.close()

# ============================================================================
# 7. CORRELATION ANALYSIS
# ============================================================================
print("\n🔗 Generating correlation analysis...")

# Analyze relationship between sentiment and theme
theme_sentiment_summary = merged_df.groupby('assigned_theme')['sentiment'].agg([
    ('positive_count', lambda x: (x == 'positive').sum()),
    ('negative_count', lambda x: (x == 'negative').sum()),
    ('neutral_count', lambda x: (x == 'neutral').sum()),
    ('total', 'count')
])

theme_sentiment_summary['positive_pct'] = (theme_sentiment_summary['positive_count'] / 
                                            theme_sentiment_summary['total'] * 100)
theme_sentiment_summary['negative_pct'] = (theme_sentiment_summary['negative_count'] / 
                                            theme_sentiment_summary['total'] * 100)

fig, ax = plt.subplots(figsize=(12, 8))
x = theme_sentiment_summary['positive_pct']
y = theme_sentiment_summary['negative_pct']
sizes = theme_sentiment_summary['total'] * 50

scatter = ax.scatter(x, y, s=sizes, alpha=0.6, c=range(len(x)), cmap='viridis')

for idx, theme in enumerate(theme_sentiment_summary.index):
    ax.annotate(theme, (x.iloc[idx], y.iloc[idx]), 
                fontsize=9, ha='center', va='bottom')

ax.set_xlabel('Positive Sentiment (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Negative Sentiment (%)', fontsize=12, fontweight='bold')
ax.set_title('Theme Positioning by Sentiment Mix\n(bubble size = number of reflections)', 
             fontsize=16, fontweight='bold', pad=20)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'theme_sentiment_correlation.png', dpi=300, bbox_inches='tight')
print(f"  ✓ Saved theme_sentiment_correlation.png")
plt.close()

# ============================================================================
# GENERATE TEXT REPORT
# ============================================================================
print("\n📝 Generating text report...")

report = f"""
# COMPREHENSIVE ANALYSIS REPORT
# GenAI Student Reflections Study
# Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

================================================================================
EXECUTIVE SUMMARY
================================================================================

This analysis examines {summary['Total Reflections']} student reflections on their experience
using generative AI tools (ChatGPT, Perplexity) in academic writing assignments.

KEY INSIGHTS:
-------------
1. MIXED SENTIMENTS: Students show balanced perspectives
   - Positive: {summary['Positive Sentiment %']:.1f}%
   - Negative: {summary['Negative Sentiment %']:.1f}%
   - Neutral: {summary['Neutral Sentiment %']:.1f}%

2. PRIMARY CONCERN: Source Verification
   - {theme_freq_df.iloc[0]['count']} reflections ({theme_freq_df.iloc[0]['percentage']:.1f}%) focused on citation accuracy
   - "source verification" mentioned {keyword_freq['source verification']} times

3. LEARNING OUTCOMES: Enhanced Critical Thinking
   - {theme_freq_df.iloc[1]['count']} reflections emphasized improved analytical skills
   - Students reported deeper engagement with source material

4. RELIABILITY CONCERNS: AI-Generated Content Accuracy
   - {theme_freq_df.iloc[2]['count']} reflections raised accuracy concerns
   - Common issues: fabricated references, oversimplification, hallucinations

================================================================================
DETAILED FINDINGS
================================================================================

THEME ANALYSIS:
--------------
"""

for idx, row in theme_freq_df.iterrows():
    report += f"{idx+1}. {row['theme']}\n"
    report += f"   Count: {row['count']} reflections ({row['percentage']:.1f}%)\n\n"

report += f"""
TOP KEYWORDS (by frequency):
---------------------------
"""

for i, (keyword, count) in enumerate(top_keywords[:10], 1):
    report += f"{i:2d}. {keyword:40s} : {count:3d} mentions\n"

report += f"""

SENTIMENT ANALYSIS:
------------------
• Most reflections ({sentiment_df['confidence'].value_counts().get('high', 0)}) 
  were classified with HIGH confidence
• Balance between positive and critical perspectives suggests thoughtful engagement

RECOMMENDATIONS FOR EDUCATORS:
-----------------------------
1. Emphasize source verification skills in AI-augmented coursework
2. Teach students to critically evaluate AI-generated content
3. Integrate ethical discussions about AI use in academic contexts
4. Address environmental concerns of AI systems
5. Promote AI as a collaborative tool, not a replacement for thinking

================================================================================
"""

with open(output_dir / 'analysis_report.txt', 'w') as f:
    f.write(report)

print(f"  ✓ Saved analysis_report.txt")

print("\n" + "="*80)
print("✅ ANALYSIS COMPLETE!")
print("="*80)
print(f"\nGenerated {len(list(output_dir.glob('*.png')))} visualizations")
print(f"Output directory: {output_dir.absolute()}")
print("\nFiles created:")
for file in sorted(output_dir.glob('*')):
    print(f"  • {file.name}")

