import os

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from holiday import Holiday

@app.route("/feriados/<ibge_code>/<date>", methods=["GET", "PUT", "DELETE"])
def holiday_methods(ibge_code=None, date=None):
    if (request.method == 'GET'):
        year, month, day = date.split('-')
        print(ibge_code)
        print(day, month, year)
        return jsonify({"name": "holiday"}), 200
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
