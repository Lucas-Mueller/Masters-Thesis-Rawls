#!/usr/bin/env python3
import json

with open('test_results/test_logging_fixes.json', 'r') as f:
    data = json.load(f)

print('=== All Agent Keys ===')
for key in data.keys():
    if key != 'experiment_metadata':
        temp = data[key].get('overall', {}).get('temperature')
        print(f'{key}: temp = {temp}')
        
        # Check for principle ratings
        round_0 = data[key].get('round_0', {})
        has_ratings = 'principle_ratings' in round_0
        print(f'  Has structured ratings: {has_ratings}')
        if has_ratings:
            print(f'  Number of ratings: {len(round_0["principle_ratings"])}')
        print()