import re
import sys
from datetime import date, timedelta
from functools import reduce

import numpy as np
import pandas as pd
import yaml
import joblib


bepcodes = {'Glucose': ['@0002464', 'CS000251'], 'Trombocyten': 'CS000009', 'Hematocriet': 'CS000002',
            'Kalium': 'CS000168', 'CRP': 'CS000277', 'Leucocyten': 'CS000013', 'Kreatinine': 'CS000187',
            'Hemoglobine': 'CS000001', 'Natrium': 'CS000165', 'Bilirubine Totaal': 'CS000197',
            'Alkalische Fosfatase (AF)': 'CS000203', 'ASAT': 'CS000208', 'ALAT': 'CS000211', 'LD': 'CS000214',
            'GGT': 'CS000205', 'Ureum': 'CS000184', 'Glucose (POC)': ['CS000267', 'CS002485'],
            'Leukocyten': 'CS003762', 'Lactaat': 'CS001401', 'NT-proBNP': 'ZGT00473', 'hsTroponine T': 'ZGT00324',
            'kalium (POC)': ['ZGT01265', 'ZGT01264'], 'Natrium (POC)': ['ZGT01448', 'ZGT01452'], 
            'Lactaat (POC)': ['@0002710', 'ZGT01324'], 'Ureum (POC)': ['ZGT01761', 'ZGT01766'],'Kreat (POC)': ['ZGT01318', 'ZGT01321']}


#####################
# loaidng function  #
#####################

def load_data(input_data):
    """ Loads the data """

    df = pd.DataFrame(input_data)
    df = df[df['UITSLAG'].notna()]
    df = df[df['UITSLAG'] != 'NA']

    return df


#######################
# date time functions #
#######################

def merge_datetime(date_col, time_col):
    """ Merges date and time columns into one column """
    date_col = pd.to_datetime(date_col).astype(str)
    return pd.to_datetime(date_col + ' ' + time_col, format='%Y-%m-%d %H:%M:%S')


def get_latest_lab_results(df):
    """ Gets the most recent lab results of a patient """
    # A patient can have multiple of the same lab results, we only want the most recent value
    df = df.sort_values('UITSLAG_TIJDSTIP')
    df = df.groupby(['PATIENTNR', 'DESC']).last().reset_index()

    return df


############################
# clean lab data functions #
############################

def merge_bep_codes(df, bepcodes, label):
    """ Merges bepcodes which belong to the same lab result """

    df.loc[df['BEPCODE'].isin(bepcodes), 'DESC'] = label

    return df


def get_lab_results(df, bepcodes):
    """ Obtain the results corresponding to the given bepcode """
    bepcodes = reduce(np.append, bepcodes)  # unpacks all lists in the list
    return df[df['BEPCODE'].isin(bepcodes)]


def remove_angle_bracketes(item):
    """ Removes angle brackets ('<' and '>')from the item """
    return re.sub(r'^[<>]', '', str(item))  # results like < 5 get replaced by 5, so that it is numeric


def to_numeric(item):
    """ Tries to convert item to a numeric value, else it will be replaced by a NaN value """

    try:
        item = float(item)
    except ValueError:
        if item == '-volgt-':
            item = -1
        else:
            item = np.nan

    return item


def set_negative_to_zero(item):
    """ Sets the word negatief to 0 """
    return 0 if item == 'negatief' else item


def is_categorical_range_data(item):
    """ Checks if data is categorical range data (data like '100-200') """
    return re.match(r'^\d+\s*-\s*\d+$', str(item)) 


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


def scale_data(df, lab_scalers_folder):

    for desc in df['DESC'].unique():

        # load right scaler 
        scaler = joblib.load(f'{lab_scalers_folder}/{desc.replace(" ", "_")}_scaler.pk1')

        # scale/transform the data
        bool_lab_res = (df['DESC'] == desc) & (df['UITSLAG'] != -1)  # we want to scale all the lab results except -1 (indicator for '-volgt-')
        if sum(bool_lab_res) != 0:
            df_lab_val = df[bool_lab_res]
            df.loc[bool_lab_res, 'UITSLAG'] = scaler.transform(df_lab_val[['UITSLAG']])

    return df


#################
# out functions #
#################

def to_tidy_format(df):
    """ Converts wide format to tidy format """
    df = df.pivot(index='PATIENTNR', columns='DESC', values='UITSLAG').reset_index()
    missing_cols = [lab for lab in bepcodes.keys() if lab not in df.columns]
    df[missing_cols] = np.nan
    return df


def preprocess_lab_data(input_data, config):
    # LOAD DATA
    df_lab = load_data(input_data)

    # GET RIGHT LEB RESULTS
    df_lab = get_lab_results(df_lab, bepcodes.values())
    df_lab = merge_bep_codes(df_lab, bepcodes['Ureum (POC)'], 'Ureum (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['Kreat (POC)'], 'Kreat (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['Natrium (POC)'], 'Natrium (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['kalium (POC)'], 'kalium (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['Glucose (POC)'], 'Glucose (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['Lactaat (POC)'], 'Lactaat (POC)')
    df_lab = merge_bep_codes(df_lab, bepcodes['Glucose'], 'Glucose')

    # HANDLE TIME DATA
    df_lab['AFNAME_TIJDSTIP']    = merge_datetime(df_lab['AFDATUM'], df_lab['AFTIJD'])
    df_lab['UITSLAG_TIJDSTIP']   = merge_datetime(df_lab['UITDATUM'], df_lab['UITTIJD'])
    df_lab = df_lab.drop(columns=['AFDATUM', 'AFTIJD', 'UITDATUM', 'UITTIJD'], axis=1)
    df_lab = get_latest_lab_results(df_lab)

    # CLEAN NUMERIC VALUES
    for desc in bepcodes.keys():
        data = df_lab[df_lab['DESC'] == desc]['UITSLAG']  # get lab result of that bepcode
        df_lab.loc[df_lab['DESC'] == desc, 'UITSLAG'] = clean_data(data)  # overwrite the non-cleaned data

    # SCALE DATA
    df_lab = scale_data(df_lab, config['lab_scalers_dir'])

    # CONVERT TO TIDY FORMAT
    df_lab = to_tidy_format(df_lab)
  
    return df_lab
    


    