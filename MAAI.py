import agents
from agents import Agent, ItemHelpers, Runner, trace
import asyncio
import os 
from dotenv import load_dotenv
import agentops
from agents.extensions.models.litellm_model import LitellmModel
import pandas as pd

from datetime import datetime

now = datetime.now()
current_time = now.strftime("%H:%M:%S")


load_dotenv()

AGENT_OPS_API_KEY=os.environ.get("AGENT_OPS_API_KEY")
agentops.init(AGENT_OPS_API_KEY)


OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
DEEPSEEK_API_KEY=os.environ.get("DEEPSEEK_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

base_instruct = """ 
You are a smart agent tasked at debating normative issues
"""




number_of_agents = 4
procedure_instructions = f""" 
You are one agent working in a group of {number_of_agents} agents who aim to agree on a principle of distributing goods in the society you will live in.
In making this choice, recall that your choice will yield you a payoff you could not be sure which income class you would actually be in.
The discussion will be conducted in rounds, where each agent will have a chance to speak in turn.
The discussion will end when all agents agree on a principle of distributive justice.
If you cannot reach an agreement after 10 rounds, you will all get nothing. 
"""

workflow_instruct= f'''
{procedure_instructions}
Please evaluate each principle carefully and extensively before making your descision
At the end of your response make a choice on which principle you favor, you must decide for one 
'''

principles = """
There are 4 principles of distributive justice that you should consider when debating normative issues:
1. Maximize the Minimum Income: The principle that ensures the worst-off member of society is as well-off as possible.

2. Maximize the Average Income: The principle that ensures the greatest possible total income for the group, without regard for its distribution.

3. Maximize the Average Income with a Floor Constraint: A hybrid principle that establishes a minimum guaranteed income (a "safety net") for everyone, and then maximizes the average income.

4. Maximize the Average Income with a Range Constraint: A hybrid principle that limits the gap between the richest and poorest members, and then maximizes the average income.
"""

judge_instruct = f'''
You are given a text and have to judge which of the following principles is favored
{principles}
It must be precisely one. 
Return just the number as one character
'''


base_agent_1 = Agent(
    name="Base Agent 1",
    instructions = base_instruct,
    model="gpt-4.1-mini",
    )
base_agent_2 = Agent(
    name="Base Agent 2",
    instructions = base_instruct,
    #model=LitellmModel(model="anthropic/claude-sonnet-4-20250514", api_key=ANTHROPIC_API_KEY)
    )

base_agent_3 = Agent(
    name="Base Agent 3",
    instructions = base_instruct,
    model="gpt-4.1-mini",
    )
base_agent_4= Agent(
    name="Base Agent 4",
    instructions= base_instruct,
    #model=LitellmModel(model="deepseek/deepseek-chat", api_key=DEEPSEEK_API_KEY)
)


agreement_judge_agent= Agent(
    name="Agreement Judger",
    instructions= judge_instruct,
    model="gpt-4.1",
    
)

def create_simple_agents_df(num_agents):
    """Simple version that creates just the column structure"""
    columns = ['Round']
    
    # Generate agent columns
    for i in range(1, num_agents + 1):
        columns += [f'Agent_{i}_response', f'Agent_{i}_choice']
    
    columns += ['agreement', 'agreement_content']
    
    return pd.DataFrame(columns=columns)

def check_agreement(session_tracker, session_row, number_of_agents):
    """Check if all agents agree on their choice for the current round"""
    # Get Agent 1's choice as reference
    first_choice = session_tracker.loc[session_row, 'Agent_1_choice']
    
    # Check all other agents against Agent 1
    agreement = True
    for i in range(2, number_of_agents + 1):
        choice = session_tracker.loc[session_row, f'Agent_{i}_choice']
        if choice != first_choice:
            agreement = False
            break
    
    # Update dataframe with results
    session_tracker.loc[session_row, 'agreement'] = agreement
    if agreement:
        session_tracker.loc[session_row, 'agreement_content'] = first_choice
    else:
        session_tracker.loc[session_row, 'agreement_content'] = None
    
    return session_tracker, agreement


async def main():
    number_of_agents = 4
    session_tracker = create_simple_agents_df(number_of_agents)
    
    print("-----Intialization Phase Starts-------")

    current_round = 1 
    with trace("Initialization Phase"):
        res_agent_1, res_agent_2, res_agent_3,res_agent_4 = await asyncio.gather(
            Runner.run(
                base_agent_1,
                workflow_instruct,
            ),
            Runner.run(
                base_agent_2,
                workflow_instruct,
            ),
            Runner.run(
                base_agent_3,
                workflow_instruct,
            ),
            Runner.run(
                base_agent_4,
                workflow_instruct,
            ),
        )
    # Adds new empty row
    session_tracker.loc[len(session_tracker)] = None

    # Get the last index and update specific column
    last_index = session_tracker.index[-1]
    session_tracker.loc[last_index, 'Round'] = current_round

    # Store responses using a loop
    res_agent_1 = ItemHelpers.text_message_outputs(res_agent_1.new_items)
    res_agent_2 = ItemHelpers.text_message_outputs(res_agent_2.new_items)
    res_agent_3 = ItemHelpers.text_message_outputs(res_agent_3.new_items)
    res_agent_4 = ItemHelpers.text_message_outputs(res_agent_4.new_items)

    responses = [res_agent_1, res_agent_2, res_agent_3, res_agent_4]

    # Find the session row
    session_row = session_tracker[session_tracker['Round'] == current_round].index[0]

    # Update each agent's response
    for i, response in enumerate(responses, 1):
        session_tracker.loc[session_row, f'Agent_{i}_response'] = response

    # Judge each agent's response and store choice directly in dataframe
    for i in range(number_of_agents):
        judge_result = await Runner.run(
            agreement_judge_agent,
            responses[i]
        )
        judge_choice = ItemHelpers.text_message_outputs(judge_result.new_items)
        session_tracker.loc[session_row, f'Agent_{i+1}_choice'] = judge_choice.strip()
    
    # Check if agreement has been reached
    session_tracker, agreement_reached = check_agreement(session_tracker, session_row, number_of_agents)
    
    
    print(f"Round {current_round}: Agreement = {agreement_reached}")
    
    current_round+=1


    session_tracker.to_csv(f'Logs_MAAI/{current_time} log.csv', index=False)


    
    
if __name__ == "__main__":
    asyncio.run(main())

