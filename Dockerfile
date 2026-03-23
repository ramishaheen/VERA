FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY vera/ ./vera/
COPY static/ ./static/
COPY run.py .

# Environment defaults (override with -e or --env-file)
ENV VERA_HOST=0.0.0.0
ENV VERA_PORT=8000
ENV VERA_MODEL=gpt-4o-mini

EXPOSE 8000

CMD ["python", "run.py", "--no-browser"]
