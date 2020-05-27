#%%
import random
import matplotlib.pyplot as plt
import tensorflow as tf
import tensorflow.keras as keras
from itertools import product
import pandas as pd

import numpy as np
import pickle

from sklearn.model_selection import StratifiedKFold
from math import log2, ceil 

import sys
sys.path.append("../../src/")
from lifelong_dnn import LifeLongDNN
from joblib import Parallel, delayed

#%%
def unpickle(file):
    with open(file, 'rb') as fo:
        dict = pickle.load(fo, encoding='bytes')
    return dict
    
#%%
def LF_experiment(train_x, train_y, test_x, test_y, ntrees, shift, acorn=None):
       
    df = pd.DataFrame()
    single_task_accuracies = np.zeros(10,dtype=float)
    shifts = []
    tasks = []
    base_tasks = []
    accuracies_across_tasks = []

    for task_ii in range(10):
        single_task_learner = LifeLongDNN()

        if acorn is not None:
            np.random.seed(acorn)

        single_task_learner.new_forest(
            train_x[task_ii*5000:(task_ii+1)*5000,:], train_y[task_ii*5000:(task_ii+1)*5000], 
            max_depth=ceil(log2(5000)), n_estimators=ntrees*(task_ii+1)
            )
        llf_task=single_task_learner.predict(
            test_x[task_ii*1000:(task_ii+1)*1000,:], representation=0, decider=0
            )
        single_task_accuracies[task_ii] = np.mean(
                llf_task == test_y[task_ii*1000:(task_ii+1)*1000]
                )

    lifelong_forest = LifeLongDNN()
    for task_ii in range(10):
        print("Starting Task {} For Fold {}".format(task_ii, shift))
        if acorn is not None:
            np.random.seed(acorn)

        lifelong_forest.new_forest(
            train_x[task_ii*5000:(task_ii+1)*5000,:], train_y[task_ii*5000:(task_ii+1)*5000], 
            max_depth=ceil(log2(5000)), n_estimators=ntrees
            )
        
        '''llf_task=lifelong_forest.predict(
            test_x[task_ii*1000:(task_ii+1)*1000,:], representation=task_ii, decider=task_ii
            )
        single_task_accuracies[task_ii] = np.mean(
                llf_task == test_y[task_ii*1000:(task_ii+1)*1000]
                )'''
        
        for task_jj in range(task_ii+1):
            llf_task=lifelong_forest.predict(
                test_x[task_jj*1000:(task_jj+1)*1000,:], representation='all', decider=task_jj
                )
            
            shifts.append(shift)
            tasks.append(task_jj+1)
            base_tasks.append(task_ii+1)
            accuracies_across_tasks.append(np.mean(
                llf_task == test_y[task_jj*1000:(task_jj+1)*1000]
                ))
            
    df['data_fold'] = shifts
    df['task'] = tasks
    df['base_task'] = base_tasks
    df['accuracy'] = accuracies_across_tasks

    df_single_task = pd.DataFrame()
    df_single_task['task'] = range(1, 11)
    df_single_task['data_fold'] = shift
    df_single_task['accuracy'] = single_task_accuracies

    summary = (df,df_single_task)
    file_to_save = 'result/'+'LF_'+str(ntrees)+'__'+str(shift)+'.pickle'
    with open(file_to_save, 'wb') as f:
        pickle.dump(summary, f)

#%%
def cross_val_data(data_x, data_y, class_idx, total_cls=100, shift=1):
    x = data_x.copy()
    y = data_y.copy()
    idx = class_idx.copy()
    
    
    for i in range(total_cls):
        indx = np.roll(idx[i],(shift-1)*100)
        
        if i==0:

            train_x = x[indx[0:500],:]
            test_x = x[indx[500:600],:]

            train_y = y[indx[0:500]]
            test_y = y[indx[500:600]]
        else:
            train_x = np.concatenate((train_x, x[indx[0:500],:]), axis=0)
            test_x = np.concatenate((test_x, x[indx[500:600],:]), axis=0)

            train_y = np.concatenate((train_y, y[indx[0:500]]), axis=0)
            test_y = np.concatenate((test_y, y[indx[500:600]]), axis=0)
        
        
    return train_x, train_y, test_x, test_y

#%%
def run_parallel_exp(data_x, data_y, class_idx, n_trees, total_cls=100, shift=1):
    train_x, train_y, test_x, test_y = cross_val_data(data_x, data_y, class_idx, shift=shift)
    LF_experiment(train_x, train_y, test_x, test_y, n_trees, shift, acorn=12345)

#%%
(X_train, y_train), (X_test, y_test) = keras.datasets.cifar100.load_data()
data_x = np.concatenate([X_train, X_test])
data_x = data_x.reshape((data_x.shape[0], data_x.shape[1] * data_x.shape[2] * data_x.shape[3]))
data_y = np.concatenate([y_train, y_test])
data_y = data_y[:, 0]


class_idx = [np.where(data_y == u)[0] for u in np.unique(data_y)]

#%%
shift_fold = range(1,7,1)
n_trees=[10,20,30,40,50]
iterable = product(n_trees,shift_fold)

Parallel(n_jobs=-2,verbose=1)(
    delayed(run_parallel_exp)(
            data_x, data_y, class_idx, ntree, total_cls=100, shift=i
            ) for ntree,i in iterable
            )

#for i in range(1,7):
#    print('doing %d fold'%i)
#    run_parallel_exp(data_x, data_y, class_idx, n_trees, total_cls=100, shift=i)

# %%
