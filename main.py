import requests
from celery import Celery
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import datetime


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        include=['main']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://redis:6379',
    CELERY_RESULT_BACKEND='redis://redis:6379',
    SQLALCHEMY_DATABASE_URI="sqlite:///bd.sqlite",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)
celery = make_celery(app)
db = SQLAlchemy(app)

class Data(db.Model):
    __tablename__ = 'data'
    id = db.Column(db.Integer(), primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Value = db.Column(db.String(100), nullable=False)
    CharCode = db.Column(db.String(100), nullable=False)
    Date = db.Column(db.String(100), nullable=False)

db.create_all()

@celery.task
def tasks(data_begin, data_end):
    begin = datetime.datetime.strptime(data_begin, "%Y-%m-%d")
    end = datetime.datetime.strptime(data_end, "%Y-%m-%d")
    day_delta = datetime.timedelta(days=1)
    for i in range((end - begin).days+1):
        date = (begin + i * day_delta).strftime("%d.%m.%Y")
        url = "http://www.cbr.ru/scripts/XML_daily.asp?date_req="
        response = requests.post(url=url + date)
        tree = ET.ElementTree(ET.fromstring(response.content))
        for child in tree.getroot():
            Name = child.find("Name").text
            Value = child.find("Value").text
            CharCode = child.find("CharCode").text
            db.session.add(Data(Name=Name, Value=Value, CharCode=CharCode, Date=date))
            db.session.commit()

@app.route('/')
def hello_world():
    return render_template("index.html", get=True)


@app.route('/get/')
def get():
    data_begin = request.args.get('data_begin')
    data_end = request.args.get('data_end')
    tasks.delay(data_begin, data_end)
    return render_template("index.html", get=True, response=True)

@app.route('/look/')
def look():
    date = datetime.datetime.strptime(request.args.get('date'), "%Y-%m-%d")
    query = Data.query.filter_by(Date=date.strftime("%d.%m.%Y"))
    return render_template("index.html", look=True, response=False, query=query)