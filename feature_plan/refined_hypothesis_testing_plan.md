# Refined Hypothesis Testing Plan: AI Agents' Distributive Justice Assessment Changes

## Hypothesis
**"The initial and final assessment of the 4 different principles differs"**

## 1. Statistical Approach Revision

### The Normality Problem
You're absolutely correct! **Likert scale data (1-4) cannot be assumed to be normally distributed**:
- **Discrete ordinal data** with only 4 possible values
- **Likely skewed distributions** (agents may cluster around certain ratings)
- **Ceiling/floor effects** possible
- **Small sample sizes** per condition make normality testing unreliable

### Revised Statistical Framework

#### Primary Statistical Tests (Non-parametric)
1. **Wilcoxon Signed-Rank Test**: Non-parametric alternative to paired t-test
   - Tests median difference in before/after ratings
   - No normality assumption required
   - Robust to outliers and skewed distributions

2. **Sign Test**: Simple and robust alternative
   - Tests whether ratings tend to increase/decrease
   - Only requires direction of change
   - Most conservative test

3. **Permutation Tests**: For complex comparisons
   - Bootstrap confidence intervals for effect sizes
   - No distributional assumptions
   - Exact p-values for small samples

#### Secondary Analyses (Ordinal-Appropriate)
1. **Ordinal Logistic Regression**: For configuration effects
   - Proper treatment of ordinal outcomes
   - Can include random effects for agents
   - Odds ratios as effect sizes

2. **Spearman Correlations**: For continuous predictors
   - Temperature vs rating change magnitude
   - Rounds to consensus vs rating stability

3. **Chi-square Tests**: For categorical analyses
   - Rating direction changes by configuration
   - Model type vs improvement patterns

## 2. Simplified Design with Default Personalities

### Design Principle: Systematic Parameter Variation
**Use default personality for all agents** to isolate technical parameter effects:
- Removes confounding personality variables
- Focuses on system parameters (temperature, model, memory strategy, etc.)
- Cleaner interpretation of results

### Parameter Generation Logic

#### Core Parameters to Vary:
1. **Number of Agents**: 3, 4, 5, 6 (balanced representation)
2. **Temperature Strategy**: Individual vs Global control
3. **Model Diversity**: Homogeneous vs Heterogeneous
4. **Memory Strategy**: "full", "recent", "decomposed"  
5. **Deliberation Length**: Short (2-3) vs Long (4-5) rounds

#### Systematic Logic for 10 Configurations:

**Configuration Generation Algorithm:**
```python
def generate_configurations():
    # Base parameters to systematically vary
    agent_counts = [3, 4, 5, 6]
    temp_strategies = ["global_low", "global_high", "individual_varied", "individual_extreme"]
    model_strategies = ["homogeneous", "mixed", "diverse"]
    memory_strategies = ["full", "recent", "decomposed"]
    round_lengths = [2, 3, 4, 5]
    
    # Generate 10 configurations with maximum variance
    configs = []
    
    # Pattern: Systematically cycle through parameter combinations
    # ensuring each parameter value appears roughly equally
```

### 10 Systematic Configurations:

#### Config 1: "Minimal Baseline"
- **Purpose**: Simple control condition
- **Agents**: 3, all `gpt-4.1-mini`, default personality
- **Temperature**: `global_temperature: 0.0` (deterministic)
- **Memory**: `full`
- **Rounds**: 2

#### Config 2: "Scale Test - Small Group High Variance"
- **Purpose**: Small group with high temperature variance
- **Agents**: 3, all `gpt-4.1-mini`, default personality
- **Temperature**: Individual [0.0, 0.5, 1.0] (extreme spread)
- **Memory**: `decomposed`
- **Rounds**: 3

#### Config 3: "Scale Test - Large Group Low Variance"
- **Purpose**: Large group with consistent temperature
- **Agents**: 6, all `gpt-4.1-mini`, default personality
- **Temperature**: `global_temperature: 0.3` (consistent moderate)
- **Memory**: `recent`
- **Rounds**: 4

#### Config 4: "Model Diversity - Mixed"
- **Purpose**: Test different model effects
- **Agents**: 4, mixed models [`gpt-4.1-mini`, `claude-sonnet-4`, `deepseek-chat`, `llama-4-maverick`]
- **Temperature**: `global_temperature: 0.5`
- **Memory**: `full`
- **Rounds**: 3

#### Config 5: "Model Diversity - Premium"
- **Purpose**: High-end model comparison
- **Agents**: 4, premium [`gpt-4.1`, `claude-sonnet-4`, `deepseek-reasoner`, `grok-3-mini`]
- **Temperature**: Individual [0.2, 0.4, 0.6, 0.8] (stepped)
- **Memory**: `decomposed`
- **Rounds**: 3

