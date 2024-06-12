# general imports
import re
import string
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import joblib

from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer  # supports Dutch langauge
from nltk.tokenize import word_tokenize

dutch_stop_words = set(stopwords.words('dutch'))


#####################
# general functions #
#####################

def load_data(file_path):
    """" Loads the data """

    df = pd.read_csv(file_path, sep=';', na_values=[''])

    return df

def remove_na_entries(df, *columns):
    """ Removes rows of the df if the column contains an NA """

    for col in columns:
        df = df.dropna(subset=[col], axis=0)
        print(f'# OF ENTRIES AFTER {col}: {len(df)}')

    return df


#######################
# date time functions #
#######################


def merge_datetime(date_col, time_col):
    """ Merges date and time into one column"""

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


def create_datetime_table(df, *datetime_cols):
    """ Creates a df with the given datetime columns """

    df_time = df[list(datetime_cols)].copy()

    return df_time


def create_date_features(df):
    """ Creates features from the date and time information """

    df['AANKSTIJD'] = pd.to_datetime(df['AANKSTIJD'],format= '%H:%M').dt.hour
    df['WEEKEND']   = df['AANKSDATUM'].apply(lambda date: 1 if date.weekday() > 4 else 0)

    return df


##############################
# feature encoding functions #
##############################

def convert_cols_to_catcodes(df, *columns):
    """ Converts the colums to category codes """

    for col in columns:
        label_encoder = LabelEncoder()
        df[col] = label_encoder.fit_transform(df[col])
        joblib.dump(label_encoder, f'{col}_label_encoder.pk1')

    return df


def create_triage_var(df, triage_col):
    """ Cleans and creates the triage code variable """

    df[triage_col] = df[triage_col].str.strip('U')  # triage codes start with U
    df[triage_col] = pd.to_numeric(df[triage_col], errors='coerce')
    
     # Triage categories goes from 0 to 5, so set to NaN if not in this range
    invalid_codes = ~df[triage_col].isin(range(0, 6))
    df.loc[invalid_codes, triage_col] = np.nan
    
    return df


def one_hot_encode_col(df, col):
    """ One hot encodes the given col, returns the whole dataframe """

    one_hot_encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    encoded_data = one_hot_encoder.fit_transform(df[[col]].astype(str))
    encoded_df = pd.DataFrame(encoded_data, columns=one_hot_encoder.get_feature_names([col]), index=df.index)
    df = pd.concat([df.drop(columns=[col], axis=1), encoded_df], axis=1)

    joblib.dump(one_hot_encoder, f'{col}_one_hot_encoder.pk1')

    return df


def group_age(df, column):
    """ Converts age to the corresponding age group """

    age_bins = [*range(0, 100, 5), float('inf')]
    cats = range(0, len(age_bins)-1)

    df[column] =  pd.cut(df[column], bins=age_bins, labels=cats, right=False).astype(int)

    return df


