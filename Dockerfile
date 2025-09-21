FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY GOOGLE_APPLICATION_CREDENTIALS.json /app/service_account.json
ENV FIREBASE_CREDENTIALS_PATH="/app/service_account.json"
EXPOSE 8080
CMD exec uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8080}