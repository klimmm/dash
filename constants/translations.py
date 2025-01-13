# constants/translations.py

from typing import Dict


TRANSLATIONS: Dict[str, str] = {

    # Period Types
    
    "ytd": "Нарастающим итогом с начала года (Year-to-Date)", 
    "qoq": "К предыдущему кварталу",
    "yoy_q": "К аналогичному кварталу прошлого года", 
    "yoy_y": "Данные за последовательные 12 месяцев, год к году", 
    "mat": "Moving Annual Total",

    # YTD
    '''это сумма данных за все завершённые периоды текущего года, начиная с января".  
    - Пример:  
      - Если сейчас февраль 2024:  
        - Период расчёта: январь 2024 + февраль 2024 (например, 1 000 + 1 200 = 2 200).  
        - Сравнивается с: январь 2023 + февраль 2023 (например, 900 + 1 100 = 2 000).'''
    # (Quarter-over-Quarter)
    '''сравнение показателей за текущий квартал с предыдущим кварталом - то есть последовательные кварталы".  
    - Пример:  
      - 1 квартал 2024:  
        - Период расчёта: январь-март 2024 (например, 3 200).  
        - Сравнивается с: октябрь-декабрь 2023 (например, 3 000).'''

    # (Year-over-Year Quarter)   
    '''сравнение показателей за текущий квартал с тем же кварталом предыдущего года".  
        - Пример:  
          - 1 квартал 2024 года:  
            - Период расчёта: январь-март 2024 (например, 3 000).  
            - Сравнивается с: январь-март 2023 (например, 2 800).  '''

    # (Year-over-Year Year)
    '''сравнение суммы показателей за последние 12 месяцев с аналогичным периодом предыдущего года".  
        - Пример:  
          - На март 2024:  
            - Период расчёта: апрель 2023 — март 2024 (например, 12 000).  
            - Сравнивается с: апрель 2022 — март 2023 (например, 11 500).'''

    # Скользящие годовые данные с квартальным интервалом между периодами (Moving Annual Total)
    '''сравнение скользящих годовых данных с квартальным интервалом между периодами".  
        - Пример:  
          - На март 2024:  
            - Период расчёта: апрель 2023 — март 2024 (например, 12 500).  
            - Сравнивается с: январь 2023 — декабрь 2023 (например, 12 300). '''


    # Line Types
    "Direct": "Прямое",
    "Inward": "Входящее",
    "Sums End": "Страховые суммы по действующим договорам",  # Made parallel with other sums
    "Average Sum Insured": "Средняя страховая сумма по действующим договорам",
    # Premium and Loss Types
    "direct_premiums": "Премии по прямому страхованию",
    "direct_losses": "Выплаты по прямому страхованию",
    "inward_premiums": "Премии по входящему перестрахованию",
    "inward_losses": "Выплаты по входящему перестрахованию",
    "ceded_premiums": "Премии по исходящему перестрахованию",
    "ceded_losses": "Выплаты по исходящему перестрахованию",
    "net_premiums": "Премии-нетто перестрахования",
    "net_losses": "Выплаты-нетто перестрахования",

    # Contract and Claims Metrics
    "new_contracts": "Количество новых договоров",
    "new_sums": "Страховые суммы по новым договорам",
    "contracts_end": "Количество действующих договоров",
    "sums_end": "Страховые суммы по действующим договорам",
    "claims_reported": "Количество заявленных страховых случаев",
    "claims_settled": "Количество урегулированных страховых случаев",

    # Intermediary Metrics
    "premiums_interm": "Премии от посредников",
    "commissions_interm": "Вознаграждение посредникам",
    "New Sums": "Страховые суммы по заключенным договорам",

    # Market Metrics
    "Total Premiums": "Премии",
    "Total Losses": "Выплаты",
    "Ceded Premiums": "Премии по исходящему перестрахованию",
    "Ceded Losses": "Выплаты по исходящему перестрахованию",
    "New Contracts": "Кол-во заключенных договоров",
    "New Sums": "Страховые суммы по заключенным договорам",
    "Claims Settled": "Кол-во урегулированных случаев",
    "Average New Sum Insured": "Средняя страховая сумма по новым договорам",
    "Average New Premium": "Средняя премия по новым договорам",
    "average_loss": "Средняя сумма выплаты",
    "Direct Premiums": "Премии по прямому страхованию",
    "Direct Losses": "Выплаты по прямому страхованию",
    "Inward Premiums": "Премии по входящему перестрахованию",
    "Inward Losses": "Выплаты по входящему перестрахованию",
    "Net Premiums": "Премии нетто-перестрахование",
    "Net Losses": "Выплаты нетто-перестрахование",
    "Premiums Interm": "Премии от посредников",
    "Commissions Interm": "Вознаграждение посредникам",
    "Premiums Interm Ratio": "Доля премий от посредников",
    "Commissions Rate": "Вознаграждение к премии",
    "Gross Loss Ratio": "Убыточность",
    "Direct Loss Ratio": "Убыточность",
    "Contracts End": "Кол-во действующих договоров",
    "Average Rate": "Средняя ставка",

    # Market Metrics
    "total_premiums": "Премии",
    "total_losses": "Выплаты",
    "ceded_premiums": "Премии по исходящему перестрахованию",
    "ceded_losses": "Выплаты по исходящему перестрахованию",
    "new_contracts": "Кол-во заключенных договоров",
    "new_sums": "Страховые суммы по заключенным договорам",
    "claims_settled": "Кол-во урегулированных случаев",
    "direct_premiums": "Премии по прямому страхованию",
    "direct_losses": "Выплаты по прямому страхованию",
    "inward_premiums": "Премии по входящему перестрахованию",
    "inward_losses": "Выплаты по входящему перестрахованию",
    "net_premiums": "Премии нетто-перестрахование",
    "net_losses": "Выплаты нетто-перестрахование",
    "premiums_interm": "Премии от посредников",
    "commissions_interm": "Вознаграждение посредникам",
    "contracts_end": "Кол-во действующих договоров",

    
    # Market Share Metrics
    "direct_premiums_market_share": "Доля рынка по прямому страхованию (премии)",
    "direct_losses_market_share": "Доля рынка по прямому страхованию (выплаты)",
    "inward_premiums_market_share": "Доля рынка по входящему перестрахованию (премии)",
    "inward_losses_market_share": "Доля рынка по входящему перестрахованию (выплаты)",
    "ceded_premiums_market_share": "Доля рынка по переданным в перестрахование премиям",
    "ceded_losses_market_share": "Доля рынка по переданным в перестрахование выплатам",
    "total_losses_market_share": "Доля рынка по общей сумме выплат",
    "total_premiums_market_share": "Доля рынка по общей сумме премий",
    "market_share": "доля рынка, %",
    # "market_share": "MS, %",
    "q_to_q_change": "Δ%",


    # Ratio Metrics and Changes
    "ceded_premiums_ratio": "Доля премий, переданных в перестрахование",
    "ceded_losses_ratio": "Доля выплат, переданных в перестрахование",
    "ceded_ratio_diff": "Разница между долями премий и выплат в перестраховании",
    "ceded_losses_to_ceded_premiums_ratio": "Коэффициент выплат по исходящему перестрахованию",
    "gross_loss_ratio": "Коэффициент убыточности (брутто)",
    "net_loss_ratio": "Коэффициент убыточности (нетто)",
    "effect_on_loss_ratio": "Влияние перестрахования на коэффициент убыточности",
    "Net Loss Ratio Growth": "Динамика коэффициента убыточности (нетто)",
    "Ceded Premiums Ratio Growth": "Динамика доли премий в перестраховании",
    "Ceded Losses to Premiums Ratio Growth": "Динамика коэффициента выплат в перестраховании",
    "Ceded Premiums Ratio": "Доля премий, переданных в перестрахование",
    "Ceded Losses Ratio": "Доля выплат, переданных в перестрахование",
    "Net Loss Ratio": "Коэффициент убыточности (нетто)",
    "Ceded Losses to Ceded Premiums Ratio": "Коэффициент выплат по исходящему перестрахованию",

    # Average Values
    "Average Sum Insured": "Средняя страховая сумма",
    "Average Loss": "Средняя сумма выплаты",

    "Total Market": "Весь рынок",

    # General Labels
    "Value": "Значение",
    "Percentage / Ratio": "Процент / Коэффициент",
    "Market Share by Line of Business": "Доля рынка по видам страхования",
    "Market Share": "Доля рынка",
    "Line of Business": "Вид страхования",
    "insurer": "Страховщик",

    # Reinsurance Categories
    "within_russia": "на территории Российской Федерации",
    "outside_russia": "за пределы территории Российской Федерации",
    "facultative": "факультативное",
    "obligatory": "облигаторное",
    "ob_fac": "облигаторно-факультативное",
    "fac_ob": "факультативно-облигаторное",
    "proportional": "пропорция",
    "non_proportional": "непропорция",
    "reinsurance_geography": "По географии перестрахования",
    "reinsurance_form": "По форме перестрахования",
    "reinsurance_type": "По виду перестрахования",
    "Hide": "Скрыть все категории",
}

def translate(text: str) -> str:
    """
    Translate the given text using the TRANSLATIONS dictionary.

    Args:
        text (str): The text to translate.

    Returns:
        str: The translated text, or the original text if no translation is found.
    """
    return TRANSLATIONS.get(text, text)

def translate_quarter_column(column_name: str, quarter: str) -> str:
    """
    Translate a quarter-specific column name.

    Args:
        column_name (str): The base column name to translate.
        quarter (str): The quarter identifier (e.g., "2023Q1").

    Returns:
        str: The translated column name with the quarter.
    """
    base_translation = translate(column_name.split('_')[0])
    return f"{base_translation} ({quarter})"

def cached_translate(text: str) -> str:
    """Cache translations to improve performance."""
    return translate(text)

def translate_quarter(quarter: str) -> str:
    """Translate quarter string to Russian format."""
    year, q = quarter.split('Q')
    months = {
        '1': '3 месяца',
        '2': '6 месяцев',
        '3': '9 месяцев',
        '4': '12 месяцев'
    }
    return f"{year} год, {months[q]}"
