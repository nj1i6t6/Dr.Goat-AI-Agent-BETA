FROM python:3.11-slim

WORKDIR /app

COPY iot_simulator.py .

RUN pip install --no-cache-dir flask requests

ENV API_KEY=""
ENV INGEST_URL="http://backend:5001/api/iot/ingest" 
ENV DEVICE_TYPE="environment_sensor"
ENV CONTROL_HOST="0.0.0.0"
ENV CONTROL_PORT=8080
ENV CONTROL_ROUTE="/cmd"
ENV SEND_INTERVAL_SECONDS=20

EXPOSE 8080

CMD ["python", "iot_simulator.py"]