#### Config 6: "Memory Strategy Focus"
- **Purpose**: Isolate memory strategy effects
- **Agents**: 5, all `deepseek-chat`, default personality
- **Temperature**: `global_temperature: 0.4`
- **Memory**: `recent` (memory_window: 2)
- **Rounds**: 5

#### Config 7: "Extended Deliberation"
- **Purpose**: Test long deliberation effects
- **Agents**: 4, alternating [`gpt-4.1-mini`, `deepseek-chat`, `gpt-4.1-mini`, `deepseek-chat`]
- **Temperature**: Individual [0.1, 0.3, 0.7, 0.9] (spread)
- **Memory**: `full`
- **Rounds**: 5

#### Config 8: "Temperature Strategy - Global Override"
- **Purpose**: Test global vs individual temperature
- **Agents**: 5, mixed models [`gpt-4.1-nano`, `claude-sonnet-4`, `deepseek-chat`, `llama-3-70B`, `grok-3-mini`]
- **Individual Temps**: [0.2, 0.4, 0.6, 0.8, 1.0] (should be overridden)
- **Global**: `global_temperature: 0.0` (override to deterministic)
- **Memory**: `decomposed`
- **Rounds**: 3

#### Config 9: "High Creativity"
- **Purpose**: Test high temperature effects
- **Agents**: 3, all `llama-4-maverick`, default personality
- **Temperature**: `global_temperature: 1.0` (maximum creativity)
- **Memory**: `recent`
- **Rounds**: 4

#### Config 10: "Balanced Complex"
- **Purpose**: Moderate complexity across all parameters
- **Agents**: 6, diverse models [`gpt-4.1-mini`, `gpt-4.1-nano`, `claude-sonnet-4`, `deepseek-chat`, `llama-3-70B`, `grok-3-mini`]
- **Temperature**: Individual [0.25, 0.35, 0.45, 0.55, 0.65, 0.75] (moderate spread)
- **Memory**: `decomposed`
- **Rounds**: 4

### Parameter Coverage Analysis:
- **Agent counts**: 3(×3), 4(×3), 5(×2), 6(×2) - balanced
- **Temperature strategies**: Global(×4), Individual(×6) - balanced  
- **Memory strategies**: full(×3), recent(×3), decomposed(×4) - balanced
- **Round lengths**: 2(×1), 3(×4), 4(×3), 5(×2) - realistic distribution
- **Model diversity**: Homogeneous(×3), Mixed(×4), Diverse(×3) - balanced

## 3. Robust Statistical Analysis Plan

### Data Structure from Logs
```python
# Extract from JSON logs:
initial_ratings = [1, 2, 3, 4]  # Per agent per principle
final_ratings = [1, 2, 3, 4]    # Per agent per principle
rating_changes = final - initial  # Can be -3 to +3

# Configuration variables:
num_agents, temperature_strategy, model_diversity, memory_strategy, rounds
```

### Primary Hypothesis Tests

#### 1. Overall Change Test (Non-parametric)
```python
# Wilcoxon Signed-Rank Test
from scipy.stats import wilcoxon

# All rating changes across all experiments
all_changes = [final_rating - initial_rating for all agents, all principles, all experiments]
statistic, p_value = wilcoxon(all_changes)

# Effect size: r = Z / sqrt(N)
effect_size = abs(statistic) / sqrt(len(all_changes))
```

#### 2. Individual Principle Analysis
```python
# Separate tests for each principle with Bonferroni correction
alpha = 0.05 / 4  # = 0.0125

for principle_id in [1, 2, 3, 4]:
    principle_changes = [changes for specific principle]
    stat, p = wilcoxon(principle_changes)
    significant = p < alpha
```

#### 3. Bootstrapped Confidence Intervals
```python
# Bootstrap for robust effect size estimation
def bootstrap_median_change(data, n_bootstrap=1000):
    bootstrap_medians = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_medians.append(np.median(sample))
    return np.percentile(bootstrap_medians, [2.5, 97.5])
```

### Secondary Analyses

#### 1. Configuration Effect Analysis (Ordinal Regression)
```python
# Ordinal logistic regression for rating changes
from statsmodels.miscmodels.ordinal_model import OrderedModel

# Model: Rating_Change ~ Temperature_Strategy + Model_Diversity + Memory_Strategy + Num_Agents
model = OrderedModel(rating_changes, configuration_predictors, 
                    distr='logit')
result = model.fit()
```

#### 2. Non-parametric Correlations
```python
# Spearman correlations for ordinal data
from scipy.stats import spearmanr

# Temperature vs change magnitude
corr, p = spearmanr(temperature_values, abs(rating_changes))

# Memory strategy vs rating stability
corr, p = spearmanr(memory_strategy_encoded, rating_variance)
```

