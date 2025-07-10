#!/usr/bin/env python3
"""
Quick demo script for new users.
This is the easiest way to test the MAAI framework.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the demo
if __name__ == "__main__":
    import asyncio
    from demos.demo_phase2 import main
    
    print("🎯 Welcome to the Multi-Agent Distributive Justice Experiment!")
    print("Running quick demonstration...")
    print()
    
    asyncio.run(main())