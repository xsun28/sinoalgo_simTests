from qa_job.check_order_func import CheckOrder
from config.config import cfg
import pandas as pd


def read_log_file(logfile):
    logfile = open(logfile, encoding="utf8", errors='ignore')
    log = logfile.readlines()
    logfile.close()
    return log  # return str


class QA:
    def __init__(self):
        self.logfile = cfg.log_file_path
        self.log = read_log_file(self.logfile)

    def run(self):
        result_df = pd.DataFrame(columns=['order', 'purpose', 'result', 'msg'])
        i = 0
        for index, order in cfg.order_params.iterrows():
            test = CheckOrder(self.log, order)
            if test.order is None:
                print("order_config_wrong, cannot match order:"+str(order))
                continue
            else:
                t = order.get('Purpose')
                if t in cfg.checks_all:
                    r = eval('test.' + t + '()')
                    if r == True:
                        result_df.loc[i] = [order.get('ticker'), t, r, '']
                    else:
                        result_df.loc[i] = [order.get('ticker'), t, False, r]
                    i += 1
                else:
                    print("WARNING: this purpose does not exist")
        result_df.to_csv('report.csv', index=False,)
        return
