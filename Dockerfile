FROM python:3.10-slim-buster

RUN apt-get update && \
    apt clean && \
    rm -rf /var/cache/apt/*

RUN python3 -m pip install --upgrade pip

COPY ./requirements.txt /tmp/requirements.txt

RUN python3 -m pip install -r /tmp/requirements.txt

WORKDIR /app
COPY ./api /app/api/

EXPOSE 9010
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "9010"]