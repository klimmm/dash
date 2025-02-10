# processors.py
from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import re
from stage_1_config import Config


logger = logging.getLogger(__name__)


class FileProcessor(ABC):
    @abstractmethod
    def read_file(self, filepath: Path) -> pd.DataFrame:
        pass

    @abstractmethod
    def process_file(
        self, 
        df: pd.DataFrame,
        filepath: Path,
        config: Config
    ) -> Optional[pd.DataFrame]:
        pass


class HeaderProcessor:
    def process_header_rows(self, dataframe: pd.DataFrame, pattern_row_index: int) -> List[str]:
        header_rows = dataframe.iloc[:pattern_row_index].values.tolist()
        logger.critical(f"Original header rows: {header_rows}")

        header_rows = self.apply_special_replacements(header_rows)

        logger.critical(f" header rows afre special replacements: {header_rows}")

        header_rows = self.vertical_fill(header_rows)
        header_rows = self.horizontal_fill_agro(header_rows)
        header_rows = self.horizontal_fill_life(dataframe, header_rows)
        combined_header = self.combined_header(dataframe, header_rows)
        #logger.critical(f" combined header: {combined_header}")

        return combined_header

    def apply_special_replacements(self, header_rows: List[List[str]]) -> List[List[str]]:
        replacements1 = {
            'Добровольное страхование прочего имущества юридических лиц': 'добровольное страхование имущества юридических лиц кроме транспортных средств грузов и сельскохозяйственного страхования',
            'Добровольное страхование прочего имущества граждан': 'добровольное страхование имущества граждан кроме транспортных средств грузов и сельскохозяйственного страхования'
        }
        replacements2 = {
            'прочего имущества': 'добровольное страхование имущества'  # Note the space after 'имущества'
        }
        replacements3 = {
            'юридических лиц': 'юридических лиц кроме транспортных средств грузов и сельскохозяйственного страхования',
            'граждан': 'граждан кроме транспортных средств грузов и сельскохозяйственного страхования'
        }

        logger.info("Starting apply_special_replacements")

        def replace_pair(row, start, end, replacements):
            if all(pd.isna(cell) or cell.strip() == '' for cell in row[start+1:end]):
                logger.info(f"Replacing pair in row:")
                logger.info(f"  Old value at start: {row[start]}")
                logger.info(f"  New value at start: {replacements[row[start]]}")
                logger.info(f"  Old value at end: {row[end]}")
                logger.info(f"  New value at end: {replacements[row[end]]}")

                row[start] = replacements[row[start]]
                row[end] = replacements[row[end]]
            return row

        for i, row in enumerate(header_rows):
            row = [str(cell).strip() if pd.notna(cell) else cell for cell in row] # Convert to string and strip

            # Case a: Replace using replacements1
            indices1 = [j for j, cell in enumerate(row) if cell in replacements1]
            if len(indices1) == 2:
                row = replace_pair(row, indices1[0], indices1[1], replacements1)

            # Case b: Replace 'прочего имущества ' pairs (note the space)
            indices2 = [j for j, cell in enumerate(row) if cell == 'прочего имущества ']
            if len(indices2) == 2:
                row = replace_pair(row, indices2[0], indices2[1], replacements2)

            # Case c: Replace 'юридических лиц' and 'граждан' pairs
            indices3 = [j for j, cell in enumerate(row) if cell in replacements3]
            if len(indices3) == 2:
                row = replace_pair(row, indices3[0], indices3[1], replacements3)

            header_rows[i] = row

        logger.info("Finished apply_special_replacements")
        return header_rows

    def vertical_fill(self, header_rows):
        logger.info("Starting vertical fill process")

        allowed_values_vertical = ['Всего', 'всего', 'вссего']
        for j in range(len(header_rows[0])):
            last_valid_value = None
            for i in range(len(header_rows)):
                cell = header_rows[i][j]
                if pd.isna(cell) or str(cell).strip() == '':
                    if last_valid_value is not None:
                        header_rows[i][j] = last_valid_value
                else:
                    cell_value = str(cell).strip()
                    if cell_value in allowed_values_vertical:
                        last_valid_value = cell_value
                    else:
                        last_valid_value = None

        logger.info("Vertical fill process completed")

        return header_rows

    def horizontal_fill_agro(self, header_rows):
        logger.info("Starting horizontal fill agro process")

        allowed_values_horizontal_agro = [
            'Добровольное сельскохозяйственное страхование, осуществляемое без государственной поддержки' 
        ]
        for i, row in enumerate(header_rows):
            last_valid_value_horizontal_agro = None
            for j, cell in enumerate(row):
                if pd.isna(cell) or str(cell).strip() == '':
                    if last_valid_value_horizontal_agro is not None:
                        header_rows[i][j] = last_valid_value_horizontal_agro
                else:
                    cell_value = str(cell).strip()
                    if cell_value in allowed_values_horizontal_agro:
                        last_valid_value_horizontal_agro = cell_value
                    else:
                        last_valid_value_horizontal_agro = None

        logger.info("Horizontal fill agro process completed")

        return header_rows

    def horizontal_fill_life(self, dataframe: pd.DataFrame, header_rows):
        logger.info("Starting horizontal fill life process")

        allowed_values_horizontal_life = [
            'Добровольное страхование жизни (кроме пенсионного страхования)',
            'Добровольное страхование жизни на случай смерти, дожития до определенного возраста или срока либо наступления иного события',
            'Добровольное страхование жизни с условием периодических страховых выплат (ренты, аннуитетов) и (или) с участием страхователя в инвестиционном доходе страховщика',
            'Добровольное пенсионное страхование',
            'Добровольное пенсионное страхование с единовременной уплатой страховой премии',
            'Добровольное страхование жизни на случай смерти, дожития до определенного возраста или срока либо наступления иного события с единовременной уплатой страховой премии',
            'Добровольное страхование жизни на случай смерти, дожития до определенного возраста или срока либо наступления иного события с уплатой страховой премии в рассрочку',
            'Добровольное страхование жизни с условием периодических страховых выплат (ренты, аннуитетов) и (или) с участием страхователя в инвестиционном доходе страховщика с единовременной уплатой страховой премии',
            'Добровольное страхование жизни с условием периодических страховых выплат (ренты, аннуитетов) и (или) с участием страхователя в инвестиционном доходе страховщика с уплатой страховой премии в рассрочку',
            'Инвестиционное страхование жизни',
            'Кредитное страхование жизни',
            'Накопительное страхование жизни',
            'Рисковое страхование жизни',
            'Прочее страхование жизни',
            'Добровольное пенсионное страхование с единовременной уплатой страховой премии',
            'Добровольное пенсионное страхование с уплатой страховой премии в рассрочку'
        ]

        num_columns = len(dataframe.columns)

        max_fill_index = -1
        for i, row in enumerate(header_rows):
            last_allowed_index = -1
            row_max_fill_index = -1
            for j, cell in enumerate(row):
                if pd.notna(cell):
                    cell_value = str(cell).strip()
                    if cell_value in allowed_values_horizontal_life:
                        last_allowed_index = j
                        row_max_fill_index = j
                    elif last_allowed_index != -1:
                        break

                if last_allowed_index != -1:
                    row_max_fill_index = j

            if last_allowed_index != -1:
                max_fill_index = row_max_fill_index
                logging.warning(f"Max fill index set to {max_fill_index} based on row {i + 1}")
                break

        if max_fill_index == -1:
            #logging.warning("No allowed values found in any row. Max fill index not set.")
            max_fill_index = num_columns - 1

        for i, row in enumerate(header_rows):
            last_valid_value = None
            for j in range(min(max_fill_index + 1, num_columns)):
                cell = row[j] if j < len(row) else None
                if pd.isna(cell) or str(cell).strip() == '':
                    if last_valid_value is not None:
                        if j >= len(row):
                            row.append(last_valid_value)
                        else:
                            row[j] = last_valid_value
                else:
                    cell_value = str(cell).strip()
                    if cell_value in allowed_values_horizontal_life:
                        last_valid_value = cell_value
                    else:
                        last_valid_value = None
        logging.info(f"Max fill index: {max_fill_index}")

        return header_rows

    def combined_header(self, dataframe: pd.DataFrame, header_rows: List[List[Any]]) -> List[str]:
        num_columns = len(dataframe.columns)
        combined_header = []
        for i in range(num_columns):
            column_values = [str(row[i]).strip() for row in header_rows if i < len(row) and pd.notna(row[i]) and str(row[i]).strip()]
            combined_header.append(' '.join(column_values) if column_values else f"Column_{i+1}")
        return combined_header


