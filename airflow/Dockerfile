FROM apache/airflow:2.8.1-python3.11

USER root
COPY requirements.txt /tmp/requirements.txt
RUN chown airflow:root /tmp/requirements.txt

USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt
