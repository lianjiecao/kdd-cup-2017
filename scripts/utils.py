# -*- coding: utf-8 -*-
#!/usr/bin/env python


# import necessary modules
import math, csv, time, argparse
import numpy as np
from datetime import datetime, timedelta

file_suffix = '.csv'
path = '../'  # set the data directory


def readCSVToList(in_file, time_key=None, time_fmt=None):
    '''
    Read .csv file with first line as keys and convert to list
    '''

    entries = []
    with open(in_file, 'r') as csv_file:
        csv_r = csv.reader(csv_file)
        keys = csv_r.next()
        for row in csv_r:
            ent = {x:y for x,y in zip(keys, row)}
            if time_key and time_fmt:
                ent.update({time_key:datetime.strptime(ent[time_key], time_fmt)})
                tw = calcTimeWindow(ent[time_key])
                ent.update({'time_window':tw})
            entries.append(ent)

    return entries


def calcTimeWindow(time_obj, win_size_min=20):
    '''
    Calculate the time window
    time_str: datetime object ()
    '''
    time_window_minute = int(math.floor(time_obj.minute / win_size_min) * win_size_min)
    return datetime(time_obj.year, time_obj.month, time_obj.day,
                                    time_obj.hour, time_window_minute, 0)



def parseTrajFile(in_file, time_fmt='%Y-%m-%d %H:%M:%S'):
    '''
    Parse trajectory data file
    Keys:
    intersection_id, tollgate_id, vehicle_id, starting_time, travel_seq, travel_time
    travel_seq: 105#2016-07-19 00:14:24#9.56;
                100#2016-07-19 00:14:34#6.75;
                111#2016-07-19 00:14:41#13.00;
                103#2016-07-19 00:14:54#7.47;
                122#2016-07-19 00:15:02#32.85
    '''

    # f = open(in_file, 'r')
    routes = set()
    veh_info = []
    fmt_str = '%Y-%m-%d %H:%M:%S'

    with open(in_file, 'r') as csv_file:
        csv_r = csv.reader(csv_file)
        keys = csv_r.next()
        for row in csv_r:
            rec = {x:y for x,y in zip(keys, row)}
            ### Split travel seq as a list and convert time string to seconds ###
            travel_seq = [x.split('#') for x in rec['travel_seq'].split(';')]
            for t in travel_seq:
                t[1] = datetime.strptime(t[1], time_fmt)
            rec.update({'travel_seq':travel_seq})
            rec.update({'starting_time':datetime.strptime(rec['starting_time'], time_fmt)})
            ### Update related time window ###
            time_window_minute = int(math.floor(rec['starting_time'].minute / 20) * 20)
            start_time_window = datetime(rec['starting_time'].year, rec['starting_time'].month, rec['starting_time'].day,
                                    rec['starting_time'].hour, time_window_minute, 0)
            rec.update({'time_window':start_time_window})
            veh_info.append(rec)
            routes.add('%s-%s' % (row[0], row[1]))

    print('All routes: %s' % ', '.join(list(routes)))
    print('# of vehicles: %d' % len(veh_info))
    # print(veh_info[:5])

    return veh_info


def dumpAverageTravelTime(traj_info, out_file, d_type, n_dps):
    ''''
    Aggregate and dump travel time info
    '''

    avg_travel_time = {} # {time_window:{(intersec, tollgate): [tt, ...], ...}, ...}
    routes = set()
    for traj in traj_info:
        route = (traj['intersection_id'], traj['tollgate_id'])
        routes.add(route)
        # avg_travel_time.setdefault(route, {})
        # avg_travel_time[route].setdefault(traj['time_window'], []).append(float(traj['travel_time']))
        avg_travel_time.setdefault(traj['time_window'], {})
        avg_travel_time[traj['time_window']].setdefault(route, []).append(float(traj['travel_time']))

    tws = avg_travel_time.keys()
    tws.sort()
    routes = list(routes)
    routes.sort()
    output_keys = ['win_start','time_of_win','weekday'] + \
        ['%s_%d' % ('-'.join(x),y) for y in range(n_dps) for x in routes]

    if d_type == 'train':
        ### Add missing time windows with 0 values for all routes ###
        for i in range(1,len(tws)):
            diff_win = (tws[i] - tws[i-1]).seconds / 1200
            if diff_win > 1:
                for j in range(diff_win-1):
                    miss_win = tws[i-1] + timedelta(seconds=1200*(j+1))
                    avg_travel_time[miss_win] = {}
                    for rt in routes:
                        avg_travel_time[miss_win][rt] = [0]
                    print 'Added missing data point: %s %s' % (str(miss_win), avg_travel_time[miss_win])

        ### Update time windws ###
        tws = avg_travel_time.keys()
        tws.sort()

        ### For training data, add target values and creat data points with each 20min window ###
        output_keys += ['y_%s_%d' % ('-'.join(x),y) for y in range(n_dps) for x in routes]
        last_dp = 2*n_dps-1
        dp_to_use = 1
    elif d_type == 'test':
        last_dp = n_dps-1
        dp_to_use = n_dps

    with open(out_file, 'w') as csv_file:
        csv_file.write('%s\n' % ','.join(output_keys))
        # for i, tw in enumerate(tws[:last_dp if last_dp != 0 else None]):
        for i in range(0, len(tws)-last_dp, dp_to_use):
            line = '%s,%s,%d' % (str(tws[i]), str(tws[i+n_dps-1]), tws[i].weekday())
            for j in range(n_dps):
                for rt in routes:
                    if rt in avg_travel_time[tws[i+j]]:
                        line = '%s,%.4f' % (line, np.mean(avg_travel_time[tws[i+j]][rt]))
                    else:
                        line = '%s,0' % line

            if d_type == 'train':
                for j in range(n_dps):
                    for rt in routes:
                        if rt in avg_travel_time[tws[n_dps+i+j]]:
                            line = '%s,%.4f' % (line, np.mean(avg_travel_time[tws[n_dps+i+j]][rt]))
                        else:
                            line = '%s,0' % line

            csv_file.write(line+'\n')

    return


