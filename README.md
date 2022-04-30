# sinoalgo_QA

This repository is for quality assurance of algo system

Tests are conducted by parsing the performance logs generated by trading system, the functions to parse and analyze keywords for each cases are included.
Each test case has a specific check function to run. To start a new test, one should assign the _order.csv_ and specify the purpose of each case in order config, then run the run_QA.py to test each order and case assigned in order config.

## Program structure
```
│  main.py
│          
│ 
├─config                  
│      test_config.py   
│          
│ 
├─test                  
│      parse_func.py   
│      analytic_func.py 
│      run_QA.py 
│      
```
### input (config):
1. order params: `'/volume1/home/xhu/sinoalgo_QA/config/orders.csv'`
2. log file path: `'/volume1/home/xhu/latest/sinoalgo/logs/sinoalgo-20220428T184032.log'`

### run test
`python main.py`

### output:
This script will print the result dataframe, contains four columns: ticker, purpose, result(True means pass, False means failed) and error msg. 

Following dataframe shows a successful test and a failed test of check_order_completion:

| ticker       | purpose                 | result | msg                                                     |
|--------------|-------------------------|--------|---------------------------------------------------------|
| 000001.XSHE  | check_order_completion  | True   ||
| 000001.XSHE  | check_order_completion  | False  | filled_size=9800, smaller than parent_order_size=10000  |



## Test cases

Currently, there are following test cases:

| Purpose                | Description                                                                                        | Param Examples                           | Pass conditions                                                         |
|------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------|-------------------------------------------------------------------------|
| check order completion | To test whether a parent order can be all filled                                                   |                                          | Parent order all filled                                                 |
| check_order_lot        | To test whether all the order placement meet the conditions of order lot                           |                                          | Each child order size meet the order lot conditions                     |
| check_noon_break       | To test if there is any order placement during noon break                                          |                                          | No order creation or cancellation during noon break                     |
| check_size_error       | When a wrong parent order size is assigned, test whether the algo can check the error              | ticker: 000001.XSHE, OrderSize: 60       | Throw parent size error message, and this parent order cannot be added  |
| check_parent_time      | Assign a parent order start time before 9:30 or end time after 15:00, which should be corrected    | StartTime: 90000000,  EndTime: 153000000 | Correct the start \ end time, then add the parent order                 |
| check_parent_rate      | Assign a parent order min rate smaller than 0 or max rate bigger than 1, which should be corrected | minRate: -1                              | Correct the min \ max rate, then add the parent order                   |
| check_rate_error       | When the assigned min rate is bigger than max rate, test if the algo can check this error          | minRate: 10                              | Throw parent rate error message, and this parent order cannot be added  |                 
| check_target_rate      | For POV, when target rate is out of range, or not set, test if the algo can check this error       | Param: null                              | Throw target rate error message, and this parent order cannot be added  |

## Test examples and results
| ticker       | purpose                | result | msg |
|--------------|------------------------|--------|-----|
| 000001.XSHE  | check_order_completion | True   ||
| 000001.XSHE  | check_order_lot        | True   ||
| 000001.XSHE  | check_noon_break       | True   ||
| 000001.XSHE  | check_size_error       | True   ||
| 688001.XSHG  | check_size_error       | True   ||
| 000001.XSHE  | check_price_limit      | True   ||
| 000001.XSHE  | check_parent_time      | True   ||
| 000001.XSHE  | check_parent_time      | True   ||
| 000001.XSHE  | check_parent_rate      | True   ||
| 000001.XSHE  | check_rate_error       | True   ||
| 000001.XSHE  | check_target_rate      | True   ||
|  688001.XSHG | check_target_rate      | True   |     |