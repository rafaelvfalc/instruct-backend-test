import os
import re
import json
import string
import pandas as pd
from datetime import datetime, timedelta
from dateutil import easter

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
FLEXIBLE_DATE_HOLIDAYS = ["Carnaval", "Pascoa", "Corpus Christi"]


@app.before_first_request
def add_national_holidays():
    """
    Add all national holidays in the database

    Args:
        None

    Return: 
        None
    """
    for index, row in national_holidays_df.iterrows():
        add_update_specific_holiday(row['name'], NATIONAL_HOLIDAY_CODE,
                                    row['date'], "national")


@app.route(
    "/feriados/<ibge_code>/<holiday_info>/", methods=["GET", "PUT", "DELETE"])
def holiday_methods(ibge_code=None, holiday_info=None):
    """
    Setup of all holiday routes and methods of the api

    Args:
        ibge_code (string): IBGE code
        holiday_info (string): Data that might have a holiday date or
                               holiday name

    Return: 
        (Message, code): Return the message result of the deletion and the http code
    """
    if (request.method == 'GET'):
        date = holiday_info
        return get_holiday(ibge_code, date)
    elif (request.method == 'PUT'):
        holiday_name = string.capwords(holiday_info.replace('-', ' '))
        if (is_flexible_holiday(holiday_name)):
            return add_date_flexible_holiday(holiday_name, ibge_code)
        else:
            name = json.loads(request.data).get("name")
            date = holiday_info
            return add_update_holiday(name, ibge_code, date)
    elif (request.method == 'DELETE'):
        holiday_name = string.capwords(holiday_info.replace('-', ' '))
        if (is_flexible_holiday(holiday_name)):
            return delete_date_flexible_holiday(holiday_name, ibge_code)
        else:
            date = holiday_info
            return delete_holiday(ibge_code, date)


