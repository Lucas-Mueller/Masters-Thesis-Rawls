"""
Demo script for Phase 2 implementation.
Shows the enhanced data collection, feedback system, and configuration management.
"""

import asyncio
import os
from pathlib import Path

from config_manager import ConfigManager, PresetConfigs, load_config_from_file
from deliberation_manager import run_single_experiment


async def demo_configuration_management():
    """Demonstrate the configuration management system."""
    print("🔧 Configuration Management Demo")
    print("=" * 50)
    
    # Show available configurations
    manager = ConfigManager()
    configs = manager.list_configs()
    print(f"📁 Available configurations: {configs}")
    
    # Load and display different configs
    print(f"\n📋 Configuration Details:")
    for config_name in ["quick_test", "multi_model", "large_group"]:
        if config_name in configs:
            config = manager.load_config(config_name)
            print(f"   {config_name}:")
            print(f"     - Agents: {config.num_agents}")
            print(f"     - Max Rounds: {config.max_rounds}")
            print(f"     - Models: {len(config.models)} different models")
            print(f"     - Timeout: {config.timeout_seconds}s")
    
    # Show preset configs
    print(f"\n🎯 Preset Configurations:")
    presets = [
        ("Quick Test", PresetConfigs.quick_test()),
        ("Standard", PresetConfigs.standard_experiment()),
        ("Large Group", PresetConfigs.large_group())
    ]
    
    for name, config in presets:
        print(f"   {name}: {config.num_agents} agents, {config.max_rounds} rounds")


async def demo_enhanced_experiment():
    """Run a demonstration experiment with all Phase 2 features."""
    print("\n🧪 Enhanced Experiment Demo")
    print("=" * 50)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY to run the experiment demo")
        return
    
    # Use a quick test configuration
    print("🚀 Running experiment with quick_test configuration...")
    config = PresetConfigs.quick_test()
    
    print(f"   Configuration: {config.num_agents} agents, {config.max_rounds} rounds")
    print(f"   Decision Rule: {config.decision_rule}")
    print(f"   Timeout: {config.timeout_seconds}s")
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        
        # Analyze results
        print(f"\n📊 Experiment Results Analysis:")
        print(f"   ✅ Consensus Reached: {'Yes' if results.consensus_result.unanimous else 'No'}")
        print(f"   ⏱️  Duration: {results.performance_metrics.total_duration_seconds:.1f}s")
        print(f"   🔄 Rounds: {results.consensus_result.rounds_to_consensus}")
        print(f"   💬 Messages: {len(results.deliberation_transcript)}")
        
        if results.consensus_result.unanimous:
            principle = results.consensus_result.agreed_principle
            print(f"   🏆 Agreed Principle: {principle.principle_id} - {principle.principle_name}")
        
        # Feedback analysis
        if results.feedback_responses:
            print(f"\n📝 Feedback Collection Results:")
            print(f"   📊 Responses Collected: {len(results.feedback_responses)}")
            
            avg_satisfaction = sum(fb.satisfaction_rating for fb in results.feedback_responses) / len(results.feedback_responses)
            avg_fairness = sum(fb.fairness_rating for fb in results.feedback_responses) / len(results.feedback_responses)
            would_choose_again = sum(1 for fb in results.feedback_responses if fb.would_choose_again)
            
            print(f"   😊 Average Satisfaction: {avg_satisfaction:.1f}/10")
            print(f"   ⚖️  Average Fairness: {avg_fairness:.1f}/10")
            print(f"   🔄 Would Choose Again: {would_choose_again}/{len(results.feedback_responses)} agents")
            
            # Show individual feedback
            print(f"\n   Individual Feedback:")
            for feedback in results.feedback_responses:
                print(f"     {feedback.agent_name}: Satisfaction {feedback.satisfaction_rating}/10, Fairness {feedback.fairness_rating}/10")
        
        # Data export information
        print(f"\n📁 Data Export:")
        export_dir = Path("experiment_results")
        if export_dir.exists():
            exported_files = list(export_dir.glob(f"{config.experiment_id}*"))
            print(f"   📂 Files exported: {len(exported_files)}")
            
            file_types = {}
            for file_path in exported_files:
                ext = file_path.suffix
                file_types[ext] = file_types.get(ext, 0) + 1
            
            for ext, count in file_types.items():
                print(f"     {ext} files: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Experiment demo failed: {e}")
        return False


