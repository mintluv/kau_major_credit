FROM python:3.11-slim

WORKDIR /app

# Set non-interactive debconf
ENV DEBIAN_FRONTEND=noninteractive

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and all Linux OS dependencies
RUN playwright install --with-deps chromium

# Copy application files
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD uvicorn app:app --host 0.0.0.0 --port $PORT
