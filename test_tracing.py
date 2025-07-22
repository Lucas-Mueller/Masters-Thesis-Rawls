#!/usr/bin/env python3
"""
Test script to verify OpenAI Agents SDK tracing integration.
This script runs a quick experiment to test the tracing functionality.
"""

import asyncio
from src.maai.runners import run_experiment


async def test_tracing():
    """Test the tracing implementation with a basic experiment."""
    
    print("=== Testing OpenAI Agents SDK Tracing Integration ===")
    print("")
    
    try:
        # Run a minimal experiment with tracing-optimized configuration
        result = await run_experiment(
            config_path="tracing_test",
            output_dir="test_tracing_output"
        )
        
        if result["success"]:
            print("✅ Experiment completed successfully!")
            print(f"   Experiment ID: {result['experiment_id']}")
            print(f"   Consensus reached: {result['consensus_reached']}")
            print(f"   Duration: {result['duration_seconds']:.1f}s")
            print(f"   Output file: {result['output_path']}")
            print("")
            print("🔍 TRACING INFORMATION:")
            print(f"   Trace ID: {result['trace_id']}")
            print(f"   Trace URL: {result['trace_url']}")
            print("")
            print("You can now view the complete trace in the OpenAI platform using the URL above.")
            print("The trace includes all agent interactions, LLM calls, and experiment phases.")
            
        else:
            print("❌ Experiment failed!")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_tracing())