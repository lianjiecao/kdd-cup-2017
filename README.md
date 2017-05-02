# kdd-cup-2017

Repo for KDD Cup 2017

URL: https://tianchi.aliyun.com/competition/information.htm?spm=5176.100067.5678.2.JJvKYv&raceId=231597

Participants: Hao Peng, Xiao Zhang, Lianjie Cao

## Change log


1. Training data is parsed and dumped with format: `win_start,time_of_win,weekday,routeN_0(tollgateN_Dir_0), ..., routeN_5(tollgateN_Dir_5), y_routeN_0(tollgateN_Dir_0), ... y_routeN_5(tollgateN_Dir_5)`. Each data point is `1*(3+2*6*n)` dimentional vector, where `n=5` for volume and `n=6` for travel time. A data point is created for each 20-min time window. Values are set to 0 if trajectory information is missing for a certain time window. *In the previous version, missing time windows were ignored.*
2. Testing data uses the same format. But there is only one data point for each prediction window (6 20-min windows).
