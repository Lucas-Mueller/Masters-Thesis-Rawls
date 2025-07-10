"""
Multi-Agent Distributive Justice Experiment Framework

A sophisticated framework for conducting automated experiments on distributive justice
using autonomous AI agents. This system simulates Rawls' "veil of ignorance" scenario.
"""

__version__ = "2.0.0"
__author__ = "MAAI Research Team"

from .core.models import ExperimentConfig, ExperimentResults
from .core.deliberation_manager import run_single_experiment
from .config.manager import PresetConfigs, load_config_from_file

__all__ = [
    "ExperimentConfig",
    "ExperimentResults", 
    "run_single_experiment",
    "PresetConfigs",
    "load_config_from_file"
]