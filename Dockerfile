# Use an official Python image as a base
FROM python:3.10-slim as base

# Set the working directory
WORKDIR /app

# Install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir pipenv \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

# Install Python dependencies
RUN pipenv install --system --deploy

# Copy the application code
COPY . .

# Expose the application's port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]