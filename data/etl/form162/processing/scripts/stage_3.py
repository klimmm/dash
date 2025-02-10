import pandas as pd
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/processing_log.txt'),
        logging.StreamHandler()
    ]
)


# Step 1: Load the CSV file
dtype_dict = {
    'linemain': 'object',
    'insurer': 'object',
    'value': 'float64'
}

df = pd.read_csv('intermediate_data/2nd_162_net.csv', dtype=dtype_dict, parse_dates=['year_quarter'])

# Log initial state
logging.info("Initial data metrics and their quarters:")
for metric in df['metric'].unique():
    quarters = sorted(df[df['metric'] == metric]['year_quarter'].unique())
    #logging.info(f"{metric}: {quarters}")

# Step 2: Rename metrics in the original data
logging.info("\nBefore first renaming - Metrics containing 'premium' or 'commission':")
premium_metrics = df[df['metric'].str.contains('premiums_interm|commission', case=False, na=False)]['metric'].unique()
logging.info(f"Premium/Commission metrics: {premium_metrics}")

df['metric'] = df['metric'].replace({
    'premiums_interm_total': 'premiums_interm',
    'commissions_total': 'commissions_interm'
})

logging.info("\nAfter first renaming - Metrics containing 'premium' or 'commission':")
premium_metrics = df[df['metric'].str.contains('premiums_interm|commission', case=False, na=False)]['metric'].unique()
logging.info(f"Premium/Commission metrics: {premium_metrics}")

