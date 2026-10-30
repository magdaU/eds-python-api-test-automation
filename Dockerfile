FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home tester && chown -R tester /app
USER tester

# Offline by default; run the live tests explicitly: docker run --rm eds-api-tests pytest -v -m live
CMD ["pytest", "-v", "-m", "not live"]
