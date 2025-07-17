"""
Tests for run_batch.py
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from run_batch import run_batch, run_batch_sync, run_test_batch
from config_generator import create_test_generator


class TestRunBatch:
    
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
    
    def test_run_batch_success(self):
        """Test successful batch execution."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(3, "batch")
        config_names = [f"batch_{i+1:03d}" for i in range(3)]
        
        # Mock the run_experiment function
        with patch('run_batch.run_experiment') as mock_run:
            # Create mock results for each experiment
            mock_results = []
            for i, name in enumerate(config_names):
                result = {
                    "success": True,
                    "experiment_id": name,
                    "consensus_reached": True,
                    "duration_seconds": 30.0 + i * 5,
                    "agreed_principle": f"principle_{i+1}",
                    "rounds_to_consensus": 2,
                    "total_messages": 5 + i,
                    "results": MagicMock()
                }
                mock_results.append(result)
            
            mock_run.side_effect = mock_results
            
            # Test batch execution
            results = run_batch_sync(config_names, max_concurrent=2)
            
            # Verify results
            assert len(results) == 3
            
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["experiment_id"] == config_names[i]
                assert result["consensus_reached"] is True
                assert result["duration_seconds"] == 30.0 + i * 5
                assert result["agreed_principle"] == f"principle_{i+1}"
                assert result["rounds_to_consensus"] == 2
                assert result["total_messages"] == 5 + i
                assert "batch_duration_seconds" in result
                assert "batch_index" in result
                assert result["batch_index"] == i
    
    def test_run_batch_with_failures(self):
        """Test batch execution with some failures."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(3, "batch")
        config_names = [f"batch_{i+1:03d}" for i in range(3)]
        
        # Mock the run_experiment function
        with patch('run_batch.run_experiment') as mock_run:
            # Create mixed results (success, failure, success)
            mock_results = [
                {
                    "success": True,
                    "experiment_id": "batch_1",
                    "consensus_reached": True,
                    "duration_seconds": 30.0,
                    "agreed_principle": "principle_1",
                    "rounds_to_consensus": 2,
                    "total_messages": 5,
                    "results": MagicMock()
                },
                {
                    "success": False,
                    "error": "Test error",
                    "experiment_id": "batch_2",
                    "consensus_reached": False,
                    "duration_seconds": 0.0,
                    "agreed_principle": None,
                    "rounds_to_consensus": 0,
                    "total_messages": 0,
                    "results": None
                },
                {
                    "success": True,
                    "experiment_id": "batch_3",
                    "consensus_reached": False,
                    "duration_seconds": 45.0,
                    "agreed_principle": None,
                    "rounds_to_consensus": 3,
                    "total_messages": 8,
                    "results": MagicMock()
                }
            ]
            
            mock_run.side_effect = mock_results
            
            # Test batch execution
            results = run_batch_sync(config_names, max_concurrent=2)
            
            # Verify results
            assert len(results) == 3
            
            # Check first result (success)
            assert results[0]["success"] is True
            assert results[0]["experiment_id"] == "batch_1"
            
            # Check second result (failure)
            assert results[1]["success"] is False
            assert results[1]["error"] == "Test error"
            assert results[1]["experiment_id"] == "batch_2"
            
            # Check third result (success but no consensus)
            assert results[2]["success"] is True
            assert results[2]["experiment_id"] == "batch_3"
            assert results[2]["consensus_reached"] is False
    
    def test_run_batch_with_exceptions(self):
        """Test batch execution with exceptions."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(2, "batch")
        # Extract actual config names from the generated paths
        config_names = []
        for path in config_paths:
            from pathlib import Path
            filename = Path(path).stem  # Get filename without extension
            config_names.append(filename)
        
        # Mock the run_experiment function
        with patch('run_batch.run_experiment') as mock_run:
            # First experiment succeeds, second raises exception
            mock_results = [
                {
                    "success": True,
                    "experiment_id": "batch_1",
                    "consensus_reached": True,
                    "duration_seconds": 30.0,
                    "agreed_principle": "principle_1",
                    "rounds_to_consensus": 2,
                    "total_messages": 5,
                    "results": MagicMock()
                }
            ]
            
            call_count = [0]  # Use mutable container
            
            def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_results[0]
                else:
                    raise Exception("Test exception")
            
            mock_run.side_effect = side_effect
            
            # Test batch execution
            results = run_batch_sync(config_names, max_concurrent=2)
            
            # Verify results
            assert len(results) == 2
            
            # Check first result (success)
            assert results[0]["success"] is True
            assert results[0]["experiment_id"] == "batch_1"
            
            # Check second result (exception)
            assert results[1]["success"] is False
            assert "Test exception" in results[1]["error"]
            assert results[1]["experiment_id"] == config_names[1]
    
    def test_run_batch_async(self):
        """Test async version of run_batch."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(2, "batch")
        # Extract actual config names from the generated paths
        config_names = []
        for path in config_paths:
            from pathlib import Path
            filename = Path(path).stem  # Get filename without extension
            config_names.append(filename)
        
        async def test_async_batch():
            # Mock the run_experiment function
            with patch('run_batch.run_experiment') as mock_run:
                # Create mock results using actual config names
                mock_results = [
                    {
                        "success": True,
                        "experiment_id": config_names[0],
                        "consensus_reached": True,
                        "duration_seconds": 30.0,
                        "agreed_principle": "principle_1",
                        "rounds_to_consensus": 2,
                        "total_messages": 5,
                        "results": MagicMock()
                    },
                    {
                        "success": True,
                        "experiment_id": config_names[1],
                        "consensus_reached": False,
                        "duration_seconds": 45.0,
                        "agreed_principle": None,
                        "rounds_to_consensus": 3,
                        "total_messages": 8,
                        "results": MagicMock()
                    }
                ]
                
                mock_run.side_effect = mock_results
                
                # Test async batch execution
                results = await run_batch(config_names, max_concurrent=2)
                
                # Verify results
                assert len(results) == 2
                
                for i, result in enumerate(results):
                    assert result["success"] is True
                    assert result["experiment_id"] == config_names[i]
                    assert "batch_duration_seconds" in result
                    assert "batch_index" in result
                    assert result["batch_index"] == i
        
        # Run async test
        asyncio.run(test_async_batch())
    
    def test_concurrency_limit(self):
        """Test that concurrency limit is respected."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(4, "batch")
        config_names = [f"batch_{i+1:03d}" for i in range(4)]
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_seen = 0
        
        async def mock_run_experiment(config_path):
            nonlocal concurrent_count, max_concurrent_seen
            
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            concurrent_count -= 1
            
            return {
                "success": True,
                "experiment_id": config_path,
                "consensus_reached": True,
                "duration_seconds": 30.0,
                "agreed_principle": "principle_1",
                "rounds_to_consensus": 2,
                "total_messages": 5,
                "results": MagicMock()
            }
        
        # Mock the run_experiment function
        with patch('run_batch.run_experiment', side_effect=mock_run_experiment):
            # Test with max_concurrent=2
            results = run_batch_sync(config_names, max_concurrent=2)
            
            # Verify concurrency limit was respected
            assert max_concurrent_seen <= 2
            assert len(results) == 4
    
    def test_result_structure(self):
        """Test that batch results have correct structure."""
        
        # Create test configurations
        generator = create_test_generator()
        generator.output_folder = str(self.temp_path)
        config_paths = generator.generate_batch_configs(1, "batch")
        config_names = ["batch_001"]
        
        # Mock the run_experiment function
        with patch('run_batch.run_experiment') as mock_run:
            mock_result = {
                "success": True,
                "experiment_id": "batch_1",
                "consensus_reached": True,
                "duration_seconds": 30.0,
                "agreed_principle": "principle_1",
                "rounds_to_consensus": 2,
                "total_messages": 5,
                "results": MagicMock()
            }
            
            mock_run.return_value = mock_result
            
            # Test batch execution
            results = run_batch_sync(config_names, max_concurrent=1)
            
            # Verify result structure
            assert len(results) == 1
            result = results[0]
            
            # Check that all original fields are preserved
            for key, value in mock_result.items():
                assert result[key] == value
            
            # Check that batch-specific fields are added
            assert "batch_duration_seconds" in result
            assert "batch_index" in result
            assert isinstance(result["batch_duration_seconds"], float)
            assert isinstance(result["batch_index"], int)
            assert result["batch_index"] == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])