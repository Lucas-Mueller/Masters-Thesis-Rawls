"""
ConstraintExtractionService for parsing principle choices and constraints using AI.
Uses GPT-4.1-mini to robustly extract structured data from natural language agent responses.
"""

from typing import Optional, Dict, Any
from agents import Runner
from litellm import acompletion
import json
import asyncio

from ..core.models import PrincipleChoice, get_principle_by_id


class ConstraintExtractionService:
    """
    AI-powered service for extracting principle choices and constraint values from agent responses.
    Uses GPT-4.1-mini to parse natural language into structured data.
    """
    
    def __init__(self):
        self.extraction_model = "gpt-4.1-mini"
        self.extraction_temperature = 0.0  # Deterministic for consistent parsing
    
    async def extract_principle_choice(self, agent_response: str, agent_id: str) -> PrincipleChoice:
        """
        Extract a structured PrincipleChoice from an agent's natural language response.
        
        Args:
            agent_response: The agent's natural language response about their principle choice
            agent_id: ID of the agent who made the choice
            
        Returns:
            PrincipleChoice object with extracted data
        """
        
        # Create the extraction prompt
        extraction_prompt = self._create_extraction_prompt(agent_response)
        
        # Get structured extraction from AI
        extracted_data = await self._call_extraction_model(extraction_prompt)
        
        # Convert to PrincipleChoice object
        return self._create_principle_choice(extracted_data, agent_response, agent_id)
    
    def _create_extraction_prompt(self, agent_response: str) -> str:
        """Create a prompt for the extraction model to parse the agent response."""
        
        return f"""You are a data extraction expert. Your task is to extract structured information about distributive justice principle choices from agent responses.

AGENT RESPONSE TO ANALYZE:
{agent_response}

DISTRIBUTIVE JUSTICE PRINCIPLES:
1. MAXIMIZING THE FLOOR INCOME - Maximize income of poorest member (no constraints needed)
2. MAXIMIZING THE AVERAGE INCOME - Maximize average income regardless of distribution (no constraints needed)  
3. MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT - Maximize average while guaranteeing minimum income (requires floor constraint in dollars)
4. MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT - Maximize average while limiting income difference (requires range constraint in dollars)

EXTRACTION TASK:
Extract the following information from the agent response:

1. PRINCIPLE_ID: Which principle number (1, 2, 3, or 4) did the agent choose?
2. FLOOR_CONSTRAINT: If principle 3 was chosen, what is the minimum income constraint in dollars? (extract number only, no commas or symbols)
3. RANGE_CONSTRAINT: If principle 4 was chosen, what is the maximum income difference constraint in dollars? (extract number only, no commas or symbols)

IMPORTANT EXTRACTION RULES:
- Look for numbers with dollar signs, commas, or written as currency (e.g., "$20,000", "20000", "$20000", "twenty thousand")
- If the agent mentions "floor", "minimum", "constraint", or "guaranteed income" with a number, that's likely the floor constraint
- If the agent mentions "range", "difference", "gap", or "maximum difference" with a number, that's likely the range constraint  
- Only extract constraints for the chosen principle (principle 3 needs floor, principle 4 needs range)
- If no constraint is mentioned for principles 3 or 4, return null for that constraint
- Extract pure numbers only (e.g., if they say "$20,000" extract "20000")

RESPONSE FORMAT (JSON):
{{
    "principle_id": [1, 2, 3, or 4],
    "floor_constraint": [number or null],
    "range_constraint": [number or null],
    "extraction_confidence": ["high", "medium", "low"],
    "reasoning": "Brief explanation of extraction logic"
}}

Extract the information now:"""
    
    async def _call_extraction_model(self, prompt: str) -> Dict[str, Any]:
        """Call the AI extraction model and parse the JSON response."""
        
        try:
            response = await acompletion(
                model=self.extraction_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.extraction_temperature,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            try:
                # Look for JSON block in the response
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                elif "{" in response_text:
                    # Find the JSON object
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    json_text = response_text[json_start:json_end]
                else:
                    raise ValueError("No JSON found in response")
                
                extracted_data = json.loads(json_text)
                return extracted_data
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse JSON from extraction model: {e}")
                print(f"Response text: {response_text}")
                
                # Fallback to basic parsing
                return self._fallback_extraction(response_text)
                
        except Exception as e:
            print(f"Error calling extraction model: {e}")
            # Return default values to prevent system failure
            return {
                "principle_id": 1,
                "floor_constraint": None,
                "range_constraint": None,
                "extraction_confidence": "low",
                "reasoning": f"Extraction failed: {e}"
            }
    
    def _fallback_extraction(self, response_text: str) -> Dict[str, Any]:
        """
        Fallback extraction when JSON parsing fails.
        Uses simple text parsing as backup.
        """
        
        import re
        
        # Try to extract principle ID
        principle_match = re.search(r'"principle_id":\s*(\d+)', response_text)
        principle_id = int(principle_match.group(1)) if principle_match else 1
        
        # Try to extract floor constraint
        floor_match = re.search(r'"floor_constraint":\s*(\d+)', response_text)
        floor_constraint = int(floor_match.group(1)) if floor_match else None
        
        # Try to extract range constraint
        range_match = re.search(r'"range_constraint":\s*(\d+)', response_text)
        range_constraint = int(range_match.group(1)) if range_match else None
        
        return {
            "principle_id": principle_id,
            "floor_constraint": floor_constraint,
            "range_constraint": range_constraint,
            "extraction_confidence": "low",
            "reasoning": "Used fallback parsing due to JSON parse error"
        }
    
    def _create_principle_choice(self, extracted_data: Dict[str, Any], original_response: str, agent_id: str) -> PrincipleChoice:
        """Convert extracted data to PrincipleChoice object."""
        
        principle_id = extracted_data.get("principle_id", 1)
        
        # Ensure valid principle ID
        if principle_id not in [1, 2, 3, 4]:
            principle_id = 1
        
        # Get principle information
        principle_info = get_principle_by_id(principle_id)
        
        # Extract constraints
        floor_constraint = extracted_data.get("floor_constraint")
        range_constraint = extracted_data.get("range_constraint")
        
        # Validate constraint types
        if floor_constraint is not None:
            try:
                floor_constraint = int(floor_constraint)
            except (ValueError, TypeError):
                floor_constraint = None
        
        if range_constraint is not None:
            try:
                range_constraint = int(range_constraint)
            except (ValueError, TypeError):
                range_constraint = None
        
        return PrincipleChoice(
            principle_id=principle_id,
            principle_name=principle_info['name'],
            reasoning=original_response,
            floor_constraint=floor_constraint,
            range_constraint=range_constraint
        )
    
    async def extract_batch_principle_choices(self, agent_responses: Dict[str, str]) -> Dict[str, PrincipleChoice]:
        """
        Extract principle choices from multiple agent responses in parallel.
        
        Args:
            agent_responses: Dict mapping agent_id to their response text
            
        Returns:
            Dict mapping agent_id to their extracted PrincipleChoice
        """
        
        tasks = []
        for agent_id, response in agent_responses.items():
            task = self.extract_principle_choice(response, agent_id)
            tasks.append((agent_id, task))
        
        results = {}
        for agent_id, task in tasks:
            try:
                principle_choice = await task
                results[agent_id] = principle_choice
            except Exception as e:
                print(f"Failed to extract principle choice for agent {agent_id}: {e}")
                # Create fallback choice
                results[agent_id] = PrincipleChoice(
                    principle_id=1,
                    principle_name="MAXIMIZING THE FLOOR INCOME",
                    reasoning=agent_responses[agent_id],
                    floor_constraint=None,
                    range_constraint=None
                )
        
        return results
    
    def get_extraction_confidence_explanation(self) -> str:
        """Get explanation of extraction confidence levels."""
        
        return """
EXTRACTION CONFIDENCE LEVELS:

HIGH: The agent response clearly specified the principle number and any required constraints 
      in standard format (e.g., "I choose principle 3 with a constraint of $20,000").

MEDIUM: The principle choice was clear but constraint extraction required some interpretation
        of natural language (e.g., "principle 3 with minimum income twenty thousand").

LOW: The response was ambiguous, required fallback parsing, or extraction model failed.
     Default values may have been used.
"""