"""
Simplified experiment runner - runs a single experiment with a given configuration.
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Initialize environment
load_dotenv()

# Import core modules
from maai.config.manager import load_config_from_file
from maai.core.deliberation_manager import run_single_experiment


async def run_experiment(config_path: str) -> Dict[str, Any]:
    """
    Run a single experiment with the given configuration.
    
    Args:
        config_path: Path to YAML configuration file (e.g., "configs/test.yaml") 
                    or just the config name (e.g., "test")
    
    Returns:
        Dict with experiment results:
        {
            "success": bool,
            "experiment_id": str,
            "consensus_reached": bool,
            "duration_seconds": float,
            "agreed_principle": str or None,
            "rounds_to_consensus": int,
            "total_messages": int,
            "error": str (if success=False)
        }
    """
    
    try:
        # Load configuration
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            config_name = Path(config_path).stem
        else:
            config_name = config_path
            
        config = load_config_from_file(config_name)
        
        # Run experiment
        results = await run_single_experiment(config)
        
        # Return simplified results
        return {
            "success": True,
            "experiment_id": config.experiment_id,
            "consensus_reached": results.consensus_result.unanimous,
            "duration_seconds": results.performance_metrics.total_duration_seconds,
            "agreed_principle": results.consensus_result.agreed_principle if results.consensus_result.unanimous else None,
            "rounds_to_consensus": results.consensus_result.rounds_to_consensus,
            "total_messages": len(results.deliberation_transcript),
            "results": results  # Keep full results for advanced users
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "experiment_id": config_path,
            "consensus_reached": False,
            "duration_seconds": 0.0,
            "agreed_principle": None,
            "rounds_to_consensus": 0,
            "total_messages": 0,
            "results": None
        }


def run_experiment_sync(config_path: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for run_experiment().
    
    Args:
        config_path: Path to YAML configuration file or config name
    
    Returns:
        Dict with experiment results
    """
    return asyncio.run(run_experiment(config_path))


if __name__ == "__main__":
    # Simple CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a single experiment")
    parser.add_argument("config", help="Configuration file path or name")
    args = parser.parse_args()
    
    result = run_experiment_sync(args.config)
    
    if result["success"]:
        print(f"✅ Experiment '{result['experiment_id']}' completed successfully!")
        print(f"   Consensus: {'YES' if result['consensus_reached'] else 'NO'}")
        print(f"   Duration: {result['duration_seconds']:.1f}s")
        print(f"   Rounds: {result['rounds_to_consensus']}")
        print(f"   Messages: {result['total_messages']}")
        if result['agreed_principle']:
            print(f"   Agreed Principle: {result['agreed_principle']}")
    else:
        print(f"❌ Experiment failed: {result['error']}")
        sys.exit(1)