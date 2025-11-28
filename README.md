# Kasparro — Agentic Facebook Performance Analyst  
Author: **Yaswanth Sai**

This project implements a multi-agent, reasoning-driven system that autonomously analyzes Facebook Ads performance, diagnoses ROAS/CTR drop-offs, and generates new creative suggestions grounded in existing dataset messages.

The architecture follows the required Planner → Data Agent → Insight Agent → Evaluator Agent → Creative Generator flow.

## Table of Contents
- [Quick Start](#-quick-start)
- [Project Structure](#project-structure)
- [Configuration](#-configuration)
- [Agent Architecture](#-agent-architecture)
- [Example CLI Usage](#-example-cli-command)
- [Example Outputs](#-example-output-files)
- [Tests](#-tests)
- [Observability](#-observability)
- [Reproducibility](#-reproducibility)
- [Release Instructions](#-release-instructions)
- [Submission](#-submission)
- [License](#license)


---

# 🚀 Quick Start

```bash
python -V  # must be >= 3.10

# Create virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt

# Run complete analysis
python src/run.py "Analyze ROAS drop"
```

Outputs will be saved to:

```
reports/report.md  
reports/insights.json  
reports/creatives.json  
logs/log_<timestamp>.json
```

---

# 📁 Project Structure

```
kasparro-agentic-fb-analyst-yaswanth-sai/
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── data/
│   ├── sample_fb_ads.csv
│   ├── synthetic_fb_ads_undergarments.csv
│   └── README.md
├── prompts/
│   ├── planner_prompt.md
│   ├── insight_prompt.md
│   └── creative_prompt.md
├── src/
│   ├── run.py
│   ├── orchestrator.py
│   ├── utils.py
│   └── agents/
│       ├── planner.py
│       ├── data_agent.py
│       ├── insight_agent.py
│       ├── evaluator.py
│       └── creative_generator.py
├── reports/
│   ├── report.md
│   ├── insights.json
│   └── creatives.json
├── logs/
│   └── [...]
└── tests/
    └── test_evaluator.py
```

---

# ⚙️ Configuration

Edit `config/config.yaml`:

```yaml
python: "3.10"
random_seed: 42
confidence_min: 0.6

use_sample_data: false
data_csv: "data/synthetic_fb_ads_undergarments.csv"

output_dir: "reports"
logs_dir: "logs"

report_file: "reports/report.md"
insights_file: "reports/insights.json"
creatives_file: "reports/creatives.json"

sample_window_days: 30

```

---

# 🧠 Agent Architecture

## 1. Planner Agent  
Breaks user query into fixed subtasks:
- Load dataset  
- Generate hypotheses  
- Validate hypotheses  
- Generate creative suggestions  
- Compile final report  

Output: structured task list in JSON.

## 2. Data Agent  
- Loads CSV  
- Cleans numeric columns  
- Computes time-series stats  
- Summaries per campaign (CTR, ROAS, spend, impressions)

## 3. Insight Agent  
Produces hypotheses using:
- CTR trend detection (linear regression)
- ROAS vs spend correlation
- Frequency-based fatigue detection
- Creative performance patterns

## 4. Evaluator Agent  
Assigns confidence scores (0–1) using:
- Trend magnitude  
- Correlation strength  
- CTR thresholds  
- Frequency thresholds  

Hypothesis marked `valid` if confidence ≥ configured threshold.

## 5. Creative Generator  
- Extracts frequently used phrases from creative messages  
- Recombines them into new headlines/CTAs  
- Produces 5–10 creative suggestions per low-CTR campaign  

---

# 📄 Example CLI Command

```bash
python src/run.py "Analyze ROAS drop in last 7 days"
```

---

# 📊 Example Output Files

### `reports/insights.json`
```json
{
  "validated": [
    {
      "id": "ctr_drop_ComfortFit_C1",
      "hypothesis": "CTR is falling — creative fatigue or weak messaging",
      "campaign": "ComfortFit_C1",
      "confidence": 0.82,
      "valid": true
    }
  ]
}
```

### `reports/creatives.json`
```json
{
  "ComfortFit_C1": {
    "suggestions": [
      "Soft breathable comfort. Shop Now. Highlight benefit cues.",
      "Premium cotton feel. Limited Offer. Emphasize fit + comfort."
    ]
  }
}
```

### `reports/report.md`
A marketer-ready summary containing:
- Top validated insights  
- Key drivers of performance change  
- Suggested creative improvements  

---

# 🧪 Tests

A minimal evaluator test is included:

```bash
pytest -q
```

Expected:
```
1 passed
```

---

# 🔍 Observability

Each run creates a structured log:

```
logs/log_20250101T123456.json
```

Includes:
- Query
- Validated hypotheses
- Timestamps

---

# 🔐 Reproducibility

- Fixed random seed (`random_seed=42`)
- Pinned library versions
- Configurable sample/full dataset mode
- Deterministic pipeline

---

# 🏷️ Release Instructions

Before submitting:

```bash
git add .
git commit -m "final project"
git tag -a v1.0 -m "v1.0 submission"
git push --tags
```

Create a PR titled **“self-review”** describing:
- architecture decisions  
- why you chose your heuristics  
- known limitations  
- next steps you would take  

---

# 🎯 Submission

Submit:
- Public GitHub repo URL  
- Commit hash  
- Tag name `v1.0`  
- CLI command used to generate outputs  

