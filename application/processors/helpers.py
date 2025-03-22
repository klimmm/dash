def filter_by_column(df, column, values, operator='in'):
    if operator == 'in':
        return df[df[column].isin(values)]
    elif operator == 'eq':
        return df[df[column] == values]
    elif operator == 'lt':
        return df[df[column] < values]
    elif operator == 'lte':
        return df[df[column] <= values]
    elif operator == 'gt':
        return df[df[column] > values]
    elif operator == 'gte':
        return df[df[column] >= values]
    elif operator == 'not_in':
        return df[~df[column].isin(values)]
    elif operator == 'not_eq':
        return df[df[column] != values]
    else:
        raise ValueError(f"Unsupported operator: {operator}")