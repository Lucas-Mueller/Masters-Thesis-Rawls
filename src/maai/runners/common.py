"""
Common utilities for experiment runners.
"""

import asyncio
from typing import Dict, Any
from pathlib import Path


def create_error_result(config_path: str, error: Exception, batch_index: int = None) -> Dict[str, Any]:
    """
    Create a standardized error result dictionary.
    
    Args:
        config_path: Configuration path that failed
        error: Exception that occurred
        batch_index: Optional batch index for batch operations
        
    Returns:
        Standardized error result dictionary
    """
    result = {
        "success": False,
        "error": str(error),
        "experiment_id": config_path,
        "consensus_reached": False,
        "duration_seconds": 0.0,
        "agreed_principle": None,
        "rounds_to_consensus": 0,
        "total_messages": 0,
        "results": None,
        "output_path": None
    }
    
    if batch_index is not None:
        result.update({
            "batch_duration_seconds": 0.0,
            "batch_index": batch_index
        })
    
    return result


def normalize_config_path(config_path: str) -> str:
    """
    Normalize configuration path to extract config name.
    
    Args:
        config_path: Path to YAML configuration file or config name
        
    Returns:
        Configuration name without extension
    """
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        return Path(config_path).stem
    return config_path


def run_async_function_sync(async_func, *args, **kwargs):
    """
    Synchronous wrapper for async functions.
    
    Args:
        async_func: Async function to run
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the async function
    """
    return asyncio.run(async_func(*args, **kwargs))