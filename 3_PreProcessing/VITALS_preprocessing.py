import sys
from datetime import date

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib


def load_data(file_path):
    """ Loads the csv data """
    return pd.read_csv(file_path, sep=';')


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

    df[col] = df[col].str.replace(',', '.')  # in Dutch the decimal is . and not ,
    df[col] = df[col].astype(float)

    return df


def remove_impossible_data(df, value_col, lower_limit, upper_limit):
    """ Removes all data outside of the given ranges """
    df.loc[(df[value_col] < lower_limit) & (df[value_col] > upper_limit)] = np.nan
    return df


def scale_data(df):

    scaler = MinMaxScaler()

    label = df['LABEL'].unique()[0]
    df['Value1'] =  scaler.fit_transform(df[['Value1']])

    joblib.dump(scaler, f'{label}_scaler.pk1')

    return df




def clean_vital_data(df, label, col, lower_lim, upper_lim):
    """ Cleans the data of the vital data """
    
    df_vital = df[df['LABEL'] == label]

    df_vital = df_vital.dropna(subset=[col])
    df_vital = remove_impossible_data(df_vital, col, lower_lim, upper_lim)
    if label != 'MEWS score':  # MEWS score is range from 0 to 3, no need to scale
        df_vital = scale_data(df_vital)

    return df_vital



def write_dataframe_to_csv(file_path, df, chunk_size=10000):
    """ Writes the dataframe in chunks to the output file """
    # write the header only once at the beginning
    header_written = False
    
    # get the total number of rows in the df
    total_rows = len(df)
    
    # determine the number of chunks needed based on chunk_size
    num_chunks = -(-total_rows // chunk_size)  

    # iterate through the df in chunks and write to the file
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        df_chunk = df.iloc[start_idx:end_idx]
        
        mode = 'w' if not header_written else 'a'

        with open(file_path, mode, encoding='utf-8') as outfile:
            outfile.write(df_chunk.to_csv(sep=';', index=False, header=not header_written))
        
        # after writing the header once, set the flag to True
        header_written = True


if __name__ == '__main__':
    # LOADING TE DATA
    df_vitals = load_data(sys.argv[1])
    
    df_vitals = cols_to_datetime(df_vitals, 'AANKSDATUM', 'DateTime')
    df_vitals['AANKOMST'] = merge_datetime(df_vitals['AANKSDATUM'], df_vitals['AANKSTIJD'])
    df_vitals = df_vitals.drop(['AANKSDATUM', 'AANKSTIJD', 'Value2'], axis=1)

    # CONVERT TO FLOAT (handles ',' decimals)
    df_vitals = to_float_data(df_vitals, 'Value1')
    # CLEANING AND SCALIGN THE DATA
    df_vitals.loc[df_vitals['LABEL'].isin(['HR', 'POLS']), 'LABEL'] = 'HR'  # set same label name for heartrate
    df_temp = clean_vital_data(df_vitals, 'Temp', 'Value1', 25, 45)
    df_resp = clean_vital_data(df_vitals, 'Resp', 'Value1', 3, 50)
    df_nibp = clean_vital_data(df_vitals, 'NIBP', 'Value1', 50, 250)
    # df_vitals = clean_vital_data(df_vitals, 'NIBP', 'Value2', 10, 150)
    df_mews = clean_vital_data(df_vitals, 'MEWS score', 'Value1', 0, 3)
    df_hr = clean_vital_data(df_vitals, 'HR', 'Value1', 30, 200)
    df_vitals = pd.concat([df_temp, df_resp, df_nibp, df_mews, df_hr])

    # WRITING OUTPUT
    out_path = sys.argv[1].rsplit('/', maxsplit=1)[0] + f'/processed/{date.today()}'
    write_dataframe_to_csv(f'{out_path}_VITALS_processed.csv', df_vitals)
    

