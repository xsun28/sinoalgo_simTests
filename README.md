# sinoalgo_simTests

## description
This repository is to test whether algorithms in sinoalgo system work well. 

Tests are conducted by parsing the performance logs generated by trading system, the functions to parse and analyze key words for each cases are included. Each test case has a specific check function to run. To start a new test, one should upload the corresponding logs, and run the check function for the case.

Until now there are six basic cases:

|case|purpose|run case(input params)|expected result|failed result|eg|
|----|----|---|---|----|----|
|Order completion|<div style="width: 100pt">The test case is for checking if the parent order is completed within the specified trading period.|**python test_case.py <br>--case=check\_order\_completion <br>--log=(filepath of log) <br>--poid=(poid)**|If the parent order is completed, returns true. Note that order lot is taken into consider.|If there are remaining shares after endtime, print filled size and return false.|10000(completed order)<br>True(normal)|
|Order placement during noon break|<div style="width: 100pt">The test case is to check whether the system is still creating or cancelling orders after morning session end.|**python test_case.py <br>--case=check\_noon\_break <br>--log=(filepath of log) <br>--poid=(poid)**|If there is no order placement during noon break, return true|If any order creating or cancelling request is made during noon break, the return false.|True(normal)|
|Order lot|<div style="width: 100pt">The test is to check if the child order placement meets the order lot conditions, note that the order lot of Sci-Tech Innovation Board is 200|**python test_case.py <br>--case=check\_order\_lot <br>--log=(filepath of log) <br>--poid=(poid)**|The child order size should be 100 shares or its integer multiples(>=200 for Sci-tech stocks), return true.|If any child order size does not meet the order lot condition, return false|True(normal)|
|Stop of early completion|<div style="width: 100pt">This test is to check if the strategy would stop quickly after a small order placement like 100 or 200 shares is completed|**python test_case.py --case=check\_early\_completion <br>--log=(filepath of log) <br>--poid=(poid)**|After a small parent order is completed, the strategy for the order should stop immediately. This case returns the interval between stop time and complete time.| The interval between stop time and complete time is large even with a strong liquidity|12(time interval)|
|Stop of large order|<div style="width: 100pt">The test is to check if a large order with a limit duration quickly stops after the parent order end time|**python test_case.py <br>--case=check\_large\_stop <br>--log=(filepath of log) <br>--poid=(poid)**|When it reach the end time of a parent order which is not completed yet, the strategy should stop immediately. This case returns the time interval between stop time and end time|The interval between stop time and end time is large even with a strong liquidity|15(time interval)|
|Check price limit|This test is to check if price of child order is not higher than limit up price and not lower than limit down price|**python test_case.py <br>--case=check\_price\_limit <br>--log=(filepath of log) <br>--poid=(poid)**|The price of every child order should not exceed the price limit, a successful test returns true|If any child order has a price exceeding the price limit, returns false|True(normal)|

## examples
Due to the order lot and liquidity difference, each case contains four example tests from four stock boards: 

1. Mainboard
2. Small and Medium Enterprises Board
3. Growth Enterprise Board (Start Up)
4. Sci-Tech Innovation Board

The example results are shown below:

|case and result|Mainboard|Small and Medium Enterprises Board|Growth Enterprise Board|Sci-Tech Innovation Board|
|---|---|---|---|---|
|Order completion|True|True|True|999900<br>False|
|Order placement during noon break|True|True|True|True|
|Order lot|True|True|True|True|
|Stop of early completion (sec)|5.0|21.0|9.0|28.0|
|Stop of a large order (sec)|13.0|12.0|15.0|19.0|

Several example cases of limit up and limit down were tested to **check price limit**:

|stock|brief description|price limit|result|
|---|---|---|---|
|000803.XSHE|reached limit up at 14:45, 2021/06/02|(10.51,12.85)|True|
|603888.XSHG|reached limit down at 14:00, 2021/06/02|(23.29,28.47)|True|
|688004.XSHG|reached limit up at 9:35, 2021/06/02|(29.10,43.65)|True|
