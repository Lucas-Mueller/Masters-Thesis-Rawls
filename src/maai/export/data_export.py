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
        
        # Initial evaluation CSV export (if initial data exists)
        if results.initial_evaluation_responses:
            initial_csv_path = self.export_initial_evaluation_csv(results)
            exported_files["initial_evaluation_csv"] = str(initial_csv_path)
            
            initial_json_path = self.export_initial_evaluation_json(results)
            exported_files["initial_evaluation_json"] = str(initial_json_path)
        
        # Final evaluation CSV export (if evaluation data exists)
        if results.evaluation_responses:
            eval_csv_path = self.export_evaluation_csv(results)
            exported_files["evaluation_csv"] = str(eval_csv_path)
            
            eval_json_path = self.export_evaluation_json(results)
            exported_files["evaluation_json"] = str(eval_json_path)
        
        # Comparison export (if both initial and final data exist)
        if results.initial_evaluation_responses and results.evaluation_responses:
            comparison_csv_path = self.export_comparison_csv(results)
            exported_files["comparison_csv"] = str(comparison_csv_path)
        
        return exported_files
    
    def export_json(self, results: ExperimentResults) -> Path:
        """Export complete results as JSON."""
        filename = f"{results.experiment_id}_complete.json"
        filepath = self.output_dir / filename
        
        # Convert to dict and handle datetime serialization
        results_dict = results.model_dump()
        
        # Custom JSON encoder for datetime objects and LitellmModel objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle LitellmModel objects by converting to string representation
            if hasattr(obj, '__class__') and 'LitellmModel' in str(type(obj)):
                return str(obj)
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
    
    def export_evaluation_csv(self, results: ExperimentResults) -> Path:
        """Export evaluation data as CSV for analysis."""
        filename = f"{results.experiment_id}_evaluation.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Experiment_ID", "Agent_ID", "Agent_Name", "Principle_ID", "Principle_Name",
                "Satisfaction_Rating", "Satisfaction_Display", "Satisfaction_Numeric",
                "Reasoning", "Evaluation_Duration", "Timestamp", "Consensus_Reached",
                "Agreed_Principle_ID"
            ])
            
            # Data rows
            for response in results.evaluation_responses:
                for evaluation in response.principle_evaluations:
                    writer.writerow([
                        results.experiment_id,
                        response.agent_id,
                        response.agent_name,
                        evaluation.principle_id,
                        evaluation.principle_name,
                        evaluation.satisfaction_rating.value,
                        evaluation.satisfaction_rating.to_display(),
                        evaluation.satisfaction_rating.to_numeric(),
                        evaluation.reasoning.replace('\n', ' ').replace('\r', ''),
                        response.evaluation_duration,
                        response.timestamp.isoformat(),
                        results.consensus_result.unanimous,
                        results.consensus_result.agreed_principle.principle_id if results.consensus_result.agreed_principle else None
                    ])
        
        return filepath
    
    def export_evaluation_json(self, results: ExperimentResults) -> Path:
        """Export evaluation data as structured JSON."""
        filename = f"{results.experiment_id}_evaluation.json"
        filepath = self.output_dir / filename
        
        # Create structured evaluation data
        evaluation_data = {
            'experiment_id': results.experiment_id,
            'consensus_reached': results.consensus_result.unanimous,
            'agreed_principle_id': results.consensus_result.agreed_principle.principle_id if results.consensus_result.agreed_principle else None,
            'agreed_principle_name': results.consensus_result.agreed_principle.principle_name if results.consensus_result.agreed_principle else None,
            'evaluation_responses': [
                {
                    'agent_id': response.agent_id,
                    'agent_name': response.agent_name,
                    'principle_evaluations': [
                        {
                            'principle_id': eval.principle_id,
                            'principle_name': eval.principle_name,
                            'satisfaction_rating': eval.satisfaction_rating.value,
                            'satisfaction_display': eval.satisfaction_rating.to_display(),
                            'satisfaction_numeric': eval.satisfaction_rating.to_numeric(),
                            'reasoning': eval.reasoning,
                            'timestamp': eval.timestamp.isoformat()
                        }
                        for eval in response.principle_evaluations
                    ],
                    'overall_reasoning': response.overall_reasoning,
                    'evaluation_duration': response.evaluation_duration,
                    'timestamp': response.timestamp.isoformat()
                }
                for response in results.evaluation_responses
            ],
            'summary_statistics': self._calculate_evaluation_statistics(results.evaluation_responses)
        }
        
        # Custom JSON encoder for datetime objects and LitellmModel objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle LitellmModel objects by converting to string representation
            if hasattr(obj, '__class__') and 'LitellmModel' in str(type(obj)):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        return filepath
    
    def _calculate_evaluation_statistics(self, evaluation_responses) -> Dict:
        """Calculate summary statistics for evaluation responses."""
        if not evaluation_responses:
            return {}
        
        # Calculate statistics by principle
        principle_stats = {}
        for i in range(1, 5):
            ratings = []
            for response in evaluation_responses:
                for eval in response.principle_evaluations:
                    if eval.principle_id == i:
                        ratings.append(eval.satisfaction_rating.to_numeric())
            
            if ratings:
                principle_stats[f"principle_{i}"] = {
                    "average_rating": sum(ratings) / len(ratings),
                    "min_rating": min(ratings),
                    "max_rating": max(ratings),
                    "total_responses": len(ratings)
                }
        
        # Overall statistics
        all_ratings = []
        total_evaluation_time = 0
        for response in evaluation_responses:
            for eval in response.principle_evaluations:
                all_ratings.append(eval.satisfaction_rating.to_numeric())
            if response.evaluation_duration:
                total_evaluation_time += response.evaluation_duration
        
        overall_stats = {
            "overall_average_rating": sum(all_ratings) / len(all_ratings) if all_ratings else 0,
            "total_evaluations": len(all_ratings),
            "total_evaluation_time": total_evaluation_time,
            "average_evaluation_time": total_evaluation_time / len(evaluation_responses) if evaluation_responses else 0
        }
        
        return {
            "by_principle": principle_stats,
            "overall": overall_stats
        }
    
    def export_initial_evaluation_csv(self, results: ExperimentResults) -> Path:
        """Export initial evaluation data as CSV."""
        filename = f"{results.experiment_id}_initial_evaluation.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Experiment_ID", "Agent_ID", "Agent_Name", "Principle_ID", "Principle_Name",
                "Satisfaction_Rating", "Satisfaction_Display", "Satisfaction_Numeric",
                "Reasoning", "Evaluation_Duration", "Timestamp", "Phase"
            ])
            
            # Data rows
            for response in results.initial_evaluation_responses:
                for evaluation in response.principle_evaluations:
                    writer.writerow([
                        results.experiment_id,
                        response.agent_id,
                        response.agent_name,
                        evaluation.principle_id,
                        evaluation.principle_name,
                        evaluation.satisfaction_rating.value,
                        evaluation.satisfaction_rating.to_display(),
                        evaluation.satisfaction_rating.to_numeric(),
                        evaluation.reasoning.replace('\n', ' ').replace('\r', ''),
                        response.evaluation_duration,
                        response.timestamp.isoformat(),
                        "initial"
                    ])
        
        return filepath
    
    def export_initial_evaluation_json(self, results: ExperimentResults) -> Path:
        """Export initial evaluation data as structured JSON."""
        filename = f"{results.experiment_id}_initial_evaluation.json"
        filepath = self.output_dir / filename
        
        # Create structured evaluation data
        evaluation_data = {
            'experiment_id': results.experiment_id,
            'phase': 'initial',
            'evaluation_responses': [
                {
                    'agent_id': response.agent_id,
                    'agent_name': response.agent_name,
                    'principle_evaluations': [
                        {
                            'principle_id': eval.principle_id,
                            'principle_name': eval.principle_name,
                            'satisfaction_rating': eval.satisfaction_rating.value,
                            'satisfaction_display': eval.satisfaction_rating.to_display(),
                            'satisfaction_numeric': eval.satisfaction_rating.to_numeric(),
                            'reasoning': eval.reasoning,
                            'timestamp': eval.timestamp.isoformat()
                        }
                        for eval in response.principle_evaluations
                    ],
                    'overall_reasoning': response.overall_reasoning,
                    'evaluation_duration': response.evaluation_duration,
                    'timestamp': response.timestamp.isoformat()
                }
                for response in results.initial_evaluation_responses
            ],
            'summary_statistics': self._calculate_evaluation_statistics(results.initial_evaluation_responses)
        }
        
        # Custom JSON encoder for datetime objects and LitellmModel objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle LitellmModel objects by converting to string representation
            if hasattr(obj, '__class__') and 'LitellmModel' in str(type(obj)):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        return filepath
    
    def export_comparison_csv(self, results: ExperimentResults) -> Path:
        """Export comparison between initial and final evaluations."""
        filename = f"{results.experiment_id}_comparison.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Experiment_ID", "Agent_ID", "Agent_Name", "Principle_ID", "Principle_Name",
                "Initial_Rating", "Initial_Display", "Initial_Numeric",
                "Final_Rating", "Final_Display", "Final_Numeric",
                "Rating_Change", "Initial_Reasoning", "Final_Reasoning",
                "Consensus_Reached", "Agreed_Principle_ID"
            ])
            
            # Create mapping of agent responses
            initial_map = {}
            for response in results.initial_evaluation_responses:
                for eval in response.principle_evaluations:
                    key = (response.agent_id, eval.principle_id)
                    initial_map[key] = (eval, response)
            
            final_map = {}
            for response in results.evaluation_responses:
                for eval in response.principle_evaluations:
                    key = (response.agent_id, eval.principle_id)
                    final_map[key] = (eval, response)
            
            # Generate comparison rows
            for key in initial_map.keys():
                if key in final_map:
                    initial_eval, initial_response = initial_map[key]
                    final_eval, final_response = final_map[key]
                    
                    rating_change = final_eval.satisfaction_rating.to_numeric() - initial_eval.satisfaction_rating.to_numeric()
                    
                    writer.writerow([
                        results.experiment_id,
                        initial_response.agent_id,
                        initial_response.agent_name,
                        initial_eval.principle_id,
                        initial_eval.principle_name,
                        initial_eval.satisfaction_rating.value,
                        initial_eval.satisfaction_rating.to_display(),
                        initial_eval.satisfaction_rating.to_numeric(),
                        final_eval.satisfaction_rating.value,
                        final_eval.satisfaction_rating.to_display(),
                        final_eval.satisfaction_rating.to_numeric(),
                        rating_change,
                        initial_eval.reasoning.replace('\n', ' ').replace('\r', ''),
                        final_eval.reasoning.replace('\n', ' ').replace('\r', ''),
                        results.consensus_result.unanimous,
                        results.consensus_result.agreed_principle.principle_id if results.consensus_result.agreed_principle else None
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