# Step 3: Define the aggregation mapping
aggregation_mapping = {  
    'дмс': ['3.2'],
    'осаго': ['6'],
    'нс и оглс': ['3.1', '5'],
    'каско и ж/д': ['4.1.1', '4.1.2'],
    'авиа, море, грузы': ['4.1.3', '4.2.3', '4.1.4', '4.1.5', '4.2.4'],
    'авиа': ['4.1.3', '4.2.3'],
    'море, грузы': ['4.1.4', '4.1.5', '4.2.4'],
    'прочее имущество': ['4.1.6', '4.1.7', '4.1.8'],
    'предпр. и фин риски': ['4.3', '4.4'],
    'прочая ответственность': ['4.2.1', '4.2.2', '4.2.5', '4.2.6', '4.2.7', '4.2.8', '7', '8'],
    'страхование нежизни': [
        '3.1', '3.2', '4.1.1', '6', '4.1.3', '4.2.3', '4.1.4', '4.1.5', 
        '4.2.4', '4.1.2', '4.2.2', '4.4', '4.1.7', '4.3', '4.1.8', 
        '4.1.6', '4.2.1', '4.2.5', '4.2.6', '4.2.7', '4.2.8', '5', '7', '8'
    ],
    'все линии': [
        '3.1', '3.2', '4.1.1', '6', '4.1.3', '4.2.3', '4.1.4', '4.1.5', 
        '4.2.4', '4.1.2', '4.2.2', '4.4', '4.1.7', '4.3', '4.1.8', 
        '4.1.6', '4.2.1', '4.2.5', '4.2.6', '4.2.7', '4.2.8', '5', '7', '8', '1.1', '1.2', '2.1', '2.2'
    ],  
    'страхование жизни': ['1', '2'],
    'прочее сж': ['1.1.1.2', '1.1.2.2', '1.2.1.2', '1.2.2.2', '1.1.1.4', '1.1.2.4', '1.2.1.4', '1.2.2.4', '1.1.1.5', '1.1.2.5', '1.2.1.5', '1.2.2.5'],

    'инвестиционное страхование жизни': ['1.1.1.1', '1.1.2.1', '1.2.1.1', '1.2.2.1'],
    'исж - до 1 года': ['1.1.1.1.1', '1.1.2.1.1', '1.2.1.1.1', '1.2.2.1.1'],
    'исж - от 1 года до 3 лет': ['1.1.1.1.2', '1.1.2.1.2', '1.2.1.1.2', '1.2.2.1.2'],
    'исж - от 3 до 5 лет': ['1.1.1.1.3', '1.1.2.1.3', '1.2.1.1.3', '1.2.2.1.3'],
    'исж - от 5 до 10 лет': ['1.1.1.1.4', '1.1.2.1.4', '1.2.1.1.4', '1.2.2.1.4'],
    'исж - свыше 10 лет': ['1.1.1.1.5', '1.1.2.1.5', '1.2.1.1.5', '1.2.2.1.5'],

    'кредитное страхование жизни': ['1.1.1.2', '1.1.2.2', '1.2.1.2', '1.2.2.2'],
    'ксж - до 1 года': ['1.1.1.2.1', '1.1.2.2.1', '1.2.1.2.1', '1.2.2.2.1'],
    'ксж - от 1 года до 3 лет': ['1.1.1.2.2', '1.1.2.2.2', '1.2.1.2.2', '1.2.2.2.2'],
    'ксж - от 3 до 5 лет': ['1.1.1.2.3', '1.1.2.2.3', '1.2.1.2.3', '1.2.2.2.3'],
    'ксж - от 5 до 10 лет': ['1.1.1.2.4', '1.1.2.2.4', '1.2.1.2.4', '1.2.2.2.4'],
    'ксж - свыше 10 лет': ['1.1.1.2.5', '1.1.2.2.5', '1.2.1.2.5', '1.2.2.2.5'],

    'накопительное страхование жизни': ['1.1.1.3', '1.1.2.3', '1.2.1.3', '1.2.2.3'],
    'нсж - до 1 года': ['1.1.1.3.1', '1.1.2.3.1', '1.2.1.3.1', '1.2.2.3.1'],
    'нсж - от 1 года до 3 лет': ['1.1.1.3.2', '1.1.2.3.2', '1.2.1.3.2', '1.2.2.3.2'],
    'нсж - от 3 до 5 лет': ['1.1.1.3.3', '1.1.2.3.3', '1.2.1.3.3', '1.2.2.3.3'],
    'нсж - от 5 до 10 лет': ['1.1.1.3.4', '1.1.2.3.4', '1.2.1.3.4', '1.2.2.3.4'],
    'нсж - свыше 10 лет': ['1.1.1.3.5', '1.1.2.3.5', '1.2.1.3.5', '1.2.2.3.5'],

    'рисковое страхование жизни': ['1.1.1.4', '1.1.2.4', '1.2.1.4', '1.2.2.4'],
    'рсж - до 1 года': ['1.1.1.4.1', '1.1.2.4.1', '1.2.1.4.1', '1.2.2.4.1'],
    'рсж - от 1 года до 3 лет': ['1.1.1.4.2', '1.1.2.4.2', '1.2.1.4.2', '1.2.2.4.2'],
    'рсж - от 3 до 5 лет': ['1.1.1.4.3', '1.1.2.4.3', '1.2.1.4.3', '1.2.2.4.3'],
    'рсж - от 5 до 10 лет': ['1.1.1.4.4', '1.1.2.4.4', '1.2.1.4.4', '1.2.2.4.4'],
    'рсж - свыше 10 лет': ['1.1.1.4.5', '1.1.2.4.5', '1.2.1.4.5', '1.2.2.4.5'],

    'прочее страхование жизни': ['1.1.1.5', '1.1.2.5', '1.2.1.5', '1.2.2.5'],
    'прсж - до 1 года': ['1.1.1.5.1', '1.1.2.5.1', '1.2.1.5.1', '1.2.2.5.1'],
    'прсж - от 1 года до 3 лет': ['1.1.1.5.2', '1.1.2.5.2', '1.2.1.5.2', '1.2.2.5.2'],
    'прсж - от 3 до 5 лет': ['1.1.1.5.3', '1.1.2.5.3', '1.2.1.5.3', '1.2.2.5.3'],
    'прсж - от 5 до 10 лет': ['1.1.1.5.4', '1.1.2.5.4', '1.2.1.5.4', '1.2.2.5.4'],
    'прсж - свыше 10 лет': ['1.1.1.5.5', '1.1.2.5.5', '1.2.1.5.5', '1.2.2.5.5'],

    'пенсионное страхование жизни': ['2.1', '2.2'],
    'пенсж - до 1 года': ['2.1.1', '2.2.1'],
    'пенсж - от 1 года до 3 лет': ['2.1.2', '2.2.2'],
    'пенсж - от 3 до 5 лет': ['2.1.3', '2.2.3'],
    'пенсж - от 5 до 10 лет': ['2.1.4', '2.2.4'],
    'пенсж - свыше 10 лет': ['2.1.5', '2.2.5'],
}

