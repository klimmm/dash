import pandas as pd


def add_top_n_rows(df, top_n_list=[5, 10, 20]):

    group_by_cols = [col for col in df.columns if col not in ['insurer', 'value']]

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

    return result_df