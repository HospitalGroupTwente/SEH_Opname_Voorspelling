import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib


def load_data(input_data):
    """ Loads the data """

    df = pd.DataFrame(input_data)

    return df


def cols_to_datetime(df, *cols):
    """ Converts the given cols to datetime fromat """

    for col in cols:
        df[col] = pd.to_datetime(df[col])
   
    return df


def merge_datetime(date_col, time_col):
    """ Merges date and time column into one column """

    date_col = pd.to_datetime(date_col).astype(str)
    return pd.to_datetime(date_col + ' ' + time_col, format='%Y-%m-%d %H:%M:%S')


def to_float_data(df, col):
    """ Converts the dataframe column to float data """

    df[col] = df[col].astype(str).str.replace(',', '.')  # in Dutch the decimal is . and not ,
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df[df[col].notna()]

    return df


def remove_impossible_data(df, value_col, lower_limit, upper_limit):
    """ Removes all data outside of the given ranges """
    df.loc[(df[value_col] < lower_limit) & (df[value_col] > upper_limit)] = np.nan
    return df


def scale_data(df, label, vital_scalers_folder):


    if (len(df[['Value1']]) > 0) and (label != 'MEWS score'):
        scaler = joblib.load(f'{vital_scalers_folder}/{label}_scaler.pk1')
        df['Value1'] = scaler.transform(df[['Value1']])

    return df


def clean_vital_data(df, label, col, lower_lim, upper_lim, config):
    """ Cleans the data of the vital data """
    # Heartrate has two labels (HR and POLS), given in a list

    df_vital = df[df['LABEL'] == label]

    df_vital = df_vital.dropna(subset=[col])
    df_vital = remove_impossible_data(df_vital, col, lower_lim, upper_lim)
    df_vital = scale_data(df_vital, label, config['vitals_scaler_dir'])

    # set the old data to the new cleaned data
    df.loc[df['LABEL'] == label] = df_vital

    return df


def get_most_recent_data(df):
    """ Gets the most recent vital results of a patient """
    # A patient can have multiple of the same vital results, we only want the most recent value
    df = df.sort_values('DateTime')
    df = df.groupby(['PATIENTNR', 'LABEL']).last().reset_index()

    return df


def to_tidy_format(df):
    """ Converts wide format to tidy format """
    all_vitals = ['Temp', 'Resp', 'NIBP', 'MEWS score', 'HR']
    df = df.pivot(index='PATIENTNR', columns='LABEL', values='Value1').reset_index()
    missing_cols = [vital for vital in all_vitals if vital not in df.columns]
    df[missing_cols] = np.nan
    return df


def preprocess_vital_data(input_data, config):
    # LOADING TE DATA
    df_vitals = load_data(input_data)
    df_vitals.loc[df_vitals['LABEL'].isin(['HR', 'POLS']), 'LABEL'] = 'HR'  # set same label name for heartrate
    df_vitals = to_float_data(df_vitals, 'Value1')

    # CLEANING THE DATA
    df_vitals = clean_vital_data(df_vitals, 'Temp', 'Value1', 25, 45, config)
    df_vitals = clean_vital_data(df_vitals, 'Resp', 'Value1', 3, 50, config)
    df_vitals = clean_vital_data(df_vitals, 'NIBP', 'Value1', 50, 250, config)
    df_vitals = clean_vital_data(df_vitals, 'MEWS score', 'Value1', 0, 3, config)
    df_vitals = clean_vital_data(df_vitals, 'HR', 'Value1', 30, 200, config)
    df_vitals = get_most_recent_data(df_vitals)
   
    
    # WRITING OUTPUT
    df_vitals = to_tidy_format(df_vitals)
    
    return df_vitals
    

