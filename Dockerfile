# python:3.12-slim (pinned by digest; refresh it when the tag moves)
FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home tester && chown -R tester /app
USER tester

# Offline by default; run the live tests explicitly: docker run --rm eds-api-tests pytest -v -m live
CMD ["pytest", "-v", "-m", "not live"]
