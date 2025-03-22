import pandas as pd
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_xlsx_to_csv():
    # Input and output directories
    xlsx_dir = 'xlsx_files'
    csv_dir = 'csv_files'

    # Create CSV directory if it doesn't exist
    os.makedirs(csv_dir, exist_ok=True)

    # Get all xlsx files
    xlsx_files = [f for f in os.listdir(xlsx_dir) if f.endswith('.xlsx')]

    for xlsx_file in xlsx_files:
        try:
            # Construct full file paths
            xlsx_path = os.path.join(xlsx_dir, xlsx_file)
            csv_file = xlsx_file.replace('.xlsx', '.csv')
            csv_path = os.path.join(csv_dir, csv_file)

            # Read Excel and write CSV
            logger.info(f"Converting {xlsx_file} to CSV...")
            df = pd.read_excel(xlsx_path)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')  # utf-8-sig for proper Russian character encoding
            logger.info(f"Successfully converted {xlsx_file} to {csv_file}")

        except Exception as e:
            logger.error(f"Error converting {xlsx_file}: {str(e)}")

if __name__ == "__main__":
    convert_xlsx_to_csv()