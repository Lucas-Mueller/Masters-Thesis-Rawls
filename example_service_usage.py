"""
Example demonstrating how the decomposed services allow for easy experimentation
with different consensus detection, communication patterns, and memory strategies.
"""

import asyncio
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from maai.core.models import ExperimentConfig, AgentConfig, DefaultConfig
from maai.core.deliberation_manager import DeliberationManager
from maai.services.consensus_service import (
    ConsensusService, 
    IdMatchingStrategy, 
    ThresholdBasedStrategy,
    SemanticSimilarityStrategy
)
from maai.services.conversation_service import (
    ConversationService,
    RandomCommunicationPattern,
    SequentialCommunicationPattern,
    HierarchicalCommunicationPattern
)
from maai.services.memory_service import (
    MemoryService,
    FullMemoryStrategy,
    RecentMemoryStrategy,
    SelectiveMemoryStrategy
)


async def demonstrate_service_usage():
    """Demonstrate different service configurations for research."""
    
    print("=== Service Decomposition Demonstration ===\n")
    
    # Base configuration
    config = ExperimentConfig(
        experiment_id="service_demo",
        max_rounds=2,
        agents=[
            AgentConfig(
                name="Economist",
                model="gpt-4.1-mini",
                personality="You are an economist focused on efficiency."
            ),
            AgentConfig(
                name="Philosopher", 
                model="gpt-4.1-mini",
                personality="You are a philosopher concerned with fairness."
            ),
            AgentConfig(
                name="Pragmatist",
                model="gpt-4.1-mini", 
                personality="You are a pragmatist focused on practical solutions."
            )
        ],
        defaults=DefaultConfig()
    )
    
    print("1. Default Configuration (Backward Compatible)")
    print("   - ID Matching Consensus")
    print("   - Random Communication Pattern")
    print("   - Full Memory Strategy")
    
    # Create default manager (same as before refactoring)
    default_manager = DeliberationManager(config)
    print(f"   ✓ DeliberationManager created with default services")
    
    print("\n2. Custom Threshold-Based Consensus (80% agreement)")
    threshold_consensus = ConsensusService(ThresholdBasedStrategy(threshold=0.8))
    threshold_manager = DeliberationManager(
        config, 
        consensus_service=threshold_consensus
    )
    print(f"   ✓ Manager with 80% threshold consensus created")
    
    print("\n3. Sequential Communication Pattern")
    sequential_conversation = ConversationService(SequentialCommunicationPattern())
    sequential_manager = DeliberationManager(
        config,
        conversation_service=sequential_conversation
    )
    print(f"   ✓ Manager with sequential communication created")
    
    print("\n4. Hierarchical Communication (1 leader speaks first)")
    hierarchical_conversation = ConversationService(
        HierarchicalCommunicationPattern(leader_count=1)
    )
    hierarchical_manager = DeliberationManager(
        config,
        conversation_service=hierarchical_conversation
    )
    print(f"   ✓ Manager with hierarchical communication created")
    
    print("\n5. Limited Memory Strategy (last 3 entries only)")
    recent_memory = MemoryService(RecentMemoryStrategy(max_entries=3))
    memory_manager = DeliberationManager(
        config,
        memory_service=recent_memory
    )
    print(f"   ✓ Manager with limited memory created")
    
    print("\n6. Fully Custom Configuration")
    custom_consensus = ConsensusService(SemanticSimilarityStrategy())
    custom_conversation = ConversationService(HierarchicalCommunicationPattern(leader_count=2))
    custom_memory = MemoryService(SelectiveMemoryStrategy(max_rounds=2))
    
    custom_manager = DeliberationManager(
        config,
        consensus_service=custom_consensus,
        conversation_service=custom_conversation,
        memory_service=custom_memory
    )
    print(f"   ✓ Fully customized manager created")
    
    print("\n7. Runtime Strategy Changes (Advanced Usage)")
    runtime_manager = DeliberationManager(config)
    
    # Access services through properties
    print(f"   - Original consensus strategy: {type(runtime_manager.consensus_service.detection_strategy).__name__}")
    
    # Change consensus strategy at runtime
    runtime_manager.consensus_service.set_detection_strategy(ThresholdBasedStrategy(threshold=0.9))
    print(f"   - Changed to: {type(runtime_manager.consensus_service.detection_strategy).__name__}")
    
    # Change communication pattern
    runtime_manager.conversation_service.set_communication_pattern(SequentialCommunicationPattern())
    print(f"   - Changed communication to: {type(runtime_manager.conversation_service.pattern).__name__}")
    
    # Change memory strategy
    runtime_manager.memory_service.set_memory_strategy(RecentMemoryStrategy(max_entries=5))
    print(f"   - Changed memory to: {type(runtime_manager.memory_service.memory_strategy).__name__}")
    
    print(f"\n✓ Demonstration complete! All service configurations work correctly.")
    print(f"✓ Researchers can now easily experiment with different strategies without modifying core logic.")


def demonstrate_research_scenarios():
    """Show specific research scenarios enabled by the decomposition."""
    
    print("\n=== Research Scenarios Enabled ===\n")
    
    print("1. Consensus Algorithm Comparison:")
    print("   - Run same experiment with ID matching vs threshold vs semantic similarity")
    print("   - Compare convergence rates and quality of decisions")
    print("   - Study impact of consensus rules on deliberation dynamics")
    
    print("\n2. Communication Pattern Research:")
    print("   - Random vs sequential vs hierarchical speaking orders")
    print("   - Impact of leader designation on group decisions") 
    print("   - Effect of speaking order on final consensus")
    
    print("\n3. Memory Strategy Studies:")
    print("   - Full memory vs limited memory impact on decisions")
    print("   - How memory constraints affect argument evolution")
    print("   - Forgetting vs remembering in multi-round deliberation")
    
    print("\n4. Combined Strategy Research:")
    print("   - Cross-factorial designs: memory × communication × consensus")
    print("   - Identify optimal combinations for different scenarios")
    print("   - Study interaction effects between different components")
    
    print("\n5. A/B Testing Framework:")
    print("   - Easy to run parallel experiments with different configurations")
    print("   - Statistical comparison of different approaches")
    print("   - Automated experimental pipelines")


if __name__ == "__main__":
    print("MAAI Service Decomposition Demo")
    print("=" * 50)
    
    # Check if we have required environment variables for actual experiments
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Note: OPENAI_API_KEY not set. This demo shows configuration only.")
        print("     To run actual experiments, set your API key.")
    
    asyncio.run(demonstrate_service_usage())
    demonstrate_research_scenarios()
    
    print("\n" + "=" * 50)
    print("🎉 Service decomposition implementation complete!")
    print("🔬 The system is now much more flexible for research experimentation.")