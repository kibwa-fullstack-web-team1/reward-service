FROM python:3.12-slim-bookworm

WORKDIR /app

COPY reward-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reward-service/app ./app
COPY reward-service/reward-service_manage.py .

CMD ["python", "reward-service_manage.py"]