class HeaderCleaner:
    def __init__(self, exact_matches: Dict[str, str], header_replacements: Dict[str, str], value_replacements: Dict[str, str]):
        self.exact_matches = exact_matches
        self.header_replacements = header_replacements
        self.value_replacements = value_replacements

    def standardize_value(self, value: Any) -> str:
        try:
            value_str = str(value).lower()
            value_str = re.sub(r'\bUnnamed(?:\s*:\s*\d+)?\b', '', value_str, flags=re.IGNORECASE)
            value_str = value_str.replace('единица', '').replace('nan', '')
            value_str = value_str.translate(str.maketrans('', '', '*«»-,():"'))
            value_str = ' '.join(value_str.split())
            value_str = re.sub(r'\s*\d+(\s+\d+)*$', '', value_str)

            # Apply replacements from JSON file
            for old, new in self.value_replacements.items():
                value_str = value_str.replace(old, new)

            return value_str.strip()

        except Exception as error:
            logger.warning(f'Error in standardize_value: {str(error)}')
            return str(value)

    def clean_and_standardize_headers(self, combined_header: List[str]) -> List[str]:
        logger.info("Starting header cleaning and standardization")

        lowercase_headers = [value.lower() if i >= 1 else value for i, value in enumerate(combined_header)]
        cleaned_header = [self.standardize_value(value) for value in lowercase_headers]
        cleaned_header = [self.replace_exact_matches(header) for header in cleaned_header]
        cleaned_header = [self.clean_remaining_vsego(header) for header in cleaned_header]
        final_headers = [self.apply_specific_replacements(header) for header in cleaned_header]

        logger.info("Finished header cleaning and standardization")

        return final_headers

    def replace_exact_matches(self, header: str) -> str:
        lowered_header = header.lower().strip()
        replacement = self.exact_matches.get(lowered_header, header)
        if replacement != header:
            logger.info(f"Replaced '{header}' with '{replacement}'")
        return replacement

    @staticmethod
    def clean_remaining_vsego(header: str) -> str:
        original_header = header
        cleaned_header = (header.replace('всего', '')
                                .replace('Всего', '')
                                .replace('вссего', '')
                                .strip())

        if cleaned_header != original_header:
            logger.info(f"Cleaned header: '{original_header}' -> '{cleaned_header}'")

        return cleaned_header

    def apply_specific_replacements(self, header: str) -> str:
        original_header = header
        lowered_header = header.lower().strip()
        replaced_header = self.header_replacements.get(lowered_header, header)

        if replaced_header != original_header:
            logger.info(f"Replaced header: '{original_header}' -> '{replaced_header}'")

        return replaced_header


