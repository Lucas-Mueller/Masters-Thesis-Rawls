# Multi-Agent Distributive Justice Experiment

A sophisticated framework for conducting automated experiments on distributive justice using autonomous AI agents. This system simulates Rawls' "veil of ignorance" scenario where multiple AI agents deliberate and reach consensus on principles of distributive justice.

## 🎯 What This Project Does

This system allows you to:
- **Run automated philosophical experiments** with 3-50 AI agents
- **Test distributive justice theories** through multi-agent deliberation
- **Collect comprehensive data** on agent reasoning and decision-making
- **Analyze consensus formation** in artificial societies
- **Export results** in multiple formats for academic research

### The Experiment

The experiment follows a three-phase process:

**Phase 1: Initial Assessment** - Agents privately rate all 4 principles using Likert scales (NEW)
**Phase 2: Deliberation** - Agents debate and must reach **unanimous agreement** on one principle
**Phase 3: Final Assessment** - Agents re-rate all 4 principles after deliberation (NEW)

All agents operate behind a "veil of ignorance" (not knowing their future economic position) and choose from:

1. **Maximize the Minimum Income** - Ensure the worst-off are as well-off as possible (Rawlsian)
2. **Maximize the Average Income** - Greatest total income regardless of distribution (Utilitarian)
3. **Floor Constraint** - Minimum guaranteed income + maximize average (Hybrid)
4. **Range Constraint** - Limit inequality gap + maximize average (Hybrid)

## 🎁 What You Get

Running an experiment produces:

### 📊 Rich Data Collection
- **Initial Likert Scale Assessment** - Baseline preferences before deliberation (NEW)
- **Complete conversation transcripts** of agent deliberations
- **Post-consensus Likert evaluation** - How views changed after deliberation (NEW)
- **Before/after comparison data** - Rating evolution through deliberation (NEW)
- **Choice evolution tracking** showing how agents change their minds
- **Performance metrics** including duration, rounds, and consensus success

### 📁 Multiple Export Formats
- **JSON files** - Complete structured data for programmatic analysis
- **CSV files** - Spreadsheet-ready data for statistical analysis
- **Comparison CSV** - Before/after Likert rating analysis (NEW)
- **Text transcripts** - Human-readable conversation logs
- **Summary reports** - Executive summaries of experiment outcomes

### 📈 Analysis-Ready Outputs
- **Initial Likert ratings** (4-point scale: Strongly Disagree to Strongly Agree) (NEW)
- **Final Likert ratings** (4-point scale: Strongly Disagree to Strongly Agree) (NEW)
- **Rating evolution analysis** - How deliberation changes agent preferences (NEW)
- Agent satisfaction ratings (1-10 scale)
- Fairness assessments of chosen principles
- Round-by-round choice evolution
- Consensus formation patterns

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- OpenAI API key (required)
- Optional: Anthropic, DeepSeek API keys for model diversity

### 1. Installation

```bash
# Clone or download the project
cd /path/to/Masters-Thesis-Rawls-

# Install dependencies
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Required: OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional: Additional model providers
export ANTHROPIC_API_KEY="your-anthropic-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
export AGENT_OPS_API_KEY="your-agentops-key"
```

### 3. Run Your First Experiment

```bash
# Quick 3-agent test with full Likert evaluation
python run_quick_demo.py

# Or use configuration-based approach
python run_config.py  # Edit CONFIG_NAME in file to change config
```

This will:
- Collect initial Likert scale preferences (NEW)
- Run a deliberation with agents debating principles
- Collect final Likert scale preferences (NEW)
- Generate before/after comparison data (NEW)
- Export results in multiple formats
- Display a comprehensive summary

## 📖 Usage Examples

### Basic Experiment
```python
import asyncio
from maai.config.manager import load_config_from_file
from maai.core.deliberation_manager import run_single_experiment

# Run a quick test using YAML configuration
config = load_config_from_file("quick_test")
results = await run_single_experiment(config)
print(f"Consensus reached: {results.consensus_result.unanimous}")
```

