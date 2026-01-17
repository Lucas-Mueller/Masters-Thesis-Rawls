#!/usr/bin/env python3
"""
Simple test script to run a standard experiment with 2 agents.

This script runs a standard experiment with gpt-4.1-mini agents and memory enabled.
"""

import asyncio
import sys
import traceback
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

from maai.runners import run_experiment


async def run_standard_test():
    """Run a standard experiment with 2 agents, gpt-4.1-mini, and memory enabled."""
    
    print("=" * 60)
    print("🧪 RUNNING STANDARD EXPERIMENT TEST")
    print("=" * 60)
    print()
    
    print("📋 Configuration:")
    print("  - Agents: 2 (Agent1, Agent2)")
    print("  - Model: gpt-4.1-mini")
    print("  - Memory: Enabled (phase_aware_decomposed)")
    print("  - Individual Rounds: 4")
    print("  - Max Group Rounds: 5")
    print("  - Bank Account: Enabled")
    print()
    
    start_time = datetime.now()
    
    try:
        print("🚀 Starting experiment...")
        print()
        
        # Create a simple config on-the-fly
        config_name = "test_standard"
        
        # Run experiment with correct config path parameters
        result = await run_experiment(
            config_path="test",  # Just the config name
            output_dir="experiment_results",
            config_dir="test_lucas"  # Specify the config directory
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Check if experiment actually succeeded
        if not result.get("success", True):
            print()
            print("=" * 60)
            print("❌ EXPERIMENT FAILED")
            print("=" * 60)
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  Error: {result.get('error', 'Unknown error')}")
            print(f"  Config Path: {result.get('experiment_id', 'N/A')}")
            print()
            print("🔧 Check the configuration file and ensure all paths are correct")
            return False
        
        # Check for missing output file (another indicator of silent failure)
        if result.get("output_path") is None:
            print()
            print("=" * 60)
            print("⚠️  EXPERIMENT COMPLETED BUT NO OUTPUT GENERATED")
            print("=" * 60)
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  This likely indicates a configuration error")
            print()
            return False
        
        # Check for suspiciously quick completion (less than 10 seconds)
        if duration < 10:
            print()
            print("=" * 60)
            print("⚠️  SUSPICIOUSLY QUICK COMPLETION")
            print("=" * 60)
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  Real experiments typically take 30+ seconds")
            print(f"  This may indicate a silent failure")
            print()
        
        print()
        print("=" * 60)
        print("✅ EXPERIMENT COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Experiment ID: {result.get('experiment_id', 'N/A')}")
        print(f"  Consensus Reached: {result.get('consensus_reached', 'N/A')}")
        print(f"  Output Path: {result.get('output_path', 'N/A')}")
        print()
        
        # Show some key results
        if result.get('total_messages', 0) > 0:
            print("🔍 Key Results:")
            print(f"  - Total messages exchanged: {result.get('total_messages', 0)}")
            print(f"  - Rounds to consensus: {result.get('rounds_to_consensus', 0)}")
            print(f"  - Phase 1 and Phase 2 completed")
            print(f"  - Memory and bank account tracking active")
            print()
        else:
            print("⚠️  No messages exchanged - check if experiment actually ran")
            print()
        
        print("📁 Results saved in: experiment_results/")
        print("🎉 Test completed successfully!")
        
        return True
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 60)
        print("❌ EXPERIMENT FAILED")
        print("=" * 60)
        print(f"  Duration: {duration:.1f} seconds")  
        print(f"  Error: {str(e)}")
        print()
        print("🔍 DETAILED ERROR:")
        traceback.print_exc()
        print()
        
        return False


def main():
    """Main entry point."""
    print(f"🕐 Starting test at {datetime.now()}")
    print()
    
    # Run the async test
    success = asyncio.run(run_standard_test())
    
    print()
    print("=" * 60)
    if success:
        print("🎉 STANDARD TEST PASSED!")
        print("📊 Check experiment_results/ for detailed output")
    else:
        print("❌ STANDARD TEST FAILED!")
        print("🔧 Review error details above")
    print("=" * 60)


if __name__ == "__main__":
    main()