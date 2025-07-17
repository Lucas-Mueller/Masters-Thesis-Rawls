#!/usr/bin/env python3
import traceback
import sys
import os
import asyncio

# Add src to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from run_experiment import run_experiment

async def test_debug():
    try:
        print("=== Starting test_debug ===")
        result = await run_experiment('lucas', output_dir='test_results')
        print('Success:', result['success'])
        if result['success']:
            print('Experiment completed successfully')
        else:
            print('Experiment failed:', result.get('error', 'Unknown error'))
    except Exception as e:
        print('EXCEPTION in test_debug:', e)
        print('Full traceback:')
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug())