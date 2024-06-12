import re
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
from lab_bepcodes import *
from sklearn.preprocessing import MinMaxScaler
import joblib


def load_data(file_path):
    """ Loads the data """

    df = pd.read_csv(file_path, sep=';', na_values=[''])
    df['AANKSDATUM'] = pd.to_datetime(df['AANKSDATUM'])

    return df


def merge_datetime(date_col, time_col):
    """ Merges date and time columns into one column """

    date_col = pd.to_datetime(date_col).astype(str)

    return pd.to_datetime(date_col + ' ' + time_col, format='%Y-%m-%d %H:%M:%S')


def handle_negative_deltas(df):
    """ Checks and fixes negative timedeltas """

    neg_indices = df['delta'] < timedelta(0)
    df.loc[neg_indices, 'datetime'] = df.loc[neg_indices, 'datetime'] + timedelta(days=1)  

    return df


def time_to_datetime(arrival_dates, *times):
    """ Converts a time column to a DateTime column with the help of a column which contains the date """

    res = []
    dates = pd.to_datetime(arrival_dates).dt.strftime('%Y-%m-%d')

    for time in times:

        datetime = merge_datetime(dates, time)
        df = pd.DataFrame({'datetime': datetime, 'delta': datetime - arrival_dates})
        df = handle_negative_deltas(df)  # if the time is the next day we get a negative timedelta, so we need to fix this
        res.append(df['datetime'])
    
    return res

def remove_negative_time_deltas(df_lab):
    """ Removes records of lab results which are before the ED visit """

    pos_time_delta = df_lab['AFNAME_TIJDSTIP'] - df_lab['AANKOMST_TIJDSTIP'] > '00:00:00'
    df_lab = df_lab[pos_time_delta]

    return df_lab
    

def merge_bep_codes(df, bepcodes, label):
    """ Merges bepcodes which belong to the same lab result """

    df.loc[df['BEPCODE'].isin(bepcodes), 'DESC'] = label

    return df


def get_lab_results(df, bepcodes):
    """ Obtain the results corresponding to the given bepcode """
    return df[df['BEPCODE'].isin(bepcodes)]


def scale_data(df):

    for desc in df['DESC'].unique():

        scaler = MinMaxScaler()
        df_lab_val = df[df['DESC'] == desc]
        df.loc[df['DESC'] == desc, 'UITSLAG'] = scaler.fit_transform(df_lab_val[['UITSLAG']])

        joblib.dump(scaler, f'{desc.replace(" ", "_")}_scaler.pk1')

    return df


def remove_angle_bracketes(item):
    """ Removes angle brackets ('<' and '>')from the item """
    return re.sub(r'^[<>]', '', str(item))  # results like < 5 get replaced by 5, so that it is numeric


def to_numeric(item):
    """ Tries to convert item to a numeric value, else it will be replaced by a NaN value """

    try:
        item = float(item)
    except ValueError:
        item = np.nan

    return item


def set_negative_to_zero(item):
    """ Sets the word negatief to 0 """
    return 0 if item == 'negatief' else item


def is_categorical_range_data(item):
    """ Checks if data is categorical range data (data like '100-200') """
    return re.match(r'^\d+\s*-\s*\d+$', item) 


def calculate_mean(item):
    """ Calculates the mean of categorical range data (data like '100-200' becomes '150') """

    numbers = [int(num) for num in item.split('-')]
    return np.mean(numbers)


def clean_data(data):
    """ 
        Cleans the numerical data: 
        1. Calculate the mean of categorical range data
        2. Removes angle bracketers
        3. Sets the word negatief to 0
        4. Converts to numeric (if possible, else NaN)
    """

    data = [calculate_mean(item.strip()) if is_categorical_range_data(item) else item for item in data]
    data = [to_numeric(set_negative_to_zero(remove_angle_bracketes(item))) for item in data]

    return data


def write_out_file(file_path, df):
    """ Writes the output file ifn csv format """
    with open(file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(df.to_csv(sep=';', index=False))



if __name__ == '__main__':
    # LOAD DATA
    df_lab = load_data(sys.argv[1])

    # GET RIGHT LEB RESULTS
    df_lab = get_lab_results(df_lab, all_bepcodes)
    df_lab = merge_bep_codes(df_lab, ureum_poc, 'Ureum (POC)')
    df_lab = merge_bep_codes(df_lab, kreat_poc, 'Kreat (POC)')
    df_lab = merge_bep_codes(df_lab, natrium_poc, 'Natrium (POC)')
    df_lab = merge_bep_codes(df_lab, kalium_poc, 'kalium (POC)')
    df_lab = merge_bep_codes(df_lab, glucose_poc, 'Glucose (POC)')
    df_lab = merge_bep_codes(df_lab, lactaat_poc, 'Lactaat (POC)')
    df_lab = merge_bep_codes(df_lab, glucose, 'Glucose')


    # HANDLE TIME DATA
    df_lab = df_lab[df_lab['AANKSDATUM'] < '20230101']
    df_lab['AANKOMST_TIJDSTIP']   = merge_datetime(df_lab['AANKSDATUM'], df_lab['AANKSTIJD'])
    df_lab['AFNAME_TIJDSTIP']   = merge_datetime(df_lab['AFDATUM'], df_lab['AFTIJD'])
    df_lab['UITSLAG_TIJDSTIP'] = time_to_datetime(df_lab['AFNAME_TIJDSTIP'], df_lab['UITTIJD'])[0]
    df_lab = remove_negative_time_deltas(df_lab)
    df_lab = df_lab.drop(columns=['AANKSDATUM', 'AANKSTIJD', 'AFDATUM', 'AFTIJD','UITTIJD', 'MATAARD', 'BESTEMMING'], axis=1)
    
    # CLEAN NUMERIC VALUES
    numeric_category_bepcodes = [glucose_urine, leukocyt_urine, crp]
    for bepcode in all_bepcodes:

        data = df_lab[df_lab['BEPCODE'] == bepcode]['UITSLAG']  # get lab result of that bepcode
        df_lab.loc[df_lab['BEPCODE'] == bepcode, 'UITSLAG'] = clean_data(data)  # overwrite the non-cleaned data
    
    # SCALE DATA
    df_lab = scale_data(df_lab)

    # WRITE OUTPUT FILE
    out_path = sys.argv[1].rsplit('/', maxsplit=1)[0] + f'/processed/{date.today()}'
    write_out_file(f'{out_path}_LAB_processed.csv', df_lab)


    