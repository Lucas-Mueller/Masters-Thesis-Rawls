"""
Test script for Phase 2 enhanced logging and data export functionality.
"""

import asyncio
import os
import json
import csv
import uuid
from pathlib import Path
from datetime import datetime

from models import ExperimentConfig
from deliberation_manager import run_single_experiment
from data_export import DataExporter, export_experiment_data


async def test_data_export():
    """Test the enhanced data export system."""
    print("=== Testing Enhanced Data Export System ===\n")
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Please set OPENAI_API_KEY environment variable")
        return False
    
    # Create a test experiment
    config = ExperimentConfig(
        experiment_id=f"export_test_{uuid.uuid4().hex[:8]}",
        num_agents=3,
        max_rounds=2,
        decision_rule="unanimity",
        timeout_seconds=120
    )
    
    print(f"Running experiment: {config.experiment_id}")
    
    try:
        # Run the experiment
        results = await run_single_experiment(config)
        
        print(f"\n--- Testing Data Export ---")
        
        # Test the export functionality
        output_dir = f"test_exports_{config.experiment_id}"
        exported_files = export_experiment_data(results, output_dir)
        
        print(f"Exported files:")
        for format_name, filepath in exported_files.items():
            print(f"  {format_name}: {filepath}")
        
        # Validate exported files exist and have content
        validation_results = {}
        
        # Test JSON export
        if "json" in exported_files:
            json_path = Path(exported_files["json"])
            if json_path.exists():
                with open(json_path, 'r') as f:
                    json_data = json.load(f)
                    validation_results["json"] = len(json_data) > 0
                    print(f"  ✓ JSON file contains {len(json_data)} top-level keys")
            else:
                validation_results["json"] = False
                print(f"  ✗ JSON file not found")
        
        # Test CSV exports
        csv_formats = ["experiment_summary", "deliberation_transcript", "feedback_responses", "choice_evolution"]
        for csv_format in csv_formats:
            if csv_format in exported_files:
                csv_path = Path(exported_files[csv_format])
                if csv_path.exists():
                    with open(csv_path, 'r') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        validation_results[csv_format] = len(rows) > 1  # Header + data
                        print(f"  ✓ {csv_format} CSV contains {len(rows)} rows")
                else:
                    validation_results[csv_format] = False
                    print(f"  ✗ {csv_format} CSV not found")
        
        # Test text exports
        text_formats = ["transcript", "summary"]
        for text_format in text_formats:
            if text_format in exported_files:
                txt_path = Path(exported_files[text_format])
                if txt_path.exists():
                    content = txt_path.read_text()
                    validation_results[text_format] = len(content) > 100  # Reasonable content
                    print(f"  ✓ {text_format} text contains {len(content)} characters")
                else:
                    validation_results[text_format] = False
                    print(f"  ✗ {text_format} text not found")
        
        # Clean up test files
        print(f"\n--- Cleaning Up Test Files ---")
        import shutil
        if Path(output_dir).exists():
            shutil.rmtree(output_dir)
            print(f"  Removed test directory: {output_dir}")
        
        # Check validation results
        failed_exports = [fmt for fmt, success in validation_results.items() if not success]
        if failed_exports:
            print(f"\n❌ Failed exports: {failed_exports}")
            return False
        else:
            print(f"\n✅ All {len(validation_results)} export formats validated successfully!")
            return True
        
    except Exception as e:
        print(f"❌ Data export test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_export_formats():
    """Test different export format structures."""
    print("\n=== Testing Export Format Structures ===\n")
    
    try:
        # Create a minimal mock experiment result for testing
        from models import (
            ExperimentResults, ExperimentConfig, ConsensusResult, 
            PerformanceMetrics, DeliberationResponse, FeedbackResponse, PrincipleChoice
        )
        
        # Mock data
        config = ExperimentConfig(
            experiment_id="format_test",
            num_agents=3,
            max_rounds=1
        )
        
        principle_choice = PrincipleChoice(
            principle_id=3,
            principle_name="Test Principle",
            reasoning="Test reasoning",
            confidence=0.8
        )
        
        consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=principle_choice,
            dissenting_agents=[],
            rounds_to_consensus=1,
            total_messages=2
        )
        
        transcript = [
            DeliberationResponse(
                agent_id="agent_1",
                agent_name="Agent 1",
                message="Test message 1",
                updated_choice=principle_choice,
                round_number=0
            ),
            DeliberationResponse(
                agent_id="agent_2", 
                agent_name="Agent 2",
                message="Test message 2",
                updated_choice=principle_choice,
                round_number=0
            )
        ]
        
        feedback = [
            FeedbackResponse(
                agent_id="agent_1",
                agent_name="Agent 1",
                satisfaction_rating=8,
                fairness_rating=7,
                would_choose_again=True,
                alternative_preference=None,
                reasoning="Test feedback",
                confidence_in_feedback=0.9
            )
        ]
        
        metrics = PerformanceMetrics(
            total_duration_seconds=10.0,
            average_round_duration=10.0,
            total_tokens_used=100,
            api_calls_made=5,
            errors_encountered=0
        )
        
        mock_results = ExperimentResults(
            experiment_id="format_test",
            configuration=config,
            deliberation_transcript=transcript,
            consensus_result=consensus_result,
            feedback_responses=feedback,
            performance_metrics=metrics,
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        # Test export
        output_dir = "format_test_exports"
        exporter = DataExporter(output_dir)
        
        print("Testing individual export methods...")
        
        # Test JSON export
        json_path = exporter.export_json(mock_results)
        print(f"  ✓ JSON export: {json_path}")
        
        # Test CSV exports
        csv_paths = exporter.export_csv(mock_results)
        print(f"  ✓ CSV exports: {len(csv_paths)} files")
        for name, path in csv_paths.items():
            print(f"    - {name}: {Path(path).name}")
        
        # Test transcript export
        transcript_path = exporter.export_transcript(mock_results)
        print(f"  ✓ Transcript export: {transcript_path}")
        
        # Test summary export
        summary_path = exporter.export_summary(mock_results)
        print(f"  ✓ Summary export: {summary_path}")
        
        # Clean up
        import shutil
        if Path(output_dir).exists():
            shutil.rmtree(output_dir)
            print(f"  Cleaned up: {output_dir}")
        
        print(f"\n✅ All export format tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Export format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 2 logging tests."""
    print("Phase 2 Enhanced Logging Testing Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Export format structures
    print("Test 1: Export Format Structures")
    result1 = await test_export_formats()
    test_results.append(("Export Formats", result1))
    
    # Test 2: Full data export integration
    if os.environ.get("OPENAI_API_KEY"):
        print("\nTest 2: Full Data Export Integration")
        result2 = await test_data_export()
        test_results.append(("Data Export Integration", result2))
    else:
        print("\n⚠️  Skipping data export integration test (no API key)")
        test_results.append(("Data Export Integration", None))
    
    # Summary
    print("\n" + "=" * 60)
    print("PHASE 2 LOGGING TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⚠️  {test_name}: SKIPPED")
    
    passed = sum(1 for _, result in test_results if result is True)
    total = len([r for r in test_results if r[1] is not None])
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 logging tests passed!")
    else:
        print("🔧 Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    asyncio.run(main())