def parseVolumeFile(in_file, time_fmt='%Y-%m-%d %H:%M:%S'):
    '''
    Parse data file and aggregate volume info
    Format:
        "time","tollgate_id","direction","vehicle_model","has_etc","vehicle_type"
        "2016-09-19 23:09:25","2","0","1","0",""

    '''

    vol_info = readCSVToList(in_file, 'time', time_fmt)
    return vol_info


def dumpAverageVolume(vol_info, out_file, d_type, n_dps):
    ''''
    Aggregate and dump traffic volume info
    '''

    agg_vol = {} # {(intersec, tollgate):{time_window: [tt, ...], ...}, ...}
    tollgates = set()
    for vol in vol_info:
        toll_dir = (vol['tollgate_id'], vol['direction'])
        tollgates.add(toll_dir)
        # agg_vol.setdefault(toll_dir, {})
        # agg_vol[toll_dir].setdefault(vol['time_window'], []).append(1)
        agg_vol.setdefault(vol['time_window'], {})
        agg_vol[vol['time_window']].setdefault(toll_dir, []).append(1)

    tws = agg_vol.keys()
    tws.sort()
    tollgates = list(tollgates)
    tollgates.sort()
    output_keys = ['win_start','time_of_win','weekday'] + \
        ['%s_%d' % ('-'.join(x),y) for y in range(n_dps) for x in tollgates]

    if d_type == 'train':
        ### For training data, add target values and creat data points with each 20min window ###
        output_keys += ['y_%s_%d' % ('-'.join(x),y) for y in range(n_dps) for x in tollgates]
        last_dp = 2*n_dps-1
        dp_to_use = 1
    elif d_type == 'test':
        last_dp = n_dps-1
        dp_to_use = n_dps

    with open(out_file, 'w') as csv_file:
        csv_file.write('%s\n' % ','.join(output_keys))
        # for i, tw in enumerate(tws[:last_dp if last_dp != 0 else None]):
        for i in range(0, len(tws)-last_dp, dp_to_use):
            line = '%s,%s,%d' % (str(tws[i]), str(tws[i+n_dps-1]), tws[i].weekday())
            for j in range(n_dps):
                for toll in tollgates:
                    if toll in agg_vol[tws[i+j]]:
                        line = '%s,%d' % (line, len(agg_vol[tws[i+j]][toll]))
                    else:
                        line = '%s,0' % line

            if d_type == 'train':
                for j in range(n_dps):
                    for toll in tollgates:
                        if toll in agg_vol[tws[n_dps+i+j]]:
                            line = '%s,%d' % (line, len(agg_vol[tws[n_dps+i+j]][toll]))
                        else:
                            line = '%s,0' % line

            csv_file.write(line+'\n')

    return 


def main():

    parser = argparse.ArgumentParser(description="Script to parse volume and traffic time data file")

    parser.add_argument('--traj-file',
        dest='traj_in',
        action='store',
        help='Trajectory data file',
        type=str,
        default='../dataSets/training/trajectories_table5_training.csv')

    parser.add_argument('--vol-file',
        dest='vol_in',
        action='store',
        help='Traffic volume data file',
        type=str,
        default='../dataSets/training/volume_table6_training.csv')

    parser.add_argument('--data-type',
        dest='d_type',
        action='store',
        help='Type of data: train or test',
        type=str,
        default='train')

    parser.add_argument('--win-size',
        dest='win_size',
        action='store',
        help='Number of data points in a training window',
        type=int,
        default=6)

    # parser.add_argument('--dump-target',
    #     dest='tar_val',
    #     action='store',
    #     help='Include target values in output files',
    #     type=bool,
    #     default=False)

    args = parser.parse_args()

    traj_in_file = args.traj_in
    traj_out_file = '%s_20min_avg_%d_window.csv' % (traj_in_file.split('.csv')[0], args.win_size)
    vol_in_file = args.vol_in
    vol_out_file = '%s_20min_avg_%d_window.csv' % (vol_in_file.split('.csv')[0], args.win_size)

    traj_info = parseTrajFile(traj_in_file)
    vol_info = parseVolumeFile(vol_in_file)
    dumpAverageTravelTime(traj_info, traj_out_file, args.d_type, args.win_size)
    dumpAverageVolume(vol_info, vol_out_file, args.d_type, args.win_size)
    print 'Output files: \n%s\n%s\n' % (traj_out_file, vol_out_file)

if __name__ == '__main__':
    main()



