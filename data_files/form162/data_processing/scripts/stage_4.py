import pandas as pd

df = pd.read_csv('intermediate_data/3rd_162_net_interim.csv', 
                 dtype={'insurer': str},
                 parse_dates=['year_quarter'])

group_cols = [col for col in df.columns if col not in ('line_type', 'value')]
df = (df.groupby(group_cols, observed=True)['value']
         .sum()
         .reset_index()
         .sort_values('year_quarter', ascending=True))

'''dates_to_remove = pd.to_datetime([
    '2018-01-01',
    '2018-04-01',
    '2018-07-01',
    '2018-10-01'
])

# Remove rows where year_quarter is in dates_to_remove
df = df[~df['year_quarter'].isin(dates_to_remove)]'''

# Save back to the same file
#df.to_csv('..../data_files/3rd_162_net.csv', index=False)
df.to_csv('intermediate_data/3rd_162_net.csv', index=False)