linemains_to_exclude = [ 
                        '3.2', '6', '3', '4', '4.1', '4.2',


                        '8.1',
                        '8.1.1',
                        '8.1.2',
                        '8.2',
                        '8.2.1',
                        '8.2.2',
                        '8.3',
                        '8.4',
                        '8.4.1',
                        '8.4.2',
                        '8.5',
                        '8.5.1',
                        '8.5.2',
                        '8.5.3',
                        '8.5.4',
                        '8.6',
                        '8.7',
                        '8.8',
                        '7.1',
                        '7.2',
                        '7.3',
                        '7.4',

                        '1', '2', '1.1', '1.1.1.1', '1.1.1.1.1', '1.1.1.1.2', '1.1.1.1.3', 
                        '1.1.1.1.4', '1.1.1.1.5', '1.1.1.2', '1.1.1.2.1', '1.1.1.2.2', 
                        '1.1.1.2.3', '1.1.1.2.4', '1.1.1.2.5', '1.1.1.3', '1.1.1.3.1', 
                        '1.1.1.3.2', '1.1.1.3.3', '1.1.1.3.4', '1.1.1.3.5', '1.1.1.4', 
                        '1.1.1.4.1', '1.1.1.4.2', '1.1.1.4.3', '1.1.1.4.4', '1.1.1.4.5', 
                        '1.1.1.5', '1.1.1.5.1', '1.1.1.5.2', '1.1.1.5.3', '1.1.1.5.4', 
                        '1.1.1.5.5', '1.1.2.1', '1.1.2.1.1', '1.1.2.1.2', '1.1.2.1.3', 
                        '1.1.2.1.4', '1.1.2.1.5', '1.1.2.2', '1.1.2.2.1', '1.1.2.2.2', 
                        '1.1.2.2.3', '1.1.2.2.4', '1.1.2.2.5', '1.1.2.3', '1.1.2.3.1', 
                        '1.1.2.3.2', '1.1.2.3.3', '1.1.2.3.4', '1.1.2.3.5', '1.1.2.4', 
                        '1.1.2.4.1', '1.1.2.4.2', '1.1.2.4.3', '1.1.2.4.4', '1.1.2.4.5', 
                        '1.1.2.5', '1.1.2.5.1', '1.1.2.5.2', '1.1.2.5.3', '1.1.2.5.4', 
                        '1.1.2.5.5', '1.2', '1.2.1.1', '1.2.1.1.1', '1.2.1.1.2', '1.2.1.1.3', 
                        '1.2.1.1.4', '1.2.1.1.5', '1.2.1.2', '1.2.1.2.1', '1.2.1.2.2', '1.2.1.2.3', 
                        '1.2.1.2.4', '1.2.1.2.5', '1.2.1.3', '1.2.1.3.1', '1.2.1.3.2', '1.2.1.3.3', 
                        '1.2.1.3.4', '1.2.1.3.5', '1.2.1.4', '1.2.1.4.1', '1.2.1.4.2', '1.2.1.4.3', 
                        '1.2.1.4.4', '1.2.1.4.5', '1.2.1.5', '1.2.1.5.1', '1.2.1.5.2', '1.2.1.5.3', 
                        '1.2.1.5.4', '1.2.1.5.5', '1.2.2.1', '1.2.2.1.1', '1.2.2.1.2', '1.2.2.1.3', 
                        '1.2.2.1.4', '1.2.2.1.5', '1.2.2.2', '1.2.2.2.1', '1.2.2.2.2', '1.2.2.2.3', 
                        '1.2.2.2.4', '1.2.2.2.5', '1.2.2.3', '1.2.2.3.1', '1.2.2.3.2', '1.2.2.3.3', 
                        '1.2.2.3.4', '1.2.2.3.5', '1.2.2.4', '1.2.2.4.1', '1.2.2.4.2', '1.2.2.4.3', 
                        '1.2.2.4.4', '1.2.2.4.5', '1.2.2.5', '1.2.2.5.1', '1.2.2.5.2', '1.2.2.5.3', 
                        '1.2.2.5.4', '1.2.2.5.5', '2.1', '2.1', '2.1.1', '2.1.2', '2.1.3', '2.1.4', 
                        '2.1.5', '2.2', '2.2', '2.2.1', '2.2.2', '2.2.3', '2.2.4', '2.2.5'
                       ] 


# Step 5: Identify grouping columns
grouping_columns = [col for col in df.columns if col not in ['linemain', 'value']]

