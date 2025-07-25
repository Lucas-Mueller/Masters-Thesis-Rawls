"""
Simplified batch experiment runner - runs multiple experiments in parallel.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
from run_experiment import run_experiment


async def run_batch(config_paths: List[str], max_concurrent: int = 3, output_dir: str = None, config_dir: str = "configs") -> List[Dict[str, Any]]:
    """
    Run multiple experiments in parallel.
    
    Args:
        config_paths: List of configuration file paths or names
        max_concurrent: Maximum number of concurrent experiments
        output_dir: Optional custom output directory for experiment logs. 
                   Defaults to "experiment_results" if not specified.
        config_dir: Directory where configuration files are stored.
                   Defaults to "configs" if not specified.
    
    Returns:
        List of experiment results dictionaries
    """
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_single_with_semaphore(config_path: str, index: int) -> Dict[str, Any]:
        """Run single experiment with semaphore control."""
        async with semaphore:
            print(f"🧪 [{index+1}/{len(config_paths)}] Starting: {config_path}")
            
            start_time = time.time()
            result = await run_experiment(config_path, output_dir, config_dir)
            duration = time.time() - start_time
            
            # Add timing info
            result["batch_duration_seconds"] = duration
            result["batch_index"] = index
            
            if result["success"]:
                print(f"✅ [{index+1}/{len(config_paths)}] SUCCESS: {result['experiment_id']} ({duration:.1f}s)")
                print(f"   Output saved to: {result['output_path']}")
            else:
                print(f"❌ [{index+1}/{len(config_paths)}] FAILED: {config_path} ({duration:.1f}s)")
                print(f"   Error: {result['error']}")
            
            return result
    
    # Create tasks for all experiments
    tasks = [
        run_single_with_semaphore(config_path, i)
        for i, config_path in enumerate(config_paths)
    ]
    
    # Execute all experiments in parallel
    print(f"🚀 Starting batch execution: {len(config_paths)} experiments, max {max_concurrent} concurrent")
    if output_dir:
        print(f"📁 Output directory: {output_dir}")
    else:
        print(f"📁 Output directory: experiment_results (default)")
    batch_start_time = time.time()
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    batch_duration = time.time() - batch_start_time
    
    # Process results and handle exceptions
    processed_results = []
    successful_runs = 0
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Handle exceptions that occurred during execution
            error_result = {
                "success": False,
                "error": str(result),
                "experiment_id": config_paths[i],
                "consensus_reached": False,
                "duration_seconds": 0.0,
                "agreed_principle": None,
                "rounds_to_consensus": 0,
                "total_messages": 0,
                "results": None,
                "batch_duration_seconds": 0.0,
                "batch_index": i
            }
            processed_results.append(error_result)
            print(f"❌ [{i+1}/{len(config_paths)}] EXCEPTION: {config_paths[i]} - {result}")
        else:
            processed_results.append(result)
            if result["success"]:
                successful_runs += 1
    
    # Print summary
    print(f"\n🎯 Batch execution complete!")
    print(f"   Total experiments: {len(config_paths)}")
    print(f"   Successful: {successful_runs}")
    print(f"   Failed: {len(config_paths) - successful_runs}")
    print(f"   Total time: {batch_duration:.1f}s")
    print(f"   Average per experiment: {batch_duration/len(config_paths):.1f}s")
    
    return processed_results


def run_batch_sync(config_paths: List[str], max_concurrent: int = 3, output_dir: str = None, config_dir: str = "configs") -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for run_batch().
    
    Args:
        config_paths: List of configuration file paths or names
        max_concurrent: Maximum number of concurrent experiments
        output_dir: Optional custom output directory for experiment logs
        config_dir: Directory where configuration files are stored
    
    Returns:
        List of experiment results dictionaries
    """
    return asyncio.run(run_batch(config_paths, max_concurrent, output_dir, config_dir))




