"""
Enhanced data export system with multiple formats for experimental results.
Supports JSON, CSV, and human-readable text formats.
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from models import ExperimentResults, DeliberationResponse, FeedbackResponse


class DataExporter:
    """
    Handles exporting experiment results in multiple formats.
    """
    
    def __init__(self, output_dir: str = "experiment_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_all_formats(self, results: ExperimentResults) -> Dict[str, str]:
        """
        Export results in all available formats.
        
        Returns:
            Dictionary mapping format names to file paths
        """
        exported_files = {}
        
        # JSON export
        json_path = self.export_json(results)
        exported_files["json"] = str(json_path)
        
        # CSV exports
        csv_paths = self.export_csv(results)
        exported_files.update(csv_paths)
        
        # Text transcript
        txt_path = self.export_transcript(results)
        exported_files["transcript"] = str(txt_path)
        
        # Summary report
        summary_path = self.export_summary(results)
        exported_files["summary"] = str(summary_path)
        
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
    
    def export_csv(self, results: ExperimentResults) -> Dict[str, str]:
        """Export results as multiple CSV files."""
        csv_files = {}
        
        # 1. Main experiment summary CSV
        summary_path = self._export_experiment_summary_csv(results)
        csv_files["experiment_summary"] = str(summary_path)
        
        # 2. Deliberation transcript CSV
        transcript_path = self._export_transcript_csv(results)
        csv_files["deliberation_transcript"] = str(transcript_path)
        
        # 3. Feedback responses CSV
        if results.feedback_responses:
            feedback_path = self._export_feedback_csv(results)
            csv_files["feedback_responses"] = str(feedback_path)
        
        # 4. Agent choice evolution CSV
        evolution_path = self._export_choice_evolution_csv(results)
        csv_files["choice_evolution"] = str(evolution_path)
        
        return csv_files
    
    def _export_experiment_summary_csv(self, results: ExperimentResults) -> Path:
        """Export experiment summary as CSV."""
        filename = f"{results.experiment_id}_summary.csv"
        filepath = self.output_dir / filename
        
        summary_data = [
            ["Field", "Value"],
            ["Experiment ID", results.experiment_id],
            ["Start Time", results.start_time.isoformat() if results.start_time else ""],
            ["End Time", results.end_time.isoformat() if results.end_time else ""],
            ["Duration (seconds)", f"{results.performance_metrics.total_duration_seconds:.2f}"],
            ["Number of Agents", results.configuration.num_agents],
            ["Max Rounds", results.configuration.max_rounds],
            ["Decision Rule", results.configuration.decision_rule],
            ["Consensus Reached", "Yes" if results.consensus_result.unanimous else "No"],
            ["Rounds to Consensus", results.consensus_result.rounds_to_consensus],
            ["Total Messages", results.consensus_result.total_messages],
            ["Average Round Duration", f"{results.performance_metrics.average_round_duration:.2f}"],
            ["Errors Encountered", results.performance_metrics.errors_encountered],
        ]
        
        if results.consensus_result.unanimous and results.consensus_result.agreed_principle:
            summary_data.extend([
                ["Agreed Principle ID", results.consensus_result.agreed_principle.principle_id],
                ["Agreed Principle Name", results.consensus_result.agreed_principle.principle_name],
                ["Agreement Confidence", f"{results.consensus_result.agreed_principle.confidence:.2%}"],
            ])
        else:
            summary_data.extend([
                ["Dissenting Agents", "; ".join(results.consensus_result.dissenting_agents)],
            ])
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(summary_data)
        
        return filepath
    
    def _export_transcript_csv(self, results: ExperimentResults) -> Path:
        """Export deliberation transcript as CSV."""
        filename = f"{results.experiment_id}_transcript.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Round", "Agent_ID", "Agent_Name", "Principle_Choice", 
                "Principle_Name", "Confidence", "Message", "Timestamp"
            ])
            
            # Data rows
            for response in results.deliberation_transcript:
                writer.writerow([
                    response.round_number,
                    response.agent_id,
                    response.agent_name,
                    response.updated_choice.principle_id,
                    response.updated_choice.principle_name,
                    f"{response.updated_choice.confidence:.2%}",
                    response.message.replace('\n', ' ').replace('\r', ''),  # Clean newlines
                    response.timestamp.isoformat()
                ])
        
        return filepath
    
    def _export_feedback_csv(self, results: ExperimentResults) -> Path:
        """Export feedback responses as CSV."""
        filename = f"{results.experiment_id}_feedback.csv"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Agent_ID", "Agent_Name", "Satisfaction_Rating", "Fairness_Rating",
                "Would_Choose_Again", "Alternative_Preference", "Confidence", 
                "Reasoning", "Timestamp"
            ])
            
            # Data rows
            for feedback in results.feedback_responses:
                writer.writerow([
                    feedback.agent_id,
                    feedback.agent_name,
                    feedback.satisfaction_rating,
                    feedback.fairness_rating,
                    "Yes" if feedback.would_choose_again else "No",
                    feedback.alternative_preference or "",
                    f"{feedback.confidence_in_feedback:.2%}",
                    feedback.reasoning.replace('\n', ' ').replace('\r', ''),
                    feedback.timestamp.isoformat()
                ])
        
        return filepath
    
    def _export_choice_evolution_csv(self, results: ExperimentResults) -> Path:
        """Export agent choice evolution as CSV."""
        filename = f"{results.experiment_id}_choice_evolution.csv"
        filepath = self.output_dir / filename
        
        # Group responses by round and agent
        rounds = {}
        agents = set()
        
        for response in results.deliberation_transcript:
            round_num = response.round_number
            agent_id = response.agent_id
            
            if round_num not in rounds:
                rounds[round_num] = {}
            rounds[round_num][agent_id] = response.updated_choice.principle_id
            agents.add(agent_id)
        
        agents = sorted(list(agents))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            header = ["Round"] + [f"Agent_{agent_id}" for agent_id in agents]
            writer.writerow(header)
            
            # Data rows
            for round_num in sorted(rounds.keys()):
                row = [f"Round {round_num}" if round_num > 0 else "Initial"]
                for agent_id in agents:
                    choice = rounds[round_num].get(agent_id, "")
                    row.append(choice)
                writer.writerow(row)
        
        return filepath
    
    def export_transcript(self, results: ExperimentResults) -> Path:
        """Export human-readable transcript."""
        filename = f"{results.experiment_id}_transcript.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"EXPERIMENT TRANSCRIPT: {results.experiment_id}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Start Time: {results.start_time}\n")
            f.write(f"End Time: {results.end_time}\n")
            f.write(f"Duration: {results.performance_metrics.total_duration_seconds:.2f} seconds\n")
            f.write(f"Agents: {results.configuration.num_agents}\n")
            f.write(f"Decision Rule: {results.configuration.decision_rule}\n\n")
            
            # Group messages by round
            rounds = {}
            for response in results.deliberation_transcript:
                round_num = response.round_number
                if round_num not in rounds:
                    rounds[round_num] = []
                rounds[round_num].append(response)
            
            # Write transcript by round
            for round_num in sorted(rounds.keys()):
                round_name = "INITIAL EVALUATION" if round_num == 0 else f"ROUND {round_num}"
                f.write(f"\n{round_name}\n")
                f.write("-" * 60 + "\n")
                
                responses = rounds[round_num]
                choices = [r.updated_choice.principle_id for r in responses]
                f.write(f"Choices: {choices}\n\n")
                
                for response in responses:
                    f.write(f"{response.agent_name} (Principle {response.updated_choice.principle_id}):\n")
                    f.write(f"{response.message}\n\n")
            
            # Final result
            f.write("\n" + "=" * 80 + "\n")
            f.write("FINAL RESULT\n")
            f.write("=" * 80 + "\n")
            
            if results.consensus_result.unanimous:
                principle = results.consensus_result.agreed_principle
                f.write(f"✓ UNANIMOUS AGREEMENT REACHED\n")
                f.write(f"Agreed Principle: {principle.principle_id} - {principle.principle_name}\n")
                f.write(f"Rounds to consensus: {results.consensus_result.rounds_to_consensus}\n")
            else:
                f.write(f"✗ NO CONSENSUS REACHED\n")
                f.write(f"Dissenting agents: {results.consensus_result.dissenting_agents}\n")
                f.write(f"Total rounds: {results.consensus_result.rounds_to_consensus}\n")
        
        return filepath
    
    def export_summary(self, results: ExperimentResults) -> Path:
        """Export executive summary report."""
        filename = f"{results.experiment_id}_summary.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("EXPERIMENT SUMMARY REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Experiment ID: {results.experiment_id}\n")
            f.write(f"Date: {results.start_time.strftime('%Y-%m-%d %H:%M:%S') if results.start_time else 'Unknown'}\n")
            f.write(f"Duration: {results.performance_metrics.total_duration_seconds:.1f} seconds\n\n")
            
            f.write("CONFIGURATION\n")
            f.write("-" * 20 + "\n")
            f.write(f"Agents: {results.configuration.num_agents}\n")
            f.write(f"Max Rounds: {results.configuration.max_rounds}\n")
            f.write(f"Decision Rule: {results.configuration.decision_rule}\n")
            f.write(f"Timeout: {results.configuration.timeout_seconds} seconds\n\n")
            
            f.write("RESULTS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Consensus Reached: {'YES' if results.consensus_result.unanimous else 'NO'}\n")
            f.write(f"Rounds Completed: {results.consensus_result.rounds_to_consensus}\n")
            f.write(f"Total Messages: {results.consensus_result.total_messages}\n")
            f.write(f"Average Round Duration: {results.performance_metrics.average_round_duration:.1f}s\n\n")
            
            if results.consensus_result.unanimous:
                principle = results.consensus_result.agreed_principle
                f.write(f"AGREED PRINCIPLE\n")
                f.write("-" * 20 + "\n")
                f.write(f"ID: {principle.principle_id}\n")
                f.write(f"Name: {principle.principle_name}\n")
                f.write(f"Confidence: {principle.confidence:.1%}\n\n")
            
            if results.feedback_responses:
                f.write("FEEDBACK SUMMARY\n")
                f.write("-" * 20 + "\n")
                
                avg_satisfaction = sum(fb.satisfaction_rating for fb in results.feedback_responses) / len(results.feedback_responses)
                avg_fairness = sum(fb.fairness_rating for fb in results.feedback_responses) / len(results.feedback_responses)
                would_choose_again_count = sum(1 for fb in results.feedback_responses if fb.would_choose_again)
                
                f.write(f"Average Satisfaction: {avg_satisfaction:.1f}/10\n")
                f.write(f"Average Fairness Rating: {avg_fairness:.1f}/10\n")
                f.write(f"Would Choose Again: {would_choose_again_count}/{len(results.feedback_responses)} agents\n\n")
            
            f.write("PERFORMANCE\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Duration: {results.performance_metrics.total_duration_seconds:.2f}s\n")
            f.write(f"API Calls: {results.performance_metrics.api_calls_made}\n")
            f.write(f"Tokens Used: {results.performance_metrics.total_tokens_used}\n")
            f.write(f"Errors: {results.performance_metrics.errors_encountered}\n")
        
        return filepath


def export_experiment_data(results: ExperimentResults, output_dir: str = "experiment_results") -> Dict[str, str]:
    """
    Convenience function to export experiment results in all formats.
    
    Args:
        results: ExperimentResults object to export
        output_dir: Directory to save files in
    
    Returns:
        Dictionary mapping format names to file paths
    """
    exporter = DataExporter(output_dir)
    return exporter.export_all_formats(results)