async def demo_data_formats():
    """Demonstrate the different data export formats."""
    print(f"\n📄 Data Export Formats Demo")
    print("=" * 50)
    
    export_dir = Path("experiment_results")
    if not export_dir.exists():
        print("   ⚠️  No experiment results found. Run an experiment first.")
        return
    
    # Find the most recent experiment files
    json_files = list(export_dir.glob("*_complete.json"))
    if not json_files:
        print("   ⚠️  No complete experiment files found.")
        return
    
    latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
    experiment_id = latest_json.stem.replace("_complete", "")
    
    print(f"📊 Showing formats for experiment: {experiment_id}")
    
    # List all files for this experiment
    experiment_files = list(export_dir.glob(f"{experiment_id}*"))
    
    print(f"\n📁 Available Files ({len(experiment_files)} total):")
    
    for file_path in sorted(experiment_files):
        file_size = file_path.stat().st_size
        print(f"   📄 {file_path.name} ({file_size:,} bytes)")
        
        # Show a sample of content for text files
        if file_path.suffix == ".txt" and "summary" in file_path.name:
            print(f"      📝 Sample content:")
            try:
                content = file_path.read_text()
                lines = content.split('\n')[:5]  # First 5 lines
                for line in lines:
                    if line.strip():
                        print(f"         {line}")
                if len(content.split('\n')) > 5:
                    print(f"         ... ({len(content.split('\n'))} total lines)")
            except Exception:
                print(f"         (Could not read content)")


async def main():
    """Run the complete Phase 2 demonstration."""
    print("🎯 Multi-Agent Distributive Justice Experiment - Phase 2 Demo")
    print("=" * 70)
    
    print("🚀 Phase 2 Features:")
    print("   ✅ Post-experiment feedback collection")
    print("   ✅ Enhanced logging with multiple formats (JSON, CSV, TXT)")
    print("   ✅ Configuration management with YAML files")
    print("   ✅ Environment variable overrides")
    print("   ✅ Preset configurations for common scenarios")
    print("   ✅ Comprehensive data validation")
    print()
    
    # Demo 1: Configuration Management
    await demo_configuration_management()
    
    # Demo 2: Enhanced Experiment
    success = await demo_enhanced_experiment()
    
    # Demo 3: Data Formats (only if experiment succeeded)
    if success:
        await demo_data_formats()
    
    print("\n" + "=" * 70)
    print("✨ Phase 2 Demo Complete")
    print("=" * 70)
    
    if success:
        print("🎉 All Phase 2 features demonstrated successfully!")
        print("\n🔧 Phase 2 Implementation Highlights:")
        print("   📊 Rich data collection with structured feedback")
        print("   📁 Multiple export formats for analysis")
        print("   ⚙️  Flexible configuration management")
        print("   🎯 Preset configurations for different scenarios")
        print("   ✅ Comprehensive validation and error handling")
        print("   🔄 Environment variable support for CI/CD")
        
        print("\n📈 Ready for Phase 3: Experimental Variations")
        print("   🗳️  Decision rule variations (majority vs unanimity)")
        print("   📋 Imposed principle experiments")
        print("   📊 Batch experiment execution")
        print("   📈 Comparative analysis tools")
    else:
        print("⚠️  Some features could not be demonstrated (API key required)")
        print("🔧 Configuration and data format features are available")


if __name__ == "__main__":
    asyncio.run(main())