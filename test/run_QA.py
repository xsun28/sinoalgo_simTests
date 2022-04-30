from test.analytic_func import Analytic
from config.test_config import cfg
import pandas as pd


def read_log_file(logfile):
    logfile = open(logfile, encoding="utf8", errors='ignore')
    log = logfile.readlines()
    logfile.close()
    return log  # return str


class runQA:
    def __init__(self):
        self.logfile = cfg.file_path
        self.log = read_log_file(self.logfile)

    def result2df(self, order, purpose, result):
        if result == True:
            r = pd.DataFrame([[order, purpose, result, '']],
                             columns=['order', 'purpose', 'result', 'msg'])
        else:
            r = pd.DataFrame([[order, purpose, False, result]],
                             columns=['order', 'purpose', 'result', 'msg'])
        return r

    def run_check(self):
        result_df = pd.DataFrame(columns=['order', 'purpose', 'result', 'msg'])
        for index, order in cfg.order_params.iterrows():
            test = Analytic(self.log, order)
            if test.order is None:
                print("order_config_wrong, cannot match order:"+str(order))
                continue
            else:
                t = order.get('Purpose')
                if t in cfg.checks_all:
                    r = self.result2df(order.get('ticker'), t, eval('test.' + t + '()'))
                    result_df = result_df.append(r)
        return result_df