### Custom Configuration
```python
from models import ExperimentConfig

config = ExperimentConfig(
    experiment_id="my_experiment",
    num_agents=5,
    max_rounds=8,
    decision_rule="unanimity",
    timeout_seconds=300
)
results = await run_single_experiment(config)
```

### Using Configuration Files
```bash
# Use predefined configurations
python -c "
import asyncio
from config_manager import load_config_from_file
from deliberation_manager import run_single_experiment

config = load_config_from_file('large_group')  # 8 agents
asyncio.run(run_single_experiment(config))
"
```

## ⚙️ Configuration Options

### Available Configurations

| Configuration | Agents | Rounds | Description |
|--------------|--------|--------|-------------|
| `quick_test` | 3 | 2 | Fast validation with Likert evaluation (1-2 minutes) |
| `lucas` | 4 | 3 | Custom personality agents (3-5 minutes) |
| `smart` | 4 | 3 | Different AI models with custom personalities |
| `default` | 3 | 10 | Standard experimental setup |

### Custom Configuration Files

Create `configs/my_experiment.yaml`:
```yaml
experiment_id: my_custom_experiment

experiment:
  max_rounds: 7
  decision_rule: unanimity
  timeout_seconds: 400

agents:
  - name: "Agent_1"
    model: "gpt-4.1-mini"
    personality: "You are an economist focused on efficiency."
  - name: "Agent_2"
    model: "gpt-4.1"
    personality: "You are a philosopher concerned with justice."
  - name: "Agent_3"
    model: "gpt-4.1-mini"
    personality: "You are a pragmatist focused on practical solutions."

defaults:
  personality: "You are an agent tasked to design a future society."
  model: "gpt-4.1-mini"

output:
  directory: experiment_results
  formats: [json, csv]
```

### Environment Variables

Customize experiments without changing code:
```bash
export MAAI_NUM_AGENTS=6
export MAAI_MAX_ROUNDS=8
export MAAI_TIMEOUT=600
export MAAI_DEBUG=true
```

## 📊 Understanding Your Results

### Experiment Outcomes

**Consensus Reached:**
- Agents successfully agreed on a principle
- View the agreed principle and reasoning
- Analyze satisfaction and fairness ratings

**No Consensus:**
- Agents couldn't agree within time/round limits
- See final choices and dissenting agents
- Useful for studying disagreement patterns

### Key Metrics

- **Satisfaction Rating** (1-10): How happy agents are with the group decision
- **Fairness Rating** (1-10): How fair agents think the chosen principle is
- **Would Choose Again**: Whether agents would make the same choice
- **Confidence Level**: Agent certainty in their feedback (0-100%)

### File Outputs

After each experiment, find files in `experiment_results/`:

```
experiment_results/
├── [ID]_complete.json              # Full structured data
├── [ID]_data.csv                   # Main conversation transcript data
├── [ID]_initial_evaluation.csv    # Initial Likert ratings (NEW)
├── [ID]_initial_evaluation.json   # Initial ratings with statistics (NEW)
├── [ID]_evaluation.csv            # Final Likert ratings (NEW)
├── [ID]_evaluation.json           # Final ratings with statistics (NEW)
└── [ID]_comparison.csv            # Before/after rating comparison (NEW)
```

### Key Research Files (NEW)

- **`[ID]_initial_evaluation.csv`** - Baseline preferences before deliberation
- **`[ID]_evaluation.csv`** - Final preferences after deliberation  
- **`[ID]_comparison.csv`** - Complete before/after analysis with rating changes

## 🔬 Research Applications

### Academic Use Cases
- **Philosophy Research**: Test theories of distributive justice
- **AI Ethics**: Study moral reasoning in artificial agents
- **Decision Science**: Analyze consensus formation mechanisms
- **Social Choice Theory**: Examine collective decision-making
- **Behavioral Economics**: Compare to human experimental data