def get_holiday(ibge_code, date):
    """
    Gets a holiday

    Args:
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday

    Return: 
        (Message, code): Return the message result of the get method and the http code
    """
    try:
        # Check if date is valid
        datetime.strptime(date, '%Y-%m-%d')
        # Check if the ibge_code is valid
        if (not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid IBGE code")
        try:
            # Check if it is a national holiday
            holiday = get_national_holiday(date)
            if (holiday is not None):
                return jsonify(holiday.serialize()), 200
            else:
                # Check if any flexible date holidays matches with the date
                holiday = get_flexible_date_holiday(ibge_code, date)
                if (holiday is not None):
                    return jsonify(holiday.serialize()), 200
                else:
                    # Query first dates in format %m-%d them %y-%m-%d
                    date_without_year = "{}-{}".format(
                        date.split("-")[1],
                        date.split("-")[2])
                    holiday = Holiday.query.filter_by(
                        ibge_code=ibge_code).filter_by(
                            date=date_without_year).first()
                    if (holiday is not None):
                        return jsonify(holiday.serialize()), 200
                    else:
                        holiday = Holiday.query.filter_by(
                            ibge_code=ibge_code).filter_by(date=date).first()
                        return jsonify(holiday.serialize()), 200
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400


def add_update_holiday(name, ibge_code, date):
    """
    Add or update a holiday

    Args:
        name (string): Name of the holiday
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday

    Return: 
        (Message, code): Return the message result of the addition/update and the http code
    """
    try:
        # Check if date is valid
        datetime.strptime(date, '%m-%d')
        # Check if the ibge_code is valid
        if (not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid IBGE code")
        try:
            # If its a state holiday
            if (len(ibge_code) == 2):
                return add_update_state_holiday(name, ibge_code, date, "state")
            # If its a town holiday
            elif (len(ibge_code) == 7):
                return add_update_specific_holiday(name, ibge_code, date,
                                                   "town")
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400


def add_update_state_holiday(name, ibge_code, date, type_):
    """
    Add or update a state holiday

    Args:
        name (string): Name of the holiday
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday
        type_ (string): Type of the holiday

    Return: 
        (Message, code): Return the message result of the addition or update and the http code
    """
    return_code = add_update_specific_holiday(name, ibge_code, date, type_)
    # If the state holiday was created or updated, add the reference to its towns
    if (return_code[1] == 200 or return_code[1] == 201):
        state_towns_codes = cities_df[cities_df['codigo_ibge'].astype(
            str).str.match(ibge_code)]['codigo_ibge'].tolist()
        for town_code in state_towns_codes:
            add_update_specific_holiday(name, town_code, date, type_)
        return return_code
    else:
        return return_code


def add_update_specific_holiday(name, ibge_code, date, type_):
    """
    Add or update a specific holiday

    Args:
        name (string): Name of the holiday
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday
        type_ (string): Type of the holiday

    Return: 
        (Message, code): Return the message result of the addition or update and the http code
    """
    holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(
        date=date).first()
    if (holiday is None or type_ == 'flexible-date'):
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
    """
    Delete a specific holiday

    Args:
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday

    Return: 
        (Message, code): Return the message result of the deletion and the http code
    """
    try:
        # Check if date is valid
        datetime.strptime(date, '%m-%d')
        # Check if the ibge_code is valid
        if (not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid ibge_code")
        try:
            # Trying to delete a holiday in a state
            if (len(ibge_code) == 2):
                return delete_state_holiday(ibge_code, date, "state")
            # Trying to delete a holiday in a town
            elif (len(ibge_code) == 7):
                return delete_specific_holiday(ibge_code, date, "town")
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400


def delete_state_holiday(ibge_code, date, type_):
    """
    Delete a state holiday

    Args:
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday
        type_ (string): Type of the holiday

    Return: 
        (Message, code): Return the message result of the deletion and the http code
    """
    return_code = delete_specific_holiday(ibge_code, date, type_)
    # If the state holiday was deleted, delete the reference to its towns
    if (return_code[1] == 204):
        state_towns_codes = cities_df[cities_df['codigo_ibge'].astype(
            str).str.match(ibge_code)]['codigo_ibge'].tolist()
        for town_code in state_towns_codes:
            delete_specific_holiday(town_code, date, type_)
        return return_code
    else:
        return return_code


def delete_specific_holiday(ibge_code, date, type_, flexible_holiday_name=""):
    """
    Delete a specific holiday

    Args:
        ibge_code (string): IBGE code
        date (string): Data that might have a holiday
        type_ (string): Type of the holiday
        flexible_holiday_name (string): If the holiday that will be deleted
                                        is a flexible date one, this variable 
                                        get its name.

    Return: 
        (Message, code): Return the message result of the deletion and the http code
    """
    # Check if it is a flexible date holiday
    try:
        holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(
            name=flexible_holiday_name).filter_by(type_=type_).first()
        if (holiday is not None):
            db.session.delete(holiday)
            db.session.commit()
            return "Holiday ID {} successfully deleted.".format(
                holiday.id), 204

        # Check if it is a national holiday
        holiday = Holiday.query.filter_by(
            ibge_code=NATIONAL_HOLIDAY_CODE).filter_by(date=date).first()
        if (holiday is not None):
            return "Unable to remove national holidays", 403

        # Check if it is a state or town holiday
        holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(
            date=date).first()
        if (holiday is None):
            raise AttributeError(
                "This holiday does not exist in this database")
        elif (holiday.type_ != type_):
            return "Incompatible types of holidays", 403
        else:
            db.session.delete(holiday)
            db.session.commit()
            return "Holiday ID {} successfully deleted.".format(
                holiday.id), 204
    except AttributeError as e:
        return str(e), 404


def get_national_holiday(date):
    """
    Gets a national holiday

    Args:
        date (string): Data that might have a holiday

    Return: 
        Holiday: Return the holiday object of the date if exists
                 None otherwise.
    """
    # Check Holy Friday special case
    year = date.split("-")[0]
    holy_friday_date = str(
        easter.easter(int(year), method=3) - timedelta(days=2))
    if (date == holy_friday_date):
        holiday = Holiday.query.filter_by(name='Sexta-Feira Santa').first()
    else:
        date_without_year = "{}-{}".format(
            date.split("-")[1],
            date.split("-")[2])
        holiday = Holiday.query.filter_by(
            ibge_code=NATIONAL_HOLIDAY_CODE).filter_by(
                date=date_without_year).first()
    return holiday


def add_date_flexible_holiday(holiday_name, ibge_code):
    """
    Add a data flexible holiday

    Args:
        holiday_name (string): The name of the holiday that will be deleted
        ibge_code (string): IBGE code of the town

    Return: 
        (Message, code): Return the message result of the addition and the http code
    """
    # Check if the ibge_code is valid town code
    try:
        if (not bool(re.match('^\d{7}$', ibge_code))):
            raise ValueError("Invalid ibge_code")
        return add_update_specific_holiday(
            str(holiday_name), ibge_code, "", "flexible-date")
    except ValueError as e:
        return str(e), 400


def delete_date_flexible_holiday(holiday_name, ibge_code):
    """
    Delete a data flexible holiday

    Args:
        holiday_name (string): The name of the holiday that will be deleted
        ibge_code (string): IBGE code of the town

    Return: 
        (Message, code): Return the message result of the deletion and the http code
    """
    # Check if the ibge_code is valid town code
    try:
        if (not bool(re.match('^\d{7}$', ibge_code))):
            raise ValueError("Invalid ibge_code")
        return delete_specific_holiday(ibge_code, "", "flexible-date",
                                       holiday_name)
    except ValueError as e:
        return str(e), 400


def get_flexible_date_holiday(ibge_code, date):
    """
    Gets a data flexible holiday

    Args:
        ibge (string): IBGE code of the town
        date (string): Data that might have a holiday

    Return: 
        Holiday: Return the holiday object of the date if exists
                 None otherwise.
    """
    year = date.split("-")[0]
    holidays = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(
        type_="flexible-date").all()
    for holiday in holidays:
        if (get_flexible_holiday_date(holiday.name, int(year)) == date):
            return holiday
    return None


def get_flexible_holiday_date(name, year):
    """
    Function that return the date of a specific
    flexible date holiday

    Args:
        name (string): Name of the holiday
        year (string): Year that it is requested the holiday date

    Return: 
        string: Date of the specific holiday in format %y-%m-%d
    """
    if (name == 'Pascoa'):
        return str(easter.easter(year, method=3))
    elif (name == 'Carnaval'):
        return str(easter.easter(year, method=3) - timedelta(days=47))
    elif (name == 'Corpus Christi'):
        return str(easter.easter(year, method=3) + timedelta(days=60))


def is_flexible_holiday(content):
    """
    Function that checks if a specific content matches
    with a Flexible Date Holiday

    Args:
        content (string): Possible flexible date holiday name

    Return: 
        bool: True if matches, False otherwise.
    """
    return content in FLEXIBLE_DATE_HOLIDAYS


if __name__ == "__main__":
    app.run(host='0.0.0.0')