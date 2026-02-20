# Use a lightweight Python base image
FROM python:3.9-slim

# 1. Install system dependencies
# We NEED 'git' installed at the OS level so GitPython can clone repos
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements first to leverage Docker cache
COPY requirements.txt .

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
# (Your .dockerignore will prevent venv/ and .env from being copied here)
COPY . .

# 6. Expose Streamlit's default port
EXPOSE 8501

# 7. Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]