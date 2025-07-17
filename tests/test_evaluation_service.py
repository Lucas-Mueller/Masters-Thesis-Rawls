"""
Comprehensive tests for EvaluationService and Likert scale evaluation functionality.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.maai.services.evaluation_service import EvaluationService
from src.maai.core.models import (
    AgentEvaluationResponse, 
    PrincipleEvaluation, 
    ConsensusResult, 
    PrincipleChoice,
    LikertScale
)


class TestEvaluationService:
    """Test EvaluationService main functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = EvaluationService(max_concurrent_evaluations=2)
        
        # Mock agents
        self.mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2"),
            Mock(agent_id="agent3", name="Agent3")
        ]
        
        # Mock moderator
        self.mock_moderator = Mock()
        
        # Mock consensus result
        self.consensus_result = ConsensusResult(
            unanimous=True,
            agreed_principle=PrincipleChoice(
                principle_id=1,
                principle_name="Maximize the Minimum Income",
                reasoning="Test reasoning"
            ),
            dissenting_agents=[],
            rounds_to_consensus=2,
            total_messages=5
        )
    
    def test_initialization(self):
        """Test service initialization."""
        assert self.service.max_concurrent_evaluations == 2
        assert self.service.semaphore._value == 2
    
    def test_default_max_concurrent_evaluations(self):
        """Test default concurrent evaluations limit."""
        default_service = EvaluationService()
        assert default_service.max_concurrent_evaluations == 50
        assert default_service.semaphore._value == 50
    
    def test_create_evaluation_prompt_with_consensus(self):
        """Test evaluation prompt creation with consensus."""
        prompt = self.service._create_evaluation_prompt(self.consensus_result)
        
        assert "The group reached consensus on: Maximize the Minimum Income" in prompt
        assert "4-point scale" in prompt
        assert "PRINCIPLE 1:" in prompt
        assert "PRINCIPLE 2:" in prompt
        assert "PRINCIPLE 3:" in prompt
        assert "PRINCIPLE 4:" in prompt
        assert "REASONING 1:" in prompt
        assert "OVERALL REASONING:" in prompt
    
    def test_create_evaluation_prompt_without_consensus(self):
        """Test evaluation prompt creation without consensus."""
        no_consensus_result = ConsensusResult(
            unanimous=False,
            agreed_principle=None,
            dissenting_agents=["agent1"],
            rounds_to_consensus=0,
            total_messages=5
        )
        
        prompt = self.service._create_evaluation_prompt(no_consensus_result)
        
        assert "The group did not reach consensus" in prompt
        assert "4-point scale" in prompt
        assert "PRINCIPLE 1:" in prompt
    
    def test_create_initial_assessment_prompt(self):
        """Test initial assessment prompt creation."""
        prompt = self.service._create_initial_assessment_prompt()
        
        assert "Before any discussion begins" in prompt
        assert "initial thoughts and preferences" in prompt
        assert "4-point scale" in prompt
        assert "Strongly Disagree (1)" in prompt
        assert "Strongly Agree (4)" in prompt
        assert "PRINCIPLE 1:" in prompt
        assert "OVERALL REASONING:" in prompt
    
    def test_create_fallback_response(self):
        """Test fallback response creation."""
        mock_agent = Mock(agent_id="agent1", name="Agent1")
        
        response = self.service._create_fallback_response(mock_agent)
        
        assert isinstance(response, AgentEvaluationResponse)
        assert response.agent_id == "agent1"
        assert response.agent_name == "Agent1"
        assert len(response.principle_evaluations) == 4
        assert response.overall_reasoning == "Evaluation process failed - using fallback response"
        assert response.evaluation_duration == 0.0
        
        # Check that all evaluations are neutral
        for evaluation in response.principle_evaluations:
            assert isinstance(evaluation, PrincipleEvaluation)
            assert evaluation.satisfaction_rating == LikertScale.AGREE
            assert "Evaluation failed" in evaluation.reasoning
    
    @pytest.mark.asyncio
    async def test_parse_evaluation_response_success(self):
        """Test successful JSON parsing of evaluation response."""
        mock_agent_response = """
        PRINCIPLE 1: Strongly Agree
        REASONING 1: This ensures fairness
        PRINCIPLE 2: Disagree
        REASONING 2: Too focused on averages
        PRINCIPLE 3: Agree
        REASONING 3: Good balance
        PRINCIPLE 4: Strongly Disagree
        REASONING 4: Too complex
        """
        
        # Mock moderator response
        mock_moderator_json = {
            "principle_1": {"rating": "strongly_agree", "reasoning": "This ensures fairness"},
            "principle_2": {"rating": "disagree", "reasoning": "Too focused on averages"},
            "principle_3": {"rating": "agree", "reasoning": "Good balance"},
            "principle_4": {"rating": "strongly_disagree", "reasoning": "Too complex"}
        }
        
        mock_result = Mock()
        mock_result.new_items = [json.dumps(mock_moderator_json)]
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            with patch('src.maai.services.evaluation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = json.dumps(mock_moderator_json)
                
                evaluations = await self.service._parse_evaluation_response(
                    mock_agent_response, self.mock_moderator
                )
                
                assert len(evaluations) == 4
                
                # Check first evaluation
                assert evaluations[0].principle_id == 1
                assert evaluations[0].satisfaction_rating == LikertScale.STRONGLY_AGREE
                assert evaluations[0].reasoning == "This ensures fairness"
                
                # Check second evaluation
                assert evaluations[1].principle_id == 2
                assert evaluations[1].satisfaction_rating == LikertScale.DISAGREE
                assert evaluations[1].reasoning == "Too focused on averages"
                
                # Check third evaluation
                assert evaluations[2].principle_id == 3
                assert evaluations[2].satisfaction_rating == LikertScale.AGREE
                assert evaluations[2].reasoning == "Good balance"
                
                # Check fourth evaluation
                assert evaluations[3].principle_id == 4
                assert evaluations[3].satisfaction_rating == LikertScale.STRONGLY_DISAGREE
                assert evaluations[3].reasoning == "Too complex"
    
    @pytest.mark.asyncio
    async def test_parse_evaluation_response_json_wrapped(self):
        """Test JSON parsing when response is wrapped in other text."""
        mock_agent_response = "Test response"
        
        wrapped_response = """
        Based on the agent's response, here is the extracted data:
        
        {
            "principle_1": {"rating": "agree", "reasoning": "Good principle"},
            "principle_2": {"rating": "disagree", "reasoning": "Not ideal"},
            "principle_3": {"rating": "strongly_agree", "reasoning": "Best option"},
            "principle_4": {"rating": "strongly_disagree", "reasoning": "Poor choice"}
        }
        
        This completes the extraction.
        """
        
        mock_result = Mock()
        mock_result.new_items = [wrapped_response]
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            with patch('src.maai.services.evaluation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = wrapped_response
                
                evaluations = await self.service._parse_evaluation_response(
                    mock_agent_response, self.mock_moderator
                )
                
                assert len(evaluations) == 4
                assert evaluations[0].satisfaction_rating == LikertScale.AGREE
                assert evaluations[1].satisfaction_rating == LikertScale.DISAGREE
                assert evaluations[2].satisfaction_rating == LikertScale.STRONGLY_AGREE
                assert evaluations[3].satisfaction_rating == LikertScale.STRONGLY_DISAGREE
    
    @pytest.mark.asyncio
    async def test_parse_evaluation_response_json_error_fallback(self):
        """Test fallback parsing when JSON parsing fails."""
        mock_agent_response = """
        PRINCIPLE 1: Strongly Agree
        REASONING 1: This is the best principle
        PRINCIPLE 2: Disagree
        REASONING 2: Not suitable for society
        PRINCIPLE 3: Agree
        REASONING 3: Reasonable approach
        PRINCIPLE 4: Strongly Disagree
        REASONING 4: Too complicated
        """
        
        # Mock moderator returning invalid JSON
        mock_result = Mock()
        mock_result.new_items = ["Invalid JSON response"]
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            with patch('src.maai.services.evaluation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.return_value = mock_result
                mock_text.return_value = "Invalid JSON response"
                
                evaluations = await self.service._parse_evaluation_response(
                    mock_agent_response, self.mock_moderator
                )
                
                assert len(evaluations) == 4
                
                # Should use fallback parsing
                assert evaluations[0].principle_id == 1
                assert evaluations[0].satisfaction_rating == LikertScale.STRONGLY_AGREE
                assert evaluations[1].satisfaction_rating == LikertScale.DISAGREE
                assert evaluations[2].satisfaction_rating == LikertScale.AGREE
                assert evaluations[3].satisfaction_rating == LikertScale.STRONGLY_DISAGREE
    
    def test_fallback_parse_evaluation_all_patterns(self):
        """Test fallback parsing with various text patterns."""
        test_response = """
        PRINCIPLE 1: Strongly Agree
        REASONING 1: This ensures fairness for all
        
        PRINCIPLE 2: Disagree
        REASONING 2: Too focused on averages
        
        PRINCIPLE 3: Agree
        REASONING 3: Good balance of concerns
        
        PRINCIPLE 4: Strongly Disagree
        REASONING 4: Too complex to implement
        """
        
        evaluations = self.service._fallback_parse_evaluation(test_response)
        
        assert len(evaluations) == 4
        
        assert evaluations[0].principle_id == 1
        assert evaluations[0].satisfaction_rating == LikertScale.STRONGLY_AGREE
        assert "This ensures fairness for all" in evaluations[0].reasoning
        
        assert evaluations[1].principle_id == 2
        assert evaluations[1].satisfaction_rating == LikertScale.DISAGREE
        assert "Too focused on averages" in evaluations[1].reasoning
        
        assert evaluations[2].principle_id == 3
        assert evaluations[2].satisfaction_rating == LikertScale.AGREE
        assert "Good balance of concerns" in evaluations[2].reasoning
        
        assert evaluations[3].principle_id == 4
        assert evaluations[3].satisfaction_rating == LikertScale.STRONGLY_DISAGREE
        assert "Too complex to implement" in evaluations[3].reasoning
    
    def test_fallback_parse_evaluation_alternative_patterns(self):
        """Test fallback parsing with alternative text patterns."""
        test_response = """
        principle 1: strongly agree because it's fair
        principle 2: disagree since it's not good
        Principle 3: agree - reasonable approach
        4. strongly disagree - too hard
        """
        
        evaluations = self.service._fallback_parse_evaluation(test_response)
        
        assert len(evaluations) == 4
        assert evaluations[0].satisfaction_rating == LikertScale.STRONGLY_AGREE
        assert evaluations[1].satisfaction_rating == LikertScale.DISAGREE
        assert evaluations[2].satisfaction_rating == LikertScale.AGREE
        assert evaluations[3].satisfaction_rating == LikertScale.STRONGLY_DISAGREE
    
    def test_fallback_parse_evaluation_no_patterns(self):
        """Test fallback parsing with no recognizable patterns."""
        test_response = "This is just random text with no principle information."
        
        evaluations = self.service._fallback_parse_evaluation(test_response)
        
        assert len(evaluations) == 4
        
        # Should default to AGREE for all
        for evaluation in evaluations:
            assert evaluation.satisfaction_rating == LikertScale.AGREE
            assert "Agent response indicated agree" in evaluation.reasoning
    
    @pytest.mark.asyncio
    async def test_evaluate_agent_principles_success(self):
        """Test successful agent principle evaluation."""
        mock_agent = Mock(agent_id="agent1", name="Agent1")
        
        # Mock agent response
        mock_result = Mock()
        mock_result.new_items = ["PRINCIPLE 1: Agree\nREASONING 1: Good principle"]
        
        # Mock moderator response
        mock_moderator_json = {
            "principle_1": {"rating": "agree", "reasoning": "Good principle"},
            "principle_2": {"rating": "disagree", "reasoning": "Not ideal"},
            "principle_3": {"rating": "strongly_agree", "reasoning": "Best option"},
            "principle_4": {"rating": "strongly_disagree", "reasoning": "Poor choice"}
        }
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            with patch('src.maai.services.evaluation_service.ItemHelpers.text_message_outputs') as mock_text:
                # First call for agent, second for moderator
                mock_run.side_effect = [mock_result, Mock(new_items=[json.dumps(mock_moderator_json)])]
                mock_text.side_effect = [
                    "PRINCIPLE 1: Agree\nREASONING 1: Good principle",
                    json.dumps(mock_moderator_json)
                ]
                
                response = await self.service._evaluate_agent_principles(
                    mock_agent, self.consensus_result, self.mock_moderator
                )
                
                assert isinstance(response, AgentEvaluationResponse)
                assert response.agent_id == "agent1"
                assert response.agent_name == "Agent1"
                assert len(response.principle_evaluations) == 4
                assert response.evaluation_duration > 0
                assert response.overall_reasoning == "PRINCIPLE 1: Agree\nREASONING 1: Good principle"
    
    @pytest.mark.asyncio
    async def test_evaluate_agent_principles_exception_handling(self):
        """Test exception handling in agent evaluation."""
        mock_agent = Mock(agent_id="agent1", name="Agent1")
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            mock_run.side_effect = Exception("Test error")
            
            response = await self.service._evaluate_agent_principles(
                mock_agent, self.consensus_result, self.mock_moderator
            )
            
            # Should return fallback response
            assert isinstance(response, AgentEvaluationResponse)
            assert response.agent_id == "agent1"
            assert response.agent_name == "Agent1"
            assert response.overall_reasoning == "Evaluation process failed - using fallback response"
            assert response.evaluation_duration == 0.0
    
    @pytest.mark.asyncio
    async def test_conduct_initial_agent_assessment_success(self):
        """Test successful initial assessment for single agent."""
        mock_agent = Mock(agent_id="agent1", name="Agent1")
        
        # Mock agent response
        mock_result = Mock()
        mock_result.new_items = ["PRINCIPLE 1: Agree\nREASONING 1: Good principle"]
        
        # Mock moderator response
        mock_moderator_json = {
            "principle_1": {"rating": "agree", "reasoning": "Good principle"},
            "principle_2": {"rating": "disagree", "reasoning": "Not ideal"},
            "principle_3": {"rating": "strongly_agree", "reasoning": "Best option"},
            "principle_4": {"rating": "strongly_disagree", "reasoning": "Poor choice"}
        }
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            with patch('src.maai.services.evaluation_service.ItemHelpers.text_message_outputs') as mock_text:
                mock_run.side_effect = [mock_result, Mock(new_items=[json.dumps(mock_moderator_json)])]
                mock_text.side_effect = [
                    "PRINCIPLE 1: Agree\nREASONING 1: Good principle",
                    json.dumps(mock_moderator_json)
                ]
                
                response = await self.service._conduct_initial_agent_assessment(
                    mock_agent, self.mock_moderator
                )
                
                assert isinstance(response, AgentEvaluationResponse)
                assert response.agent_id == "agent1"
                assert response.agent_name == "Agent1"
                assert len(response.principle_evaluations) == 4
                assert response.evaluation_duration > 0
    
    @pytest.mark.asyncio
    async def test_conduct_initial_agent_assessment_exception(self):
        """Test exception handling in initial assessment."""
        mock_agent = Mock(agent_id="agent1", name="Agent1")
        
        with patch('src.maai.services.evaluation_service.Runner.run') as mock_run:
            mock_run.side_effect = Exception("Test error")
            
            response = await self.service._conduct_initial_agent_assessment(
                mock_agent, self.mock_moderator
            )
            
            # Should return fallback response
            assert isinstance(response, AgentEvaluationResponse)
            assert response.agent_id == "agent1"
            assert response.overall_reasoning == "Evaluation process failed - using fallback response"
    
    @pytest.mark.asyncio
    async def test_conduct_parallel_evaluation_success(self):
        """Test successful parallel evaluation of multiple agents."""
        mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2")
        ]
        
        # Mock successful evaluations
        mock_evaluation_1 = AgentEvaluationResponse(
            agent_id="agent1",
            agent_name="Agent1",
            principle_evaluations=[],
            overall_reasoning="Test reasoning 1",
            evaluation_duration=1.0
        )
        
        mock_evaluation_2 = AgentEvaluationResponse(
            agent_id="agent2",
            agent_name="Agent2",
            principle_evaluations=[],
            overall_reasoning="Test reasoning 2",
            evaluation_duration=2.0
        )
        
        with patch.object(self.service, '_evaluate_agent_principles') as mock_evaluate:
            mock_evaluate.side_effect = [mock_evaluation_1, mock_evaluation_2]
            
            results = await self.service.conduct_parallel_evaluation(
                mock_agents, self.consensus_result, self.mock_moderator
            )
            
            assert len(results) == 2
            assert results[0].agent_id == "agent1"
            assert results[1].agent_id == "agent2"
            assert mock_evaluate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_conduct_parallel_evaluation_with_exceptions(self):
        """Test parallel evaluation with some agents failing."""
        mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2")
        ]
        
        # Mock one success and one failure
        mock_evaluation_1 = AgentEvaluationResponse(
            agent_id="agent1",
            agent_name="Agent1",
            principle_evaluations=[],
            overall_reasoning="Test reasoning 1",
            evaluation_duration=1.0
        )
        
        with patch.object(self.service, '_evaluate_agent_principles') as mock_evaluate:
            mock_evaluate.side_effect = [mock_evaluation_1, Exception("Test error")]
            
            results = await self.service.conduct_parallel_evaluation(
                mock_agents, self.consensus_result, self.mock_moderator
            )
            
            assert len(results) == 2
            assert results[0].agent_id == "agent1"  # Success
            assert results[1].agent_id == "agent2"  # Fallback response
            assert results[1].overall_reasoning == "Evaluation process failed - using fallback response"
    
    @pytest.mark.asyncio
    async def test_conduct_initial_assessment_success(self):
        """Test successful initial assessment for multiple agents."""
        mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2")
        ]
        
        # Mock successful assessments
        mock_assessment_1 = AgentEvaluationResponse(
            agent_id="agent1",
            agent_name="Agent1",
            principle_evaluations=[],
            overall_reasoning="Initial assessment 1",
            evaluation_duration=1.0
        )
        
        mock_assessment_2 = AgentEvaluationResponse(
            agent_id="agent2",
            agent_name="Agent2",
            principle_evaluations=[],
            overall_reasoning="Initial assessment 2",
            evaluation_duration=2.0
        )
        
        with patch.object(self.service, '_conduct_initial_agent_assessment') as mock_assess:
            mock_assess.side_effect = [mock_assessment_1, mock_assessment_2]
            
            dummy_consensus = ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=0
            )
            
            results = await self.service.conduct_initial_assessment(
                mock_agents, dummy_consensus, self.mock_moderator
            )
            
            assert len(results) == 2
            assert results[0].agent_id == "agent1"
            assert results[1].agent_id == "agent2"
            assert mock_assess.call_count == 2
    
    @pytest.mark.asyncio
    async def test_conduct_initial_assessment_with_exceptions(self):
        """Test initial assessment with some agents failing."""
        mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2")
        ]
        
        # Mock one success and one failure
        mock_assessment_1 = AgentEvaluationResponse(
            agent_id="agent1",
            agent_name="Agent1",
            principle_evaluations=[],
            overall_reasoning="Initial assessment 1",
            evaluation_duration=1.0
        )
        
        with patch.object(self.service, '_conduct_initial_agent_assessment') as mock_assess:
            mock_assess.side_effect = [mock_assessment_1, Exception("Test error")]
            
            dummy_consensus = ConsensusResult(
                unanimous=False,
                agreed_principle=None,
                dissenting_agents=[],
                rounds_to_consensus=0,
                total_messages=0
            )
            
            results = await self.service.conduct_initial_assessment(
                mock_agents, dummy_consensus, self.mock_moderator
            )
            
            assert len(results) == 2
            assert results[0].agent_id == "agent1"  # Success
            assert results[1].agent_id == "agent2"  # Fallback response
            assert results[1].overall_reasoning == "Evaluation process failed - using fallback response"
    
    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """Test that semaphore properly limits concurrent evaluations."""
        # Create service with limit of 1
        service = EvaluationService(max_concurrent_evaluations=1)
        
        mock_agents = [
            Mock(agent_id="agent1", name="Agent1"),
            Mock(agent_id="agent2", name="Agent2")
        ]
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0
        
        async def mock_evaluate(agent, consensus_result, moderator):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            
            # Simulate work
            await asyncio.sleep(0.1)
            
            concurrent_count -= 1
            
            return AgentEvaluationResponse(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                principle_evaluations=[],
                overall_reasoning="Test",
                evaluation_duration=0.1
            )
        
        with patch.object(service, '_evaluate_agent_principles', side_effect=mock_evaluate):
            await service.conduct_parallel_evaluation(
                mock_agents, self.consensus_result, self.mock_moderator
            )
            
            # Should never exceed semaphore limit
            assert max_concurrent <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])