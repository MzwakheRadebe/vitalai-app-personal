# 1. Use a slim Python image to keep the overall size smaller
FROM python:3.13-slim

# Set environment variables to optimize pip installation
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_NO_CACHE_DIR=off

# Set the working directory
WORKDIR /app

# Copy the requirements file first to take advantage of Docker layer caching
COPY requirements.txt .

# 2. The critical step: Install with specific flags
# We use --no-cache-dir to save disk space and --upgrade for robustness
# You must ensure the *correct* torch version is installed if you use a specific one.
# Given your requirements.txt, this should work:
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# 3. Specify the startup command (adjust the path if necessary)
CMD ["uvicorn", "ai_and_nlp.non_final_draft:app", "--host", "0.0.0.0", "--port", "8000"]