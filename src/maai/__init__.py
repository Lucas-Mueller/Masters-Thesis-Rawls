"""
Multi-Agent Distributive Justice Experiment Framework

A sophisticated framework for conducting automated experiments on distributive justice
using autonomous AI agents. This system simulates Rawls' "veil of ignorance" scenario.
"""

__version__ = "2.0.0"
__author__ = "MAAI Research Team"

from .core.models import ExperimentConfig, ExperimentResults
from .config.manager import load_config_from_file
from .services.experiment_orchestrator import ExperimentOrchestrator

__all__ = [
    "ExperimentConfig",
    "ExperimentResults",
    "ExperimentOrchestrator",
    "load_config_from_file"
]