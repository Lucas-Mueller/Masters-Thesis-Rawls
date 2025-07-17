"""
Simplified batch experiment runner - runs multiple experiments in parallel.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
from run_experiment import run_experiment


async def run_batch(config_paths: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """
    Run multiple experiments in parallel.
    
    Args:
        config_paths: List of configuration file paths or names
        max_concurrent: Maximum number of concurrent experiments
    
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
            result = await run_experiment(config_path)
            duration = time.time() - start_time
            
            # Add timing info
            result["batch_duration_seconds"] = duration
            result["batch_index"] = index
            
            if result["success"]:
                print(f"✅ [{index+1}/{len(config_paths)}] SUCCESS: {result['experiment_id']} ({duration:.1f}s)")
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


def run_batch_sync(config_paths: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for run_batch().
    
    Args:
        config_paths: List of configuration file paths or names
        max_concurrent: Maximum number of concurrent experiments
    
    Returns:
        List of experiment results dictionaries
    """
    return asyncio.run(run_batch(config_paths, max_concurrent))


def run_test_batch(count: int = 3, max_concurrent: int = 2) -> List[Dict[str, Any]]:
    """
    Run a test batch with the specified number of test configurations.
    
    Args:
        count: Number of test experiments to run
        max_concurrent: Maximum concurrent experiments
    
    Returns:
        List of experiment results
    """
    
    # Create simple test configurations
    test_configs = []
    for i in range(count):
        test_configs.append(f"test_config_{i+1}")
    
    print(f"🧪 Running test batch with {count} experiments")
    return run_batch_sync(test_configs, max_concurrent)


if __name__ == "__main__":
    # Simple CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multiple experiments in parallel")
    parser.add_argument("configs", nargs="+", help="Configuration file paths or names")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Maximum concurrent experiments")
    parser.add_argument("--test", action="store_true", help="Run test batch instead")
    parser.add_argument("--test-count", type=int, default=3, help="Number of test experiments")
    
    args = parser.parse_args()
    
    if args.test:
        results = run_test_batch(args.test_count, args.max_concurrent)
    else:
        results = run_batch_sync(args.configs, args.max_concurrent)
    
    # Simple summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"\n📊 Final Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success rate: {successful/len(results)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ Failed experiments:")
        for result in results:
            if not result["success"]:
                print(f"   - {result['experiment_id']}: {result['error']}")