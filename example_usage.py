#!/usr/bin/env python3
"""
Example usage of the probabilistic configuration generator.

This file demonstrates how to use the new ProbabilisticConfigGenerator
to create experiment configurations with different probability distributions.
"""

from config_generator import ProbabilisticConfigGenerator, create_test_generator, create_example_generator

def basic_example():
    """Basic usage with simple probability distributions."""
    print("🔧 Basic Example: Simple Configuration Generation")
    print("=" * 50)
    
    # Create a generator with custom probabilities
    generator = ProbabilisticConfigGenerator(
        agent_count_probabilities={2: 0.5, 3: 0.5},
        personality_probabilities={
            "You are an economist.": 0.5,
            "You are a philosopher.": 0.5
        },
        rounds_probabilities={3: 0.7, 5: 0.3},
        model_probabilities={"gpt-4.1-nano": 1.0},
        output_folder="configs",
        temperature = 0,
    )
    
    # Generate a single configuration
    config_path = generator.generate_and_save_config("basic_example.yaml", "basic_example")
    print(f"✅ Generated: {config_path}")
    
    # Generate multiple configurations
    batch_paths = generator.generate_batch_configs(3, "basic_batch")
    print(f"✅ Generated {len(batch_paths)} configurations:")
    for i, path in enumerate(batch_paths, 1):
        print(f"   {i}. {path}")
    print()

def test_generator_example():
    """Using the pre-configured test generator."""
    print("🧪 Test Generator Example: Simple Testing Setup")
    print("=" * 50)
    
    # Use the pre-configured test generator
    generator = create_test_generator()
    
    # Generate test configurations
    config_paths = generator.generate_batch_configs(2, "test")
    print(f"✅ Generated {len(config_paths)} test configurations:")
    for path in config_paths:
        print(f"   • {path}")
    print()

def diverse_generator_example():
    """Using the example generator with diverse options."""
    print("🌟 Diverse Generator Example: Rich Experimental Setup")
    print("=" * 50)
    
    # Use the pre-configured example generator
    generator = create_example_generator()
    
    # Generate diverse configurations
    config_paths = generator.generate_batch_configs(3, "diverse")
    print(f"✅ Generated {len(config_paths)} diverse configurations:")
    for path in config_paths:
        print(f"   • {path}")
    print()

def custom_probabilities_example():
    """Custom probability distributions for specific research needs."""
    print("🎯 Custom Probabilities Example: Research-Specific Setup")
    print("=" * 50)
    
    # Create generator with research-specific probabilities
    generator = ProbabilisticConfigGenerator(
        agent_count_probabilities={
            3: 0.2,   # 20% chance of 3 agents
            4: 0.6,   # 60% chance of 4 agents  
            5: 0.2    # 20% chance of 5 agents
        },
        personality_probabilities={
            "You are a utilitarian focused on maximizing overall welfare.": 0.3,
            "You are a deontologist focused on duties and rights.": 0.3,
            "You are a virtue ethicist focused on character and virtues.": 0.2,
            "You are a pragmatist focused on practical outcomes.": 0.2
        },
        rounds_probabilities={
            5: 0.4,   # 40% chance of 5 rounds
            7: 0.4,   # 40% chance of 7 rounds
            10: 0.2   # 20% chance of 10 rounds
        },
        model_probabilities={
            "gpt-4.1": 0.5,
            "gpt-4.1-mini": 0.3,
            "claude-3-5-sonnet-20241022": 0.2
        },
        output_folder="configs"
    )
    
    # Generate configurations for research
    config_paths = generator.generate_batch_configs(5, "research")
    print(f"✅ Generated {len(config_paths)} research configurations:")
    for path in config_paths:
        print(f"   • {path}")
    print()

def command_line_examples():
    """Show command-line usage examples."""
    print("💻 Command-Line Usage Examples")
    print("=" * 50)
    
    print("Basic test generation:")
    print("  python config_generator.py --count 3 --prefix test")
    print()
    
    print("Diverse configuration generation:")
    print("  python config_generator.py --example --count 5 --prefix experiment")
    print()
    
    print("Custom output directory:")
    print("  python config_generator.py --example --count 2 --prefix custom --output-dir my_configs")
    print()

if __name__ == "__main__":
    print("🚀 Probabilistic Configuration Generator Examples")
    print("=" * 60)
    print()
    
    # Run all examples
    basic_example()
    test_generator_example()
    diverse_generator_example()
    custom_probabilities_example()
    command_line_examples()
    
    print("✨ All examples completed!")
    print("Check the 'configs/' directory for generated configuration files.")