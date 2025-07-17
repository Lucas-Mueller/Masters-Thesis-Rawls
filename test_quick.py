#!/usr/bin/env python3
"""Quick test of the logging fixes."""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

from run_experiment import run_experiment

async def quick_test():
    try:
        print("🧪 Running quick test...")
        result = await run_experiment('test_logging_fixes', output_dir='test_results')
        
        if result['success']:
            print("✅ Test passed!")
            print(f"   Experiment ID: {result['experiment_id']}")
            print(f"   Output: {result['output_path']}")
            
            # Check the output file
            import json
            with open(result['output_path'], 'r') as f:
                data = json.load(f)
                
            print("\n=== Temperature Check ===")
            for agent_id, agent_data in data.items():
                if agent_id != 'experiment_metadata':
                    temp = agent_data.get('overall', {}).get('temperature')
                    print(f"  {agent_id}: {temp}")
                    
            print("\n=== Likert Rating Check ===")
            for agent_id, agent_data in data.items():
                if agent_id != 'experiment_metadata':
                    round_0 = agent_data.get('round_0', {})
                    if 'principle_ratings' in round_0:
                        print(f"  {agent_id}: HAS structured ratings ✅")
                    else:
                        print(f"  {agent_id}: NO structured ratings ❌")
            
        else:
            print("❌ Test failed!")
            print(f"   Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())