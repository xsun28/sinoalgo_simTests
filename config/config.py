import pandas as pd
import sys
sys.path.insert(0, '../')


class Config:
    def __init__(self):
        self.order_params = pd.read_csv('resources/orders.csv')
        self.log_file_path = 'resources/sinoalgo-20220513T182652.log'
        self.report_file_path = 'report/report.csv'
        self.checks_all = ['check_size_error', 'check_parent_size', 'check_time_error', 'check_parent_time',
                           'check_rate_error', 'check_parent_rate', 'check_target_rate', 'check_order_completion',
                           'check_noon_break', 'check_order_lot', 'check_early_completion',
                           'check_large_stop', 'check_price_limit', 'check_POV_execution']


cfg = Config()
