import os
import datetime
import re

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import Holiday

@app.route("/feriados/<ibge_code>/<date>", methods=["GET", "PUT", "DELETE"])
def holiday_methods(ibge_code=None, date=None):
    if (request.method == 'GET'):
        try:
            # Check if date is valid
            datetime.datetime.strptime(date, '%Y-%m-%d')
            # Check if the ibge_code is valid
            if(not bool(re.match('^\d{2}$|^\d{7}$', ibge_code))):
                raise ValueError("Invalid ibge_code")
            try:
                holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
                return jsonify(holiday.serialize()), 200
            except AttributeError as e:
                return str(e), 404
        except ValueError as e:
            return str(e), 400

    if (request.method == 'PUT'):
        pass
    if (request.method == 'DELETE'):
        pass

@app.route("/feriados/<ibge_code>/<holiday_name>", methods=["PUT", "DELETE"])
def date_flexible_holiday(ibge_code=None, date=None):
    if (request.method == 'PUT'):
        pass
    if (request.method == 'DELETE'):
        pass

if __name__ == "__main__":
    app.run(host='0.0.0.0')
