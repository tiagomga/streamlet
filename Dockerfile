# Build from Alpine's Python 3.12 image
FROM python:3.12-alpine

# Set working directory to /app
WORKDIR /app

# Copy configuration file and list of dependencies
COPY config.yaml requirements.txt ./

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY src/ ./src/

# Start the application
CMD ["python3", "src/main.py"]