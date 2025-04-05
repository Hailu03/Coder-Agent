FROM python:3.9-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install uvicorn with standard extras for hot-reload functionality
RUN pip install uvicorn[standard]

# For development, we won't copy the application code
# since it will be mounted as a volume
# COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Default command - this will be overridden by docker-compose in development
CMD ["python", "run.py"]