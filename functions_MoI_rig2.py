#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 14:14:22 2022

Updated 2026:
- pandas 2.x compatible
- No SettingWithCopyWarning
- Explicit dtypes
- Safer DataFrame handling

@author: basstijnen
"""

import numpy as np
import pandas as pd
import glob
import os
import scipy.signal
from matplotlib import pyplot as plt

n = 5  # extrema detection window


# ----------------------------
# Data preparation
# ----------------------------

def rename_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Drop Blender junk columns
    columns_to_delete = range(3, len(df.columns), 4)
    df = df.drop(df.columns[list(columns_to_delete)], axis=1)

    new_column_names = {
        0: 'frame_num',
        1: 'x_pos_centre',
        2: 'y_pos_centre'
    }

    remaining_columns = df.columns[3:]
    new_remaining_columns = [
        f'pos_{i // 2}_{i % 2}' for i in range(len(remaining_columns))
    ]

    new_column_names.update(dict(zip(remaining_columns, new_remaining_columns)))
    df = df.rename(columns=new_column_names)

    return df


def normalize(df: pd.DataFrame, fps: float) -> pd.DataFrame:
    point_nom = df[['frame_num', 'pos_0_0', 'pos_0_1',
                    'x_pos_centre', 'y_pos_centre']].copy()

    point_nom.loc[:, 'frame_num'] = (point_nom['frame_num'] / fps).astype(float)
    point_nom.loc[:, 'x_nom_1'] = point_nom['pos_0_0'] - point_nom['x_pos_centre']
    point_nom.loc[:, 'y_nom_1'] = point_nom['pos_0_1'] - point_nom['y_pos_centre']

    return point_nom[['frame_num', 'x_nom_1', 'y_nom_1']]


def polar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.loc[:, 'polar_12'] = np.arctan2(df['y_nom_1'], df['x_nom_1'])
    df.loc[:, 'polar_1'] = np.where(
        df['polar_12'] < 0,
        df['polar_12'] + 2 * np.pi,
        df['polar_12']
    )

    return df


def Filter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    delete = []
    for column in df.columns[1:]:
        col_min = df[column].min()
        col_max = df[column].max()

        if abs(col_max) >= 6.27 or abs(col_min) <= 0.01:
            delete.append(column)

    if delete:
        df = df.drop(columns=delete)

    return df


# ----------------------------
# Analysis functions
# ----------------------------

def plot_data(df: pd.DataFrame):
    for column in df.columns[1:]:
        plt.plot(df['frame_num'], df[column])
    plt.show()


def find_tau(df: pd.DataFrame, column: str) -> float:
    df = df.copy()

    extrema_idx = scipy.signal.argrelextrema(
        df[column].values,
        np.greater_equal,
        order=n
    )[0]

    df.loc[:, 'max'] = np.nan
    df.loc[extrema_idx, 'max'] = df.loc[extrema_idx, column]

    df = df.dropna(subset=['max'])
    df = df.iloc[1:-1].copy()

    df.loc[:, 'period'] = df['frame_num'].diff()

    return df['period'].mean()


def find_angle(df: pd.DataFrame) -> float:
    df = df.copy()

    df.loc[:, 'angle'] = df['polar_1'] * 180 / np.pi

    extrema_idx = scipy.signal.argrelextrema(
        df['angle'].values,
        np.greater_equal,
        order=n
    )[0]

    max_angles = df.loc[extrema_idx, 'angle']

    return (max_angles.max() - max_angles.min()) / 2


def Average(values):
    values = [v for v in values if not pd.isna(v)]
    return sum(values) / len(values)


# ----------------------------
# Main public API
# ----------------------------

def Find_Moment_Of_Inertia(path, fps, m, R, L):
    files = glob.glob(os.path.join(path, "*.csv"))
    frames = [pd.read_csv(f) for f in files]

    frame = pd.concat(frames, axis=1, ignore_index=True)
    frame = rename_headers(frame)
    frame = normalize(frame, fps)
    frame = polar(frame)
    frame = Filter(frame)

    angle = find_angle(frame)

    Tau = []
    for column in frame.columns[1:]:
        Tau.append(find_tau(frame, column))

    Tau = Average(Tau)

    g = 9806  # mm/s^2
    I = (m * g * R**2 * Tau**2) / (4 * L * np.pi**2)

    return I, frame, angle


def print_tau(path, fps):
    files = glob.glob(os.path.join(path, "*.csv"))
    frames = [pd.read_csv(f) for f in files]

    frame = pd.concat(frames, axis=1, ignore_index=True)
    frame = rename_headers(frame)
    frame = normalize(frame, fps)
    frame = polar(frame)
    frame = Filter(frame)

    Tau = []
    for column in frame.columns[1:]:
        Tau.append(find_tau(frame, column))

    return Average(Tau)