class CSVProcessor(FileProcessor):
    def __init__(self, exact_matches: Dict[str, str], header_replacements: Dict[str, str], value_replacements: Dict[str, str]):
        self.header_processor = HeaderProcessor()
        self.header_cleaner = HeaderCleaner(exact_matches, header_replacements, value_replacements)
        self.value_replacements = value_replacements

    def read_file(self, filepath: Path) -> pd.DataFrame:
        try:
            return pd.read_csv(filepath, header=None, encoding='utf-8')
        except (IOError, pd.errors.EmptyDataError) as error:
            logger.error(f'Error reading file {filepath}: {str(error)}')
            return pd.DataFrame()

    def find_pattern_row(self, dataframe: pd.DataFrame) -> Tuple[Optional[List[str]], Optional[int]]:
        for index, row in dataframe.iterrows():
            if any('ИТОГО' in str(cell).upper() for cell in row):
                return [str(cell) for cell in row], index
        return None, None

    def process_file(self, df: pd.DataFrame, filepath: Path, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        if df.empty:
            return None

        try:
            pattern_row, pattern_row_index = self.find_pattern_row(df)
            if pattern_row is None:
                logger.warning(f'No pattern row found in file: {filepath}')
                return None

            combined_header = self.header_processor.process_header_rows(df, pattern_row_index)
            cleaned_header = self.header_cleaner.clean_and_standardize_headers(combined_header)

            processed_df = self.process_data_rows(df, pattern_row_index, cleaned_header)
            processed_df = self.apply_value_replacements(processed_df)

            metadata_values = self.extract_metadata(combined_header[0] if combined_header else '', config['datatype_mapping'])

            df_long = self.melt_dataframe(processed_df)
            return self.add_metadata_to_dataframe(df_long, metadata_values)
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {str(e)}")
            return None

    def apply_value_replacements(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            df[col] = df[col].replace(self.value_replacements)
        return df

    def process_data_rows(self, df: pd.DataFrame, pattern_row_index: int, cleaned_header: List[str]) -> pd.DataFrame:
        data_rows = df.iloc[pattern_row_index:].values.tolist()
        return pd.DataFrame(data_rows, columns=cleaned_header)
    
    def extract_metadata(self, combined_header: str, datatype_mapping: Dict[str, str]) -> Dict[str, str]:
        parts = {'datatype': '', 'year': '', 'quarter': ''}
        header_text = combined_header.lower()
    
        # Try to find matching datatype
        matched_datatype = None
        for key, value in datatype_mapping.items():
            if key in header_text:
                matched_datatype = value
                logger.info(f"Mapped datatype: Header contains '{key}', mapped to '{value}'")
                break
        
        if matched_datatype:
            parts['datatype'] = matched_datatype
        else:
            logger.warning(f"No datatype mapping found for header: '{header_text}'")
            logger.warning(f"Available mappings: {datatype_mapping}")
            parts['datatype'] = ''
    
        # Rest of the method remains the same
        year_match = re.search(r'отчетный период:.*?(\d{4})', header_text) or re.search(r'\b\d{4}\b', header_text)
        parts['year'] = year_match.group(1) if year_match else ''
    
        if 'январь-март' in header_text:
            parts['quarter'] = '1'
        elif 'январь-июнь' in header_text:
            parts['quarter'] = '2'
        elif 'январь-сентябрь' in header_text:
            parts['quarter'] = '3'
        elif 'январь-декабрь' in header_text:
            parts['quarter'] = '4'
        else:
            parts['quarter'] = '4'

        logger.info(f"Extracted metadata: {parts}")
        return parts

    def melt_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        reg_pattern = r'\b(рег|регистрационный)\b'
        reg_columns = [col for col in df.columns if re.search(reg_pattern, col.lower())]

        if not reg_columns:
            raise ValueError("No column containing 'Рег' as a separate word found in the DataFrame")

        index_column = reg_columns[0]
        index_column_position = df.columns.get_loc(index_column)

        df = df.iloc[:, index_column_position:]
        df.loc[df.index[0], index_column] = 'all_insurers'
        df.set_index(index_column, inplace=True)

        df_long = df.melt(ignore_index=False, var_name='insurance_line', value_name='value')
        df_long.reset_index(inplace=True)
        df_long.rename(columns={index_column: 'insurer'}, inplace=True)

        return df_long

    def add_metadata_to_dataframe(self, df: pd.DataFrame, metadata_values: Dict[str, str]) -> pd.DataFrame:
        for key, value in metadata_values.items():
            df[key] = value
        return df