"""
Integration tests for the simplified experiment system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config_generator import create_test_generator
from run_experiment import run_experiment_sync
from run_batch import run_batch_sync


class TestIntegration:
    
    def setup_method(self):
        """Setup test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create a configs directory
        self.config_dir = self.temp_path / "configs"
        self.config_dir.mkdir()
        
        # Change to temp directory
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_config_generation_and_loading(self):
        """Test that generated configs can be loaded and used."""
        
        # Generate a test config
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("integration_test.yaml", "integration_test")
        
        # Verify the config file exists
        assert Path(config_path).exists()
        
        # Load the config file and verify structure
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check structure
        assert config["experiment_id"] == "integration_test"
        assert len(config["agents"]) == 2
        assert config["experiment"]["max_rounds"] == 2
        assert all(agent["model"] == "gpt-4.1-nano" for agent in config["agents"])
    
    def test_end_to_end_workflow_mock(self):
        """Test complete workflow with mocked experiment execution."""
        
        # Step 1: Generate configs
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(2, "e2e")
        # Extract actual config names from the generated paths
        config_names = []
        for path in config_paths:
            from pathlib import Path
            filename = Path(path).stem  # Get filename without extension
            config_names.append(filename)
        
        # Verify configs were created
        assert len(config_paths) == 2
        for path in config_paths:
            assert Path(path).exists()
        
        # Step 2: Mock experiment execution and test batch run
        from unittest.mock import patch, MagicMock
        
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                
                # Create mock results for both experiments
                mock_results_1 = MagicMock()
                mock_results_1.consensus_result.unanimous = True
                mock_results_1.consensus_result.agreed_principle = "principle_1"
                mock_results_1.consensus_result.rounds_to_consensus = 2
                mock_results_1.performance_metrics.total_duration_seconds = 30.0
                mock_results_1.deliberation_transcript = ["msg1", "msg2"]
                
                mock_results_2 = MagicMock()
                mock_results_2.consensus_result.unanimous = False
                mock_results_2.consensus_result.agreed_principle = None
                mock_results_2.consensus_result.rounds_to_consensus = 2
                mock_results_2.performance_metrics.total_duration_seconds = 45.0
                mock_results_2.deliberation_transcript = ["msg1", "msg2", "msg3"]
                
                # Mock config loading
                def mock_load_config(config_name):
                    mock_config = MagicMock()
                    mock_config.experiment_id = config_name
                    return mock_config
                
                mock_load.side_effect = mock_load_config
                mock_run.side_effect = [mock_results_1, mock_results_2]
                
                # Step 3: Run batch experiment
                results = run_batch_sync(config_names, max_concurrent=2)
                
                # Step 4: Verify results
                assert len(results) == 2
                
                # Check first result
                assert results[0]["success"] is True
                assert results[0]["experiment_id"] == config_names[0]
                assert results[0]["consensus_reached"] is True
                assert results[0]["agreed_principle"] == "principle_1"
                assert results[0]["duration_seconds"] == 30.0
                assert results[0]["total_messages"] == 2
                
                # Check second result
                assert results[1]["success"] is True
                assert results[1]["experiment_id"] == config_names[1]
                assert results[1]["consensus_reached"] is False
                assert results[1]["agreed_principle"] is None
                assert results[1]["duration_seconds"] == 45.0
                assert results[1]["total_messages"] == 3
    
    def test_single_experiment_workflow_mock(self):
        """Test single experiment workflow with mocked execution."""
        
        # Step 1: Generate config
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("single_test.yaml", "single_test")
        
        # Step 2: Mock experiment execution
        from unittest.mock import patch, MagicMock
        
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                
                # Create mock config and results
                mock_config = MagicMock()
                mock_config.experiment_id = "single_test"
                mock_load.return_value = mock_config
                
                mock_results = MagicMock()
                mock_results.consensus_result.unanimous = True
                mock_results.consensus_result.agreed_principle = "principle_2"
                mock_results.consensus_result.rounds_to_consensus = 1
                mock_results.performance_metrics.total_duration_seconds = 25.0
                mock_results.deliberation_transcript = ["msg1"]
                
                mock_run.return_value = mock_results
                
                # Step 3: Run single experiment
                result = run_experiment_sync("single_test")
                
                # Step 4: Verify result
                assert result["success"] is True
                assert result["experiment_id"] == "single_test"
                assert result["consensus_reached"] is True
                assert result["agreed_principle"] == "principle_2"
                assert result["duration_seconds"] == 25.0
                assert result["total_messages"] == 1
    
    def test_error_handling_integration(self):
        """Test error handling throughout the workflow."""
        
        # Step 1: Generate config
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_path = generator.generate_and_save_config("error_test.yaml", "error_test")
        
        # Step 2: Mock experiment execution to fail
        from unittest.mock import patch, MagicMock
        
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                
                # Make the experiment fail
                mock_run.side_effect = Exception("Test integration error")
                
                # Step 3: Run experiment and verify error handling
                result = run_experiment_sync("error_test")
                
                # Step 4: Verify error result
                assert result["success"] is False
                assert "Test integration error" in result["error"]
                assert result["experiment_id"] == "error_test"
                assert result["consensus_reached"] is False
                assert result["duration_seconds"] == 0.0
    
    def test_batch_error_handling_integration(self):
        """Test batch error handling with mixed results."""
        
        # Step 1: Generate configs
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(3, "batch_error")
        # Extract actual config names from the generated paths
        config_names = []
        for path in config_paths:
            from pathlib import Path
            filename = Path(path).stem  # Get filename without extension
            config_names.append(filename)
        
        # Step 2: Mock experiment execution with mixed results
        from unittest.mock import patch, MagicMock
        
        with patch('run_experiment.run_single_experiment') as mock_run:
            with patch('run_experiment.load_config_from_file') as mock_load:
                
                # Create mock config loading
                def mock_load_config(config_name):
                    mock_config = MagicMock()
                    mock_config.experiment_id = config_name
                    return mock_config
                
                mock_load.side_effect = mock_load_config
                
                # Create mixed results: success, failure, success
                mock_results_1 = MagicMock()
                mock_results_1.consensus_result.unanimous = True
                mock_results_1.consensus_result.agreed_principle = "principle_1"
                mock_results_1.consensus_result.rounds_to_consensus = 2
                mock_results_1.performance_metrics.total_duration_seconds = 30.0
                mock_results_1.deliberation_transcript = ["msg1", "msg2"]
                
                mock_results_3 = MagicMock()
                mock_results_3.consensus_result.unanimous = False
                mock_results_3.consensus_result.agreed_principle = None
                mock_results_3.consensus_result.rounds_to_consensus = 2
                mock_results_3.performance_metrics.total_duration_seconds = 40.0
                mock_results_3.deliberation_transcript = ["msg1", "msg2", "msg3"]
                
                def mock_run_side_effect(*args, **kwargs):
                    call_count = mock_run_side_effect.call_count
                    mock_run_side_effect.call_count += 1
                    
                    if call_count == 0:
                        return mock_results_1
                    elif call_count == 1:
                        raise Exception("Test batch error")
                    else:
                        return mock_results_3
                
                mock_run_side_effect.call_count = 0
                mock_run.side_effect = mock_run_side_effect
                
                # Step 3: Run batch experiment
                results = run_batch_sync(config_names, max_concurrent=2)
                
                # Step 4: Verify mixed results
                assert len(results) == 3
                
                # First experiment should succeed
                assert results[0]["success"] is True
                assert results[0]["experiment_id"] == config_names[0]
                assert results[0]["consensus_reached"] is True
                
                # Second experiment should fail
                assert results[1]["success"] is False
                assert "Test batch error" in results[1]["error"]
                assert results[1]["experiment_id"] == config_names[1]
                
                # Third experiment should succeed
                assert results[2]["success"] is True
                assert results[2]["experiment_id"] == config_names[2]
                assert results[2]["consensus_reached"] is False
    
    def test_config_variations(self):
        """Test that different configuration variations work correctly."""
        
        # Generate configs with different parameters
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_1 = generator.generate_and_save_config("var_test_1.yaml", "var_test_1")
        config_2 = generator.generate_and_save_config("var_test_2.yaml", "var_test_2")
        
        # Load and verify they have different settings
        import yaml
        
        with open(config_1, 'r') as f:
            config_data_1 = yaml.safe_load(f)
        
        with open(config_2, 'r') as f:
            config_data_2 = yaml.safe_load(f)
        
        # Verify different experiment IDs
        assert config_data_1["experiment_id"] == "var_test_1"
        assert config_data_2["experiment_id"] == "var_test_2"
        
        # Verify probabilistic values are valid
        assert config_data_1["experiment"]["max_rounds"] in [2, 3]
        assert config_data_2["experiment"]["max_rounds"] in [2, 3]
        
        # Verify both have valid agent counts
        assert len(config_data_1["agents"]) >= 2
        assert len(config_data_2["agents"]) >= 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])