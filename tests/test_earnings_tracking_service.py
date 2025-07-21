"""
Unit tests for EarningsTrackingService.
Tests earnings tracking functionality, disclosure generation, and performance calculations.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from typing import List

# Add src to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from maai.core.models import (
    EarningsTrackingConfig,
    IncomeDistribution,
    IncomeClass,
    AgentEarnings,
    EarningsUpdate,
    EarningsContext
)
from maai.services.earnings_tracking_service import EarningsTrackingService
from maai.agents.enhanced import DeliberationAgent


@pytest.fixture
def sample_income_distributions():
    """Sample income distributions for testing."""
    return [
        IncomeDistribution(
            distribution_id=1,
            name="Distribution A",
            income_by_class={
                IncomeClass.HIGH: 50000,
                IncomeClass.MEDIUM_HIGH: 40000,
                IncomeClass.MEDIUM: 30000,
                IncomeClass.MEDIUM_LOW: 20000,
                IncomeClass.LOW: 10000
            }
        ),
        IncomeDistribution(
            distribution_id=2,
            name="Distribution B",
            income_by_class={
                IncomeClass.HIGH: 60000,
                IncomeClass.MEDIUM_HIGH: 45000,
                IncomeClass.MEDIUM: 35000,
                IncomeClass.MEDIUM_LOW: 25000,
                IncomeClass.LOW: 15000
            }
        )
    ]


@pytest.fixture
def default_config():
    """Default earnings tracking configuration for testing."""
    return EarningsTrackingConfig(
        enabled=True,
        disclosure_points=["after_round_2", "end_phase1", "after_group", "experiment_end"],
        disclosure_style="motivational",
        show_performance_context=True,
        show_potential_ranges=True,
        include_phase_breakdown=True
    )


@pytest.fixture
def earnings_service(sample_income_distributions, default_config):
    """Create earnings tracking service for testing."""
    return EarningsTrackingService(
        payout_ratio=0.0001,
        config=default_config,
        income_distributions=sample_income_distributions
    )


@pytest.fixture
def mock_agent():
    """Create mock deliberation agent for testing."""
    agent = Mock(spec=DeliberationAgent)
    agent.agent_id = "test_agent_1"
    agent.name = "TestAgent"
    return agent


class TestEarningsTrackingService:
    """Test cases for EarningsTrackingService functionality."""
    
    def test_initialization(self, earnings_service, default_config, sample_income_distributions):
        """Test service initialization with proper configuration."""
        assert earnings_service.payout_ratio == 0.0001
        assert earnings_service.config == default_config
        assert earnings_service.income_distributions == sample_income_distributions
        assert earnings_service.agent_earnings == {}
        assert earnings_service.disclosure_history == {}
    
    def test_initialize_agent_earnings(self, earnings_service):
        """Test agent earnings initialization."""
        agent_id = "test_agent_1"
        
        # Initialize agent earnings
        earnings_service.initialize_agent_earnings(agent_id)
        
        # Verify initialization
        assert agent_id in earnings_service.agent_earnings
        assert earnings_service.agent_earnings[agent_id].agent_id == agent_id
        assert earnings_service.agent_earnings[agent_id].total_earnings == 0.0
        assert earnings_service.agent_earnings[agent_id].phase1_earnings == 0.0
        assert earnings_service.agent_earnings[agent_id].phase2_earnings == 0.0
        assert agent_id in earnings_service.disclosure_history
        assert earnings_service.disclosure_history[agent_id] == []
    
    def test_add_individual_round_payout(self, earnings_service):
        """Test adding individual round payouts."""
        agent_id = "test_agent_1"
        payout = 5.0
        round_num = 1
        context = "Test round 1"
        
        # Add payout
        result = earnings_service.add_individual_round_payout(agent_id, payout, round_num, context)
        
        # Verify payout was added correctly
        assert result.total_earnings == 5.0
        assert result.phase1_earnings == 5.0
        assert result.phase2_earnings == 0.0
        assert len(result.individual_round_payouts) == 1
        assert result.individual_round_payouts[0] == 5.0
        
        # Verify earnings history
        assert len(result.earnings_history) == 1
        history_entry = result.earnings_history[0]
        assert history_entry.round_type == "individual_round"
        assert history_entry.round_number == 1
        assert history_entry.payout_amount == 5.0
        assert history_entry.cumulative_total == 5.0
        assert history_entry.context == context
    
    def test_add_multiple_individual_payouts(self, earnings_service):
        """Test adding multiple individual round payouts."""
        agent_id = "test_agent_1"
        
        # Add multiple payouts
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1, "Round 1")
        earnings_service.add_individual_round_payout(agent_id, 3.0, 2, "Round 2")
        result = earnings_service.add_individual_round_payout(agent_id, 7.0, 3, "Round 3")
        
        # Verify cumulative totals
        assert result.total_earnings == 15.0
        assert result.phase1_earnings == 15.0
        assert result.phase2_earnings == 0.0
        assert len(result.individual_round_payouts) == 3
        assert result.individual_round_payouts == [5.0, 3.0, 7.0]
        
        # Verify cumulative history tracking
        assert len(result.earnings_history) == 3
        assert result.earnings_history[0].cumulative_total == 5.0
        assert result.earnings_history[1].cumulative_total == 8.0
        assert result.earnings_history[2].cumulative_total == 15.0
    
    def test_add_group_payout(self, earnings_service):
        """Test adding group outcome payout."""
        agent_id = "test_agent_1"
        
        # First add individual payouts
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1, "Round 1")
        earnings_service.add_individual_round_payout(agent_id, 3.0, 2, "Round 2")
        
        # Add group payout
        group_payout = 10.0
        context = "Group consensus outcome"
        result = earnings_service.add_group_payout(agent_id, group_payout, context)
        
        # Verify group payout integration
        assert result.total_earnings == 18.0
        assert result.phase1_earnings == 8.0
        assert result.phase2_earnings == 10.0
        
        # Verify group entry in history
        group_entry = result.earnings_history[-1]  # Should be last entry
        assert group_entry.round_type == "group_outcome"
        assert group_entry.round_number is None
        assert group_entry.payout_amount == 10.0
        assert group_entry.cumulative_total == 18.0
        assert group_entry.context == context
    
    def test_get_agent_total_earnings(self, earnings_service):
        """Test retrieving agent total earnings."""
        agent_id = "test_agent_1"
        
        # Before any earnings
        assert earnings_service.get_agent_total_earnings(agent_id) == 0.0
        
        # After adding earnings
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1)
        earnings_service.add_group_payout(agent_id, 10.0)
        
        assert earnings_service.get_agent_total_earnings(agent_id) == 15.0
        
        # Non-existent agent
        assert earnings_service.get_agent_total_earnings("nonexistent") == 0.0
    
    def test_calculate_potential_earnings_range(self, earnings_service):
        """Test potential earnings range calculation."""
        potential_range = earnings_service.calculate_potential_earnings_range()
        
        # Should calculate based on min/max incomes across distributions
        # Min: 10,000 (LOW from Distribution A), Max: 60,000 (HIGH from Distribution B)
        # Assuming 5 rounds total (4 individual + 1 group)
        expected_min = (10000 * 5) * 0.0001  # $5.00
        expected_max = (60000 * 5) * 0.0001  # $30.00
        
        assert potential_range["min"] == expected_min
        assert potential_range["max"] == expected_max
    
    def test_calculate_potential_earnings_range_no_distributions(self):
        """Test potential earnings calculation with no distributions."""
        config = EarningsTrackingConfig()
        service = EarningsTrackingService(0.0001, config, [])
        
        potential_range = service.calculate_potential_earnings_range()
        assert potential_range["min"] == 0.0
        assert potential_range["max"] == 0.0
    
    def test_get_performance_percentile(self, earnings_service):
        """Test performance percentile calculation."""
        # Add earnings for multiple agents
        earnings_service.add_individual_round_payout("agent_1", 10.0, 1)  # Total: 10.0
        earnings_service.add_individual_round_payout("agent_2", 20.0, 1)  # Total: 20.0
        earnings_service.add_individual_round_payout("agent_3", 30.0, 1)  # Total: 30.0
        
        # Test percentiles
        assert earnings_service.get_performance_percentile("agent_1") == 0.0  # Lowest
        assert earnings_service.get_performance_percentile("agent_2") == 1/3  # Middle
        assert earnings_service.get_performance_percentile("agent_3") == 2/3  # Highest
        
        # Test single agent (should return 0.5)
        single_service = EarningsTrackingService(0.0001, EarningsTrackingConfig(), [])
        single_service.add_individual_round_payout("solo_agent", 10.0, 1)
        assert single_service.get_performance_percentile("solo_agent") == 0.5
    
    def test_get_earnings_summary(self, earnings_service, sample_income_distributions):
        """Test earnings context generation."""
        agent_id = "test_agent_1"
        
        # Add some earnings
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1)
        earnings_service.add_individual_round_payout(agent_id, 3.0, 2)
        earnings_service.add_group_payout(agent_id, 10.0)
        
        # Get summary
        summary = earnings_service.get_earnings_summary(agent_id)
        
        assert isinstance(summary, EarningsContext)
        assert summary.agent_id == agent_id
        assert summary.current_total == 18.0
        assert summary.phase1_total == 8.0
        assert summary.phase2_total == 10.0
        assert summary.round_count == 2
        assert "min" in summary.potential_range
        assert "max" in summary.potential_range
        assert summary.performance_percentile is not None
    
    @pytest.mark.asyncio
    async def test_generate_earnings_disclosure_after_round_2(self, earnings_service, mock_agent):
        """Test earnings disclosure generation after round 2."""
        agent_id = mock_agent.agent_id
        
        # Add earnings for 2 rounds
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1)
        earnings_service.add_individual_round_payout(agent_id, 3.0, 2)
        
        context = earnings_service.get_earnings_summary(agent_id)
        
        # Generate disclosure
        disclosure = await earnings_service.generate_earnings_disclosure(
            mock_agent, context, "after_round_2"
        )
        
        assert "You have now completed 2 individual rounds" in disclosure
        assert "$8.00 total so far" in disclosure
        assert "Continue applying your developing strategy" in disclosure
    
    @pytest.mark.asyncio
    async def test_generate_earnings_disclosure_end_phase1(self, earnings_service, mock_agent):
        """Test earnings disclosure generation at end of Phase 1."""
        agent_id = mock_agent.agent_id
        
        # Add earnings for 4 rounds (typical Phase 1)
        for i in range(1, 5):
            earnings_service.add_individual_round_payout(agent_id, 2.5 * i, i)
        
        context = earnings_service.get_earnings_summary(agent_id)
        
        # Generate disclosure
        disclosure = await earnings_service.generate_earnings_disclosure(
            mock_agent, context, "end_phase1"
        )
        
        assert "Phase 1 Complete!" in disclosure
        assert "$25.00 total from 4 individual rounds" in disclosure
        assert "possible range was" in disclosure
        assert "ready to enter group deliberation" in disclosure
    
    @pytest.mark.asyncio
    async def test_generate_earnings_disclosure_after_group(self, earnings_service, mock_agent):
        """Test earnings disclosure generation after group outcome."""
        agent_id = mock_agent.agent_id
        
        # Add Phase 1 and Phase 2 earnings
        earnings_service.add_individual_round_payout(agent_id, 5.0, 1)
        earnings_service.add_individual_round_payout(agent_id, 5.0, 2)
        earnings_service.add_group_payout(agent_id, 10.0)
        
        context = earnings_service.get_earnings_summary(agent_id)
        
        # Generate disclosure
        disclosure = await earnings_service.generate_earnings_disclosure(
            mock_agent, context, "after_group"
        )
        
        assert "Group Decision Payout: $10.00" in disclosure
        assert "Phase 1 Total: $10.00" in disclosure
        assert "Grand Total: $20.00" in disclosure
    
    @pytest.mark.asyncio
    async def test_generate_earnings_disclosure_experiment_end(self, earnings_service, mock_agent):
        """Test earnings disclosure generation at experiment end."""
        agent_id = mock_agent.agent_id
        
        # Add multiple agents for performance context
        earnings_service.add_individual_round_payout("other_1", 5.0, 1)
        earnings_service.add_individual_round_payout("other_2", 15.0, 1)
        
        # Add earnings for test agent (should be middle performance)
        earnings_service.add_individual_round_payout(agent_id, 10.0, 1)
        earnings_service.add_group_payout(agent_id, 5.0)
        
        context = earnings_service.get_earnings_summary(agent_id)
        
        # Generate disclosure
        disclosure = await earnings_service.generate_earnings_disclosure(
            mock_agent, context, "experiment_end"
        )
        
        assert "Experiment Complete!" in disclosure
        assert "Your total earnings: $15.00" in disclosure
        assert "- Phase 1 (Individual):" in disclosure
        assert "- Phase 2 (Group):" in disclosure
        assert "Performance:" in disclosure
        assert "percentile" in disclosure
        assert "Thank you for your thoughtful participation" in disclosure
    
    def test_should_disclose_at_point(self, earnings_service):
        """Test disclosure point checking."""
        # Should disclose at configured points
        assert earnings_service.should_disclose_at_point("after_round_2")
        assert earnings_service.should_disclose_at_point("end_phase1")
        assert earnings_service.should_disclose_at_point("after_group")
        assert earnings_service.should_disclose_at_point("experiment_end")
        
        # Should not disclose at non-configured points
        assert not earnings_service.should_disclose_at_point("random_point")
        
        # Test with disabled service
        disabled_config = EarningsTrackingConfig(enabled=False)
        disabled_service = EarningsTrackingService(0.0001, disabled_config, [])
        assert not disabled_service.should_disclose_at_point("after_round_2")
    
    def test_get_all_agent_earnings(self, earnings_service):
        """Test retrieving all agent earnings."""
        # Add earnings for multiple agents
        earnings_service.add_individual_round_payout("agent_1", 10.0, 1)
        earnings_service.add_individual_round_payout("agent_2", 20.0, 1)
        
        all_earnings = earnings_service.get_all_agent_earnings()
        
        assert len(all_earnings) == 2
        assert "agent_1" in all_earnings
        assert "agent_2" in all_earnings
        assert all_earnings["agent_1"].total_earnings == 10.0
        assert all_earnings["agent_2"].total_earnings == 20.0
        
        # Should be a copy (not reference to original)
        all_earnings["agent_1"] = None
        assert earnings_service.agent_earnings["agent_1"] is not None
    
    def test_get_disclosure_history(self, earnings_service):
        """Test disclosure history retrieval."""
        agent_id = "test_agent_1"
        
        # Initially empty
        assert earnings_service.get_disclosure_history(agent_id) == []
        
        # Add some disclosure history (simulate)
        earnings_service.disclosure_history[agent_id] = ["Message 1", "Message 2"]
        
        history = earnings_service.get_disclosure_history(agent_id)
        assert history == ["Message 1", "Message 2"]
        
        # Should be a copy
        history.append("Message 3")
        assert len(earnings_service.disclosure_history[agent_id]) == 2
    
    def test_get_total_experiment_payouts(self, earnings_service):
        """Test total experiment payouts summary."""
        # Add earnings for multiple agents
        earnings_service.add_individual_round_payout("agent_1", 10.0, 1)
        earnings_service.add_group_payout("agent_1", 5.0)
        earnings_service.add_individual_round_payout("agent_2", 15.0, 1)
        
        payouts = earnings_service.get_total_experiment_payouts()
        
        assert payouts == {
            "agent_1": 15.0,
            "agent_2": 15.0
        }
    
    @pytest.mark.asyncio
    async def test_disclosure_style_variations(self, sample_income_distributions, mock_agent):
        """Test different disclosure style configurations."""
        styles = ["minimal", "standard", "motivational", "detailed"]
        
        for style in styles:
            config = EarningsTrackingConfig(disclosure_style=style)
            service = EarningsTrackingService(0.0001, config, sample_income_distributions)
            
            # Add some earnings
            service.add_individual_round_payout(mock_agent.agent_id, 10.0, 1)
            context = service.get_earnings_summary(mock_agent.agent_id)
            
            # Generate disclosure
            disclosure = await service.generate_earnings_disclosure(
                mock_agent, context, "end_phase1"
            )
            
            # All styles should generate some disclosure
            assert len(disclosure) > 0
            assert "$10.00" in disclosure  # Should contain earnings amount
    
    def test_performance_thresholds(self, sample_income_distributions):
        """Test performance threshold messaging."""
        config = EarningsTrackingConfig(
            congratulatory_threshold=0.75,
            encouragement_threshold=0.25
        )
        service = EarningsTrackingService(0.0001, config, sample_income_distributions)
        
        # Test threshold values are set correctly
        assert service.config.congratulatory_threshold == 0.75
        assert service.config.encouragement_threshold == 0.25


class TestEarningsTrackingIntegration:
    """Integration tests for earnings tracking with other components."""
    
    def test_earnings_update_model_validation(self):
        """Test EarningsUpdate model validation."""
        # Valid update
        update = EarningsUpdate(
            round_type="individual_round",
            round_number=1,
            payout_amount=5.0,
            cumulative_total=5.0,
            context="Test context"
        )
        
        assert update.round_type == "individual_round"
        assert update.round_number == 1
        assert update.payout_amount == 5.0
        assert update.cumulative_total == 5.0
        assert update.context == "Test context"
        assert isinstance(update.timestamp, datetime)
    
    def test_agent_earnings_model_methods(self):
        """Test AgentEarnings model method functionality."""
        earnings = AgentEarnings(agent_id="test_agent")
        
        # Test individual round payout method
        earnings.add_individual_round_payout(5.0, 1, "Round 1")
        
        assert earnings.total_earnings == 5.0
        assert earnings.phase1_earnings == 5.0
        assert earnings.phase2_earnings == 0.0
        assert len(earnings.individual_round_payouts) == 1
        assert len(earnings.earnings_history) == 1
        
        # Test group payout method
        earnings.add_group_payout(10.0, "Group outcome")
        
        assert earnings.total_earnings == 15.0
        assert earnings.phase1_earnings == 5.0
        assert earnings.phase2_earnings == 10.0
        assert len(earnings.earnings_history) == 2
    
    def test_earnings_context_model(self):
        """Test EarningsContext model structure."""
        context = EarningsContext(
            agent_id="test_agent",
            current_total=15.0,
            phase1_total=10.0,
            phase2_total=5.0,
            round_count=4,
            potential_range={"min": 5.0, "max": 30.0},
            performance_percentile=0.75
        )
        
        assert context.agent_id == "test_agent"
        assert context.current_total == 15.0
        assert context.phase1_total == 10.0
        assert context.phase2_total == 5.0
        assert context.round_count == 4
        assert context.potential_range == {"min": 5.0, "max": 30.0}
        assert context.performance_percentile == 0.75


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])