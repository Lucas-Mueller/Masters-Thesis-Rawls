#!/usr/bin/env python3
import json
from pathlib import Path

# Read the most recent test file
test_file = Path('test_results/Lucas Test.json')
if test_file.exists():
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    print('=== Temperature Logging Test ===')
    for agent_id, agent_data in data.items():
        if agent_id != 'experiment_metadata':
            temp = agent_data.get('overall', {}).get('temperature')
            print(f'{agent_id}: temperature = {temp}')
    
    print()
    print('=== Likert Rating Test ===')
    for agent_id, agent_data in data.items():
        if agent_id != 'experiment_metadata':
            round_0 = agent_data.get('round_0', {})
            if 'principle_ratings' in round_0:
                print(f'{agent_id}: Has principle_ratings = YES')
                ratings = round_0['principle_ratings']
                for principle_id, rating_data in ratings.items():
                    print(f'  Principle {principle_id}: {rating_data["rating"]} ({rating_data["rating_text"]})')
            else:
                print(f'{agent_id}: Has principle_ratings = NO')
                if 'rating_likert' in round_0:
                    print(f'  Old format: {round_0["rating_likert"]}')
else:
    print('No test file found')