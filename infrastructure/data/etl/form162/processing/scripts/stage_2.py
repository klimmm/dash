import pandas as pd
import logging
from stage_2_line_maps import lines_custom_just_aggregate, lines_custom_just_exclude, lines_custom_aggregate_and_drop

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.FileHandler('logs/logs_2nd_stage.log'),
        logging.StreamHandler()
    ]
)

file_path = 'intermediate_data/1st_162_net.csv'
# Load data with logging
logging.info("Starting data processing")
df = pd.read_csv(file_path)
# Date conversion
logging.info("Converting dates")
df['year_quarter'] = pd.to_datetime(df['year'].astype(str) + '-' +
                                    ((df['quarter'] - 1) * 3 + 1).astype(str) + '-01')
df = df.drop(columns=['year', 'quarter'])
df = df.rename(columns={'insurance_line': 'line', 'datatype': 'metric'})
df = df.replace({'insurer': {'all_insurers': 'total'}})
mask = (df['insurer'] == 'total') & (df['line'] == '5') & (
    df['year_quarter'] >= pd.Timestamp('2021-10-01'))
df = pd.concat([df, df[mask].assign(insurer='0000')], ignore_index=True)

df = df[(df['value'] != 0) & (df['value'].notna())]
df = df[(df['year_quarter'] <= pd.Timestamp('2025-01-01'))]
df = df[(df['year_quarter'] >= pd.Timestamp('2019-01-01'))]

df['value'] = df['value'] / 1_000_000

line_group_cols = [col for col in df.columns if col not in ['line', 'value']]
new_rows = []
lines_to_remove = []  # Keep track of all lines that will be aggregated
logging.info(f"lines unique: {df['line'].unique() }")

for new_line, line_list in lines_custom_aggregate_and_drop.items():
    filtered_df = df[df['line'].isin(line_list)]
    aggregated = filtered_df.groupby(line_group_cols,
                                     as_index=False)['value'].sum()
    aggregated['line'] = new_line
    new_rows.append(aggregated)
    lines_to_remove.extend(line_list)
logging.info(f"lines_to_remove{lines_to_remove}")

for new_line, line_list in lines_custom_just_aggregate.items():
    filtered_df = df[df['line'].isin(line_list)]
    aggregated = filtered_df.groupby(line_group_cols,
                                     as_index=False)['value'].sum()
    aggregated['line'] = new_line
    new_rows.append(aggregated)
logging.info(f"lines_custom_just_exclude{lines_custom_just_exclude}")
lines_to_remove.extend(lines_custom_just_exclude)
logging.info(f"lines_to_remove{lines_to_remove}")

filtered_df = df[~df['line'].isin(lines_to_remove)]

df = pd.concat([filtered_df] + new_rows, ignore_index=True)
logging.info(f"lines unique: {df['line'].unique() }")

metric_mapping = {
    'premiums_interm_total': 'premiums_interm',
    'commissions_total': 'commissions_interm',
    'premiums_interm_nonelec': 'premiums_interm',
    'premiums_interm_electronic': 'premiums_interm',
    'commissions_nonelec': 'commissions_interm',
    'commissions_electronic': 'commissions_interm'
}
df = df.copy()
df.loc[df['metric'].isin(
    metric_mapping.keys()), 'metric'] = df.loc[df['metric'].isin(
        metric_mapping.keys()), 'metric'].map(metric_mapping)
metric_group_cols = [col for col in df.columns if col != 'value']
df_new = df.groupby(metric_group_cols, as_index=False)['value'].sum()

df_new.to_csv('intermediate_data/3rd_162_net.csv', index=False)