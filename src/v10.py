import os
import datetime
import dateutil
import re
import json
import pandas as pd

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Holiday

cities_df = pd.read_csv("./data/municipios-2019.csv")
national_holidays_df = pd.read_csv("./data/national-holidays.csv")

NATIONAL_HOLIDAY_CODE = '-1'
FLEXIBLE_DATE_HOLIDAYS = ["carnaval","sexta-feira-santa", "pascoa", "corpus-christi"]

@app.before_first_request
def add_national_holidays():
    for index, row in national_holidays_df.iterrows():
        add_update_specific_holiday(row['name'], NATIONAL_HOLIDAY_CODE, row['date'], "national")

@app.route("/feriados/<ibge_code>/<holiday_info>/", methods=["GET", "PUT", "DELETE"])
def holiday_methods(ibge_code=None, holiday_info=None):
    if (request.method == 'GET'):
        date = holiday_info
        return get_holiday(ibge_code, date)
    elif (request.method == 'PUT'):
        if(is_flexible_holiday(holiday_info)):
            holiday_name = holiday_info
            return add_date_flexible_holiday(ibge_code, holiday_name)
        else:
            name = json.loads(request.data).get("name")
            date = holiday_info
            return add_update_holiday(name, ibge_code, date)
    elif (request.method == 'DELETE'):
        if(is_flexible_holiday(holiday_info)):
            holiday_name = holiday_info
            return delete_date_flexible_holiday(ibge_code, holiday_name)
        else:
            date = holiday_info
            return delete_holiday(ibge_code, date)

def is_flexible_holiday(content):
    return content in FLEXIBLE_DATE_HOLIDAYS
    
def get_holiday(ibge_code, date):
    try:
        # Check if date is valid
        datetime.datetime.strptime(date, '%Y-%m-%d')
        # Check if the ibge_code is valid
        if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid IBGE code")
        try:
            date_without_year = "{}-{}".format(date.split("-")[1], date.split("-")[2])
            # Check if it is a national holiday
            holiday = Holiday.query.filter_by(ibge_code=NATIONAL_HOLIDAY_CODE).filter_by(date=date_without_year).first()
            if(holiday is not None):
                return jsonify(holiday.serialize()), 200
            else:
                # Query first dates in format %m-%d them %y-%m-%d
                holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date_without_year).first()
                if(holiday is not None):
                    return jsonify(holiday.serialize()), 200
                else:
                    holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
                    return jsonify(holiday.serialize()), 200
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400

def add_update_holiday(name, ibge_code, date):
    try:
        # Check if date is valid
        datetime.datetime.strptime(date, '%m-%d')
        # Check if the ibge_code is valid
        if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid IBGE code")
        try:
            # If its a state holiday
            if(len(ibge_code) == 2):
                return add_update_state_holiday(name, ibge_code, date, "state")
            # If its a town holiday
            elif(len(ibge_code) == 7):
                return add_update_specific_holiday(name, ibge_code, date, "town")
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400

def add_update_state_holiday(name, ibge_code, date, type_):
    return_code = add_update_specific_holiday(name, ibge_code, date, type_)
    # If the state holiday was created or updated, add the reference to its towns
    if(return_code[1] == 200 or return_code[1] == 201):
        state_towns_codes = cities_df[cities_df['codigo_ibge'].astype(str).str.match(ibge_code)]['codigo_ibge'].tolist()
        for town_code in state_towns_codes:
            add_update_specific_holiday(name, town_code, date, type_)
        return return_code
    else:
        return return_code

def add_update_specific_holiday(name, ibge_code, date, type_):
    holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
    if(holiday is None):
        try:
            holiday = Holiday(name, date, ibge_code, type_)
            db.session.add(holiday)
            db.session.commit()
            return "Holiday ID {} added.".format(holiday.id), 201
        except Exception as e:
	        return str(e), 400
    else:
        try:
            holiday.name = name
            db.session.commit()
            return "Holiday ID {} updated.".format(holiday.id), 200
        except Exception as e:
	        return str(e), 400

def delete_holiday(ibge_code, date):
    try:
        # Check if date is valid
        datetime.datetime.strptime(date, '%m-%d')
        # Check if the ibge_code is valid
        if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid ibge_code")
        try:
            # Trying to delete a holiday in a state
            if(len(ibge_code) == 2):
                return delete_state_holiday(ibge_code, date, "state")
            # Trying to delete a holiday in a town
            elif(len(ibge_code) == 7):
                return delete_specific_holiday(ibge_code, date, "town")
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400

def delete_state_holiday(ibge_code, date, type_):
    return_code = delete_specific_holiday(ibge_code, date, type_)
    # If the state holiday was deleted, delete the reference to its towns
    if(return_code[1] == 204):
        state_towns_codes = cities_df[cities_df['codigo_ibge'].astype(str).str.match(ibge_code)]['codigo_ibge'].tolist()
        for town_code in state_towns_codes:
            delete_specific_holiday(town_code, date, type_)
        return return_code
    else:
        return return_code

def delete_specific_holiday(ibge_code, date, type_):
    # Check if it is a national holiday
    holiday = Holiday.query.filter_by(ibge_code=NATIONAL_HOLIDAY_CODE).filter_by(date=date).first()
    if(holiday is not None):
       return "Unable to remove national holidays", 403 

    # Check if it is a state or town holiday
    holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
    if(holiday is None):
        raise AttributeError("This holiday does not exist in this database")
    elif(holiday.type_ != type_):
        return "Incompatible types of holidays", 403
    else:
        db.session.delete(holiday)
        db.session.commit()
        return "Holiday ID {} successfully deleted.".format(holiday.id), 204

def add_date_flexible_holiday(ibge_code, holiday_name):
    print("ADDING FLEXIBLE")
    return "", 200

def delete_date_flexible_holiday(ibge_code, holiday_name):
    print("DELETING FLEXIBLE")
    return "", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0')