#### 3. Chi-square Tests for Categorical Analysis
```python
# Direction of change by configuration
from scipy.stats import chi2_contingency

# Create contingency table: Configuration × Change Direction (Positive/Negative/None)
contingency_table = pd.crosstab(configuration_type, change_direction)
chi2, p, dof, expected = chi2_contingency(contingency_table)
```

### Advanced Robust Analyses

#### 1. Permutation Tests
```python
def permutation_test(group1, group2, n_permutations=10000):
    """Non-parametric test for group differences"""
    observed_diff = np.median(group1) - np.median(group2)
    
    combined = np.concatenate([group1, group2])
    n1 = len(group1)
    
    permuted_diffs = []
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_group1 = combined[:n1]
        perm_group2 = combined[n1:]
        permuted_diffs.append(np.median(perm_group1) - np.median(perm_group2))
    
    p_value = np.mean(np.abs(permuted_diffs) >= np.abs(observed_diff))
    return observed_diff, p_value
```

#### 2. Robust Effect Sizes
```python
# Cliff's delta: Non-parametric effect size
def cliffs_delta(group1, group2):
    """Robust effect size for ordinal data"""
    n1, n2 = len(group1), len(group2)
    
    # Count pairs where group1 > group2
    dominance = sum(1 for x1 in group1 for x2 in group2 if x1 > x2)
    
    # Cliff's delta = (dominance - subordinance) / (n1 * n2)
    subordinance = sum(1 for x1 in group1 for x2 in group2 if x1 < x2)
    delta = (dominance - subordinance) / (n1 * n2)
    
    return delta  # Range: -1 to +1
```

## 4. Implementation Framework

### Configuration Generation Logic
```python
def generate_systematic_configs():
    """Generate 10 configurations with systematic parameter variation"""
    
    base_config = {
        "experiment": {"decision_rule": "unanimity", "timeout_seconds": 300},
        "defaults": {
            "personality": "You are an agent tasked to design a future society.",
            "model": "gpt-4.1-mini"
        },
        "memory_strategy": "full",
        "output": {"directory": "experiment_results", "formats": ["json"]},
        "performance": {"trace_enabled": True, "debug_mode": False}
    }
    
    configurations = [
        # Config 1: Minimal baseline
        {
            **base_config,
            "experiment_id": "hyp_test_01_minimal_baseline",
            "global_temperature": 0.0,
            "agents": [{"name": f"Agent_{i}"} for i in range(1, 4)],
            "experiment": {**base_config["experiment"], "max_rounds": 2},
            "memory_strategy": "full"
        },
        
        # Config 2: Small group high temp variance
        {
            **base_config,
            "experiment_id": "hyp_test_02_small_high_variance",
            "agents": [
                {"name": "Agent_1", "temperature": 0.0},
                {"name": "Agent_2", "temperature": 0.5},
                {"name": "Agent_3", "temperature": 1.0}
            ],
            "experiment": {**base_config["experiment"], "max_rounds": 3},
            "memory_strategy": "decomposed"
        },
        
        # ... (continue for all 10 configurations)
    ]
    
    return configurations
```

### Data Analysis Pipeline
```python
def analyze_experiment_results(experiment_folders):
    """Non-parametric analysis of rating changes"""
    
    # 1. Extract data
    data = extract_ratings_from_logs(experiment_folders)
    
    # 2. Primary hypothesis tests
    results = {
        'overall_change': wilcoxon_test(data['all_changes']),
        'principle_tests': bonferroni_corrected_tests(data['by_principle']),
        'effect_sizes': bootstrap_effect_sizes(data['all_changes'])
    }
    
    # 3. Configuration analysis
    results['config_effects'] = ordinal_regression_analysis(data)
    
    # 4. Robust correlations
    results['correlations'] = spearman_correlation_analysis(data)
    
    return results
```

## 5. Expected Statistical Power

### Power Analysis for Non-parametric Tests
- **10 experiments × 3-6 agents × 4 principles = 120-240 observations**
- **Wilcoxon test power**: >0.80 for medium effects (r=0.3) with n>100
- **Sign test power**: More conservative but very robust
- **Permutation test power**: Excellent for any effect size with sufficient n

### Interpretation Framework
- **Wilcoxon p<0.05**: Evidence of systematic rating changes
- **Effect size r>0.3**: Meaningful practical significance  
- **Cliff's delta |d|>0.33**: Medium effect size for ordinal data
- **Configuration effects**: Ordinal regression odds ratios

This refined approach provides robust statistical inference without problematic normality assumptions while maintaining scientific rigor and interpretability.