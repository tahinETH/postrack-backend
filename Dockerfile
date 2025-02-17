

FROM python:3.10-slim

# Set a working directory inside the container
WORKDIR /app

# Install system dependencies if you need them
# RUN apt-get update && apt-get install -y <some-dependency>

# Copy requirements.txt first to leverage Docker's caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install clerk-backend-api
RUN pip install svix

# Copy the rest of your code
COPY . .

# Expose the port where your FastAPI app will run (3001 in main.py)
EXPOSE 3001

# By default, run uvicorn with the main:app from your project
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3001"]