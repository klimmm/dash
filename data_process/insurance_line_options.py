

from config.main_config import LINES_162_DICTIONARY, LINES_158_DICTIONARY
from config.logging_config import get_logger
from data_process.data_utils import load_json
logger = get_logger(__name__)



def get_insurance_line_options(reporting_form, level=1, indent_char="\u2003"):

    category_structure = load_json(LINES_162_DICTIONARY) if reporting_form == '0420162' else load_json(LINES_158_DICTIONARY)

    def clean_label(label):
        """Remove 'Добровольное' from the label and handle extra spaces"""
        return ' '.join(label.replace('Добровольное', '').split())

    def traverse_categories(code, current_level=0, max_level=None):
        # Check if category exists in structure
        if code not in category_structure:
            return []

        if max_level is not None and current_level > max_level:
            return []

        result = []
        # Add current category
        label = category_structure[code].get('label', f"Category {code}")
        cleaned_label = clean_label(label)
        indentation = indent_char * current_level
        result.append({
            'label': f"{indentation}{cleaned_label}",
            'value': code
        })

        # Add children if within max_level
        if max_level is None or current_level < max_level:
            # Safely get children, defaulting to empty list if none exist
            children = category_structure[code].get('children', [])
            # Only traverse existing children
            for child in children:
                if child in category_structure:  # Extra safety check
                    result.extend(traverse_categories(child, current_level + 1, max_level))

        return result

    # Verify root category exists
    root = "все линии"
    if root not in category_structure:
        return []  # Return empty list if root category doesn't exist

    # Start with root category and traverse
    return traverse_categories(root, 0, level)