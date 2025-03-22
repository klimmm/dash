import json

def transform_hierarchy(data):
    result = {}

    def process_node(node, node_key):
        # Create entry for current node
        result[node_key] = {
            "label": node["name"],
            "children": list(node.get("sublines", {}).keys())
        }

        # Process all children recursively
        if "sublines" in node and node["sublines"]:
            for child_key, child_node in node["sublines"].items():
                process_node(child_node, child_key)

    # Start processing from the root nodes
    for key, node in data.items():
        process_node(node, key)

    return result

# Read the input file
with open('lines_hierarchy.json', 'r', encoding='utf-8') as file:
    input_data = json.load(file)

# Transform the data
transformed_data = transform_hierarchy(input_data)

# Write to output file
with open('transformed_hierarchy.json', 'w', encoding='utf-8') as file:
    json.dump(transformed_data, file, ensure_ascii=False, indent=2)

print('Transformation complete! Output saved to transformed_hierarchy.json')