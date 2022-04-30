import pandas as pd


class Config:
    def __init__(self):
        self.order_params = pd.read_csv('/Users/xinlan/PycharmProjects/sinoalgo_QA/config/orders.csv')
        self.file_path = '/Users/xinlan/Documents/sinoalgo/code/logs/sinoalgo-20220428T184032.log'
        self.checks_all = ['check_size_error', 'check_parent_size', 'check_time_error', 'check_parent_time',
                           'check_rate_error', 'check_parent_rate', 'check_target_rate', 'check_order_completion',
                           'check_noon_break', 'check_order_lot', 'check_early_completion',
                           'check_large_stop', 'check_price_limit']


cfg = Config()
