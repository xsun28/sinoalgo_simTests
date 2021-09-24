# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 20:20:04 2021

@author: Hxl
"""
# In[38]:


import re
import pandas as pd
import math
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

morning_end = (11 * 3600 + 30 * 60) * 1000000
afternoon_start = (13 * 3600) * 1000000
close_start = (14 * 3600 + 57 * 60) * 1000000
afternoon_end = (15 * 3600) * 1000000


def read_log_file(file_path):
    logfile = open(file_path, encoding="utf8", errors='ignore')
    txt = logfile.read()
    logfile.close()
    return txt  # return str


def get_po_info(log, po):
    # conditions to get doClose information of po:
    condPO = r'Added parent order.*'  # AddPO line
    condPO_doClose = r'(?<=doClose=).'  # match the Parent Order doClose value
    condPO_id = r'.*orderId=' + po + '.*'  # conditions to get doClose information of po:
    condPO_size = r'(?<=size=)\d*'
    condPO_symbol = r'(?<=symbol=)\d*'
    doClose = get_specific_values(log, condPO, condPO_doClose, condPO_id)[0]
    parentSize = int(get_specific_values(log, condPO, condPO_size, condPO_id)[0])
    symbol = get_specific_values(log,condPO,condPO_symbol,condPO_id)[0]
    return doClose, parentSize,symbol


def get_specific_lines(log, lines_cond, PO_cond):
    pattern = re.compile(lines_cond)
    data = pattern.findall(log)

    pattern_po = re.compile(PO_cond)
    lines = []
    for line in data:
        if pattern_po.findall(line):
            lines.append(line)
    #     print(values)
    return lines


def get_specific_values(log, lines_cond, values_cond, PO_cond):
    data = get_specific_lines(log, lines_cond, PO_cond)
    pattern_value = re.compile(values_cond)
    values = []
    for line in data:
        value = pattern_value.findall(line)[0]
        values.append(value)
    #     print(values)
    return values


def get_value_in_line(line, value_cond):
    pattern_value = re.compile(value_cond)
    value = pattern_value.findall(line)[0]
    return value


def get_child_orders(log, po):
    # get all create orders information
    cond_create_msg = r'OMS message.*OMS tries to create order'
    cond_msg_po = r'.*parentOrderId=' + po + '.*'
    cond_msg_time = r'(?<=current_t=)\d*'
    cond_msg_order_id = r'(?<=orderId=)\d*'
    cond_msg_order_size = r'(?<=size=)\d*'
    cond_msg_order_type = r'(?<=orderType=)\w*'
    create_time = list(map(int, get_specific_values(log, cond_create_msg, cond_msg_time, cond_msg_po)))
    create_id = get_specific_values(log, cond_create_msg, cond_msg_order_id, cond_msg_po)
    create_size = list(map(int, get_specific_values(log, cond_create_msg, cond_msg_order_size, cond_msg_po)))
    create_type = get_specific_values(log, cond_create_msg, cond_msg_order_type, cond_msg_po)

    create = list(zip(create_time, create_size, create_type))
    orders = pd.DataFrame(create, index=create_id, columns=['time', 'create_size', 'type'])

    return orders


def get_fill_size(log, orders):
    condFillMsg = r'addMsgFromVenue: OrderFillMessage.*'  # filledSize lines, match the chars behind 'algo status'
    condFillMsg_value = r'(?<=size=)\d*'  # filledSize value, match the number behind 'size='
    condFillMsg_oid = r'(?<=orderId=)\d*'
    condFillTime = r'(?<=timestamp=)\d*'

    filled_s = list(map(int, get_specific_values(log, condFillMsg, condFillMsg_value, r'')))
    filled_oid = get_specific_values(log, condFillMsg, condFillMsg_oid, r'')
    filled_time = list(map(int, get_specific_values(log, condFillMsg, condFillTime, r'')))
    create_id = list(orders.index)
    orders.insert(orders.shape[1], 'filled', 0)
    fill = list(zip(filled_oid, filled_s, filled_time))
    fill_info = pd.DataFrame(fill, columns=['oid', 'size', 'time'])

    for oid, fills, fillt in zip(filled_oid, filled_s, filled_time):
        if oid in create_id:
            orders.loc[[oid], ['filled']] += fills
    this_po_fill = fill_info[fill_info['oid'].isin(create_id)]
    return orders, this_po_fill


def get_cancel_msg(log, po):
    # conditions to get order cancel time of po:
    condCancelMsg = r'OMS message.*OMS tries to cancel order'
    condMsg_time = r'(?<=timestamp=)\d*'
    condMsg_order_id = r'(?<=orderId=)\d*'
    condMsg_PO = r'.*parentOrderId=' + po + '.*'
    cancel_time = list(map(int, get_specific_values(log, condCancelMsg, condMsg_time, condMsg_PO)))
    cancel_id = list(map(int, get_specific_values(log, condCancelMsg, condMsg_order_id, condMsg_PO)))
    cancel_info = pd.DataFrame(list(zip(cancel_id, cancel_time)), columns=['oid', 'time'])
    return cancel_info


# ## Test Case 1: Order completion
# #### Description
# The test case is for checking if the parent order in completed within the specified trading period.

# In[71]:


def check_order_completion(file_path, po):
    log = read_log_file(file_path)
    doClose, parentSize, symbol = get_po_info(log, po)
    orders = get_child_orders(log, po)
    orders, fill = get_fill_size(log, orders)
    # get supposedly filled size
    supposed_filled = parentSize
    # get actually filled size
    regular_filled = sum(fill.loc[fill['time'] <= close_start]['size'])
    close_filled = sum(fill.loc[fill['time'] > close_start]['size'])
    star = symbol[0:3] == '688'
#     print("regular_filled=%d, close_filled=%d, regular_filled+close_filled=%d"%(regular_filled,close_filled,regular_filled+close_filled))
    if star:
        regular_filled = (math.ceil(int(regular_filled) / 200.0)) * 200
    else:
        regular_filled = (math.ceil(int(regular_filled) / 100.0)) * 100
    all_filled = (regular_filled + int(close_filled)) == supposed_filled
    return all_filled


# In[61]:


check_order_completion('/home/xhu/log/testfill.txt','10000')


# In[72]:


check_order_completion('/home/xhu/log/testSTAR0919.log','10000')


# In[53]:


# This is about close auction, not considered now
check_order_completion('/home/xhu/log/testclose688001.log','10000')


# ## Test case 2: Order placement in noon break
# #### Description
# The test case is to check whether the system is still creating or cancelling orders after morning session end
# 
# The case is split into four sub-cases:
# 
# 1. End time between 11:30 and 13:00
# 2. End time after 13:00

# In[4]:


def check_noon_break(file_path, po):
    log = read_log_file(file_path)
    # get all create and cancel order time
    orders = get_child_orders(log, po)
    cancel_msg = get_cancel_msg(log, po)
    # check during afternoon break
    break_create = any((time > morning_end) & (time < afternoon_start) for time in list(orders['time']))
    break_cancel = any((time > morning_end) & (time < afternoon_start) for time in list(cancel_msg['time']))
    break_placement = break_create | break_cancel
    return not break_placement


# In[5]:


check_noon_break('/home/xhu/log/testclose0917.txt','10000')


# ## Test case 3: Order placement after close auction start
# #### Description
# The test case is to check if the system is still cancelling orders when close auction start, or creating orders after session end, and to check whether all the partially filled orders would be left into close auction
# 
# The case is split into four sub-cases:
# 
# 1. End time after 15:00 and not participate in close auction
# 2. End time after 15:00 and participate in close auction
# 3. End time between 14:57 and 15:00, cancel orders before 14:57
# 
# #### This is about close auction, not considered now

# In[57]:


# This is about close auction, not considered now
def check_after_close(file_path, po):
    log = read_log_file(file_path)
    sop_id = 2 * int(po[-1]) + 1
    doClose, parentSize, symbol= get_po_info(log, po)
    # get all create orders information
    orders = get_child_orders(log, po)
    cancels = get_cancel_msg(log, po)

    # check during afternoon break
    if doClose == 'f':
        endTime = close_start
    else:
        endTime = afternoon_end
    afterEnd_create = any(time > endTime for time in list(orders['time']))
    afterEnd_cancel = any(time > close_start for time in list(cancels['time']))
    afterEnd_placement = afterEnd_cancel | afterEnd_create

    # get all filled size
    orders, fill_info = get_fill_size(log, orders)
    filled_size_before_close = sum(fill_info.loc[fill_info['time'] <= close_start]['size'])
    filled_size_after_close = sum(fill_info.loc[fill_info['time'] > close_start]['size'])
    
    # get total active size
    condActiveSize = r'.*totalActiveSize.*'
    condActiveValue = r'(?<=totalActiveSize=)\d*'
    condSOP_id = r'SOP ' + str(sop_id) + '.*'
    cond_time = r'(?<=time=)\d*'
    totalActive = list(map(int, get_specific_values(log, condActiveSize, condActiveValue, condSOP_id)))
    totalActiveTime = list(map(int, get_specific_values(log, condActiveSize, cond_time, condSOP_id)))
    
    # get total cancel pending size
    condCancelPSize = r'.*totalCancelPendingSize.*'
    condCancelPValue = r'(?<=totalCancelPendingSize=)\d*'
    totalCancelP = list(map(int, get_specific_values(log, condCancelPSize, condCancelPValue, condSOP_id)))
    totalCancelPTime = list(map(int, get_specific_values(log, condCancelPSize, cond_time, condSOP_id)))
    for active, time in zip(totalActive, totalActiveTime):
        if time <= close_start:
            lastActive_before_close = active

    firstCancelP_after_close = 0
    for canp, time in zip(totalCancelP, totalCancelPTime):
        if time > close_start:
            firstCancelP_after_close = canp
    if doClose == 'f':
        # Do not explicitily allucate close size, but can participate in close auction when regular size parcially filled
        # The last active size before close plus the filled size should equals to parent order size
        close_placement = (lastActive_before_close + filled_size_before_close == parentSize)
    else:
        # Allocate the close size at the start time, unfilled regular size can participate in close auction
        # The last active size before close plus the filled size and the close size should equals to Parent order size
        close = orders.loc[(orders['type'] == 'Close')|(orders['type'] == 'CLOSE')]
        closeSize = sum(close['create_size'])
        print(lastActive_before_close,filled_size_before_close,closeSize,lastActive_before_close+filled_size_before_close+closeSize)
        close_placement = ((math.ceil(
            int(lastActive_before_close + filled_size_before_close) / 100.0)) * 100 + closeSize == parentSize)
        print(afterEnd_create,afterEnd_cancel)
    return (not afterEnd_placement) & close_placement


# In[56]:


# doClose = true
check_after_close('/home/xhu/log/testclose0917.txt','10001')


# In[9]:


# doClose = false
check_after_close('/home/xhu/log/testclose0916.txt','10000')


# In[26]:


# STAR market, doClose = true, endTime = 1510
check_after_close('/home/xhu/log/testclose688001.1510.log','10000')


# ## Test case 4: Order placement in STAR market
# ### Description
# The test is to check if the child order placement of STAR market meets the order lot conditions

# In[66]:


def check_STAR_order_lot(file_path, po):
    log = read_log_file(file_path)
    child_orders = get_child_orders(log,po)
    # check if the create size > 200
    size_lot = all((size>=200) for size in list(child_orders['create_size']))
    multiple_of_200 = all((size%200 == 0)for size in list(child_orders['create_size']))
    return size_lot&multiple_of_200


# In[68]:


check_STAR_order_lot('/home/xhu/log/testSTAR0919.log','10000')


# ## Test case 5: Quick execution with a small order
# ### Description
# The test is to check if a small order placement, like 100 or 200 shares, can be quickly executed even with a long execution time

# In[123]:


def check_quick_execution(file_path, po):
    log = read_log_file(file_path)
    OPs = [2*int(po[-1]),2*int(po[-1])+1]
    complete_time = []
    for op in OPs:
        cond_Completed = r'.*OMS removed OP.*'
        cond_OPid = r'.*OPid=' + str(op)
        cond_Complete_time = r'(?<=time=)\d*'
        complete_time.append(int(get_specific_values(log,cond_Completed,cond_Complete_time,cond_OPid)[0]))
    
    # get start end time of parent order
    condPO = r'Added parent order.*'  # AddPO line
    condPO_starttime = r'(?<=startTime=)\d*'
    condPO_endtime = r'(?<=endTime=)\d*'
    condPO_id = r'.*orderId=' + po + '.*'  # conditions to get doClose information of po:
    startTime = int(get_specific_values(log,condPO,condPO_starttime,condPO_id)[0])
    endTime = int(get_specific_values(log,condPO,condPO_endtime,condPO_id)[0])
    
    # return an interval rate
    interval = endTime-max(complete_time)
    interval_rate = interval/(endTime-startTime)
    return interval_rate


# In[124]:


# 200 shares
check_quick_execution('/home/xhu/log/test_quickExecution.log','10000')


# In[125]:


# 100 shares
check_quick_execution('/home/xhu/log/test_quickExecution.log','10001')


# In[ ]:




