# 1. Use an official, slim Python runtime as the base image.
# Using a specific version ensures consistent builds.
FROM python:3.11-slim

# 2. Set the working directory inside the container to /app.
# All subsequent commands will run from this directory.
WORKDIR /app

# 3. Copy the requirements file into the container.
# This is done first to leverage Docker's layer caching. If requirements.txt
# doesn't change, this layer won't be rebuilt, speeding up future builds.
COPY requirements.txt .

# 4. Install the Python dependencies.
# --no-cache-dir keeps the image size smaller.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container.
COPY . .

# 6. Define the command to run your application.
# This command starts the uvicorn server.
# --host 0.0.0.0 makes the server accessible from outside the container.
# --port $PORT is critical for Cloud Run, which injects the port number
# it wants the container to listen on into this environment variable.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]