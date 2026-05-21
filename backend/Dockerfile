FROM python:3.10-slim

# Install system utilities including Nmap
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8000
