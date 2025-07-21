"""
EconomicsService for handling income distributions, economic calculations, and payouts.
Simple service focused on core economic logic for the new game system.
"""

import random
from typing import List, Dict, Optional, Any
from ..core.models import (
    IncomeDistribution, 
    EconomicOutcome, 
    IncomeClass, 
    PrincipleChoice
)


class EconomicsService:
    """
    Simple service for economic calculations and income distribution logic.
    Handles principle application, random assignment, and payout calculations.
    """
    
    def __init__(self, income_distributions: List[IncomeDistribution], payout_ratio: float = 0.0001):
        """
        Initialize the economics service.
        
        Args:
            income_distributions: Available income distribution scenarios
            payout_ratio: Ratio for converting income to actual payout (default: $1 per $10,000)
        """
        self.income_distributions = income_distributions
        self.payout_ratio = payout_ratio
        
        # Create mapping for quick lookups
        self.distributions_by_id = {dist.distribution_id: dist for dist in income_distributions}
    
    def calculate_payout(self, actual_income: int) -> float:
        """
        Calculate payout amount based on actual income and payout ratio.
        
        Args:
            actual_income: Income amount from distribution
            
        Returns:
            Payout amount (actual_income * payout_ratio)
        """
        return actual_income * self.payout_ratio
    
    def assign_random_income_class(self) -> IncomeClass:
        """
        Randomly assign an income class to an agent.
        
        Returns:
            Randomly selected income class
        """
        return random.choice(list(IncomeClass))
    
    def get_income_for_class(self, distribution: IncomeDistribution, income_class: IncomeClass) -> int:
        """
        Get the income amount for a specific class in a distribution.
        
        Args:
            distribution: Income distribution scenario
            income_class: Income class to look up
            
        Returns:
            Income amount for the specified class
        """
        return distribution.income_by_class[income_class]
    
    def apply_principle_to_distributions(self, principle_choice: PrincipleChoice) -> IncomeDistribution:
        """
        Apply the chosen principle to select the appropriate income distribution.
        
        Args:
            principle_choice: Agent's principle choice with constraints
            
        Returns:
            Selected income distribution based on principle logic
        """
        if not self.income_distributions:
            raise ValueError("No income distributions available")
        
        # For now, implement simple principle-to-distribution mapping
        # This will be enhanced based on specific principle logic requirements
        
        if principle_choice.principle_id == 1:
            # Maximizing floor income - select distribution with highest minimum
            return self._select_distribution_with_highest_minimum()
        
        elif principle_choice.principle_id == 2:
            # Maximizing average income - select distribution with highest average
            return self._select_distribution_with_highest_average()
        
        elif principle_choice.principle_id == 3:
            # Floor constraint - select distribution meeting floor requirement
            if principle_choice.floor_constraint is None:
                raise ValueError("Floor constraint value required for principle 3")
            return self._select_distribution_with_floor_constraint(principle_choice.floor_constraint)
        
        elif principle_choice.principle_id == 4:
            # Range constraint - select distribution meeting range requirement
            if principle_choice.range_constraint is None:
                raise ValueError("Range constraint value required for principle 4")
            return self._select_distribution_with_range_constraint(principle_choice.range_constraint)
        
        else:
            raise ValueError(f"Unknown principle ID: {principle_choice.principle_id}")
    
    def create_economic_outcome(
        self, 
        agent_id: str, 
        round_number: int, 
        principle_choice: PrincipleChoice,
        assigned_income_class: Optional[IncomeClass] = None
    ) -> EconomicOutcome:
        """
        Create a complete economic outcome for an agent's choice.
        
        Args:
            agent_id: Agent identifier
            round_number: Round number (1-4 for individual rounds)
            principle_choice: Agent's principle choice
            assigned_income_class: Income class (if None, will be randomly assigned)
            
        Returns:
            Complete economic outcome with income and payout
        """
        # Apply principle to get distribution
        selected_distribution = self.apply_principle_to_distributions(principle_choice)
        
        # Assign income class if not provided
        if assigned_income_class is None:
            assigned_income_class = self.assign_random_income_class()
        
        # Get actual income for the class
        actual_income = self.get_income_for_class(selected_distribution, assigned_income_class)
        
        # Calculate payout
        payout_amount = self.calculate_payout(actual_income)
        
        return EconomicOutcome(
            agent_id=agent_id,
            round_number=round_number,
            chosen_principle=principle_choice.principle_id,
            assigned_income_class=assigned_income_class,
            actual_income=actual_income,
            payout_amount=payout_amount
        )
    
    def _select_distribution_with_highest_minimum(self) -> IncomeDistribution:
        """Select distribution with the highest minimum income."""
        best_dist = None
        highest_min = -1
        
        for dist in self.income_distributions:
            min_income = min(dist.income_by_class.values())
            if min_income > highest_min:
                highest_min = min_income
                best_dist = dist
        
        if best_dist is None:
            return self.income_distributions[0]  # Fallback
        
        return best_dist
    
    def _select_distribution_with_highest_average(self) -> IncomeDistribution:
        """Select distribution with the highest average income."""
        best_dist = None
        highest_avg = -1
        
        for dist in self.income_distributions:
            avg_income = sum(dist.income_by_class.values()) / len(dist.income_by_class)
            if avg_income > highest_avg:
                highest_avg = avg_income
                best_dist = dist
        
        if best_dist is None:
            return self.income_distributions[0]  # Fallback
        
        return best_dist
    
    def _select_distribution_with_floor_constraint(self, floor_constraint: int) -> IncomeDistribution:
        """Select distribution that maximizes average while meeting floor constraint."""
        valid_distributions = []
        
        # Find distributions that meet the floor constraint
        for dist in self.income_distributions:
            min_income = min(dist.income_by_class.values())
            if min_income >= floor_constraint:
                valid_distributions.append(dist)
        
        if not valid_distributions:
            # If no distribution meets constraint, return the one with highest minimum
            return self._select_distribution_with_highest_minimum()
        
        # Among valid distributions, select the one with highest average
        best_dist = None
        highest_avg = -1
        
        for dist in valid_distributions:
            avg_income = sum(dist.income_by_class.values()) / len(dist.income_by_class)
            if avg_income > highest_avg:
                highest_avg = avg_income
                best_dist = dist
        
        return best_dist if best_dist else valid_distributions[0]
    
    def _select_distribution_with_range_constraint(self, range_constraint: int) -> IncomeDistribution:
        """Select distribution that maximizes average while meeting range constraint."""
        valid_distributions = []
        
        # Find distributions that meet the range constraint
        for dist in self.income_distributions:
            income_values = list(dist.income_by_class.values())
            income_range = max(income_values) - min(income_values)
            if income_range <= range_constraint:
                valid_distributions.append(dist)
        
        if not valid_distributions:
            # If no distribution meets constraint, return the one with smallest range
            return self._select_distribution_with_smallest_range()
        
        # Among valid distributions, select the one with highest average
        best_dist = None
        highest_avg = -1
        
        for dist in valid_distributions:
            avg_income = sum(dist.income_by_class.values()) / len(dist.income_by_class)
            if avg_income > highest_avg:
                highest_avg = avg_income
                best_dist = dist
        
        return best_dist if best_dist else valid_distributions[0]
    
    def _select_distribution_with_smallest_range(self) -> IncomeDistribution:
        """Select distribution with the smallest income range."""
        best_dist = None
        smallest_range = float('inf')
        
        for dist in self.income_distributions:
            income_values = list(dist.income_by_class.values())
            income_range = max(income_values) - min(income_values)
            if income_range < smallest_range:
                smallest_range = income_range
                best_dist = dist
        
        return best_dist if best_dist else self.income_distributions[0]
    
    def analyze_all_principle_outcomes(self) -> Dict[str, Any]:
        """
        Analyze what distribution each principle would select for current set.
        Returns detailed mapping for all principles and constraint values.
        """
        analysis = {
            "principle_1": self._analyze_principle_1(),
            "principle_2": self._analyze_principle_2(), 
            "principle_3": self._analyze_principle_3_variations(),
            "principle_4": self._analyze_principle_4_variations()
        }
        return analysis

    def _analyze_principle_1(self) -> Dict[str, Any]:
        """Analyze which distribution maximizes floor income."""
        best_distribution = self._select_distribution_with_highest_minimum()
        return {
            "selected_distribution": best_distribution,
            "reasoning": "Maximizes minimum income across all classes"
        }

    def _analyze_principle_2(self) -> Dict[str, Any]:
        """Analyze which distribution maximizes average income.""" 
        best_distribution = self._select_distribution_with_highest_average()
        return {
            "selected_distribution": best_distribution,
            "reasoning": "Maximizes average income across all classes"
        }

    def _analyze_principle_3_variations(self) -> Dict[str, Any]:
        """Analyze principle 3 outcomes for various floor constraint values."""
        # Get meaningful floor values from actual distribution data
        floor_values = self._generate_meaningful_floor_values()
        
        variations = {}
        for floor_value in floor_values:
            try:
                selected_dist = self._select_distribution_with_floor_constraint(floor_value)
                variations[f"<=${floor_value:,}"] = {
                    "selected_distribution": selected_dist,
                    "reasoning": f"Maximizes average while ensuring minimum ${floor_value:,}"
                }
            except ValueError:
                # No distribution meets this floor constraint
                variations[f"<=${floor_value:,}"] = {
                    "selected_distribution": None,
                    "reasoning": f"No distribution meets floor constraint of ${floor_value:,}"
                }
        
        return variations

    def _analyze_principle_4_variations(self) -> Dict[str, Any]:
        """Analyze principle 4 outcomes for various range constraint values."""
        # Get meaningful range values from actual distribution data
        range_values = self._generate_meaningful_range_values()
        
        variations = {}
        for range_value in range_values:
            try:
                selected_dist = self._select_distribution_with_range_constraint(range_value)
                variations[f">=${range_value:,}"] = {
                    "selected_distribution": selected_dist,
                    "reasoning": f"Maximizes average while limiting range to ${range_value:,}"
                }
            except ValueError:
                variations[f">=${range_value:,}"] = {
                    "selected_distribution": None,
                    "reasoning": f"No distribution meets range constraint of ${range_value:,}"
                }
        
        return variations

    def _generate_meaningful_floor_values(self) -> List[int]:
        """Generate meaningful floor constraint values for analysis."""
        # Use actual income values from distributions to create realistic test cases
        unique_incomes = set()
        for dist in self.income_distributions:
            unique_incomes.update(dist.income_by_class.values())
        
        # Return sorted list of meaningful floor values (limit to 4 as in plan)
        sorted_incomes = sorted(list(unique_incomes))
        # Take up to 4 values, focusing on lower end for floor constraints
        return sorted_incomes[:4]

    def _generate_meaningful_range_values(self) -> List[int]:
        """Generate meaningful range constraint values for analysis."""
        # Calculate actual ranges in each distribution and create test values
        ranges = []
        for dist in self.income_distributions:
            income_values = list(dist.income_by_class.values())
            income_range = max(income_values) - min(income_values)
            ranges.append(income_range)
        
        # Return unique ranges sorted in descending order (limit to 3)
        unique_ranges = sorted(list(set(ranges)), reverse=True)
        return unique_ranges[:3]

    def get_distribution_summary_table(self) -> str:
        """Generate formatted table of all distributions for display."""
        lines = []
        lines.append("Income Distribution Summary:")
        lines.append("")
        
        # Header
        header = "| Income Class | " + " | ".join([f"Dist. {d.distribution_id}" for d in self.income_distributions]) + " |"
        lines.append(header)
        
        # Separator
        separator = "|" + "|".join([" --- " for _ in range(len(self.income_distributions) + 1)]) + "|"
        lines.append(separator)
        
        # Data rows
        for income_class in IncomeClass:
            row = f"| {income_class.value} | "
            values = []
            for dist in self.income_distributions:
                values.append(f"${dist.income_by_class[income_class]:,}")
            row += " | ".join(values) + " |"
            lines.append(row)
        
        return "\n".join(lines)

    def get_principle_outcome_summary(self, analysis: Dict) -> str:
        """Generate formatted summary of principle outcomes for display.""" 
        lines = []
        lines.append("Principle Outcome Mappings:")
        lines.append("")
        
        # Principle 1
        p1_result = analysis["principle_1"]
        lines.append(f"Maximizing the floor → {p1_result['selected_distribution'].name}")
        
        # Principle 2  
        p2_result = analysis["principle_2"]
        lines.append(f"Maximizing average → {p2_result['selected_distribution'].name}")
        
        # Principle 3 variations
        lines.append("")
        lines.append("Maximizing average with a floor constraint of:")
        for constraint, result in analysis["principle_3"].items():
            if result["selected_distribution"]:
                lines.append(f"  {constraint} → {result['selected_distribution'].name}")
            else:
                lines.append(f"  {constraint} → No valid distribution")
        
        # Principle 4 variations
        lines.append("")
        lines.append("Maximizing average with a range constraint of:")
        for constraint, result in analysis["principle_4"].items():
            if result["selected_distribution"]:
                lines.append(f"  {constraint} → {result['selected_distribution'].name}")
            else:
                lines.append(f"  {constraint} → No valid distribution")
        
        return "\n".join(lines)