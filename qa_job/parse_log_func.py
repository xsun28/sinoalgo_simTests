import re
import pandas as pd


def convert_time(time):
    microseconds = (time // 10000000 * 3600 + time % 10000000 // 100000 * 60) * 1000000
    return microseconds


def match_order(uncheck, checked, order_cfg):
    # convert order params
    order_cfg.update({'StartTime': convert_time(order_cfg.get('StartTime'))})
    order_cfg.update({'EndTime': convert_time(order_cfg.get('EndTime'))})
    if not order_cfg['OrderSide'] == -1:
        order_cfg['OrderSide'] = 1
    # match config with unchecked order
    for index, order in uncheck.iterrows():
        algo = order['strategyType']
        ticker = order['symbol']
        OrderSize = int(order['size'])
        OrderSide = int(order['side'])
        StartTime = int(order['startTime'])
        EndTime = int(order['endTime'])
        if [algo, ticker, OrderSize, OrderSide, StartTime, EndTime] == list(order_cfg[['algo','ticker','OrderSize','OrderSide','StartTime','EndTime']]):
            return index
    return 'config error, cannot match parent order'


def parse_order(log):
    parent_uncheck = parse_whole_line(log, "tag:parent order before check:", '', "tag:parent order before check:")
    parent_checked = []
    for lines in log:
        if "tag:parent order after check:" in lines:
            info = lines.split("tag:parent order after check:")[-1].rstrip('\n')
            error_msg = info.split("error msg:")[-1].rstrip('\n')
            info = info.split("error msg:")[0].rstrip('\n').split("|")
            msg = {}
            for i in info:
                if ',' in i:
                    items = i.split(',')
                    info += items  # params
                    info.remove(i)
            for i in info:
                if '=' in i:
                    key = i.split('=')[0]
                    value = i.split('=')[1]
                    if (key != '') & (value != ''):
                        msg.update({key: value})
            msg.update({"error_msg": error_msg})
            parent_checked.append(msg)
    parent_checked = pd.DataFrame(parent_checked)
    parent_uncheck[['size', 'side', 'startTime', 'endTime']] = parent_uncheck[
        ['size', 'side', 'startTime', 'endTime']].astype('int')
    parent_uncheck[['minRate', 'maxRate']] = parent_uncheck[['minRate', 'maxRate']].astype('float')
    parent_checked[['size', 'side', 'startTime', 'endTime']] = parent_checked[
        ['size', 'side', 'startTime', 'endTime']].astype('int')
    parent_checked[['minRate', 'maxRate']] = parent_checked[['minRate', 'maxRate']].astype('float')
    return parent_uncheck, parent_checked


def parse_whole_line(log, line_cond, po_cond, split_txt):
    data = []
    for line in log:
        if (line_cond in line) & (po_cond in line):
            info = line.split(split_txt)[-1].rstrip('\n').split('|')
            msg = {}
            for i in info:
                if ',' in i:
                    items = i.split(',')
                    info += items  # params
                    info.remove(i)
            for i in info:
                if '=' in i:
                    key = i.split('=')[0]
                    value = i.split('=')[1]
                    if (key != '') & (value != ''):
                        msg.update({key: value})
            data.append(msg)
    return pd.DataFrame(data)


def get_specific_lines(log, lines_cond, PO_cond):
    data = []
    for lines in log:
        if (lines_cond in lines) & (PO_cond in lines):
            data.append(lines)
    return data


def get_specific_values(log, lines_cond, values_cond, PO_cond):
    data = get_specific_lines(log, lines_cond=lines_cond, PO_cond=PO_cond)
    pattern_value = re.compile(values_cond)
    values = []
    if not data:
        return ['']
    for line in data:
        value = pattern_value.findall(line)[0]
        values.append(value)
    return values


class ParseOrderInfo:
    def __init__(self, log, this_order):
        self.log = log
        self.order = self.get_this_po(this_order)
        self.po = self.order['orderId']
        self.child = self.get_child_orders()
        self.child, self.fill = self.get_fill_msg(self.child)
        self.cancel = self.get_cancel_msg()

    def get_this_po(self, this_order):
        parent_orders = pd.DataFrame(columns=['orderId', 'strategyType', 'symbol', 'MarketType', 'size', 'side',
                                              'startTime', 'endTime', 'doOpen', 'doClose', 'pct_open', 'pct_close',
                                              'Plimit', 'Pstop', 'maxRate', 'minRate'])
        checked_param = [this_order['strategyType'], this_order['symbol'], this_order['size'], this_order['side'],
                         this_order['startTime'], this_order['endTime']]
        po = parse_whole_line(self.log, "Added parent order:", '', "Added parent order:")
        if len(po) > 0:
            parent_orders = po
        parent_orders[['size', 'side', 'startTime', 'endTime']] = parent_orders[
            ['size', 'side', 'startTime', 'endTime']].astype('int')
        parent_orders[['pct_open', 'pct_close', 'Plimit', 'Pstop', 'maxRate', 'minRate', 'pct_complete']] = \
            parent_orders[['pct_open', 'pct_close', 'Plimit', 'Pstop', 'maxRate', 'minRate', 'pct_complete']].astype(
                'float')
        for index, order in parent_orders.iterrows():
            param_withid = [order['strategyType'], order['symbol'], order['size'], order['side'],
                            order['startTime'],
                            order['endTime']]
            if param_withid == checked_param:
                this_order = order
                break
        return this_order

    def get_child_orders(self):
        # get all create orders information
        cond_create_msg = r'OMS tries to create order'
        cond_msg_po = r'parentOrderId=' + self.po
        child_orders = pd.DataFrame(columns=['current_t', 'OrderCreateMessage', 'timestamp', 'mType', 'source',
                                             'destination', 'mId', 'orderId', 'OrderMessageType', 'parentOrderId',
                                             'parentStrategyType', 'symbol', 'side', 'price', 'size', 'orderType',
                                             'msg'])
        co = parse_whole_line(self.log, cond_create_msg, cond_msg_po, "tag:OMS message;")
        if len(co) > 0:
            child_orders = co
        child_orders.index = child_orders['orderId']
        child_orders[['current_t', 'timestamp', 'side', 'size', 'price']] = child_orders[
            ['current_t', 'timestamp', 'side', 'size', 'price']].astype('int')
        return child_orders

    def get_fill_msg(self, orders):
        fill_info = pd.DataFrame(columns=['timestamp', 'mType', 'orderId', 'OrderMessageType', 'side', 'size', 'price',
                                          'time'])
        condFillMsg = r'addMsgFromVenue:OrderFillMessage='  # filledSize lines, match the chars behind 'algo status'
        fill = parse_whole_line(self.log, condFillMsg, '', condFillMsg)
        if len(fill) > 0:
            fill_info = fill
        create_id = list(orders.index)
        orders.insert(orders.shape[1], 'filled', 0)
        for oid, fills in zip(fill_info['orderId'], fill_info['size']):
            if oid in create_id:
                orders.loc[[oid], ['filled']] += int(fills)
        this_po_fill = fill_info[fill_info['orderId'].isin(create_id)]
        this_po_fill.loc[:, ('timestamp', 'side', 'size', 'price', 'time')] = this_po_fill[[
            'timestamp', 'side', 'size', 'price', 'time']].astype('int')
        return orders, this_po_fill

    def get_cancel_msg(self):
        cancel_info = pd.DataFrame(columns=['timestamp', 'mType', 'orderId', 'OrderMessageType', 'time'])
        condCancelMsg = r'OMS tries to cancel order'
        condMsg_PO = r'parentOrderId=' + self.po
        cancel = parse_whole_line(self.log, condCancelMsg, condMsg_PO, "tag:OMS message;")
        if len(cancel) > 0:
            cancel_info = cancel
        return cancel_info

    def get_stopped_time(self):
        cond_stopped = r'removePO'
        cond_POid = r'.*POId=' + self.po
        cond_stoppedTime = r'(?<=current_t=)\d*'
        stopped_time = int(get_specific_values(self.log, cond_stopped, cond_stoppedTime, cond_POid)[0])
        return stopped_time
