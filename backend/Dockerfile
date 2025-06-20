# Use Python 3.9.6 as base image
FROM python:3.9.6-slim

# Set working directory
WORKDIR /app

# Install required system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install --with-deps

# Copy the rest of the application
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
