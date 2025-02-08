DEFAULT_END_QUARTER = '2024Q3'
DEFAULT_CHECKED_LINES = ['дмс', 'нс и оглс', 'осаго', 'каско и ж/д', 'авиа, море, грузы', 'прочее имущество', 'предпр. и фин риски', 'прочая ответственность']
#DEFAULT_CHECKED_LINES = ['осаго']

DEFAULT_METRICS = ['direct_premiums', 'ceded_premiums_ratio', 'premiums_interm_ratio', 'ceded_losses_to_ceded_premiums_ratio', 'average_new_premium']
#DEFAULT_METRICS = ['direct_premiums']
DEFAULT_METRICS_158 = ['total_premiums']

DEFAULT_INSURER = []

DEFAULT_NUMBER_OF_PERIODS = 5
#DEFAULT_NUMBER_OF_PERIODS = 2
DEFAULT_BUSINESS_TYPE = ['direct']
DEFAULT_SHOW_MARKET_SHARE = []
DEFAULT_SHOW_CHANGES= ['show']
DEFAULT_SPLIT_MODE='line'
DEFAULT_REPORTING_FORM = '0420162'
TOP_N_LIST = 20
DEFAULT_PERIOD_TYPE = 'ytd'

DEFAULT_BUTTON_VALUES = {
    'periods': DEFAULT_NUMBER_OF_PERIODS,
    'business_type': DEFAULT_BUSINESS_TYPE,
    'market_share': DEFAULT_SHOW_MARKET_SHARE,
    'qtoq': DEFAULT_SHOW_CHANGES,
    'split_mode': DEFAULT_SPLIT_MODE,
    'reporting_form': DEFAULT_REPORTING_FORM,
    'top_n': TOP_N_LIST,
    'period_type': DEFAULT_PERIOD_TYPE
}