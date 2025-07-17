#!/usr/bin/env python3
"""
Simple script to run a single experiment with a YAML config file.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Import experiment runner
from run_experiment import run_experiment


async def main():
    """Run a single experiment with specified config and output directory."""
    
    # Configuration
    config_file = "configs/lucas.yaml"  # Change this to your desired config file
    output_directory = "test_results"   # Change this to your desired output folder
    
    print(f"🚀 Running experiment with config: {config_file}")
    print(f"📁 Output directory: {output_directory}")
    print("-" * 50)
    
    try:
        # Run the experiment
        result = await run_experiment(config_file, output_dir=output_directory)
        
        if result["success"]:
            print("✅ Experiment completed successfully!")
            print(f"   Experiment ID: {result['experiment_id']}")
            print(f"   Consensus reached: {result['consensus_reached']}")
            print(f"   Duration: {result['duration_seconds']:.1f} seconds")
            print(f"   Total messages: {result['total_messages']}")
            print(f"   Results saved to: {result['output_path']}")
            
            if result['consensus_reached']:
                print(f"   Agreed principle: {result['agreed_principle']}")
                print(f"   Rounds to consensus: {result['rounds_to_consensus']}")
                
        else:
            print("❌ Experiment failed!")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)