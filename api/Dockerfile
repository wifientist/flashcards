FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; psycopg2-binary ships wheels so no build toolchain.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
