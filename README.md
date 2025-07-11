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

AI agents are presented with four principles of distributive justice and must reach **unanimous agreement** on one principle, while operating behind a "veil of ignorance" (not knowing their future economic position):

1. **Maximize the Minimum Income** - Ensure the worst-off are as well-off as possible (Rawlsian)
2. **Maximize the Average Income** - Greatest total income regardless of distribution (Utilitarian)
3. **Floor Constraint** - Minimum guaranteed income + maximize average (Hybrid)
4. **Range Constraint** - Limit inequality gap + maximize average (Hybrid)

## 🎁 What You Get

Running an experiment produces:

### 📊 Rich Data Collection
- **Complete conversation transcripts** of agent deliberations
- **Individual feedback interviews** with satisfaction and fairness ratings
- **Choice evolution tracking** showing how agents change their minds
- **Performance metrics** including duration, rounds, and consensus success

### 📁 Multiple Export Formats
- **JSON files** - Complete structured data for programmatic analysis
- **CSV files** - Spreadsheet-ready data for statistical analysis
- **Text transcripts** - Human-readable conversation logs
- **Summary reports** - Executive summaries of experiment outcomes

### 📈 Analysis-Ready Outputs
- Agent satisfaction ratings (1-10 scale)
- Fairness assessments of chosen principles
- Confidence levels in decisions
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
# Quick 3-agent test 
python demo_phase2.py
```

This will:
- Run a deliberation with 3 agents
- Show the decision-making process
- Collect post-experiment feedback
- Export results in multiple formats
- Display a summary of findings

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
| `quick_test` | 3 | 2 | Fast validation (1-2 minutes) |
| `multi_model` | 4 | 5 | Different AI models (3-5 minutes) |
| `large_group` | 8 | 10 | Larger deliberation (5-10 minutes) |

### Custom Configuration Files

Create `configs/my_experiment.yaml`:
```yaml
experiment_id: my_custom_experiment

experiment:
  num_agents: 6
  max_rounds: 7
  decision_rule: unanimity
  timeout_seconds: 400
  models:
    - gpt-4.1-mini
    - gpt-4.1
    - gpt-4.1-mini
    - gpt-4.1
    - gpt-4.1-mini
    - gpt-4.1-mini

output:
  directory: experiment_results
  include_feedback: true
  include_transcript: true
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
├── [ID]_complete.json          # Full structured data
├── [ID]_summary.csv           # Key metrics spreadsheet
├── [ID]_transcript.csv        # Conversation data
├── [ID]_feedback.csv          # Agent feedback responses
├── [ID]_choice_evolution.csv  # How choices changed
├── [ID]_transcript.txt        # Human-readable conversation
└── [ID]_summary.txt          # Executive summary
```

## 🔬 Research Applications

### Academic Use Cases
- **Philosophy Research**: Test theories of distributive justice
- **AI Ethics**: Study moral reasoning in artificial agents
- **Decision Science**: Analyze consensus formation mechanisms
- **Social Choice Theory**: Examine collective decision-making
- **Behavioral Economics**: Compare to human experimental data

### Example Research Questions
- Do AI agents naturally converge on Rawlsian principles?
- How does group size affect consensus formation?
- What factors influence agent satisfaction with outcomes?
- How do different AI models reason about justice differently?

## 🧪 Running Tests

Validate your installation:
```bash
# Test core functionality
python tests/test_phase1.py

# Test feedback collection
python tests/test_phase2_feedback.py

# Test data export
python tests/test_phase2_logging.py

# Test configuration system
python tests/test_phase2_config.py
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
from pathlib import Path

# Load experiment results
with open("experiment_results/my_exp_complete.json") as f:
    data = json.load(f)

# Analyze consensus patterns
consensus_rate = data["consensus_result"]["unanimous"]
satisfaction_scores = [fb["satisfaction_rating"] 
                      for fb in data["feedback_responses"]]
avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
```


**Ready to explore distributive justice with AI agents?** Start with `python demo_phase2.py` and see what principles artificial minds choose when they don't know their place in society! 🤖⚖️