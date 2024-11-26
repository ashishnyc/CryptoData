# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app
COPY api/ .
COPY database/ ./database/
COPY dataManagers/ ./dataManagers/
COPY xchanges/ ./xchanges/
COPY requirements.txt .
COPY Config.py .
COPY .env .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the command to start uvicorn
CMD ["uvicorn", "api.load:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]