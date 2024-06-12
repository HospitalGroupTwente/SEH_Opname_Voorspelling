from flask import Flask, request, jsonify
import yaml
import pandas as pd
import joblib
from datetime import datetime
from preprocessing.scripts import SEH_preprocessing, LAB_preprocessing, VITALS_preprocessing


def get_arrival_datetimes(data):
    df = pd.DataFrame(data)
    df = df[['SEHID', 'AANKSDATUM', 'AANKSTIJD']]


def preprocess_all_data(data):

    seh_data    = data.get('seh_data')
    processed_seh = SEH_preprocessing.preprocess_seh_data(seh_data, config)

    lab_data    = data.get('lab_data')  
    processed_lab = LAB_preprocessing.preprocess_lab_data(lab_data, config)


    vital_data  = data.get('vital_data') 
    processed_vitals = VITALS_preprocessing.preprocess_vital_data(vital_data, config)

    df_all = pd.merge(processed_seh, processed_lab, on='PATIENTNR', how='left')
    df_all = pd.merge(df_all, processed_vitals, on='PATIENTNR', how='left')
    df_all['naam'] = ''
    
    return df_all


def add_text_preds(df):

    text_transformed = vec.transform(df['KLACHT'])
    df['KLACHT_PRED'] = nlp_model.predict_proba(text_transformed)[:, 1]

    return df.drop(['KLACHT'], axis=1)


def select_model_based_on_time(arrival_datetime, current_datetime):
    time_diff = current_datetime - arrival_datetime
    time_diff_min = time_diff.total_seconds() / 60

    # gets the right model time
    # for example: 8 min becomes 0 min, 22 min becomes 20 min, etc...
    time_diff_10min = int(time_diff_min / 10) * 10  
    if time_diff_10min > 180:
        time_diff_10min = 180
    model = models[time_diff_10min]
    return model, time_diff_10min


def predict_admission(seh_entry):
    sehid = seh_entry['SEHID']
    try:
        model, timedelta = select_model_based_on_time(seh_entry['AANKOMST'], datetime.now())
        seh_entry = seh_entry.drop(['SEHID', 'PATIENTNR', 'VOORNAAM', 'ACHTERNAAM', 'AANKOMST'])
        seh_entry = seh_entry.to_frame().T
        seh_entry = seh_entry.apply(pd.to_numeric)

        pred = model.predict_proba(seh_entry)[:,1][0]
        return [sehid, float(pred), int(timedelta)]
    except Exception as e:
        print(f"Failed to obtaine prediction for {sehid}: {e}")
        return [sehid, '', '']


def drop_feature_columns(df):
    return df.drop(['VVCODE_AMBG', 'VVCODE_AMBH', 'VVCODE_AND', 'VVCODE_HELI', 'SPECIALISM_ALL', 'SPECIALISM_ANE', 'SPECIALISM_DER', 'SPECIALISM_GGZ', 'SPECIALISM_ICA', 'SPECIALISM_KAA', 'SPECIALISM_ONC', 'SPECIALISM_OOG', 'SPECIALISM_PSY', 'SPECIALISM_PYN', 'SPECIALISM_RAD', 'SPECIALISM_REU', 'SPECIALISM_SEH', 'SPECIALISM_TRAU', 'SPECIALISM_ZA', 'SPECIALISM_nan', 'naam'], axis=1)


def sort_columns(df):
    sorter = [
        'SEHID', 'PATIENTNR', 'VOORNAAM', 'ACHTERNAAM', 'AANKOMST','AANKSTIJD', 'GESLACHT',
        'AGE','PreviousVisits','PrevAdmissionPercentage', 'WEEKEND','VVCODE_AMB','VVCODE_EV','VVCODE_nan','SPECIALISM_CAR','SPECIALISM_CHI',
        'SPECIALISM_GER','SPECIALISM_GYN','SPECIALISM_INT','SPECIALISM_KIN','SPECIALISM_KNO','SPECIALISM_LON','SPECIALISM_MDL',
        'SPECIALISM_NEU','SPECIALISM_ORT','SPECIALISM_PLA','SPECIALISM_URO','TRIANIVCOD',
        'Glucose','Trombocyten','Hematocriet','Kalium','CRP','Leucocyten','Kreatinine','Hemoglobine','Natrium','Bilirubine Totaal',
        'Alkalische Fosfatase (AF)','ASAT','ALAT','LD','GGT','Ureum','Glucose (POC)','Leukocyten','Lactaat','NT-proBNP','hsTroponine T',
        'kalium (POC)','Natrium (POC)','Lactaat (POC)','Ureum (POC)','Kreat (POC)','Temp','Resp','NIBP','MEWS score','HR','KLACHT_PRED']
    return df[sorter]

app = Flask(__name__)

@app.route('/get_predictions', methods=['POST'])
def get_predictions():

    data = request.json
    processed_data = preprocess_all_data(data)
    processed_data = add_text_preds(processed_data)
    processed_data = drop_feature_columns(processed_data)
    processed_data = sort_columns(processed_data)
    preds = processed_data.apply(lambda row: predict_admission(row), axis=1)
    preds = [{'SEHID': id, 'PREDICTION': pred, 'TIMEDELTA': time}for id, pred, time in preds]
    return jsonify({'result': preds})

if __name__ == '__main__':
    # load config 
    config_path = './config.yaml' 
    with open(config_path) as stream:
        config = yaml.safe_load(stream)
    
    # load models in memory
    vec = joblib.load(config['nlp_vec'])
    nlp_model = joblib.load(config['nlp_pred_model'])
    models = {time: joblib.load(f'{config["model_dir"]}/{time}_min_xgboost.joblib') for time in range(0, 190, 10)}
    
    # start flask app
    app.run(host='0.0.0.0', port=5555)  # Run the Flask application

