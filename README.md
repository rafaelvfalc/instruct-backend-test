# Instruct Backend Test

Solution for the Instruct Backend Test

## Requirements
- Python 3.6+  
- PostgreSQL 12.3+
... and that's it! :rocket:

## Local Usage Instructions

### 1. Go to the main directory of the repository
```bash
$ cd path/to/instruct-backend-test
```

### 2. Create a virtual environment
```bash
$ virtualenv venv
```

### 3. Connect to the created virtual environment
```bash
$ source venv/bin/activate
```

### 4. Install all necessary packages
```bash
$ pip install -r requirements.txt
```

### 5. Create all required environment variables
```bash
$ cd src
$ source .env
```

### 6. Setup database
```bash
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py db upgrade
```

### 7. Execute API
```bash
$ python manage.py runserver
```

### 8. Run Basic Tests (Optional)
Go to another terminal and run de following commands
```bash
$ cd path/to/instruct-backend-test/src/tests
$ k6 run -e API_BASE='API_URL' tests-open.js
```
Remember to change the 'API_URL' for the actual URL of the running API

## Help
TBD

## Author of the Solution
Rafael Falcão [@rafaelvfalc](https://github.com/rafaelvfalc)

## Helpful Links
* [Create a web application with python + Flask + PostgreSQL and deploy on Heroku](https://medium.com/@dushan14/create-a-web-application-with-python-flask-postgresql-and-deploy-on-heroku-243d548335cc)

* [Easter documentation](https://dateutil.readthedocs.io/en/stable/easter.html)
