"""
Tests for DetailedExamplesService.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.maai.services.detailed_examples_service import DetailedExamplesService
from src.maai.services.economics_service import EconomicsService
from src.maai.core.models import IncomeDistribution, IncomeClass


class TestDetailedExamplesService:
    """Test the DetailedExamplesService functionality."""
    
    @pytest.fixture
    def income_distributions(self):
        """Create test income distributions."""
        return [
            IncomeDistribution(
                distribution_id=1,
                name="Distribution 1",
                income_by_class={
                    IncomeClass.HIGH: 32000,
                    IncomeClass.MEDIUM_HIGH: 27000,
                    IncomeClass.MEDIUM: 24000,
                    IncomeClass.MEDIUM_LOW: 13000,
                    IncomeClass.LOW: 12000
                }
            ),
            IncomeDistribution(
                distribution_id=2,
                name="Distribution 2",
                income_by_class={
                    IncomeClass.HIGH: 28000,
                    IncomeClass.MEDIUM_HIGH: 22000,
                    IncomeClass.MEDIUM: 20000,
                    IncomeClass.MEDIUM_LOW: 17000,
                    IncomeClass.LOW: 13000
                }
            )
        ]
    
    @pytest.fixture
    def economics_service(self, income_distributions):
        """Create test economics service."""
        return EconomicsService(income_distributions, 0.0001)
    
    @pytest.fixture
    def service(self, economics_service):
        """Create test detailed examples service."""
        return DetailedExamplesService(economics_service)
    
    def test_service_initialization(self, service, economics_service):
        """Test service initializes correctly."""
        assert service.economics_service == economics_service
    
    def test_format_detailed_examples(self, service):
        """Test that examples are formatted correctly."""
        # Mock analysis result
        dist1 = Mock()
        dist1.name = "Distribution 1"
        dist2 = Mock()
        dist2.name = "Distribution 2"
        
        mock_analysis = {
            "principle_1": {
                "selected_distribution": dist2,
                "reasoning": "Test reasoning"
            },
            "principle_2": {
                "selected_distribution": dist1, 
                "reasoning": "Test reasoning"
            },
            "principle_3": {
                "<=12,000": {
                    "selected_distribution": dist1,
                    "reasoning": "Test reasoning"
                },
                "<=13,000": {
                    "selected_distribution": dist2,
                    "reasoning": "Test reasoning"
                }
            },
            "principle_4": {
                ">=20,000": {
                    "selected_distribution": dist1,
                    "reasoning": "Test reasoning"
                }
            }
        }
        
        result = service._format_detailed_examples(mock_analysis)
        
        # Check that all key components are present
        assert "detailed examples" in result
        assert "outcome mappings" in result
        assert "Maximizing the floor → Distribution 2" in result
        assert "Maximizing average → Distribution 1" in result
        assert "floor constraint of:" in result
        assert "<=12,000 → Distribution 1" in result
        assert "<=13,000 → Distribution 2" in result
        assert "range constraint of:" in result
        assert ">=20,000 → Distribution 1" in result
    
    @pytest.mark.asyncio
    async def test_present_examples_to_agent(self, service):
        """Test presenting examples to a single agent."""
        # Create mock agent
        mock_agent = Mock()
        mock_agent.name = "Test Agent"
        mock_agent.run = AsyncMock(return_value=Mock(data="I understand the examples"))
        
        examples_text = "Test examples text"
        
        # Present examples
        await service._present_examples_to_agent(mock_agent, examples_text)
        
        # Verify agent.run was called with correct prompt
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args[0][0]
        assert "detailed examples" in call_args
        assert examples_text in call_args
        assert "acknowledge that you understand" in call_args
    
    @pytest.mark.asyncio
    async def test_present_detailed_examples(self, service, economics_service):
        """Test presenting examples to multiple agents."""
        # Create mock agents
        mock_agents = [
            Mock(name="Agent 1"),
            Mock(name="Agent 2")
        ]
        for agent in mock_agents:
            agent.run = AsyncMock(return_value=Mock(data="I understand"))
        
        # Mock the economics service analysis
        economics_service.analyze_all_principle_outcomes = Mock(return_value={
            "principle_1": {"selected_distribution": Mock(name="Dist 1")},
            "principle_2": {"selected_distribution": Mock(name="Dist 2")},
            "principle_3": {},
            "principle_4": {}
        })
        
        # Present examples
        await service.present_detailed_examples(mock_agents)
        
        # Verify all agents received examples
        for agent in mock_agents:
            agent.run.assert_called_once()


class TestEconomicsServiceAnalysis:
    """Test the new analysis methods in EconomicsService."""
    
    @pytest.fixture
    def income_distributions(self):
        """Create test income distributions."""
        return [
            IncomeDistribution(
                distribution_id=1,
                name="Distribution 1",
                income_by_class={
                    IncomeClass.HIGH: 32000,
                    IncomeClass.MEDIUM_HIGH: 27000,
                    IncomeClass.MEDIUM: 24000,
                    IncomeClass.MEDIUM_LOW: 13000,
                    IncomeClass.LOW: 12000
                }
            ),
            IncomeDistribution(
                distribution_id=4,
                name="Distribution 4",
                income_by_class={
                    IncomeClass.HIGH: 21000,
                    IncomeClass.MEDIUM_HIGH: 20000,
                    IncomeClass.MEDIUM: 19000,
                    IncomeClass.MEDIUM_LOW: 16000,
                    IncomeClass.LOW: 15000
                }
            )
        ]
    
    @pytest.fixture
    def service(self, income_distributions):
        """Create test economics service."""
        return EconomicsService(income_distributions, 0.0001)
    
    def test_analyze_principle_1(self, service):
        """Test principle 1 analysis (maximizing floor)."""
        result = service._analyze_principle_1()
        
        assert "selected_distribution" in result
        assert "reasoning" in result
        # Distribution 4 has higher minimum (15000 vs 12000)
        assert result["selected_distribution"].name == "Distribution 4"
    
    def test_analyze_principle_2(self, service):
        """Test principle 2 analysis (maximizing average)."""
        result = service._analyze_principle_2()
        
        assert "selected_distribution" in result
        assert "reasoning" in result
        # Distribution 1 has higher average
        assert result["selected_distribution"].name == "Distribution 1"
    
    def test_analyze_all_principle_outcomes(self, service):
        """Test complete principle analysis."""
        result = service.analyze_all_principle_outcomes()
        
        assert "principle_1" in result
        assert "principle_2" in result
        assert "principle_3" in result
        assert "principle_4" in result
        
        # Check structure
        assert "selected_distribution" in result["principle_1"]
        assert "selected_distribution" in result["principle_2"]
        assert isinstance(result["principle_3"], dict)
        assert isinstance(result["principle_4"], dict)
    
    def test_generate_meaningful_floor_values(self, service):
        """Test floor value generation."""
        floor_values = service._generate_meaningful_floor_values()
        
        assert isinstance(floor_values, list)
        assert len(floor_values) <= 4  # Limited to 4 as per plan
        assert all(isinstance(val, int) for val in floor_values)
        assert floor_values == sorted(floor_values)  # Should be sorted
    
    def test_generate_meaningful_range_values(self, service):
        """Test range value generation."""
        range_values = service._generate_meaningful_range_values()
        
        assert isinstance(range_values, list)
        assert len(range_values) <= 3  # Limited to 3 as per plan
        assert all(isinstance(val, int) for val in range_values)
        assert range_values == sorted(range_values, reverse=True)  # Should be sorted descending