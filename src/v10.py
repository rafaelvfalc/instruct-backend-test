import os
import datetime
import re
import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Holiday

@app.route("/feriados/<ibge_code>/<date>/", methods=["GET", "PUT", "DELETE"])
def holiday_methods(ibge_code=None, date=None):
    if (request.method == 'GET'):
        return get_holiday(ibge_code, date)
    if (request.method == 'PUT'):
        name = json.loads(request.data).get("name")
        return add_update_holiday(name, ibge_code, date)
    if (request.method == 'DELETE'):
        return delete_holiday(ibge_code, date)

@app.route("/feriados/<ibge_code>/<holiday_name>/", methods=["PUT", "DELETE"])
def date_flexible_holiday(ibge_code=None, date=None):
    if (request.method == 'PUT'):
        pass
    if (request.method == 'DELETE'):
        pass

def get_holiday(ibge_code, date):
    try:
        # Check if date is valid
        datetime.datetime.strptime(date, '%Y-%m-%d')
        # Check if the ibge_code is valid
        if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid IBGE code")
        try:
            # Query first dates in format %m-%d them %y-%m-%d
            date_without_year = "{}-{}".format(date.split("-")[1], date.split("-")[2])
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
            holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
            if(holiday is None):
                try:
                    holiday = Holiday(name, date, ibge_code)
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
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400

def delete_holiday(ibge_code, date):
    try:
        # Check if date is valid
        datetime.datetime.strptime(date, '%m-%d')
        # Check if the ibge_code is valid
        if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
            raise ValueError("Invalid ibge_code")
        try:
            holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
            if(holiday is None):
                raise AttributeError("This holiday does not exist in this database")
            else:
                db.session.delete(holiday)
                db.session.commit()
                return "Holiday ID {} successfully deleted.".format(holiday.id), 204
        except AttributeError as e:
            return str(e), 404
    except ValueError as e:
        return str(e), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0')