# Step 6: Aggregate and create new rows
new_rows = []
for new_linemain, linemain_list in aggregation_mapping.items():
    filtered_df = df[df['linemain'].isin(linemain_list)]
    aggregated = filtered_df.groupby(grouping_columns, as_index=False)['value'].sum()
    aggregated['linemain'] = new_linemain
    new_rows.append(aggregated)

# Combine all new rows into a single DataFrame
aggregated_df = pd.concat(new_rows, ignore_index=True)

# Step 7: Combine the original and aggregated DataFrames
df = pd.concat([df, aggregated_df], ignore_index=True)

# Step 8: Filter out excluded lines
df = df[~df['linemain'].isin(linemains_to_exclude)]

# Before electronic/nonelectric aggregation
logging.info("\nBefore electronic/nonelectric aggregation:")
for metric in ['premiums_interm_nonelec', 'premiums_interm_electronic', 'premiums_interm']:
    if metric in df['metric'].unique():
        quarters = sorted(df[df['metric'] == metric]['year_quarter'].unique())
        logging.info(f"{metric}: {quarters}")

# Step 9: Aggregate metrics
metric_grouping_cols = [col for col in df.columns if col not in ['metric', 'value']]

# Aggregate premiums_interm
premiums_mask = df['metric'].isin(['premiums_interm_nonelec', 'premiums_interm_electronic'])
premiums_agg = df[premiums_mask].groupby(metric_grouping_cols, as_index=False)['value'].sum()
premiums_agg['metric'] = 'premiums_interm'

# Log the quarters present in aggregated data
logging.info("\nQuarters present in aggregated premiums_interm:")
quarters = sorted(premiums_agg['year_quarter'].unique())
logging.info(f"Aggregated premiums_interm: {quarters}")

# Aggregate commissions
commissions_mask = df['metric'].isin(['commissions_nonelec', 'commissions_electronic'])
commissions_agg = df[commissions_mask].groupby(metric_grouping_cols, as_index=False)['value'].sum()
commissions_agg['metric'] = 'commissions_interm'

# Remove rows with old metrics and add aggregated ones
df = df[~df['metric'].isin(['premiums_interm_nonelec', 'premiums_interm_electronic', 
                           'commissions_nonelec', 'commissions_electronic'])]
df = pd.concat([df, premiums_agg, commissions_agg], ignore_index=True)

logging.info("\nAfter aggregation and concat - Quarters for premiums_interm:")
quarters = sorted(df[df['metric'] == 'premiums_interm']['year_quarter'].unique())
logging.info(f"premiums_interm: {quarters}")

# Step 10: Final renaming check
logging.info("\nBefore final renaming:")
for metric in df['metric'].unique():
    if 'premiums_' in metric.lower() or 'commission' in metric.lower():
        quarters = sorted(df[df['metric'] == metric]['year_quarter'].unique())
        logging.info(f"{metric}: {quarters}")

df['metric'] = df['metric'].replace({
    'premiums_interm_total': 'premiums_interm',
    'commissions_total': 'commissions_interm'
})

logging.info("\nAfter final renaming:")
for metric in df['metric'].unique():
    if 'premiums_' in metric.lower() or 'commission' in metric.lower():
        quarters = sorted(df[df['metric'] == metric]['year_quarter'].unique())
        logging.info(f"{metric}: {quarters}")

# Calculate totals
group_columns = [col for col in df.columns if col not in ['insurer', 'value']]
df_total = df.groupby(group_columns)['value'].sum().reset_index()
df_total['insurer'] = 'total'

# Combine original data with totals
df_new = pd.concat([df, df_total], ignore_index=True)

# Final check on df_new
logging.info("\nFinal data - Quarters for premiums_interm:")
quarters = sorted(df_new[df_new['metric'] == 'premiums_interm']['year_quarter'].unique())
logging.info(f"premiums_interm final: {quarters}")

quarters = df[df['metric'] == 'premiums_interm']['year_quarter'].unique()
sorted_quarters = sorted(quarters)
print("Total quarters:", len(sorted_quarters))
print("\nChecking for duplicates:")
from collections import Counter
counts = Counter(quarters)
duplicates = {q: count for q, count in counts.items() if count > 1}
if duplicates:
    print("Found duplicates:", duplicates)
else:
    print("No duplicates found")

# Save to CSV
# df_new.to_csv('../dash-table-app/data_files/3rd_162_net.csv', index=False)
df_new.to_csv('intermediate_data/3rd_162_net_interim.csv', index=False)