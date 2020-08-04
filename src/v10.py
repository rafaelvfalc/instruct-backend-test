import os

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
            holiday = Holiday.query.filter_by(ibge_code=ibge_code).filter_by(date=date).first()
            return jsonify(holiday.serialize()), 200
        except Exception as e:
            return str(e), 404
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
