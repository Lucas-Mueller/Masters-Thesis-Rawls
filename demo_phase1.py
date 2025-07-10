"""
Demo script for Phase 1 implementation.
Shows the enhanced multi-agent deliberation system in action.
"""

import asyncio
import os
import uuid
from datetime import datetime

from models import ExperimentConfig
from deliberation_manager import run_single_experiment


async def run_demo():
    """Run a demonstration of the enhanced system."""
    print("🎯 Multi-Agent Distributive Justice Experiment - Phase 1 Demo")
    print("=" * 70)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return
    
    # Create a demo experiment configuration
    config = ExperimentConfig(
        experiment_id=f"demo_{uuid.uuid4().hex[:8]}",
        num_agents=4,
        max_rounds=5,
        decision_rule="unanimity",
        timeout_seconds=300,
        models=["gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini", "gpt-4.1-mini"]
    )
    
    print(f"🏁 Starting Demo Experiment")
    print(f"   Experiment ID: {config.experiment_id}")
    print(f"   Agents: {config.num_agents}")
    print(f"   Decision Rule: {config.decision_rule}")
    print(f"   Max Rounds: {config.max_rounds}")
    print(f"   Timeout: {config.timeout_seconds}s")
    print()
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        
        print("\n" + "=" * 70)
        print("📊 EXPERIMENT RESULTS")
        print("=" * 70)
        
        # Basic results
        print(f"🎯 Consensus Reached: {'✅ YES' if results.consensus_result.unanimous else '❌ NO'}")
        print(f"⏱️  Total Duration: {results.performance_metrics.total_duration_seconds:.1f} seconds")
        print(f"🔄 Rounds Completed: {results.consensus_result.rounds_to_consensus}")
        print(f"💬 Total Messages: {len(results.deliberation_transcript)}")
        print(f"⚡ Avg Round Duration: {results.performance_metrics.average_round_duration:.1f}s")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"🏆 Agreed Principle: {principle.principle_id} - {principle.principle_name}")
            print(f"🎯 Confidence: {principle.confidence:.1%}")
        else:
            print(f"⚠️  Dissenting Agents: {results.consensus_result.dissenting_agents}")
        
        print("\n" + "=" * 70)
        print("📝 DELIBERATION TRANSCRIPT")
        print("=" * 70)
        
        # Group messages by round
        rounds = {}
        for response in results.deliberation_transcript:
            round_num = response.round_number
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(response)
        
        # Show transcript
        for round_num in sorted(rounds.keys()):
            round_name = "🎯 INITIAL EVALUATION" if round_num == 0 else f"🔄 ROUND {round_num}"
            print(f"\n{round_name}")
            print("-" * 50)
            
            responses = rounds[round_num]
            
            # Show choices summary
            choices = [r.updated_choice.principle_id for r in responses]
            choice_summary = ", ".join([f"{r.agent_name}: P{r.updated_choice.principle_id}" for r in responses])
            print(f"Choices: {choice_summary}")
            
            # Show a sample message from each agent
            for response in responses:
                print(f"\n🤖 {response.agent_name} (Principle {response.updated_choice.principle_id}):")
                
                # Show first 200 characters of message
                message = response.message.strip()
                if len(message) > 200:
                    message = message[:200] + "..."
                print(f"   {message}")
                
                # Show confidence if available
                if hasattr(response.updated_choice, 'confidence'):
                    print(f"   Confidence: {response.updated_choice.confidence:.1%}")
        
        print("\n" + "=" * 70)
        print("🎯 PRINCIPLE ANALYSIS")
        print("=" * 70)
        
        # Analyze choice evolution
        print("📈 Choice Evolution:")
        for round_num in sorted(rounds.keys()):
            round_name = "Initial" if round_num == 0 else f"Round {round_num}"
            responses = rounds[round_num]
            choices = [r.updated_choice.principle_id for r in responses]
            choice_counts = {}
            for choice in choices:
                choice_counts[choice] = choice_counts.get(choice, 0) + 1
            
            choice_str = ", ".join([f"P{p}:{count}" for p, count in sorted(choice_counts.items())])
            print(f"   {round_name}: {choice_str}")
        
        # Show principle definitions
        from models import DISTRIBUTIVE_JUSTICE_PRINCIPLES
        print("\n📚 Principle Definitions:")
        for pid, info in DISTRIBUTIVE_JUSTICE_PRINCIPLES.items():
            print(f"   {pid}. {info['short_name']}: {info['description']}")
        
        print("\n" + "=" * 70)
        print("✨ DEMO COMPLETE")
        print("=" * 70)
        
        if results.consensus_result.unanimous:
            print("🎉 The agents successfully reached unanimous agreement!")
            print("   This demonstrates the enhanced multi-agent deliberation system working correctly.")
        else:
            print("🤔 The agents did not reach unanimous agreement within the time limit.")
            print("   This shows the system properly handles disagreement scenarios.")
        
        print("\n🔧 Phase 1 Implementation Features Demonstrated:")
        print("   ✅ Enhanced agent architecture with specialized roles")
        print("   ✅ Multi-round deliberation engine")
        print("   ✅ Consensus detection and resolution")
        print("   ✅ Comprehensive data collection and logging")
        print("   ✅ Structured output models with validation")
        print("   ✅ Performance metrics tracking")
        print("   ✅ Robust error handling")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_demo())