import re
import sys
from datetime import date
import pandas as pd

import string
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer  # supports Dutch langauge
from nltk.tokenize import word_tokenize

dutch_stop_words = set(stopwords.words('dutch'))


def load_data(file_path):
    """ Loads the data """

    df = pd.read_csv(file_path, sep=';', na_values=[''])
    df['AANKSDATUM'] = pd.to_datetime(df['AANKSDATUM'])

    return df


def merge_datetime(date_col, time_col):
    """ Merges date and time columns into one column """

    date_col = pd.to_datetime(date_col).astype(str)

    return pd.to_datetime(date_col + ' ' + time_col, format='%Y-%m-%d %H:%M:%S')


def clean_text(tokens: list, stop_words: set):
    """ 
        Cleans text:
        1. lowers the word
        2. removes punctuation
        3. removes stop words
    """

    words = [word.lower() if word != 'HET' else word for word in tokens]  # HET stands for Hoog-Energetisch Trauma and gets filtered out in the stopwords if set to lower
    words = [re.sub(f'[{string.punctuation}]', '', word) for word in words if word not in {*stop_words, *string.punctuation}]  # remove stop words and punctuation
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
    df[text_column] = df['text']   

    return df.drop(columns=['text'], axis=1)


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


def write_out_file(file_path, df):
    """ Writes output file """
    print(file_path)
    with open(file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(df.to_csv(sep=';', index=False))


if __name__ == '__main__':
    # LOAD DATA
    df_rad = load_data(sys.argv[1])
    df_rad = df_rad[['SEHID', 'PATIENTNR', 'AANKSDATUM', 'AANKSTIJD', 'ACCDATUM', 'ACCTIJD', 'TRANSTEXT', 'BESTEMMING']]

    # DROP NAs
    df_rad = df_rad[df_rad['BESTEMMING'].notna()]
    df_rad = df_rad[df_rad['TRANSTEXT'].notna()]
    df_rad = df_rad[df_rad['ACCDATUM'].notna()]

    # HANDLE DATETIMES
    df_rad['AANKOMST']   = merge_datetime(df_rad['AANKSDATUM'], df_rad['AANKSTIJD'])
    df_rad['ACCORD']   = merge_datetime(df_rad['ACCDATUM'],  df_rad['ACCTIJD'])
    df_rad = df_rad.drop(columns=['AANKSDATUM', 'AANKSTIJD', 'ACCDATUM', 'ACCTIJD'], axis=1)

    # CLEAN TEXT
    df_rad = preprocess_text(df_rad, 'TRANSTEXT')
    df_rad['RAD_REPORT'] = df_rad['TRANSTEXT'].apply(lambda x: ' '.join(x))
    df_rad = df_rad.drop(columns=['TRANSTEXT'], axis=1)

    # CREATE TARGET VARIABLE
    df_rad = handle_target_variable(df_rad, 'BESTEMMING')
    
    # CREATE OUTPUT FILE
    out_path = sys.argv[1].rsplit('/', maxsplit=1)[0] + f'/processed/{date.today()}'
    write_out_file(f'{out_path}_RAD_processed.csv', df_rad)




