# Data Directory

This directory contains input data for the qualitative analysis pipeline.

## 📁 Structure

```
data/
├── reflections/              # Student reflection data
│   ├── reflections.txt       # Plain text input (default)
│   ├── reflections.csv       # CSV format (optional)
│   ├── reflections_cleaned.csv  # Preprocessed version
│   └── example_reflections.csv  # Sample data for testing
└── README.md                 # This file
```

## 📝 Input Formats

### 1. Plain Text (`.txt`)

**Format:** Reflections separated by `---` delimiter

**Example:**
```
This is the first student reflection about using generative AI...
---
This is the second reflection discussing ChatGPT's strengths and limitations...
---
This is the third reflection...
```

**Configuration (config.yaml):**
```yaml
input:
  format: "txt"
  path: "data/reflections/reflections.txt"
  delimiter: "---"
```

### 2. CSV (`.csv`)

**Format:** CSV file with reflection text in specified column

**Example:**
```csv
id,name,reflection,date
R001,Student1,"This is my reflection...",2025-01-15
R002,Student2,"This is another reflection...",2025-01-15
```

**Configuration (config.yaml):**
```yaml
input:
  format: "csv"
  path: "data/reflections/reflections.csv"
  csv_column: "reflection"
```

### 3. JSON (`.json`)

**Format:** JSON array with reflection objects

**Example:**
```json
[
  {
    "id": "R001",
    "text": "This is my reflection...",
    "metadata": {"date": "2025-01-15"}
  },
  {
    "id": "R002",
    "text": "This is another reflection...",
    "metadata": {"date": "2025-01-15"}
  }
]
```

**Configuration (config.yaml):**
```yaml
input:
  format: "json"
  path: "data/reflections/reflections.json"
  json_text_field: "text"
```

## 🔒 Data Privacy

- **Student Data:** This repository contains anonymized student reflections
- **IDs:** All personal identifiers have been removed (e.g., `R001`, `R002`, etc.)
- **Consent:** Students provided informed consent for research use
- **Ethics:** Study approved by institutional review board

## 📊 Current Dataset

**Dataset Information:**
- **Size:** 59 student reflections
- **Source:** University psychology course
- **Context:** Assignments on GenAI use in academic writing
- **AI Tools Evaluated:** ChatGPT, Perplexity AI
- **Date Collected:** November 2025

**Content:**
Students reflected on:
- Strengths and limitations of AI tools
- Accuracy of AI-generated references
- Impact on their learning process
- Ethical concerns about AI use
- Environmental impact of AI systems

## 🧪 Using Your Own Data

### Quick Start

1. **Prepare your data** in one of the supported formats
2. **Place files** in `data/reflections/`
3. **Update `config.yaml`** with correct paths and column names
4. **Run analysis:** `python main.py analyze`

### Data Preparation Tips

- **Clean your data:** Remove extra whitespace, ensure consistent encoding (UTF-8)
- **Anonymize:** Remove personal identifiers before analysis
- **Structure:** Ensure each reflection is complete and standalone
- **Length:** Works best with reflections of 100-1000 words
- **Language:** Currently optimized for English (multi-language support coming)

## 📋 Example Workflow

```bash
# 1. Place your data file
cp ~/my_reflections.csv data/reflections/reflections.csv

# 2. Edit config.yaml
vim config.yaml  # Set format: "csv" and csv_column: "text"

# 3. Run analysis
python main.py analyze

# 4. View results
ls output/results/
ls output/analysis/
```

## 🔍 Data Quality Checks

Before running analysis, ensure:
- ✅ File exists and is readable
- ✅ Encoding is UTF-8
- ✅ No completely empty reflections
- ✅ Column names match config (for CSV/JSON)
- ✅ Delimiters are consistent (for TXT)

## 📚 Sample Data

`example_reflections.csv` contains 5 sample reflections for testing the pipeline without using the full dataset.

To test with samples:
```bash
python main.py analyze --input data/reflections/example_reflections.csv
```

## 🆘 Troubleshooting

**Issue:** `FileNotFoundError`
- **Solution:** Check path in `config.yaml` matches actual file location

**Issue:** `UnicodeDecodeError`
- **Solution:** Ensure file is UTF-8 encoded: `iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv`

**Issue:** Empty results
- **Solution:** Verify delimiter (for TXT) or column name (for CSV/JSON)

---

For questions about data formatting, see the main [README.md](../README.md) or open an issue.

