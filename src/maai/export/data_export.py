"""
Simplified data export system with essential formats only.
Exports JSON (complete data) and CSV (for analysis).
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict
from pathlib import Path

from ..core.models import ExperimentResults


class DataExporter:
    """
    Simplified data exporter with essential formats only.
    """
    
    def __init__(self, output_dir: str = "experiment_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_all_formats(self, results: ExperimentResults) -> Dict[str, str]:
        """
        Export results in essential formats: JSON (complete) and CSV (analysis).
        
        Returns:
            Dictionary mapping format names to file paths
        """
        exported_files = {}
        
        # JSON export (complete data)
        json_path = self.export_json(results)
        exported_files["json"] = str(json_path)
        
        # Main CSV export (for analysis)
        csv_path = self.export_main_csv(results)
        exported_files["csv"] = str(csv_path)
        
        return exported_files
    
    def export_json(self, results: ExperimentResults) -> Path:
        """Export complete results as JSON."""
        filename = f"{results.experiment_id}_complete.json"
        filepath = self.output_dir / filename
        
        # Convert to dict and handle datetime serialization
        results_dict = results.model_dump()
        
        # Custom JSON encoder for datetime objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        return filepath
    
    def export_main_csv(self, results: ExperimentResults) -> Path:
        """Export main data as a single comprehensive CSV file."""
        filename = f"{results.experiment_id}_data.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Experiment_ID", "Round", "Agent_ID", "Agent_Name", "Speaking_Position",
                "Principle_Choice", "Principle_Name", "Public_Message", "Timestamp",
                "Consensus_Reached", "Duration_Seconds"
            ])
            
            # Data rows
            for response in results.deliberation_transcript:
                writer.writerow([
                    results.experiment_id,
                    response.round_number,
                    response.agent_id,
                    response.agent_name,
                    response.speaking_position,
                    response.updated_choice.principle_id,
                    response.updated_choice.principle_name,
                    response.public_message.replace('\n', ' ').replace('\r', ''),
                    response.timestamp.isoformat(),
                    results.consensus_result.unanimous,
                    results.performance_metrics.total_duration_seconds
                ])
        
        return filepath


def export_experiment_data(results: ExperimentResults, output_dir: str = "experiment_results") -> Dict[str, str]:
    """
    Convenience function to export experiment results in essential formats.
    
    Args:
        results: ExperimentResults object to export
        output_dir: Directory to save files in
    
    Returns:
        Dictionary mapping format names to file paths
    """
    exporter = DataExporter(output_dir)
    return exporter.export_all_formats(results)