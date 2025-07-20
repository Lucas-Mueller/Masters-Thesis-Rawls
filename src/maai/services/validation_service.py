"""
ValidationService for validating principle choices and ensuring required constraints are provided.
Simple service focused on choice validation and error messaging.
"""

from typing import List, Optional
from ..core.models import PrincipleChoice, get_principle_by_id


class ValidationService:
    """
    Simple service for validating principle choices and constraint parameters.
    Ensures agents provide required constraint values for principles 3 and 4.
    """
    
    def validate_principle_choice(self, principle_choice: PrincipleChoice) -> dict:
        """
        Validate a principle choice and return validation result.
        
        Args:
            principle_choice: Agent's principle choice to validate
            
        Returns:
            Dictionary with validation result and any error messages
        """
        errors = []
        is_valid = True
        
        # Check if principle ID is valid
        if principle_choice.principle_id not in [1, 2, 3, 4]:
            errors.append(f"Invalid principle ID: {principle_choice.principle_id}. Must be 1, 2, 3, or 4.")
            is_valid = False
        
        # Get principle information
        principle_info = get_principle_by_id(principle_choice.principle_id)
        
        if not principle_info:
            errors.append(f"Unknown principle ID: {principle_choice.principle_id}")
            is_valid = False
        else:
            # Check constraint requirements for principle 3 (floor constraint)
            if principle_choice.principle_id == 3:
                if principle_choice.floor_constraint is None:
                    errors.append("Floor constraint value is required for principle 3 (MAXIMIZING THE AVERAGE WITH A FLOOR CONSTRAINT). Please specify the minimum income amount.")
                    is_valid = False
                elif principle_choice.floor_constraint < 0:
                    errors.append("Floor constraint must be a non-negative dollar amount.")
                    is_valid = False
            
            # Check constraint requirements for principle 4 (range constraint)
            if principle_choice.principle_id == 4:
                if principle_choice.range_constraint is None:
                    errors.append("Range constraint value is required for principle 4 (MAXIMIZING THE AVERAGE WITH A RANGE CONSTRAINT). Please specify the maximum income difference amount.")
                    is_valid = False
                elif principle_choice.range_constraint < 0:
                    errors.append("Range constraint must be a non-negative dollar amount.")
                    is_valid = False
            
            # Check that constraints are not provided for principles that don't need them
            if principle_choice.principle_id in [1, 2]:
                if principle_choice.floor_constraint is not None:
                    errors.append(f"Floor constraint is not applicable for principle {principle_choice.principle_id}.")
                    is_valid = False
                if principle_choice.range_constraint is not None:
                    errors.append(f"Range constraint is not applicable for principle {principle_choice.principle_id}.")
                    is_valid = False
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'validated_choice': principle_choice if is_valid else None
        }
    
    def generate_error_message(self, validation_result: dict) -> str:
        """
        Generate a user-friendly error message for invalid principle choices.
        
        Args:
            validation_result: Result from validate_principle_choice()
            
        Returns:
            Formatted error message for the agent
        """
        if validation_result['is_valid']:
            return ""
        
        error_message = "Invalid principle choice. Please correct the following issues:\n\n"
        
        for i, error in enumerate(validation_result['errors'], 1):
            error_message += f"{i}. {error}\n"
        
        error_message += "\nPlease make your choice again with the required information."
        
        return error_message
    
    def validate_batch_choices(self, principle_choices: List[PrincipleChoice]) -> dict:
        """
        Validate multiple principle choices at once.
        
        Args:
            principle_choices: List of principle choices to validate
            
        Returns:
            Dictionary with batch validation results
        """
        all_valid = True
        validation_results = []
        
        for choice in principle_choices:
            result = self.validate_principle_choice(choice)
            validation_results.append(result)
            if not result['is_valid']:
                all_valid = False
        
        return {
            'all_valid': all_valid,
            'results': validation_results,
            'valid_choices': [r['validated_choice'] for r in validation_results if r['is_valid']],
            'invalid_count': sum(1 for r in validation_results if not r['is_valid'])
        }
    
    def get_constraint_requirements_text(self) -> str:
        """
        Get explanatory text about constraint requirements for agents.
        
        Returns:
            Formatted text explaining when constraints are required
        """
        return """
CONSTRAINT REQUIREMENTS:

- Principle 1 (MAXIMIZING THE FLOOR INCOME): No additional parameters required
- Principle 2 (MAXIMIZING THE AVERAGE INCOME): No additional parameters required  
- Principle 3 (FLOOR CONSTRAINT): You MUST specify a floor constraint amount (minimum income in dollars)
- Principle 4 (RANGE CONSTRAINT): You MUST specify a range constraint amount (maximum income difference in dollars)

When choosing principles 3 or 4, include the constraint amount in your response.
For example: "I choose principle 3 with a floor constraint of $15,000"
"""