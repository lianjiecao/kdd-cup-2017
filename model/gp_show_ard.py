# show the importance of each dimension in the learned model
# Usage: python gp_show_ard.py [dimension #]
# where dimension # range from 0 to 29

import GPy
import matplotlib.pyplot as plt
import numpy as np
import scipy as sc
import string
import sys
import datetime as dt


if len(sys.argv) != 2:
  print "Usage: python %s [model number]" %(sys.argv[0])
  exit()

# settings
train_filename = "../dataSets/training/volume_table6_training_20min_avg_6_window.csv"
test_filename = "../dataSets/testing_phase1/volume_table6_test1_20min_avg_6_window.csv"

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


# compute labels
dim      = int(sys.argv[1])
h        = train_header[33+dim]
print h + ": gate " + h[2] + " dir " + h[4] + " shift " + h[6] 

# load model
kernel = GPy.kern.RBF(num_of_features, variance = 1., lengthscale=1., ARD = True)
m_load = GPy.models.GPRegression(norm_train_x, np.reshape(norm_train_y[:,dim], (norm_train_x.shape[0], 1)), kernel, initialize=False)
m_load.update_model(False)
m_load.initialize_parameter()
m_load[:] = np.load('saves/sep_model_save_%d.npy'%(dim))
m_load.update_model(True) 

# plot importance and performance on training data
m_load.kern.plot_ARD()


plt.figure(2)
(pred_mean, pred_var) = m_load.predict(norm_train_x)
plt.plot(norm_train_y[:,dim], "-")
plt.plot(pred_mean, "-r")
plt.show()