### Example Research Questions
- **How does deliberation change agent preferences?** (NEW - use comparison data)
- **Do initial Likert ratings predict final consensus choices?** (NEW)
- **Which principles show the most rating volatility through deliberation?** (NEW)
- Do AI agents naturally converge on Rawlsian principles?
- How does group size affect consensus formation?
- What factors influence agent satisfaction with outcomes?
- How do different AI models reason about justice differently?

## 🧪 Running Tests

Validate your installation:
```bash
# Test all core functionality including new Likert evaluation
python run_tests.py

# Or test individual components
python tests/test_core.py
```

All tests should show "PASSED" status.

## 🛠️ Troubleshooting


**"No consensus reached"**
- This is normal behavior - not all groups agree
- Try increasing `max_rounds` or `timeout_seconds`
- Use different AI models for diversity

**"Import errors"**
```bash
# Ensure you're in the project directory
cd /path/to/Masters-Thesis-Rawls-

# Reinstall dependencies
pip install -r requirements.txt
```

### Getting Help

1. **Check the logs** in `experiment_results/` for error details
2. **Run tests** to identify specific issues
3. **Try `quick_test`** configuration first
4. **Verify API keys** are set correctly

## 📚 Advanced Usage

### Batch Experiments
```python
from maai.config.manager import load_config_from_file

# Load different YAML configurations
config_names = ["quick_test", "multi_model", "large_group"]

for config_name in config_names:
    config = load_config_from_file(config_name)
    results = await run_single_experiment(config)
    print(f"{config.experiment_id}: {results.consensus_result.unanimous}")
```

### Custom Analysis
```python
import json
import pandas as pd

# Load experiment results
with open("experiment_results/my_exp_complete.json") as f:
    data = json.load(f)

# Analyze consensus patterns
consensus_rate = data["consensus_result"]["unanimous"]

# NEW: Analyze Likert rating evolution
comparison_df = pd.read_csv("experiment_results/my_exp_comparison.csv")

# Calculate rating changes
rating_changes = comparison_df['Rating_Change'].mean()
print(f"Average rating change through deliberation: {rating_changes}")

# Analyze principle-specific changes
principle_changes = comparison_df.groupby('Principle_ID')['Rating_Change'].mean()
print("Rating changes by principle:")
print(principle_changes)
```

### Advanced Research Analysis (NEW)
```python
# Load initial and final evaluations
initial_df = pd.read_csv("experiment_results/my_exp_initial_evaluation.csv")
final_df = pd.read_csv("experiment_results/my_exp_evaluation.csv")

# Analyze preference stability
stable_ratings = comparison_df[comparison_df['Rating_Change'] == 0]
volatility_rate = 1 - (len(stable_ratings) / len(comparison_df))
print(f"Preference volatility rate: {volatility_rate:.2%}")

# Find most influential principles
principle_volatility = comparison_df.groupby('Principle_ID')['Rating_Change'].std()
print("Principle volatility (standard deviation of changes):")
print(principle_volatility)
```

**Ready to explore distributive justice with AI agents?** Start with `python run_quick_demo.py` and see how artificial minds' preferences evolve when they don't know their place in society! 🤖⚖️

## 🆕 What's New

### Latest Features (2025)
- ✅ **Initial Likert Scale Assessment** - Collect baseline preferences before deliberation
- ✅ **Parallel Evaluation Processing** - Faster data collection through concurrent agent processing
- ✅ **Before/After Comparison Analysis** - Track how deliberation changes agent preferences
- ✅ **Enhanced Export Formats** - Research-ready CSV files with comprehensive rating data
- ✅ **Improved Error Handling** - Robust parsing with graceful fallback mechanisms

### Research Impact
The new Likert scale evaluation system enables unprecedented analysis of preference evolution in artificial agents, providing insights into how collective deliberation influences individual judgment in AI systems.