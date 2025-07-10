#!/usr/bin/env python3
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
load_dotenv()

AGENT_OPS_API_KEY=os.environ.get("AGENT_OPS_API_KEY")
agentops.init(AGENT_OPS_API_KEY)
from maai.config.manager import load_config_from_file
from maai.core.deliberation_manager import run_single_experiment

# ========================================
# CHANGE THIS LINE TO RUN DIFFERENT CONFIGS
# ========================================
CONFIG_NAME = "lucas"  # Options: "lucas", "quick_test", "large_group", "multi_model", "default"

async def main():
    """Run experiment with the specified configuration."""
    print(f"🎯 Running Configuration: {CONFIG_NAME}")
    print("=" * 60)
    
    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Load specified config
        print(f"📋 Loading {CONFIG_NAME}.yaml configuration...")
        config = load_config_from_file(CONFIG_NAME)
        
        print(f"   ✓ Configuration loaded successfully")
        print(f"   📊 Agents: {config.num_agents}")
        print(f"   🔄 Max Rounds: {config.max_rounds}")
        print(f"   ⏱️  Timeout: {config.timeout_seconds}s")
        print(f"   🎯 Decision Rule: {config.decision_rule}")
        print(f"   🤖 Models: {config.models}")
        print()
        
        # Run experiment
        print("🚀 Starting experiment...")
        results = await run_single_experiment(config)
        
        # Show results
        print("\n" + "=" * 60)
        print("📊 EXPERIMENT RESULTS")
        print("=" * 60)
        
        print(f"🎯 Consensus Reached: {'✅ YES' if results.consensus_result.unanimous else '❌ NO'}")
        print(f"⏱️  Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        print(f"🔄 Rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"💬 Messages: {len(results.deliberation_transcript)}")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"🏆 Agreed Principle: {principle.principle_id} - {principle.principle_name}")
        
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

if __name__ == "__main__":
    asyncio.run(main())