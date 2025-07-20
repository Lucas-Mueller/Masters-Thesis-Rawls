"""
Single experiment runner - runs one experiment with a given configuration.
"""

from typing import Dict, Any

from ..config.manager import load_config_from_file
from ..core.deliberation_manager import run_single_experiment
from .common import create_error_result, normalize_config_path, run_async_function_sync


async def run_experiment(config_path: str, output_dir: str = None, config_dir: str = "configs") -> Dict[str, Any]:
    """
    Run a single experiment with the given configuration.
    
    Args:
        config_path: Path to YAML configuration file (e.g., "configs/test.yaml") 
                    or just the config name (e.g., "test")
        output_dir: Optional custom output directory for experiment logs. 
                   Defaults to "experiment_results" if not specified.
        config_dir: Directory where configuration files are stored.
                   Defaults to "configs" if not specified.
    
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
            "error": str (if success=False),
            "output_path": str (path to saved JSON file)
        }
    """
    
    try:
        # Load configuration
        config_name = normalize_config_path(config_path)
            
        config = load_config_from_file(config_name, config_dir=config_dir)
        
        # Override output directory if specified
        if output_dir is not None:
            config.output.directory = output_dir
        
        # Run experiment
        results = await run_single_experiment(config)
        
        # Determine output path
        output_path = f"{config.output.directory}/{config.experiment_id}.json"
        
        # Return simplified results
        return {
            "success": True,
            "experiment_id": config.experiment_id,
            "consensus_reached": results.consensus_result.unanimous,
            "duration_seconds": results.performance_metrics.total_duration_seconds,
            "agreed_principle": results.consensus_result.agreed_principle if results.consensus_result.unanimous else None,
            "rounds_to_consensus": results.consensus_result.rounds_to_consensus,
            "total_messages": len(results.deliberation_transcript),
            "results": results,  # Keep full results for advanced users
            "output_path": output_path  # Path to the saved JSON file
        }
        
    except Exception as e:
        return create_error_result(config_path, e)


def run_experiment_sync(config_path: str, output_dir: str = None, config_dir: str = "configs") -> Dict[str, Any]:
    """
    Synchronous wrapper for run_experiment().
    
    Args:
        config_path: Path to YAML configuration file or config name
        output_dir: Optional custom output directory for experiment logs
        config_dir: Directory where configuration files are stored
    
    Returns:
        Dict with experiment results
    """
    return run_async_function_sync(run_experiment, config_path, output_dir, config_dir)