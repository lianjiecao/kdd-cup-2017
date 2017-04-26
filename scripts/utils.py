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



def parseTrajFile(in_file):
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
                # t[1] = time.mktime(time.strptime(t[1], fmt_str))
                t[1] = datetime.strptime(t[1], '%Y-%m-%d %H:%M:%S')
            rec.update({'travel_seq':travel_seq})
            # rec.update({'starting_time':time.mktime(time.strptime(rec['starting_time'], fmt_str))})
            rec.update({'starting_time':datetime.strptime(rec['starting_time'], '%Y-%m-%d %H:%M:%S')})
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


def dumpAverageTravelTime(traj_info, out_file):
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

    # for rt in avg_travel_time:
    #     tws = avg_travel_time[rt].keys()
    #     tws.sort()
    #     for tw in tws:
    #         print('%s-%s %s %.4f' % (rt[0], rt[1], str(tw), np.mean(avg_travel_time[rt][tw])))

    tws = avg_travel_time.keys()
    tws.sort()
    routes = list(routes)
    routes.sort()

    with open(out_file, 'w') as csv_file:
        csv_file.write('window_start,%s\n' % ','.join(['%s-%s' % (x[0], x[1]) for x in routes]))
        for tw in tws:
            line = str(tw)
            for rt in routes:
                if rt in avg_travel_time[tw]:
                    line = '%s,%.4f' % (line, np.mean(avg_travel_time[tw][rt]))
                else:
                    line = '%s,0' % line

            csv_file.write(line+'\n')

    return


def parseVolumeFile(in_file):
    '''
    Parse data file and aggregate volume info
    Format:
        "time","tollgate_id","direction","vehicle_model","has_etc","vehicle_type"
        "2016-09-19 23:09:25","2","0","1","0",""

    '''

    vol_info = readCSVToList(in_file, time_key='time', time_fmt='%Y-%m-%d %H:%M:%S')
    return vol_info


def dumpAverageVolume(vol_info, out_file):
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

    with open(out_file, 'w') as csv_file:
        csv_file.write('window_start,%s\n' % ','.join(['%s-%s' % (x[0], x[1]) for x in tollgates]))
        for tw in tws:
            line = str(tw)
            for toll in tollgates:
                if toll in agg_vol[tw]:
                    line = '%s,%d' % (line, len(agg_vol[tw][toll]))
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

    parser.add_argument('--vol-in',
        dest='vol_in',
        action='store',
        help='Traffic volume data file',
        type=str,
        default='../dataSets/training/volume_table6_training.csv')

    args = parser.parse_args()

    traj_in_file = args.traj_in
    traj_out_file = '%s_20min_avg.csv' % traj_in_file.split('.csv')[0]
    vol_in_file = args.vol_in
    vol_out_file = '%s_20min_avg.csv' % vol_in_file.split('.csv')[0]

    traj_info = parseTrajFile(traj_in_file)
    vol_info = parseVolumeFile(vol_in_file)
    dumpAverageTravelTime(traj_info, traj_out_file)
    dumpAverageVolume(vol_info, vol_out_file)

if __name__ == '__main__':
    main()



