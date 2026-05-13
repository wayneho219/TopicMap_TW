#!/usr/bin/env python3
"""
Generate conceptGroups.json from result_all.csv label_fine column.
Groups fine-level topic labels by stock_id.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

def generate_concept_groups():
    root = Path(__file__).parent.parent
    csv_path = root / 'output' / 'result_all.csv'
    json_path = root / 'frontend' / 'src' / 'data' / 'conceptGroups.json'

    # Group labels by stock_id
    groups = defaultdict(set)

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stock_id = row['stock_id'].strip()
            label = row['label_fine'].strip()
            if stock_id and label:
                groups[stock_id].add(label)

    # Convert sets to sorted lists
    result = {stock_id: sorted(list(labels)) for stock_id, labels in groups.items()}

    # Write to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Generated {json_path}")
    print(f"Total stocks: {len(result)}")

    # Show a sample
    for stock_id in sorted(result.keys())[:5]:
        print(f"  {stock_id}: {result[stock_id]}")

if __name__ == '__main__':
    generate_concept_groups()
