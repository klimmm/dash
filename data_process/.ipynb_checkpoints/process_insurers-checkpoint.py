import pandas as pd
from typing import Optional, List, Any, Se
import logging

def process_insurers_data(df: pd.DataFrame, top_n_list: List[int], main_insurer: List[str], compare_insurers: List[str], end_quarter: str) -> pd.DataFrame:
    # Define categories
    logging.info(f"Unique insurers df before process insurers: {df['insurer'].unique().tolist()}")

    benchmark_metric = 'direct_premiums'
    benchmark_insurers = {f"top-{n}-benchmark" for n in top_n_list}
    top_n_rows = {f"top-{n}" for n in top_n_list}
    total_rows = {'total'}
    others_rows = {'others'}
    compare_insurers = [item for sublist in compare_insurers for item in (sublist if isinstance(sublist, list) else [sublist])]
    main_insurer = [item for sublist in main_insurer for item in (sublist if isinstance(sublist, list) else [sublist])]
    selected_insurers = (main_insurer or []) + (compare_insurers or [])

    group_columns = [col for col in df.columns if col not in ['insurer', 'value']]

    dataframes_to_concat = []

    logging.info(f"compare_insurers: {compare_insurers}")
    logging.info(f"main_insurer: {main_insurer}")
    logging.info(f"selected_insurers: {selected_insurers}")


    # Calculate top_n rows
    if len(df['insurer'].unique()) > 1:

        insurers_to_exclude = top_n_rows | benchmark_insurers | others_rows | total_rows
        df_top_n_row = df[~df['insurer'].isin(insurers_to_exclude)]
        logging.info(f"Unique insurers df afterfilter to exculde for top n calc: {df['insurer'].unique().tolist()}")

        for n in top_n_list:
            df_top_n_row = df.groupby(group_columns).apply(lambda x: x.nlargest(n, 'value'))
            df_top_n_row = df_top_n_row.reset_index(drop=True)
            df_top_n_row = df_top_n_row.groupby(group_columns)['value'].sum().reset_index()
            df_top_n_row['insurer'] = f'top-{n}'
            dataframes_to_concat.append(df_top_n_row)
            logging.info(f"dataframes_to_concat: {dataframes_to_concat}")


    # Calculate total rows
    if 'total' not in df['insurer'].unique():
        insurers_to_exclude = top_n_rows | benchmark_insurers | others_rows
        df_total = df[~df['insurer'].isin(insurers_to_exclude)]
        df_total = df_total.groupby(group_columns)['value'].sum().reset_index()
        df_total['insurer'] = 'total'
        dataframes_to_concat.append(df_total)
        #logging.info(f"dataframes_to_concat: {dataframes_to_concat}")

    # Calculate benchmark rows
    if any(insurer in benchmark_insurers for insurer in selected_insurers):
        insurers_to_exclude = set(main_insurer) | benchmark_insurers | top_n_rows | total_rows | others_rows
        end_quarter_dt = pd.to_datetime(end_quarter)

        end_quarter_df = df[
            (~df['insurer'].isin(insurers_to_exclude)) &
            (df['year_quarter'] == end_quarter_dt) &
            (df['metric'] == benchmark_metric)
        ]

        for n in top_n_list:
            benchmark_insurers_list = end_quarter_df.groupby('insurer')['value'].sum().nlargest(n).index.tolist()
            df_benchmark_n = df[df['insurer'].isin(benchmark_insurers_list)]
            df_benchmark_n = df_benchmark_n.groupby(group_columns)['value'].sum().reset_index()
            df_benchmark_n['insurer'] = f'top-{n}-benchmark'
            dataframes_to_concat.append(df_benchmark_n)

    # Calculate others rows
    if any(insurer in others_rows for insurer in selected_insurers):
        selected_insurers = [insurer for insurer in selected_insurers if insurer not in others_rows]
        insurers_to_exclude = set(selected_insurers) | top_n_rows | benchmark_insurers | total_rows
        df_others = df[~df['insurer'].isin(insurers_to_exclude)]
        df_others = df_others.groupby(group_columns)['value'].sum().reset_index()

        selected_top_n = next((f'top-{n}' for n in top_n_list if f'top-{n}' in selected_insurers or f'top-{n}-benchmark' in selected_insurers), None)

        if selected_top_n:
            df_top_n = df[df['insurer'] == selected_top_n]
            df_others = df_others.merge(df_top_n[group_columns + ['value']],
                                        on=group_columns, how='left', suffixes=('', '_top_n'))
            df_others['value'] = df_others['value'] - df_others['value_top_n'].fillna(0)
            df_others = df_others.drop(columns=['value_top_n'])

        df_others['insurer'] = 'others'
        df_others = df_others[df_others['value'] > 0]
        dataframes_to_concat.append(df_others)

    insurers_to_exclude_original_df = benchmark_insurers | top_n_rows | total_rows | others_rows
    original_df = df[~df['insurer'].isin(insurers_to_exclude_original_df)]
    dataframes_to_concat.insert(0, original_df)  # Add original_df at the beginning of the lis

    # Concatenate all DataFrames
    result_df = pd.concat(dataframes_to_concat, ignore_index=True)
    logging.info(f"Unique insurers df after process insurers: {result_df['insurer'].unique().tolist()}")

    return result_df



