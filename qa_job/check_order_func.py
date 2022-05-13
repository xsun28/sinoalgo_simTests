import math
import qa_job.parse_log_func as parse

morning_end = (11 * 3600 + 30 * 60) * 1000000
afternoon_start = (13 * 3600) * 1000000
close_start = (14 * 3600 + 57 * 60) * 1000000
afternoon_end = (15 * 3600) * 1000000


class CheckOrder:

    def __init__(self, log, this_order_cfg):
        """
        :param log:
        :param this_order_cfg: The
        """
        self.log = log
        self.uncheck, self.checked = parse.parse_order(self.log)
        # self.order = this_order_cfg
        self.index = parse.match_order(self.uncheck, self.checked, this_order_cfg)
        if isinstance(self.index, str):  # no match order, config wrong
            self.order = None
            self.err_msg = self.index
            self.poi = None
        else:
            self.order = self.checked.iloc[self.index]
            self.err_msg = self.order['error_msg']
            self.poi = parse.ParseOrderInfo(log=log, this_order=self.order) if not self.err_msg == '' else None

    def check_size_error(self):
        check_min_size = ("|Main, MediumSmall, Startup, stock order size must be larger than 100.|" in
                          self.order['error_msg']) | ("|Technology stock order size must be larger than 200.|" in
                                                      self.order['error_msg'])
        if check_min_size:
            return True
        else:
            return "parent order size error unchecked"

    def check_parent_size(self):
        if self.order['symbol'][0:3] == '688':
            check_size = self.order['size'] >= 200
        else:
            check_size = (self.order['size'] >= 100) & (self.order['size'] % 100 == 0)
        if check_size:
            return True
        else:
            return "parent order size unchecked"

    def check_time_error(self):
        check_start_end = "|Start time surpasses the exchange close time" in self.order['error_msg']
        if check_start_end:
            return True
        else:
            return "parent order time error unchecked"

    def check_parent_time(self):
        check_start_time = self.order['startTime'] >= 34200000000
        check_end_time = (self.order['endTime'] <= 54000000000) & (self.order['endTime'] >= self.order['startTime'])

        if check_end_time & check_start_time:
            return True
        else:
            return "parent order time unchecked"

    def check_rate_error(self):
        check_rate = ("|Max participation rate must larger than 0|" in self.order['error_msg']) or (
                "|Min participation rate is larger than max participation rate|" in self.order['error_msg'])
        if check_rate:
            return True
        else:
            return "parent order participation rate error unchecked"

    def check_parent_rate(self):
        check_minRate = self.order['minRate'] >= 0
        check_maxRate = self.order['maxRate'] <= 1
        check_min_max = self.order['minRate'] < self.poi.order['maxRate']
        if check_minRate & check_maxRate & check_min_max:
            return True
        else:
            return "parent order rate unchecked"

    def check_target_rate(self):
        check_target = ("|Target rate of POV out of range|" in self.order['error_msg']) or (
                "|Target rate of POV not set|" in self.order['error_msg'])
        if check_target:
            return True
        else:
            return "Target rate of POV not checked"

    def check_order_completion(self):
        star = self.poi.order['symbol'][0:3] == '688'
        fill = self.poi.fill
        # get supposedly filled size
        supposed_filled = self.poi.order['size']
        # get actually filled size
        regular_filled = sum(fill.loc[fill['time'] <= close_start]['size'])
        close_filled = sum(fill.loc[fill['time'] > close_start]['size'])
        regular_filled = (math.ceil(int(regular_filled) / 200.0)) * 200 if star else (math.ceil(int(regular_filled) / 100.0)) * 100
        all_filled = (regular_filled + int(close_filled)) == supposed_filled
        if all_filled:
            return True
        else:
            if self.poi.order['strategyType'] == 'POV':
                market_data = self.poi.get_market_data()
                start_volume = market_data[market_data['time'] < self.order['startTime']]['accvol'].values[-1]
                end_volume = market_data[market_data['time'] < self.order['endTime']]['accvol'].values[-1]
                market_SV = end_volume - start_volume
                if market_SV * float(self.poi.order['target_rate']) < self.poi.order['size']:
                    return True
                else:
                    return "early completion should occurs due to POV target rate =" + self.poi.order['target_rate']
            else:
                return "filled_size=" + str(regular_filled) + ", smaller than parent_order_size=" + str(supposed_filled)

    def check_noon_break(self):
        # get all create and cancel order time
        orders = self.poi.child
        cancel_msg = self.poi.cancel
        # check during afternoon break
        break_create = any((time > morning_end) & (time < afternoon_start) for time in list(orders['timestamp']))
        break_cancel = any((time > morning_end) & (time < afternoon_start) for time in list(cancel_msg['timestamp']))
        if not break_create | break_cancel:
            return True
        elif break_create:
            return "order created during noon break"
        else:
            return "order cancelled during noon break"

    # This is about close auction, not considered now
    # def check_after_close(self):
    #     sop_id = 2 * int(self.poi.po[-1]) + 1
    #     doClose, parentSize, symbol = self.poi.get_po_info()
    #     # get all create orders information
    #     orders = self.poi.get_child_orders()
    #     cancels = self.poi.get_cancel_msg()
    #
    #     # check during afternoon break
    #     if doClose == 'f':
    #         endTime = close_start
    #     else:
    #         endTime = afternoon_end
    #     afterEnd_create = any(time > endTime for time in list(orders['time']))
    #     afterEnd_cancel = any(time > close_start for time in list(cancels['time']))
    #     afterEnd_placement = afterEnd_cancel | afterEnd_create
    #
    #     # get all filled size
    #     orders, fill_info = self.poi.get_fill_msg(orders)
    #     filled_size_before_close = sum(fill_info.loc[fill_info['time'] <= close_start]['size'])
    #     filled_size_after_close = sum(fill_info.loc[fill_info['time'] > close_start]['size'])
    #
    #     # get total active size
    #     condActiveSize = r'.*totalActiveSize.*'
    #     condActiveValue = r'(?<=totalActiveSize=)\d*'
    #     condSOP_id = r'SOP ' + str(sop_id) + '.*'
    #     cond_time = r'(?<=time=)\d*'
    #     totalActive = list(map(int, self.poi.get_specific_values(condActiveSize, condActiveValue, condSOP_id)))
    #     totalActiveTime = list(map(int, self.poi.get_specific_values(condActiveSize, cond_time, condSOP_id)))
    #
    #     # get total cancel pending size
    #     condCancelPSize = r'.*totalCancelPendingSize.*'
    #     condCancelPValue = r'(?<=totalCancelPendingSize=)\d*'
    #     totalCancelP = list(map(int, self.poi.get_specific_values(condCancelPSize, condCancelPValue, condSOP_id)))
    #     totalCancelPTime = list(map(int, self.poi.get_specific_values(condCancelPSize, cond_time, condSOP_id)))
    #     for active, time in zip(totalActive, totalActiveTime):
    #         if time <= close_start:
    #             lastActive_before_close = active
    #
    #     firstCancelP_after_close = 0
    #     for canp, time in zip(totalCancelP, totalCancelPTime):
    #         if time > close_start:
    #             firstCancelP_after_close = canp
    #     if doClose == 'f':
    #         # Do not explicitily allucate close size, but can participate in close auction when regular size parcially filled
    #         # The last active size before close plus the filled size should equals to parent order size
    #         close_placement = (lastActive_before_close + filled_size_before_close == parentSize)
    #     else:
    #         # Allocate the close size at the start time, unfilled regular size can participate in close auction
    #         # The last active size before close plus the filled size and the close size should equals to Parent order size
    #         close = orders.loc[(orders['type'] == 'Close') | (orders['type'] == 'CLOSE')]
    #         closeSize = sum(close['create_size'])
    #         print(lastActive_before_close, filled_size_before_close, closeSize,
    #               lastActive_before_close + filled_size_before_close + closeSize)
    #         close_placement = ((math.ceil(
    #             int(lastActive_before_close + filled_size_before_close) / 100.0)) * 100 + closeSize == parentSize)
    #         print(afterEnd_create, afterEnd_cancel)
    #     return (not afterEnd_placement) & close_placement

    def check_order_lot(self):
        star = self.poi.order['symbol'][0:3] == '688'
        child_orders = self.poi.child
        # check if the create size > 200
        lot = 200 if star else 100
        size_lot = all((size >= lot) for size in list(child_orders['size']))
        multiple_of_lot = all((size % lot == 0) for size in list(child_orders['size']))
        return size_lot & multiple_of_lot

    def check_price_limit(self):
        POid = r'Order=' + self.poi.po
        cond_buy_limit = 'Plimit>LimitUpPrice'
        cond_sell_limit = 'Plimit<LimitDownPrice'
        if self.poi.order['side'] == 1:
            check_plimit = self.poi.po in parse.get_specific_values(self.log, cond_buy_limit, r'(?<=Order=)\d*', POid)
        else:
            check_plimit = self.poi.po in parse.get_specific_values(self.log, cond_sell_limit, r'(?<=Order=)\d*', POid)
        if check_plimit:
            return True
        else:
            return "plimit unchecked"

    def check_child_price(self):
        cond_initFirstQuote = 'initWithFirstQuote'
        cond_plimit = r'(?<=Plimit=)\d*'
        cond_pstop = r'(?<=Pstop=)\d*'
        POid = r'Order=' + self.poi.po
        PLimit = int(parse.get_specific_values(self.log, cond_initFirstQuote, cond_plimit, POid)[0])
        PStop = int(parse.get_specific_values(self.log, cond_initFirstQuote, cond_pstop, POid)[0])

        exceed_Plimit = any((p > PLimit) for p in list(self.poi.child['price'])) if self.poi.po['side'] == 1 else any(
            (p < PLimit) for p in list(self.poi.child['price']))
        exceed_Pstop = any((p < PStop) for p in list(self.poi.child['price'])) if self.poi.po['side'] == 1 else any(
            (p > PStop) for p in list(self.poi.child['price']))
        if not exceed_Plimit | exceed_Pstop:
            return True
        else:
            return "child order price exceed the range of Plimit and Pstop"
