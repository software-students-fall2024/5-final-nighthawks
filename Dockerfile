# Use an official Python image as a base
FROM python:3.10-slim as base

# Set the working directory
WORKDIR /app

COPY Pipfile Pipfile.lock ./

# Install Python dependencies
RUN pip install pipenv && pipenv install --system --deploy

# Copy the application code
COPY . .

# Expose the application's port
EXPOSE 8000

# Start the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "backend.app:app"]