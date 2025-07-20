"""
Tests for run_experiment.py
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import yaml
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maai.runners import run_experiment, run_experiment_sync
from config_generator import create_test_generator


class TestRunExperiment:
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create a configs directory
        self.config_dir = self.temp_path / "configs"
        self.config_dir.mkdir()
        
        # Change to temp directory
        import os
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test."""
        import os
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_run_experiment_with_config_name(self):
        """Test running experiment with just config name."""
        
        # Create test configuration
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("test_experiment.yaml", "test_experiment")
        
        # Mock the core experiment function
        with patch('run_experiment.run_single_experiment') as mock_run:
            # Mock the config loading
            with patch('run_experiment.load_config_from_file') as mock_load:
                # Create mock config object
                mock_config = MagicMock()
                mock_config.experiment_id = "test_experiment"
                mock_load.return_value = mock_config
                
                # Create mock results
                mock_results = MagicMock()
                mock_results.consensus_result.unanimous = True
                mock_results.consensus_result.agreed_principle = "principle_1"
                mock_results.consensus_result.rounds_to_consensus = 2
                mock_results.performance_metrics.total_duration_seconds = 45.5
                mock_results.deliberation_transcript = ["msg1", "msg2", "msg3"]
                
                mock_run.return_value = mock_results
                
                # Test the function
                result = run_experiment_sync("test_experiment")
                
                # Verify results
                assert result["success"] is True
                assert result["experiment_id"] == "test_experiment"
                assert result["consensus_reached"] is True
                assert result["agreed_principle"] == "principle_1"
                assert result["rounds_to_consensus"] == 2
                assert result["duration_seconds"] == 45.5
                assert result["total_messages"] == 3
                assert result["results"] == mock_results
    
    def test_run_experiment_with_config_path(self):
        """Test running experiment with full config path."""
        
        # Create test configuration
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("test_path.yaml", "test_path")
        
        # Mock the core experiment function
        with patch('run_experiment.run_single_experiment') as mock_run:
            # Mock the config loading
            with patch('run_experiment.load_config_from_file') as mock_load:
                # Create mock config object
                mock_config = MagicMock()
                mock_config.experiment_id = "test_path"
                mock_load.return_value = mock_config
                
                # Create mock results
                mock_results = MagicMock()
                mock_results.consensus_result.unanimous = False
                mock_results.consensus_result.agreed_principle = None
                mock_results.consensus_result.rounds_to_consensus = 3
                mock_results.performance_metrics.total_duration_seconds = 75.2
                mock_results.deliberation_transcript = ["msg1", "msg2"]
                
                mock_run.return_value = mock_results
                
                # Test with full path
                result = run_experiment_sync(config_path)
                
                # Verify results
                assert result["success"] is True
                assert result["experiment_id"] == "test_path"
                assert result["consensus_reached"] is False
                assert result["agreed_principle"] is None
                assert result["rounds_to_consensus"] == 3
                assert result["duration_seconds"] == 75.2
                assert result["total_messages"] == 2
    
    def test_run_experiment_error_handling(self):
        """Test error handling when experiment fails."""
        
        # Mock the core experiment function to raise an exception
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                mock_run.side_effect = Exception("Test error")
                
                # Test the function
                result = run_experiment_sync("test_error")
                
                # Verify error handling
                assert result["success"] is False
                assert result["error"] == "Test error"
                assert result["experiment_id"] == "test_error"
                assert result["consensus_reached"] is False
                assert result["duration_seconds"] == 0.0
                assert result["agreed_principle"] is None
                assert result["rounds_to_consensus"] == 0
                assert result["total_messages"] == 0
                assert result["results"] is None
    
    def test_run_experiment_async(self):
        """Test async version of run_experiment."""
        
        # Create test configuration
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("test_async.yaml", "test_async")
        
        async def test_async_run():
            # Mock the core experiment function
            with patch('run_experiment.run_single_experiment') as mock_run:
                with patch('run_experiment.load_config_from_file') as mock_load:
                    # Create mock config object
                    mock_config = MagicMock()
                    mock_config.experiment_id = "test_async"
                    mock_load.return_value = mock_config
                    
                    # Create mock results
                    mock_results = MagicMock()
                    mock_results.consensus_result.unanimous = True
                    mock_results.consensus_result.agreed_principle = "principle_2"
                    mock_results.consensus_result.rounds_to_consensus = 1
                    mock_results.performance_metrics.total_duration_seconds = 30.0
                    mock_results.deliberation_transcript = ["msg1"]
                    
                    mock_run.return_value = mock_results
                    
                    # Test async function
                    result = await run_experiment("test_async")
                    
                    # Verify results
                    assert result["success"] is True
                    assert result["experiment_id"] == "test_async"
                    assert result["consensus_reached"] is True
                    assert result["agreed_principle"] == "principle_2"
                    assert result["rounds_to_consensus"] == 1
                    assert result["duration_seconds"] == 30.0
                    assert result["total_messages"] == 1
        
        # Run async test
        asyncio.run(test_async_run())
    
    def test_config_name_extraction(self):
        """Test that config names are extracted correctly from paths."""
        
        # Mock the core functions
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                # Create mock config object
                mock_config = MagicMock()
                mock_config.experiment_id = "test_name"
                mock_load.return_value = mock_config
                
                # Create mock results
                mock_results = MagicMock()
                mock_results.consensus_result.unanimous = True
                mock_results.consensus_result.agreed_principle = "principle_1"
                mock_results.consensus_result.rounds_to_consensus = 2
                mock_results.performance_metrics.total_duration_seconds = 45.5
                mock_results.deliberation_transcript = ["msg1", "msg2"]
                
                mock_run.return_value = mock_results
                
                # Test different path formats
                test_paths = [
                    "test_name.yaml",
                    "configs/test_name.yaml",
                    "/full/path/to/test_name.yaml",
                    "test_name.yml"
                ]
                
                for path in test_paths:
                    result = run_experiment_sync(path)
                    assert result["success"] is True
                    
                    # Verify that load_config_from_file was called with just the name
                    mock_load.assert_called_with("test_name")
    
    def test_result_structure(self):
        """Test that result dictionary has correct structure."""
        
        # Create test configuration
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("test_structure.yaml", "test_structure")
        
        # Mock the core experiment function
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                # Create mock config object
                mock_config = MagicMock()
                mock_config.experiment_id = "test_structure"
                mock_load.return_value = mock_config
                
                # Create mock results
                mock_results = MagicMock()
                mock_results.consensus_result.unanimous = True
                mock_results.consensus_result.agreed_principle = "principle_1"
                mock_results.consensus_result.rounds_to_consensus = 2
                mock_results.performance_metrics.total_duration_seconds = 45.5
                mock_results.deliberation_transcript = ["msg1", "msg2"]
                
                mock_run.return_value = mock_results
                
                # Test the function
                result = run_experiment_sync("test_structure")
                
                # Verify all required fields are present
                required_fields = [
                    "success", "experiment_id", "consensus_reached", 
                    "duration_seconds", "agreed_principle", "rounds_to_consensus",
                    "total_messages", "results"
                ]
                
                for field in required_fields:
                    assert field in result
                
                # Verify field types
                assert isinstance(result["success"], bool)
                assert isinstance(result["experiment_id"], str)
                assert isinstance(result["consensus_reached"], bool)
                assert isinstance(result["duration_seconds"], float)
                assert isinstance(result["rounds_to_consensus"], int)
                assert isinstance(result["total_messages"], int)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])