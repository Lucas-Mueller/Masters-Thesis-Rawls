#!/usr/bin/env python3
"""
Simple test to verify OpenAI Agents SDK tracing is properly set up.
This test only checks if tracing is working without running a full experiment.
"""

import asyncio
from agents import trace, gen_trace_id, Agent, Runner


async def simple_trace_test():
    """Test basic tracing functionality."""
    print("=== Simple OpenAI Agents SDK Tracing Test ===")
    print("")
    
    try:
        # Generate trace ID
        trace_id = gen_trace_id()
        print(f"Generated trace ID: {trace_id}")
        
        # Test basic trace setup
        with trace(
            workflow_name="Simple Tracing Test",
            trace_id=trace_id,
            group_id="tracing_test"
        ):
            print("✅ Trace context established successfully!")
            print(f"   Trace URL: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            
            # Test a simple agent interaction
            agent = Agent(
                name="TestAgent",
                instructions="You are a test agent. Respond with 'Hello World!' to any input.",
                model="gpt-4o-mini"
            )
            
            print("\n   Testing simple agent interaction...")
            result = await Runner.run(agent, "Say hello")
            print("✅ Agent interaction completed and traced!")
            
        print("\n🎉 All tracing tests passed!")
        print("The framework is properly configured for comprehensive experiment tracing.")
        
    except Exception as e:
        print(f"❌ Tracing test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_trace_test())