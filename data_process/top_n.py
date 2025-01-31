import pandas as pd

from data_process.io import save_df_to_csv


def add_top_n_rows(df, top_n_list=[5, 10, 20]):

    group_by_cols = [col for col in df.columns if col not in ['insurer', 'value']]
    save_df_to_csv(df, "df_before_top_n.csv")
    dfs = [df.copy()]

    for n in top_n_list:
        if n != 999:
            # Filter out excluded insurers and get top N
            top_n_df = (
                df[df['insurer'] != 'total']
                .groupby(group_by_cols)
                .apply(lambda x: x.nlargest(n, 'value'))
                .reset_index(drop=True)
                .groupby(group_by_cols, observed=True)['value']
                .sum()
                .reset_index()
            )

            top_n_df['insurer'] = f'top-{n}'
            dfs.append(top_n_df)

    result_df = pd.concat(dfs, ignore_index=True)
    save_df_to_csv(result_df, "df_after_top_n.csv")

    return result_df