#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 14:14:22 2022

This library is created to assist the user in calculating the MoI measured on a trifilar pendulum using 4 datasets obtained
from video editing sw Blender. the first data set describing the motion of the centre of the plate of the pendulum. 



@author: basstijnen
"""
from __future__ import division
import numpy as np
from matplotlib import pyplot as plt
from scipy.fft import fft, rfft, rfftfreq, ifft
import scipy.signal
import pandas as pd
import os
import glob

n = 5

def rename_headers(df):
    #find headers names
    headers = df.columns.to_list()
    columns_to_delete = range(3, len(df.columns),4)
    df = df.drop(df.columns[columns_to_delete], axis=1)
    new_column_names = {0:'frame_num',1:'x_pos_centre', 2:  'y_pos_centre'}
    remaining_columns = df.columns[3:]
    new_remaning_columns = [f'pos_{i//2}_{i%2}'for i in range(len(remaining_columns))]
    new_column_names.update(zip(remaining_columns, new_remaning_columns))
    df = df.rename(columns=new_column_names)
    return df

def nomalize(df, fps):
    point_nom = df[['frame_num']]
    point_nom.loc[:,'frame_num'] = (df.frame_num/fps)
    point_nom.loc[:,'x_nom_1'] = df.pos_0_0 -df.x_pos_centre
    point_nom.loc[:,'y_nom_1'] = df.pos_0_1 -df.y_pos_centre
    #point_nom.loc[:,'x_nom_2'] = df.pos_1_0 -df.x_pos_centre
    #point_nom.loc[:,'y_nom_2'] = df.pos_1_1 -df.y_pos_centre
    #point_nom.loc[:,'x_nom_3'] = df.pos_2_0 -df.x_pos_centre
    #point_nom.loc[:,'y_nom_3'] = df.pos_2_1 -df.y_pos_centre
    return point_nom

def polar(df):
    df.loc[:,'polar_12'] = np.arctan2(df.y_nom_1, df.x_nom_1)
    df.loc[:,'polar_1'] = np.where(df.polar_12 < 0, df.polar_12 + 2 * np.pi, df.polar_12)
    #df.loc[:,'polar_22'] = np.arctan2(df.y_nom_2, df.x_nom_2)
    #df.loc[:,'polar_2'] = np.where(df.polar_22 < 0, df.polar_22 + 2 * np.pi, df.polar_22)
    #df.loc[:,'polar_32'] = np.arctan2(df.y_nom_3, df.x_nom_3)
    #df.loc[:,'polar_3'] = np.where(df.polar_32 < 0, df.polar_32 + 2 * np.pi, df.polar_32)
    #df = df.drop(columns = ['x_nom_1','y_nom_1','x_nom_2','y_nom_2','x_nom_3','y_nom_3','polar_12', 'polar_22','polar_32'])
    return df

def Filter(df):
    cols = list(df.columns)
    cols.pop(0)
    delete = []
    for column in df[cols]:
        a = df[column].min()
        c =  df[column].max() 
        if abs(c) >= 6.27:
            delete.append(column)
        elif abs(a) <= 0.01:
            delete.append(column)
    df = df.drop(delete,1)
    
    return df



def plot_data(df):
    
    columns = list(df.columns)
    columns.pop(0)
    for columns in df:
        plt.plot(df['frame_num'],df[columns])

    return df

def find_tau(df,column):
    df.loc[:,'max']=df.iloc[scipy.signal.argrelextrema(df[column].values, np.greater_equal, order=n)[0]][column]
    df = df.dropna(subset=['max'])
    df = df.iloc[:-1, :]
    df = df.iloc[1: , :]
    df['period'] = df.frame_num.diff()
    tau = df.period.mean()
    return tau 

def Average(lst):
    cleanedList = [x for x in lst if str(x) != 'nan']
    return sum(cleanedList)/len(cleanedList)

def Find_Moment_Of_Inertia(path,fps, m, R, L):
   
    all_files = glob.glob(os.path.join(path , "*.csv"))

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None)
        li.append(df)
    frame = pd.concat(li, axis=1, ignore_index=True)
    frame = rename_headers(frame)

    frame = nomalize(frame, fps)
    Tau = []
    frame = polar(frame)
    frame = Filter(frame)
    #fig, ax = plt.subplots()
    #plot_data(frame)
    col = list(frame.columns)
    col.pop(0)
    for column in frame[col]:
        tau = find_tau(frame, column)
        Tau.append(tau)

    
    Tau = Average(Tau)
  
    g = 9806 #mm/s^2

    #I = 'commented out'
    I = ((m)*g*(R**2)*(Tau**2)) / (4*L*(np.pi**2))
    return I, frame

def print_tau(path,fps):
    all_files = glob.glob(os.path.join(path , "*.csv"))

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, index_col=None)
        li.append(df)
    frame = pd.concat(li, axis=1, ignore_index=True)
    frame = rename_headers(frame)

    frame = nomalize(frame, fps)
    Tau = []
    frame = polar(frame)
    frame = Filter(frame)
    #fig, ax = plt.subplots()
    #plot_data(frame)
    col = list(frame.columns)
    col.pop(0)
    for column in frame[col]:
        tau = find_tau(frame, column)
        Tau.append(tau)
    Tau = Average(Tau)
    return Tau