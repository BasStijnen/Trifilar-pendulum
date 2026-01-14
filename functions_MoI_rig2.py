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

    point_nom['frame_num'] = point_nom['frame_num'].to_numpy(dtype=float) / float(fps)
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

def calculate_expected_error(I_object, MoI_platform, L, R, m, sigma_L=0.001, sigma_R=0.001,
                             sigma_m=0.001, sigma_T=0.001, g=9.80665):
    """
    Calculate expected relative MoI error for a trifilar suspension system.

    """
    I_total = MoI_platform + I_object

    # Compute period
    T = np.sqrt((4 * np.pi**2 * L * I_total) / (m * g * R**2))

    # Partial derivatives
    dI_dm = (g * R**2 / (4 * np.pi**2 * L)) * T**2
    dI_dR = (2 * m * g * R / (4 * np.pi**2 * L)) * T**2
    dI_dL = -(m * g * R**2 / (4 * np.pi**2 * L**2)) * T**2
    dI_dT = (2 * m * g * R**2 / (4 * np.pi**2 * L)) * T

    # Total uncertainty
    sigma_I = np.sqrt(
        (dI_dm * sigma_m)**2 +
        (dI_dR * sigma_R)**2 +
        (dI_dL * sigma_L)**2 +
        (dI_dT * sigma_T)**2
    )

    # Avoid division by zero
    relative_error = np.where(I_object > 0, sigma_I / I_object, np.nan)
    return relative_error