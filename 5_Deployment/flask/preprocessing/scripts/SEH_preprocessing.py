# general imports
import re
import string
from datetime import timedelta

import numpy as np
import pandas as pd
import joblib

from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer  # supports Dutch langauge
from nltk.tokenize import word_tokenize
from workalendar.europe import NetherlandsWithSchoolHolidays

dutch_stop_words = set(stopwords.words('dutch'))


#####################
# loading function  #
#####################

def load_data(input_data):
    """" Loads the data """

    df = pd.DataFrame(input_data)
    df['AANKSDATUM'] = pd.to_datetime(df['AANKSDATUM'])

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


def create_date_features(df):
    """ Creates features from the date and time information """

    df['AANKSTIJD'] = pd.to_datetime(df['AANKSTIJD'],format= '%H:%M').dt.hour
    df['WEEKEND']   = df['AANKSDATUM'].apply(lambda date: 1 if date.weekday() > 4 else 0)

    return df


##############################
# feature encoding functions #
##############################

def convert_to_label(df, column, path_to_encoder_dir):
    """ Converts the colums to category codes """

    label_encoder = joblib.load(f'{path_to_encoder_dir}/{column}_label_encoder.pk1')
    df[column] = df[column].apply(lambda row: label_encoder.transform([row])[0] if row in label_encoder.classes_ else np.nan)

    return df


def create_triage_var(df, triage_col):
    """ Cleans and creates the triage code variable """

    df[triage_col] = df[triage_col].astype(str).str.strip('U')  # triage codes start with U
    df[triage_col] = pd.to_numeric(df[triage_col], errors='coerce')
    
     # Triage categories goes from 0 to 5, so set to NaN if not in this range
    invalid_codes = ~df[triage_col].isin(range(0, 6))
    df.loc[invalid_codes, triage_col] = np.nan
    
    return df


def one_hot_encode_col(df, column, path_to_encoder_dir):
    """ One hot encodes the given col, returns the whole dataframe """

    one_hot_encoder = joblib.load(f'{path_to_encoder_dir}/{column}_one_hot_encoder.pk1')
    encoded_data = one_hot_encoder.transform(df[[column]].astype(str))
    encoded_df = pd.DataFrame(encoded_data, columns=one_hot_encoder.get_feature_names([column]), index=df.index)
    df = pd.concat([df.drop(columns=[column], axis=1), encoded_df], axis=1)

    return df


def group_age(df, column):
    """ Converts age to the corresponding age group """

    age_bins = [*range(0, 100, 5), float('inf')]
    cats = range(0, len(age_bins)-1)

    df[column] =  pd.cut(df[column], bins=age_bins, labels=cats, right=False)#.astype(int)

    return df


def group_time(df, column):
    """ Groups time into time groups """

    time_cats = {i: (i // 6) for i in range(24)}
    df[column] = df[column].apply(lambda row: time_cats[row])

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
    #df = df[df[text_column] != '']  # drop empty fields

    return df.drop(columns=['text'], axis=1)


def preprocess_seh_data(input_data, config):
    df_seh = load_data(input_data)

    # HANDLE TIME DATA
    df_seh['AANKOMST'] = merge_datetime(df_seh['AANKSDATUM'], df_seh['AANKSTIJD'])

    # # CREATE DATE FEATURES
    df_seh = create_date_features(df_seh)

    # CREATE CATEGORY CODES
    encoder_dir = config['feature_encoders_dir']
    df_seh = convert_to_label(df_seh, 'GESLACHT', encoder_dir)
    df_seh = one_hot_encode_col(df_seh, 'VVCODE', encoder_dir)
    df_seh = one_hot_encode_col(df_seh, 'SPECIALISM', encoder_dir)

    df_seh = create_triage_var(df_seh, 'TRIANIVCOD')
 
    # CREATE GROUPES 
    df_seh = group_age(df_seh, 'LEEFTIJD')
    df_seh = group_time(df_seh, 'AANKSTIJD')

    # CLEAN TEXT DATA
    df_seh = preprocess_text(df_seh, 'KLACHT')
    return df_seh.drop(['AANKSDATUM', 'TRIAGETIJD', 'TRIADATUM'], axis=1).rename(columns={'LEEFTIJD': 'AGE'})