def group_time(df, column):
    """ Groups time into time groups """

    time_cats = {i: (i // 6) for i in range(24)}
    df[column] = df[column].apply(lambda x: time_cats[x])

    return df

    
def handle_target_variable(df, target_col):
    """ Creates the target variable (1 if admitted, 0 if discharged) """

    invalid_codes = ['NHTA', # Naar huis tegen advies
                     'MOR',  # Mortuarium / overleden
                     'OVNH'] # Overleden naar huis

    admission_codes = ['OPN',   # Opname
                       'OVER'] # Overplaatsing ander ziekenhuis
    
    df = df.copy()  # settings with copy warning prevention
    df = df[~df[target_col].isin(invalid_codes)]

    df.loc[df[target_col].isin(admission_codes), target_col]  = 1
    df.loc[df[target_col]!=1, target_col] = 0

    df['OPNAME'] = df['BESTEMMING']  # rename column

    return df.drop('BESTEMMING', axis=1)


def remove_features_below_tresh(df, treshold):
    """ Removes features which occur less than the given treshold """

    col_sums = df.sum(axis=0, numeric_only=True)
    remove_cols = col_sums[col_sums < treshold].index.tolist()
    df = df.drop(remove_cols, axis=1) 

    return df


##########################
# text and NLP functions #
##########################

def clean_text(tokens: list, stop_words: set):
    """ 
        Cleans text:
        1. lowers the word
        2. removes punctuation
        3. removes stop words
    """
    puncs = string.punctuation.replace('#', '')
    words = [word.lower() if word != 'HET' else word for word in tokens]  # HET stands for Hoog-Energetisch Trauma and gets filtered out in the stopwords if set to lower
    words = [re.sub(f'[{puncs}]', '', word) for word in words if word not in {*stop_words, *puncs}]  # remove stop words and punctuation
    return words


def remove_stop_words(text):
    """ Removes dutch stop words from text """

    dutch_stop_words = set(stopwords.words('dutch'))
    text = text.apply(clean_text, stop_words = dutch_stop_words)

    return text


def stem_text(text):
    """ Stems dutch text """

    stemmer = SnowballStemmer('dutch')
    text = text.apply(lambda tokens: [stemmer.stem(token) for token in tokens])
    
    return text


def preprocess_text(df, text_column):
    """
        Preprocesses text:
        1. Tokenizes the sentence
        2. Removes stop words
        3. Removes digits
        4. Removes empty strings
    """

    df['text'] = df[text_column].apply(word_tokenize, language='dutch')
    df['text'] = remove_stop_words(df['text'])
    df['text'] = stem_text(df['text'])
    df['text'] = df['text'].apply(lambda text: [word for word in text if not re.match(r'\d', word)])
    df['text'] = df['text'].apply(lambda text: [word for word in text if not word == ''])
    df[text_column] = df['text'].apply(lambda x: ' '.join(x))  
    df = df[df[text_column] != '']  # drop empty fields

    return df.drop(columns=['text'], axis=1)


###################
# output function #
###################

def write_out_file(file_path, df):
    """ Writes output file"""
    with open(file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(df.to_csv(sep=';', index=False))


if __name__ == '__main__':

    df_seh = load_data(sys.argv[1])

    df_seh['AANKSDATUM'] = pd.to_datetime(df_seh['AANKSDATUM'])

    print(f'Number of starting entries: {len(df_seh)}')
    # HANDLE MISSING DATA
    df_seh = remove_na_entries(df_seh, 'BESTEMMING', 'AANKSDATUM', 'TRIADATUM', 
                                'TRIAGETIJD', 'AGE', 'KLACHT')
    # CREATE TARGET VARIABLE
    df_seh = handle_target_variable(df_seh, 'BESTEMMING')

    # HANDLE TIME DATA
    df_seh = df_seh[df_seh['AANKSDATUM'] < '20230101']
    df_seh['AANKOMST'] = merge_datetime(df_seh['AANKSDATUM'], df_seh['AANKSTIJD'])
    df_seh['TRIAGE']   = merge_datetime(df_seh['TRIADATUM'], df_seh['TRIAGETIJD'])
    df_seh['REGISTRATIE'], df_seh['EIND'] = time_to_datetime(df_seh['AANKOMST'], df_seh['REGTIJD'], df_seh['EINDTIJD'])
    df_time = create_datetime_table(df_seh, 'SEHID', 'AANKOMST', 'TRIAGE', 'EIND')

    # CREATE DATE FEATURES
    df_features = create_date_features(df_seh)
    df_features = df_features.drop(columns=['AANKSDATUM', 'REGTIJD','TRIADATUM', 'TRIAGETIJD', 'AANKOMST', 
                                    'REGISTRATIE', 'TRIAGE', 'EIND', 'EINDTIJD'])
    del df_seh  # all the date has been splitted to df_time and df_features, df_seh can be removed
    # CREATE CATEGORY CODES
    df_features = convert_cols_to_catcodes(df_features, 'GESLACHT')
    df_features = create_triage_var(df_features, 'TRIANIVCOD')
    df_features = one_hot_encode_col(df_features, 'VVCODE')
    df_features = one_hot_encode_col(df_features, 'SPECIALISM')
    df_features = remove_features_below_tresh(df_features, treshold=500)

    # CREATE GROUPES 
    df_features = group_age(df_features, 'AGE')
    df_features = group_time(df_features, 'AANKSTIJD')

    # CLEAN TEXT DATA
    df_features = preprocess_text(df_features, 'KLACHT')
    df_time = df_time[df_time.SEHID.isin(df_features.SEHID)]  # some entries were removed during text processing

    # WRITE OUTPUT FILES
    out_path = sys.argv[1].rsplit('/', maxsplit=1)[0] + f'/processed/{date.today()}'
    write_out_file(f'{out_path}_SEH_processed.csv', df_features.drop('POSTCODE', axis=1))
    write_out_file(f'{out_path}_time_processed.csv', df_time) 