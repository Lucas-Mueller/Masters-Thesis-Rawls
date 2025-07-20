"""
DEPRECATED: Backward compatibility wrapper for run_batch.py
Use 'from maai.runners import run_batch' instead.
"""

import sys
import os
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import from new location
from maai.runners import run_batch, run_batch_sync

# Re-export for backward compatibility
__all__ = ["run_batch", "run_batch_sync"]

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run batch experiments")
    parser.add_argument("configs", nargs="+", help="Configuration names or paths")
    parser.add_argument("--max-concurrent", type=int, default=3, help="Maximum concurrent experiments")
    parser.add_argument("--output-dir", help="Custom output directory")
    parser.add_argument("--config-dir", default="configs", help="Configuration directory")
    
    args = parser.parse_args()
    
    results = run_batch_sync(args.configs, args.max_concurrent, args.output_dir, args.config_dir)
    
    successful = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"\n🎯 Batch completed: {successful}/{total} successful")
    
    if successful < total:
        sys.exit(1)