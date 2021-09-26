# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 20:20:04 2021

@author: Hxl
"""
# In[14]:


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

def get_stopped_time(log, po):
    cond_stopped = r'AGS action.*removePO.*'
    cond_POid = r'.*POId=' + po
    cond_stoppedTime = r'(?<=current_t=)\d*'
    stopped_time = int(get_specific_values(log,cond_stopped,cond_stoppedTime,cond_POid)[0])
    return stopped_time
    


# ## Test Case 1: Order completion
# #### Description
# The test case is for checking if the parent order in completed within the specified trading period.

# In[42]:


def check_order_completion(file_path, po):
    log = read_log_file(file_path)
    doClose, parentSize, symbol = get_po_info(log, po)
    star = symbol[0:3] == '688'
    
    orders = get_child_orders(log, po)
    orders, fill = get_fill_size(log, orders)
    # get supposedly filled size
    supposed_filled = parentSize
    # get actually filled size
    regular_filled = sum(fill.loc[fill['time'] <= close_start]['size'])
    close_filled = sum(fill.loc[fill['time'] > close_start]['size'])
#     print("regular_filled=%d, close_filled=%d, regular_filled+close_filled=%d"%(regular_filled,close_filled,regular_filled+close_filled))
    if star:
        regular_filled = (math.ceil(int(regular_filled) / 200.0)) * 200
    else:
        regular_filled = (math.ceil(int(regular_filled) / 100.0)) * 100
    all_filled = (regular_filled + int(close_filled)) == supposed_filled
    print(regular_filled)
    return all_filled


# #### Mainboard

# In[61]:


check_order_completion('/home/xhu/log/testfill.txt','10000')


# #### Small and Medium Enterprises (SME) Board

# In[43]:


check_order_completion('/home/xhu/log/test_SMEmarket.log','10000') # 002024.XSHE


# #### Growth Enterprise Market (GEM)

# In[54]:


check_order_completion('/home/xhu/log/test_GEMmarket.log','10000') # 300059.XSHE


# #### Sci-Tech Innovation Board (STAR)

# In[72]:


check_order_completion('/home/xhu/log/testSTAR0919.log','10000') #  688001.XSHG


# In[53]:


# This is about close auction, not considered now
check_order_completion('/home/xhu/log/testclose688001.log','10000')


# ## Test case 2: Order placement during noon break
# #### Description
# The test case is to check whether the system is still creating or cancelling orders after morning session end
# 
# The case is split into four sub-cases:
# 
# 1. End time between 11:30 and 13:00
# 2. End time after 13:00

# In[26]:


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


# #### Mainboard

# In[5]:


check_noon_break('/home/xhu/log/testclose0917.txt','10000')


# #### Small and Medium Enterprises (SME) Board

# In[52]:


check_noon_break('/home/xhu/log/test_SMEmarket.log','10000')


# #### Growth Enterprise Market (GEM)

# In[34]:


check_noon_break('/home/xhu/log/test_GEMmarket.log','10000')


# #### Sci-Tech Innovation Board (STAR)

# In[53]:


check_noon_break('/home/xhu/log/testSTAR0919.log','10000')


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


# #### Mainboard

# In[56]:


# doClose = true
check_after_close('/home/xhu/log/testclose0917.txt','10001')


# #### Mainboard

# In[9]:


# doClose = false
check_after_close('/home/xhu/log/testclose0916.txt','10000')


# In[26]:


# STAR market, doClose = true, endTime = 1510
check_after_close('/home/xhu/log/testclose688001.1510.log','10000')


# ## Test case 4: Order placement
# ### Description
# The test is to check if the child order placement meets the order lot conditions, this case is devided into three sub-cases:
# 1. STAR market stocks, whose order lot is 200
# 2. mainboard and other second board stocks, whose order lot is 100

# In[45]:


def check_order_lot(file_path, po):
    log = read_log_file(file_path)
    doClose, parentSize, symbol = get_po_info(log, po)
    star = symbol[0:3] == '688'
    child_orders = get_child_orders(log,po)
    # check if the create size > 200
    if star:
        lot = 200
    else:
        lot = 100
    size_lot = all((size>=lot) for size in list(child_orders['create_size']))
    multiple_of_lot = all((size%lot == 0)for size in list(child_orders['create_size']))
    return size_lot&multiple_of_lot


# #### Mainboard

# In[47]:


check_order_lot('/home/xhu/log/testfill.txt','10000')


# #### Small and Medium Enterprises (SME) Board

# In[51]:


check_order_lot('/home/xhu/log/test_SMEmarket.log','10000')


# #### Growth Enterprise Market (GEM)

# In[50]:


check_order_lot('/home/xhu/log/test_GEMmarket.log','10000')


# #### Sci-Tech Innovation Board (STAR)

# In[46]:


check_order_lot('/home/xhu/log/testSTAR0919.log','10000')


# ## Test case 5: Stop of a early completion
# ### Description
# The test is to check if the strategy would stop quickly after a small order placement like 100 or 200 shares is completed

# In[55]:


def check_early_completion(file_path, po):
    log = read_log_file(file_path)
    cond_completed = r'.*Algo=VWAP,completed.*'
    cond_completedTime =  r'(?<=current_t=)\d*'
    cond_PO = r'Order=' + po
    complete_time = int(get_specific_values(log,cond_completed,cond_completedTime,cond_PO)[0])
    stopped_time = get_stopped_time(log,po)
    
    # return an interval
    interval = stopped_time - complete_time
    return interval/1000000


# #### Mainboard

# In[6]:


# 200 shares
check_early_completion('/home/xhu/log/test_quickExecution.log','10000')


# #### Mainboard

# In[7]:


# 100 shares
check_early_completion('/home/xhu/log/test_quickExecution.log','10001')


# #### Small and Medium Enterprises (SME) Board

# In[62]:


check_early_completion('/home/xhu/log/test_earlyCompleteSME.log','10000') # The market data is empty during 37884000000--37893000000 (9secs), 37896-37905000000(9secs)


# #### Growth Enterprise Market (GEM)

# In[60]:


check_early_completion('/home/xhu/log/test_earlyCompleteGEM.log','10000')


# #### Sci-Tech Innovation Board (STAR)

# In[61]:


check_early_completion('/home/xhu/log/test_earlyCompleteSTAR.log','10000') # The market data is empty during 35129000000--35145000000(16secs), --35157000000(12secs)


# ## Test case 6: Stop of a large order
# #### Description
# The test is to check if a large order with a limit duration quickly stops after the parent order end time
# 

# In[8]:


def check_large_stop(file_path, po):
    log = read_log_file(file_path)
    stopped_time = get_stopped_time(log,po)
    
    # get start end time of parent order
    condPO = r'Added parent order.*'  # AddPO line
    condPO_endtime = r'(?<=endTime=)\d*'
    condPO_id = r'.*orderId=' + po + '.*'  # conditions to get doClose information of po:
    endTime = int(get_specific_values(log,condPO,condPO_endtime,condPO_id)[0])
    
    interval = stopped_time - endTime
    return interval/1000000


# #### Mainboard

# In[9]:


check_large_stop('/home/xhu/log/test_largeStop.log','10000')


# #### Small and Medium Enterprises (SME) Board

# In[44]:


check_large_stop('/home/xhu/log/test_SMEmarket.log','10000')


# #### Growth Enterprise Market (GEM)

# In[40]:


check_large_stop('/home/xhu/log/test_GEMmarket.log','10000')


# #### Sci-Tech Innovation Board (STAR)

# In[10]:


check_large_stop('/home/xhu/log/test_largeStop.log','10001')


# In[ ]:




