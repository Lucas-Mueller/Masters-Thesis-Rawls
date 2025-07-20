#!/usr/bin/env python3
"""
Simple test to validate the new game logic configuration loading.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading():
    """Test that the new configuration can be loaded properly."""
    print("🧪 Testing new game logic configuration loading...")
    
    try:
        from maai.config.manager import load_config_from_file
        
        # Test loading the new basic configuration
        config_path = "configs/new_game_basic.yaml"
        print(f"Loading configuration from: {config_path}")
        
        config = load_config_from_file(config_path)
        
        print("✅ Configuration loaded successfully!")
        print(f"  Experiment ID: {config.experiment_id}")
        print(f"  Agents: {config.num_agents}")
        print(f"  Individual Rounds: {config.individual_rounds}")
        print(f"  Payout Ratio: {config.payout_ratio}")
        print(f"  Income Distributions: {len(config.income_distributions)}")
        
        # Validate income distributions
        for i, dist in enumerate(config.income_distributions):
            print(f"  Distribution {dist.distribution_id}: {dist.name}")
            income_classes = list(dist.income_by_class.keys())
            print(f"    Income classes: {[cls.value for cls in income_classes]}")
        
        return config
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_service_initialization():
    """Test that all new services can be initialized."""
    print("\n🧪 Testing service initialization...")
    
    try:
        from maai.services import (
            EconomicsService, 
            PreferenceService, 
            ValidationService,
            ExperimentOrchestrator
        )
        from maai.core.models import IncomeDistribution, IncomeClass
        
        # Create sample income distributions
        sample_dist = IncomeDistribution(
            distribution_id=1,
            name="Test Distribution",
            income_by_class={
                IncomeClass.HIGH: 30000,
                IncomeClass.MEDIUM_HIGH: 25000,
                IncomeClass.MEDIUM: 20000,
                IncomeClass.MEDIUM_LOW: 15000,
                IncomeClass.LOW: 10000
            }
        )
        
        # Test economics service
        economics_service = EconomicsService([sample_dist], 0.0001)
        print("✅ EconomicsService initialized")
        
        # Test preference service
        preference_service = PreferenceService()
        print("✅ PreferenceService initialized")
        
        # Test validation service
        validation_service = ValidationService()
        print("✅ ValidationService initialized")
        
        # Test orchestrator
        orchestrator = ExperimentOrchestrator()
        print("✅ ExperimentOrchestrator initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """Test that the new models can be created."""
    print("\n🧪 Testing new models...")
    
    try:
        from maai.core.models import (
            IncomeDistribution,
            EconomicOutcome, 
            PreferenceRanking,
            PrincipleChoice,
            IncomeClass,
            CertaintyLevel
        )
        
        # Test IncomeDistribution
        dist = IncomeDistribution(
            distribution_id=1,
            name="Test Distribution",
            income_by_class={
                IncomeClass.HIGH: 30000,
                IncomeClass.MEDIUM: 20000,
                IncomeClass.LOW: 10000
            }
        )
        print("✅ IncomeDistribution model works")
        
        # Test PreferenceRanking
        ranking = PreferenceRanking(
            agent_id="test_agent",
            rankings=[1, 2, 3, 4],
            certainty_level=CertaintyLevel.SURE,
            reasoning="Test reasoning",
            phase="initial"
        )
        print("✅ PreferenceRanking model works")
        
        # Test PrincipleChoice with constraints
        choice = PrincipleChoice(
            principle_id=3,
            principle_name="Test Principle",
            reasoning="Test reasoning",
            floor_constraint=15000
        )
        print("✅ PrincipleChoice with constraints works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 New Game Logic System Test")
    print("=" * 50)
    
    # Test configuration loading
    config = test_config_loading()
    if not config:
        print("❌ Configuration loading failed - stopping tests")
        sys.exit(1)
    
    # Test service initialization
    services_ok = test_service_initialization()
    if not services_ok:
        print("❌ Service initialization failed - stopping tests")
        sys.exit(1)
    
    # Test models
    models_ok = test_models()
    if not models_ok:
        print("❌ Model testing failed - stopping tests")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 All basic tests passed!")
    print("✅ Configuration loading works")
    print("✅ Service initialization works")
    print("✅ New models work")
    print("\nThe new game logic system is ready for further testing!")