"""
DEPRECATED: Backward compatibility wrapper for run_experiment.py
Use 'from maai.runners import run_experiment' instead.
"""

import sys
import os
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new location
from maai.runners import run_experiment, run_experiment_sync

# Re-export for backward compatibility
__all__ = ["run_experiment", "run_experiment_sync"]

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a single experiment")
    parser.add_argument("config", help="Configuration name or path")
    parser.add_argument("--output-dir", help="Custom output directory")
    parser.add_argument("--config-dir", default="configs", help="Configuration directory")
    
    args = parser.parse_args()
    
    result = run_experiment_sync(args.config, args.output_dir, args.config_dir)
    
    if result["success"]:
        print(f"✅ SUCCESS: {result['experiment_id']}")
        print(f"Output saved to: {result['output_path']}")
    else:
        print(f"❌ FAILED: {result['error']}")
        sys.exit(1)