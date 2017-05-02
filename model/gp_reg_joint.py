# this models the problem as a regresssoin problem
# data inputs consists a 2-hour window (divided to 20-min frames) of volumns and time information
# data outputs is a 20-min frame of volumn immediately after the 2-hour window. ("Immediately" here means  0 - 1:40 hours after the training inputs)
# the models are GP models with ARD RBF kernels
# build a single model for all different gates, directions, or time frames

#import sklearn as sk
import GPy
import matplotlib.pyplot as plt
import numpy as np
import scipy as sc
import string
import sys
import datetime as dt


# settings
train_filename = "../dataSets/training/volume_table6_training_20min_avg_6_window.csv"
test_filename = "../dataSets/testing_phase1/volume_table6_test1_20min_avg_6_window.csv"
output_filename = "../prediction/"+dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d_%H:%M:%S")+".csv"
max_iters = 200

print "output to: " + output_filename

# load data

train_header = []
test_header = []
train_x = []
train_y = []
test_x  = []
test_times = []

print "load traininging data ..."
with open(train_filename, "r") as f:
  lineNum = 0
  for line in f:
    lineNum += 1
    tokens = string.split(line[0:-1], ","); # remove \n
    if lineNum == 1: # skip header
      train_header =  tokens
      continue
    if len(tokens) != 63:
      print "Invalid input dimension %d." % (len(tokens))
      exit()

    time = dt.datetime.strptime(tokens[1], "%Y-%m-%d %H:%M:%S")
    inputs = [time.hour*3600+time.minute*60+time.second, time.weekday()] +  [float(tok) for tok in tokens[3:33]]
    outputs = [float(tok) for tok in tokens[33:]]
    train_x.append(inputs)
    train_y.append(outputs)
print "done"

print "load test data ..."
with open(test_filename, "r") as f:
  lineNum = 0
  for line in f:
    lineNum += 1
    tokens = string.split(line[0:-1], ","); # remove \n
    if lineNum == 1: # skip header
      test_header =  tokens
      continue
    if len(tokens) != 33:
      print "Invalid input dimension %d." % (len(tokens))
      exit()

    time = dt.datetime.strptime(tokens[1], "%Y-%m-%d %H:%M:%S")
    inputs = [time.hour*3600+time.minute*60+time.second, time.weekday()] +  [float(tok) for tok in tokens[3:33]]
    test_x.append(inputs)
    test_times.append(time)

print "done"


# normalize data
train_x = np.array(train_x)
train_y = np.array(train_y)
test_x  = np.array(test_x)

(num_of_samples, num_of_features) = train_x.shape

mean_train_x = np.mean(train_x, 0)
std_train_x  = np.std (train_x, 0)
norm_train_x = (train_x - mean_train_x) / std_train_x

mean_train_y = np.mean(train_y, 0)
std_train_y  = np.std (train_y, 0)
norm_train_y = (train_y - mean_train_y) / std_train_y

norm_test_x = (test_x - mean_train_x) / std_train_x

# setup models
kernel = GPy.kern.RBF(num_of_features, variance = 1., lengthscale=1., ARD = True)
m = GPy.models.GPRegression(norm_train_x, norm_train_y, kernel)

# training
print "training ..."
m.optimize(messages=True, max_iters = max_iters)
np.save('saves/joint_model_save.npy', m.param_array)
m.kern.plot_ARD()
plt.show()
print "done"

#(pred_mean, pred_var) = m.predict(norm_train_x)
#plt.plot(norm_train_y[:,1], "-")
#plt.plot(pred_mean[:,1], "-r")
#plt.show()

# testing
print "testing ..."
(pred_mean, pred_var) = m.predict(norm_test_x)
pred_y = pred_mean * std_train_y + mean_train_y
print "done"


# output prediction

with open(output_filename, "w" ) as f:
  f.write('tollgate_id,time_window,direction,volume\n')
  for n in xrange(test_x.shape[0]):
    for m in xrange(train_y.shape[1]):
      h        = train_header[33+m]
      gate_num = int(h[2])
      dir_num  = int(h[4])
      shift    = int(h[6])

      time       = test_times[n]
      time_start = time       + dt.timedelta(minutes = 20*(shift+1))
      time_end   = time_start + dt.timedelta(minutes = 20)

      f.write('%d,"[%s,%s)",%d,%f\n' %(gate_num, \
            dt.datetime.strftime(time_start, "%Y-%m-%d %H:%M:%S"), \
            dt.datetime.strftime(time_end, "%Y-%m-%d %H:%M:%S"), \
            dir_num, \
            pred_y[n,m]))
