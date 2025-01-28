import logging

# Basic logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)


def handle_parent_child_selections(selected_categories, category_structure, detailize=False):
    logger.info(f"Starting handle_parent_child_selections with selected categories: {selected_categories}")
    logger.info(f"Detailize flag: {detailize}")

    def get_immediate_children(category):
        return set(category_structure[category].get('children', []))

    def get_all_descendants(category):
        descendants = set()
        to_process = get_immediate_children(category)

        while to_process:
            current = to_process.pop()
            descendants.add(current)
            # Add children of current category to processing queue
            if current in category_structure:
                to_process.update(get_immediate_children(current))

        return descendants

    if not detailize:
        new_selected = set(selected_categories)
        # Remove all descendants if their ancestor is selected
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                descendants = get_all_descendants(category)
                removed_descendants = new_selected.intersection(descendants)
                new_selected.difference_update(removed_descendants)
                if removed_descendants:
                    logger.debug(f"Removed descendants of {category}: {removed_descendants}")
    else:
        new_selected = set()
        # Add children for categories that have them, or keep the category if it's a leaf
        for category in selected_categories:
            if category in category_structure and category_structure[category].get('children'):
                children = get_immediate_children(category)
                new_selected.update(children)
                logger.info(f"Detailized {category}. Added children: {children}")
            else:
                new_selected.add(category)
                logger.info(f"Category {category} has no children, keeping it as is")

    final_selected = list(new_selected)
    logger.info(f"Final selected categories: {final_selected}")
    return final_selected


