FROM python:3.9.0-alpine
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=main.py
RUN apk add bash
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt