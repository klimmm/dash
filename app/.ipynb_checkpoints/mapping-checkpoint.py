import pandas as pd
import json
from typing import Dic
from logging_config import get_logger
from .data_utils import load_json
logger = get_logger(__name__)
import re

def map_insurer_code_to_name(df: pd.DataFrame) -> pd.DataFrame:
    insurer_map_dict = load_json('./preprocess_map_dict/insurer_map.json')
    insurer_map = {item['insurer']: item['name'] for item in insurer_map_dict}
    df['insurer'] = df['insurer'].map(insurer_map).fillna(df['insurer'])
    return df

def map_line_code_to_name(df: pd.DataFrame) -> pd.DataFrame:
    line_map_dict = load_json('./preprocess_map_dict/line_map.json')
    line_map = {item['code']: item['name'] for item in line_map_dict}
    df['linemain'] = df['linemain'].map(line_map).fillna(df['linemain'])
    return df

def map_metric_code_to_name(df: pd.DataFrame) -> pd.DataFrame:
    datatype_map = load_json('./preprocess_map_dict/datatype_map.json')

    df['metric'] = df['metric'].map(datatype_map).fillna(df['metric'])
    return df


def map_insurer(insurer_code: str) -> str:
    # Load the insurer mapping from the JSON file
    with open('./preprocess_map_dict/insurer_map.json', 'r', encoding='utf-8') as f:
        INSURER_MAPPING = {item['insurer']: item['name'] for item in json.load(f)}

    INSURER_MAPPING['total'] = 'Всего по рынку'
    INSURER_MAPPING['others'] = 'Остальные'

    # Regular expressions to match 'top-X' and 'top-Y-benchmark' patterns
    top_pattern = re.compile(r'^top-(\d+)$')
    benchmark_pattern = re.compile(r'^top-(\d+)-benchmark$')

    # Check for 'top-X' pattern
    top_match = top_pattern.match(insurer_code)
    if top_match:
        n = top_match.group(1)
        return f'Топ {n}'

    # Check for 'top-Y-benchmark' pattern
    benchmark_match = benchmark_pattern.match(insurer_code)
    if benchmark_match:
        n = benchmark_match.group(1)
        return f'Топ {n} Бенчмарк'

    # Fallback to the existing mapping or return the original insurer_code
    return INSURER_MAPPING.get(insurer_code, insurer_code)





def map_line(line_code):

    with open('./modified_insurance.json', 'r', encoding='utf-8') as f:
        insurance_data = json.load(f)

    LINE_MAPPING = {category: data['label'] for category, data in insurance_data.items()}

    if isinstance(line_code, list):
        return [LINE_MAPPING.get(code, code) for code in line_code]


    return LINE_MAPPING.get(line_code, line_code)








__all__ = ['map_insurer', 'map_line', 'map_insurer_code_to_name', 'map_line_code_to_name', 'map_metric_code_to_name']


