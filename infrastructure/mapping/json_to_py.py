
import json

# Load the insurers JSON file
with open('./insurers.json', 'r', encoding='utf-8') as f:
    insurers_data = json.load(f)

# Create Python file content
python_code = "# Auto-generated from insurers JSON\n\nINSURERS_MAPPING = {\n"

# Add each insurer entry, using single quotes around values with double quotes
for insurer in insurers_data:
    # Ensure reg_number is treated as a string with any leading zeros preserved
    reg_number = insurer["reg_number"]
    # Use single quotes for strings containing double quotes
    short_name = insurer["short_name"].replace("'", "\\'")  # Escape any single quotes
    python_code += f'    "{reg_number}": \'{short_name}\',\n'

# Add closing bracket and special values
python_code += "}\n\n"
python_code += "# Add special values\n"
python_code += "INSURERS_MAPPING.update({\n"
python_code += '    "total_market": "Весь рынок",\n'
python_code += '    "others": "Остальные"\n'
python_code += "})\n"

# Write to file
with open('./insurersnew.py', 'w', encoding='utf-8') as f:
    f.write(python_code)


#!/usr/bin/env python3
"""
Script to convert insurance lines JSON files to a Python module.
This combines lines_158_rev.json and lines_162_rev.json into a single Python module.
"""

import json
import pprint
import os

def pretty_format_dict(d, indent=4):
    """Format dictionary with proper indentation and string handling."""
    # Use pprint for nice formatting but fix the strings afterwards
    formatted = pprint.pformat(d, indent=indent, width=100)

    # Fix double quotes inside string literals by using single quotes for strings
    # This is a simplistic approach - more robust handling may be needed for complex data
    lines = []
    for line in formatted.split('\n'):
        # If the line has uneven number of quotes (likely containing a string with quotes)
        # convert the outer quotes to single quotes
        if line.count('"') % 2 != 0 and line.count('"') > 0:
            line = line.replace('"', "'", 1)
            line = line[::-1].replace('"', "'", 1)[::-1]
        lines.append(line)

    return '\n'.join(lines)

def convert_lines_to_python():
    """Convert lines JSON files to a Python module."""
    lines_158_path = './lines_158_rev.json'
    lines_162_path = './lines_162_rev.json'
    output_path = './lines.py'

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Read JSON files
    with open(lines_158_path, 'r', encoding='utf-8') as f158:
        lines_158 = json.load(f158)

    with open(lines_162_path, 'r', encoding='utf-8') as f162:
        lines_162 = json.load(f162)

    # Format as Python code with nice indentation
    lines_158_formatted = pretty_format_dict(lines_158)
    lines_162_formatted = pretty_format_dict(lines_162)

    # Calculate combined dictionary
    combined = {**lines_158, **lines_162}

    # Check for overlapping keys with different values
    overlap_info = []
    for key in set(lines_158.keys()) & set(lines_162.keys()):
        if lines_158[key] != lines_162[key]:
            overlap_info.append(f"# Note: Key '{key}' has different values in 158 and 162 mappings.")
            overlap_info.append(f"# 158: {lines_158[key]}")
            overlap_info.append(f"# 162: {lines_162[key]}")
            overlap_info.append(f"# The 162 value is used in combined mapping.")

    overlap_comment = '\n'.join(overlap_info)

    # Create Python module content
    python_code = f"""# Auto-generated from lines_158_rev.json and lines_162_rev.json

# Lines mapping from Form 0420158
LINES_158_MAPPING = {lines_158_formatted}

# Lines mapping from Form 0420162
LINES_162_MAPPING = {lines_162_formatted}

# Information about overlapping keys with different values
{overlap_comment if overlap_info else '# No overlapping keys with different values found.'}

# Combined mapping (with 162 values taking precedence for overlapping keys)
COMBINED_LINES_MAPPING = {{**LINES_158_MAPPING, **LINES_162_MAPPING}}
"""

    # Write to Python file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(python_code)

    print(f"Conversion complete! Python module created at {output_path}")
    if overlap_info:
        print("WARNING: Some keys overlap with different values. Check the module for details.")

if __name__ == "__main__":
    convert_lines_to_python()