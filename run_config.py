
"""
Universal experiment runner for any YAML configuration.
Simply change the CONFIG_NAME variable below to run different experiments.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv
import agentops

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Initialize environment and AgentOps
load_dotenv()

# Suppress OpenAI beta warnings in AgentOps
os.environ.setdefault("AGENTOPS_SUPPRESS_OPENAI_WARNINGS", "true")

# Import core modules first to avoid circular imports
from maai.config.manager import load_config_from_file
from maai.core.models import all_models_are_openai

# CONFIG_NAME must be defined before the tracing configuration function
CONFIG_NAME = "temperature_test"  # Options: "lucas", "quick_test", "large_group", "multi_model", "default", "philosophical_debate", "economic_perspectives", "mixed_defaults"

# Pre-configure OpenAI tracing based on the config
def configure_openai_tracing():
    """Configure OpenAI tracing based on the configuration."""
    try:
        config = load_config_from_file(CONFIG_NAME)
        openai_only_run = all_models_are_openai(config)
        
        if openai_only_run:
            # Enable OpenAI Agents SDK tracing for OpenAI-only runs
            os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "0"
            return True, config
        else:
            # Disable OpenAI Agents SDK tracing for mixed provider runs
            os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
            return False, config
    except Exception as e:
        print(f"Error configuring tracing: {e}")
        # Default to disabled tracing on error
        os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
        return False, None

# Configure tracing before importing deliberation_manager
openai_tracing_enabled, _ = configure_openai_tracing()

# Now import the deliberation manager after tracing is configured
from maai.core.deliberation_manager import run_single_experiment

# Initialize AgentOps after imports to avoid circular dependency issues

async def main():
    """Run experiment with the specified configuration."""
    print(f"🎯 Running Configuration: {CONFIG_NAME}")
    print("=" * 60)
    
    # Check for AgentOps API key first
    AGENT_OPS_API_KEY = os.environ.get("AGENT_OPS_API_KEY")
    
    try:
        # Load specified config (already loaded during tracing configuration)
        print(f" Loading {CONFIG_NAME}.yaml configuration...")
        config = load_config_from_file(CONFIG_NAME)
        
        # Conditional tracing initialization to avoid conflicts
        # Only use AgentOps when OpenAI tracing is disabled
        if openai_tracing_enabled:
            print("🔍 OpenAI Agents SDK tracing enabled (all models are OpenAI)")
            print("ℹ️  AgentOps disabled to prevent instrumentation conflict")
        else:
            print("ℹ️  OpenAI Agents SDK tracing disabled (mixed model providers)")
            # Initialize AgentOps only for mixed-provider runs
            if AGENT_OPS_API_KEY:
                agentops.init(
                    api_key=AGENT_OPS_API_KEY,
                    auto_start_session=False,
                    tags=["distributive_justice_experiment"]
                )
                # Start session with experiment ID as session name
                agentops.start_session(tags=[str(config.experiment_id), "distributive_justice_experiment"])
                print("🔍 AgentOps monitoring enabled")
            else:
                print("⚠️  No tracing active (AgentOps API key not found)")

        
        print(f"   Configuration loaded successfully")
        print(f"   #Agents: {config.num_agents}")
        print(f"   Max Rounds: {config.max_rounds}")
        print(f"   ⏱ Timeout: {config.timeout_seconds}s")
        print(f"   Decision Rule: {config.decision_rule}")


        print(f"   Agent Details:")
        for agent in config.agents:
            model = agent.model or config.defaults.model
            has_custom = "✨" if agent.personality else "📝"
            print(f"      {has_custom} {agent.name}: {model}")
        print()
        
        # Run experiment
        print("Starting experiment...")
        results = await run_single_experiment(config)
        
        # Show results
        print("\n" + "=" * 60)
        print(" EXPERIMENT RESULTS")
        print("=" * 60)
        
        print(f"Consensus Reached: {'✅ YES' if results.consensus_result.unanimous else '❌ NO'}")
        print(f"⏱ Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        print(f"#Rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"Messages: {len(results.deliberation_transcript)}")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"Agreed Principle: {principle.principle_id} - {principle.principle_name}")
        
        # Show where results are saved
        print(f"\n📁 Results saved to: experiment_results/")
        print(f"   📄 Main file: {config.experiment_id}_complete.json")
        print(f"   📊 Summary: {config.experiment_id}_summary.txt")
        print(f"   💬 Transcript: {config.experiment_id}_transcript.txt")
        
        
        if results.feedback_responses:
            avg_satisfaction = sum(fb.satisfaction_rating for fb in results.feedback_responses) / len(results.feedback_responses)
            print(f"   📝 Average Satisfaction: {avg_satisfaction:.1f}/10")
        
        print("\n🎉 Experiment completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running experiment: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # End AgentOps session only if it was initialized (mixed-provider runs)
        if not openai_tracing_enabled and AGENT_OPS_API_KEY:
            try:
                agentops.end_session("Success")
                print("🔍 AgentOps session completed - view at: https://app.agentops.ai/")
            except Exception as e:
                print(f"⚠️  AgentOps session end failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())