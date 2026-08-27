# Official Playwright Python image containing all browser binaries & dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (Render automatically assigns PORT env variable)
ENV PORT=8000
EXPOSE 8000

# Start Uvicorn server
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
