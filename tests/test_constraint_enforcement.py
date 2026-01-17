"""
Test suite for constraint enforcement - ensuring agents must provide explicit constraints
for principles 3 and 4 to make well-defined choices.

This test verifies the fix for the default constraint issue.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from maai.services.validation_service import ValidationService
from maai.services.consensus_service import ConsensusService  
from maai.services.experiment_orchestrator import ExperimentOrchestrator
from maai.core.models import PrincipleChoice, ExperimentConfig, ConsensusResult


class TestConstraintEnforcement:
    """Test constraint enforcement without default values."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()
        self.consensus_service = ConsensusService()
    
    def test_validation_rejects_principle_3_without_floor_constraint(self):
        """Test that principle 3 without floor constraint fails validation."""
        # Create principle choice without floor constraint
        choice = PrincipleChoice(
            principle_id=3,
            principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
            reasoning="This is the best principle",
            floor_constraint=None  # Missing constraint
        )
        
        # Validate the choice
        result = self.validation_service.validate_principle_choice(choice)
        
        # Should fail validation
        assert not result['is_valid']
        assert any("Floor constraint value is required" in error for error in result['errors'])
    
    def test_validation_rejects_principle_4_without_range_constraint(self):
        """Test that principle 4 without range constraint fails validation."""
        # Create principle choice without range constraint
        choice = PrincipleChoice(
            principle_id=4,
            principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT", 
            reasoning="This is the best principle",
            range_constraint=None  # Missing constraint
        )
        
        # Validate the choice
        result = self.validation_service.validate_principle_choice(choice)
        
        # Should fail validation
        assert not result['is_valid']
        assert any("Range constraint value is required" in error for error in result['errors'])
    
    def test_validation_accepts_principle_3_with_floor_constraint(self):
        """Test that principle 3 with floor constraint passes validation."""
        # Create principle choice with floor constraint
        choice = PrincipleChoice(
            principle_id=3,
            principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
            reasoning="This is the best principle with $18,000 floor",
            floor_constraint=18000
        )
        
        # Validate the choice
        result = self.validation_service.validate_principle_choice(choice)
        
        # Should pass validation
        assert result['is_valid']
        assert len(result['errors']) == 0
    
    def test_validation_accepts_principle_4_with_range_constraint(self):
        """Test that principle 4 with range constraint passes validation."""
        # Create principle choice with range constraint
        choice = PrincipleChoice(
            principle_id=4,
            principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
            reasoning="This is the best principle with $25,000 range",
            range_constraint=25000
        )
        
        # Validate the choice
        result = self.validation_service.validate_principle_choice(choice)
        
        # Should pass validation
        assert result['is_valid']
        assert len(result['errors']) == 0
    
    def test_consensus_rejects_principle_3_without_constraint(self):
        """Test that consensus detection rejects principle 3 without constraint."""
        # Mock transcript with responses missing floor constraint
        transcript = []
        
        # Mock agent responses - all choosing principle 3 but without constraint
        latest_responses = {
            "agent1": Mock(
                agent_id="agent1",
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=3,
                    principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
                    reasoning="Best principle",
                    floor_constraint=None  # Missing!
                )
            ),
            "agent2": Mock(
                agent_id="agent2", 
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=3,
                    principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT", 
                    reasoning="Best principle",
                    floor_constraint=None  # Missing!
                )
            )
        }
        
        # Mock conversation service to return these responses
        with patch('maai.services.consensus_service.ConversationService') as mock_conversation_service:
            mock_instance = mock_conversation_service.return_value
            mock_instance.get_latest_responses.return_value = latest_responses
            self.consensus_service.conversation_service = mock_instance
            result = asyncio.run(self.consensus_service.detect_consensus(transcript))
        
        # Should not detect consensus due to missing constraints
        assert not result.unanimous
        assert result.agreed_principle is None
    
    def test_consensus_rejects_principle_4_without_constraint(self):
        """Test that consensus detection rejects principle 4 without constraint."""
        # Mock transcript with responses missing range constraint
        transcript = []
        
        # Mock agent responses - all choosing principle 4 but without constraint
        latest_responses = {
            "agent1": Mock(
                agent_id="agent1",
                round_number=1, 
                updated_choice=PrincipleChoice(
                    principle_id=4,
                    principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
                    reasoning="Best principle",
                    range_constraint=None  # Missing!
                )
            ),
            "agent2": Mock(
                agent_id="agent2",
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=4,
                    principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
                    reasoning="Best principle", 
                    range_constraint=None  # Missing!
                )
            )
        }
        
        # Mock conversation service to return these responses
        with patch('maai.services.consensus_service.ConversationService') as mock_conversation_service:
            mock_instance = mock_conversation_service.return_value
            mock_instance.get_latest_responses.return_value = latest_responses
            self.consensus_service.conversation_service = mock_instance
            result = asyncio.run(self.consensus_service.detect_consensus(transcript))
        
        # Should not detect consensus due to missing constraints
        assert not result.unanimous
        assert result.agreed_principle is None
    
    def test_consensus_accepts_principle_3_with_constraints(self):
        """Test that consensus detection accepts principle 3 with proper constraints."""
        # Mock transcript
        transcript = []
        
        # Mock agent responses - all choosing principle 3 WITH constraint
        latest_responses = {
            "agent1": Mock(
                agent_id="agent1",
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=3,
                    principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
                    reasoning="Best principle with $18,000 floor",
                    floor_constraint=18000  # Explicit constraint!
                )
            ),
            "agent2": Mock(
                agent_id="agent2",
                round_number=1, 
                updated_choice=PrincipleChoice(
                    principle_id=3,
                    principle_name="MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT",
                    reasoning="Best principle with $18,000 floor",
                    floor_constraint=18000  # Explicit constraint!
                )
            )
        }
        
        # Mock conversation service to return these responses
        with patch('maai.services.consensus_service.ConversationService') as mock_conversation_service:
            mock_instance = mock_conversation_service.return_value
            mock_instance.get_latest_responses.return_value = latest_responses
            self.consensus_service.conversation_service = mock_instance
            result = asyncio.run(self.consensus_service.detect_consensus(transcript))
        
        # Should detect consensus with explicit constraints
        assert result.unanimous
        assert result.agreed_principle is not None
        assert result.agreed_principle.principle_id == 3
        assert result.agreed_principle.floor_constraint == 18000
    
    def test_consensus_accepts_principle_4_with_constraints(self):
        """Test that consensus detection accepts principle 4 with proper constraints."""
        # Mock transcript
        transcript = []
        
        # Mock agent responses - all choosing principle 4 WITH constraint
        latest_responses = {
            "agent1": Mock(
                agent_id="agent1", 
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=4,
                    principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT",
                    reasoning="Best principle with $25,000 range",
                    range_constraint=25000  # Explicit constraint!
                )
            ),
            "agent2": Mock(
                agent_id="agent2",
                round_number=1,
                updated_choice=PrincipleChoice(
                    principle_id=4,
                    principle_name="MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT", 
                    reasoning="Best principle with $25,000 range",
                    range_constraint=25000  # Explicit constraint!
                )
            )
        }
        
        # Mock conversation service to return these responses
        with patch('maai.services.consensus_service.ConversationService') as mock_conversation_service:
            mock_instance = mock_conversation_service.return_value
            mock_instance.get_latest_responses.return_value = latest_responses
            self.consensus_service.conversation_service = mock_instance
            result = asyncio.run(self.consensus_service.detect_consensus(transcript))
        
        # Should detect consensus with explicit constraints
        assert result.unanimous
        assert result.agreed_principle is not None
        assert result.agreed_principle.principle_id == 4
        assert result.agreed_principle.range_constraint == 25000

    @pytest.mark.asyncio
    async def test_parsing_without_defaults(self):
        """Test that parsing doesn't provide default values."""
        # Create a mock orchestrator to test parsing
        config = Mock()
        orchestrator = Mock()
        orchestrator.validation_service = self.validation_service
        
        # Import the parsing method
        from maai.services.experiment_orchestrator import ExperimentOrchestrator
        
        # Test principle 3 without constraint in text
        response_text = "I choose principle 3 because it's the best option"
        
        # Create actual instance to test parsing
        real_orchestrator = ExperimentOrchestrator()
        choice = await real_orchestrator._parse_individual_principle_choice(response_text, "test_agent")
        
        # Should have principle_id=3 but floor_constraint=None (no default)
        assert choice.principle_id == 3
        assert choice.floor_constraint is None  # No default applied!
        
        # Test principle 4 without constraint in text
        response_text = "I choose principle 4 because it maximizes efficiency"
        
        choice = await real_orchestrator._parse_individual_principle_choice(response_text, "test_agent")
        
        # Should have principle_id=4 but range_constraint=None (no default)
        assert choice.principle_id == 4
        assert choice.range_constraint is None  # No default applied!
        
    @pytest.mark.asyncio 
    async def test_parsing_with_explicit_constraints(self):
        """Test that parsing correctly extracts explicit constraints."""
        from maai.services.experiment_orchestrator import ExperimentOrchestrator
        
        real_orchestrator = ExperimentOrchestrator()
        
        # Test principle 3 with explicit floor constraint
        response_text = "I choose principle 3 with constraint $17,500 because it ensures fairness"
        
        choice = await real_orchestrator._parse_individual_principle_choice(response_text, "test_agent")
        
        # Should correctly parse the constraint
        assert choice.principle_id == 3
        assert choice.floor_constraint == 17500
        
        # Test principle 4 with explicit range constraint
        response_text = "I choose principle 4 with constraint $22,000 to limit inequality"
        
        choice = await real_orchestrator._parse_individual_principle_choice(response_text, "test_agent")
        
        # Should correctly parse the constraint
        assert choice.principle_id == 4
        assert choice.range_constraint == 22000


class TestConstraintEnforcementIntegration:
    """Integration tests for constraint enforcement across the full system."""
    
    @pytest.mark.asyncio
    async def test_no_default_constraints_end_to_end(self):
        """Test that the system never applies default constraints in any scenario."""
        # This is a conceptual test - in practice, we'd need to mock the full agent interaction
        # The key assertion is that any incomplete choice should trigger re-prompting, not defaults
        
        # Create validation service
        validation_service = ValidationService()
        
        # Test various incomplete choices
        incomplete_choices = [
            PrincipleChoice(
                principle_id=3, 
                principle_name="PRINCIPLE_3", 
                reasoning="reasoning", 
                floor_constraint=None
            ),
            PrincipleChoice(
                principle_id=4, 
                principle_name="PRINCIPLE_4", 
                reasoning="reasoning", 
                range_constraint=None
            ),
        ]
        
        for choice in incomplete_choices:
            result = validation_service.validate_principle_choice(choice)
            # All should fail validation - no defaults applied
            assert not result['is_valid']
            # Validation should identify the missing constraint
            assert any("constraint" in error.lower() for error in result['errors'])


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])